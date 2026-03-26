"""
extract_bkpf_bseg_parallel.py
==============================
Extracts BKPF (FI Doc Headers) + BSEG replacement tables from P01.

CELONIS PATTERN: Instead of extracting the BSEG cluster table directly
(slow, 6 fields/call, no date filter), extract the 6 transparent secondary
index tables and UNION them in SQLite to reconstruct BSEG:

  Vendor (AP/P2P):    BSIK (open) + BSAK (cleared)   KOART=K
  Customer (AR/O2C):  BSID (open) + BSAD (cleared)   KOART=D
  GL Account (B2R):   BSIS (open) + BSAS (cleared)   KOART=S

Benefits:
  - Transparent tables = standard date-based extraction (CPUDT/BUDAT)
  - All fields available (WAERS, HKONT, BUDAT, MONAT, etc.)
  - 10-50x faster than BSEG cluster extraction
  - Auto field-splitting handles the 512-byte buffer limit
  - UNION in SQLite recreates BSEG with deduplication

Ref: https://docs.celonis.com/en/replacing-sap-cluster-tables--bseg-.html

SAP SAFETY:
  - Max 2 concurrent RFC connections via semaphore
  - Checkpoint per table per month -- safe to resume
  - Proven batch_size=5000, throttle=3.0

Output:
  extracted_data/BKPF/BKPF_YYYY_MM.json
  extracted_data/BSIK/BSIK_YYYY_MM.json  (+ BSAK, BSID, BSAD, BSIS, BSAS)
  UNION as 'bseg' view in SQLite gold DB

Usage:
    python extract_bkpf_bseg_parallel.py                  # Full run
    python extract_bkpf_bseg_parallel.py --year 2025
    python extract_bkpf_bseg_parallel.py --bkpf-only
    python extract_bkpf_bseg_parallel.py --table BSIK     # Single table
    python extract_bkpf_bseg_parallel.py --merge-only
"""

import os
import json
import time
import argparse
import threading
from datetime import datetime

# -----------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------
BASE_DIR   = os.path.dirname(__file__)
DATA_DIR   = os.path.join(BASE_DIR, "extracted_data")
BKPF_DIR   = os.path.join(DATA_DIR, "BKPF")
MERGED_OUT = os.path.join(DATA_DIR, "BKPF_BSEG_merged.json")
YEARS      = [2024, 2025, 2026]
BATCH_SIZE = 5000

# BKPF: FI Document Header
BKPF_FIELDS = [
    "MANDT", "BUKRS", "BELNR", "GJAHR", "BLART", "BLDAT", "BUDAT", "MONAT",
    "CPUDT", "CPUTM", "USNAM", "TCODE", "BKTXT", "WAERS",
    "AWTYP", "AWKEY", "XBLNR", "GLVOR",
]

# BSEG secondary index tables -- common fields across all 6 tables
# These are the fields we need for process mining (P2P, B2R, AR, AP)
# All 6 tables share this field structure (they mirror BSEG columns)
BSEG_REPLACEMENT_FIELDS = [
    # Keys
    "MANDT", "BUKRS", "BELNR", "GJAHR", "BUZEI",
    # Dates (available on transparent tables, NOT on BSEG cluster)
    "BUDAT", "BLDAT", "CPUDT", "MONAT",
    # Amounts
    "SHKZG", "WRBTR", "WAERS",   # Document currency amount + debit/credit indicator
    "DMBTR",                      # Local currency amount
    "DMBE2",                      # Second local currency amount
    # Account assignment
    "HKONT", "BSCHL", "GSBER", "KOSTL",
    "AUFNR", "PRCTR", "FKBER",
    # PS/WBS assignment (internal key — JOIN with PRPS.PSPNR to get POSID)
    "PS_PSP_PNR",
    # References
    "EBELN", "EBELP", "MWSKZ",
    # Clearing
    "AUGDT", "AUGBL",
    # Vendor/Customer (only populated on respective tables)
    "LIFNR",
    # Text
    "SGTXT",
    # Payment terms
    "ZFBDT", "ZTERM",
]

