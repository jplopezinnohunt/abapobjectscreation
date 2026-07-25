"""
extraction_status.py
=====================
Unified status dashboard + SQLite loader for all SAP extractions.

Shows a comparison table:
  Table  | SAP Checkpoint Rows | SQLite Rows | Coverage | Priority

Loads extracted JSON checkpoints into SQLite one table at a time.
Handles all tables: existing PSM tables + new FI/MM tables.

SQLite DB: knowledge/domains/PSM/p01_gold_master_data.db

TABLE LOAD PRIORITY ORDER (decided by data size + dependency):
  1. BKPF   — FI Document Headers       (small, key table for analysis)
  2. EKKO   — PO Headers                (small, fast)
  3. EKPO   — PO Line Items             (medium)
  4. EKBE   — PO History / GR / SES     (medium — links PO to entry sheets)
  5. ESSR   — Entry Sheet Headers       (small)
  6. ESLL   — Entry Sheet Lines         (depends on ESSR keys)
  7. BSEG   — FI Line Items             (LARGEST — load last, takes longest)

Usage:
    python extraction_status.py                     # Show status only
    python extraction_status.py --load BKPF         # Load BKPF into SQLite
    python extraction_status.py --load EKKO         # Load EKKO into SQLite
    python extraction_status.py --load all          # Load all in priority order
    python extraction_status.py --clear BKPF        # Drop & recreate BKPF table in SQLite
    python extraction_status.py --status-only       # Compact status (no row preview)
"""

import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
SCRIPTS_DIR  = os.path.dirname(os.path.abspath(__file__))
BASE_DIR     = os.path.dirname(SCRIPTS_DIR)   # sap_data_extraction/
DATA_DIR     = os.path.join(BASE_DIR, "extracted_data")
DB_PATH      = os.path.normpath(os.path.join(BASE_DIR, "sqlite", "p01_gold_master_data.db"))
DB_V2_PATH   = os.path.normpath(os.path.join(BASE_DIR, "sqlite", "p01_master_data_v2.db"))
TADIR_DB     = os.path.normpath(os.path.join(BASE_DIR, "..", "..",
                "mcp-backend-server-python", "tadir_cache.sqlite"))

YEARS = [2024, 2025, 2026]

# ─────────────────────────────────────────────────────────────────────────────
# TABLE REGISTRY
# Priority order: 1=highest  | type: period=monthly checkpoints, single=one file
# ─────────────────────────────────────────────────────────────────────────────
TABLE_REGISTRY = [
    # (table_name, checkpoint_dir, file_pattern, sqlite_table, priority, note)
    ("BKPF", os.path.join(DATA_DIR, "BKPF"), "BKPF_{y}_{m}.json", "bkpf", 1, "FI Doc Headers"),
    ("EKKO", os.path.join(DATA_DIR, "EKKO"), "EKKO_{y}_{m}.json", "ekko", 2, "PO Headers"),
    ("EKPO", os.path.join(DATA_DIR, "EKPO"), "EKPO_{y}_{m}.json", "ekpo", 3, "PO Lines"),
    ("EKBE", os.path.join(DATA_DIR, "EKBE"), "EKBE_{y}_{m}.json", "ekbe", 4, "PO History/GR/SES"),
    ("ESSR", os.path.join(DATA_DIR, "ESSR"), "ESSR_{y}_{m}.json", "essr", 5, "Entry Sheet Headers"),
    ("ESLL", os.path.join(DATA_DIR, "ESLL"), "ESLL_all.json",     "esll", 6, "Entry Sheet Lines (single file)"),
    ("BSEG", os.path.join(DATA_DIR, "BSEG"), "BSEG_{y}_{m}.json", "bseg", 7, "FI Line Items (LARGEST)"),
]

