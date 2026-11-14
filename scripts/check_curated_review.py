#!/usr/bin/env python3
"""Require documented human review before new/modified clinical records are merged.

Checks metadata and structural safeguards only, NOT actual scientific correctness.
Run in PR CI against the main branch baseline.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "data" / "studies.json"

def check(base, current):
    previous = {r["id"]: r for r in base.get("studies", [])}
    violations = []
    for item in current.get("studies", []):
        old = previous.get(item["id"])
        if old == item:
            continue
        c = item.get("curation") or {}
        name = item.get("acronym", item["id"])
        first = str(c.get("reviewer") or "").strip()
        second = str(c.get("second_reviewer") or "").strip()
        notes = str(c.get("review_notes") or "").strip()
        basis = str(c.get("source_basis") or "").lower()
        status = str(c.get("verification_status") or "").lower()
        if not first or not second or first.casefold() == second.casefold():
            violations.append(f"{name}: independent first and second reviewer identities required")
        if len(notes) < 35 or not any(x in notes.lower() for x in ("page", "table", "section", "supplement")):
            violations.append(f"{name}: review_notes must document source page/table/section and adjudication")
        if "full" not in basis:
            violations.append(f"{name}: source_basis must document full-text review")
        if "review" not in status:
            violations.append(f"{name}: verification_status must state actual review level")
    return violations

def main():
    try:
        baseline = subprocess.check_output(["git","show","origin/main:data/studies.json"],cwd=ROOT)
        old = json.loads(baseline)
    except (subprocess.CalledProcessError, ValueError) as exc:
        print("Cannot retrieve PR base version; fail closed:", exc, file=sys.stderr)
        return 1
    new = json.loads(CURRENT.read_text(encoding="utf-8"))
    errors = check(old,new)
    if errors:
        print("CURATED PROMOTION BLOCKED:")
        for e in errors: print(" -",e)
        return 1
    print("PASS: review metadata present for all modified/new records.")
    print("Warning: this check cannot prove scientific correctness or human identity.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
