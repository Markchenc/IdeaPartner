import json
import multiprocessing
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tests.helpers import FakeSourceVerifier, plan, review, report, batch, submit
from idea_review_runtime.pipeline import ReviewPipeline
from idea_review_runtime.validation import PipelineError
from idea_review_runtime.artifacts import atomic_write_json

def add_worker(run, bid, start, output):
    try:
        p=ReviewPipeline(Path(run),source_verifier=FakeSourceVerifier())
        start.wait(10)
        value=batch(bid,cid="e"+bid)
        for attempt in range(5):
            try:
                p.add_evidence(value)
                output.put(None)
                return
            except PipelineError:
                if attempt == 4: raise
    except Exception as error: output.put(str(error))

class FailureTests(unittest.TestCase):
    def test_concurrent_evidence_batches_do_not_lose_updates(self):
        with tempfile.TemporaryDirectory() as root:
            p=ReviewPipeline.create(Path(root),"Idea",run_id="concurrent",source_verifier=FakeSourceVerifier())
            submit(p,"s1-plan",plan()); p.emit_task("s2-review")
            context=multiprocessing.get_context("spawn")
            start=context.Event(); output=context.Queue()
            workers=[context.Process(target=add_worker,args=(str(p.run_dir),str(i),start,output)) for i in range(2)]
            try:
                for w in workers: w.start()
                start.set()
                for w in workers:
                    w.join(20)
                    self.assertFalse(w.is_alive())
                    self.assertEqual(0,w.exitcode)
                self.assertEqual([None,None],[output.get(timeout=5) for _ in workers])
                m=p.manifest; ledger=json.loads((p.run_dir/m["evidence_snapshot"]).read_text(encoding="utf-8"))
                self.assertEqual({"0","1"},set(ledger["batches"]))
            finally:
                for w in workers:
                    if w.is_alive(): w.terminate(); w.join()
                output.close()
    def test_failed_commit_keeps_manifest_and_can_retry(self):
        with tempfile.TemporaryDirectory() as root:
            p=ReviewPipeline.create(Path(root),"Idea",run_id="failure",source_verifier=FakeSourceVerifier())
            packet=p.emit_task("s1-plan")
            value={"task_id":"s1-plan","packet_id":packet["packet_id"],"payload":plan()}
            before=p.manifest_path.read_bytes()
            def fail_manifest(path, value):
                if Path(path).name == "manifest.json": raise OSError("simulated disk failure")
                atomic_write_json(path,value)
            with patch("idea_review_runtime.pipeline.atomic_write_json",side_effect=fail_manifest):
                with self.assertRaises(OSError): p.ingest("s1-plan",value)
            self.assertEqual(before,p.manifest_path.read_bytes())
            self.assertEqual("PLANNING",p.status()["state"])
            p.ingest("s1-plan",value)
            self.assertEqual("REVIEWING",p.status()["state"])
    def test_wrong_packet_cannot_cross_runs(self):
        with tempfile.TemporaryDirectory() as root:
            p=ReviewPipeline.create(Path(root),"Idea",run_id="a")
            other=ReviewPipeline.create(Path(root),"Idea",run_id="b")
            packet=p.emit_task("s1-plan")
            with self.assertRaises(PipelineError):
                other.ingest("s1-plan",{"task_id":"s1-plan","packet_id":packet["packet_id"],"payload":plan()})
