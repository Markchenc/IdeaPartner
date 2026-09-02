from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


SCRIPTS = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "ideapartner"
    / "scripts"
)
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class FakeSourceVerifier:
    def verify(self, source: dict[str, Any]) -> dict[str, Any]:
        verified = not source["source_id"].startswith("unverified-")
        return {
            "status": "verified" if verified else "unverified",
            "method": "fake-resolver",
            "checked_at": "2026-09-02T00:00:00+00:00",
            "resolved_url": source.get("url"),
            "detail": "test fixture",
        }


def submission(packet: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": packet["task_id"],
        "summary": f"Completed {packet['task_id']} for the test run.",
        "attention_items": [],
        "consumed_inputs": [
            {
                "artifact_id": item["artifact_id"],
                "artifact_version": item["artifact_version"],
                "used_for": f"Used to execute {packet['task_id']}",
            }
            for item in packet["inputs"]
        ],
        "payload": payload,
    }


def positioning_payload() -> dict[str, Any]:
    return {
        "domains": {"primary": "NLP", "related": ["HCI"], "adjacent": []},
        "scenario": {"track": "human-AI dialogue", "constraints": ["privacy"]},
        "research_object": {"core": "dialogue explanations", "scope": "multi-turn"},
        "core_difficulty": {"problem": "explanations are not faithful"},
        "contribution": {"primary_type": "new problem/framing", "claim": "situated faithfulness"},
        "maturity": {"level": "early", "rationale": "method is incomplete"},
        "control": {"confidence": "medium", "ambiguities": []},
    }


def route_payload() -> dict[str, Any]:
    return {
        "maturity": "early",
        "alignment_questions": ["Does the object match the scenario?"],
        "m3_scope": {"branches": ["faithfulness"], "evidence_norms_to_find": ["human validity"]},
        "m4_assessability": {"method_construction": "not_yet_assessable"},
        "review_lens_seed": {"primary_contribution": "new problem/framing"},
    }


def source(source_id: str = "paper-1") -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_type": "paper",
        "title": "A Real Research Paper",
        "authors": ["Researcher"],
        "year": 2025,
        "url": "https://example.org/paper",
        "identifiers": {"doi": "10.0000/example"},
    }


def prior_phase_payload(
    *, sources: list[dict[str, Any]] | None = None, claims: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    return {
        "scope": {"included": ["faithfulness"]},
        "queries": [{"query": "dialogue explanation faithfulness", "purpose": "closest work"}],
        "sources": sources or [],
        "evidence_claims": claims or [],
        "coverage": {"covered": ["seed branch"], "gaps": []},
    }


def prior_synthesis_payload(source_ids: list[str] | None = None) -> dict[str, Any]:
    ids = source_ids or []
    claims = []
    if ids:
        claims.append(
            {
                "claim_id": "claim-1",
                "claim": "Faithfulness remains contested.",
                "source_ids": ids,
                "relation": "support",
                "locator": "abstract",
            }
        )
    return {
        "evolution_tree": {"root": "explanation faithfulness", "branches": []},
        "field_map": {"foundation": [], "data": [], "frontier": []},
        "idea_attachment": {"relation": "redirects", "nodes": []},
        "closest_work": ids,
        "evidence_claims": claims,
        "coverage": {"sufficient_for": ["problem positioning"], "gaps": []},
        "repositioning": {"required": False, "reason": ""},
    }


def reconstruction_payload(evidence_claim_id: str | None = None) -> dict[str, Any]:
    supported = (
        {
            "text": "Prior work leaves a measurement gap.",
            "provenance": "evidence_supported",
            "evidence_claim_ids": [evidence_claim_id],
        }
        if evidence_claim_id
        else {
            "text": "The researcher reports a faithfulness gap.",
            "provenance": "researcher_stated",
            "evidence_claim_ids": [],
        }
    )
    missing = {
        "text": "Method details are not specified.",
        "provenance": "missing",
        "evidence_claim_ids": [],
    }
    return {
        "problem_definition": [supported],
        "limitations_and_core_difficulty": [supported],
        "contribution_design": [supported],
        "method_construction": [missing],
        "experimental_setting": [missing],
        "expected_difficulties": [supported],
    }


def review_payload(*, blocker: bool = False, direct_evidence_claim_ids: list[str] | None = None) -> dict[str, Any]:
    return {
        "review_lens": {
            "maturity": "early",
            "primary_contribution": "new problem/framing",
            "field_norms": ["construct validity"],
        },
        "judgments": [
            {
                "claim": "The problem is provisionally legitimate.",
                "status": "provisional",
                "provenance": "inferred",
                "evidence_claim_ids": [],
            }
        ],
        "conclusion": "provisional",
        "blocker": {
            "active": blocker,
            "scope": "current formulation" if blocker else "none",
            "reason": "Closest work subsumes the claim." if blocker else "",
            "direct_evidence_claim_ids": direct_evidence_claim_ids or [],
        },
    }
