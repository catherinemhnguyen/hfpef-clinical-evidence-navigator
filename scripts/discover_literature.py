#!/usr/bin/env python3
"""Discover HFpEF bibliographic candidates via PubMed E-utilities and ClinicalTrials.gov API v2.

No clinical results are extracted or automatically promoted to the curated study dataset.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
NCBI = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
CTG = "https://clinicaltrials.gov/api/v2/studies"
SEARCHES = {
    "hfpef": '("heart failure with preserved ejection fraction"[Title/Abstract] OR HFpEF[Title/Abstract] OR "diastolic heart failure"[Title/Abstract])',
    "hfmrEF": '("heart failure with mildly reduced ejection fraction"[Title/Abstract] OR HFmrEF[Title/Abstract] OR "heart failure with normal ejection fraction"[Title/Abstract])',
}

def get_json(url, params, pause=0.37):
    request = Request(url + "?" + urlencode(params), headers={
        "User-Agent": "HFpEFEvidenceNavigator/0.3 (research bibliography; see GitHub repository)",
        "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=45) as r:
                value = json.loads(r.read())
            time.sleep(pause)
            return value
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt == 2:
                raise RuntimeError("Public API unavailable; existing outputs were not overwritten") from exc
            time.sleep(2 ** attempt)

def existing_ids():
    studies = json.loads((DATA / "studies.json").read_text())["studies"]
    guidance = json.loads((DATA / "guidelines.json").read_text())["guidelines"]
    pmids = {s["reference"]["pmid"] for s in studies} | {g["pmid"] for g in guidance}
    dois = {s["reference"]["doi"].lower() for s in studies} | {g["doi"].lower() for g in guidance}
    ncts = {s["reference"].get("clinicaltrials_id", "") for s in studies} - {""}
    return pmids, dois, ncts

def deduplicate(rows):
    pmids, dois, ncts = existing_ids()
    output = []
    for r in rows:
        pmid, doi, nct = r.get("pmid", ""), r.get("doi", "").lower(), r.get("nct_id", "")
        if ((pmid and pmid in pmids) or (doi and doi in dois) or (nct and nct in ncts)
                or not r.get("title") or not (pmid or nct)):
            continue
        output.append(r)
        if pmid: pmids.add(pmid)
        if doi: dois.add(doi)
        if nct: ncts.add(nct)
    return sorted(output, key=lambda r: (-(r.get("year") or 0), r["title"].lower()))

def pubmed_record(pmid, record):
    ids = record.get("articleids") or []
    doi = next((x.get("value", "") for x in ids if x.get("idtype") == "doi"), "")
    year = re.search(r"\b(?:19|20)\d{2}\b", record.get("pubdate") or "")
    return {
        "id": "pmid-" + pmid, "source": "PubMed", "pmid": pmid, "nct_id": "", "doi": doi,
        "title": re.sub(r"<[^>]+>", "", record.get("title", "")).strip(),
        "year": int(year.group()) if year else None,
        "journal": record.get("fulljournalname", ""),
        "publication_type": ", ".join(record.get("pubtype") or []),
        "url": "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/",
        "discovery_status": "Pending screening",
        "source_kind": "Journal publication", "provenance": "PubMed ESummary API"
    }

def find_pubmed(max_items):
    rows, logs = [], []
    per_query = max(1, max_items // len(SEARCHES))
    for label, clause in SEARCHES.items():
        query = clause + ' AND ("clinical trial"[Publication Type] OR "randomized controlled trial"[Publication Type] OR "observational study"[Publication Type] OR "cohort studies"[MeSH Terms] OR "guideline"[Publication Type] OR "registry"[Title/Abstract] OR "trial"[Title/Abstract])'
        ids, count = [], 0
        for offset in range(0, per_query, 200):
            result = get_json(NCBI + "esearch.fcgi", {
                "db": "pubmed", "term": query, "retmode": "json", "retstart": offset,
                "retmax": min(200, per_query - offset), "sort": "pub_date"
            })["esearchresult"]
            count = int(result.get("count", 0))
            page = result.get("idlist", [])
            if not page: break
            ids.extend(page)
            if offset + len(page) >= count: break
        for start in range(0, len(ids), 100):
            page = ids[start:start + 100]
            records = get_json(NCBI + "esummary.fcgi", {
                "db": "pubmed", "id": ",".join(page), "retmode": "json"
            }).get("result", {})
            for pmid in page:
                if pmid in records:
                    rows.append(pubmed_record(pmid, records[pmid]))
        logs.append({"source": "PubMed", "query_label": label, "query": query,
                     "reported_matches": count, "retrieved": len(ids),
                     "search_truncated": count > len(ids)})
    return rows, logs

def find_ctg(max_items):
    rows, token, fetched, total = [], None, 0, None
    while fetched < max_items:
        params = {"query.term": '"heart failure with preserved ejection fraction"',
                  "format": "json", "pageSize": min(100, max_items - fetched),
                  "countTotal": "true"}
        if token: params["pageToken"] = token
        body = get_json(CTG, params, pause=0.1)
        total = body.get("totalCount")
        studies = body.get("studies", [])
        fetched += len(studies)
        for s in studies:
            p = s.get("protocolSection", {})
            idm = p.get("identificationModule", {})
            nct, title = idm.get("nctId", ""), idm.get("briefTitle", "")
            text = " ".join([title, p.get("descriptionModule", {}).get("briefSummary", "")] +
                            p.get("conditionsModule", {}).get("conditions", [])).lower()
            if (not re.fullmatch(r"NCT\d{8}", nct) or
                    not any(term in text for term in ("hfpef", "preserved ejection fraction",
                                                      "diastolic heart failure", "hfmref", "mildly reduced ejection fraction"))):
                continue
            stamp = p.get("statusModule", {}).get("studyFirstPostDateStruct", {}).get("date", "")
            yr = re.search(r"\b(?:19|20)\d{2}\b", stamp)
            rows.append({
                "id": "nct-" + nct, "source": "ClinicalTrials.gov", "pmid": "", "nct_id": nct,
                "doi": "", "title": title, "year": int(yr.group()) if yr else None,
                "journal": "", "publication_type": p.get("designModule", {}).get("studyType", "Trial registry"),
                "url": "https://clinicaltrials.gov/study/" + nct, "discovery_status": "Pending screening",
                "source_kind": "Trial registry", "provenance": "ClinicalTrials.gov API v2"
            })
        token = body.get("nextPageToken")
        if not token or not studies: break
    return rows, {"source": "ClinicalTrials.gov", "query": '"heart failure with preserved ejection fraction"',
                  "reported_matches": total, "retrieved": fetched, "search_truncated": bool(token)}

def build(offline=False, max_pubmed=600, max_trials=200):
    seeds = json.loads((DATA / "discovery_seed.json").read_text())["candidates"]
    rows = list(seeds)
    logs = [{"source": "Manually sourced PubMed links", "retrieved": len(seeds), "search_truncated": False}]
    if not offline:
        added, l1 = find_pubmed(max_pubmed)
        trials, l2 = find_ctg(max_trials)
        rows.extend(added + trials)
        logs.extend(l1 + [l2])
    rows = deduplicate(rows)
    output = {
        "project": "HFpEF Clinical Evidence Navigator",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "discovery_method": "Public API bibliographic discovery; clinical eligibility and outcome review pending",
        "not_systematic_review": True, "candidates": rows, "search_log": logs
    }
    (DATA / "discovery_candidates.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    fields = ["id", "source", "title", "year", "journal", "publication_type", "doi",
              "pmid", "nct_id", "url", "source_kind", "discovery_status", "provenance"]
    with (DATA / "discovery_candidates.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    (DATA / "discovery_search_log.json").write_text(json.dumps(logs, indent=2, ensure_ascii=False) + "\n")
    return len(rows)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Use verified local seed citations only")
    parser.add_argument("--max-pubmed", type=int, default=600)
    parser.add_argument("--max-trials", type=int, default=200)
    args = parser.parse_args()
    if args.max_pubmed < 1 or args.max_trials < 1:
        parser.error("Positive API caps required")
    print("Pending-screening citation candidates:", build(args.offline, args.max_pubmed, args.max_trials))
