from __future__ import annotations
import re

class PipelineError(RuntimeError): pass
class RunNotFound(PipelineError): pass
class MissingDependency(PipelineError): pass
class StaleDependency(MissingDependency): pass
class SubmissionError(PipelineError): pass
class EvidenceIntegrityError(SubmissionError): pass
class ProvenanceIntegrityError(SubmissionError): pass
class TaskAlreadyComplete(PipelineError): pass

DIMENSIONS = ("value", "contribution", "mechanism", "testability")
SECTIONS = ("problem_definition", "limitations_and_core_difficulty", "contribution_design",
            "method_construction", "experimental_setting", "expected_difficulties")

def require_keys(value, keys, *, context="payload"):
    if not isinstance(value, dict):
        raise SubmissionError(f"{context} must be an object")
    missing = set(keys) - value.keys()
    if missing:
        raise SubmissionError(f"{context} missing: {', '.join(sorted(missing))}")

def nonempty(value, context):
    if not isinstance(value, str) or not value.strip():
        raise SubmissionError(f"{context} must be non-empty text")

def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", value):
        raise SubmissionError("Invalid identifier")
    return value

def strings(value, context):
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise SubmissionError(f"{context} must be a list of strings")

def objects(value, context):
    if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
        raise SubmissionError(f"{context} must be a list of objects")
    return value

def input_locator(locator, line_count):
    require_keys(locator, ("start", "end"), context="input_locator")
    a, b = locator["start"], locator["end"]
    if type(a) is not int or type(b) is not int or not 1 <= a <= b <= line_count:
        raise ProvenanceIntegrityError("Input locator is outside the original input")

def refs_in(value):
    refs = {}
    def put(cid, version):
        if cid in refs and refs[cid] != version:
            raise EvidenceIntegrityError("Conflicting evidence versions")
        refs[cid] = version
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "evidence_refs":
                for ref in objects(item, "evidence_refs"):
                    require_keys(ref, ("claim_id", "version"), context="evidence_ref")
                    cid = identifier(ref["claim_id"])
                    if type(ref["version"]) is not int or ref["version"] < 1:
                        raise EvidenceIntegrityError("Invalid evidence version")
                    put(cid, ref["version"])
            else:
                for cid, version in refs_in(item).items(): put(cid, version)
    elif isinstance(value, list):
        for item in value:
            for cid, version in refs_in(item).items(): put(cid, version)
    return refs

def validate_refs(refs, ledger, *, direct=False):
    for cid, version in refs.items():
        claim = ledger["claims"].get(cid)
        if not claim or claim["version"] != version or claim["status"] != "active":
            raise EvidenceIntegrityError(f"Evidence {cid}@{version} is missing, stale or candidate")
        if direct and (claim["inspection"] not in {"full_text", "official_document"} or claim["relation"] == "context"):
            raise EvidenceIntegrityError("Decisive overlap needs substantive inspected evidence")
        for ref in claim["source_refs"]:
            source = ledger["sources"].get(ref["source_id"])
            if not source or source["version"] != ref["version"] or source["verification"]["status"] != "verified":
                raise EvidenceIntegrityError(f"Source for {cid} is unverified or stale")

def validate_questions(value):
    ids = set()
    for q in objects(value, "questions"):
        require_keys(q, ("id", "question", "decision_impact"))
        identifier(q["id"])
        if q["id"] in ids: raise SubmissionError("Duplicate question ID")
        ids.add(q["id"])
        nonempty(q["question"], "question")
        nonempty(q["decision_impact"], "decision_impact")
    return ids

