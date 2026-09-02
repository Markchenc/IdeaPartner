from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

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
from idea_review_runtime.pipeline import (
    CheckpointRequired,
    MissingDependency,
    ReviewPipeline,
)


class PipelineDependencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.pipeline = ReviewPipeline.create(
            Path(self.tempdir.name),
            "Study whether situated explanations improve faithful human-AI dialogue.",
            run_id="test-run",
            source_verifier=FakeSourceVerifier(),
        )

    def ingest(self, task_id: str, payload: dict, *, replace: bool = False) -> None:
        packet = self.pipeline.emit_task(task_id, refresh=replace)
        self.pipeline.ingest(task_id, submission(packet, payload), replace=replace)

    def complete_through_m3(self) -> None:
        self.ingest("m1-positioning", positioning_payload())
        self.pipeline.confirm_positioning("confirmed by test")
        self.ingest("m2-route", route_payload())
        self.ingest("m3-foundation", prior_phase_payload(sources=[source("paper-1")]))
        self.ingest("m3-data", prior_phase_payload())
        self.ingest("m3-frontier", prior_phase_payload())
        self.ingest("m3-synthesis", prior_synthesis_payload(["paper-1"]))

    def test_checkpoint_blocks_m2_until_positioning_is_confirmed(self) -> None:
        self.ingest("m1-positioning", positioning_payload())

        with self.assertRaises(CheckpointRequired):
            self.pipeline.emit_task("m2-route")

        self.pipeline.confirm_positioning("The positioning reflects my intent.")
        packet = self.pipeline.emit_task("m2-route")
        self.assertEqual("m2-route", packet["task_id"])

    def test_m4_requires_explicit_m1_m2_and_synthesized_m3(self) -> None:
        self.ingest("m1-positioning", positioning_payload())
        self.pipeline.confirm_positioning("confirmed")
        self.ingest("m2-route", route_payload())

        with self.assertRaises(MissingDependency):
            self.pipeline.emit_task("m4-reconstruction")

        self.ingest("m3-foundation", prior_phase_payload(sources=[source("paper-1")]))
        self.ingest("m3-data", prior_phase_payload())
        self.ingest("m3-frontier", prior_phase_payload())
        self.ingest("m3-synthesis", prior_synthesis_payload(["paper-1"]))
        packet = self.pipeline.emit_task("m4-reconstruction")

        self.assertEqual(
            ["m0-input", "m1-positioning", "m2-route", "m3-synthesis"],
            [item["artifact_id"] for item in packet["inputs"]],
        )

    def test_replacing_upstream_artifact_marks_downstream_stale(self) -> None:
        self.complete_through_m3()
        self.ingest("m4-reconstruction", reconstruction_payload("claim-1"))
        self.assertTrue(self.pipeline.artifact_is_fresh("m4-reconstruction"))

        changed_route = route_payload()
        changed_route["alignment_questions"].append("Is the method compatible with privacy constraints?")
        self.ingest("m2-route", changed_route, replace=True)

        self.assertFalse(self.pipeline.artifact_is_fresh("m3-synthesis"))
        self.assertFalse(self.pipeline.artifact_is_fresh("m4-reconstruction"))
        with self.assertRaises(MissingDependency):
            self.pipeline.emit_task("m5-a")

    def test_evidence_triggered_repositioning_creates_a_second_checkpoint(self) -> None:
        self.ingest("m1-positioning", positioning_payload())
        self.pipeline.confirm_positioning("confirmed")
        self.ingest("m2-route", route_payload())
        self.ingest("m3-foundation", prior_phase_payload(sources=[source("paper-1")]))
        self.ingest("m3-data", prior_phase_payload())
        self.ingest("m3-frontier", prior_phase_payload())
        synthesis = prior_synthesis_payload(["paper-1"])
        synthesis["repositioning"] = {
            "required": True,
            "reason": "The closest work places the idea in HCI rather than NLP.",
            "proposed_change": {"primary_domain": "HCI"},
        }
        self.ingest("m3-synthesis", synthesis)

        with self.assertRaises(CheckpointRequired):
            self.pipeline.emit_task("m4-reconstruction")

        self.pipeline.confirm_post_m3("Researcher accepts the revised positioning.")
        packet = self.pipeline.emit_task("m4-reconstruction")
        self.assertEqual("m4-reconstruction", packet["task_id"])

    def test_every_m4_to_m7_packet_carries_m1_m2_and_m3(self) -> None:
        self.complete_through_m3()
        self.ingest("m4-reconstruction", reconstruction_payload("claim-1"))

        for task_id in ("m5-a", "m5-b"):
            packet = self.pipeline.emit_task(task_id)
            self.assertTrue(
                {"m1-positioning", "m2-route", "m3-synthesis"}.issubset(
                    {item["artifact_id"] for item in packet["inputs"]}
                )
            )
            self.pipeline.ingest(task_id, submission(packet, review_payload()))

        for task_id in ("m5-c", "m5-d"):
            packet = self.pipeline.emit_task(task_id)
            self.assertTrue(
                {"m1-positioning", "m2-route", "m3-synthesis"}.issubset(
                    {item["artifact_id"] for item in packet["inputs"]}
                )
            )
            self.pipeline.ingest(task_id, submission(packet, review_payload()))

        m6_packet = self.pipeline.emit_task("m6-challenge")
        self.assertTrue(
            {"m1-positioning", "m2-route", "m3-synthesis"}.issubset(
                {item["artifact_id"] for item in m6_packet["inputs"]}
            )
        )
        self.pipeline.ingest(
            "m6-challenge",
            submission(m6_packet, {"selected_challenges": [], "updates": []}),
        )

        m7_packet = self.pipeline.emit_task("m7-synthesis")
        self.assertTrue(
            {"m1-positioning", "m2-route", "m3-synthesis"}.issubset(
                {item["artifact_id"] for item in m7_packet["inputs"]}
            )
        )
        self.pipeline.ingest(
            "m7-synthesis",
            submission(
                m7_packet,
                {
                    "report_markdown": "# Review\n\nWorth continuing with reframing.",
                    "conclusion": "promising but needs reframing",
                    "citation_claim_ids": ["claim-1"],
                },
            ),
        )

        self.assertEqual("FINALIZED", self.pipeline.compute_state())
        self.assertTrue((self.pipeline.run_dir / "07-final-report.md").is_file())
        self.assertTrue(self.pipeline.validate_run()["valid"])


if __name__ == "__main__":
    unittest.main()
