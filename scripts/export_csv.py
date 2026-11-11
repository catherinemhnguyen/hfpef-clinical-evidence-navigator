#!/usr/bin/env python3
"""Regenerate the public CSV snapshots from the canonical JSON records."""
from pathlib import Path
from evidence import ROOT, csv_text, flatten_guideline, flatten_study, load_records


def main() -> None:
    studies, guidance = load_records()
    a = [flatten_study(s) for s in studies["studies"]]
    b = [flatten_guideline(g) for g in guidance["guidelines"]]
    files = {
        "studies.csv": a,
        "guidelines.csv": b,
        "evidence_index.csv": a + b,
    }
    for fname, rows in files.items():
        target = ROOT / 'data' / fname
        target.write_text(csv_text(rows), encoding="utf-8-sig")
        print(f"Wrote {target.relative_to(ROOT)}: {len(rows)} records")


if __name__ == "__main__":
    main()
