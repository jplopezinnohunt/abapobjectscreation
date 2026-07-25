"""
extract_ps_avc_core.py
======================
Block A — PS-AVC core tables for INC-000005638.

Strategy:
  - Chunk by GJAHR x WRTTP (value-type) for COSP, COSS, BPJA
  - Chunk by RYEAR for FMAVCT (FM-AVC live pool)
  - Single pull for BPGE, BPHI (no GJAHR in key)
  - Targeted pull for EKKN (the 3 incident POs first, then broader)
  - All fields per table (no SELECT field list — RFC returns all by default
    when FIELDS=[] is passed). The rfc_helpers wrapper auto-splits if the
    512-byte field buffer is exceeded.
  - 5-min hard timeout per chunk via ALARM-style wrapper.
  - Skip-existing per (table, GJAHR, WRTTP) tuple for resume safety.

Scope: GJAHR 2024-2026 only.

Run:
    python extract_ps_avc_core.py
    python extract_ps_avc_core.py --table COSP
    python extract_ps_avc_core.py --table COSP --year 2026 --wrttp 04
"""

import os
import sys
import time
import sqlite3
import argparse
import threading
from datetime import datetime

MCP = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD_DB = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
LOG_DIR = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, f"ps_avc_core_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

YEARS = ["2024", "2025", "2026"]
# Value types relevant for PS-AVC.
# Actuals/commitments side (COSP/COSS): 04=Actual, 11=Statistical actual,
#   01=Plan, 21=Statistical plan
# Budget side (BPJA/BPGE): 41=Current budget, 42=Original, 43=Supplement,
#   44=Return, 51=Released, 54=Actual-as-budget, 60=Distributable, 61=Assigned
WRTTP_CONSUMPTION = ["04", "11"]   # tightest set for PS-AVC consumption
WRTTP_BUDGET = ["41", "42", "43", "44", "51", "60", "61"]
BATCH_SIZE = 5000
THROTTLE = 3.0
CHUNK_TIMEOUT_SEC = 300  # 5 minutes per chunk


def log(msg):
    line = f"{datetime.now().strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


# ---------------------------------------------------------------------------
# Generic per-chunk extractor with thread-based timeout
# ---------------------------------------------------------------------------
def _extract_one_chunk(table, where, on_rows):
    """Extract a single chunk with timeout protection. Returns (n_rows, error)."""
    result = {"rows": None, "err": None}

    def runner():
        try:
            conn = get_connection("P01")
            try:
                rows = rfc_read_paginated(
                    conn, table, [], where,
                    batch_size=BATCH_SIZE, throttle=THROTTLE
                )
                result["rows"] = rows
            finally:
                try: conn.close()
                except Exception: pass
        except Exception as e:
            result["err"] = f"{type(e).__name__}: {e}"

    t = threading.Thread(target=runner, daemon=True)
    t.start()
    t.join(CHUNK_TIMEOUT_SEC)
    if t.is_alive():
        return 0, "TIMEOUT"
    if result["err"]:
        return 0, result["err"]
    rows = result["rows"] or []
    on_rows(rows)
    return len(rows), None


def load_rows_to_sqlite(db, table_name, rows):
    """Persist rows to SQLite. Schema = union of keys across rows."""
    if not rows:
        return 0
    tbl = table_name.lower()
    fields = sorted({k for r in rows for k in r.keys()})
    cols_def = ", ".join([f'"{f}" TEXT' for f in fields])
    db.execute(f'CREATE TABLE IF NOT EXISTS {tbl} ({cols_def})')
    # Make sure all columns exist (extend schema if new keys appear)
    existing = {row[1] for row in db.execute(f'PRAGMA table_info({tbl})').fetchall()}
    for f in fields:
        if f not in existing:
            db.execute(f'ALTER TABLE {tbl} ADD COLUMN "{f}" TEXT')
    placeholders = ", ".join(["?"] * len(fields))
    col_list = ", ".join([f'"{f}"' for f in fields])
    batch = [tuple(r.get(f, "") for f in fields) for r in rows]
    db.executemany(f'INSERT INTO {tbl} ({col_list}) VALUES ({placeholders})', batch)
    db.commit()
    return len(batch)


def already_loaded(db, table, where_clause):
    """Return existing row count matching where (or -1 if table doesn't exist)."""
    tbl = table.lower()
    try:
        n = db.execute(f'SELECT COUNT(*) FROM {tbl} WHERE {where_clause}').fetchone()[0]
        return n
    except sqlite3.OperationalError:
        return -1


# ---------------------------------------------------------------------------
# Per-table extraction strategies
# ---------------------------------------------------------------------------
def extract_cosp_or_coss(table, db, years, wrttps):
    """COSP/COSS: chunk by GJAHR x WRTTP, OBJNR LIKE 'PR%' (PS WBS only)."""
    total = 0
    for year in years:
        for wt in wrttps:
            sql_where = f"OBJNR LIKE 'PR%' AND GJAHR = '{year}' AND WRTTP = '{wt}'"
            existing = already_loaded(db, table, sql_where)
            if existing > 0:
                log(f"  {table} {year} W{wt}: skip ({existing:,} already loaded)")
                total += existing
                continue
            t0 = time.time()
            n, err = _extract_one_chunk(
                table, sql_where,
                lambda rows: load_rows_to_sqlite(db, table, rows)
            )
            dt = time.time() - t0
            if err:
                log(f"  {table} {year} W{wt}: ERROR {err} ({dt:.0f}s)")
            else:
                log(f"  {table} {year} W{wt}: {n:,} rows ({dt:.0f}s)")
                total += n
    return total


