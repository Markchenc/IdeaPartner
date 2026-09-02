from __future__ import annotations

from typing import Any, Iterable, Mapping


class PipelineError(RuntimeError):
    """Base error for an invalid pipeline operation."""


class RunNotFound(PipelineError):
    pass


class MissingDependency(PipelineError):
    pass


class StaleDependency(MissingDependency):
    pass


class CheckpointRequired(PipelineError):
    pass


class TaskAlreadyComplete(PipelineError):
    pass


class SubmissionError(PipelineError):
    pass


class EvidenceIntegrityError(SubmissionError):
    pass


class ProvenanceIntegrityError(SubmissionError):
    pass


PROVENANCE_STATES = {
    "researcher_stated",
    "evidence_supported",
    "inferred",
    "missing",
}


def require_keys(payload: Mapping[str, Any], required: Iterable[str], *, context: str) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise SubmissionError(f"{context} is missing required payload keys: {', '.join(missing)}")


def validate_consumed_inputs(
    consumed: Any,
    expected: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(consumed, list):
        raise SubmissionError("consumed_inputs must be a list")
    expected_by_id = {item["artifact_id"]: item for item in expected}
    actual_by_id: dict[str, dict[str, Any]] = {}
    for item in consumed:
        if not isinstance(item, dict):
            raise SubmissionError("Every consumed input must be an object")
        artifact_id = item.get("artifact_id")
        if not isinstance(artifact_id, str) or artifact_id in actual_by_id:
            raise SubmissionError("Every consumed input must have one unique artifact_id")
        actual_by_id[artifact_id] = item

    if set(actual_by_id) != set(expected_by_id):
        missing = sorted(set(expected_by_id) - set(actual_by_id))
        extra = sorted(set(actual_by_id) - set(expected_by_id))
        raise SubmissionError(f"Input acknowledgement mismatch; missing={missing}, extra={extra}")

    normalized = []
    for artifact_id, expected_item in expected_by_id.items():
        actual = actual_by_id[artifact_id]
        if actual.get("artifact_version") != expected_item["artifact_version"]:
            raise SubmissionError(f"Version mismatch for consumed input {artifact_id}")
        used_for = actual.get("used_for")
        if not isinstance(used_for, str) or not used_for.strip():
            raise SubmissionError(f"consumed input {artifact_id} must explain how it was used")
        if used_for.strip().startswith("REPLACE_WITH_"):
            raise SubmissionError(f"consumed input {artifact_id} still contains the acknowledgement placeholder")
        normalized.append(
            {
                "artifact_id": artifact_id,
                "path": expected_item["relative_path"],
                "artifact_version": expected_item["artifact_version"],
                "used_for": used_for.strip(),
            }
        )
    return normalized


def _require_verified_source_ids(
    source_ids: Any,
    ledger: Mapping[str, dict[str, Any]],
    *,
    context: str,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(source_ids, list) or any(not isinstance(item, str) for item in source_ids):
        raise EvidenceIntegrityError(f"{context} source_ids must be a list of strings")
    if not source_ids and not allow_empty:
        raise EvidenceIntegrityError(f"{context} requires at least one verified source")
    for source_id in source_ids:
        if source_id not in ledger:
            raise EvidenceIntegrityError(f"{context} cites unregistered source {source_id}")
        verification = ledger[source_id].get("verification", {})
        if verification.get("status") != "verified":
            raise EvidenceIntegrityError(f"{context} cites source {source_id}, which is not verified")
    return source_ids


def validate_evidence_claims(
    claims: Any,
    ledger: Mapping[str, dict[str, Any]],
    *,
    context: str,
) -> None:
    if not isinstance(claims, list):
        raise EvidenceIntegrityError(f"{context} evidence_claims must be a list")
    claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        location = f"{context} evidence_claims[{index}]"
        if not isinstance(claim, dict):
            raise EvidenceIntegrityError(f"{location} must be an object")
        require_keys(claim, ("claim_id", "claim", "source_ids", "relation", "locator"), context=location)
        claim_id = claim["claim_id"]
        if not isinstance(claim_id, str) or not claim_id or claim_id in claim_ids:
            raise EvidenceIntegrityError(f"{location} must have one unique non-empty claim_id")
        claim_ids.add(claim_id)
        if not isinstance(claim["claim"], str) or not claim["claim"].strip():
            raise EvidenceIntegrityError(f"{location} must contain a non-empty claim")
        if claim["relation"] not in {"support", "contradict", "context"}:
            raise EvidenceIntegrityError(f"{location} has an invalid relation")
        if not isinstance(claim["locator"], str) or not claim["locator"].strip():
            raise EvidenceIntegrityError(f"{location} requires a page, section, figure, or other locator")
        _require_verified_source_ids(claim["source_ids"], ledger, context=location)


def evidence_claim_ledger(claims: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(claims, list):
        raise EvidenceIntegrityError("Canonical M3 evidence_claims must be a list")
    ledger: dict[str, dict[str, Any]] = {}
    for claim in claims:
        if not isinstance(claim, dict) or not isinstance(claim.get("claim_id"), str):
            raise EvidenceIntegrityError("Canonical M3 evidence claim is malformed")
        claim_id = claim["claim_id"]
        if claim_id in ledger:
            raise EvidenceIntegrityError(f"Duplicate canonical evidence claim {claim_id}")
        ledger[claim_id] = claim
    return ledger


def _require_registered_claim_ids(
    claim_ids: Any,
    ledger: Mapping[str, dict[str, Any]],
    *,
    context: str,
    allow_empty: bool = False,
    substantive: bool = False,
) -> list[str]:
    if not isinstance(claim_ids, list) or any(not isinstance(item, str) for item in claim_ids):
        raise EvidenceIntegrityError(f"{context} evidence_claim_ids must be a list of strings")
    if not claim_ids and not allow_empty:
        raise EvidenceIntegrityError(f"{context} requires at least one registered M3 evidence claim")
    for claim_id in claim_ids:
        if claim_id not in ledger:
            raise EvidenceIntegrityError(f"{context} cites unregistered M3 evidence claim {claim_id}")
        if substantive and ledger[claim_id].get("relation") == "context":
            raise EvidenceIntegrityError(
                f"{context} cites contextual claim {claim_id}; supporting or contradicting evidence is required"
            )
    return claim_ids


def validate_provenance_sections(
    payload: Mapping[str, Any],
    sections: Iterable[str],
    claim_ledger: Mapping[str, dict[str, Any]],
) -> None:
    for section in sections:
        items = payload.get(section)
        if not isinstance(items, list):
            raise ProvenanceIntegrityError(f"{section} must be a list of provenance-tagged items")
        for index, item in enumerate(items):
            context = f"{section}[{index}]"
            if not isinstance(item, dict):
                raise ProvenanceIntegrityError(f"{context} must be an object")
            require_keys(item, ("text", "provenance", "evidence_claim_ids"), context=context)
            provenance = item["provenance"]
            if provenance not in PROVENANCE_STATES:
                raise ProvenanceIntegrityError(f"{context} has invalid provenance {provenance!r}")
            claim_ids = item["evidence_claim_ids"]
            if provenance == "evidence_supported":
                try:
                    _require_registered_claim_ids(
                        claim_ids, claim_ledger, context=context, substantive=True
                    )
                except EvidenceIntegrityError as error:
                    raise ProvenanceIntegrityError(str(error)) from error
            elif claim_ids != []:
                raise ProvenanceIntegrityError(
                    f"{context} is {provenance}; only evidence_supported content may carry evidence_claim_ids"
                )


def validate_review_payload(
    payload: Mapping[str, Any],
    claim_ledger: Mapping[str, dict[str, Any]],
    *,
    context: str,
) -> None:
    judgments = payload.get("judgments")
    if not isinstance(judgments, list):
        raise SubmissionError(f"{context} judgments must be a list")
    for index, judgment in enumerate(judgments):
        location = f"{context} judgments[{index}]"
        if not isinstance(judgment, dict):
            raise SubmissionError(f"{location} must be an object")
        require_keys(
            judgment,
            ("claim", "status", "provenance", "evidence_claim_ids"),
            context=location,
        )
        provenance = judgment["provenance"]
        if provenance not in PROVENANCE_STATES:
            raise ProvenanceIntegrityError(f"{location} has invalid provenance {provenance!r}")
        claim_ids = judgment["evidence_claim_ids"]
        if provenance == "evidence_supported":
            _require_registered_claim_ids(
                claim_ids, claim_ledger, context=location, substantive=True
            )
        elif claim_ids != []:
            raise ProvenanceIntegrityError(
                f"{location} is {provenance}; only evidence_supported judgments may carry evidence_claim_ids"
            )

    blocker = payload.get("blocker")
    if not isinstance(blocker, dict) or not isinstance(blocker.get("active"), bool):
        raise SubmissionError(f"{context} blocker must contain an active boolean")
    direct_ids = blocker.get("direct_evidence_claim_ids")
    if blocker["active"]:
        _require_registered_claim_ids(
            direct_ids, claim_ledger, context=f"{context} blocker", substantive=True
        )
        if not isinstance(blocker.get("scope"), str) or not blocker["scope"].strip():
            raise SubmissionError(f"{context} active blocker requires a scope")
        if not isinstance(blocker.get("reason"), str) or not blocker["reason"].strip():
            raise SubmissionError(f"{context} active blocker requires a reason")
    elif direct_ids not in ([], None):
        _require_registered_claim_ids(direct_ids, claim_ledger, context=f"{context} blocker", allow_empty=True)


def validate_optional_evidence_claim_ids(
    records: Any,
    claim_ledger: Mapping[str, dict[str, Any]],
    *,
    context: str,
) -> None:
    if not isinstance(records, list):
        raise SubmissionError(f"{context} must be a list")
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise SubmissionError(f"{context}[{index}] must be an object")
        if "evidence_claim_ids" in record:
            _require_registered_claim_ids(
                record["evidence_claim_ids"],
                claim_ledger,
                context=f"{context}[{index}]",
                allow_empty=True,
            )


def validate_citation_claim_ids(
    claim_ids: Any,
    claim_ledger: Mapping[str, dict[str, Any]],
    *,
    context: str,
) -> None:
    _require_registered_claim_ids(claim_ids, claim_ledger, context=context, allow_empty=True)


def validate_source_ids(source_ids: Any, ledger: Mapping[str, dict[str, Any]], *, context: str) -> None:
    _require_verified_source_ids(source_ids, ledger, context=context, allow_empty=True)
