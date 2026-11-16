# HFpEF bibliography: scalable and auditable verification

**Implemented:** November 16, 2026. **Purpose:** Distinguish real, source-linked bibliographic candidates from citation/identifier errors. This is **not** clinical accuracy validation.

## The existing two layers remain separate

- `data/discovery_candidates.json`: automatically discovered **unreviewed citations and trial registrations**, not 1,663 unique HFpEF trials.
- `data/studies.json`: 22 selected detailed study summaries awaiting independent clinical validation. No automated code adds or modifies these records.

## Step 1: check every record against deterministic rules

`python scripts/verify_candidates.py` performs zero network calls by default, rechecking all candidate IDs, PubMed URLs, ClinicalTrials.gov URLs, title presence, reasonable year format, optional DOI syntax, and duplicate PMIDs/DOIs/NCT IDs. It emits:

- `data/verification_report.json`: aggregate counts; clearly marked as **bibliographic**, not clinical verification.
- `data/verification_flags.csv`: problematic bibliographic IDs, relevant metadata, and reasons.
- `data/verification_online_ledger.json`: checks of separately retrieved original public-source records.

These are public metadata outputs, with no raw medical records or model-generated trial outcomes.

## Step 2: independent API re-fetch on a capped batch

The existing Monday/Wednesday/Friday discovery workflow now runs:

```bash
python scripts/verify_candidates.py --online-limit 20
```

It re-fetches up to **20 previously unchecked candidates** from one of:
- **PubMed EFetch XML**, separately from the ESummary metadata used during discovery, matching publication PMID, title and any available DOI.
- **ClinicalTrials.gov API v2 individual study endpoint**, matching NCT ID and title.

Every source check records a timestamp and one of `identity_match`, `identity_mismatch` or `unavailable`. **Unavailable is not success.** Candidates with malformed metadata are not granted a matching source check. Older source checks are invalidated if identity fields change, and stale IDs are dropped. This is a bounded, incremental process, **not** a claim that every candidate has been separately re-fetched already.

No citation-only match proves HFpEF eligibility or correct effect estimates, and no model is permitted to infer an endpoint from its memory. Reviewers must resolve exceptions against original published sources.

The crawler periodically updates the public metadata report and the front page displays the number of separately cross-checked **bibliographic identities**, not physician-approved clinical studies.

## Step 3: structured LLM drafting and independent auditing

New default (provided a separately paid OpenAI API key is configured):
- **Extraction:** `gpt-6-luna`.
- **Auditor:** `gpt-6.1-sol`.

The scheduled batch remains limited to **two abstracts per Monday, Wednesday, Friday run**, with the auditor enabled. The manual Actions workflow allows independent model choices; it now defaults to an auditor but can be disabled for a controlled baseline comparison. Costs and service access depend on your OpenAI API account.

**The current secret `OPENAI_API_KEY` is absent or not available to scheduled Actions**, based on the November 16 workflow skipping extraction. Therefore newer models are configured, **not yet demonstrated as executed**. ChatGPT subscription access does not grant an OpenAI API key.

AI drafts, snippets, source evidence matches, and model judgments remain in temporary GitHub Actions artifacts, not the public clinical data file.

## Step 4: evaluate reliability before promotion

Use [VERIFICATION_PILOT.md](VERIFICATION_PILOT.md) for a 3-paper pilot, then a larger stratified sample with independently adjudicated field-level reference labels. Compare extraction precision, recall, numerical and endpoint accuracy, missing qualifications, and auditor error detection. Clinical outcomes require review against authorized full text, supplements, and any trial registration, with two independent human reviewers for newly promoted clinical data.

**Do not report verified clinical accuracy until completed, documented validation actually exists.**

## Step 5: get prospective users involved

The public website has a **Give feedback** link that opens a standardized GitHub Issue Form. It asks user role, feature tested, task, outcome and suggested improvement; it explicitly prohibits patient data. Users need a GitHub account to submit. See [CLINICIAN_FEEDBACK.md](CLINICIAN_FEEDBACK.md) for a 15-minute clinician/researcher pilot.

This implements the technical feedback loop Dr. Thanhvu suggested, but **does not mean cardiologists have already been recruited**.

## Operational checks

1. In GitHub → Actions, confirm the literature discovery run succeeds and `verification_report.json` appears on `main`.
2. Check `verification_flags.csv` for mismatched DOI/title/identifiers; do not automatically delete ambiguous papers.
3. Confirm the website reports source-identity matches separately from its detailed-study count.
4. Enable `OPENAI_API_KEY` only if you approve separate API charges, review model pricing and set usage limits.
5. Run a small manual three-PMID extraction pilot and download the resulting artifacts for human reference evaluation.
6. Use real cardiologist/researcher feedback to prioritize website changes.

### What this system does *not* do

This is not a systematic review, a guarantee of exhaustive worldwide HFpEF literature coverage, independent physician verification of 1,663 articles, a clinical decision-support service, or automated publication of unverified efficacy/safety claims.
