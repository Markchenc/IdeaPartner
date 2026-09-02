from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.helpers import (
    FakeSourceVerifier,
    positioning_payload,
    prior_phase_payload,
    prior_synthesis_payload,
    reconstruction_payload,
    review_payload,
    route_payload,
    source,
    submission,
)
from idea_review_runtime.pipeline import ReviewPipeline
from idea_review_runtime.evidence import LiveSourceVerifier
from idea_review_runtime.validation import EvidenceIntegrityError, ProvenanceIntegrityError


class EvidenceAndProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.pipeline = ReviewPipeline.create(
            Path(self.tempdir.name),
            "Study situated explanations in dialogue.",
            run_id="evidence-run",
            source_verifier=FakeSourceVerifier(),
        )
        self._ingest("m1-positioning", positioning_payload())
        self.pipeline.confirm_positioning("confirmed")
        self._ingest("m2-route", route_payload())

    def _ingest(self, task_id: str, payload: dict) -> None:
        packet = self.pipeline.emit_task(task_id)
        self.pipeline.ingest(task_id, submission(packet, payload))

    def _complete_prior(self) -> None:
        self._ingest("m3-foundation", prior_phase_payload(sources=[source("paper-1")]))
        self._ingest("m3-data", prior_phase_payload())
        self._ingest("m3-frontier", prior_phase_payload())
        self._ingest("m3-synthesis", prior_synthesis_payload(["paper-1"]))

    def test_unverified_source_cannot_support_a_domain_prior_claim(self) -> None:
        bad_source = source("unverified-paper")
        payload = prior_phase_payload(
            sources=[bad_source],
            claims=[
                {
                    "claim_id": "bad-claim",
                    "claim": "This source proves the gap.",
                    "source_ids": ["unverified-paper"],
                    "relation": "support",
                    "locator": "page 1",
                }
            ],
        )
        packet = self.pipeline.emit_task("m3-foundation")

        with self.assertRaises(EvidenceIntegrityError):
            self.pipeline.ingest("m3-foundation", submission(packet, payload))

    def test_worker_cannot_self_declare_source_verification(self) -> None:
        claimed_verified = source("unverified-paper")
        claimed_verified["verification"] = {"status": "verified", "method": "worker-claim"}
        packet = self.pipeline.emit_task("m3-foundation")
        artifact_path = self.pipeline.ingest(
            "m3-foundation",
            submission(packet, prior_phase_payload(sources=[claimed_verified])),
        )

        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        verification = artifact["payload"]["sources"][0]["verification"]
        self.assertEqual("unverified", verification["status"])
        self.assertEqual("fake-resolver", verification["method"])

    def test_unknown_source_type_cannot_bypass_identity_policy(self) -> None:
        disguised_paper = source("paper-with-arbitrary-type")
        disguised_paper["source_type"] = "web_page_that_should_be_treated_as_verified"
        packet = self.pipeline.emit_task("m3-foundation")

        with self.assertRaises(EvidenceIntegrityError):
            self.pipeline.ingest(
                "m3-foundation",
                submission(packet, prior_phase_payload(sources=[disguised_paper])),
            )

    @patch(
        "idea_review_runtime.evidence._http_text",
        return_value=("<html><title>An Unrelated Resource</title></html>", "https://example.org/resource"),
    )
    def test_allowed_nonpaper_type_still_requires_matching_url_identity(self, _mock_http) -> None:
        record = source("misclassified-paper")
        record["source_type"] = "official_docs"
        record["identifiers"] = {}
        result = LiveSourceVerifier().verify(record)

        self.assertEqual("metadata_mismatch", result["status"])

    def test_synthesis_cannot_cite_an_unregistered_source(self) -> None:
        self._ingest("m3-foundation", prior_phase_payload(sources=[source("paper-1")]))
        self._ingest("m3-data", prior_phase_payload())
        self._ingest("m3-frontier", prior_phase_payload())
        packet = self.pipeline.emit_task("m3-synthesis")

        with self.assertRaises(EvidenceIntegrityError):
            self.pipeline.ingest(
                "m3-synthesis",
                submission(packet, prior_synthesis_payload(["invented-paper"])),
            )

    def test_m4_evidence_supported_content_requires_verified_source(self) -> None:
        self._complete_prior()
        payload = reconstruction_payload()
        payload["method_construction"] = [
            {
                "text": "The method uses a special causal module.",
                "provenance": "evidence_supported",
                "evidence_claim_ids": [],
            }
        ]
        packet = self.pipeline.emit_task("m4-reconstruction")

        with self.assertRaises(ProvenanceIntegrityError):
            self.pipeline.ingest("m4-reconstruction", submission(packet, payload))

    def test_inferred_content_cannot_carry_evidence_ids(self) -> None:
        self._complete_prior()
        payload = reconstruction_payload()
        payload["method_construction"] = [
            {
                "text": "A causal module may be intended.",
                "provenance": "inferred",
                "evidence_claim_ids": ["claim-1"],
            }
        ]
        packet = self.pipeline.emit_task("m4-reconstruction")

        with self.assertRaises(ProvenanceIntegrityError):
            self.pipeline.ingest("m4-reconstruction", submission(packet, payload))

    def test_active_m5_blocker_requires_direct_verified_evidence(self) -> None:
        self._complete_prior()
        self._ingest("m4-reconstruction", reconstruction_payload("claim-1"))
        packet = self.pipeline.emit_task("m5-a")

        with self.assertRaises(EvidenceIntegrityError):
            self.pipeline.ingest("m5-a", submission(packet, review_payload(blocker=True)))


if __name__ == "__main__":
    unittest.main()
