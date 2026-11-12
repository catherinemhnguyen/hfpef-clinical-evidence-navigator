# Literature discovery and validation methods (v0.3)

## Goals and research integrity

Respond to the request to identify a broader HFpEF evidence corpus using reproducible searches instead of stopping at 22 manually selected studies. The **curated dataset** (`data/studies.json`) and **bibliographic discovery queue** (`data/discovery_candidates.json`) are intentionally separate. A candidate is *not* a completed study extraction, clinician-validated finding, or independent clinical trial. The project is not yet a systematic review.

## Sources and reproducible acquisition

The Python script `scripts/discover_literature.py` searches the official public APIs for [PubMed E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25499/) (`ESearch` and `ESummary`) and [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api). Searches include HFpEF, diastolic heart failure, normal EF and HFmrEF terminology, with trial/cohort/guideline qualifiers. Results are paginated, limited by configurable safety caps, and deduplicated by PMID, DOI and NCT ID against existing records and other candidates. The query strings, reported totals, retrieved counts and truncation flags are written to `data/discovery_search_log.json`.

No proprietary agent or model has been used to generate unverified outcome results; this is structured retrieval of public bibliographic metadata rather than indiscriminate web crawling. **The 15 checked-in seed citations were manually located in PubMed; a network-connected live API run remains to be verified.**

## Reproduce

```bash
python scripts/discover_literature.py --offline
python scripts/discover_literature.py --max-pubmed 1000 --max-trials 300
python scripts/validate_data.py
```

The first command regenerates the cross-checked seed-only citation index and requires no network. The second queries public APIs and will fail without internet access. The proposed GitHub Actions workflow runs on Monday mornings or manually, then commits only changes to the **candidate queue**, never the curated clinical interpretations. If disabled, enable Actions and check workflow permissions in the repository settings. A successful deployment is not proof of a successful literature search; inspect the run log.

## Screening and clinical extraction

1. Confirm direct HFpEF or justified HFmrEF/HFpEF relevance, original full-text source and year.
2. Label record as original trial report, trial protocol, subgroup/secondary analysis, observational cohort, meta-analysis, guideline, or trial registry entry. Count *unique NCT studies* separately from *publications*.
3. Extract eligibility (exact LVEF and diagnostic criteria), sample size, randomization design, intervention/comparator, endpoint definitions and analysis method from full text/supplement.
4. Verify numeric estimates, confidence intervals, p values, harms, and duration against original sources; never infer a mortality benefit from composite outcomes.
5. Record reviewer identity, extraction dates, inclusion/exclusion decisions and discrepancies. Have a second reviewer verify and adjudicate.
6. Only then migrate a record into the more detailed `data/studies.json` format and regenerate exports with `python scripts/export_csv.py`.

## Limitations

No finite search is literally 'everything on the internet'. The PubMed query omits nonindexed literature and may be constrained by pagination limits. ClinicalTrials.gov records can represent ongoing and unpublished studies. The same trial often produces several publications; DOI/PMID deduplication cannot by itself detect all trial-level duplicates. Indexing may be delayed or corrected; manual screening and citation chasing are still required. For a future systematic review, establish a preregistered protocol, full search dates and strings, dual screening, cross-database searches (including Embase/CENTRAL where licensed), and a transparent exclusion log.
