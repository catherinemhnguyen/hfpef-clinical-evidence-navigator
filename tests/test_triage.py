"""Tests for nonclinical metadata triage; do not imply clinical inclusion or verification."""
import csv
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.triage_candidates import make_rows, propose, read_decisions, FIELDS

class TestTriage(unittest.TestCase):
    def test_protocol_never_assumed_results(self):
        row={'title':'SPIRRIT-HFpEF: Rationale and design','publication_type':'Randomized Controlled Trial','source':'PubMed'}
        p=propose(row)
        self.assertEqual(p['proposed_record_type'],'Protocol/design (not outcomes)')
        self.assertEqual(p['possible_parent_trial'],'SPIRRIT-HFpEF')
    def test_ambiguous_no_auto_exclusion(self):
        r=make_rows([{'id':'p1','title':'A diuretic trial in heart failure','source':'PubMed'}])[0]
        self.assertEqual(r['human_screening_decision'],'')
        self.assertEqual(r['final_eligibility'],'')
    def test_trials_are_not_assumed_full_text_checked(self):
        r=make_rows([{'id':'p2','title':'Randomized trial for HFpEF','source':'PubMed'}])[0]
        self.assertEqual(r['priority_for_abstract_review'],'High')
        self.assertEqual(r['abstract_reviewed'],'')
        self.assertEqual(r['full_text_reviewed'],'')
    def test_decisions_merge_and_preserve(self):
        d={'pmid-12345678':{'human_screening_decision':'Maybe','reviewer':'AB'}}
        row=make_rows([{'id':'pmid-12345678','title':'HFpEF trial'}],d)[0]
        self.assertEqual(row['reviewer'],'AB')
        self.assertEqual(row['human_screening_decision'],'Maybe')
    def test_nct_registration_is_not_published_trial(self):
        p=propose({'title':'Interventional study in HFpEF','source':'ClinicalTrials.gov','nct_id':'NCT12345678'})
        self.assertEqual(p['proposed_record_type'],'Trial registration (not published results)')
if __name__=='__main__':unittest.main()
