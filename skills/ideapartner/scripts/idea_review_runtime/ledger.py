"""Versioned evidence snapshots. Network verification is performed before commit."""
from __future__ import annotations
import copy
import hashlib
import json
from urllib.parse import urlsplit, urlunsplit
from .evidence import normalize_and_verify_source
from .validation import (EvidenceIntegrityError, SubmissionError, identifier, require_keys,
                         nonempty, objects, strings, validate_questions, validate_refs, refs_in)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

def empty_ledger():
    return {"sources": {}, "claims": {}, "questions": {}, "batches": {}, "aliases": {}, "cache": {}}

def source_key(source):
    ids = source.get("identifiers", {})
    if ids.get("doi"):
        key = "doi:" + ids["doi"].lower().removeprefix("https://doi.org/").removeprefix("http://doi.org/")
    elif ids.get("arxiv"):
        key = "arxiv:" + ids["arxiv"].removeprefix("arXiv:")
    else:
        parts = urlsplit(source.get("url") or "https://openalex.org/" + ids.get("openalex", ""))
        key = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))
    return key + "|" + str(source.get("edition", ""))

class CachedVerifier:
    def __init__(self, verifier, cache):
        self.verifier, self.cache, self.hits = verifier, cache, 0
    def verify(self, source):
        key = digest({k: v for k, v in source.items() if k not in {"source_id", "content_locator"}})
        if key in self.cache:
            self.hits += 1
            return copy.deepcopy(self.cache[key])
        result = self.verifier.verify(source)
        if result.get("status") == "verified": self.cache[key] = copy.deepcopy(result)
        return result

