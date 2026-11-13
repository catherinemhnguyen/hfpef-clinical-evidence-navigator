"""Offline, API-free validation for extraction safeguards and PubMed parsing."""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import extract_candidates as ex


class ExtractionTests(unittest.TestCase):
    def test_strict_schemas_all_required(self):
        schema = ex.extraction_schema()
        self.assertEqual(set(schema["properties"]), set(schema["required"]))
        self.assertEqual(set(schema["properties"]["fields"]["properties"]), set(ex.FIELD_NAMES))
        self.assertEqual(set(ex.auditor_schema()["properties"]), {"judgments", "potential_omissions"})

    def test_validated_verbatim_quote(self):
        self.assertTrue(ex.quote_present("EF above 40%", "Inclusion: EF above 40% at baseline."))
        self.assertFalse(ex.quote_present("reduced mortality", "No mortality benefit established."))

    def test_unsupported_value_is_flagged(self):
        items = {n: {"value": None, "evidence_quote": None} for n in ex.FIELD_NAMES}
        items["sample_size"] = {"value": "8000", "evidence_quote": "Participants included 100 adults"}
        result = ex.evidence_checks({"report_type": "original_trial", "fields": items,
                                     "knowledge_units": [], "missing_information": []},
                                    "Participants included 100 adults in the trial.")
        self.assertTrue(any(x["problem"] == "number_not_in_quote" for x in result["mechanical_flags"]))
        self.assertTrue(result["requires_human_review"])

    def test_nonexistent_quote_flagged(self):
        items = {n: {"value": None, "evidence_quote": None} for n in ex.FIELD_NAMES}
        items["study_design"] = {"value": "Randomized", "evidence_quote": "double blind randomized"}
        result = ex.evidence_checks({"report_type": "original_trial", "fields": items,
                                     "knowledge_units": [], "missing_information": []},
                                    "This was a prospective observational study.")
        self.assertEqual(result["evidence_spans_found"], 0)

    def test_xml_sections_and_entrez_id(self):
        xml = b'''<PubmedArticleSet><PubmedArticle><MedlineCitation>
        <PMID>12345678</PMID><Article><ArticleTitle>Example <i>HFpEF</i> trial.</ArticleTitle>
        <Abstract><AbstractText Label="METHODS">Randomized 100 adults.</AbstractText>
        <AbstractText Label="RESULTS">Benefit was not significant.</AbstractText></Abstract>
        </Article></MedlineCitation></PubmedArticle></PubmedArticleSet>'''
        doc = ex.parse_pubmed_xml(xml, "12345678")
        self.assertEqual(doc["title"], "Example HFpEF trial.")
        self.assertIn("METHODS: Randomized 100 adults", doc["abstract"])
        with self.assertRaises(ValueError):
            ex.parse_pubmed_xml(xml, "87654321")

    def test_prioritization_respects_pmid_filter(self):
        rows = [{"id":"pmid-12345678", "pmid":"12345678", "source":"PubMed", "title":"HFpEF randomized trial"},
                {"id":"pmid-23456789", "pmid":"23456789", "source":"PubMed", "title":"HFpEF registry"}]
        found = ex.select_candidates(rows, ["23456789"], 5, "High")
        self.assertEqual(found[0]["pmid"], "23456789")
        with self.assertRaises(ValueError):
            ex.select_candidates(rows, ["99999999"], 1, "High")

    def test_missing_key_fails_without_network(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"OPENAI_API_KEY":""}):
            with self.assertRaises(SystemExit) as raised:
                ex.main(["--limit", "1"])
        self.assertNotEqual(raised.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
