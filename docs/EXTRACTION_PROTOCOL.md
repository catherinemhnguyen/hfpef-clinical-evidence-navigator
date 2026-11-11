# Evidence extraction and independent review protocol (working draft)

**Version 0.2 (November 11, 2026).** This document specifies how to improve the existing curated pilot. It is **not** a registered review protocol and does not claim systematic review methods were completed.

## 1. Purpose and scope

Create a searchable evidence dataset of selected interventional HFpEF/HFmrEF-spectrum studies and guideline documents, prioritizing traceability and cautious interpretation over large-scale automatic extraction.

## 2. Inclusion approach for the existing 25 records

The 22 study records were purposively chosen to span older and newer therapy classes, medical-device/lifestyle work, and clinical versus functional outcomes. The 3 guidance records are selected source documents from U.S. and European groups. This is a **convenience/landmark selection**, not an exhaustive search. Do not characterize the collection as a systematic review, imply completion of two-reviewer screening, or generate a retrospective PRISMA diagram.

## 3. Source hierarchy

1. Original study manuscript and published supplement, including protocol/statistical analysis plan if available.
2. Official trial registration (ClinicalTrials.gov), including dates, eligibility, and outcome version history.
3. PubMed bibliographic record and abstract, for initial metadata cross-checks.
4. Original guideline/consensus document, for recommendation-specific abstraction.

Secondary summaries may assist discovery but **do not replace the primary source** for numerical extraction.

## 4. Minimum fields and extraction checks

For each trial: unique ID, full title, citation, DOI/PMID, optional verified NCT identifier, year, study design, randomized N, exact EF eligibility, inclusion/exclusion criteria, phenotype inclusion, intervention and comparator doses, prespecified primary endpoint(s), outcome analysis type, numerical estimate, confidence interval, p value, overall significance, limitations, and source-verification date.

In interpreting results, distinguish hazard ratio vs rate ratio vs win ratio vs mean difference; time-to-first-event vs recurrent-event analyses; co-primary outcomes vs exploratory secondary findings; and subgroup findings vs overall trial conclusions. Record `null` for values not yet extracted.

For each guidance source: document type (guideline vs expert consensus), year/version, organization, exact recommendation wording, section/table reference, class and evidence level **only where formally defined**, and link to supporting trial(s). The current three records **do not yet** include individual recommendation extraction.

## 5. Proposed two-reviewer adjudication

- **Extractor A:** complete a source-specific worksheet from primary paper, supplement, and registration.
- **Reviewer B:** independently verify core fields and numerical values without seeing A's final extraction.
- **Resolve differences:** document disagreements and their resolution against original text; escalate ambiguous endpoints to a clinician.
- **Adjudication log:** document reviewer initials, review date, article version, change reason and field-level corrections.
- **Final approval:** label a record *full-text verified* only after this process is actually completed.

Do not substitute code-level JSON validation for scientific verification.

## 6. Suggested audit worksheet (fill manually)

| Field | Extractor A | Reviewer B | Final agreed value | Page/table or source link |
| --- | --- | --- | --- | --- |
| PMID / DOI / NCT | | | | |
| Study eligibility / EF cutoff | | | | |
| Randomized N / analysis N | | | | |
| Primary outcome and analysis | | | | |
| Effect estimate, 95% CI, p | | | | |
| Adverse events / harms | | | | |
| Risk-of-bias / limitation notes | | | | |
| Comments and adjudication | | | | |

## 7. QA before showing to a clinical mentor

- Run JSON structural validation and unit tests; regenerate CSV snapshots.
- Verify all hyperlinks and publication identifiers manually.
- Confirm whether some HFmrEF-including studies should be omitted under the selected EF definition.
- Re-extract and adjudicate numerical outcomes with a second reviewer.
- Check latest clinical guidelines and whether the proposed documents should be replaced or supplemented.
- Ask clinical collaborators about acceptable inclusion criteria, evidence classification and usability goals.

## 8. Transparency and public information

Publish original paraphrases, study-level public data and links only. Do not include patient-level data, internal correspondence, copyrighted full-text reproductions, or unpublished confidential materials. Maintain a dated version history and correction log for future updates.
