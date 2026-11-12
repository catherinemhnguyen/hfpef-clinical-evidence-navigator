#!/usr/bin/env python3
"""Nonclinical rule-based triage of bibliographic candidates. No automatic inclusion or efficacy claims.

Run: python scripts/triage_candidates.py
Generated triage_queue.csv may be overwritten by the discovery workflow.
Record *human* decisions separately in screening_decisions.csv, which is never overwritten.
"""
from __future__ import annotations
import csv
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
FIELDS = ['id','title','year','source','pmid','doi','nct_id','url','publication_type',
          'proposed_record_type','title_relevance_flag','priority_for_abstract_review',
          'possible_parent_trial','parent_link_basis','human_screening_decision',
          'human_exclusion_reason','reviewer','review_date','abstract_reviewed',
          'full_text_reviewed','second_reviewer','final_eligibility','notes']
# Conservative, transparent hints. An acronym match does not prove same participants/trial.
PARENT_ALIASES = {
    'FINEARTS-HF': [r'FINEARTS[- ]HF'],
    'EMPEROR-Preserved': [r'EMPEROR[- ]Preserved'],
    'DELIVER': [r'\bDELIVER\b'],
    'PARAGON-HF': [r'PARAGON[- ]HF'],
    'TOPCAT': [r'\bTOPCAT\b'],
    'SUMMIT': [r'\bSUMMIT\b'],
    'STEP-HFpEF': [r'STEP[- ]HFpEF'],
    'REDUCE LAP-HF I': [r'REDUCE LAP[- ]HF I\b'],
    'REDUCE LAP-HF II': [r'REDUCE LAP[- ]HF II\b'],
    'SPIRRIT-HFpEF': [r'SPIRRIT[- ]HFpEF'],
    'INDIE-HFpEF': [r'INDIE[- ]HFpEF'],
    'ROPA-DOP': [r'ROPA[- ]DOP'],
    'TRAINING-HR': [r'TRAINING[- ]HR'],
    'HuMAIN-HFpEF': [r'HuMAIN[- ]HFpEF'],
    'IRONMET-HFpEF': [r'IRONMET[- ]HFpEF'],
}
HF_EXPLICIT = re.compile(r'HFpEF|heart failure with preserved (?:left ventricular )?ejection fraction|preserved[- ]ejection[- ]fraction heart failure|diastolic heart failure', re.I)
HF_MILD = re.compile(r'\bHFmrEF\b|mildly reduced ejection fraction', re.I)
HF_BROAD = re.compile(r'\bheart failure\b|\bHF\b|cardiac', re.I)
META = re.compile(r'\bmeta[- ]analysis\b|systematic review|pooled analysis', re.I)
PROTOCOL = re.compile(r'\bprotocol\b|rationale and design|study design|design of the|design and rationale', re.I)
SECONDARY = re.compile(r'subgroup|post hoc|post-hoc|secondary analysis|prespecified analysis|follow[- ]up|long[- ]term outcomes|bayesian analysis', re.I)
OBSERVATIONAL = re.compile(r'cohort|observational|registry|retrospective|real[- ]world|propensity|case.control', re.I)
TRIAL = re.compile(r'\brandomi[sz]ed\b|\brandomi[sz]ation\b|\btrial\b|phase [1234]|placebo', re.I)
GUIDANCE = re.compile(r'guideline|expert consensus|recommendation|practice guidance', re.I)

def propose(row: dict) -> dict:
    title = str(row.get('title') or '')
    pub = str(row.get('publication_type') or '')
    both = title + ' ' + pub
    if row.get('source') == 'ClinicalTrials.gov' or row.get('nct_id') and not row.get('pmid'):
        category = 'Trial registration (not published results)'
    elif GUIDANCE.search(title) or 'Guideline' in pub:
        category = 'Guideline or guidance candidate'
    elif PROTOCOL.search(title):
        category = 'Protocol/design (not outcomes)'
    elif META.search(title):
        category = 'Synthesis / pooled analysis'
    elif SECONDARY.search(title):
        category = 'Follow-up / subgroup / secondary report'
    elif OBSERVATIONAL.search(both):
        category = 'Observational / registry study'
    elif TRIAL.search(both):
        category = 'Potential original clinical trial report'
    else:
        category = 'Other publication / classification needed'

    explicit = HF_EXPLICIT.search(title)
    mild = HF_MILD.search(title)
    broad = HF_BROAD.search(title)
    if explicit:
        relevance = 'Explicit HFpEF in title'
    elif mild:
        relevance = 'HFmrEF/EF-spectrum title; check HFpEF subgroup'
    elif broad:
        relevance = 'General heart failure; verify HFpEF eligibility'
    else:
        relevance = 'No HFpEF in title; verify abstract before exclusion'

    if explicit and category in ('Potential original clinical trial report','Observational / registry study'):
        priority='High'
    elif explicit or (mild and category == 'Potential original clinical trial report'):
        priority='Medium'
    else:
        priority='Low / needs relevance check'

    matched = [key for key,pats in PARENT_ALIASES.items() if any(re.search(p,title,re.I) for p in pats)]
    parent_hint='; '.join(matched)
    basis='Title acronym match only; verify NCT, participants and publication role' if matched else ''
    return {
        'proposed_record_type':category,
        'title_relevance_flag':relevance,
        'priority_for_abstract_review':priority,
        'possible_parent_trial':parent_hint,
        'parent_link_basis':basis,
    }

def make_rows(candidates: list[dict], decisions: dict[str,dict] | None=None) -> list[dict]:
    decisions=decisions or {}
    out=[]
    for r in candidates:
        d={k:str(r.get(k,'') or '') for k in ['id','title','year','source','pmid','doi','nct_id','url','publication_type']}
        d.update(propose(r))
        decision=decisions.get(d['id'],{})
        for k in ['human_screening_decision','human_exclusion_reason','reviewer','review_date','abstract_reviewed','full_text_reviewed','second_reviewer','final_eligibility','notes']:
            d[k]=decision.get(k,'')
        out.append(d)
    return out

def read_decisions() -> dict[str,dict]:
    p=DATA/'screening_decisions.csv'
    if not p.exists(): return {}
    with p.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=len(set(r['id'] for r in rows)):
        raise ValueError('Duplicate record id in human screening decisions; do not overwrite.')
    return {r['id']:r for r in rows}

def run() -> dict:
    candidates=json.loads((DATA/'discovery_candidates.json').read_text(encoding='utf-8'))['candidates']
    rows=make_rows(candidates,read_decisions())
    with (DATA/'triage_queue.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    c=Counter(r['priority_for_abstract_review'] for r in rows)
    return {'total':len(rows),'priority_breakdown':dict(c),'human_decisions_recorded':sum(bool(r['human_screening_decision']) for r in rows)}

if __name__=='__main__':
    print(json.dumps(run(),indent=2))