def validate_plan(p, line_count):
    require_keys(p, ("idea_claims", "boundaries", "maturity", "contribution_type", "constraints",
                     "working_assumptions", "review_questions"))
    if p["maturity"] not in {"early", "middle", "developed"}: raise SubmissionError("Invalid maturity")
    nonempty(p["contribution_type"], "contribution_type")
    for key in ("boundaries", "constraints"): strings(p[key], key)
    if not p["idea_claims"] or not p["review_questions"]: raise SubmissionError("Plan needs claims and questions")
    ids = set()
    for item in objects(p["idea_claims"], "idea_claims"):
        require_keys(item, ("id", "text", "input_locator"))
        identifier(item["id"])
        if item["id"] in ids: raise SubmissionError("Duplicate idea claim")
        ids.add(item["id"])
        nonempty(item["text"], "claim")
        input_locator(item["input_locator"], line_count)
    for a in objects(p["working_assumptions"], "working_assumptions"):
        require_keys(a, ("text", "consequence_if_wrong"))
        nonempty(a["text"], "assumption"); nonempty(a["consequence_if_wrong"], "consequence")
    validate_questions(p["review_questions"])

def validate_review(p, ledger, known_questions, line_count):
    require_keys(p, ("questions", "judgments", "closest_work", "decision", "stop"))
    qids = validate_questions(p["questions"])
    if not set(known_questions) <= qids: raise SubmissionError("Review must account for every planned/researched question")
    for q in p["questions"]:
        nonempty(q.get("outcome"), "question outcome")
        if q["id"] in known_questions and any(q[k] != known_questions[q["id"]][k] for k in ("question", "decision_impact")):
            raise SubmissionError("Cannot silently redefine researched question")
    ids, dimensions = set(), set()
    for j in objects(p["judgments"], "judgments"):
        require_keys(j, ("id", "dimension", "statement", "applicability", "basis", "evidence_refs",
                         "rationale", "strongest_counterargument", "uncertainty", "next_action"))
        identifier(j["id"])
        if j["id"] in ids or j["dimension"] not in DIMENSIONS: raise SubmissionError("Duplicate judgment/invalid dimension")
        ids.add(j["id"]); dimensions.add(j["dimension"])
        for k in ("statement", "rationale", "strongest_counterargument", "uncertainty", "next_action"): nonempty(j[k], k)
        if j["applicability"] not in {"assessable", "provisional", "not_yet_assessable", "not_applicable"}:
            raise SubmissionError("Invalid applicability")
        if j["basis"] not in {"literature", "researcher_input", "inference"}: raise SubmissionError("Invalid basis")
        if j["basis"] == "literature" and not refs_in(j): raise EvidenceIntegrityError("Literature judgment needs evidence")
        if j["basis"] == "researcher_input":
            if not j.get("input_locators"): raise ProvenanceIntegrityError("Input judgment needs locator")
            for loc in objects(j["input_locators"], "input_locators"): input_locator(loc, line_count)
    if dimensions != set(DIMENSIONS): raise SubmissionError("Account for all four dimensions")
    for work in objects(p["closest_work"], "closest_work"):
        require_keys(work, ("source_ref", "overlaps", "differences", "consequence", "evidence_refs"))
        require_keys(work["source_ref"], ("source_id", "version"))
        source = ledger["sources"].get(work["source_ref"]["source_id"])
        if not source or source["version"] != work["source_ref"]["version"]: raise EvidenceIntegrityError("Unknown closest source")
        if not refs_in(work): raise EvidenceIntegrityError("Closest comparison needs evidence")
        validate_refs(refs_in(work), ledger, direct=True)
        if not any(work["source_ref"] in ledger["claims"][cid]["source_refs"] for cid in refs_in(work)):
            raise EvidenceIntegrityError("Closest comparison must inspect the named source")
    d = p["decision"]
    require_keys(d, ("status", "rationale", "scope", "decisive_judgment_ids"))
    if d["status"] not in {"continue", "revise", "subsumed", "not_viable", "insufficient_evidence"}: raise SubmissionError("Invalid decision")
    strings(d["decisive_judgment_ids"], "decisive_judgment_ids")
    if not d["decisive_judgment_ids"] or not set(d["decisive_judgment_ids"]) <= ids: raise SubmissionError("Decision needs known judgments")
    nonempty(d["rationale"], "decision rationale"); nonempty(d["scope"], "decision scope")
    if d["status"] == "subsumed":
        decisive = [j for j in p["judgments"] if j["id"] in d["decisive_judgment_ids"]]
        if not p["closest_work"] or not refs_in(decisive): raise EvidenceIntegrityError("Subsumed needs closest-work evidence")
        validate_refs(refs_in(decisive), ledger, direct=True)
    require_keys(p["stop"], ("reason", "unresolved_question_ids", "coverage_limits"))
    if p["stop"]["reason"] not in {"decision_supported", "budget_exhausted", "retrieval_unavailable"}: raise SubmissionError("Invalid stop")
    strings(p["stop"]["unresolved_question_ids"], "unresolved questions")
    if not set(p["stop"]["unresolved_question_ids"]) <= qids: raise SubmissionError("Unknown unresolved question")
    strings(p["stop"]["coverage_limits"], "coverage limits")
    validate_refs(refs_in(p), ledger)

