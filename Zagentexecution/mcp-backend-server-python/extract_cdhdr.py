"""
extract_cdhdr.py
================
Extract CDHDR (Change Document Headers) and CDPOS (Change Document Items)
from SAP P01 via RFC_READ_TABLE.

WHO changed WHAT config and WHEN — the missing audit trail.

Pattern: Same checkpoint-per-period design as extract_bkpf_bseg_parallel.py
Safety: Max 2 concurrent RFC connections via semaphore.

Target OBJECTCLAS values (from Celonis + Javert899/sap-extractor):
  EINKBELEG  = Purchase documents (ME21N, ME22N, ME29N, etc.)
  VERKBELEG  = Sales documents
  LIEFERUNG  = Deliveries
  MATERIAL   = Material master
  KRED       = Vendor master
  DEBT       = Customer master
  BANF       = Purchase requisitions
  FMIFIIT    = FM documents (UNESCO specific)
  FM_BUDGET  = FM budget documents

Output:
  extracted_data/CDHDR/CDHDR_YYYY_MM.json
  extracted_data/CDPOS/CDPOS_<changenr_batch>.json
  Tables in gold SQLite DB: cdhdr, cdpos

Usage:
    python extract_cdhdr.py                    # Full run (CDHDR + CDPOS)
    python extract_cdhdr.py --cdhdr-only       # Only headers
    python extract_cdhdr.py --cdpos-only       # Only items (needs CDHDR done first)
    python extract_cdhdr.py --year 2025        # Single year
    python extract_cdhdr.py --merge-only       # Merge checkpoints to SQLite
    python extract_cdhdr.py --status           # Show progress
"""

import os
import json
import time
import argparse
import threading
import sqlite3
from datetime import datetime

