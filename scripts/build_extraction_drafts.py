"""Source-checked abstract-level extraction drafts for ten pilot publications.

The data in this file is deliberately manual; no model-generated claims enter the curated JSON.
Each draft must be independently checked against full text before promotion.
"""
from __future__ import annotations
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIELDNAMES=['pmid','title','publication_type','parent_trial_or_context','nct_id','sample_size_reported',
'enrollment','lvef_eligibility','intervention_or_exposure','comparator',
'primary_endpoint','primary_result_as_reported','effect_measure','effect_estimate','ci_lower','ci_upper','p_value',
'source_url','source_level','verification_status','reviewer_a','reviewer_b','full_text_checked','limitations_or_followup']
# All sourced from public PubMed abstracts, verified Nov 12 2026.
DRAFTS = [
('29142012','Original randomized sham-controlled trial','REDUCE LAP-HF I','NCT02600234','44','HF with raised exercise filling pressures','≥40%','Interatrial shunt device','Sham procedure','Pulmonary capillary wedge pressure during exercise at 1 month','Greater reduction across exercise stages vs sham (P=0.028); peak PCWP comparisons not statistically significant (P=0.14)','', '', '', '', '0.028','Peak vs all-stage outcomes differ'),
('30398602','Original randomized crossover trial','INDIE-HFpEF','NCT02742129','105','Symptomatic HFpEF','','Inhaled inorganic nitrite','Placebo','Peak VO2 after four weeks','13.5 vs 13.7 mL/kg/min; treatment difference -0.20 (95% CI -0.56 to 0.16), P=.27','Between-phase mean difference','-0.20','-0.56','0.16','0.27','Cross-over design; 98 completed'),
('30098962','Original randomized factorial-style trial','ROPA-DOP','NCT01901809','90','Hospitalized acute HFpEF','','Continuous IV furosemide, bolus IV furosemide, with/without low-dose dopamine','Comparative 4-arm diuretic regimens','Percent change in creatinine at 72 hours','Continuous infusion associated with greater creatinine increase than bolus (16.01% vs 4.62%, P=.02); no detectable dopamine benefit (P=.33)','Multiple contrasts','','','','0.02','Multiple treatment contrasts; do not simplify into a single risk ratio'),
('40294211','Original randomized exercise trial','TRAINING-HR','NCT05649787','80','HFpEF with chronotropic incompetence','','Supervised aerobic ± resistance exercise','Nonsupervised exercise recommendations','Change in peak VO2 at 12 weeks','Aerobic plus higher-resistance training versus recommendations: +4.0 mL/kg/min (95% CI 2.9 to 5.1; P<.001)','Between-group mean difference','4.0','2.9','5.1','<0.001','Four-arm study; result corresponds to one specified treatment contrast'),
('40072462','Original randomized placebo-controlled trial','HuMAIN-HFpEF','NCT05284617','66','Obesity-related HFpEF','','HU6','Placebo','Change in body weight at 19 weeks','Between-group difference -2.86 kg (95% CI -4.68 to -1.04), P=.003','Between-group mean difference','-2.86','-4.68','-1.04','0.003','Peak VO2 and quality-of-life improvements were not statistically significant'),
('42999950','Original randomized placebo-controlled trial','IRONMET-HFpEF','NCT04945707','65','HFpEF with iron deficiency','','Ferric derisomaltose 1000 mg IV','Placebo','Change in peak VO2 at 12 weeks','Least-squares mean difference 1.1 mL/kg/min (95% CI 0.2 to 1.9), P=.02','Least-squares mean difference','1.1','0.2','1.9','0.02','Published 2026-11-08 ahead of print; follow-up 12 weeks'),
('40368924','Retrospective propensity-matched cohort','Tirzepatide target-trial emulation','','14154','Real-world HFpEF diagnosis','','Tirzepatide exposure','Matched non-tirzepatide cohort','HF exacerbation or all-cause death','Association HR 0.52 for composite; CI not in abstract summary','Adjusted hazard ratio','0.52','','','','Observational association, not randomized causal efficacy'),
('41950988','Participant-level pooled secondary trial analysis','HFpEF diagnostic scores across five parent trials','','15318','HFpEF in CHARM-Preserved, I-PRESERVE, TOPCAT-Americas, PARAGON-HF, DELIVER','','HFpEF-ABA diagnostic score','Higher vs lower score','CV death or HF hospitalization risk association','High vs low/intermediate HFpEF-ABA: HR 1.75 (95% CI 1.62 to 1.89); association, not treatment efficacy','Hazard ratio for prognostic association','1.75','1.62','1.89','<0.001','Not a new independent randomized cohort; links five older parent trials'),
('39282788','Protocol / rationale only','SPIRRIT-HFpEF','','','Planned HFpEF/HFmrEF randomized registry trial','≥40%','Spironolactone/eplerenone + usual care','Usual care','Planned total CV deaths and HF hospitalizations','No clinical outcome results: design paper only','', '', '', '', '','Projected approximately 2400; not a completed outcomes paper'),
('42573026','Retrospective propensity-matched cohort','Tirzepatide vs dulaglutide','','48610','Matched HFpEF cohorts from electronic health records','','Tirzepatide','Dulaglutide','Multiple outcomes (including 1-year all-cause mortality)','1-year all-cause mortality HR 0.66 (95% CI 0.59 to 0.74); secondary reported association','Hazard ratio','0.66','0.59','0.74','','Matched 24,305 per arm; observational, not head-to-head randomized trial')
]

def main():
    seed=json.loads((ROOT/'data/discovery_seed.json').read_text())['candidates']
    lookup={s['pmid']:s for s in seed}
    with (ROOT/'data/abstract_extraction_drafts.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDNAMES);w.writeheader()
        for entry in DRAFTS:
            (pmid,etype,parent,nct,n,group,ef,exposure,comp,endpoint,result,measure,est,low,high,p,notes)=entry
            pub=lookup[pmid]
            row=dict(pmid=pmid,title=pub['title'],publication_type=etype,parent_trial_or_context=parent,nct_id=nct,
            sample_size_reported=n,enrollment=group,lvef_eligibility=ef,intervention_or_exposure=exposure,comparator=comp,
            primary_endpoint=endpoint,primary_result_as_reported=result,effect_measure=measure,effect_estimate=est,
            ci_lower=low,ci_upper=high,p_value=p,source_url=pub['url'],source_level='PubMed abstract',
            verification_status='Source-linked abstract draft; full-text and independent verification pending',
            reviewer_a='',reviewer_b='',full_text_checked='No',limitations_or_followup=notes)
            w.writerow(row)
    print('Wrote ten abstract-level source linked draft records; none independently verified.')
if __name__=='__main__':main()
