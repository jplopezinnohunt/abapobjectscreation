"""
extract_ekko_ekpo_parallel.py
==============================
Parallel extractor for Purchasing & Entry Sheet data:
  - EKKO  : Purchase Order Headers
  - EKPO  : Purchase Order Line Items
  - EKBE  : PO History (GR, Entry Sheet, Invoice events)
  - ESSR  : Service Entry Sheet Headers
  - ESLL  : Service Entry Sheet Lines (derived from ESSR keys)

Covers fiscal years 2024-2026 from P01 (Production).

SAP-SAFE DESIGN (matches extract_bkpf_bseg_parallel.py):
  - All 4 main tables share the SAME global SAP semaphore (passed in by orchestrator)
  - Max 2 concurrent RFC connections at any time — GUARANTEED by semaphore
  - Within each table thread: sequential period-by-period extraction
  - Checkpointing per month — safe to resume at any time

Execution order when run standalone:
  Wave 1: EKKO + EKPO  (2 connections -> fills semaphore -> SAP at 100% limit)
  Wave 2: EKBE + ESSR  (2 connections -> same pattern)
  Wave 3: ESLL         (1 connection, uses ESSR keys)

When run from the master orchestrator, the semaphore is shared with FI tables,
so all 7 tables (BKPF, BSEG, EKKO, EKPO, EKBE, ESSR, ESLL) compete for only
2 slots — max 2 RFC connections at all times.

Output:
  extracted_data/EKKO/EKKO_YYYY_MM.json
  extracted_data/EKPO/EKPO_YYYY_MM.json
  extracted_data/EKBE/EKBE_YYYY_MM.json
  extracted_data/ESSR/ESSR_YYYY_MM.json
  extracted_data/ESLL/ESLL_all.json
  extracted_data/EKKO_EKPO_merged.json

Usage:
    python extract_ekko_ekpo_parallel.py
    python extract_ekko_ekpo_parallel.py --year 2024
    python extract_ekko_ekpo_parallel.py --table EKKO
    python extract_ekko_ekpo_parallel.py --merge-only
"""

import os
import json
import time
import argparse
import threading
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
DATA_DIR   = os.path.join(BASE_DIR, "extracted_data")
EKKO_DIR   = os.path.join(DATA_DIR, "EKKO")
EKPO_DIR   = os.path.join(DATA_DIR, "EKPO")
EKBE_DIR   = os.path.join(DATA_DIR, "EKBE")
ESSR_DIR   = os.path.join(DATA_DIR, "ESSR")
ESLL_DIR   = os.path.join(DATA_DIR, "ESLL")
MERGED_OUT = os.path.join(DATA_DIR, "EKKO_EKPO_merged.json")
YEARS      = [2024, 2025, 2026]

# Field lists (compact — avoid DATA_BUFFER_EXCEEDED)
EKKO_FIELDS = [
    "MANDT", "EBELN", "BUKRS", "BSART", "LOEKZ", "STATU", "AEDAT", "BEDAT",
    "EKGRP", "WAERS", "ZTERM", "LIFNR", "EKORG",
    # WERKS removed — auth-restricted on EKKO in P01, available on EKPO
]

EKPO_FIELDS = [
    "MANDT", "EBELN", "EBELP", "LOEKZ", "STATU", "AEDAT", "TXZ01",
    "MATNR", "BUKRS", "WERKS", "MENGE", "MEINS", "NETPR", "NETWR",
    "BRTWR", "MWSKZ", "PSTYP", "KNTTP", "BEDAT",
]

EKBE_FIELDS = [
    "MANDT", "EBELN", "EBELP", "ZEKKN", "VGABE", "GJAHR", "BELNR", "BUZEI",
    "BEWTP", "BUDAT", "BLDAT", "MENGE", "MEINS", "DMBTR", "WRBTR", "WAERS",
    "SHKZG", "XBLNR",
]

ESSR_FIELDS = [
    "MANDT", "LBLNI", "LBLNS", "ERDAT", "ERUHR", "USNAM",
    "EBELN", "EBELP", "LBLDT", "FRGKZ", "FRGDT", "WEBLNR",
]

ESLL_FIELDS = [
    "MANDT", "PACKNO", "INTROW", "SRVPOS", "EXTROW", "KTEXT1",
    "MENGE", "MEINS", "NETWR", "WAERS", "LOEKZ",
]

# Table -> (fields, date_field, output_dir)
TABLE_DEFS = {
    "EKKO": (EKKO_FIELDS, "BEDAT", EKKO_DIR),
    "EKPO": (EKPO_FIELDS, "AEDAT", EKPO_DIR),
    "EKBE": (EKBE_FIELDS, "BUDAT", EKBE_DIR),
    "ESSR": (ESSR_FIELDS, "ERDAT", ESSR_DIR),
}


