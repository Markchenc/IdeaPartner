import unittest
import tempfile
from pathlib import Path
from tests.helpers import FakeSourceVerifier, plan, review, batch, submit
from idea_review_runtime.pipeline import ReviewPipeline
from idea_review_runtime.artifacts import read_json

class PacketTests(unittest.TestCase):
    def test_only_used_evidence_including_counterevidence_is_forwarded(self):
        with tempfile.TemporaryDirectory() as root:
            p = ReviewPipeline.create(Path(root),"Idea",run_id="packets",source_verifier=FakeSourceVerifier())
            submit(p,"s1-plan",plan()); p.emit_task("s2-review")
            p.add_evidence(batch())
            counter = batch("b2","s2","e2"); counter["claims"][0]["relation"]="contradict"; p.add_evidence(counter)
            unused = batch("b3","s3","e3"); unused["claims"][0]["claim"]="x"*10000; p.add_evidence(unused)
            r = review(True); r["judgments"][0]["evidence_refs"].append({"claim_id":"e2","version":1})
            submit(p,"s2-review",r)
            packet = p.emit_task("s3-report")
            view = read_json(Path(packet["evidence_view"]))
            self.assertEqual({"e1","e2"},set(view["claims"]))
            self.assertNotIn("evidence_snapshot",packet)
            self.assertNotIn("consumed_inputs",packet)
