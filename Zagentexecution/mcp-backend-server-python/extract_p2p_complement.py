"""
extract_p2p_complement.py
=========================
Extract tables needed for complete P2P and B2R process mining that are NOT
in the existing extraction scripts.

P2P complement:
  EBAN   — Purchase Requisitions (PR create/approve — first P2P step)
  RBKP   — Invoice Document Headers (Logistics Invoice Verification)
  RSEG   — Invoice Document Line Items (paired with RBKP)

B2R complement (FM tables missing from FMIFIIT extraction):
  FMIOI  — FM Commitments (WRTTP 50-65, obligations — middle of B2R)
  FMBH   — FM Budget Document Headers (budget entry — start of B2R)
  FMBL   — FM Budget Document Lines (budget detail)

Pattern: Same checkpoint-per-period design as extract_bkpf_bseg_parallel.py
Safety: Max 2 concurrent RFC connections via semaphore.

Output:
  extracted_data/<TABLE>/<TABLE>_YYYY_MM.json (per table per month)
  Merge to gold SQLite DB

Usage:
    python extract_p2p_complement.py                    # All tables
    python extract_p2p_complement.py --table EBAN       # Single table
    python extract_p2p_complement.py --pipeline p2p     # P2P tables only (EBAN+RBKP+RSEG)
    python extract_p2p_complement.py --pipeline b2r     # B2R tables only (FMIOI+FMBH+FMBL)
    python extract_p2p_complement.py --year 2025
    python extract_p2p_complement.py --merge-only
    python extract_p2p_complement.py --status
"""