def extract_bpja(db, years):
    """BPJA: GJAHR + WRTTP keyed. Pull all WRTTP for budget side."""
    table = "BPJA"
    total = 0
    for year in years:
        sql_where = f"OBJNR LIKE 'PR%' AND GJAHR = '{year}'"
        existing = already_loaded(db, table, sql_where)
        if existing > 0:
            log(f"  {table} {year}: skip ({existing:,} already loaded)")
            total += existing
            continue
        t0 = time.time()
        n, err = _extract_one_chunk(
            table, sql_where,
            lambda rows: load_rows_to_sqlite(db, table, rows)
        )
        dt = time.time() - t0
        if err:
            log(f"  {table} {year}: ERROR {err} ({dt:.0f}s)")
            # Fallback: chunk by WRTTP if too big
            if "DATA_BUFFER_EXCEEDED" in err or "TIMEOUT" in err:
                log(f"    -> retry by WRTTP")
                for wt in WRTTP_BUDGET + WRTTP_CONSUMPTION:
                    inner_where = sql_where + f" AND WRTTP = '{wt}'"
                    t1 = time.time()
                    n2, err2 = _extract_one_chunk(
                        table, inner_where,
                        lambda rows: load_rows_to_sqlite(db, table, rows)
                    )
                    dt1 = time.time() - t1
                    if err2:
                        log(f"    {table} {year} W{wt}: ERROR {err2} ({dt1:.0f}s)")
                    else:
                        log(f"    {table} {year} W{wt}: {n2:,} rows ({dt1:.0f}s)")
                        total += n2
        else:
            log(f"  {table} {year}: {n:,} rows ({dt:.0f}s)")
            total += n
    return total


def extract_bpge(db):
    """BPGE: no GJAHR in key. Single pull for PS objects."""
    table = "BPGE"
    sql_where = "OBJNR LIKE 'PR%'"
    existing = already_loaded(db, table, sql_where)
    if existing > 1000:  # 654 was the suspicious initial count
        log(f"  {table}: skip ({existing:,} already loaded)")
        return existing
    # Re-extract fresh
    db.execute(f"DELETE FROM bpge WHERE OBJNR LIKE 'PR%'")
    db.commit()
    t0 = time.time()
    n, err = _extract_one_chunk(
        table, sql_where,
        lambda rows: load_rows_to_sqlite(db, table, rows)
    )
    dt = time.time() - t0
    if err:
        log(f"  {table}: ERROR {err} ({dt:.0f}s)")
        return 0
    log(f"  {table}: {n:,} rows ({dt:.0f}s)")
    return n


def extract_bphi(db):
    """BPHI: small budget header table. Single pull, no WHERE."""
    table = "BPHI"
    existing = already_loaded(db, table, "1=1")
    if existing > 0:
        log(f"  {table}: skip ({existing:,} already loaded)")
        return existing
    t0 = time.time()
    n, err = _extract_one_chunk(
        table, "OBJNR LIKE 'PR%'",
        lambda rows: load_rows_to_sqlite(db, table, rows)
    )
    dt = time.time() - t0
    if err:
        log(f"  {table}: ERROR {err} ({dt:.0f}s)")
        return 0
    log(f"  {table}: {n:,} rows ({dt:.0f}s)")
    return n


def extract_fmavct(db, years):
    """FMAVCT: live FM-AVC pool. Chunk by RYEAR. RFIKRS='UNES'."""
    table = "FMAVCT"
    total = 0
    for year in years:
        sql_where = f"RFIKRS = 'UNES' AND RYEAR = '{year}'"
        existing = already_loaded(db, table, sql_where)
        if existing > 0:
            log(f"  {table} {year}: skip ({existing:,} already loaded)")
            total += existing
            continue
        t0 = time.time()
        n, err = _extract_one_chunk(
            table, sql_where,
            lambda rows: load_rows_to_sqlite(db, table, rows)
        )
        dt = time.time() - t0
        if err:
            log(f"  {table} {year}: ERROR {err} ({dt:.0f}s)")
        else:
            log(f"  {table} {year}: {n:,} rows ({dt:.0f}s)")
            total += n
    return total


