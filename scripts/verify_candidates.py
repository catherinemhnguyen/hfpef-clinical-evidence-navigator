#!/usr/bin/env python3
"""Independent bibliographic identity checks for the HFpEF discovery queue.

Checks ALL candidate metadata offline; optionally re-fetches a capped batch from
PubMed EFetch / ClinicalTrials.gov API v2. This does NOT verify clinical results.
Never promotes records to studies.json, even when a source identity matches.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PMID_PATTERN = re.compile(r"\d{7,9}")
NCT_PATTERN = re.compile(r"NCT\d{8}", re.I)
DOI_PATTERN = re.compile(r"10\.\d{4,9}/\S+", re.I)
SOURCE_TYPES = ("PubMed", "ClinicalTrials.gov")


def normalize_title(value):
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    return " ".join(re.findall(r"[a-z0-9]+", value))


def title_similarity(a, b):
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


def normalize_doi(value):
    return str(value or "").strip().lower().removeprefix("https://doi.org/")


def fingerprint(record):
    payload = {name: record.get(name) for name in
               ("id", "source", "pmid", "nct_id", "doi", "title")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def local_flags(records):
    """No factual conclusions: check shapes, identity, URLs and duplication."""
    per = defaultdict(list)
    seen_id, seen_pmid, seen_nct, seen_doi = {}, {}, {}, {}
    for row in records:
        key = str(row.get("id", ""))
        if not key:
            raise ValueError("All candidates must have a nonempty id")
        if key in seen_id:
            per[key].append("duplicate_record_id")
        seen_id[key] = True
        source = row.get("source")
        pmid = str(row.get("pmid") or "")
        nct = str(row.get("nct_id") or "")
        doi = normalize_doi(row.get("doi"))
        if source not in SOURCE_TYPES:
            per[key].append("unrecognized_source")
        if not str(row.get("title") or "").strip():
            per[key].append("missing_title")
        if source == "PubMed":
            if not PMID_PATTERN.fullmatch(pmid) or key != f"pmid-{pmid}":
                per[key].append("invalid_pubmed_identity")
            if nct:
                per[key].append("unexpected_registry_id_for_pubmed_record")
            if row.get("url") != f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/":
                per[key].append("pubmed_url_mismatch")
        if source == "ClinicalTrials.gov":
            if not NCT_PATTERN.fullmatch(nct) or key != f"nct-{nct}":
                per[key].append("invalid_registry_identity")
            if pmid:
                per[key].append("unexpected_pmid_for_registry_record")
            if row.get("url") != f"https://clinicaltrials.gov/study/{nct}":
                per[key].append("registry_url_mismatch")
        if doi and not DOI_PATTERN.fullmatch(doi):
            per[key].append("malformed_doi")
        year = row.get("year")
        if year is not None and (type(year) is not int or not 1900 <= year <= datetime.now(timezone.utc).year + 2):
            per[key].append("implausible_publication_year")
        for value, target, name in (
            (pmid, seen_pmid, "duplicate_pmid"), (nct, seen_nct, "duplicate_nct_id"),
            (doi, seen_doi, "duplicate_doi"),
        ):
            if value:
                if value in target:
                    per[key].append(name)
                    per[target[value]].append(name)
                else:
                    target[value] = key
    return {key: sorted(set(values)) for key, values in per.items()}


def retrieve_source(record):
    """Recheck a source identity using an independently fetched API response."""
    source = record["source"]
    if source == "PubMed":
        pmid = str(record.get("pmid") or "")
        if not PMID_PATTERN.fullmatch(pmid):
            raise ValueError("Invalid PMID for remote verification")
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
        req = Request(url, headers={"User-Agent": "HFpEFEvidenceNavigator/1.0 (research metadata verification)"})
        with urlopen(req, timeout=25) as handle:
            root = ET.fromstring(handle.read())
        articles = root.findall(".//PubmedArticle")
        for article in articles:
            ident = (article.findtext("./MedlineCitation/PMID") or "").strip()
            if ident != pmid:
                continue
            title_node = article.find("./MedlineCitation/Article/ArticleTitle")
            title = "".join(title_node.itertext()) if title_node is not None else ""
            doi = ""
            for node in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
                if node.attrib.get("IdType", "").lower() == "doi":
                    doi = "".join(node.itertext())
                    break
            return {"id": pmid, "title": title, "doi": doi, "source": "PubMed EFetch"}
        raise ValueError("PubMed EFetch did not return requested PMID")
    if source == "ClinicalTrials.gov":
        nct = str(record.get("nct_id") or "")
        if not NCT_PATTERN.fullmatch(nct):
            raise ValueError("Invalid NCT for remote verification")
        url = f"https://clinicaltrials.gov/api/v2/studies/{nct}"
        req = Request(url, headers={"Accept": "application/json",
                                    "User-Agent": "HFpEFEvidenceNavigator/1.0"})
        with urlopen(req, timeout=25) as handle:
            data = json.loads(handle.read())
        module = data["protocolSection"]["identificationModule"]
        return {"id": module.get("nctId"), "title": module.get("briefTitle", ""),
                "doi": "", "source": "ClinicalTrials.gov API v2"}
    raise ValueError("Unsupported source for online verification")


def compare_source(record, fresh):
    expected_id = str(record.get("pmid") or record.get("nct_id") or "")
    if fresh.get("id") != expected_id:
        return ["source_identifier_mismatch"]
    issues = []
    if title_similarity(record.get("title"), fresh.get("title")) < 0.82:
        issues.append("source_title_mismatch")
    old_doi, current_doi = normalize_doi(record.get("doi")), normalize_doi(fresh.get("doi"))
    if old_doi and current_doi and old_doi != current_doi:
        issues.append("source_doi_mismatch")
    return issues


def load_ledger(path):
    if not path.exists():
        return {"schema_version": 1, "records": {}}
    ledger = json.loads(path.read_text(encoding="utf-8"))
    if ledger.get("schema_version") != 1 or not isinstance(ledger.get("records"), dict):
        raise ValueError("Malformed bibliographic source-check ledger")
    return ledger


def verify(records, ledger, online_limit=0, source_reader=retrieve_source):
    if not isinstance(records, list):
        raise ValueError("Candidate data must be an array")
    if not 0 <= online_limit <= 100:
        raise ValueError("Online limit must be 0–100 records")
    by_id = {}
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("Every candidate must be an object")
        if not row.get("id"):
            raise ValueError("Missing candidate id")
        if row["id"] in by_id:
            raise ValueError(f"Duplicate candidate id: {row['id']}")
        by_id[row["id"]] = row
    checks = local_flags(records)
    stored = ledger["records"]
    active_ids = set(by_id)
    # Remove stale checks. The verification log never acts as an approval list.
    for key in list(stored):
        if key not in active_ids:
            del stored[key]
    for key, row in by_id.items():
        if stored.get(key, {}).get("fingerprint") != fingerprint(row):
            stored.pop(key, None)
    eligible = [r for r in records if not checks.get(r["id"]) and r.get("source") in SOURCE_TYPES]
    untested = [r for r in eligible if r["id"] not in stored]
    retryable = [r for r in eligible if stored.get(r["id"], {}).get("status") == "unavailable"]
    # Prioritize never-checked records; process in deterministic queue order.
    selected = (untested + retryable)[:online_limit]
    for row in selected:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            fresh = source_reader(row)
            problems = compare_source(row, fresh)
            stored[row["id"]] = {
                "fingerprint": fingerprint(row), "checked_at_utc": now,
                "status": "identity_mismatch" if problems else "identity_match",
                "source": fresh.get("source", ""),
                "flags": problems,
            }
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError, ET.ParseError, OSError, json.JSONDecodeError):
            # Do not create a positive verification status after an API failure.
            stored[row["id"]] = {"fingerprint": fingerprint(row),
                                  "checked_at_utc": now, "status": "unavailable",
                                  "source": "", "flags": ["source_check_unavailable"]}
        # Be polite to public APIs; no concurrent flooding.
        if online_limit:
            time.sleep(0.25)

    rows, flags = [], []
    for row in records:
        key = row["id"]
        local = list(checks.get(key, []))
        cross = stored.get(key, {})
        status = cross.get("status", "not_checked")
        all_issues = local + (cross.get("flags", []) if status == "identity_mismatch" else [])
        record = {
            "id": key, "source": row.get("source", ""), "title": row.get("title", ""),
            "pmid": row.get("pmid", ""), "nct_id": row.get("nct_id", ""),
            "metadata_structure": "flagged" if local else "passed",
            "source_identity": status, "flags": "|".join(sorted(set(all_issues))),
            "last_checked_utc": cross.get("checked_at_utc", ""),
        }
        rows.append(record)
        if all_issues or status == "unavailable":
            flags.append(record)
    status_counts = Counter(x["source_identity"] for x in rows)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "bibliographic identity only; NOT HFpEF eligibility, clinical extraction or physician validation",
        "total_candidates": len(rows),
        "local_metadata_passed": sum(x["metadata_structure"] == "passed" for x in rows),
        "local_metadata_flagged": sum(x["metadata_structure"] == "flagged" for x in rows),
        "online_identity_matched": status_counts["identity_match"],
        "online_identity_mismatched": status_counts["identity_mismatch"],
        "online_identity_unavailable": status_counts["unavailable"],
        "online_identity_not_checked": status_counts["not_checked"],
        "online_attempted_this_run": len(selected),
        "unverified_clinical_records": len(rows),
        "not_a_comprehensive_search": True,
    }
    return report, flags, ledger


def write_csv(path, rows):
    columns = ["id", "source", "title", "pmid", "nct_id",
               "metadata_structure", "source_identity", "flags", "last_checked_utc"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online-limit", type=int, default=0,
                        help="Re-fetch at most N pending bibliographic records (0 = offline only)")
    parser.add_argument("--candidates", type=Path, default=DATA / "discovery_candidates.json")
    parser.add_argument("--ledger", type=Path, default=DATA / "verification_online_ledger.json")
    parser.add_argument("--report", type=Path, default=DATA / "verification_report.json")
    parser.add_argument("--flags", type=Path, default=DATA / "verification_flags.csv")
    args = parser.parse_args(argv)
    records = json.loads(args.candidates.read_text(encoding="utf-8"))["candidates"]
    ledger = load_ledger(args.ledger)
    report, flags, updated = verify(records, ledger, args.online_limit)
    for path in (args.ledger, args.report, args.flags):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(args.flags, flags)
    print(json.dumps(report, indent=2))
    if report["local_metadata_flagged"] or report["online_identity_mismatched"]:
        print("Metadata exceptions require review; no study was promoted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
