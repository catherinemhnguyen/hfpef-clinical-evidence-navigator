#!/usr/bin/env python3
"""Sanity-check the starter HFpEF clinical trial JSON before publishing."""
import json
import re
from pathlib import Path

FILE = Path(__file__).resolve().parent.parent / 'data' / 'studies.json'
data = json.loads(FILE.read_text(encoding='utf-8'))
assert isinstance(data['studies'], list) and data['studies'], 'Dataset must include studies'
ids=set()
for study in data['studies']:
    name=study['acronym']
    assert study['id'] not in ids, f'duplicate id for {name}'
    ids.add(study['id'])
    assert 1950 <= study['year'] <= 2100, f'invalid year for {name}'
    assert study['population']['sample_size'] > 0, f'invalid enrollment for {name}'
    assert study['population']['lvef_eligibility'], f'missing EF criterion for {name}'
    assert study['primary_outcomes'], f'missing primary endpoints for {name}'
    for outcome in study['primary_outcomes']:
        assert outcome['name'] and outcome['analysis'] and outcome['effect_type'], f'incomplete endpoint for {name}'
        ci = outcome['ci_95']
        assert len(ci) == 2 and ci[0] <= ci[1], f'invalid CI for {name}'
        assert ci[0] <= outcome['effect_estimate'] <= ci[1], f'estimate outside CI for {name}'
        assert isinstance(outcome['significant'], bool), f'invalid significant flag for {name}'
    ref=study['reference']
    assert re.fullmatch(r'10\.\d{4,9}/\S+',ref['doi']), f'bad DOI for {name}'
    assert re.fullmatch(r'\d{7,9}',ref['pmid']), f'bad PMID for {name}'
    assert re.fullmatch(r'NCT\d{8}',ref['clinicaltrials_id']), f'bad NCT ID for {name}'
    assert ref['pubmed_url'] == f"https://pubmed.ncbi.nlm.nih.gov/{ref['pmid']}/", f'bad URL for {name}'
    assert study['curation']['verification_status'], f'unclear verification status for {name}'
print(f"PASS: {len(data['studies'])} studies validated, {sum(s['population']['sample_size'] for s in data['studies']):,} summed enrollments.")