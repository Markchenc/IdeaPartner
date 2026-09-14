import copy
import unittest
import tempfile
from pathlib import Path
from tests.helpers import FakeSourceVerifier
from idea_review_runtime.pipeline import ReviewPipeline
from tests.helpers import batch, plan, review, submit, question
from idea_review_runtime.validation import PipelineError, EvidenceIntegrityError
from idea_review_runtime.ledger import prepare_batch

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.p = ReviewPipeline.create(Path(self.tmp.name), 'Idea', run_id='ledger', source_verifier=FakeSourceVerifier())
        submit(self.p,"s1-plan",plan())
        self.p.emit_task("s2-review")
    def test_batch_replay_and_identity_cache(self):
        result = self.p.add_evidence(batch())
        self.assertEqual(result,self.p.add_evidence(batch()))
        calls = self.p.source_verifier.calls
        other = batch("b2","alias","e2")
        r = self.p.add_evidence(other)
        self.assertEqual("s1",r["aliases"]["alias"])
        self.assertEqual(calls,self.p.source_verifier.calls)
        bad = batch(); bad["outcome"] = "changed"
        with self.assertRaises(PipelineError): self.p.add_evidence(bad)
    def test_missing_question_rejects_without_commit(self):
        before = self.p.manifest
        b = batch(qid="unknown")
        with self.assertRaises(PipelineError): self.p.add_evidence(b)
        self.assertEqual(before,self.p.manifest)
    def test_candidate_cannot_support_review(self):
        result = self.p.add_evidence(batch(sid="unverified1"))
        self.assertEqual(["e1"],result["candidates"])
        with self.assertRaises(EvidenceIntegrityError): submit(self.p,"s2-review",review(True))
        submit(self.p,"s2-review",review())
    def test_unrelated_addition_not_stale_but_relevant_addition_is(self):
        self.p.add_evidence(batch()); submit(self.p,"s2-review",review(True))
        unrelated = batch("b2","s2","e2","q2"); unrelated["question"] = question("q2")
        self.p.add_evidence(unrelated)
        self.assertTrue(self.p.artifact_is_fresh("review"))
        self.assertTrue(self.p.validate_run()["valid"])
        related = batch("b3","s3","e3")
        self.p.add_evidence(related)
        self.assertFalse(self.p.artifact_is_fresh("review"))
    def test_revision_requires_expected_version(self):
        self.p.add_evidence(batch())
        b = batch("b2"); b["claims"][0]["claim"] = "Corrected"
        with self.assertRaises(EvidenceIntegrityError): self.p.add_evidence(b)
        b["claims"][0]["expected_version"] = 1
        self.p.add_evidence(b)
        with self.assertRaises(EvidenceIntegrityError): submit(self.p,"s2-review",review(True))
        submit(self.p,"s2-review",review(True,2))
    def test_verification_conflict_is_retryable(self):
        base = self.p.manifest
        class MutatingVerifier:
            def verify(_, source):
                self.p.add_evidence({**batch("other"),"sources":[],"claims":[]})
                return {"status":"verified"}
        self.p.source_verifier = MutatingVerifier()
        with self.assertRaises(PipelineError): self.p.add_evidence(batch())
        self.assertEqual(base["evidence_revision"]+1,self.p.manifest["evidence_revision"])

    def test_subsumed_cannot_rely_on_abstract_only(self):
        b = batch(); b["claims"][0]["inspection"] = "abstract"
        self.p.add_evidence(b)
        r = review(True)
        r["decision"]["status"] = "subsumed"
        r["closest_work"] = [{"source_ref": {"source_id":"s1", "version":1},
                              "overlaps":"method", "differences":"unclear", "consequence":"subsumed",
                              "evidence_refs":[{"claim_id":"e1","version":1}]}]
        with self.assertRaises(EvidenceIntegrityError): submit(self.p,"s2-review",r)

    def test_source_alias_cannot_be_rebound(self):
        self.p.add_evidence(batch())
        other = batch("b2", "s2", "e2")
        other["sources"][0]["identifiers"]["doi"] = "10.1234/another"
        self.p.add_evidence(other)
        rebound = batch("b3", "s1", "e3")
        rebound["sources"][0]["identifiers"]["doi"] = "10.1234/another"
        with self.assertRaises(EvidenceIntegrityError): self.p.add_evidence(rebound)
