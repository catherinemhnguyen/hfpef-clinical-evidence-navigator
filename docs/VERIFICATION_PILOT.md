# Independent verification pilot (November 2026)

**Goal:** Answer how reliably the HFpEF agents extract study facts and how often a second LLM finds errors. This is an evaluation workflow, not a claim that 1,660 discovered records are verified.

## Current guardrails

- Scheduled discovery continues to gather bibliographic **candidates**.
- Scheduled abstract extraction creates **AI drafts** and AI audit reports in GitHub Actions artifacts. It does not update `data/studies.json`.
- The public candidate explorer is explicitly **unverified**.
- New curated study rows require independent full-text human review and documented two-reviewer metadata before publication. A CI check verifies that metadata is present; it cannot verify scientific correctness.
- The LLM API key is a separate paid account credential. No API calls are made by the evaluation script.

## A reproducible pilot

1. Select **at least three different publication types**: (a) an original randomized trial, (b) a subgroup/secondary report, and (c) an observational cohort. A 10–20-document follow-up sample will give a more useful error profile. Keep original publication PMID distinct from parent trial NCT.
2. In **GitHub → Actions → HFpEF LLM extraction drafts (manual review only)**, choose the PMIDs, set `llm_check=true`, and choose a **small batch**. Leave `extraction_model=gpt-4.1-mini` for baseline. For a controlled higher-capability audit test, set `audit_model=gpt-6.1-sol` if the model is accessible and the API cost is acceptable. Confirm model identifiers and price with the API provider before the run.
3. Download the `unreviewed-extraction-drafts` run artifact and unpack the `pmid-*-draft.json` files into a local folder, for example `outputs/pilot-a/`. Do not check source text, API secrets, or identifiable reviewer notes into the public repo.
4. Generate a human worksheet (Python 3.11+; no additional packages):
   
   ```bash
   python scripts/evaluate_extractions.py --make-template --drafts outputs/pilot-a --output outputs/pilot-a-reviews.json
   ```

5. A real reviewer independently reads the **same abstract/input text** the model saw, confirms its publication identity and source hash, and fills **all twelve** fields in `outputs/pilot-a-reviews.json`:
   - `reviewer`: nonempty reviewer name or auditable ID
   - `review_date`: YYYY-MM-DD
   - `source_notes`: PMID and exact source/sections used, plus corrections when needed
   - `expected_present`: `true` if the field has an extractable answer **in the input text**; otherwise `false`
   - `extraction_correct`: `true` only if the AI correctly extracted that field, or correctly left a non-extractable field empty; otherwise `false`

   For example, when an abstract contains a sample size but the model omits it: `expected_present=true`, `extraction_correct=false`. When the source does not describe an adverse event and the model leaves safety empty: `expected_present=false`, `extraction_correct=true`. **Do not copy or automatically accept an auditor's verdict as human ground truth.** For ambiguous fields, adjudicate against the source before assigning a boolean. Keep review notes referencing source passages/sections. A more rigorous study should use two human adjudicators and reconcile disagreements.

6. Run the evaluator:
   
   ```bash
   python scripts/evaluate_extractions.py --reviews outputs/pilot-a-reviews.json --drafts outputs/pilot-a --output outputs/pilot-a-metrics.json
   ```

   It reports **extracted-field precision**, **extractable-field recall**, **all-field accuracy**, **auditor sensitivity to human-identified errors**, and **auditor correct acceptance rate**. An undefined denominator is reported as `null`, not 100%. It rejects blank reviews, incomplete fields, mismatched PMIDs, duplicate reviews, or source-hash mismatches.

7. Rerun the **same PMIDs** with a different extractor/auditor model combination. Make a **new review worksheet** for that second run, with an independent assessment of that model's actual output. Compare the two metric JSON reports, API usage cost, latency and types of errors. A model can have high precision but low recall. Small-sample results should not be generalized.
8. For **clinical approval**, conduct a separate full-text + supplements + registry/protocol review with two qualified human reviewers, check all clinical numerical fields, capture page/table locations, record adjudication, then propose a curated JSON change in a pull request. **Do not use abstract-only benchmark scores as a publication gate or claim physician verification.**

## What this pilot can and cannot establish

The pilot tests whether a model's **input-text extraction** is correct, and whether a second AI flags errors identified by humans. It does **not** establish that the underlying paper itself is scientifically valid, that original full texts were checked, that all relevant HFpEF articles were discovered, that the same article has not been counted twice across reports, or that future extractions will be equally accurate.

No benchmark results exist until humans fill and run the worksheets. The script does not generate or guess clinical ground-truth labels.

## Next deployment increment

1. Keep discovered metadata and unreviewed candidate counts public, clearly labeled.
2. After clinical verification, curate a **small diverse set (e.g., 10–20)** of additional study records and use the existing `curated-review-gate.yml` pull-request gate.
3. Regenerate `studies.csv` and `evidence_index.csv`; verify static GitHub Pages shows the approved additions.
4. Invite 3–5 cardiology research/clinical users for structured usability feedback, with no patient identifiers or medical advice requests: see [CLINICIAN_FEEDBACK.md](CLINICIAN_FEEDBACK.md).

**Stop condition:** If auditing fails to catch serious unsupported claims, if the benchmark is inaccurate, or if reviewers disagree on clinical effect estimates, leave those records out of the curated site and revise the system before scaling.
