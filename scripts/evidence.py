"""Pure-Python data and filtering helpers for the HFpEF Evidence Navigator.

This module does not access the network or interpret the strength of clinical evidence.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load_records() -> tuple[dict[str, Any], dict[str, Any]]:
    trials = json.loads((DATA / "studies.json").read_text(encoding="utf-8"))
    guidance = json.loads((DATA / "guidelines.json").read_text(encoding="utf-8"))
    return trials, guidance


def result_status(study: dict[str, Any]) -> str:
    statuses = [o.get("significant") for o in study.get("primary_outcomes", [])]
    if not statuses or any(v is None for v in statuses):
        return "Not fully extracted"
    if all(statuses):
        return "All primary endpoints significant"
    if any(statuses):
        return "Mixed primary endpoint results"
    return "Primary endpoint(s) not significant"


def flatten_study(s: dict[str, Any]) -> dict[str, Any]:
    ref = s["reference"]
    pop = s["population"]
    return {
        "Record type": "Study",
        "Study": s["acronym"],
        "Title": s["title"],
        "Year": s["year"],
        "Journal": s["journal"],
        "Study type": s.get("study_type", "Randomized trial"),
        "Treatment category": s["treatment_category"],
        "Intervention": s["intervention"]["name"],
        "Comparator": s["intervention"]["comparator"],
        "Population": pop["summary"],
        "Sample size": pop["sample_size"],
        "LVEF eligibility": pop["lvef_eligibility"],
        "Outcome categories": "; ".join(s.get("outcome_tags", [])),
        "Population tags": "; ".join(s.get("phenotype_tags", [])),
        "Primary endpoints": " | ".join(o["name"] for o in s["primary_outcomes"]),
        "Primary endpoint results": " | ".join(o["result_text"] for o in s["primary_outcomes"]),
        "Primary result status": result_status(s),
        "Interpretation": s.get("interpretation", ""),
        "DOI": ref["doi"],
        "PMID": ref["pmid"],
        "ClinicalTrials.gov ID": ref.get("clinicaltrials_id", ""),
        "Source URL": ref["pubmed_url"],
        "Verification": s["curation"]["verification_status"],
        "Last source check": s["curation"]["last_source_check"],
    }


def flatten_guideline(g: dict[str, Any]) -> dict[str, Any]:
    return {
        "Record type": "Guidance",
        "Study": g["short_name"],
        "Title": g["title"],
        "Year": g["year"],
        "Journal": g["organization"],
        "Study type": g["study_type"],
        "Treatment category": "Guidance document",
        "Intervention": "",
        "Comparator": "",
        "Population": g.get("summary", ""),
        "Sample size": "",
        "LVEF eligibility": "",
        "Outcome categories": "; ".join(g["topics"]),
        "Population tags": "",
        "Primary endpoints": "",
        "Primary endpoint results": "",
        "Primary result status": "Not applicable",
        "Interpretation": "Guidance; not an interventional trial",
        "DOI": g["doi"],
        "PMID": g["pmid"],
        "ClinicalTrials.gov ID": "",
        "Source URL": g["source_url"],
        "Verification": g["verification_status"],
        "Last source check": g["last_source_check"],
    }


def csv_text(rows: Iterable[dict[str, Any]]) -> str:
    data = list(rows)
    if not data:
        return ""
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=list(data[0]), extrasaction="ignore")
    writer.writeheader()
    writer.writerows(data)
    return buf.getvalue()


def filter_studies(
    studies: list[dict[str, Any]], *, keyword: str = "", types: list[str] | None = None,
    categories: list[str] | None = None, outcome_tags: list[str] | None = None,
    phenotype_tags: list[str] | None = None, statuses: list[str] | None = None,
    years: tuple[int, int] | None = None,
) -> list[dict[str, Any]]:
    query = keyword.casefold().strip()
    output = []
    for study in studies:
        if types and study.get("study_type", "Randomized trial") not in types:
            continue
        if categories and study["treatment_category"] not in categories:
            continue
        if outcome_tags and not set(outcome_tags).intersection(study.get("outcome_tags", [])):
            continue
        if phenotype_tags and not set(phenotype_tags).intersection(study.get("phenotype_tags", [])):
            continue
        if statuses and result_status(study) not in statuses:
            continue
        if years and not years[0] <= study["year"] <= years[1]:
            continue
        haystack = json.dumps(
            {k: v for k, v in study.items() if k != "curation"}, ensure_ascii=False
        ).casefold()
        if query and query not in haystack:
            continue
        output.append(study)
    return sorted(output, key=lambda s: (-s["year"], s["acronym"].casefold()))


def filter_guidelines(guidelines: list[dict[str, Any]], *, keyword: str = "", topics: list[str] | None = None) -> list[dict[str, Any]]:
    query = keyword.strip().casefold()
    return [g for g in guidelines if (not topics or set(topics).intersection(g["topics"])) and
            (not query or query in json.dumps(g, ensure_ascii=False).casefold())]