# GL tables (BSIS/BSAS) have different structure: no LIFNR, no CPUDT, use BUDAT
BSEG_GL_FIELDS = [f for f in BSEG_REPLACEMENT_FIELDS if f not in ("LIFNR", "CPUDT")]

# Table definitions: (table_name, date_field, koart, description)
BSEG_TABLES = [
    ("BSIK", "CPUDT", "K", "Vendor open items"),
    ("BSAK", "CPUDT", "K", "Vendor cleared items"),
    ("BSID", "CPUDT", "D", "Customer open items"),
    ("BSAD", "CPUDT", "D", "Customer cleared items"),
    ("BSIS", "BUDAT", "S", "GL open items"),
    ("BSAS", "BUDAT", "S", "GL cleared items"),
]

# All table defs for the orchestrator: table -> (fields, date_field, out_dir)
TABLE_DEFS = {}
for tbl_name, date_f, koart, desc in BSEG_TABLES:
    fields = BSEG_GL_FIELDS if koart == "S" else BSEG_REPLACEMENT_FIELDS
    TABLE_DEFS[tbl_name] = (fields, date_f, os.path.join(DATA_DIR, tbl_name))


# -----------------------------------------------------------------------
# RFC HELPERS -- imported from shared module
# -----------------------------------------------------------------------
from rfc_helpers import get_connection, rfc_read_paginated


# -----------------------------------------------------------------------
# TABLE THREAD (one connection, sequential periods)
# -----------------------------------------------------------------------

def extract_table_thread(table_name, fields, date_field, out_dir,
                          years, batch_size, throttle, sap_semaphore):
    """
    Extracts a single table month-by-month using date_field as filter.
    Acquires one semaphore slot for the full duration.
    Works for BKPF and all BSEG replacement tables (transparent).
    """
    label = f"[{table_name}]"

    with sap_semaphore:
        print(f"  {label} Semaphore acquired. Connecting to P01...")
        os.makedirs(out_dir, exist_ok=True)

        try:
            conn = get_connection("P01")
        except Exception as e:
            print(f"  {label} Connection FAILED: {e}")
            return

        print(f"  {label} Connected. Extracting {len(years)*12} periods sequentially...")
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
                    print(f"  {label} SKIP {year}/{monat}  [{cnt} rows -- already done]")
                    total_rows += cnt
                    continue

                # WHERE clause
                date_from = f"{year}{monat}01"
                if month < 12:
                    date_to_next = f"{year}{(month+1):02d}01"
                    where = f"{date_field} >= '{date_from}' AND {date_field} < '{date_to_next}'"
                else:
                    where = f"{date_field} >= '{date_from}' AND {date_field} <= '{year}1231'"

                print(f"  {label} {year}/{monat}  where: {where}")
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
                    # If connection is dead, try to reconnect before continuing
                    try:
                        conn.close()
                    except Exception:
                        pass
                    try:
                        conn = get_connection("P01")
                        print(f"  {label}   -> Reconnected to P01")
                    except Exception as ce:
                        print(f"  {label}   -> Reconnect failed: {ce} -- stopping extraction")
                        break
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
                print(f"  {label}   -> {len(rows):,} rows  ({elapsed:.0f}s)  running total: {total_rows:,}")

                if throttle > 0:
                    time.sleep(throttle)

        try:
            conn.close()
        except Exception:
            pass

        elapsed_total = (time.time() - t_start) / 60
        print(f"\n  {label} COMPLETE. {total_rows:,} rows in {elapsed_total:.1f} min. Semaphore released.")


# -----------------------------------------------------------------------
# MERGE / STATUS
# -----------------------------------------------------------------------

