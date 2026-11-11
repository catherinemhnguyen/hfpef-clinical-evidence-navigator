#!/usr/bin/env python3
"""Validate cross-file structure and references; does NOT validate scientific truth."""
from __future__ import annotations

import re
from datetime import date
from evidence import load_records, result_status


def check(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def validate() -> dict[str, int]:
    studies, guidance = load_records()
    a, b = studies['studies'], guidance['guidelines']
    check(len(a) == 22, f"Expected 22 studies; got {len(a)}")
    check(len(b) == 3, f"Expected 3 guidance documents; got {len(b)}")
    ids = set()
    pmids = set()
    for r in a:
        name = r.get('acronym', '<unnamed>')
        check(r.get('id') not in ids, f"Duplicate ID: {name}")
        ids.add(r['id'])
        check(1950 <= r['year'] <= date.today().year + 1, f"Invalid year: {name}")
        check(bool(r.get('study_type')), f"Missing study type: {name}")
        check(isinstance(r['population']['sample_size'], int) and r['population']['sample_size'] > 0, f"Invalid sample size: {name}")
        check(bool(r['population']['lvef_eligibility']), f"Missing EF eligibility/description: {name}")
        check(isinstance(r['outcome_tags'], list) and r['outcome_tags'], f"No outcome tags: {name}")
        check(bool(r['primary_outcomes']), f"Missing primary outcome: {name}")
        check(bool(r['curation']['verification_status']), f"Missing verification: {name}")
        check(result_status(r) != 'Not fully extracted', f"Missing primary significance flag: {name}")
        for o in r['primary_outcomes']:
            check(bool(o['name']) and bool(o['analysis']) and bool(o['result_text']), f"Incomplete outcome: {name}")
            check(isinstance(o['significant'], bool), f"Missing primary significance: {name}")
            ci = o.get('ci_95')
            estimate = o.get('effect_estimate')
            check((ci is None) == (estimate is None), f"Unpaired estimate and CI: {name}")
            if ci is not None:
                check(len(ci) == 2 and all(isinstance(x, (int, float)) for x in ci), f"Malformed CI: {name}")
                check(ci[0] <= estimate <= ci[1], f"Effect not inside CI: {name}")
        ref = r['reference']
        check(bool(re.fullmatch(r'10\.\d{4,9}/\S+',ref['doi'])), f"Malformed DOI: {name}")
        check(bool(re.fullmatch(r'\d{7,9}',ref['pmid'])), f"Malformed PMID: {name}")
        check(ref['pmid'] not in pmids, f"Repeated PMID: {name}")
        pmids.add(ref['pmid'])
        check(ref['pubmed_url'] == f"https://pubmed.ncbi.nlm.nih.gov/{ref['pmid']}/", f"Invalid PubMed link: {name}")
        nct = ref.get('clinicaltrials_id', '')
        check(not nct or bool(re.fullmatch(r'NCT\d{8}', nct)), f"Invalid NCT: {name}")
    for r in b:
        check(r['id'] not in ids, 'Repeated guidance ID')
        ids.add(r['id'])
        check(r['study_type'] == 'Guideline', 'Guidance type inconsistent')
        check(bool(re.fullmatch(r'10\.\d{4,9}/\S+',r['doi'])), 'Guidance DOI malformed')
        check(r['source_url'] == f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/", 'Guidance source URL incorrect')
        check(r['pmid'] not in pmids, 'Repeated PMID across source collection')
        pmids.add(r['pmid'])
        check(bool(r['verification_status']), 'Missing guideline verification status')
    return {"studies": len(a), "guidelines": len(b), "total": len(a) + len(b), "participants_summed": sum(s['population']['sample_size'] for s in a)}


if __name__ == "__main__":
    print('PASS:', validate())