# ─────────────────────────────────────────────────────────────────────────────
# FULL SQLITE INVENTORY — all 3 databases
# (db_label, sqlite_table, sap_source_table, description)
# ─────────────────────────────────────────────────────────────────────────────
EXISTING_SQLITE_TABLES = [
    # ── p01_gold_master_data.db (PSM master data) ───────────────────────────
    ("PSM",  "funds",              "FMFCT",         "FM Funds Master"),
    ("PSM",  "fund_centers",       "FMFCTR",        "FM Fund Centers"),
    ("PSM",  "proj",               "PROJ",          "PS Project Definitions"),
    ("PSM",  "prps",               "PRPS",          "PS WBS Elements"),
    ("PSM",  "ytfm_fund_cpl",      "YTFM_FUND_CPL", "UNESCO Fund-Ceiling coupling"),
    ("PSM",  "ytfm_wrttp_gr",      "YTFM_WRTTP_GR", "UNESCO Value Type Groups"),
    ("PSM",  "movements_summary",  "FMIFIIT",       "FM FI Integration (summary)"),
    ("PSM",  "fmbdt_summary",      "FMBDT",         "FM Budget Table (summary)"),
    ("PSM",  "fmavct_summary",     "FMAVCT",        "FM Availability Control (summary)"),
    ("PSM",  "fmifiit_full",       "FMIFIIT",       "FM FI Integration full (empty)"),
    ("PSM",  "fmifiit_raw_data",   "FMIFIIT",       "FM FI Raw data (empty)"),
    ("PSM",  "cooi",               "COOI",          "CO Order Items (empty)"),
    ("PSM",  "coep",               "COEP",          "CO Postings (empty)"),
    ("PSM",  "rpsco",              "RPSCO",         "PS Cost Plan (empty)"),
    ("PSM",  "jest",               "JEST",          "Object Status (empty)"),
    # ── p01_gold_master_data.db (CTS + TADIR enrichment — loaded 2026-03-14) ─
    ("CTS",  "tadir_enrichment",   "TADIR+DD02T",   "All ABAP objects with package+desc"),
    ("CTS",  "volume_anchors",     "FMIFIIT/FMBDT/FMAVCT", "Row counts by year/fund area"),
    ("CTS",  "cts_transports",     "E070",          "Transport orders 2017-2026"),
    ("CTS",  "cts_objects",        "E071",          "Transport objects 2017-2026"),
]


# ─────────────────────────────────────────────────────────────────────────────
# CHECKPOINT READER
# ─────────────────────────────────────────────────────────────────────────────

def count_checkpoint_rows(tbl_name, chk_dir, file_pattern):
    """Count total rows across all checkpoint files for a table."""
    total = 0
    periods_done = 0
    periods_expected = 36  # 3 years × 12 months

    if file_pattern == "ESLL_all.json":
        # Single file pattern
        fp = os.path.join(chk_dir, "ESLL_all.json")
        periods_expected = 1
        if os.path.exists(fp):
            try:
                with open(fp, encoding="utf-8") as f:
                    d = json.load(f)
                total = d.get("meta", {}).get("row_count", len(d.get("rows", [])))
                periods_done = 1
            except Exception:
                pass
        return total, periods_done, periods_expected

    for year in YEARS:
        for month in range(1, 13):
            monat = f"{month:02d}"
            fname = file_pattern.replace("{y}", str(year)).replace("{m}", monat)
            fp = os.path.join(chk_dir, fname)
            if os.path.exists(fp):
                try:
                    with open(fp, encoding="utf-8") as f:
                        d = json.load(f)
                    total += d.get("meta", {}).get("row_count", len(d.get("rows", [])))
                    periods_done += 1
                except Exception:
                    pass

    return total, periods_done, periods_expected


def get_sqlite_count(conn, table_name):
    """Get row count from SQLite table, 0 if table doesn't exist."""
    try:
        row = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()
        return row[0] if row else 0
    except Exception:
        return -1   # Table doesn't exist


# ─────────────────────────────────────────────────────────────────────────────
# STATUS REPORT
# ─────────────────────────────────────────────────────────────────────────────

