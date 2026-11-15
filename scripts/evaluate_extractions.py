#!/usr/bin/env python3
"""Measure extraction and AI-auditor agreement with manually adjudicated source reviews.

This is a benchmark, NOT a clinical validation or automatic promotion process.
No model calls are made. Reviews must refer to the *same input text* as the draft.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from extract_candidates import FIELD_NAMES


def rate(numerator: int, denominator: int):
    return round(numerator / denominator, 4) if denominator else None


def new_counts():
    return {
        "documents": 0, "fields_reviewed": 0, "fields_expected": 0,
        "extracted_fields": 0, "correct_extracted": 0,
        "correct_including_absent": 0, "audited_fields": 0,
        "auditor_detected_errors": 0, "auditor_missed_errors": 0,
        "auditor_false_alarms": 0, "auditor_correct_accepts": 0,
        "auditor_unassessed": 0,
    }


def summarize(counts: dict):
    result = dict(counts)
    result["extracted_field_precision"] = rate(
        counts["correct_extracted"], counts["extracted_fields"])
    result["extractable_field_recall"] = rate(
        counts["correct_extracted"], counts["fields_expected"])
    result["all_field_accuracy"] = rate(
        counts["correct_including_absent"], counts["fields_reviewed"])
    result["auditor_error_sensitivity"] = rate(
        counts["auditor_detected_errors"],
        counts["auditor_detected_errors"] + counts["auditor_missed_errors"])
    result["auditor_correct_acceptance_rate"] = rate(
        counts["auditor_correct_accepts"],
        counts["auditor_correct_accepts"] + counts["auditor_false_alarms"])
    return result


def evaluate(annotation: dict, drafts_dir: Path) -> dict:
    if annotation.get("schema_version") != 1:
        raise ValueError("Review file must use schema_version 1")
    reviews = annotation.get("reviews")
    if not isinstance(reviews, list) or not reviews:
        raise ValueError("No manually completed reviews; cannot report accuracy")
    totals = new_counts()
    by_pair = defaultdict(new_counts)
    seen = set()
    for review in reviews:
        pmid = str(review.get("pmid", ""))
        if not re.fullmatch(r"\d{7,9}", pmid):
            raise ValueError("Invalid review PMID")
        draft_name = str(review.get("draft_file", ""))
        if not re.fullmatch(r"pmid-\d{7,9}-draft\.json", draft_name):
            raise ValueError(f"{pmid}: draft_file must be a generated PMID draft filename")
        draft_path = drafts_dir / draft_name
        if not draft_path.is_file():
            raise ValueError(f"{pmid}: draft file not found: {draft_path}")
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
        if str(draft.get("pmid")) != pmid or draft_name != f"pmid-{pmid}-draft.json":
            raise ValueError(f"{pmid}: draft identity mismatch")
        sha = review.get("source_sha256")
        if not isinstance(sha, str) or sha != draft.get("source_sha256"):
            raise ValueError(f"{pmid}: reviewed source hash does not match draft")
        if not str(review.get("reviewer") or "").strip() or not str(review.get("source_notes") or "").strip():
            raise ValueError(f"{pmid}: human reviewer and source_notes are required")
        if review.get("reference_scope") != "same_input_text":
            raise ValueError(f"{pmid}: compare against same input text; use separate full-text review for publication")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(review.get("review_date") or "")):
            raise ValueError(f"{pmid}: review_date must be YYYY-MM-DD")
        key = (pmid, str(draft.get("model")), str(draft.get("auditor_model", "")))
        if key in seen:
            raise ValueError(f"{pmid}: duplicate model-pair review")
        seen.add(key)
        field_reviews = review.get("fields")
        fields = draft.get("extraction", {}).get("fields", {})
        if not isinstance(field_reviews, dict) or set(field_reviews) != set(FIELD_NAMES):
            raise ValueError(f"{pmid}: all {len(FIELD_NAMES)} fields require independent review")
        if set(fields) != set(FIELD_NAMES):
            raise ValueError(f"{pmid}: malformed extraction")
        judgements = (draft.get("llm_audit") or {}).get("judgments", [])
        audit_map = {}
        for item in judgements:
            name = item.get("field")
            if name in audit_map:
                raise ValueError(f"{pmid}: auditor provided duplicate judgement for {name}")
            audit_map[name] = item.get("verdict")
        pair = f"{draft.get('model','unknown')} / {draft.get('auditor_model') or 'no AI audit'}"
        stats = by_pair[pair]
        totals["documents"] += 1
        stats["documents"] += 1
        for field in FIELD_NAMES:
            labels = field_reviews[field]
            present_expected = labels.get("expected_present")
            correct = labels.get("extraction_correct")
            if type(present_expected) is not bool or type(correct) is not bool:
                raise ValueError(f"{pmid}/{field}: expected_present and extraction_correct must be booleans")
            value = fields[field].get("value")
            extracted = value is not None and bool(str(value).strip())
            if correct and (extracted != present_expected):
                raise ValueError(f"{pmid}/{field}: correctness contradicts expected/extracted presence")
            for counts in (totals, stats):
                counts["fields_reviewed"] += 1
                counts["fields_expected"] += int(present_expected)
                counts["extracted_fields"] += int(extracted)
                counts["correct_extracted"] += int(extracted and correct)
                counts["correct_including_absent"] += int(correct)
                if not extracted:
                    continue
                verdict = audit_map.get(field)
                if verdict not in ("supported", "unsupported", "unclear", "not_extracted"):
                    counts["auditor_unassessed"] += 1
                    continue
                counts["audited_fields"] += 1
                flagged = verdict != "supported"
                if not correct:
                    counts["auditor_detected_errors" if flagged else "auditor_missed_errors"] += 1
                else:
                    counts["auditor_false_alarms" if flagged else "auditor_correct_accepts"] += 1
    return {
        "status": "human-annotated, input-text benchmark only; not independent clinical verification",
        "documents_reviewed": totals["documents"],
        "overall": summarize(totals),
        "model_pairs": {pair: summarize(values) for pair, values in sorted(by_pair.items())},
        "cautions": [
            "The manual reviewer, not this script, determines whether each clinical extraction is correct.",
            "Precision and recall apply only to reviewed fields and the exact supplied input text.",
            "AI auditor agreement does not guarantee factual correctness or justify auto-publication.",
            "A sample of three documents is a pilot, not a population-level accuracy guarantee.",
        ],
    }


def make_review_template(drafts_dir: Path) -> dict:
    """Create deliberately blank human review labels from AI drafts."""
    reviews = []
    for path in sorted(drafts_dir.glob("pmid-*-draft.json")):
        if not re.fullmatch(r"pmid-\d{7,9}-draft\.json", path.name):
            continue
        draft = json.loads(path.read_text(encoding="utf-8"))
        if str(draft.get("pmid")) != path.name.removeprefix("pmid-").removesuffix("-draft.json"):
            raise ValueError(f"{path.name}: PMID identity mismatch")
        if not re.fullmatch(r"[a-fA-F0-9]{64}", str(draft.get("source_sha256", ""))):
            raise ValueError(f"{path.name}: missing valid input source hash")
        reviews.append({
            "pmid": str(draft["pmid"]), "draft_file": path.name,
            "source_sha256": draft["source_sha256"],
            "reviewer": "", "review_date": "", "source_notes": "",
            "reference_scope": "same_input_text",
            "fields": {name: {"expected_present": None, "extraction_correct": None}
                       for name in FIELD_NAMES},
        })
    if not reviews:
        raise ValueError("No valid PMID drafts found; generate or download drafts first")
    return {"schema_version": 1, "reviews": reviews}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=Path, help="Local JSON with human field adjudications")
    parser.add_argument("--make-template", action="store_true", help="Create a blank field review worksheet (no accuracy scores)")
    parser.add_argument("--drafts", type=Path, required=True, help="Directory containing model-generated draft JSON")
    parser.add_argument("--output", type=Path, help="Optional JSON results file")
    args = parser.parse_args(argv)
    if args.make_template:
        report = make_review_template(args.drafts)
    else:
        if args.reviews is None:
            parser.error("--reviews is required unless --make-template is set")
        report = evaluate(json.loads(args.reviews.read_text(encoding="utf-8")), args.drafts)
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
