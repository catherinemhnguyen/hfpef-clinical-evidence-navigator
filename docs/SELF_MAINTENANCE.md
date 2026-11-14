# Self-maintaining HFpEF research index — operating guide (November 2026)

The website has two clearly different layers:
1. **Discovery candidates** are public bibliographic metadata from PubMed and ClinicalTrials.gov. Their presence does not establish HFpEF eligibility, study uniqueness, or clinical validity.
2. **Detailed selected studies** in `data/studies.json` are source-checked research prototypes. Even these original 22 records lack independent full-text/clinician validation; they must not be labeled as clinically approved.

## Automated workflow

- `.github/workflows/literature-discovery.yml`: Monday/Wednesday/Friday at 08:17 UTC (subject to GitHub Actions timing and settings). Uses public APIs and updates the unreviewed candidate files and title triage queue.
- `.github/workflows/scheduled-extraction.yml`: Monday/Wednesday/Friday at 09:17 UTC, selects up to **two** previously successfully processed-free, high-priority PubMed IDs; retrieves abstracts; creates LLM structured drafts; always requests a second LLM audit. The raw source excerpts and clinical drafts are retained in **Actions artifacts for 30 days**, not added to the public website. The public `data/extraction_attempts.json` ledger stores only bibliographic PMIDs and processing status. Failed candidates can be retried, and manual runs are available.
- If the repo secret `OPENAI_API_KEY` is missing, the paid extraction stage **skips safely**. A connected ChatGPT subscription does not provide this API key. GitHub Actions and model API usage may incur costs; review billing and usage limits. Default model is `gpt-4.1-mini`; verify availability and pricing before enabling.
- Scheduled workflows are not guaranteed to fire at the exact minute. The extraction workflow reads the most recently committed discovery data; it is not guaranteed to wait for a concurrently running discovery job. The crawler and extraction workflows both need successful GitHub Actions permissions.

## Clinical safety gates and reviewer workflow

The auditor checks extracted fields and possible omissions using a second model, but **this does not prove correctness, completeness, trial eligibility, or lack of hallucinations**. Any automated output remains an AI draft. No automated process updates `data/studies.json`.

To publish a verified new clinical record:
1. Screen title and abstract, classify publication and link the parent trial, and document the screening decision separately.
2. Obtain legally accessible original full text, supplements, registry and/or protocol and check study design, EF criteria, denominators, outcome definitions, effect sizes, uncertainty, limitations, and publication identity.
3. Have two **different human reviewers** independently verify clinically material data and record source page/table/section identifiers, date, discrepancies and adjudication in the curation fields.
4. Add or modify the structured entry in `data/studies.json` on a pull request, set `curation.reviewer`, `curation.second_reviewer`, `curation.source_basis` (include full text), `curation.review_notes` (source page/table/section and resolution), and a truthful verification status.
5. The `curated-review-gate.yml` PR workflow checks metadata, structural validity, and regression tests. It does **not** authenticate reviewer identities or validate clinical truth; a human must still check the underlying evidence.
6. After approval and merge, regenerate CSV exports using `python scripts/export_csv.py` and confirm the public site. The static site reads `data/studies.json` directly, so the new approved JSON study record appears without editing site HTML. CSV exports must be regenerated separately.

**Repository owners should enable branch protection requiring pull requests, relevant status checks, and actual human approval.** Without branch protection, a direct push can bypass the PR-based check. Do not falsely claim these controls are already enabled.

## Checklist before calling it fully automatic

- [ ] Add `OPENAI_API_KEY` under GitHub repository Settings → Secrets and variables → Actions if you authorize API charges.
- [ ] Test the discovery workflow and the scheduled extraction workflow on demand in GitHub Actions.
- [ ] Download and manually inspect draft artifacts and second-model audit results, including negative cases.
- [ ] Configure branch protection and human reviewer requirements.
- [ ] Confirm GitHub Pages displays fresh candidate counts and that study-review labels are accurate.
- [ ] Evaluate extraction accuracy/completeness on a manually adjudicated sample before scaling.

This is a research/educational prototype, not a systematic review, medical advice, or clinical decision support.
