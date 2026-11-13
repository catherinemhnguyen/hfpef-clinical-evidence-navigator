# LLM-assisted HFpEF evidence extraction (v0.4 — draft-only)

## What the agent does

`python scripts/extract_candidates.py` selects up to ten **PubMed** papers from the existing discovery queue, downloads their public abstracts with NCBI EFetch, and asks an API-accessible LLM to propose structured clinical study fields and individual knowledge units. Each nonempty field requires a short verbatim source excerpt. The program checks for excerpt matches and obvious numeric mismatches. An optional **second LLM** judges contextual support and potential omissions.

**Important limitations:** These are *abstract-only* drafts, not extracted full-text trials, verified numerical findings, systematic review results, or proven complete knowledge lists. They are never published into `data/studies.json` automatically. Neither a matching quote nor a second model is proof that the scientific interpretation is correct. Keep the website's curated records and candidate queue distinct.

## Setup in GitHub (first run)

1. Open the repository → **Settings** → **Secrets and variables** → **Actions**.
2. Choose **New repository secret**, name it exactly `OPENAI_API_KEY`, and paste an API key that you own and are authorized to use. **Do not commit keys to files**. API use incurs charges based on your account's billing.
3. In **Actions**, open **HFpEF LLM extraction drafts (manual review only)** → **Run workflow**.
4. Select 1–3 documents for the pilot. You may provide comma-separated PMIDs from the discovery queue. The optional `llm_check` doubles the approximate number of model calls per document.
5. Open the successful run → **Artifacts** → download `unreviewed-extraction-drafts`. This ZIP contains JSON drafts and `batch_report.json`. Artifacts expire after 14 days.

No model API key is stored in the project or required for public website visitors. The extraction workflow is **manual-trigger-only**, avoiding unattended charges; the weekly discovery workflow remains independent. There are **no auto-commits or public displays** of AI drafts.

## Run on your computer

Requires Python 3.11+; uses the standard library. Set your API key in your shell, then:

```bash
python scripts/extract_candidates.py --limit 3 --priority High --llm-check
# Choose exact known PubMed IDs instead of title-ranked candidates:
python scripts/extract_candidates.py --pmids 42822640,41697954 --limit 2
# If you have a legally accessible full-text document converted to UTF-8 text:
python scripts/extract_candidates.py --pmids 41697954 --limit 1 --source-text /path/to/article.txt
python -m unittest discover -s tests -v
```

`--source-text` is **optional and local only**. Check the article's license and completeness first; do not commit copyrighted full text, abstracts, API keys, or confidential documents. The source file is never uploaded to GitHub by the script, though its text is sent to the model API for extraction. Review the model provider's data handling before processing nonpublic material. Do not process patient data.

Default model: `gpt-4.1-mini`, overridable using `--model MODEL` or `OPENAI_MODEL`; model compatibility, pricing, and availability can change. The script uses the OpenAI **Responses API** with strict JSON schema output and `store: false`, but the call still goes to an external provider. The key is never included in generated output.

## What each draft contains

- Original source URL, PMID/DOI, title and SHA-256 of the extracted source text.
- Report classification (original trial, subgroup analysis, observational study, protocol, etc.).
- Fields: study design, population, EF threshold, sample size, intervention/comparator, primary endpoint, effect estimate, confidence interval, p value, follow-up and safety.
- Knowledge units with short source quotes and a list of missing/unextractable information.
- Automated flags for quote absence and numerical inconsistencies.
- Optional second-model judgments and possible omissions.
- Explicit `human_approved: false` and pending-review status.

## Review before database entry

1. Manually verify that PMID/title/source match and that the abstract is really about HFpEF; verify whether the publication is a parent trial, secondary analysis, protocol, or an unrelated paper.
2. Retrieve original full text, supplement and registered protocol **through authorized access**. Compare all design, enrollment, endpoint and numeric details to original tables, including analysis type (HR vs RR, time-to-first vs recurrent event) and EF restrictions.
3. Have a second reviewer independently check numerical and core clinical fields, mark each as supported / corrected / unextractable, and log page/table citations.
4. Add reviewer identities, disagreements, and resolution to the screening/extraction records. Do not claim systematic completeness based on three sampled articles; a 3-paper pilot establishes an error estimate for the sample, not the entire corpus.
5. **Only after independent validation** manually adapt the information to the schema in `data/studies.json`, run `scripts/validate_data.py`, regenerate CSV with `scripts/export_csv.py`, and rerun tests.

For a reproducible pilot with Dr. Nguyen, choose three different publication types: original RCT, subgroup analysis, and observational cohort. Measure *per-field precision*, *knowledge-unit support*, and *recall against a human-written reference list*. A second LLM may flag concerns but cannot replace human gold-standard evaluation. Cite page/table/section for every accepted claim.

## Safety and integrity

The API prompt treats retrieved article text as untrusted data and forbids obeying instructions embedded in a paper. The only URL fetched by the script is NCBI EFetch, constructed from a validated numeric PMID (or an explicitly provided local UTF-8 text file); arbitrary discovered URLs are not crawled. Outputs live in ignored `outputs/` and workflow artifacts, never the verified dataset. Source quotes are intentionally short, but review copyright/attribution before distributing any extracted text. `store:false` disables response storage for supported API use, not necessarily all processing or logging by a provider.