# ─────────────────────────────────────────────────────────────────────────────
# RFC HELPERS — imported from shared module
# ─────────────────────────────────────────────────────────────────────────────
from rfc_helpers import get_connection, rfc_read_paginated


# ─────────────────────────────────────────────────────────────────────────────
# TABLE THREAD — acquires 1 semaphore slot for its full lifetime
# ─────────────────────────────────────────────────────────────────────────────

def extract_table_thread(table_name, fields, date_field, out_dir,
                          years, batch_size, throttle, sap_semaphore):
    label = f"[{table_name}]"

    with sap_semaphore:   # One slot of the global 2-connection limit
        print(f"  {label} Semaphore acquired. Connecting to P01...")
        os.makedirs(out_dir, exist_ok=True)
        try:
            conn = get_connection("P01")
        except Exception as e:
            print(f"  {label} Connection FAILED: {e}")
            return

        print(f"  {label} Connected. Extracting sequentially...")
        total_rows = 0
        t_start    = time.time()

        for year in years:
            for month in range(1, 13):
                monat      = f"{month:02d}"
                checkpoint = os.path.join(out_dir, f"{table_name}_{year}_{monat}.json")

                if os.path.exists(checkpoint):
                    with open(checkpoint, encoding="utf-8") as f:
                        d = json.load(f)
                    cnt = d.get("meta", {}).get("row_count", 0)
                    print(f"  {label} SKIP {year}/{monat}  [{cnt} rows]")
                    total_rows += cnt
                    continue

                date_from = f"{year}{monat}01"
                if month < 12:
                    date_to_next = f"{year}{(month+1):02d}01"
                    where = f"{date_field} >= '{date_from}' AND {date_field} < '{date_to_next}'"
                else:
                    where = f"{date_field} >= '{date_from}' AND {date_field} <= '{year}1231'"

                print(f"  {label} {year}/{monat}")
                t0 = time.time()
                errored = False
                try:
                    rows = rfc_read_paginated(conn, table_name, fields, where, batch_size, throttle)
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
                        "table": table_name, "year": year, "month": month,
                        "monat_str": monat, "row_count": len(rows),
                        "extracted_at": datetime.now().isoformat(),
                        "elapsed_sec": round(elapsed, 1),
                    },
                    "rows": rows,
                }
                with open(checkpoint, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, default=str)

                total_rows += len(rows)
                print(f"  {label}   -> {len(rows):,} rows  ({elapsed:.0f}s)  total: {total_rows:,}")
                if throttle > 0:
                    time.sleep(throttle)

        try: conn.close()
        except Exception: pass
        elapsed_total = (time.time() - t_start) / 60
        print(f"  {label} DONE. {total_rows:,} rows in {elapsed_total:.1f} min. Semaphore released.")


# ─────────────────────────────────────────────────────────────────────────────
# ESLL — derived extraction via ESSR LBLNI keys
# ─────────────────────────────────────────────────────────────────────────────

def extract_esll(years, batch_size, throttle, sap_semaphore):
    label = "[ESLL]"

    # Gather LBLNI keys from ESSR checkpoints
    lblni_set = set()
    for year in years:
        for month in range(1, 13):
            fp = os.path.join(ESSR_DIR, f"ESSR_{year}_{month:02d}.json")
            if os.path.exists(fp):
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                for row in data.get("rows", []):
                    v = row.get("LBLNI", "").strip()
                    if v: lblni_set.add(v)

    checkpoint = os.path.join(ESLL_DIR, "ESLL_all.json")
    if os.path.exists(checkpoint):
        with open(checkpoint, encoding="utf-8") as f:
            d = json.load(f)
        print(f"  {label} SKIP — checkpoint exists ({d['meta']['row_count']} rows)")
        return

    if not lblni_set:
        print(f"  {label} No LBLNI keys from ESSR checkpoints — skipping.")
        return

    keys = list(lblni_set)
    print(f"  {label} {len(keys)} unique LBLNI keys to query...")
    os.makedirs(ESLL_DIR, exist_ok=True)

    with sap_semaphore:
        print(f"  {label} Semaphore acquired -> connecting P01...")
        conn = get_connection("P01")
        all_rows = []
        CHUNK = 30   # SAP OR-chain limit

        for i in range(0, len(keys), CHUNK):
            chunk   = keys[i : i + CHUNK]
            in_expr = " OR ".join(f"PACKNO = '{k}'" for k in chunk)
            try:
                rows = rfc_read_paginated(conn, "ESLL", ESLL_FIELDS, f"( {in_expr} )", batch_size, throttle)
                all_rows.extend(rows)
                print(f"  {label} chunk {i//CHUNK+1}: +{len(rows)} rows  total: {len(all_rows):,}")
            except Exception as e:
                print(f"  {label} ERROR chunk {i//CHUNK+1}: {e}")
            time.sleep(throttle)

        conn.close()

    data = {
        "meta": {"table": "ESLL", "source_keys": len(keys),
                 "row_count": len(all_rows), "extracted_at": datetime.now().isoformat()},
        "rows": all_rows,
    }
    with open(checkpoint, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)
    print(f"  {label} DONE. {len(all_rows):,} rows -> {checkpoint}")