def validate_report(p, ledger, review, line_count):
    require_keys(p, ("language", "structured_idea", "assessment", "recommendations", "decision", "limitations"))
    if p["language"] not in {"zh", "en"}: raise SubmissionError("Report language must be zh or en")
    require_keys(p["structured_idea"], SECTIONS)
    for section in SECTIONS:
        items = objects(p["structured_idea"][section], section)
        if not items: raise ProvenanceIntegrityError("Section needs content or explicit missing item")
        for item in items:
            require_keys(item, ("text", "provenance", "input_locators", "evidence_refs"))
            nonempty(item["text"], "reconstruction text")
            provenance = item["provenance"]
            if provenance not in {"researcher_stated", "evidence_supported", "inferred", "missing"}: raise ProvenanceIntegrityError("Invalid provenance")
            for loc in objects(item["input_locators"], "input_locators"): input_locator(loc, line_count)
            if provenance == "researcher_stated" and not item["input_locators"]: raise ProvenanceIntegrityError("Original statement needs locator")
            if provenance == "evidence_supported" and not refs_in(item): raise ProvenanceIntegrityError("Evidence item needs reference")
            if provenance in {"missing", "inferred"} and refs_in(item): raise ProvenanceIntegrityError("Inference/missing cannot be relabelled evidence")
    judgments = {j["id"]: j for j in review["judgments"]}
    def block(b):
        require_keys(b, ("text", "judgment_ids", "evidence_refs"))
        nonempty(b["text"], "block")
        strings(b["judgment_ids"], "judgment_ids")
        if not set(b["judgment_ids"]) <= judgments.keys(): raise SubmissionError("Unknown judgment")
        required = refs_in([judgments[jid] for jid in b["judgment_ids"]])
        if not required.keys() <= refs_in(b).keys():
            raise EvidenceIntegrityError("Report block must retain its judgments' supporting and opposing evidence")
    dimensions = []
    for section in objects(p["assessment"], "assessment"):
        require_keys(section, ("dimension", "blocks"))
        dimensions.append(section["dimension"])
        if not section["blocks"]: raise SubmissionError("Empty assessment")
        for b in objects(section["blocks"], "blocks"):
            block(b)
            if not any(judgments[jid]["dimension"] == section["dimension"] for jid in b["judgment_ids"]):
                raise SubmissionError("Assessment block must identify a judgment in this dimension")
    if sorted(dimensions) != sorted(DIMENSIONS): raise SubmissionError("Cover four dimensions exactly once")
    for key in ("recommendations", "limitations"):
        for b in objects(p[key], key): block(b)
    block(p["decision"])
    if not p["decision"]["judgment_ids"]: raise SubmissionError("Decision needs judgment IDs")
    validate_refs(refs_in(p), ledger)
    if not set(refs_in(p)) <= set(refs_in(review)): raise EvidenceIntegrityError("Review new report evidence in s2 first")
