"""Checks source-level draft extraction remains unverified."""
import csv, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestDrafts(unittest.TestCase):
 def test_count_and_provenance(self):
  with (ROOT/'data/abstract_extraction_drafts.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
  self.assertEqual(len(rows),10)
  self.assertEqual(len({r['pmid'] for r in rows}),10)
  self.assertTrue(all(r['source_url'].endswith('/'+r['pmid']+'/') for r in rows))
  self.assertTrue(all(r['full_text_checked']=='No' and not r['reviewer_b'] for r in rows))
 def test_design_separated(self):
  with (ROOT/'data/abstract_extraction_drafts.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
  protocol=next(x for x in rows if x['pmid']=='39282788')
  self.assertIn('Protocol',protocol['publication_type'])
  self.assertFalse(protocol['primary_result_as_reported'].startswith('HR'))
  observational=next(x for x in rows if x['pmid']=='40368924')
  self.assertIn('Retrospective',observational['publication_type'])
  self.assertEqual(observational['ci_lower'],'')
if __name__=='__main__':unittest.main()
