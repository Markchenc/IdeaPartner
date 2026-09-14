import copy
import json
import tempfile
import unittest
from pathlib import Path
from tests.helpers import FakeSourceVerifier, plan, review, report, submit
from idea_review_runtime.pipeline import ReviewPipeline
from idea_review_runtime.validation import PipelineError, MissingDependency, StaleDependency

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.p = ReviewPipeline.create(Path(self.tmp.name), "Original idea", run_id="test", source_verifier=FakeSourceVerifier())
    def test_three_stages_finish_without_confirmation(self):
        self.assertEqual(["s1-plan"], self.p.status()["ready_tasks"])
        submit(self.p, "s1-plan", plan())
        self.assertEqual(["s2-review"], self.p.status()["ready_tasks"])
        submit(self.p, "s2-review", review())
        self.assertEqual(["s3-report"], self.p.status()["ready_tasks"])
        submit(self.p, "s3-report", report())
        self.assertEqual("FINALIZED", self.p.status()["state"])
        self.assertTrue(self.p.validate_run()["valid"])
        self.assertNotIn("checkpoints", self.p.manifest)
    def test_cannot_skip_review(self):
        submit(self.p, "s1-plan", plan())
        with self.assertRaises(MissingDependency): self.p.emit_task("s3-report")
    def test_changed_plan_rejects_old_review_packet(self):
        submit(self.p, "s1-plan", plan())
        packet = self.p.emit_task("s2-review")
        changed = plan(); changed["boundaries"] = ["Restricted setting"]
        submit(self.p, "s1-plan", changed, replace=True)
        with self.assertRaises(StaleDependency):
            self.p.ingest("s2-review", {"task_id":"s2-review", "packet_id":packet["packet_id"], "payload":review()})
    def test_submission_retries_are_idempotent(self):
        packet = self.p.emit_task("s1-plan")
        v = {"task_id":"s1-plan", "packet_id":packet["packet_id"], "payload":plan()}
        first = self.p.ingest("s1-plan", v)
        self.assertEqual(first, self.p.ingest("s1-plan", v))
        v["payload"]["boundaries"] = ["Changed"]
        with self.assertRaises(PipelineError): self.p.ingest("s1-plan", v)
    def test_legacy_read_only_and_unknown_schema(self):
        path = self.p.manifest_path
        old = {"schema_version":1, "state":"DOMAIN_PRIOR_SYNTHESIS", "run_id":"old", "exports":{}}
        path.write_text(json.dumps(old), encoding="utf-8")
        before = path.read_bytes()
        legacy = ReviewPipeline(self.p.run_dir)
        self.assertEqual([], legacy.status()["ready_tasks"])
        self.assertTrue(legacy.status()["legacy_read_only"])
        with self.assertRaises(PipelineError): legacy.emit_task("s1-plan")
        self.assertEqual(before, path.read_bytes())
        old["schema_version"] = 100; path.write_text(json.dumps(old))
        with self.assertRaises(PipelineError): ReviewPipeline(self.p.run_dir)
    def test_tampered_export_is_detected(self):
        submit(self.p,"s1-plan",plan()); submit(self.p,"s2-review",review()); submit(self.p,"s3-report",report())
        export = self.p.manifest["exports"]["final_report"]["path"]
        (self.p.run_dir/export).write_text("tampered",encoding="utf-8")
        self.assertFalse(self.p.validate_run()["valid"])
