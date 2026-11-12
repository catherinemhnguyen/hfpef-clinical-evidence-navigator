# HFpEF candidate screening workflow

The automated discovery has retrieved **1,660 bibliographic candidates** as of November 12, 2026, **not 1,660 independently validated HFpEF studies**. Keep the existing 22 detailed studies separate.

## Rebuild the review queue

```bash
python scripts/triage_candidates.py
```

This reads `data/discovery_candidates.json` and produces `data/screening_priority.csv` with deterministic **high / medium / low** review priorities. It does **not** assign inclusion decisions, verify abstracts, infer outcomes, or add items to `data/studies.json`.

The ranking is a keyword-based aid, not a machine-learning relevance estimate. High-scoring records may be irrelevant or duplicate reports; low-scoring entries can still be important. Review every citation before making any completeness claim.

## Record decisions separately

The file `data/screening_decisions.csv` is the persistent **human-review ledger**. Add one row per source candidate ID, with a decision of `include`, `exclude`, `uncertain`, `duplicate`, or `awaiting full text`. Record a reason, publication type, NCT number (when confirmed), reviewer and date. Never record assumed NCT IDs or effect estimates.

Example:

```csv
id,decision,reason,record_type,trial_id,reviewer,review_date,notes
pmid-EXAMPLE,uncertain,Awaiting full-text eligibility review,primary report,,,, 
```

That example ID is a placeholder, **not** a real candidate. The actual template contains the header only.

After the next weekly discovery run, rerun the triage command. Decisions are joined by stable candidate ID and persist even if a candidate is absent from the latest crawl. Do not store screening decisions inside `discovery_candidates.json`, because automated regeneration would discard them.

## Review and inclusion criteria

1. Screen title and abstract for population and endpoint relevance; resolve ambiguous studies with full text.
2. Label the **publication** type: primary report, secondary/subgroup report, observational cohort, trial registration, guideline, review, protocol, or other.
3. Identify trial registration numbers from source documents. Link publications from the same trial before counting independent studies; PMID/DOI de-duplication alone is insufficient.
4. Confirm exact EF threshold, whether HFpEF-only or mixed HFmrEF/HFpEF, study design and primary endpoint. Document exclusions explicitly.
5. Independently extract and double-check outcomes, adverse effects, sample size and effect estimates before promoting a publication to the curated JSON. A second reviewer should resolve discrepancies.
6. Report separate numbers for citations discovered, publications screened, unique trials, included studies and fully verified records.

The current discovery log contains truncated PubMed and ClinicalTrials.gov search windows. For more comprehensive retrieval, increase the search caps or stratify searches by publication year, test for completeness, and archive queries/dates. Additional databases and backward/forward citation searches may be needed for a defensible systematic review.

## Safety

The project is for research/education, not patient care. Keep missing clinical values blank and mark uncertainties rather than generating guessed findings. The triage output is a **review queue**, not a clinical evidence synthesis.