# ─────────────────────────────────────────────────────────────────────────────
# MERGE
# ─────────────────────────────────────────────────────────────────────────────

def merge_all():
    summary = {}
    for tbl, (_, _, out_dir) in TABLE_DEFS.items():
        total, periods = 0, []
        for year in YEARS:
            for month in range(1, 13):
                fp = os.path.join(out_dir, f"{tbl}_{year}_{month:02d}.json")
                if os.path.exists(fp):
                    with open(fp, encoding="utf-8") as f:
                        d = json.load(f)
                    cnt = d["meta"]["row_count"]
                    total += cnt
                    periods.append({"year": year, "month": month, "rows": cnt})
        summary[tbl] = {"total_rows": total, "periods": periods}

    esll_f = os.path.join(ESLL_DIR, "ESLL_all.json")
    if os.path.exists(esll_f):
        with open(esll_f, encoding="utf-8") as f:
            d = json.load(f)
        summary["ESLL"] = {"total_rows": d["meta"]["row_count"]}

    merged = {
        "meta": {"extraction_type": "EKKO+EKPO+EKBE+ESSR+ESLL (2024-2026)",
                 "merged_at": datetime.now().isoformat(), "source_system": "P01", "years": YEARS},
        "summary": summary,
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MERGED_OUT, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  [Merge MM] Done -> {MERGED_OUT}")
    for tbl, info in summary.items():
        print(f"    {tbl}: {info.get('total_rows', 0):>10,} rows")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main(sap_semaphore=None):
    parser = argparse.ArgumentParser(description="EKKO+EKPO+EKBE+ESSR extractor — max 2 SAP connections")
    parser.add_argument("--year",       type=int,   default=None)
    parser.add_argument("--batch-size", type=int,   default=5000)
    parser.add_argument("--throttle",   type=float, default=3.0)
    parser.add_argument("--merge-only", action="store_true")
    parser.add_argument("--skip-esll",  action="store_true")
    parser.add_argument("--table",      type=str,   default=None,
                        help="Extract only this table: EKKO, EKPO, EKBE, ESSR, ESLL")
    args = parser.parse_args()

    years      = [args.year] if args.year else YEARS
    batch_size = args.batch_size
    throttle   = args.throttle
    only_table = args.table.upper() if args.table else None

    # Standalone semaphore: allows 2 concurrent connections
    if sap_semaphore is None:
        sap_semaphore = threading.Semaphore(2)

    t_start = datetime.now()
    print(f"\n{'='*70}")
    print(f"  EKKO+EKPO+EKBE+ESSR  |  P01  |  {t_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Years={years}  Batch={batch_size}  Throttle={throttle}s  Max connections=2")
    print(f"{'='*70}\n")

    if not args.merge_only:
        tables_to_run = (
            {only_table: TABLE_DEFS[only_table]}
            if only_table and only_table in TABLE_DEFS
            else TABLE_DEFS
        )

        # Launch all table threads — semaphore limits to 2 active at a time
        threads = []
        for tbl, (fields, date_field, out_dir) in tables_to_run.items():
            t = threading.Thread(
                target=extract_table_thread,
                args=(tbl, fields, date_field, out_dir, years, batch_size, throttle, sap_semaphore),
                name=tbl, daemon=True,
            )
            threads.append(t)
            t.start()
            print(f"  [QUEUED] {tbl} — waiting for a semaphore slot...")
            time.sleep(0.5)   # Stagger thread startup

        for t in threads:
            t.join()

        # ESLL always runs after ESSR (needs its keys)
        if not args.skip_esll and (not only_table or only_table == "ESLL"):
            extract_esll(years, batch_size, throttle, sap_semaphore)

    if not only_table:
        merge_all()

    elapsed = (datetime.now() - t_start).total_seconds()
    print(f"\n  MM pipeline finished. Total: {elapsed/60:.1f} min")


if __name__ == "__main__":
    main()
