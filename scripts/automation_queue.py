#!/usr/bin/env python3
"""Choose and record scheduled *unreviewed* abstract extraction attempts.

Only bibliographic identifiers/statuses are committed; clinical drafts stay in Actions artifacts.
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "extraction_attempts.json"

def read_ledger(path=LEDGER):
    if not path.exists():
        return {"schema_version": 1, "records": {}}
    ledger = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(ledger.get("records"), dict):
        raise ValueError("Invalid extraction attempts ledger")
    return ledger

def select_candidates(candidates, ledger, limit=2):
    from triage_candidates import propose
    done = ledger["records"]
    choices = []
    seen = set()
    for candidate in candidates:
        pmid = str(candidate.get("pmid") or "")
        if not pmid or pmid in seen or pmid in done or candidate.get("source") != "PubMed":
            continue
        seen.add(pmid)
        if propose(candidate)["priority_for_abstract_review"] == "High":
            choices.append(pmid)
        if len(choices) >= limit:
            break
    return choices

def record_successes(report, ledger):
    timestamp = datetime.now(timezone.utc).isoformat()
    failed = {str(item["pmid"]) for item in report.get("failed", [])}
    # Report only counts; the workflow also checks output file existence.
    for pmid in report.get("selected_pmids", []):
        if pmid not in failed and pmid not in ledger["records"]:
            ledger["records"][pmid] = {"last_drafted_at": timestamp,
               "status": "AI draft and AI audit generated; human review pending"}
    return ledger

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["select", "record"])
    parser.add_argument("--limit", type=int, default=2)
    args = parser.parse_args()
    ledger = read_ledger()
    if args.mode == "select":
        from json import loads
        candidates = loads((ROOT / "data" / "discovery_candidates.json").read_text(encoding="utf-8"))["candidates"]
        chosen = select_candidates(candidates, ledger, args.limit)
        (ROOT / "outputs").mkdir(exist_ok=True)
        (ROOT / "outputs" / "selected_pmids.json").write_text(json.dumps(chosen), encoding="utf-8")
        print(",".join(chosen))
    else:
        report_path = ROOT / "outputs" / "extraction_drafts" / "batch_report.json"
        chosen_path = ROOT / "outputs" / "selected_pmids.json"
        if not report_path.exists() or not chosen_path.exists():
            raise SystemExit("Missing selection or extraction report")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        chosen = json.loads(chosen_path.read_text(encoding="utf-8"))
        successes = []
        failed = {str(r["pmid"]) for r in report.get("failed", [])}
        for pmid in chosen:
            path = ROOT / "outputs" / "extraction_drafts" / f"pmid-{pmid}-draft.json"
            if pmid in failed or not path.exists():
                continue
            draft = json.loads(path.read_text(encoding="utf-8"))
            if (draft.get("pmid") != pmid or draft.get("human_approved") is not False or
                not isinstance(draft.get("llm_audit"), dict)):
                continue
            successes.append(pmid)
        record_successes({"selected_pmids": successes, "failed": []}, ledger)
        LEDGER.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Recorded {len(successes)} audited AI drafts; no clinical data promoted")
if __name__ == "__main__":
    main()