def prepare_batch(current, batch, verifier, known_questions):
    require_keys(batch, ("batch_id", "question_id", "decision_impact", "sources", "claims", "outcome"))
    bid = identifier(batch["batch_id"]); qid = identifier(batch["question_id"])
    nonempty(batch["decision_impact"], "decision_impact"); nonempty(batch["outcome"], "outcome")
    signature = digest(batch)
    if bid in current["batches"]:
        prior = current["batches"][bid]
        if prior["digest"] != signature: raise SubmissionError("Batch ID reused with different content")
        return copy.deepcopy(current), prior["result"], True
    ledger = copy.deepcopy(current)
    questions = {**ledger["questions"], **known_questions}
    if "question" in batch:
        validate_questions([batch["question"]])
        q = batch["question"]
        if q["id"] != qid: raise SubmissionError("Question ID mismatch")
        if qid in questions and any(q[k] != questions[qid][k] for k in ("question", "decision_impact")):
            raise SubmissionError("Cannot redefine an existing question")
        questions[qid] = q
    if qid not in questions: raise SubmissionError("Unknown question; provide its definition")
    ledger["questions"][qid] = questions[qid]
    cached = CachedVerifier(verifier, ledger["cache"])
    touched_sources, seen_sources = set(), set()
    for raw in objects(batch["sources"], "sources"):
        sid = identifier(raw.get("source_id"))
        if sid in seen_sources: raise SubmissionError("Duplicate batch source")
        seen_sources.add(sid)
        normalized = normalize_and_verify_source(raw, cached)
        normalized["edition"] = raw.get("edition", "")
        key = source_key(normalized)
        prior_id = ledger["aliases"].get(sid, sid)
        prior_source = ledger["sources"].get(prior_id)
        if prior_source and source_key(prior_source) != key:
            raise EvidenceIntegrityError("An existing source alias cannot change identity")
        existing = next((x for x in ledger["sources"].values() if source_key(x) == key), None)
        canonical = ledger["aliases"].get(sid, sid)
        if existing:
            canonical = existing["source_id"]
            for field in ("title", "authors", "year", "source_type"):
                if existing[field] != normalized[field] and sid != canonical:
                    raise EvidenceIntegrityError("Conflicting metadata for duplicate source identity")
        old = ledger["sources"].get(canonical)
        if old and source_key(old) != key: raise EvidenceIntegrityError("Source ID cannot change identity")
        ledger["aliases"][sid] = canonical
        normalized["source_id"] = canonical
        comparable = lambda x: {k: v for k, v in x.items() if k not in {"version", "verification"}}
        same = old and comparable(old) == comparable(normalized) and old["verification"]["status"] == normalized["verification"]["status"]
        if same: continue
        normalized["version"] = old["version"] + 1 if old else 1
        ledger["sources"][canonical] = normalized
        touched_sources.add(canonical)
    touched_claims, seen_claims = set(), set()
    for raw in objects(batch["claims"], "claims"):
        require_keys(raw, ("claim_id", "claim", "question_ids", "source_refs", "relation", "locator", "inspection", "limits"))
        cid = identifier(raw["claim_id"])
        if cid in seen_claims: raise SubmissionError("Duplicate batch claim")
        seen_claims.add(cid)
        nonempty(raw["claim"], "claim"); nonempty(raw["locator"], "locator")
        strings(raw["question_ids"], "question_ids")
        if qid not in raw["question_ids"] or not set(raw["question_ids"]) <= questions.keys():
            raise SubmissionError("Claim must link to known decision questions")
        if raw["relation"] not in {"support", "contradict", "context"}: raise SubmissionError("Invalid evidence relation")
        if raw["inspection"] not in {"full_text", "official_document", "abstract", "snippet"}: raise SubmissionError("Invalid inspection")
        if not isinstance(raw["limits"], str): raise SubmissionError("limits must be text")
        claim = copy.deepcopy(raw)
        if not claim["source_refs"]: raise EvidenceIntegrityError("Claim needs source")
        for ref in objects(claim["source_refs"], "source_refs"):
            require_keys(ref, ("source_id", "version"))
            ref["source_id"] = ledger["aliases"].get(ref["source_id"], ref["source_id"])
            source = ledger["sources"].get(ref["source_id"])
            if not source or type(ref["version"]) is not int or source["version"] != ref["version"]:
                raise EvidenceIntegrityError("Unknown or stale source version")
        old = ledger["claims"].get(cid)
        if old:
            if raw.get("expected_version") != old["version"]: raise EvidenceIntegrityError("Claim replacement needs expected_version")
        claim.pop("expected_version", None)
        claim["version"] = old["version"] + 1 if old else 1
        claim["status"] = "active" if all(ledger["sources"][r["source_id"]]["verification"]["status"] == "verified" for r in claim["source_refs"]) else "candidate"
        if claim["inspection"] == "snippet": claim["status"] = "candidate"
        ledger["claims"][cid] = claim; touched_claims.add(cid)
    # Source revisions invalidate dependent claims unless this batch refreshed them.
    for cid, claim in ledger["claims"].items():
        if cid not in touched_claims and any(r["source_id"] in touched_sources for r in claim["source_refs"]):
            claim["status"] = "candidate"
            touched_claims.add(cid)
    result = {"batch_id": bid, "accepted": sorted(c for c in seen_claims if ledger["claims"][c]["status"] == "active"),
              "candidates": sorted(c for c in seen_claims if ledger["claims"][c]["status"] == "candidate"),
              "rejected": [], "aliases": {s: ledger["aliases"][s] for s in seen_sources},
              "source_versions": {s: v["version"] for s, v in ledger["sources"].items()},
              "changed_claim_ids": sorted(touched_claims), "cache_hits": cached.hits}
    ledger["batches"][bid] = {"digest": signature, "question_id": qid, "outcome": batch["outcome"], "result": result}
    return ledger, result, False

def evidence_view(payload, ledger):
    refs = refs_in(payload)
    validate_refs(refs, ledger)
    claims = {cid: copy.deepcopy(ledger["claims"][cid]) for cid in refs}
    source_ids = {r["source_id"] for c in claims.values() for r in c["source_refs"]}
    return {"claims": claims, "sources": {sid: copy.deepcopy(ledger["sources"][sid]) for sid in source_ids}}
