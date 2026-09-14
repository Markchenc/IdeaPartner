import unittest
from unittest.mock import patch
from tests.helpers import FakeSourceVerifier, source
from idea_review_runtime.evidence import normalize_and_verify_source, LiveSourceVerifier
from idea_review_runtime.validation import EvidenceIntegrityError

class EvidenceTests(unittest.TestCase):
    def test_worker_verification_is_ignored(self):
        s = source("unverified1"); s["verification"] = {"status":"verified"}
        self.assertEqual("unverified", normalize_and_verify_source(s,FakeSourceVerifier())["verification"]["status"])
    def test_unknown_source_type_rejected(self):
        s = source(); s["source_type"] = "trust_me"
        with self.assertRaises(EvidenceIntegrityError): normalize_and_verify_source(s,FakeSourceVerifier())
    @patch("idea_review_runtime.evidence._http_text",return_value=("<title>Unrelated document</title>","https://example.org"))
    def test_resource_title_must_match(self,_):
        s = source(); s["source_type"] = "official_docs"; s["identifiers"] = {}
        result = normalize_and_verify_source(s,LiveSourceVerifier())
        self.assertEqual("metadata_mismatch",result["verification"]["status"])
