# HFpEF Clinical Evidence Navigator

**v0.2.0 | 22 selected research studies + 3 published guidance documents | Updated November 11, 2026**

A small, reproducible, public-facing **Python/Streamlit** prototype organizing selected trial findings and guidance related to heart failure with preserved ejection fraction (HFpEF) and adjacent mildly reduced EF populations. The previous static GitHub Pages website is preserved.

> **Research and education only — not for clinical decision-making.** Records have undergone selective publication/abstract-level checks, **not** independent full-text verification, systematic screening, guideline recommendation extraction, clinical adjudication, or formal risk-of-bias assessment. Sources and exact EF eligibility vary; results must not be pooled casually.

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

The structural validator checks field consistency, DOI/PMID formatting, the limited 22+3 inventory, and coherence of confidence intervals where numeric results are entered. **These tests do not check actual scientific accuracy, full-text fidelity, or physician agreement.**

## How this aligns with the initial mentor proposal

| Proposed milestone | Current prototype |
| --- | --- |
| 20–30 studies/guidance sources | 22 study records plus 3 guidance documents |
| Structured CSV/database | Canonical JSON plus reproducible CSV exports |
| Python + Streamlit website | `streamlit_app.py` with search and multi-select filters |
| GitHub hosting | Public GitHub repository; static site already on GitHub Pages |
| Verification and iteration | Source metadata/abstract checks, audit statuses and offline code tests; independent review **pending** |
| Automation later | CSV generation is automated; **PubMed ingestion is not yet automated**, avoiding premature extraction error |

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
