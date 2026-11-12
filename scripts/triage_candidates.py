#!/usr/bin/env python3
"""Produce a reproducible HFpEF citation screening queue.

This is *prioritization*, not inclusion adjudication or clinical extraction.
Never changes data/studies.json or the original discovery candidates.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DECISION_FIELDS = ["id", "decision", "reason", "record_type", "trial_id", "reviewer", "review_date", "notes"]
OUTPUT_FIELDS = ["priority", "score", "flag", "id", "source", "year", "title", "publication_type",
                 "url", "pmid", "nct_id", "doi", "decision", "reason", "record_type",
                 "trial_id", "reviewer", "review_date", "notes"]

DIRECT = re.compile(r"\b(hfpef|heart failure with preserved ejection fraction|diastolic heart failure|hfmr?ef|heart failure with mildly reduced ejection fraction)\b", re.I)
TRIAL = re.compile(r"\b(randomi[sz]ed|clinical trial|placebo|phase [1-4iv]+|double.blind|trial)\b", re.I)
IMPORTANT = re.compile(r"\b(primary results?|primary outcome|efficacy|mortality|hospitali[sz]ation|finerenone|semaglutide|tirzepatide|dapagliflozin|empagliflozin|sacubitril|spironolactone|interatrial shunt|exercise training)\b", re.I)
SECONDARY = re.compile(r"\b(subgroup|post hoc|post-hoc|secondary analysis|pooled analysis|meta.analysis|systematic review|protocol|design and rationale|economic|cost.effectiveness)\b", re.I)
BROAD = re.compile(r"\b(heart failure|cardiac|left ventricular|atrial)\b", re.I)
VALID = {"", "include", "exclude", "uncertain", "duplicate", "awaiting full text"}

def read_decisions(path: Path):
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    decisions = {}
    for row in rows:
        key = (row.get("id") or "").strip()
        if not key:
            continue
        decision = (row.get("decision") or "").strip().lower()
        if decision not in VALID:
            raise ValueError(f"Unknown decision {decision!r} for {key}")
        if key in decisions:
            raise ValueError(f"Duplicate screening decision id: {key}")
        decisions[key] = {field: (row.get(field) or "").strip() for field in DECISION_FIELDS}
        decisions[key]["decision"] = decision
    return decisions

def prioritize(record):
    title = (record.get("title") or "")
    kind = (record.get("publication_type") or "")
    source = (record.get("source") or "")
    combined = f"{title} {kind}"
    score = 0
    flags = []
    if DIRECT.search(title):
        score += 5
    elif DIRECT.search(combined):
        score += 3
    elif BROAD.search(title):
        score += 1
        flags.append("broad-heart-failure-only")
    else:
        flags.append("no-direct-HFpEF-in-title")
    if TRIAL.search(combined):
        score += 3
    if IMPORTANT.search(title):
        score += 2
    if SECONDARY.search(title):
        score -= 3
        flags.append("possible-secondary-publication")
    if source == "ClinicalTrials.gov":
        score += 1
        flags.append("registration-not-publication")
    if record.get("year") and int(record["year"]) > 2026:
        flags.append("future-year-check-publication-date")
    rank = "high" if score >= 8 else "medium" if score >= 4 else "low"
    return rank, score, "; ".join(flags)

def build(source: Path, decisions_path: Path, output: Path):
    raw = json.loads(source.read_text(encoding="utf-8"))
    records = raw.get("candidates")
    if not isinstance(records, list):
        raise ValueError("Expected top-level candidates list")
    decisions = read_decisions(decisions_path)
    seen = set()
    rows = []
    for record in records:
        rid = str(record.get("id") or "").strip()
        if not rid or rid in seen:
            raise ValueError(f"Missing or duplicate candidate id: {rid!r}")
        seen.add(rid)
        rank, score, flag = prioritize(record)
        row = {key: record.get(key, "") for key in OUTPUT_FIELDS}
        row.update({"priority": rank, "score": score, "flag": flag})
        row.update(decisions.get(rid, {}))
        rows.append(row)
    rows.sort(key=lambda r: (r.get("decision") not in ("", "uncertain"),
                            -int(r["score"]), -(int(r.get("year") or 0)), r["id"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    by_priority = Counter(row["priority"] for row in rows)
    print(f"Candidates: {len(rows)} | high: {by_priority['high']} | medium: {by_priority['medium']} | low: {by_priority['low']}")
    print(f"Screening decisions carried forward: {sum(bool(row.get('decision')) for row in rows)}")
    unknown = sorted(set(decisions) - seen)
    if unknown:
        print(f"Warning: {len(unknown)} decisions reference candidate IDs absent from this crawl; retained in decision ledger")
    print(f"Review queue: {output}")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DATA / "discovery_candidates.json")
    parser.add_argument("--decisions", type=Path, default=DATA / "screening_decisions.csv")
    parser.add_argument("--output", type=Path, default=DATA / "screening_priority.csv")
    args = parser.parse_args()
    build(args.input, args.decisions, args.output)

if __name__ == "__main__":
    main()
