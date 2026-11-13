**v0.4.0 | Discovery + opt-in LLM draft extraction | Updated November 12, 2026**nical Evidence Navigator

**v0.3.0 | 22 preliminary detailed studies + 3 guidance documents + 1,660 unreviewed discovery candidates | Updated November 12, 2026**

A small, reproducible, public-facing **Python/Streamlit** prototype organizing selected trial findings and guidance related to heart failure with preserved ejection fraction (HFpEF) and adjacent mildly reduced EF populations. The previous static GitHub Pages website is preserved.

> **Research and education only — not for clinical decision-making.** Records have undergone selective publication/abstract-level checks, **not** independent full-text verification, systematic screening, guideline recommendation extraction, clinical adjudication, or formal risk-of-bias assessment. Sources and exact EF eligibility vary; results must not be pooled casually.

## Literature discovery expansion (v0.3)

Following mentor feedback, an initial set of 15 manually checked bibliographic links seeded a live API discovery search. GitHub Actions successfully completed the first run, producing **1,660 candidate records** (1,310 PubMed publications plus 350 ClinicalTrials.gov registrations). Together with 22 preliminary detailed study records and 3 guidance documents, the repository contains **1,685 indexed records**, **not 1,685 independent HFpEF studies**. Candidates include observational studies, follow-ups, protocols and potentially irrelevant matches that require screening. The search log records **truncated query windows**, so this is not exhaustive.

- `data/discovery_seed.json`: source-linked PubMed seed records
- `data/discovery_candidates.json` and `data/discovery_candidates.csv`: separate searchable review queue
- `scripts/discover_literature.py`: PubMed ESearch/ESummary and ClinicalTrials.gov API v2 discovery, deduplication and pagination
- `data/discovery_search_log.json`: search provenance and truncation tracking
- `.github/workflows/literature-discovery.yml`: weekly/on-demand API collection, subject to GitHub Actions permissions
- `docs/DISCOVERY_METHODS.md`: scope, limitations, and human review process

Recreate the seed with `python scripts/discover_literature.py --offline` or run the live API search without `--offline` on an internet-connected computer. **The first GitHub Actions live API crawl succeeded on November 12, 2026.** It was not independently reproduced in the local offline environment; future weekly runs depend on the GitHub Actions configuration and permissions. Clinical outcomes are never automatically synthesized or promoted from a citation alone. This is not a comprehensive systematic review.

## LLM-assisted extraction drafts (v0.4)

**New: opt-in research extraction, not automatic clinical publication.** The [manual GitHub Actions extraction workflow](.github/workflows/extraction-drafts.yml) selects 1–10 PubMed publications already found by the discovery crawler, retrieves available **PubMed abstracts**, and calls an LLM to produce structured clinical fields and source-linked knowledge units. Every populated field must have a short verbatim source excerpt. Basic evidence-substring and numerical consistency checks flag possible unsupported claims; an optional second LLM call audits contextual support and omissions.

**Requirements:** Set your own `OPENAI_API_KEY` as a GitHub Actions repository secret before running the workflow; this is a paid model API and will not execute without credentials. It is manual-trigger-only to avoid unintended charges. After a run, download the **unreviewed-extraction-drafts** artifact; the draft JSON files are not committed, incorporated into `data/studies.json`, or shown as validated clinical results. The GitHub Pages site remains a static research index; the extraction agent is a separate server-side batch workflow.

To run locally:

```bash
python scripts/extract_candidates.py --limit 3 --priority High --llm-check
python scripts/extract_candidates.py --pmids 41697954 --limit 1
python -m unittest discover -s tests -v
```

Use `--source-text /path/to/authorized_fulltext.txt` with one explicit PMID to inspect a locally supplied, appropriately licensed complete document. The model then processes that text via an external API. The default public API ingestion is **abstract-only**, so no claims of full-text completeness are supported.

**[Read the full setup, source verification, and limitations](docs/LLM_EXTRACTION.md).** Automated retrieval and source-quote matching do not replace independent full-text extraction and human verification; the formal promotion path is still described in [the screening protocol](docs/SCREENING_AND_EXTRACTION.md).

## Features

- **22 study records** selected from different trial eras, including both neutral and positive findings.
- **3 guidance records**: 2022 AHA/ACC/HFSA HF guideline, 2023 ESC focused update, and 2023 ACC HFpEF expert consensus decision pathway (labeled as consensus, not a graded formal guideline).
- Streamlit searches and filters by **study design, treatment, endpoint family, enrolled phenotype, primary result status, and publication year**.
- Side-by-side descriptive comparison of **up to four selected studies**, with endpoint definitions and original citations visible.
- Direct PubMed/DOI links and ClinicalTrials.gov links **when a confirmed registration ID was recorded**.
- CSV exports for studies, guidance and all 25 evidence records, plus filtered JSON download.
- Validation and regression tests using built-in Python `unittest`.

## Project files

```text
.
├── streamlit_app.py               # Python/Streamlit application
├── requirements.txt               # Python dependencies
├── .streamlit/config.toml         # Theme
├── data/
│   ├── studies.json               # Canonical clinical-trial data
│   ├── guidelines.json            # Canonical guidance records
│   ├── studies.csv                 # Export snapshot
│   ├── guidelines.csv              # Export snapshot
│   └── evidence_index.csv         # All 25 records in one table
├── scripts/
│   ├── evidence.py                # Data, filters, flattening, export logic
│   ├── validate_data.py           # Basic structural validation
│   └── export_csv.py              # Rebuild CSV snapshots from JSON
├── tests/test_evidence.py         # Offline checks
├── docs/EXTRACTION_PROTOCOL.md    # Provenance and reviewer workflow
├── index.html                     # Original GitHub Pages website
└── assets/                        # Original HTML site CSS/JavaScript
```

