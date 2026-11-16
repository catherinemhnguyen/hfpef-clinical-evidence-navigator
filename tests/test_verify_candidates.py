"""Network-free safeguards for bibliographic identity auditing."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_candidates as ver


def pubmed(pmid="12345678", title="Heart failure with preserved ejection fraction"):
    return {
        "id": f"pmid-{pmid}", "source": "PubMed", "pmid": pmid,
        "nct_id": "", "doi": "10.1000/example", "title": title,
        "year": 2026, "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
    }


def registry(nct="NCT01234567", title="HFpEF diagnostic trial"):
    return {
        "id": f"nct-{nct}", "source": "ClinicalTrials.gov", "pmid": "",
        "nct_id": nct, "doi": "", "title": title, "year": 2025,
        "url": f"https://clinicaltrials.gov/study/{nct}",
    }


class IdentityTests(unittest.TestCase):
    def test_consistent_records_locally_checked(self):
        r = [pubmed(), registry()]
        self.assertEqual(ver.local_flags(r), {})

    def test_bad_pmid_and_url_are_flagged(self):
        x = pubmed()
        x["url"] = "https://example.com/unrelated"
        x["pmid"] = "not-a-pmid"
        issues = ver.local_flags([x])[x["id"]]
        self.assertIn("invalid_pubmed_identity", issues)
        self.assertIn("pubmed_url_mismatch", issues)

    def test_doi_duplicates_flag_both_records(self):
        a, b = pubmed(), pubmed("23456789")
        flags = ver.local_flags([a, b])
        self.assertIn("duplicate_doi", flags[a["id"]])
        self.assertIn("duplicate_doi", flags[b["id"]])

    def test_source_comparison_uses_title_doi_and_identifier(self):
        p = pubmed()
        self.assertEqual(ver.compare_source(p, {
            "id": "12345678", "title": p["title"].upper() + ".",
            "doi": "10.1000/example",
        }), [])
        self.assertIn("source_identifier_mismatch", ver.compare_source(p, {
            "id": "99999999", "title": p["title"], "doi": p["doi"],
        }))
        self.assertIn("source_doi_mismatch", ver.compare_source(p, {
            "id": "12345678", "title": p["title"], "doi": "10.1000/other",
        }))
        self.assertIn("source_title_mismatch", ver.compare_source(p, {
            "id": "12345678", "title": "Completely unrelated paper", "doi": p["doi"],
        }))

    def test_online_check_does_not_imply_clinical_verification(self):
        records = [pubmed(), registry()]
        seen = []
        def fake_source(row):
            seen.append(row["id"])
            return {"id": row.get("pmid") or row.get("nct_id"),
                    "title": row["title"], "doi": row.get("doi"),
                    "source": "mock source"}
        result, flagged, ledger = ver.verify(records, {"schema_version": 1, "records": {}},
                                             online_limit=1, source_reader=fake_source)
        self.assertEqual(result["total_candidates"], 2)
        self.assertEqual(result["online_identity_matched"], 1)
        self.assertEqual(result["online_identity_not_checked"], 1)
        self.assertEqual(result["unverified_clinical_records"], 2)
        self.assertEqual(len(seen), 1)
        self.assertFalse(flagged)
        result, _, ledger = ver.verify(records, ledger, online_limit=1, source_reader=fake_source)
        self.assertEqual(result["online_identity_matched"], 2)
        self.assertEqual(result["online_identity_not_checked"], 0)
        self.assertEqual(len(seen), 2)
        result, _, _ = ver.verify(records, ledger, online_limit=1, source_reader=fake_source)
        self.assertEqual(result["online_attempted_this_run"], 0)

    def test_changed_metadata_rechecked(self):
        a = pubmed()
        _, _, ledger = ver.verify([a], {"schema_version": 1, "records": {}}, 1,
                                  lambda row: {"id": row["pmid"], "title": row["title"],
                                               "doi": row["doi"]})
        a2 = dict(a, title="Updated publication title")
        report, _, _ = ver.verify([a2], ledger, 0,
                                  lambda row: {"id": row["pmid"], "title": row["title"],
                                               "doi": row["doi"]})
        self.assertEqual(report["online_identity_not_checked"], 1)
        self.assertEqual(report["online_identity_matched"], 0)

    def test_outage_not_success(self):
        def fail(_):
            raise TimeoutError("simulated")
        report, flagged, ledger = ver.verify([pubmed()], {"schema_version": 1, "records": {}},
                                             1, fail)
        self.assertEqual(report["online_identity_matched"], 0)
        self.assertEqual(report["online_identity_unavailable"], 1)
        self.assertEqual(len(flagged), 1)
        self.assertEqual(ledger["records"]["pmid-12345678"]["status"], "unavailable")

    def test_duplicate_ids_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "Duplicate candidate id"):
            ver.verify([pubmed(), pubmed()], {"schema_version": 1, "records": {}})


if __name__ == "__main__":
    unittest.main()
