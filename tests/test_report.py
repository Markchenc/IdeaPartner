import unittest
import tempfile
from pathlib import Path
from tests.helpers import FakeSourceVerifier, plan, review, report, submit, batch
from idea_review_runtime.pipeline import ReviewPipeline
from idea_review_runtime.validation import PipelineError

class ReportTests(unittest.TestCase):
    def test_missing_section_and_invented_original_statement_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            p=ReviewPipeline.create(Path(root),"Idea",run_id="report",source_verifier=FakeSourceVerifier())
            submit(p,"s1-plan",plan()); submit(p,"s2-review",review())
            r=report(); del r["structured_idea"]["method_construction"]
            with self.assertRaises(PipelineError): submit(p,"s3-report",r)
            r=report(); r["structured_idea"]["method_construction"][0]["provenance"]="researcher_stated"
            with self.assertRaises(PipelineError): submit(p,"s3-report",r)
            submit(p,"s3-report",report())
            self.assertEqual(1,(p.run_dir/"final-report.md").read_text(encoding="utf-8").count("## 结论"))
    def test_citations_render_and_stale_claims_cannot_be_used(self):
        with tempfile.TemporaryDirectory() as root:
            p=ReviewPipeline.create(Path(root),"Idea",run_id="citation",source_verifier=FakeSourceVerifier())
            submit(p,"s1-plan",plan()); p.emit_task("s2-review"); p.add_evidence(batch())
            submit(p,"s2-review",review(True))
            r=report(True); r["decision"]["evidence_refs"][0]["version"]=2
            with self.assertRaises(PipelineError): submit(p,"s3-report",r)
            submit(p,"s3-report",report(True))
            rendered=(p.run_dir/"final-report.md").read_text(encoding="utf-8")
            self.assertIn("https://example.org/paper",rendered)
            self.assertIn("Section 3",rendered)

    def test_report_cannot_drop_judgment_evidence(self):
        with tempfile.TemporaryDirectory() as root:
            p=ReviewPipeline.create(Path(root),"Idea",run_id="retain",source_verifier=FakeSourceVerifier())
            submit(p,"s1-plan",plan()); p.emit_task("s2-review"); p.add_evidence(batch())
            counter=batch("b2","s2","e2"); counter["claims"][0]["relation"]="contradict"
            p.add_evidence(counter)
            r=review(True)
            r["judgments"][1]["evidence_refs"].append({"claim_id":"e2","version":1})
            submit(p,"s2-review",r)
            with self.assertRaises(PipelineError): submit(p,"s3-report",report(True))
