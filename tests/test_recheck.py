import unittest
import tempfile
from pathlib import Path
from tests.helpers import FakeSourceVerifier, plan, review, report, submit, batch
from idea_review_runtime.pipeline import ReviewPipeline
from idea_review_runtime.artifacts import atomic_write_json
from idea_review_runtime.validation import PipelineError

class RecheckTests(unittest.TestCase):
    def test_bounded_recheck_then_report(self):
        with tempfile.TemporaryDirectory() as root:
            p=ReviewPipeline.create(Path(root),"Idea",run_id="recheck",source_verifier=FakeSourceVerifier())
            submit(p,"s1-plan",plan()); submit(p,"s2-review",review())
            packet=p.emit_task("s3-report")
            req={"task_id":"s3-report","packet_id":packet["packet_id"],"recheck_request":{
                "question_id":"q1","reason":"Inspect overlap","affected_judgment_ids":["j1"],"needed_evidence":"Method section"}}
            p.ingest("s3-report",req)
            self.assertEqual("RECHECKING",p.status()["state"])
            self.assertEqual({"recheck_requested":True},p.ingest("s3-report",req))
            submit(p,"s2-review",review())
            packet=p.emit_task("s3-report"); req["packet_id"]=packet["packet_id"]
            self.assertTrue(p.ingest("s3-report",req)["limit_reached"])
            p.ingest("s3-report",{"task_id":"s3-report","packet_id":packet["packet_id"],"payload":report()})
            self.assertEqual("FINALIZED",p.status()["state"])
    def test_expired_budget_does_not_block_qualified_completion(self):
        with tempfile.TemporaryDirectory() as root:
            p=ReviewPipeline.create(Path(root),"Idea",run_id="deadline",source_verifier=FakeSourceVerifier())
            submit(p,"s1-plan",plan()); p.emit_task("s2-review")
            m=p.manifest; m["budget"]["review_started_at"]="2000-01-01T00:00:00+00:00"
            atomic_write_json(p.manifest_path,m)
            packet=p.emit_task("s2-review")
            self.assertFalse(packet["research_allowed"])
            with self.assertRaises(PipelineError): p.add_evidence(batch())
            submit(p,"s2-review",review()); submit(p,"s3-report",report())
            self.assertEqual("FINALIZED",p.status()["state"])