def print_status():
    SEP = "=" * 92
    SEC = "-" * 90
    print(f"\n{SEP}")
    print(f"  UNESCO P01 -- SAP EXTRACTION vs SQLITE COMPARISON REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if os.path.exists(DB_PATH):
        print(f"  SQLite DB: {os.path.basename(DB_PATH)}  ({os.path.getsize(DB_PATH)//1024:,} KB)")
    print(f"{SEP}")

    if not os.path.exists(DB_PATH):
        print(f"  WARNING: DB not found: {DB_PATH}")
        return

    db = sqlite3.connect(DB_PATH)

    # Open TADIR db separately
    tadir_conn = None
    if os.path.exists(TADIR_DB):
        tadir_conn = sqlite3.connect(TADIR_DB)

    # ── SECTION 1: PSM tables already in SQLite ──
    print(f"\n  SECTION 1: PSM FINANCE TABLES (previously extracted)")
    print(f"  {'-'*12} {'-'*20} {'-'*35} {'-'*10}  {'-'*18}")
    print(f"  {'SAP Table':<12} {'SQLite Table':<20} {'Description':<35} {'Rows':>10}  {'Status'}")
    print(f"  {'-'*12} {'-'*20} {'-'*35} {'-'*10}  {'-'*18}")

    psm_total = 0
    last_db_label = None
    for db_label, sqlite_tbl, sap_tbl, desc in EXISTING_SQLITE_TABLES:
        if db_label != last_db_label:
            lbl = f"[{db_label}]"
            print(f"  {lbl}")
            last_db_label = db_label

        if db_label == "TADIR":
            use_conn = tadir_conn
        else:
            use_conn = db

        if use_conn is None:
            cnt_str, status = "DB missing", "MISSING"
        else:
            cnt = get_sqlite_count(use_conn, sqlite_tbl)
            psm_total += max(cnt, 0)
            if cnt > 0:
                status = "OK"
            elif cnt == 0:
                status = "empty"
            else:
                status = "not exist"
            cnt_str = f"{cnt:,}" if cnt >= 0 else "NOT EXIST"

        print(f"  {sap_tbl:<12} {sqlite_tbl:<20} {desc:<35} {cnt_str:>10}  {status}")

    print(f"  {SEC}")
    print(f"  {'':12} {'PSM TOTAL':<20} {'':<35} {psm_total:>10,}")

    # ── SECTION 2: FI/MM tables (overnight extraction) ──
    print(f"\n  SECTION 2: FI / MM TABLES (overnight extraction 2024-2026)")
    print(f"  {'P#':<4} {'SAP Table':<8} {'Description':<28} {'Checkpoint':>12} {'SQLite':>12} {'Coverage':>14}  {'Status'}")
    print(f"  {'-'*4} {'-'*8} {'-'*28} {'-'*12} {'-'*12} {'-'*14}  {'-'*18}")

    total_chk, total_sqlite = 0, 0

    for tbl_name, chk_dir, file_pat, sqlite_tbl, priority, desc in TABLE_REGISTRY:
        chk_rows, done, expected = count_checkpoint_rows(tbl_name, chk_dir, file_pat)
        sql_rows = get_sqlite_count(db, sqlite_tbl)

        total_chk    += chk_rows
        total_sqlite += max(sql_rows, 0)

        if sql_rows < 0:
            coverage = "not loaded"
            status   = "pending"
        elif sql_rows == 0 and chk_rows == 0:
            coverage = f"0/{expected} periods"
            status   = "not extracted"
        elif sql_rows == 0 and chk_rows > 0:
            coverage = f"{done}/{expected} periods"
            status   = "ready to load"
        elif chk_rows > 0 and sql_rows >= chk_rows:
            coverage = f"{done}/{expected} periods"
            status   = "COMPLETE"
        elif chk_rows > 0:
            pct = int(sql_rows / chk_rows * 100)
            coverage = f"{done}/{expected} periods"
            status   = f"partial ({pct}%)"
        else:
            coverage = "?"
            status   = "no checkpoint"

        chk_str = f"{chk_rows:,}" if chk_rows > 0 else "--"
        sql_str = f"{sql_rows:,}" if sql_rows >= 0 else "NOT EXIST"

        print(f"  [{priority}]  {tbl_name:<8} {desc:<28} {chk_str:>12} {sql_str:>12} {coverage:>14}   {status}")

    print(f"  {SEC}")
    print(f"  {'':4} {'FI/MM TOTAL':<8} {'':<28} {total_chk:>12,} {total_sqlite:>12,}")

    grand_total = psm_total + total_sqlite
    print(f"\n  {SEC}")
    print(f"  GRAND TOTAL (ALL TABLES IN SQLITE): {grand_total:,} rows")
    print(f"  {SEC}")

    db.close()
    if tadir_conn:
        tadir_conn.close()

    print(f"\n  LOAD ORDER (run --load <TABLE> to import checkpoints into SQLite):")
    for tbl_name, _, _, _, priority, desc in sorted(TABLE_REGISTRY, key=lambda x: x[4]):
        print(f"  [{priority}] python extraction_status.py --load {tbl_name:<6}  # {desc}")
    print(f"{SEP}\n")




# ─────────────────────────────────────────────────────────────────────────────
# LOADER
# ─────────────────────────────────────────────────────────────────────────────

def infer_sqlite_schema(sample_rows, table_name):
    """Infer column names and types from sample rows."""
    if not sample_rows:
        return None, None
    cols = list(sample_rows[0].keys())
    # All columns as TEXT — safe for SAP data (amounts, dates all as strings initially)
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    return cols, col_defs


def load_table_into_sqlite(tbl_name, chk_dir, file_pat, sqlite_tbl, clear_first=False):
    """Load all checkpoint files for a table into SQLite."""
    label = f"[{tbl_name}→SQLite]"

    if not os.path.exists(DB_PATH):
        print(f"  {label} ERROR: DB not found: {DB_PATH}")
        return

    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")

    existing_count = get_sqlite_count(db, sqlite_tbl)

    if clear_first and existing_count >= 0:
        print(f"  {label} Dropping existing table '{sqlite_tbl}' ({existing_count:,} rows)...")
        db.execute(f'DROP TABLE IF EXISTS "{sqlite_tbl}"')
        db.commit()
        existing_count = -1

    if existing_count > 0:
        print(f"  {label} Table '{sqlite_tbl}' already has {existing_count:,} rows.")
        ans = input(f"  {label} Continue and APPEND more rows? [y/N]: ").strip().lower()
        if ans != "y":
            print(f"  {label} Skipped (use --clear {tbl_name} to drop and reload).")
            db.close()
            return

    # Collect all checkpoint files
    checkpoint_files = []
    if file_pat == "ESLL_all.json":
        fp = os.path.join(chk_dir, "ESLL_all.json")
        if os.path.exists(fp):
            checkpoint_files.append(fp)
    else:
        for year in YEARS:
            for month in range(1, 13):
                monat = f"{month:02d}"
                fname = file_pat.replace("{y}", str(year)).replace("{m}", monat)
                fp = os.path.join(chk_dir, fname)
                if os.path.exists(fp):
                    checkpoint_files.append(fp)

    if not checkpoint_files:
        print(f"  {label} No checkpoint files found in {chk_dir}. Run extraction first.")
        db.close()
        return

    print(f"  {label} Loading {len(checkpoint_files)} checkpoint files into '{sqlite_tbl}'...")
    total_inserted = 0
    table_created  = existing_count >= 0   # Already exists or was just dropped
    t_start = datetime.now()

    for i, fp in enumerate(checkpoint_files):
        fname = os.path.basename(fp)
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
            rows = data.get("rows", [])
            if not rows:
                print(f"  {label}   [{i+1}/{len(checkpoint_files)}] {fname}: 0 rows — skip")
                continue

            cols, col_defs = infer_sqlite_schema(rows, tbl_name)
            if not cols:
                continue

            # Create table on first non-empty file
            if not table_created:
                db.execute(f'CREATE TABLE IF NOT EXISTS "{sqlite_tbl}" ({col_defs})')
                db.execute(f'CREATE INDEX IF NOT EXISTS "idx_{sqlite_tbl}_year" ON "{sqlite_tbl}" ("GJAHR")')
                db.commit()
                table_created = True
                print(f"  {label} Created table '{sqlite_tbl}' with {len(cols)} columns.")

            # Insert in batches of 1000
            placeholders = ", ".join("?" for _ in cols)
            col_list     = ", ".join(f'"{c}"' for c in cols)
            insert_sql   = f'INSERT INTO "{sqlite_tbl}" ({col_list}) VALUES ({placeholders})'
            batch = [[r.get(c, "") for c in cols] for r in rows]

            BATCH_SIZE = 1000
            for b_start in range(0, len(batch), BATCH_SIZE):
                db.executemany(insert_sql, batch[b_start : b_start + BATCH_SIZE])
            db.commit()

            total_inserted += len(rows)
            print(f"  {label}   [{i+1}/{len(checkpoint_files)}] {fname}: +{len(rows):,} rows  (total: {total_inserted:,})")

        except Exception as e:
            print(f"  {label}   ERROR loading {fname}: {e}")

    elapsed = (datetime.now() - t_start).total_seconds()
    print(f"\n  {label} DONE. {total_inserted:,} rows loaded in {elapsed:.0f}s.")

    # Verify final count
    final_count = get_sqlite_count(db, sqlite_tbl)
    print(f"  {label} SQLite count now: {final_count:,}")
    db.close()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

TABLE_MAP = {r[0]: r for r in TABLE_REGISTRY}   # tbl_name → full registry entry

def main():
    parser = argparse.ArgumentParser(description="SAP Extraction Status + SQLite Loader")
    parser.add_argument("--load",  type=str, default=None,
                        help="Load table into SQLite: BKPF, EKKO, EKPO, EKBE, ESSR, ESLL, BSEG, or 'all'")
    parser.add_argument("--clear", type=str, default=None,
                        help="Drop and recreate this SQLite table before loading: BKPF, EKKO, ...")
    parser.add_argument("--status-only", action="store_true",
                        help="Print status report only (no loading)")
    args = parser.parse_args()

    # Always show status first
    print_status()

    if args.status_only or (not args.load and not args.clear):
        return

    # --- CLEAR ---------------------------------------------------------------
    if args.clear:
        tbl = args.clear.upper()
        if tbl not in TABLE_MAP:
            print(f"  ERROR: Unknown table '{tbl}'. Valid: {list(TABLE_MAP.keys())}")
            sys.exit(1)
        _, chk_dir, file_pat, sqlite_tbl, _, desc = TABLE_MAP[tbl]
        print(f"\n  [CLEAR] Dropping '{sqlite_tbl}' from SQLite and reloading '{tbl}'...")
        load_table_into_sqlite(tbl, chk_dir, file_pat, sqlite_tbl, clear_first=True)
        return

    # --- LOAD ----------------------------------------------------------------
    if args.load:
        if args.load.upper() == "ALL":
            print(f"\n  Loading ALL tables in priority order...\n")
            for tbl_name, chk_dir, file_pat, sqlite_tbl, priority, desc in sorted(TABLE_REGISTRY, key=lambda x: x[4]):
                print(f"\n  {'─'*60}")
                print(f"  PRIORITY {priority}: {tbl_name} — {desc}")
                print(f"  {'─'*60}")
                load_table_into_sqlite(tbl_name, chk_dir, file_pat, sqlite_tbl)
        else:
            tbl = args.load.upper()
            if tbl not in TABLE_MAP:
                print(f"  ERROR: Unknown table '{tbl}'. Valid: {list(TABLE_MAP.keys())} or 'all'")
                sys.exit(1)
            _, chk_dir, file_pat, sqlite_tbl, _, desc = TABLE_MAP[tbl]
            print(f"\n  Loading {tbl} ({desc}) into SQLite...")
            load_table_into_sqlite(tbl, chk_dir, file_pat, sqlite_tbl)

    # Show updated status after loading
    print(f"\n  {'═'*40}")
    print(f"  UPDATED STATUS after load:")
    print_status()


if __name__ == "__main__":
    main()
