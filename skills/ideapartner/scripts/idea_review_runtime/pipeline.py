from __future__ import annotations
import copy
import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .artifacts import atomic_write_json, atomic_write_text, read_json, utc_now
from .evidence import LiveSourceVerifier
from .ledger import empty_ledger, prepare_batch, evidence_view, digest
from .locking import InterProcessFileLock
from .tasks import TASKS, TASK_ORDER
from .validation import (PipelineError, RunNotFound, MissingDependency, StaleDependency,
                         SubmissionError, EvidenceIntegrityError, TaskAlreadyComplete,
                         identifier, require_keys, nonempty, strings, refs_in, validate_refs,
                         validate_plan, validate_review, validate_report)
from .report import render_report


class ReviewPipeline:
    def __init__(self, run_dir, *, source_verifier=None):
        self.run_dir = Path(run_dir).resolve()
        self.manifest_path = self.run_dir / "manifest.json"
        if not self.manifest_path.is_file(): raise RunNotFound(str(self.manifest_path))
        self.source_verifier = source_verifier or LiveSourceVerifier()
        self.skill_root = Path(__file__).resolve().parents[2]
        self._manifest = read_json(self.manifest_path)
        if self._manifest.get("schema_version") not in (1, 2): raise PipelineError("Unsupported manifest schema")

    @classmethod
    def create(cls, runs_dir, idea_text, *, run_id, source_verifier=None, max_rechecks=1, review_deadline_minutes=30):
        identifier(run_id)
        nonempty(idea_text, "idea input")
        if type(max_rechecks) is not int or not 0 <= max_rechecks <= 3: raise PipelineError("max_rechecks must be 0..3")
        if not isinstance(review_deadline_minutes, (int, float)) or not 0 < review_deadline_minutes <= 1440:
            raise PipelineError("review deadline must be 0..1440 minutes")
        directory = Path(runs_dir).resolve() / run_id
        # Exclusive directory creation prevents two initializers from sharing a run.
        directory.parent.mkdir(parents=True, exist_ok=True)
        try: directory.mkdir()
        except FileExistsError: raise PipelineError("Run directory already exists")
        atomic_write_text(directory / "input.md", idea_text.rstrip() + "\n")
        manifest = {"schema_version": 2, "runtime_version": __version__, "run_id": run_id,
                    "created_at": utc_now(), "updated_at": utc_now(), "state": "PLANNING",
                    "artifacts": {"input": {"path": "input.md", "version": 1}},
                    "evidence_snapshot": None, "evidence_revision": 0, "task_packets": {},
                    "budget": {"max_rechecks": max_rechecks, "review_deadline_minutes": review_deadline_minutes,
                               "review_started_at": None},
                    "recheck": {"count": 0, "pending": None}, "review_dirty": False, "exports": {}}
        atomic_write_json(directory / "manifest.json", manifest)
        return cls(directory, source_verifier=source_verifier)

    @property
    def manifest(self):
        with self._transaction(): return copy.deepcopy(self._manifest)

    @contextmanager
    def _transaction(self):
        # Legacy reads never create lock files or mutate old runs.
        if self._manifest["schema_version"] == 1:
            self._manifest = read_json(self.manifest_path)
            yield
            return
        with InterProcessFileLock(self.run_dir / ".manifest.lock"):
            self._manifest = read_json(self.manifest_path)
            yield

    def _writable(self):
        if self._manifest["schema_version"] != 2:
            raise PipelineError("Legacy run is read-only; create a v2 run from input.md or use the old release")

    def _path(self, relative):
        path = (self.run_dir / relative).resolve()
        if not path.is_relative_to(self.run_dir): raise PipelineError("Path escapes run directory")
        return path

    def _save(self):
        self._manifest["state"] = self.compute_state()
        self._manifest["updated_at"] = utc_now()
        atomic_write_json(self.manifest_path, self._manifest)

    def _payload(self, aid):
        return read_json(self._path(self._manifest["artifacts"][aid]["path"]))["payload"]

    def _ledger(self):
        path = self._manifest["evidence_snapshot"]
        return read_json(self._path(path)) if path else empty_ledger()

    def _questions(self):
        questions = dict(self._ledger()["questions"])
        if "plan" in self._manifest["artifacts"]:
            questions.update({q["id"]: q for q in self._payload("plan")["review_questions"]})
        return questions

    def _fresh(self, aid):
        record = self._manifest["artifacts"].get(aid)
        if not record or not self._path(record["path"]).is_file(): return False
        if aid == "input": return True
        if aid in {"review", "report"} and self._manifest["review_dirty"]: return False
        try:
            envelope = read_json(self._path(record["path"]))
            if envelope["artifact_version"] != record["version"]: return False
            for dep, version in envelope["inputs"].items():
                if not self._fresh(dep) or self._manifest["artifacts"][dep]["version"] != version: return False
            validate_refs(envelope["evidence_refs"], self._ledger())
        except (ValueError, KeyError, OSError, PipelineError):
            return False
        return True

    def artifact_is_fresh(self, aid):
        with self._transaction(): return self._fresh(aid)

    def compute_state(self):
        if self._manifest["schema_version"] == 1: return self._manifest["state"]
        if not self._fresh("plan"): return "PLANNING"
        if self._manifest["recheck"]["pending"]: return "RECHECKING"
        if not self._fresh("review"): return "REVIEWING"
        if not self._fresh("report"): return "REPORTING"
        return "FINALIZED"

    def _expired(self):
        b = self._manifest["budget"]
        return bool(b["review_started_at"] and
                    (datetime.now(timezone.utc) - datetime.fromisoformat(b["review_started_at"])).total_seconds()
                    >= b["review_deadline_minutes"] * 60)

    def status(self):
        with self._transaction():
            if self._manifest["schema_version"] == 1:
                return {"run_id": self._manifest["run_id"], "state": self.compute_state(),
                        "legacy_read_only": True, "ready_tasks": [], "exports": self._manifest.get("exports", {})}
            state = self.compute_state()
            ready = {"PLANNING": ["s1-plan"], "REVIEWING": ["s2-review"], "RECHECKING": ["s2-review"],
                     "REPORTING": ["s3-report"], "FINALIZED": []}[state]
            return {"run_id": self._manifest["run_id"], "state": state, "ready_tasks": ready,
                    "budget": self._manifest["budget"], "research_allowed": not self._expired(),
                    "recheck": self._manifest["recheck"], "exports": self._manifest["exports"],
                    "evidence_revision": self._manifest["evidence_revision"],
                    "size_warnings": [p["size_warning"] for p in self._manifest["task_packets"].values() if p.get("size_warning")]}

    def emit_task(self, task_id, *, refresh=False):
        with self._transaction():
            self._writable()
            if task_id not in TASKS: raise PipelineError("Unknown task")
            spec = TASKS[task_id]
            if self._fresh(spec.artifact_id) and not refresh: raise TaskAlreadyComplete(task_id)
            if task_id == "s3-report" and self._manifest["recheck"]["pending"]: raise MissingDependency("Complete pending recheck first")
            inputs = {}
            for dep in spec.dependencies:
                if not self._fresh(dep): raise MissingDependency(f"Missing/stale {dep}")
                r = self._manifest["artifacts"][dep]
                inputs[dep] = {"version": r["version"], "path": str(self._path(r["path"]))}
            pid = uuid.uuid4().hex
            packet = {"packet_id": pid, "run_id": self._manifest["run_id"], "task_id": task_id,
                      "objective": spec.objective, "inputs": inputs,
                      "instruction": str(self.skill_root / "references" / spec.instruction_file),
                      "contract": str(self.skill_root / "references/artifact-contracts.md"),
                      "submission_path": str(self.run_dir / "submissions" / (pid + ".json")),
                      "isolation_mode": "fresh_stage_context", "evidence_revision": self._manifest["evidence_revision"]}
            if task_id == "s2-review":
                if not self._manifest["budget"]["review_started_at"]:
                    self._manifest["budget"]["review_started_at"] = utc_now()
                packet["research_allowed"] = not self._expired()
                packet["budget"] = copy.deepcopy(self._manifest["budget"])
                packet["evidence_snapshot"] = str(self._path(self._manifest["evidence_snapshot"])) if self._manifest["evidence_snapshot"] else None
                packet["recheck_request"] = self._manifest["recheck"]["pending"]
                if "review" in self._manifest["artifacts"]:
                    packet["previous_review"] = str(self._path(self._manifest["artifacts"]["review"]["path"]))
                packet["recovery_path"] = str(self.run_dir / "recovery-review.json")
            if task_id == "s3-report":
                view = evidence_view(self._payload("review"), self._ledger())
                relative = f"views/{pid}-evidence.json"
                atomic_write_json(self._path(relative), view)
                packet["evidence_view"] = str(self._path(relative))
                packet["rechecks_remaining"] = max(0, self._manifest["budget"]["max_rechecks"] - self._manifest["recheck"]["count"])
            packet["input_chars"] = sum(len(Path(v["path"]).read_text(encoding="utf-8-sig")) for v in inputs.values())
            if "evidence_view" in packet: packet["input_chars"] += len(Path(packet["evidence_view"]).read_text(encoding="utf-8-sig"))
            atomic_write_json(self.run_dir / "tasks" / (pid + ".json"), packet)
            self._manifest["task_packets"][pid] = {"path": f"tasks/{pid}.json", "task_id": task_id, "consumed": False,
                                                     "input_chars": packet["input_chars"], "created_at": utc_now()}
            self._save()
            return packet

    def add_evidence(self, batch):
        if isinstance(batch, (Path, str)): batch = read_json(Path(batch))
        with self._transaction():
            self._writable()
            if not self._fresh("plan"): raise MissingDependency("Plan required")
            baseline = self._ledger()
            # Idempotent retry remains allowed after the budget expired.
            if batch.get("batch_id") not in baseline["batches"]:
                if not self._manifest["budget"]["review_started_at"]:
                    raise MissingDependency("Emit s2-review before researching")
                if self._expired():
                    raise PipelineError("Research deadline reached; submit a qualified review")
            revision = self._manifest["evidence_revision"]
            plan_version = self._manifest["artifacts"]["plan"]["version"]
            questions = self._questions()
        ledger, result, replay = prepare_batch(baseline, batch, self.source_verifier, questions)
        if replay: return result
        with self._transaction():
            self._writable()
            if revision != self._manifest["evidence_revision"] or plan_version != self._manifest["artifacts"]["plan"]["version"]:
                raise StaleDependency("Evidence changed during verification; retry batch")
            revision += 1
            path = f"evidence/ledger-{uuid.uuid4().hex}.json"
            atomic_write_json(self._path(path), ledger)
            self._manifest["evidence_snapshot"] = path
            self._manifest["evidence_revision"] = revision
            if "review" in self._manifest["artifacts"]:
                review = self._payload("review")
                reviewed_qids = {q["id"] for q in review["questions"]}
                if batch["question_id"] in reviewed_qids or set(result["changed_claim_ids"]) & refs_in(review).keys():
                    self._manifest["review_dirty"] = True
                    self._manifest["exports"] = {}
            self._save()
            return result

    def ingest(self, task_id, submission, *, replace=False):
        value = read_json(Path(submission)) if isinstance(submission, (Path, str)) else copy.deepcopy(submission)
        require_keys(value, ("task_id", "packet_id"))
        with self._transaction():
            self._writable()
            if task_id not in TASKS or value["task_id"] != task_id: raise SubmissionError("Task ID mismatch")
            pid = value["packet_id"]
            record = self._manifest["task_packets"].get(pid)
            if not record or record["task_id"] != task_id: raise SubmissionError("Unknown packet")
            if record["consumed"]:
                if record.get("submission_digest") == digest(value): return copy.deepcopy(record["result"])
                raise SubmissionError("Packet already consumed")
            packet = read_json(self._path(record["path"]))
            for aid, ref in packet["inputs"].items():
                if not self._fresh(aid) or self._manifest["artifacts"][aid]["version"] != ref["version"]:
                    raise StaleDependency("Packet inputs changed")
            if task_id == "s3-report" and self._manifest["recheck"]["pending"]:
                raise StaleDependency("Complete pending recheck first")
            if task_id == "s2-review":
                # Evidence additions are expected during a stage; the submitted review must close over current questions.
                if self._manifest["artifacts"]["plan"]["version"] != packet["inputs"]["plan"]["version"]:
                    raise StaleDependency("Plan changed")
            if "recheck_request" in value:
                if task_id != "s3-report" or "payload" in value: raise SubmissionError("Recheck and final payload are exclusive")
                req = value["recheck_request"]
                require_keys(req, ("question_id", "reason", "affected_judgment_ids", "needed_evidence"))
                review = self._payload("review")
                if req["question_id"] not in {q["id"] for q in review["questions"]}: raise SubmissionError("Unknown recheck question")
                strings(req["affected_judgment_ids"], "affected judgments")
                if not req["affected_judgment_ids"] or not set(req["affected_judgment_ids"]) <= {j["id"] for j in review["judgments"]}:
                    raise SubmissionError("Unknown affected judgment")
                nonempty(req["reason"], "recheck reason"); nonempty(req["needed_evidence"], "needed evidence")
                if self._manifest["recheck"]["count"] >= self._manifest["budget"]["max_rechecks"] or self._expired():
                    return {"limit_reached": True, "instruction": "Complete report with explicit limitations"}
                self._manifest["recheck"]["count"] += 1
                self._manifest["recheck"]["pending"] = req
                self._manifest["review_dirty"] = True
                self._manifest["exports"] = {}
                atomic_write_json(self.run_dir / "rechecks" / (pid + ".json"), req)
                result = {"recheck_requested": True}
            else:
                require_keys(value, ("payload",))
                p = value["payload"]; ledger = self._ledger()
                line_count = len((self.run_dir / "input.md").read_text(encoding="utf-8").splitlines())
                if task_id == "s1-plan": validate_plan(p, line_count)
                elif task_id == "s2-review": validate_review(p, ledger, self._questions(), line_count)
                else: validate_report(p, ledger, self._payload("review"), line_count)
                aid = TASKS[task_id].artifact_id
                if self._fresh(aid) and not replace: raise TaskAlreadyComplete("Use replace for an existing fresh artifact")
                old = self._manifest["artifacts"].get(aid)
                version = old["version"] + 1 if old else 1
                relative = f"artifacts/{aid}-v{version}-{pid}.json"
                envelope = {"artifact_id": aid, "artifact_version": version,
                            "inputs": {k: v["version"] for k, v in packet["inputs"].items()},
                            "evidence_refs": refs_in(p), "payload": p}
                atomic_write_json(self._path(relative), envelope)
                self._manifest["artifacts"][aid] = {"path": relative, "version": version}
                if task_id == "s1-plan":
                    self._manifest["review_dirty"] = True
                    self._manifest["recheck"]["pending"] = None
                    self._manifest["exports"] = {}
                elif task_id == "s2-review":
                    self._manifest["review_dirty"] = False
                    self._manifest["recheck"]["pending"] = None
                    self._manifest["exports"] = {}
                else:
                    report_text = render_report(p, ledger)
                    # Versioned export is authoritative; convenience copy is not used for state.
                    export = f"artifacts/final-report-v{version}-{pid}.md"
                    atomic_write_text(self._path(export), report_text)
                    atomic_write_text(self.run_dir / "final-report.md", report_text)
                    self._manifest["exports"] = {"final_report": {"path": export, "version": version}}
                result = {"artifact": str(self._path(relative)), "version": version}
                record["output_chars"] = len(json.dumps(p, ensure_ascii=False))
                limit = {"s1-plan": 4000, "s2-review": 16000, "s3-report": 24000}[task_id]
                if record["output_chars"] > limit:
                    record["size_warning"] = f"{task_id}: {record['output_chars']} characters exceeds soft limit {limit}; avoid repeated analysis"
                record["token_usage"] = None
            record.update(consumed=True, submission_digest=digest(value), result=result, completed_at=utc_now())
            self._save()
            return copy.deepcopy(result)

    def validate_run(self):
        with self._transaction():
            if self._manifest["schema_version"] == 1:
                return {"valid": True, "legacy_read_only": True, "state": self.compute_state(),
                        "warnings": ["Legacy structure not validated by v2"], "errors": []}
            errors, warnings = [], []
            for aid in self._manifest["artifacts"]:
                if not self._fresh(aid): warnings.append(f"{aid} is stale; regenerate affected stage")
            try:
                lines = len((self.run_dir / "input.md").read_text(encoding="utf-8").splitlines())
                ledger = self._ledger()
                if self._fresh("plan"): validate_plan(self._payload("plan"), lines)
                if self._fresh("review"):
                    reviewed = self._payload("review")
                    qids = {q["id"] for q in reviewed["questions"]}
                    relevant = {k: v for k, v in self._questions().items() if k in qids}
                    validate_review(reviewed, ledger, relevant, lines)
                if self._fresh("report"):
                    p = self._payload("report")
                    validate_report(p, ledger, self._payload("review"), lines)
                    export = self._manifest["exports"].get("final_report")
                    if not export or not self._path(export["path"]).is_file(): raise SubmissionError("Missing report export")
                    if self._path(export["path"]).read_text(encoding="utf-8") != render_report(p, ledger):
                        raise SubmissionError("Report export does not match validated payload")
            except (PipelineError, KeyError, OSError, ValueError) as error: errors.append(str(error))
            return {"valid": not errors, "state": self.compute_state(), "errors": errors, "warnings": warnings}
