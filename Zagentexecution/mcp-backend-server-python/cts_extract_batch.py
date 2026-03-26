"""
cts_extract_batch.py -- Batched 4-Year CTS Transport Order Extractor
=====================================================================
Extracts ONE YEAR at a time to avoid RFC timeout / memory issues.
Each year is saved as its own checkpoint file.
After all years complete, it merges them into a single raw JSON.

Strategy:
  - Phase 1 (Headers): runs per-status per-year  (E070, 4 queries per year)
  - Phase 2 (Objects): runs per-TRKORR           (E071, 1 call per transport)
  - Phase 3 (Deploy) : TRSTATUS heuristic        (E070L blocked)
  - Merge  : combine all year JSONs -> cts_4yr_raw.json

Checkpointing:
  - Each year saved to cts_batch_YYYY.json
  - On re-run, already-completed years are SKIPPED (delete file to re-extract)

Usage:
    python cts_extract_batch.py              # Extract 2022-2025 (4 years)
    python cts_extract_batch.py --years 3    # Last 3 years
    python cts_extract_batch.py --merge-only # Just merge existing batch files
    python cts_extract_batch.py --year 2023  # Re-extract one specific year only
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from collections import Counter

# Re-use all the helpers from cts_extract.py
sys.path.insert(0, os.path.dirname(__file__))
from cts_extract import (
    rfc_connect, rfc_table, rfc_table_paginated,
    extract_descriptions, extract_objects,
    extract_deployment_status, extract_tadir_enrichment,
    assemble_result, TPSTAT_MAP
)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

BATCH_DIR = os.path.dirname(__file__)   # same folder as scripts


# ─────────────────────────────────────────────────────────────────────────────
# YEAR EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_year(conn, year: int) -> dict:
    """
    Extract all released transports for a single calendar year.
    Returns the assembled result dict for that year.
    """
    date_from = f"{year}0101"
    date_to   = f"{year}1231"

    fields  = ["TRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER",
                "AS4DATE", "AS4TIME", "STRKORR", "KORRDEV"]
    headers = []

    # E071 has same IN() restriction as E070 -- one status at a time
    for status in ['R', 'D', 'L', 'E']:
        where = [
            f"AS4DATE >= '{date_from}'",
            f"AND AS4DATE <= '{date_to}'",
            f"AND TRSTATUS = '{status}'",
            # Focus: Workbench (K) and Customizing (W) only
            "AND TRFUNCTION IN ('K', 'W', 'T')",
        ]
        try:
            rows = rfc_table_paginated(conn, "E070", fields, where,
                                       page_size=5000, verbose=False)
            print(f"      TRSTATUS='{status}': {len(rows)} rows")
            headers.extend(rows)
        except Exception as ex:
            print(f"      [WARN] E070 {year} status={status}: {str(ex)[:80]}")

    # Deduplicate
    seen, deduped = set(), []
    for r in headers:
        k = r.get("TRKORR", "")
        if k and k not in seen:
            seen.add(k)
            deduped.append(r)

    print(f"      -> {len(deduped)} unique headers for {year}")

    if not deduped:
        return None

    trkorrs = [h["TRKORR"] for h in deduped if h.get("TRKORR")]

    # Descriptions (may be unavailable -- graceful skip)
    descriptions = extract_descriptions(conn, trkorrs)

    # Objects (per-TRKORR loop)
    objects_by_trkorr = extract_objects(conn, trkorrs)

    # Deployment heuristic
    deployment = extract_deployment_status(conn, trkorrs)

    # No TADIR in batch mode (too slow per-year; merged later)
    tadir_cache, devclass_info = {}, {}

    return assemble_result(deduped, descriptions, objects_by_trkorr,
                           deployment, tadir_cache, devclass_info)


# ─────────────────────────────────────────────────────────────────────────────
# MERGE
# ─────────────────────────────────────────────────────────────────────────────

def merge_batches(batch_files: list, outfile: str):
    """
    Merge multiple year batch JSONs into a single raw JSON file.
    Combines all transports; recomputes summary stats.
    """
    print(f"\n  [Merge] Combining {len(batch_files)} year batches -> {outfile}")

    all_transports = []
    earliest_meta  = None

    for bf in sorted(batch_files):
        if not os.path.exists(bf):
            print(f"    [SKIP] {bf} not found")
            continue
        with open(bf, encoding="utf-8") as f:
            data = json.load(f)
        year_transports = data.get("transports", [])
        all_transports.extend(year_transports)
        meta = data.get("meta", {})
        year = meta.get("batch_year", "?")
        print(f"    {bf}: {len(year_transports)} transports  (year {year})")
        if earliest_meta is None:
            earliest_meta = meta

    # Recompute summary
    total_headers = len(all_transports)
    total_objects = sum(t.get("obj_count", 0) for t in all_transports)
    levels        = Counter(t.get("deploy_level","UNKNOWN") for t in all_transports)
    type_dist     = Counter(t.get("type","?") for t in all_transports)
    top_owners    = Counter(t.get("owner","") for t in all_transports).most_common(20)
    devclass_cnt  = Counter()
    obj_type_cnt  = Counter()
    for t in all_transports:
        for o in t.get("objects",[]):
            devclass_cnt[o.get("devclass","")] += 1
            obj_type_cnt[o.get("change_cat","")] += 1

    merged = {
        "meta": {
            "extracted_at":  datetime.now().isoformat(),
            "source_system": "D01",
            "batch_years":   [os.path.basename(f) for f in batch_files],
            "total_headers": total_headers,
            "total_objects": total_objects,
            "e070l_note":    "E070L not readable via RFC. Deploy level from TRSTATUS.",
        },
        "summary": {
            "deployment_levels": dict(levels),
            "request_types":     dict(type_dist),
            "top_20_owners":     top_owners,
            "top_30_devclasses": devclass_cnt.most_common(30),
            "change_cat_dist":   dict(obj_type_cnt),
        },
        "transports": all_transports,
    }

    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n  [OK] Merged: {total_headers} transports, {total_objects} objects -> {outfile}")
    return merged


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Batched CTS Extractor -- one year at a time")
    parser.add_argument("--years",      type=int, default=4,   help="Number of years to extract (default: 4)")
    parser.add_argument("--year",       type=int, default=None, help="Extract only this specific year (YYYY)")
    parser.add_argument("--merge-only", action="store_true",   help="Skip extraction, only merge existing batch files")
    parser.add_argument("--out",        type=str, default="cts_4yr_raw.json", help="Merged output file")
    parser.add_argument("--skip-tadir", action="store_true",   help="Skip TADIR enrichment in final merge")
    args = parser.parse_args()

    current_year = datetime.now().year
    if args.year:
        years_to_run = [args.year]
    else:
        years_to_run = list(range(current_year - args.years + 1, current_year + 1))

    batch_files  = [os.path.join(BATCH_DIR, f"cts_batch_{y}.json") for y in years_to_run]

    print("=" * 70)
    print(f"  CTS BATCH EXTRACTOR -- UNESCO D01")
    print(f"  Years   : {years_to_run}")
    print(f"  Focus   : Workbench (K) + Customizing (W) + Copies (T)")
    print(f"  Output  : {args.out}")
    print("=" * 70)

    if not args.merge_only:
        conn = rfc_connect()
        print(f"  [OK] Connected to D01\n")

        for year in years_to_run:
            batch_file = os.path.join(BATCH_DIR, f"cts_batch_{year}.json")

            # Skip if checkpoint already exists
            if os.path.exists(batch_file):
                with open(batch_file, encoding="utf-8") as f:
                    existing = json.load(f)
                count = existing.get("meta", {}).get("total_headers", "?")
                print(f"\n  [SKIP] Year {year} already extracted ({count} transports) -> {batch_file}")
                print(f"         Delete the file to re-extract this year.")
                continue

            print(f"\n  {'=' * 60}")
            print(f"  Extracting year: {year}")
            print(f"  {'=' * 60}")
            t0 = datetime.now()

            result = extract_year(conn, year)

            if result is None:
                print(f"  [INFO] Year {year}: no transports found. Skipping.")
                continue

            # Stamp the year on meta
            result["meta"]["batch_year"] = year

            with open(batch_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)

            elapsed = (datetime.now() - t0).total_seconds()
            print(f"\n  [OK] Year {year}: {result['meta']['total_headers']} transports,"
                  f" {result['meta']['total_objects']} objects -> {batch_file} ({elapsed:.0f}s)")

        conn.close()

    # Merge all batch files
    merged = merge_batches(batch_files, args.out)

    print(f"\n  Next step: python cts_analyze.py --input {args.out}")
    print("=" * 70)

    # Quick summary per year
    print(f"\n  Per-year breakdown:")
    for bf in batch_files:
        if os.path.exists(bf):
            with open(bf, encoding="utf-8") as f:
                d = json.load(f)
            y   = d.get("meta",{}).get("batch_year","?")
            cnt = d.get("meta",{}).get("total_headers",0)
            obj = d.get("meta",{}).get("total_objects",0)
            print(f"    {y}: {cnt:>6} transports  {obj:>8} objects")


if __name__ == "__main__":
    main()