def extract_ekkn_for_incident(db):
    """EKKN: targeted pull for the 3 incident POs first."""
    table = "EKKN"
    pos = ["4500543365", "4500540022", "4500540024"]
    where_in = ",".join([f"'{p}'" for p in pos])
    sql_where = f"EBELN IN ({where_in})"
    existing = already_loaded(db, table, sql_where)
    if existing > 0:
        log(f"  {table} (3 incident POs): skip ({existing:,} already loaded)")
        return existing
    t0 = time.time()
    n, err = _extract_one_chunk(
        table, sql_where,
        lambda rows: load_rows_to_sqlite(db, table, rows)
    )
    dt = time.time() - t0
    if err:
        log(f"  {table} (3 POs): ERROR {err} ({dt:.0f}s)")
        return 0
    log(f"  {table} (3 POs): {n:,} rows ({dt:.0f}s)")
    return n


def extract_ekkn_broader(db):
    """EKKN: broader pull for class analysis. Chunk by EBELN ranges."""
    table = "EKKN"
    total = 0
    # PO ranges typical at UNESCO: 4500*, 4600*, 4700*
    ranges = [
        ("4500000000", "4600000000"),
        ("4600000000", "4700000000"),
        ("4700000000", "4800000000"),
    ]
    for lo, hi in ranges:
        sql_where = f"EBELN >= '{lo}' AND EBELN < '{hi}'"
        existing = already_loaded(db, table, sql_where)
        if existing > 1000:
            log(f"  {table} [{lo}-{hi}): skip ({existing:,} already loaded)")
            total += existing
            continue
        t0 = time.time()
        n, err = _extract_one_chunk(
            table, sql_where,
            lambda rows: load_rows_to_sqlite(db, table, rows)
        )
        dt = time.time() - t0
        if err:
            log(f"  {table} [{lo}-{hi}): ERROR {err} ({dt:.0f}s)")
        else:
            log(f"  {table} [{lo}-{hi}): {n:,} rows ({dt:.0f}s)")
            total += n
    return total


def extract_t185f(db):
    """T185F: PS field selection — small config table."""
    table = "T185F"
    existing = already_loaded(db, table, "1=1")
    if existing > 0:
        log(f"  {table}: skip ({existing:,} already loaded)")
        return existing
    t0 = time.time()
    n, err = _extract_one_chunk(
        table, "",
        lambda rows: load_rows_to_sqlite(db, table, rows)
    )
    dt = time.time() - t0
    if err:
        log(f"  {table}: ERROR {err} ({dt:.0f}s)")
        return 0
    log(f"  {table}: {n:,} rows ({dt:.0f}s)")
    return n


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", help="Single table (COSP, COSS, BPJA, BPGE, BPHI, FMAVCT, EKKN, T185F)")
    parser.add_argument("--year", help="Single year (used with --table COSP/COSS/BPJA/FMAVCT)")
    parser.add_argument("--wrttp", help="Single WRTTP (used with --table COSP/COSS)")
    parser.add_argument("--ekkn-broader", action="store_true", help="Also pull EKKN broader range")
    args = parser.parse_args()

    log(f"=== PS-AVC core extraction starting ===")
    log(f"Log: {LOG_PATH}")
    log(f"Gold DB: {GOLD_DB}")
    log(f"Years: {YEARS} | WRTTP_consumption: {WRTTP_CONSUMPTION}")

    db = sqlite3.connect(GOLD_DB)
    grand = 0
    t_start = time.time()

    years = [args.year] if args.year else YEARS
    wrttps = [args.wrttp] if args.wrttp else WRTTP_CONSUMPTION

    if args.table:
        tbl = args.table.upper()
        if tbl in ("COSP", "COSS"):
            grand += extract_cosp_or_coss(tbl, db, years, wrttps)
        elif tbl == "BPJA":
            grand += extract_bpja(db, years)
        elif tbl == "BPGE":
            grand += extract_bpge(db)
        elif tbl == "BPHI":
            grand += extract_bphi(db)
        elif tbl == "FMAVCT":
            grand += extract_fmavct(db, years)
        elif tbl == "EKKN":
            grand += extract_ekkn_for_incident(db)
            if args.ekkn_broader:
                grand += extract_ekkn_broader(db)
        elif tbl == "T185F":
            grand += extract_t185f(db)
        else:
            log(f"Unknown table {tbl}")
    else:
        # Full sequence — incident-priority order
        log("--- Phase 1: incident-blocking pulls (EKKN + FMAVCT + BPHI) ---")
        grand += extract_ekkn_for_incident(db)
        grand += extract_t185f(db)
        grand += extract_bphi(db)
        grand += extract_fmavct(db, YEARS)

        log("--- Phase 2: PS budget (BPJA, BPGE) ---")
        grand += extract_bpja(db, YEARS)
        grand += extract_bpge(db)

        log("--- Phase 3: CO totals (COSP, COSS) — chunked by GJAHR x WRTTP ---")
        grand += extract_cosp_or_coss("COSP", db, YEARS, WRTTP_CONSUMPTION)
        grand += extract_cosp_or_coss("COSS", db, YEARS, WRTTP_CONSUMPTION)

        if args.ekkn_broader:
            log("--- Phase 4 (optional): EKKN broader for class analysis ---")
            grand += extract_ekkn_broader(db)

    db.close()
    dt = time.time() - t_start
    log(f"=== DONE — total rows touched: {grand:,} | elapsed: {dt/60:.1f} min ===")


if __name__ == "__main__":
    main()
