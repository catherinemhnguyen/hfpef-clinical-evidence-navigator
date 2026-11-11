# HFpEF Clinical Evidence Navigator

A lightweight, **GitHub Pages-ready** educational prototype for searching selected landmark trials in heart failure with preserved or mildly reduced ejection fraction.

**Current status:** version 0.1.0 — six curated trial records, preliminary summaries, and no independent clinician validation. **Not clinical decision support.**

## What's included

- `index.html` — the website's landing page, filters, study cards, and methods section.
- `assets/styles.css` — responsive visual design.
- `assets/app.js` — JavaScript that reads the JSON, searches/filters studies, and exports filtered results.
- `data/studies.json` — **single source of truth** for the clinical data. Each study includes its population, EF eligibility, intervention/comparator, primary endpoint(s), results, DOI, PMID, and NCT ID.
- `scripts/validate_data.py` — a basic structural check of the dataset.

No npm installation, JavaScript framework, API key, or external backend is required.

## Preview on your computer

1. Unzip the project and open a terminal inside the `hfpef-clinical-evidence-navigator` folder.
2. Run:

   ```bash
   python -m http.server 8000
   ```

3. In your browser, visit **http://localhost:8000**.

> Opening `index.html` directly with `file://` may fail because browser security restrictions can block fetching local JSON. Use the local server instead.

## Put it on GitHub and publish it

### Browser method (no terminal Git required)

1. Create a **public** repository on [GitHub](https://github.com/new) called `hfpef-clinical-evidence-navigator`.
2. Extract this ZIP. In your new repository select **Add file → Upload files** and upload the *contents of the project folder*, preserving `assets/`, `data/`, and `scripts/` paths. GitHub's web upload supports dragging the extracted project files/folders into the upload area. **Do not upload only the ZIP.**
3. Commit the files to the `main` branch.
4. Go to **Settings → Pages → Build and deployment**, set **Source: Deploy from a branch**, **Branch: main**, **Folder: /(root)**, and select **Save**.
5. GitHub Pages will publish to `https://YOUR-USERNAME.github.io/hfpef-clinical-evidence-navigator/` once deployment completes (replace `YOUR-USERNAME`).

### Terminal method (if Git is installed)

```bash
git init
git add .
git commit -m "Build initial HFpEF evidence navigator"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/hfpef-clinical-evidence-navigator.git
git push -u origin main
```

Create the empty GitHub repository first, then enable Pages as above.

**Publishing note:** GitHub Pages websites are public; do not commit patient data, unpublished confidential results, or internal communications.

## Add another study

1. Open `data/studies.json` in VS Code or any text editor.
2. Duplicate an existing study object inside the `studies` array, then assign a new, unique `id`.
3. Replace the title, population, EF threshold, intervention, exact endpoint definition, effect measure and CI, and all source IDs.
4. Label the endpoint analysis accurately (e.g., time-to-first event, recurrent-event composite, KCCQ change). **Do not treat HR, RR, and between-group mean difference as interchangeable.**
5. Update `updated_at` and the study's curation/source-check fields.
6. Validate and reload the website:

   ```bash
   python scripts/validate_data.py
   ```

**Data quality rule:** Never label a trial's overall primary outcome positive when its prespecified result is not statistically significant. Preserve whether the source reports a hazard ratio, rate ratio, or difference, and avoid claiming an isolated mortality benefit based on a composite endpoint.

## Research development roadmap

- **v0.1**: six source-linked original RCTs, searchable filters, CSV/JSON export (this release).
- **v0.2**: full-text verification by a second reviewer; protocol details, registration status, follow-up period, adverse events, and risk-of-bias fields.
- **v0.3**: phenotype tags (obesity/AF/CKD/EF strata), guidelines mapped to studies, structured search provenance, reviewer audit log.
- **v1.0**: clinician-reviewed evidence summaries with a documented update process and clearly declared scope.

## Academic and clinical limitations

This is a **selected-study navigator**, not a systematic review, complete evidence synthesis, or diagnostic/treatment recommendation engine. Some trials include HF with mildly reduced or improved EF; verify inclusion and exclusion criteria in the full publication/protocol. The initial records have been checked against published abstracts and bibliographic records, but **full-text verification, expert adjudication, and independent data extraction remain outstanding**.

The content is original paraphrase of source articles, not copied abstracts. The source publications remain the authoritative reference. If used in a manuscript or shared with a mentor, describe this as an **early prototype** rather than as validated clinical evidence infrastructure.

## Initial source publications (primary reports)

| Trial | PMID | DOI |
|---|---|---|
| EMPEROR-Preserved | 34449189 | [10.1056/NEJMoa2107038](https://doi.org/10.1056/NEJMoa2107038) |
| DELIVER | 36027570 | [10.1056/NEJMoa2206286](https://doi.org/10.1056/NEJMoa2206286) |
| PARAGON-HF | 31475794 | [10.1056/NEJMoa1908655](https://doi.org/10.1056/NEJMoa1908655) |
| TOPCAT | 24716680 | [10.1056/NEJMoa1313731](https://doi.org/10.1056/NEJMoa1313731) |
| STEP-HFpEF | 37622681 | [10.1056/NEJMoa2306963](https://doi.org/10.1056/NEJMoa2306963) |
| FINEARTS-HF | 39225278 | [10.1056/NEJMoa2407107](https://doi.org/10.1056/NEJMoa2407107) |

## Suggested mentor questions

1. Should the initial scope include only trials with LVEF ≥50%, or clearly tagged HFmrEF/HFpEF spectrum studies too?
2. What fields must be physician-validated before a record is labeled *reviewed*?
3. Should the navigator prioritize trial-level evidence, guideline recommendation mapping, or both?
4. What minimum extraction and audit documentation would make the dataset appropriate for a methods publication?