BASE_DIR   = os.path.dirname(__file__)
DATA_DIR   = os.path.join(BASE_DIR, "extracted_data")
CDHDR_DIR  = os.path.join(DATA_DIR, "CDHDR")
CDPOS_DIR  = os.path.join(DATA_DIR, "CDPOS")
GOLD_DB    = os.path.join(BASE_DIR, "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
YEARS      = [2024, 2025, 2026]

# CDHDR fields — WHO changed WHAT and WHEN
# NOTE: CDHDR uses MANDANT (not MANDT) — confirmed via DD03L
CDHDR_FIELDS = [
    "MANDANT", "OBJECTCLAS", "OBJECTID", "CHANGENR", "USERNAME",
    "UDATE", "UTIME", "TCODE",
]

# CDPOS fields — field-level detail of each change
# NOTE: CDPOS also uses MANDANT (not MANDT) — same as CDHDR
CDPOS_FIELDS = [
    "MANDANT", "OBJECTCLAS", "OBJECTID", "CHANGENR",
    "TABNAME", "TABKEY", "FNAME", "CHNGIND",
    "VALUE_NEW", "VALUE_OLD",
]


from rfc_helpers import get_connection, rfc_read_paginated


# ─────────────────────────────────────────────────────────────────────
# CDHDR EXTRACTION — month by month via UDATE
# ─────────────────────────────────────────────────────────────────────

def extract_cdhdr(years, batch_size, throttle, sap_semaphore):
    label = "[CDHDR]"
    os.makedirs(CDHDR_DIR, exist_ok=True)

    with sap_semaphore:
        print(f"  {label} Semaphore acquired. Connecting to P01...")
        try:
            conn = get_connection("P01")
        except Exception as e:
            print(f"  {label} Connection FAILED: {e}")
            return

        total_rows = 0
        t_start = time.time()

        for year in years:
            for month in range(1, 13):
                monat = f"{month:02d}"
                checkpoint = os.path.join(CDHDR_DIR, f"CDHDR_{year}_{monat}.json")

                if os.path.exists(checkpoint):
                    with open(checkpoint, encoding="utf-8") as f:
                        d = json.load(f)
                    cnt = d.get("meta", {}).get("row_count", 0)
                    print(f"  {label} SKIP {year}/{monat} [{cnt} rows]")
                    total_rows += cnt
                    continue

                date_from = f"{year}{monat}01"
                if month < 12:
                    date_to_next = f"{year}{(month+1):02d}01"
                    where = f"UDATE >= '{date_from}' AND UDATE < '{date_to_next}'"
                else:
                    where = f"UDATE >= '{date_from}' AND UDATE <= '{year}1231'"

                print(f"  {label} {year}/{monat}...")
                t0 = time.time()
                errored = False
                try:
                    rows = rfc_read_paginated(conn, "CDHDR", CDHDR_FIELDS, where, batch_size, throttle)
                except Exception as e:
                    print(f"  {label} ERROR {year}/{monat}: {e}")
                    rows = []
                    errored = True

                elapsed = time.time() - t0

                if errored and len(rows) == 0:
                    print(f"  {label}   -> SKIPPED checkpoint (error, 0 rows) -- will retry on next run")
                    continue

                data = {
                    "meta": {
                        "table": "CDHDR", "year": year, "month": month,
                        "row_count": len(rows),
                        "extracted_at": datetime.now().isoformat(),
                        "elapsed_sec": round(elapsed, 1),
                    },
                    "rows": rows,
                }
                with open(checkpoint, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, default=str)

                total_rows += len(rows)
                print(f"  {label}   -> {len(rows):,} rows ({elapsed:.0f}s) total: {total_rows:,}")
                if throttle > 0:
                    time.sleep(throttle)

        try:
            conn.close()
        except Exception:
            pass

        elapsed_total = (time.time() - t_start) / 60
        print(f"  {label} DONE. {total_rows:,} rows in {elapsed_total:.1f} min.")


# ─────────────────────────────────────────────────────────────────────
# CDPOS EXTRACTION — batch by CHANGENR from CDHDR results
# ─────────────────────────────────────────────────────────────────────

def extract_cdpos(years, batch_size, throttle, sap_semaphore):
    label = "[CDPOS]"
    os.makedirs(CDPOS_DIR, exist_ok=True)

    # Gather all CHANGENR values from CDHDR checkpoints
    changenr_set = set()
    for year in years:
        for month in range(1, 13):
            fp = os.path.join(CDHDR_DIR, f"CDHDR_{year}_{month:02d}.json")
            if os.path.exists(fp):
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                for row in data.get("rows", []):
                    v = row.get("CHANGENR", "").strip()
                    if v:
                        changenr_set.add(v)

    if not changenr_set:
        print(f"  {label} No CHANGENR keys from CDHDR checkpoints. Run CDHDR first.")
        return

    # Check what's already done
    checkpoint = os.path.join(CDPOS_DIR, "CDPOS_all.json")
    if os.path.exists(checkpoint):
        with open(checkpoint, encoding="utf-8") as f:
            d = json.load(f)
        print(f"  {label} SKIP -- checkpoint exists ({d['meta']['row_count']} rows)")
        return

    keys = sorted(changenr_set)
    print(f"  {label} {len(keys)} unique CHANGENR keys to query...")

    with sap_semaphore:
        print(f"  {label} Semaphore acquired -> connecting P01...")
        conn = get_connection("P01")
        all_rows = []
        CHUNK = 25  # SAP OR-chain limit for safety

        for i in range(0, len(keys), CHUNK):
            chunk = keys[i : i + CHUNK]
            in_expr = " OR ".join(f"CHANGENR = '{k}'" for k in chunk)
            try:
                rows = rfc_read_paginated(conn, "CDPOS", CDPOS_FIELDS,
                                          [f"( {in_expr} )"], batch_size, throttle)
                all_rows.extend(rows)
                if (i // CHUNK) % 10 == 0:
                    print(f"  {label} chunk {i//CHUNK+1}/{(len(keys)+CHUNK-1)//CHUNK}: "
                          f"+{len(rows)} rows, total: {len(all_rows):,}")
            except Exception as e:
                print(f"  {label} ERROR chunk {i//CHUNK+1}: {e}")
            time.sleep(throttle)

        conn.close()

    data = {
        "meta": {
            "table": "CDPOS", "source_keys": len(keys),
            "row_count": len(all_rows),
            "extracted_at": datetime.now().isoformat(),
        },
        "rows": all_rows,
    }
    with open(checkpoint, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)
    print(f"  {label} DONE. {len(all_rows):,} rows -> {checkpoint}")


# ─────────────────────────────────────────────────────────────────────
# MERGE TO SQLITE
# ─────────────────────────────────────────────────────────────────────

def merge_to_sqlite():
    print("\n[MERGE] Loading CDHDR/CDPOS into gold SQLite DB...")
    conn = sqlite3.connect(GOLD_DB)

    # CDHDR
    all_cdhdr = []
    for year in YEARS:
        for month in range(1, 13):
            fp = os.path.join(CDHDR_DIR, f"CDHDR_{year}_{month:02d}.json")
            if os.path.exists(fp):
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                all_cdhdr.extend(data.get("rows", []))

    if all_cdhdr:
        cols = list(all_cdhdr[0].keys())
        conn.execute("DROP TABLE IF EXISTS cdhdr")
        conn.execute(f"CREATE TABLE cdhdr ({', '.join(c + ' TEXT' for c in cols)})")
        conn.executemany(
            f"INSERT INTO cdhdr VALUES ({', '.join('?' for _ in cols)})",
            [tuple(r.get(c, "") for c in cols) for r in all_cdhdr]
        )
        conn.commit()
        print(f"  CDHDR: {len(all_cdhdr):,} rows -> gold DB")

    # CDPOS
    cdpos_fp = os.path.join(CDPOS_DIR, "CDPOS_all.json")
    if os.path.exists(cdpos_fp):
        with open(cdpos_fp, encoding="utf-8") as f:
            cdpos_data = json.load(f)
        all_cdpos = cdpos_data.get("rows", [])
        if all_cdpos:
            cols = list(all_cdpos[0].keys())
            conn.execute("DROP TABLE IF EXISTS cdpos")
            conn.execute(f"CREATE TABLE cdpos ({', '.join(c + ' TEXT' for c in cols)})")
            conn.executemany(
                f"INSERT INTO cdpos VALUES ({', '.join('?' for _ in cols)})",
                [tuple(r.get(c, "") for c in cols) for r in all_cdpos]
            )
            conn.commit()
            print(f"  CDPOS: {len(all_cdpos):,} rows -> gold DB")

    conn.close()
    print("  [MERGE] Done.")


# ─────────────────────────────────────────────────────────────────────
# STATUS
# ─────────────────────────────────────────────────────────────────────

def print_status():
    print(f"\n{'='*60}")
    print(f"  CDHDR/CDPOS EXTRACTION STATUS")
    print(f"{'='*60}")

    for tbl, d in [("CDHDR", CDHDR_DIR), ("CDPOS", CDPOS_DIR)]:
        if not os.path.exists(d):
            print(f"  {tbl}: NOT STARTED")
            continue
        files = [f for f in os.listdir(d) if f.endswith(".json")]
        total = 0
        for fname in files:
            try:
                with open(os.path.join(d, fname), encoding="utf-8") as f:
                    data = json.load(f)
                total += data.get("meta", {}).get("row_count", 0)
            except Exception:
                pass
        print(f"  {tbl}: {len(files)} files, {total:,} rows")

    print(f"{'='*60}\n")


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CDHDR+CDPOS Extractor")
    parser.add_argument("--year",       type=int,   default=None)
    parser.add_argument("--batch-size", type=int,   default=5000)
    parser.add_argument("--throttle",   type=float, default=3.0)
    parser.add_argument("--cdhdr-only", action="store_true")
    parser.add_argument("--cdpos-only", action="store_true")
    parser.add_argument("--merge-only", action="store_true")
    parser.add_argument("--status",     action="store_true")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    years = [args.year] if args.year else YEARS
    sap_semaphore = threading.Semaphore(2)

    if args.merge_only:
        merge_to_sqlite()
        return

    t_start = datetime.now()
    print(f"\n{'='*60}")
    print(f"  CDHDR + CDPOS  |  P01  |  {t_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Years={years}  Batch={args.batch_size}  Throttle={args.throttle}s")
    print(f"{'='*60}\n")

    if not args.cdpos_only:
        extract_cdhdr(years, args.batch_size, args.throttle, sap_semaphore)

    if not args.cdhdr_only:
        extract_cdpos(years, args.batch_size, args.throttle, sap_semaphore)

    merge_to_sqlite()

    elapsed = (datetime.now() - t_start).total_seconds()
    print(f"\n  Finished. Total: {elapsed/60:.1f} min")
    print_status()


if __name__ == "__main__":
    main()