import os
import json
import time
import argparse
import threading
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "extracted_data")
GOLD_DB  = os.path.join(BASE_DIR, "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
YEARS    = [2024, 2025, 2026]
BATCH_SIZE = 5000

# ─────────────────────────────────────────────────────────────────────
# TABLE DEFINITIONS
# ─────────────────────────────────────────────────────────────────────

# EBAN: Purchase Requisitions
EBAN_FIELDS = [
    "MANDT", "BANFN", "BNFPO", "BSART", "BSTYP", "LOEKZ", "STATU",
    "ERNAM", "ERDAT", "BADAT", "FRGDT", "FRGKZ",
    "EKGRP", "EKORG", "WERKS", "MATNR", "TXZ01",
    "MENGE", "MEINS", "PREIS", "PEINH", "WAERS",
    "KNTTP", "PSTYP", "BUKRS",
]

# RBKP: Invoice Document Headers
RBKP_FIELDS = [
    "MANDT", "BELNR", "GJAHR", "BLART", "BLDAT", "BUDAT", "USNAM",
    "TCODE", "CPUDT", "CPUTM", "WAERS", "RMWWR", "WMWST1",
    "LIFNR", "BUKRS", "XBLNR", "STBLG", "STJAH",
]

# RSEG: Invoice Document Line Items
RSEG_FIELDS = [
    "MANDT", "BELNR", "GJAHR", "BUZEI", "EBELN", "EBELP",
    "MATNR", "WERKS", "MENGE", "MEINS", "WRBTR", "WAERS",
    "MWSKZ", "BUKRS", "BSTME",
]

# FMIOI: FM Commitments (obligations — WRTTP 50-65)
FMIOI_FIELDS = [
    "FIKRS", "GJAHR", "FMBELNR", "FMBUZEI", "BTART", "RLDNR",
    "FONDS", "FISTL", "FIPEX", "FAREA", "WRTTP",
    "TWAER", "FKBTR", "TRBTR", "PERIO",
    "VRGNG", "BUKRS", "KNBELNR", "KNGJAHR", "SGTXT",
]

# FMBH: FM Budget Document Headers
FMBH_FIELDS = [
    "MANDT", "DOCNR", "GJAHR", "VERSN", "VORGA", "BELNR",
    "ERNAM", "ERDAT", "CPUDT", "CPUTM", "TCODE",
    "FIKRS",
]

# FMBL: FM Budget Document Lines
FMBL_FIELDS = [
    "MANDT", "DOCNR", "GJAHR", "VERSN", "DOCLN",
    "FONDS", "FISTL", "FIPEX", "FAREA",
    "WLBTR", "TWAER", "PERIO",
]

# Table → (fields, date_field, pipeline)
TABLE_DEFS = {
    "EBAN":  (EBAN_FIELDS,  "ERDAT", "p2p"),
    "RBKP":  (RBKP_FIELDS,  "BUDAT", "p2p"),
    "RSEG":  (RSEG_FIELDS,  "GJAHR", "p2p"),    # RSEG has no date field, use GJAHR
    "FMIOI": (FMIOI_FIELDS, "GJAHR", "b2r"),    # FMIOI has no BUDAT, use GJAHR+PERIO
    "FMBH":  (FMBH_FIELDS,  "ERDAT", "b2r"),
    "FMBL":  (FMBL_FIELDS,  "GJAHR", "b2r"),    # FMBL has no date field, use GJAHR
}


# ─────────────────────────────────────────────────────────────────────
# RFC HELPERS — imported from shared module
# ─────────────────────────────────────────────────────────────────────
from rfc_helpers import get_connection, rfc_read_paginated


# ─────────────────────────────────────────────────────────────────────
# EXTRACTION THREAD (per table)
# ─────────────────────────────────────────────────────────────────────

def extract_table_thread(table_name, fields, date_field, out_dir,
                          years, batch_size, throttle, sap_semaphore):
    label = f"[{table_name}]"

    with sap_semaphore:
        print(f"  {label} Semaphore acquired. Connecting to P01...")
        os.makedirs(out_dir, exist_ok=True)
        try:
            conn = get_connection("P01")
        except Exception as e:
            print(f"  {label} Connection FAILED: {e}")
            return

        total_rows = 0
        t_start = time.time()

        for year in years:
            # Tables with only GJAHR (no monthly date field): extract per year
            if date_field == "GJAHR":
                checkpoint = os.path.join(out_dir, f"{table_name}_{year}_00.json")
                if os.path.exists(checkpoint):
                    with open(checkpoint, encoding="utf-8") as f:
                        d = json.load(f)
                    cnt = d.get("meta", {}).get("row_count", 0)
                    print(f"  {label} SKIP {year} [{cnt} rows]")
                    total_rows += cnt
                    continue

                where = [f"GJAHR = '{year}'"]
                print(f"  {label} {year} (full year)...")
                t0 = time.time()
                try:
                    rows = rfc_read_paginated(conn, table_name, fields, where, batch_size, throttle)
                except Exception as e:
                    print(f"  {label} ERROR {year}: {e}")
                    rows = []

                elapsed = time.time() - t0
                data = {
                    "meta": {
                        "table": table_name, "year": year, "month": 0,
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
            else:
                # Monthly extraction via date field
                for month in range(1, 13):
                    monat = f"{month:02d}"
                    checkpoint = os.path.join(out_dir, f"{table_name}_{year}_{monat}.json")

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
                        where = [f"{date_field} >= '{date_from}' AND {date_field} < '{date_to_next}'"]
                    else:
                        where = [f"{date_field} >= '{date_from}' AND {date_field} <= '{year}1231'"]

                    print(f"  {label} {year}/{monat}...")
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
# MERGE TO SQLITE
# ─────────────────────────────────────────────────────────────────────

def merge_to_sqlite(tables_to_merge=None):
    print("\n[MERGE] Loading extracted tables into gold SQLite DB...")
    conn = sqlite3.connect(GOLD_DB)

    for tbl in (tables_to_merge or TABLE_DEFS.keys()):
        tbl_dir = os.path.join(DATA_DIR, tbl)
        if not os.path.exists(tbl_dir):
            print(f"  {tbl}: no data directory, skipping")
            continue

        all_rows = []
        for fname in sorted(os.listdir(tbl_dir)):
            if fname.endswith(".json"):
                with open(os.path.join(tbl_dir, fname), encoding="utf-8") as f:
                    data = json.load(f)
                all_rows.extend(data.get("rows", []))

        if not all_rows:
            print(f"  {tbl}: no rows found")
            continue

        cols = list(all_rows[0].keys())
        tbl_lower = tbl.lower()
        conn.execute(f"DROP TABLE IF EXISTS {tbl_lower}")
        conn.execute(f"CREATE TABLE {tbl_lower} ({', '.join(c + ' TEXT' for c in cols)})")
        conn.executemany(
            f"INSERT INTO {tbl_lower} VALUES ({', '.join('?' for _ in cols)})",
            [tuple(r.get(c, "") for c in cols) for r in all_rows]
        )
        conn.commit()
        print(f"  {tbl}: {len(all_rows):,} rows -> {tbl_lower}")

    conn.close()
    print("  [MERGE] Done.")


# ─────────────────────────────────────────────────────────────────────
# STATUS
# ─────────────────────────────────────────────────────────────────────

def print_status():
    print(f"\n{'='*60}")
    print(f"  P2P/B2R COMPLEMENT EXTRACTION STATUS")
    print(f"{'='*60}")
    for tbl in TABLE_DEFS:
        tbl_dir = os.path.join(DATA_DIR, tbl)
        if not os.path.exists(tbl_dir):
            print(f"  {tbl:<8}: NOT STARTED")
            continue
        files = [f for f in os.listdir(tbl_dir) if f.endswith(".json")]
        total = 0
        for fname in files:
            try:
                with open(os.path.join(tbl_dir, fname), encoding="utf-8") as f:
                    data = json.load(f)
                total += data.get("meta", {}).get("row_count", 0)
            except Exception:
                pass
        print(f"  {tbl:<8}: {len(files)} files, {total:>10,} rows")
    print(f"{'='*60}\n")


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="P2P/B2R complement extractor")
    parser.add_argument("--table",      type=str,   default=None,
                        help="Extract single table: EBAN, RBKP, RSEG, FMIOI, FMBH, FMBL")
    parser.add_argument("--pipeline",   choices=["p2p", "b2r"], default=None,
                        help="Run only P2P or B2R pipeline")
    parser.add_argument("--year",       type=int,   default=None)
    parser.add_argument("--batch-size", type=int,   default=BATCH_SIZE)
    parser.add_argument("--throttle",   type=float, default=3.0)
    parser.add_argument("--merge-only", action="store_true")
    parser.add_argument("--status",     action="store_true")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.merge_only:
        merge_to_sqlite()
        return

    years = [args.year] if args.year else YEARS
    sap_semaphore = threading.Semaphore(2)

    # Determine which tables to extract
    if args.table:
        tbl = args.table.upper()
        if tbl not in TABLE_DEFS:
            print(f"Unknown table: {tbl}. Options: {list(TABLE_DEFS.keys())}")
            return
        tables_to_run = {tbl: TABLE_DEFS[tbl]}
    elif args.pipeline:
        tables_to_run = {t: d for t, d in TABLE_DEFS.items() if d[2] == args.pipeline}
    else:
        tables_to_run = TABLE_DEFS

    t_start = datetime.now()
    print(f"\n{'='*60}")
    print(f"  P2P/B2R COMPLEMENT  |  P01  |  {t_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Tables: {list(tables_to_run.keys())}")
    print(f"  Years={years}  Batch={args.batch_size}  Throttle={args.throttle}s  Max conn=2")
    print(f"{'='*60}\n")

    # Launch threads — semaphore limits to 2 concurrent
    threads = []
    for tbl, (fields, date_field, _pipeline) in tables_to_run.items():
        out_dir = os.path.join(DATA_DIR, tbl)
        t = threading.Thread(
            target=extract_table_thread,
            args=(tbl, fields, date_field, out_dir, years, args.batch_size, args.throttle, sap_semaphore),
            name=tbl, daemon=True,
        )
        threads.append(t)
        t.start()
        print(f"  [QUEUED] {tbl}")
        time.sleep(0.5)

    for t in threads:
        t.join()

    merge_to_sqlite(list(tables_to_run.keys()))

    elapsed = (datetime.now() - t_start).total_seconds()
    print(f"\n  Finished. Total: {elapsed/60:.1f} min")
    print_status()


if __name__ == "__main__":
    main()