def merge_all():
    """Merge checkpoint summaries into a single status file."""
    all_tables = {}
    for tbl_name, _, _, _ in [("BKPF", "BUDAT", "", "")] + BSEG_TABLES:
        tbl_dir = os.path.join(DATA_DIR, tbl_name)
        summaries = []
        if os.path.exists(tbl_dir):
            for year in YEARS:
                for month in range(1, 13):
                    monat = f"{month:02d}"
                    fp = os.path.join(tbl_dir, f"{tbl_name}_{year}_{monat}.json")
                    if os.path.exists(fp):
                        with open(fp, encoding="utf-8", errors="replace") as f:
                            d = json.load(f)
                        summaries.append({
                            "year": d["meta"]["year"], "month": d["meta"]["month"],
                            "rows": d["meta"]["row_count"],
                        })
        total = sum(s["rows"] for s in summaries)
        all_tables[tbl_name] = {"periods": len(summaries), "total_rows": total, "summary": summaries}

    merged = {
        "meta": {
            "extraction_type": "BKPF + BSEG replacement (Celonis pattern)",
            "tables": ["BKPF"] + [t[0] for t in BSEG_TABLES],
            "merged_at": datetime.now().isoformat(),
            "source_system": "P01", "years": YEARS,
        },
        "tables": all_tables,
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MERGED_OUT, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n  [Merge] Status:")
    for tbl, info in all_tables.items():
        print(f"    {tbl:<6}: {info['total_rows']:>10,} rows  ({info['periods']} periods)")
    print(f"  -> {MERGED_OUT}")
    return merged


# -----------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------

def main(sap_semaphore=None):
    parser = argparse.ArgumentParser(
        description="BKPF + BSEG replacement tables (Celonis pattern) -- max 2 SAP connections"
    )
    parser.add_argument("--year",       type=int,   default=None)
    parser.add_argument("--batch-size", type=int,   default=5000)
    parser.add_argument("--throttle",   type=float, default=3.0)
    parser.add_argument("--bkpf-only",  action="store_true", help="Extract only BKPF")
    parser.add_argument("--table",      type=str,   default=None,
                        help="Extract only this table (BSIK, BSAK, BSID, BSAD, BSIS, BSAS)")
    parser.add_argument("--merge-only", action="store_true")
    args = parser.parse_args()

    years      = [args.year] if args.year else YEARS
    batch_size = args.batch_size
    throttle   = args.throttle

    if sap_semaphore is None:
        sap_semaphore = threading.Semaphore(2)

    t_start = datetime.now()
    print(f"\n{'='*70}")
    print(f"  BKPF + BSEG Replacement  |  P01  |  {t_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Years={years}  Batch={batch_size}  Throttle={throttle}s")
    print(f"  Tables: BKPF + BSIK/BSAK/BSID/BSAD/BSIS/BSAS (Celonis pattern)")
    print(f"{'='*70}\n")

    if args.merge_only:
        merge_all()
        return

    threads = []

    # BKPF extraction
    if not args.table:
        if not False:  # always extract BKPF unless --table is specified
            t = threading.Thread(
                target=extract_table_thread,
                args=("BKPF", BKPF_FIELDS, "BUDAT", BKPF_DIR,
                      years, batch_size, throttle, sap_semaphore),
                name="BKPF", daemon=True,
            )
            threads.append(t)
            t.start()
            print("  [START] BKPF -> extracting by BUDAT...")

    if args.bkpf_only:
        for t in threads:
            t.join()
        merge_all()
        return

    # BSEG replacement tables
    time.sleep(0.5)
    for tbl_name, date_f, koart, desc in BSEG_TABLES:
        if args.table and args.table.upper() != tbl_name:
            continue

        fields, date_field, out_dir = TABLE_DEFS[tbl_name]
        t = threading.Thread(
            target=extract_table_thread,
            args=(tbl_name, fields, date_field, out_dir,
                  years, batch_size, throttle, sap_semaphore),
            name=tbl_name, daemon=True,
        )
        threads.append(t)
        t.start()
        print(f"  [START] {tbl_name} -> {desc} (KOART={koart}, filter={date_f})")
        time.sleep(0.5)

    for t in threads:
        t.join()

    merge_all()
    elapsed = (datetime.now() - t_start).total_seconds()
    print(f"\n  Finished. Total: {elapsed/60:.1f} min")


if __name__ == "__main__":
    main()
