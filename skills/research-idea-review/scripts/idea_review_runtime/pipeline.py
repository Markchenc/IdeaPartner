from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from .artifacts import atomic_write_json, atomic_write_text, read_json, sha256_file, utc_now
from .evidence import (
    LiveSourceVerifier,
    SourceVerifier,
    merge_source_ledgers,
    normalize_and_verify_sources,
)
from .tasks import (
    ARTIFACT_PURPOSES,
    INPUT_ARTIFACT_ID,
    M3_DISCOVERY_TASKS,
    M5_TASKS,
    TASK_ORDER,
    TASKS,
    TaskSpec,
)
from .validation import (
    CheckpointRequired,
    EvidenceIntegrityError,
    MissingDependency,
    PipelineError,
    ProvenanceIntegrityError,
    RunNotFound,
    StaleDependency,
    SubmissionError,
    TaskAlreadyComplete,
    evidence_claim_ledger,
    require_keys,
    validate_citation_claim_ids,
    validate_consumed_inputs,
    validate_evidence_claims,
    validate_optional_evidence_claim_ids,
    validate_provenance_sections,
    validate_review_payload,
    validate_source_ids,
)


RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
MANIFEST_NAME = "manifest.json"


class ReviewPipeline:
    def __init__(self, run_dir: Path, *, source_verifier: SourceVerifier | None = None) -> None:
        self.run_dir = Path(run_dir).resolve()
        self.manifest_path = self.run_dir / MANIFEST_NAME
        if not self.manifest_path.is_file():
            raise RunNotFound(f"No IdeaPartner run manifest exists at {self.manifest_path}")
        self.source_verifier = source_verifier or LiveSourceVerifier()
        self._manifest = read_json(self.manifest_path)
        self.skill_root = Path(__file__).resolve().parents[2]

    @classmethod
    def create(
        cls,
        runs_dir: Path,
        idea_text: str,
        *,
        run_id: str,
        source_verifier: SourceVerifier | None = None,
    ) -> "ReviewPipeline":
        if not RUN_ID_PATTERN.fullmatch(run_id):
            raise PipelineError("run_id must contain only letters, digits, dots, underscores, or hyphens")
        if not idea_text.strip():
            raise PipelineError("The idea input cannot be empty")
        run_dir = Path(runs_dir).resolve() / run_id
        if run_dir.exists() and any(run_dir.iterdir()):
            raise PipelineError(f"Run directory already exists and is not empty: {run_dir}")
        run_dir.mkdir(parents=True, exist_ok=True)
        input_path = run_dir / "input.md"
        atomic_write_text(input_path, idea_text.rstrip() + "\n")
        created_at = utc_now()
        manifest = {
            "schema_version": 1,
            "runtime_version": "1.1.0",
            "run_id": run_id,
            "created_at": created_at,
            "updated_at": created_at,
            "state": "POSITIONING",
            "artifacts": {
                INPUT_ARTIFACT_ID: {
                    "artifact_id": INPUT_ARTIFACT_ID,
                    "path": "input.md",
                    "sha256": sha256_file(input_path),
                    "produced_by": "researcher",
                    "created_at": created_at,
                }
            },
            "checkpoints": {
                "positioning": {
                    "status": "pending",
                    "artifact_sha256": None,
                    "note": "",
                    "decided_at": None,
                },
                "post-m3": {
                    "status": "not_required",
                    "artifact_sha256": None,
                    "note": "",
                    "decided_at": None,
                },
            },
            "task_packets": {},
            "exports": {},
        }
        atomic_write_json(run_dir / MANIFEST_NAME, manifest)
        return cls(run_dir, source_verifier=source_verifier)

    @property
    def manifest(self) -> dict[str, Any]:
        return copy.deepcopy(self._manifest)

    def _save_manifest(self) -> None:
        self._manifest["updated_at"] = utc_now()
        self._manifest["state"] = self.compute_state()
        atomic_write_json(self.manifest_path, self._manifest)

    def _artifact_record(self, artifact_id: str) -> dict[str, Any] | None:
        record = self._manifest.get("artifacts", {}).get(artifact_id)
        return record if isinstance(record, dict) else None

    def _artifact_path(self, artifact_id: str) -> Path:
        record = self._artifact_record(artifact_id)
        if not record:
            raise MissingDependency(f"Artifact {artifact_id} is missing")
        return self.run_dir / record["path"]

    def artifact_is_fresh(self, artifact_id: str) -> bool:
        return self._artifact_is_fresh(artifact_id, {}, set())

    def _artifact_is_fresh(
        self,
        artifact_id: str,
        memo: dict[str, bool],
        visiting: set[str],
    ) -> bool:
        if artifact_id in memo:
            return memo[artifact_id]
        record = self._artifact_record(artifact_id)
        if not record:
            memo[artifact_id] = False
            return False
        path = self.run_dir / record["path"]
        if not path.is_file() or sha256_file(path) != record.get("sha256"):
            memo[artifact_id] = False
            return False
        if artifact_id == INPUT_ARTIFACT_ID:
            memo[artifact_id] = True
            return True
        if artifact_id in visiting:
            memo[artifact_id] = False
            return False
        visiting.add(artifact_id)
        try:
            envelope = read_json(path)
        except (OSError, ValueError):
            memo[artifact_id] = False
            return False
        inputs = envelope.get("inputs")
        if not isinstance(inputs, list):
            memo[artifact_id] = False
            return False
        for dependency in inputs:
            if not isinstance(dependency, dict):
                memo[artifact_id] = False
                return False
            dependency_id = dependency.get("artifact_id")
            current = self._artifact_record(str(dependency_id))
            if not current or dependency.get("sha256") != current.get("sha256"):
                memo[artifact_id] = False
                return False
            if not self._artifact_is_fresh(str(dependency_id), memo, visiting.copy()):
                memo[artifact_id] = False
                return False
        memo[artifact_id] = True
        return True

    def _positioning_confirmed(self) -> bool:
        checkpoint = self._manifest["checkpoints"]["positioning"]
        record = self._artifact_record("m1-positioning")
        return bool(
            record
            and self.artifact_is_fresh("m1-positioning")
            and checkpoint.get("status") == "confirmed"
            and checkpoint.get("artifact_sha256") == record.get("sha256")
        )

    def _post_m3_confirmed(self) -> bool:
        checkpoint = self._manifest["checkpoints"]["post-m3"]
        if checkpoint.get("status") == "not_required":
            record = self._artifact_record("m3-synthesis")
            return bool(record and checkpoint.get("artifact_sha256") == record.get("sha256"))
        record = self._artifact_record("m3-synthesis")
        return bool(
            record
            and self.artifact_is_fresh("m3-synthesis")
            and checkpoint.get("status") == "confirmed"
            and checkpoint.get("artifact_sha256") == record.get("sha256")
        )

    def confirm_positioning(self, note: str) -> None:
        if not self.artifact_is_fresh("m1-positioning"):
            raise MissingDependency("A fresh M1 positioning artifact is required before confirmation")
        record = self._artifact_record("m1-positioning")
        self._manifest["checkpoints"]["positioning"] = {
            "status": "confirmed",
            "artifact_sha256": record["sha256"],
            "note": note.strip(),
            "decided_at": utc_now(),
        }
        self._save_manifest()

    def confirm_post_m3(self, note: str) -> None:
        if not self.artifact_is_fresh("m3-synthesis"):
            raise MissingDependency("A fresh M3 synthesis artifact is required before re-positioning confirmation")
        checkpoint = self._manifest["checkpoints"]["post-m3"]
        if checkpoint.get("status") != "pending":
            raise CheckpointRequired("The M3 result does not currently require a re-positioning decision")
        record = self._artifact_record("m3-synthesis")
        self._manifest["checkpoints"]["post-m3"] = {
            "status": "confirmed",
            "artifact_sha256": record["sha256"],
            "note": note.strip(),
            "decided_at": utc_now(),
        }
        self._save_manifest()

    def _ensure_checkpoint(self, spec: TaskSpec) -> None:
        if spec.checkpoint == "positioning" and not self._positioning_confirmed():
            raise CheckpointRequired("M2 is blocked until the researcher confirms the current M1 positioning")
        if spec.checkpoint == "post-m3" and not self._post_m3_confirmed():
            raise CheckpointRequired(
                "M3 materially changed the positioning; M4 is blocked until the researcher confirms or corrects it"
            )

    def _dependency_inputs(self, spec: TaskSpec) -> list[dict[str, Any]]:
        inputs: list[dict[str, Any]] = []
        missing: list[str] = []
        stale: list[str] = []
        for artifact_id in spec.dependencies:
            record = self._artifact_record(artifact_id)
            if not record:
                missing.append(artifact_id)
                continue
            if not self.artifact_is_fresh(artifact_id):
                stale.append(artifact_id)
                continue
            path = (self.run_dir / record["path"]).resolve()
            inputs.append(
                {
                    "artifact_id": artifact_id,
                    "relative_path": record["path"],
                    "path": str(path),
                    "sha256": record["sha256"],
                    "purpose": ARTIFACT_PURPOSES[artifact_id],
                }
            )
        if missing:
            raise MissingDependency(f"{spec.task_id} is missing dependencies: {', '.join(missing)}")
        if stale:
            raise StaleDependency(f"{spec.task_id} has stale dependencies: {', '.join(stale)}")
        return inputs

    def emit_task(self, task_id: str, *, refresh: bool = False) -> dict[str, Any]:
        if task_id not in TASKS:
            raise PipelineError(f"Unknown task_id {task_id}")
        spec = TASKS[task_id]
        if self.artifact_is_fresh(spec.artifact_id) and not refresh:
            raise TaskAlreadyComplete(f"{task_id} already has a fresh artifact; use refresh to rerun it")
        inputs = self._dependency_inputs(spec)
        self._ensure_checkpoint(spec)
        instruction_path = (self.skill_root / spec.instruction_file).resolve()
        packet = {
            "packet_version": 1,
            "run_id": self._manifest["run_id"],
            "task_id": task_id,
            "objective": spec.objective,
            "isolation_contract": {
                "mode": "fresh_worker_context",
                "rule": "Use only this packet, every listed input artifact, the specified instruction section, and retrieved evidence. Do not rely on hidden conversation history.",
            },
            "instruction": {
                "path": str(instruction_path),
                "section": spec.instruction_section,
            },
            "artifact_contract": {
                "path": str((self.skill_root / "references" / "artifact-contracts.md").resolve()),
                "rule": "Read the common submission envelope and the payload contract for this task before writing the submission.",
            },
            "inputs": inputs,
            "read_all_inputs": True,
            "output_contract": {
                "artifact_id": spec.artifact_id,
                "required_payload_keys": list(spec.required_payload_keys),
                "submission_path": str((self.run_dir / "submissions" / f"{task_id}.json").resolve()),
            },
            "validation_scope": [
                "checkpoint_and_dependency_integrity",
                "source_and_citation_integrity",
                "provenance_and_no_invented_evidence",
            ],
            "submission_template": {
                "task_id": task_id,
                "summary": "REPLACE_WITH_A_2_TO_4_SENTENCE_SUPERVISOR_SUMMARY",
                "attention_items": [],
                "consumed_inputs": [
                    {
                        "artifact_id": item["artifact_id"],
                        "sha256": item["sha256"],
                        "used_for": "REPLACE_WITH_A_SHORT_DESCRIPTION_OF_HOW_THIS_INPUT_SHAPED_THE_RESULT",
                    }
                    for item in inputs
                ],
                "payload": {key: None for key in spec.required_payload_keys},
            },
        }
        packet_path = self.run_dir / "tasks" / f"{task_id}.json"
        atomic_write_json(packet_path, packet)
        self._manifest["task_packets"][task_id] = {
            "path": str(packet_path.relative_to(self.run_dir)).replace("\\", "/"),
            "sha256": sha256_file(packet_path),
            "emitted_at": utc_now(),
        }
        self._save_manifest()
        return packet

    def _load_task_packet(self, task_id: str) -> dict[str, Any]:
        packet_record = self._manifest.get("task_packets", {}).get(task_id)
        if not isinstance(packet_record, dict):
            raise SubmissionError(f"No task packet has been emitted for {task_id}")
        packet_path = self.run_dir / packet_record["path"]
        if not packet_path.is_file() or sha256_file(packet_path) != packet_record.get("sha256"):
            raise SubmissionError(f"The task packet for {task_id} is missing or was modified")
        return read_json(packet_path)

    def _artifact_payload(self, artifact_id: str) -> dict[str, Any]:
        path = self._artifact_path(artifact_id)
        envelope = read_json(path)
        payload = envelope.get("payload")
        if not isinstance(payload, dict):
            raise SubmissionError(f"Artifact {artifact_id} has an invalid payload")
        return payload

    def source_ledger(self) -> dict[str, dict[str, Any]]:
        groups: list[list[dict[str, Any]]] = []
        for task_id in M3_DISCOVERY_TASKS:
            artifact_id = TASKS[task_id].artifact_id
            if not self.artifact_is_fresh(artifact_id):
                continue
            sources = self._artifact_payload(artifact_id).get("sources", [])
            if isinstance(sources, list):
                groups.append(sources)
        return merge_source_ledgers(*groups)

    def canonical_evidence_claims(self) -> dict[str, dict[str, Any]]:
        if not self.artifact_is_fresh("m3-synthesis"):
            return {}
        return evidence_claim_ledger(self._artifact_payload("m3-synthesis").get("evidence_claims", []))

    def _prepare_payload(self, task_id: str, raw_payload: Any) -> dict[str, Any]:
        if not isinstance(raw_payload, dict):
            raise SubmissionError("payload must be a JSON object")
        payload = copy.deepcopy(raw_payload)
        spec = TASKS[task_id]
        require_keys(payload, spec.required_payload_keys, context=task_id)

        if task_id in M3_DISCOVERY_TASKS:
            payload["sources"] = normalize_and_verify_sources(payload["sources"], self.source_verifier)
            local_ledger = merge_source_ledgers(payload["sources"])
            validate_evidence_claims(payload["evidence_claims"], local_ledger, context=task_id)
        elif task_id == "m3-synthesis":
            ledger = self.source_ledger()
            validate_evidence_claims(payload["evidence_claims"], ledger, context=task_id)
            validate_source_ids(payload["closest_work"], ledger, context=f"{task_id} closest_work")
            repositioning = payload["repositioning"]
            if not isinstance(repositioning, dict) or not isinstance(repositioning.get("required"), bool):
                raise SubmissionError("m3-synthesis repositioning must contain a required boolean")
        elif task_id == "m4-reconstruction":
            validate_provenance_sections(payload, spec.required_payload_keys, self.canonical_evidence_claims())
        elif task_id in M5_TASKS:
            validate_review_payload(payload, self.canonical_evidence_claims(), context=task_id)
        elif task_id == "m6-challenge":
            challenges = payload["selected_challenges"]
            if not isinstance(challenges, list) or len(challenges) > 3:
                raise SubmissionError("m6-challenge must select at most three challenges")
            validate_optional_evidence_claim_ids(
                challenges, self.canonical_evidence_claims(), context="selected_challenges"
            )
            validate_optional_evidence_claim_ids(
                payload["updates"], self.canonical_evidence_claims(), context="updates"
            )
        elif task_id == "m7-synthesis":
            if not isinstance(payload["report_markdown"], str) or not payload["report_markdown"].strip():
                raise SubmissionError("m7-synthesis report_markdown must be non-empty")
            validate_citation_claim_ids(
                payload["citation_claim_ids"],
                self.canonical_evidence_claims(),
                context="m7-synthesis citations",
            )
        return payload

    def ingest(
        self,
        task_id: str,
        submission: dict[str, Any] | Path,
        *,
        replace: bool = False,
    ) -> Path:
        if task_id not in TASKS:
            raise PipelineError(f"Unknown task_id {task_id}")
        spec = TASKS[task_id]
        current_record = self._artifact_record(spec.artifact_id)
        if current_record and not replace:
            raise TaskAlreadyComplete(f"{task_id} already has an artifact; use replace to ingest a new version")
        expected_inputs = self._dependency_inputs(spec)
        self._ensure_checkpoint(spec)
        packet = self._load_task_packet(task_id)
        packet_inputs = packet.get("inputs")
        expected_signature = [(item["artifact_id"], item["sha256"]) for item in expected_inputs]
        packet_signature = [
            (item.get("artifact_id"), item.get("sha256"))
            for item in packet_inputs
            if isinstance(item, dict)
        ] if isinstance(packet_inputs, list) else []
        if packet_signature != expected_signature:
            raise SubmissionError(f"The emitted task packet for {task_id} no longer matches current dependencies")

        submission_value = read_json(Path(submission)) if isinstance(submission, Path) else copy.deepcopy(submission)
        if not isinstance(submission_value, dict) or submission_value.get("task_id") != task_id:
            raise SubmissionError(f"Submission task_id must equal {task_id}")
        summary = submission_value.get("summary")
        if not isinstance(summary, str) or not summary.strip() or summary.startswith("REPLACE_WITH_"):
            raise SubmissionError("Submission must contain a concise supervisor summary")
        attention_items = submission_value.get("attention_items", [])
        if not isinstance(attention_items, list) or any(not isinstance(item, str) for item in attention_items):
            raise SubmissionError("attention_items must be a list of strings")
        consumed_inputs = validate_consumed_inputs(submission_value.get("consumed_inputs"), expected_inputs)
        payload = self._prepare_payload(task_id, submission_value.get("payload"))

        artifact_path = self.run_dir / spec.artifact_path
        envelope = {
            "schema_version": 1,
            "run_id": self._manifest["run_id"],
            "artifact_id": spec.artifact_id,
            "task_id": task_id,
            "created_at": utc_now(),
            "summary": summary.strip(),
            "attention_items": attention_items,
            "inputs": consumed_inputs,
            "payload": payload,
        }
        atomic_write_json(artifact_path, envelope)
        artifact_record = {
            "artifact_id": spec.artifact_id,
            "path": str(artifact_path.relative_to(self.run_dir)).replace("\\", "/"),
            "sha256": sha256_file(artifact_path),
            "produced_by": task_id,
            "created_at": envelope["created_at"],
            "summary": envelope["summary"],
            "attention_items": envelope["attention_items"],
        }
        self._manifest["artifacts"][spec.artifact_id] = artifact_record

        if task_id == "m1-positioning":
            self._manifest["checkpoints"]["positioning"] = {
                "status": "pending",
                "artifact_sha256": artifact_record["sha256"],
                "note": "",
                "decided_at": None,
            }
        elif task_id == "m3-synthesis":
            needs_confirmation = payload["repositioning"]["required"]
            self._manifest["checkpoints"]["post-m3"] = {
                "status": "pending" if needs_confirmation else "not_required",
                "artifact_sha256": artifact_record["sha256"],
                "note": "",
                "decided_at": None,
            }
        elif task_id == "m7-synthesis":
            report_path = self.run_dir / "07-final-report.md"
            atomic_write_text(report_path, payload["report_markdown"].rstrip() + "\n")
            self._manifest.setdefault("exports", {})["final_report"] = {
                "path": "07-final-report.md",
                "sha256": sha256_file(report_path),
                "source_artifact_sha256": artifact_record["sha256"],
                "created_at": utc_now(),
            }

        self._save_manifest()
        return artifact_path

    def compute_state(self) -> str:
        if not self.artifact_is_fresh("m1-positioning"):
            return "POSITIONING"
        if not self._positioning_confirmed():
            return "WAITING_FOR_POSITIONING_CONFIRMATION"
        if not self.artifact_is_fresh("m2-route"):
            return "ROUTING"
        if any(not self.artifact_is_fresh(TASKS[task].artifact_id) for task in M3_DISCOVERY_TASKS):
            return "DOMAIN_PRIOR_RESEARCH"
        if not self.artifact_is_fresh("m3-synthesis"):
            return "DOMAIN_PRIOR_SYNTHESIS"
        if not self._post_m3_confirmed():
            return "WAITING_FOR_REPOSITIONING_CONFIRMATION"
        if not self.artifact_is_fresh("m4-reconstruction"):
            return "IDEA_RECONSTRUCTION"
        if not self.artifact_is_fresh("m5-a") or not self.artifact_is_fresh("m5-b"):
            return "REVIEW_AB"
        if not self.artifact_is_fresh("m5-c"):
            return "REVIEW_C"
        if not self.artifact_is_fresh("m5-d"):
            return "REVIEW_D"
        if not self.artifact_is_fresh("m6-challenge"):
            return "CHALLENGE"
        if not self.artifact_is_fresh("m7-synthesis"):
            return "SYNTHESIS"
        return "FINALIZED"

    def _task_ready(self, task_id: str) -> bool:
        spec = TASKS[task_id]
        if self.artifact_is_fresh(spec.artifact_id):
            return False
        try:
            self._dependency_inputs(spec)
            self._ensure_checkpoint(spec)
        except PipelineError:
            return False
        return True

    def status(self) -> dict[str, Any]:
        artifacts: dict[str, dict[str, Any]] = {}
        for artifact_id, record in self._manifest.get("artifacts", {}).items():
            artifacts[artifact_id] = {
                "path": record["path"],
                "fresh": self.artifact_is_fresh(artifact_id),
                "summary": record.get("summary"),
                "attention_items": record.get("attention_items", []),
            }
        return {
            "run_id": self._manifest["run_id"],
            "state": self.compute_state(),
            "ready_tasks": [task_id for task_id in TASK_ORDER if self._task_ready(task_id)],
            "artifacts": artifacts,
            "checkpoints": copy.deepcopy(self._manifest["checkpoints"]),
            "exports": copy.deepcopy(self._manifest.get("exports", {})),
        }

    def validate_run(self) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        for artifact_id in self._manifest.get("artifacts", {}):
            if not self.artifact_is_fresh(artifact_id):
                errors.append(f"Artifact {artifact_id} is stale, missing, or externally modified")
        ledger = self.source_ledger()
        for source_id, source in ledger.items():
            if source.get("verification", {}).get("status") != "verified":
                warnings.append(f"Source {source_id} is registered but cannot support evidence-dependent claims")
        if self.artifact_is_fresh("m1-positioning") and not self._positioning_confirmed():
            warnings.append("The pipeline is correctly stopped at the positioning checkpoint")
        if self.artifact_is_fresh("m7-synthesis"):
            export = self._manifest.get("exports", {}).get("final_report")
            m7_record = self._artifact_record("m7-synthesis")
            if not isinstance(export, dict):
                errors.append("The final report export is missing")
            else:
                export_path = self.run_dir / export.get("path", "")
                if not export_path.is_file() or sha256_file(export_path) != export.get("sha256"):
                    errors.append("The final report export is missing or externally modified")
                if export.get("source_artifact_sha256") != m7_record.get("sha256"):
                    errors.append("The final report export was not generated from the current M7 artifact")
        return {
            "valid": not errors,
            "state": self.compute_state(),
            "errors": errors,
            "warnings": warnings,
            "verified_source_count": sum(
                1 for source in ledger.values() if source.get("verification", {}).get("status") == "verified"
            ),
            "registered_source_count": len(ledger),
        }


__all__ = [
    "CheckpointRequired",
    "EvidenceIntegrityError",
    "MissingDependency",
    "PipelineError",
    "ProvenanceIntegrityError",
    "ReviewPipeline",
    "StaleDependency",
    "SubmissionError",
    "TaskAlreadyComplete",
]
