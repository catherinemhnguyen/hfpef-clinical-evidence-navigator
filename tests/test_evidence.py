"""Offline data integrity and filtering regression tests (stdlib unittest)."""
import csv
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from scripts.evidence import (
    csv_text, filter_guidelines, filter_studies, flatten_guideline,
    flatten_study, load_records, result_status,
)
from scripts.validate_data import validate


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs, cls.guide = load_records()
        cls.studies = cls.docs['studies']
        cls.guidelines = cls.guide['guidelines']

    def test_target_inventory(self):
        self.assertGreaterEqual(len(self.studies), 22)
        self.assertEqual(len(self.guidelines), 3)
        self.assertEqual(validate()['total'], len(self.studies)+len(self.guidelines))

    def test_distinct_source_ids(self):
        pmids = [r['reference']['pmid'] for r in self.studies] + [g['pmid'] for g in self.guidelines]
        self.assertEqual(len(pmids), len(set(pmids)))

    def test_filter_treatment_and_keyword(self):
        rows = filter_studies(self.studies, categories=['SGLT2 inhibitor'], keyword='empagliflozin')
        self.assertTrue({x['acronym'] for x in rows} >= {'EMPEROR-Preserved', 'EMPERIAL-Preserved'})
        self.assertTrue(all(x['treatment_category']=='SGLT2 inhibitor' for x in rows))

    def test_filter_outcome_population(self):
        rows = filter_studies(self.studies, outcome_tags=['Weight'], phenotype_tags=['Type 2 diabetes'])
        self.assertEqual([x['acronym'] for x in rows], ['STEP-HFpEF DM'])

    def test_filter_year_range(self):
        rows = filter_studies(self.studies, years=(2003, 2008))
        self.assertEqual({x['acronym'] for x in rows}, {'CHARM-Preserved','PEP-CHF','I-PRESERVE'})

    def test_filter_study_design(self):
        rows = filter_studies(self.studies, types=['Sham-controlled device trial'])
        self.assertEqual([s['acronym'] for s in rows], ['REDUCE LAP-HF II'])

    def test_mixed_primary_outcomes(self):
        by_name = {s['acronym']: s for s in self.studies}
        self.assertEqual(result_status(by_name['Aldo-DHF']), 'Mixed primary endpoint results')
        self.assertEqual(result_status(by_name['PARALLAX']), 'Mixed primary endpoint results')
        self.assertEqual(result_status(by_name['SUMMIT']), 'All primary endpoints significant')
        self.assertEqual(result_status(by_name['I-PRESERVE']), 'Primary endpoint(s) not significant')

    def test_filter_status(self):
        rows = filter_studies(self.studies, statuses=['Mixed primary endpoint results'])
        self.assertEqual({s['acronym'] for s in rows}, {'PARALLAX','Aldo-DHF'})

    def test_guidance_source_types(self):
        rows = filter_guidelines(self.guidelines, keyword='Consensus')
        self.assertEqual(len(rows), 1)
        self.assertIn('Consensus', rows[0]['title'])

    def test_csv_roundtrip(self):
        rows = [flatten_study(s) for s in self.studies] + [flatten_guideline(g) for g in self.guidelines]
        parsed = list(csv.DictReader(io.StringIO(csv_text(rows))))
        self.assertEqual(len(parsed), len(self.studies)+len(self.guidelines))
        self.assertEqual(sum(row['Record type']=='Guidance' for row in parsed), 3)

    def test_csv_snapshots_up_to_date(self):
        rows = [flatten_study(s) for s in self.studies] + [flatten_guideline(g) for g in self.guidelines]
        with (ROOT/'data/evidence_index.csv').open('r', encoding='utf-8-sig', newline='') as f:
            text = f.read()
        self.assertEqual(text, csv_text(rows))


if __name__ == '__main__':
    unittest.main()