## Run Streamlit locally

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then visit the local address printed by Streamlit (usually `http://localhost:8501`).

## Deploy the Streamlit version

1. Push this repository to your GitHub account (already tracked under `catherinemhnguyen/hfpef-clinical-evidence-navigator`).
2. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub.
3. Choose **Create app** → **Deploy a public app from GitHub**.
4. Select the repository `catherinemhnguyen/hfpef-clinical-evidence-navigator`, branch `main`, and app file `streamlit_app.py`.
5. Deploy, then verify search, comparison, guidance and download controls on the public app.

**Deployment status:** GitHub Pages hosts the original *static* interface, which now lists the 22 studies. **Streamlit deployment is a separate step**, requiring the account owner to authorize Streamlit Community Cloud. Do not confuse the successful GitHub Pages build with an active Streamlit application.

## Use or edit the data

JSON is the **source of truth**. Do not hand-edit CSV exports. To add a study, append a JSON object with a unique `id`, an accurate source, explicit EF eligibility, intervention/comparator, primary endpoint structure, and conservative verification status. Missing numerical effect estimates should be `null` and should be described as unextracted rather than guessed.

After editing:

```bash
python scripts/validate_data.py
python scripts/export_csv.py
python -m unittest discover -s tests -v
```

The structural validator checks field consistency, DOI/PMID formatting, a nonempty, growing inventory, and coherence of confidence intervals where numeric results are entered. **These tests do not check actual scientific accuracy, full-text fidelity, or physician agreement.**

## How this aligns with the initial mentor proposal

| Proposed milestone | Current prototype |
| --- | --- |
| 20–30 studies/guidance sources | 22 study records plus 3 guidance documents |
| Structured CSV/database | Canonical JSON plus reproducible CSV exports |
| Python + Streamlit website | `streamlit_app.py` with search and multi-select filters |
| GitHub hosting | Public GitHub repository; static site already on GitHub Pages |
| Verification and iteration | Source metadata/abstract checks, audit statuses and offline code tests; independent review **pending** |
| Automation later | CSV generation is automated; PubMed discovery via public APIs is now automated, avoiding premature extraction error |

## Clinical/research limitations

- This is a **purposefully selected** library, not a systematic review or meta-analysis. No PRISMA flow, exhaustive searches, or formal GRADE assessment.
- Study endpoints differ (clinical events, recurrent events, exercise capacity, biomarkers, KCCQ scores, body weight); effect measures are not interchangeable.
- Several studies enrolled EF >40% or ≥45% and should not be labeled as restricted to EF ≥50%.
- A tag such as `Obesity` describes trial enrollment criteria, **not a validated interaction effect**.
- Guidelines are **not** reduced to clinical recommendations; exact recommendation text, class and evidence level require targeted extraction and attribution.
- Trial registration IDs are included only when recorded; a blank field means **not yet extracted**, not "not registered".
- Review field values remain preliminary until independent checking by a research collaborator and qualified clinical reviewer.

See [`docs/EXTRACTION_PROTOCOL.md`](docs/EXTRACTION_PROTOCOL.md) for the review plan and reviewer worksheet. All clinical assertions should be checked in linked primary sources before public-facing scholarly claims.

## Selected sources

Links to the original bibliographic records are embedded alongside **every** study and guidance record in the JSON and both website interfaces. For example: [CHARM-Preserved](https://pubmed.ncbi.nlm.nih.gov/13678871/), [EMPEROR-Preserved](https://pubmed.ncbi.nlm.nih.gov/34449189/), [DELIVER](https://pubmed.ncbi.nlm.nih.gov/36027570/), [SUMMIT](https://pubmed.ncbi.nlm.nih.gov/39555826/), [2022 AHA/ACC/HFSA guideline](https://pubmed.ncbi.nlm.nih.gov/35363499/), and [2023 ACC HFpEF pathway](https://pubmed.ncbi.nlm.nih.gov/37137593/).

## Screening and extraction workflow (v0.4)

To expand beyond 22 detailed studies without inventing results or counting multiple reports as independent trials, the project now has a **separate evidence-screening layer**:

- [All bibliographic candidates](data/discovery_candidates.csv): public-API metadata, not clinical claims.
- [Automated triage](data/triage_queue.csv): all candidates assigned provisional priority, report type, and title-based possible parent-trial hints. **No automated eligibility decisions**.
- [First 50 title-level suggestions](data/title_triage_first50.csv): an initial practical review batch. These are not 50 completed abstract screens.
- [Human decisions ledger](data/screening_decisions.csv): stable file reserved for reviewer decisions; the weekly discovery workflow does **not** overwrite it. Record decisions against exact candidate IDs.
- [Ten source-linked extraction drafts](data/abstract_extraction_drafts.csv): PubMed abstract-level records across original randomized trials, a trial-design paper, observational studies, and a pooled analysis. **No independent full-text confirmation or second reviewer yet**; drafts are not promoted to `studies.json`.
- [Screening and extraction methods](docs/SCREENING_AND_EXTRACTION.md): eligibility rules, citation-to-trial linkage, verification process, and audit fields.

Run `python scripts/triage_candidates.py` to regenerate the candidate review queue; the scheduled GitHub Actions workflow also performs this step. Python validation no longer fixes the study inventory to exactly 22, allowing addition of truly reviewed studies. The Python files can be tested with `python -m unittest discover -s tests -v`.

**Next scientific milestone:** verify eligible records with original manuscripts/protocols and independent adjudication. Automated title relevance is not full-text eligibility, and PubMed abstract transcription is not medical/clinical validation. 
