from pathlib import Path
import sys
SCRIPTS = Path(__file__).resolve().parents[1] / "skills/ideapartner/scripts"
sys.path.insert(0, str(SCRIPTS))
from idea_review_runtime.validation import DIMENSIONS, SECTIONS

class FakeSourceVerifier:
    def __init__(self): self.calls = 0
    def verify(self, source):
        self.calls += 1
        return {"status": "unverified" if source["source_id"].startswith("unverified") else "verified",
                "method": "fake", "resolved_url": source.get("url")}

def question(qid="q1"):
    return {"id": qid, "question": "Has the contribution been covered?", "decision_impact": "Changes novelty decision"}

def plan():
    return {"idea_claims": [{"id": "i1", "text": "Study compositional generalization", "input_locator": {"start": 1, "end": 1}}],
            "boundaries": [], "maturity": "early", "contribution_type": "method", "constraints": [],
            "working_assumptions": [], "review_questions": [question()]}

def source(sid="s1"):
    return {"source_id": sid, "source_type": "paper", "title": "A Study of Generalization",
            "authors": ["A"], "year": 2025, "url": "https://example.org/paper",
            "identifiers": {"doi": "10.1234/example"}}

def batch(bid="b1", sid="s1", cid="e1", qid="q1"):
    return {"batch_id": bid, "question_id": qid, "decision_impact": "Assess overlap",
            "sources": [source(sid)], "claims": [{"claim_id": cid, "claim": "The paper covers this method",
            "question_ids": [qid], "source_refs": [{"source_id": sid, "version": 1}],
            "relation": "support", "locator": "Section 3", "inspection": "full_text", "limits": "Only this setting"}],
            "outcome": "Inspect the remaining contribution"}

def review(evidence=False, version=1):
    refs = [{"claim_id": "e1", "version": version}] if evidence else []
    return {"questions": [{**question(), "outcome": "Covered search remains incomplete", "evidence_refs": refs}],
            "judgments": [{"id": "j"+str(i), "dimension": d, "statement": "Provisional judgment",
            "applicability": "provisional", "basis": "literature" if evidence else "inference",
            "evidence_refs": refs, "rationale": "Available evidence is limited",
            "strongest_counterargument": "An adjacent contribution might differ", "uncertainty": "Coverage",
            "next_action": "Inspect a discriminating case"} for i,d in enumerate(DIMENSIONS)],
            "closest_work": [], "decision": {"status": "insufficient_evidence", "rationale": "Search incomplete",
            "scope": "Current contribution", "decisive_judgment_ids": ["j1"]},
            "stop": {"reason": "retrieval_unavailable", "unresolved_question_ids": ["q1"], "coverage_limits": ["Limited access"]}}

def report(evidence=False, version=1):
    def block(text="Current judgment", jid="j1"):
        return {"text": text, "judgment_ids": [jid],
                "evidence_refs": [{"claim_id": "e1", "version": version}] if evidence else []}
    return {"language": "zh", "structured_idea": {s: [{"text": "Not specified by researcher", "provenance": "missing",
            "input_locators": [], "evidence_refs": []}] for s in SECTIONS},
            "assessment": [{"dimension": d, "blocks": [block(jid="j"+str(i))]} for i,d in enumerate(DIMENSIONS)],
            "recommendations": [block("Run a minimal test")], "decision": block("Evidence is insufficient"),
            "limitations": [block("Retrieval incomplete")]}

def submit(pipeline, task, payload, **kwargs):
    packet = pipeline.emit_task(task, refresh=kwargs.get("replace", False))
    return pipeline.ingest(task, {"task_id": task, "packet_id": packet["packet_id"], "payload": payload}, **kwargs)
