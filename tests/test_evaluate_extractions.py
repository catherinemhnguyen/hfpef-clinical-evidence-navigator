"""Offline tests: benchmarking requires real human labels and matching source hashes."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evaluate_extractions as ev
from extract_candidates import FIELD_NAMES


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        fields = {k: {"value": None, "evidence_quote": None} for k in FIELD_NAMES}
        fields["sample_size"] = {"value": "80", "evidence_quote": "80 participants"}
        fields["primary_endpoint"] = {"value": "Wrong endpoint", "evidence_quote": "endpoint"}
        self.draft = {
            "pmid": "12345678", "model": "extractor-A", "auditor_model": "auditor-B",
            "source_sha256": "f" * 64,
            "extraction": {"fields": fields},
            "llm_audit": {"judgments": [
                {"field": "sample_size", "verdict": "supported", "reason": "matches"},
                {"field": "primary_endpoint", "verdict": "unsupported", "reason": "wrong"},
            ]},
        }
        (self.folder / "pmid-12345678-draft.json").write_text(json.dumps(self.draft))
        reviews = {k: {"expected_present": False, "extraction_correct": True} for k in FIELD_NAMES}
        reviews["sample_size"] = {"expected_present": True, "extraction_correct": True}
        reviews["primary_endpoint"] = {"expected_present": True, "extraction_correct": False}
        reviews["population"] = {"expected_present": True, "extraction_correct": False}
        self.review = {
            "pmid": "12345678", "draft_file": "pmid-12345678-draft.json",
            "source_sha256": "f" * 64, "reviewer": "Pilot reviewer",
            "review_date": "2026-11-15", "source_notes": "Synthetic test only",
            "reference_scope": "same_input_text", "fields": reviews,
        }

    def test_metrics_require_independently_labeled_fields(self):
        result = ev.evaluate({"schema_version": 1, "reviews": [self.review]}, self.folder)
        stats = result["overall"]
        self.assertEqual(stats["fields_reviewed"], len(FIELD_NAMES))
        self.assertEqual(stats["correct_extracted"], 1)
        self.assertEqual(stats["fields_expected"], 3)
        self.assertEqual(stats["extracted_fields"], 2)
        self.assertEqual(stats["extracted_field_precision"], 0.5)
        self.assertEqual(stats["extractable_field_recall"], 0.3333)
        self.assertEqual(stats["auditor_error_sensitivity"], 1.0)
        self.assertEqual(stats["auditor_correct_acceptance_rate"], 1.0)
        self.assertIn("extractor-A / auditor-B", result["model_pairs"])

    def test_reject_unlabeled_or_no_human_reviews(self):
        with self.assertRaisesRegex(ValueError, "No manually completed reviews"):
            ev.evaluate({"schema_version": 1, "reviews": []}, self.folder)
        del self.review["fields"]["follow_up"]
        with self.assertRaisesRegex(ValueError, "all 12 fields"):
            ev.evaluate({"schema_version": 1, "reviews": [self.review]}, self.folder)

    def test_reject_wrong_source_or_invalid_truth(self):
        self.review["source_sha256"] = "a" * 64
        with self.assertRaisesRegex(ValueError, "hash"):
            ev.evaluate({"schema_version": 1, "reviews": [self.review]}, self.folder)
        self.review["source_sha256"] = "f" * 64
        self.review["fields"]["primary_endpoint"]["extraction_correct"] = True
        with self.assertRaisesRegex(ValueError, "correctness contradicts"):
            # Incorrect extracted value cannot be automatically detected: this test
            # checks only presence consistency, so this is a valid human judgement.
            self.review["fields"]["population"]["extraction_correct"] = True
            ev.evaluate({"schema_version": 1, "reviews": [self.review]}, self.folder)


if __name__ == "__main__":
    unittest.main()
