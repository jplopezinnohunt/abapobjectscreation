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
  1. BKPF   -- FI Document Headers       (small, key table for analysis)
  2. EKKO   -- PO Headers                (small, fast)
  3. EKPO   -- PO Line Items             (medium)
  4. EKBE   -- PO History / GR / SES     (medium -- links PO to entry sheets)
  5. ESSR   -- Entry Sheet Headers       (small)
  6. ESLL   -- Entry Sheet Lines         (depends on ESSR keys)
  7. BSEG   -- FI Line Items             (LARGEST -- load last, takes longest)

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

# -----------------------------------------------------------------------------
# PATHS
# -----------------------------------------------------------------------------
BASE_DIR   = os.path.dirname(__file__)
DATA_DIR   = os.path.join(BASE_DIR, "extracted_data")
DB_PATH    = os.path.join(BASE_DIR, "..", "..", "Zagentexecution", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
DB_PATH    = os.path.normpath(DB_PATH)

YEARS = [2024, 2025, 2026]

# -----------------------------------------------------------------------------
# TABLE REGISTRY
# Priority order: 1=highest  | type: period=monthly checkpoints, single=one file
# -----------------------------------------------------------------------------
TABLE_REGISTRY = [
    # (table_name, checkpoint_dir, file_pattern, sqlite_table, priority, note)
    # --- FI Pipeline ---
    ("BKPF", os.path.join(DATA_DIR, "BKPF"), "BKPF_{y}_{m}.json", "bkpf",  1, "FI Doc Headers"),
    ("EKKO", os.path.join(DATA_DIR, "EKKO"), "EKKO_{y}_{m}.json", "ekko",  2, "PO Headers"),
    ("EKPO", os.path.join(DATA_DIR, "EKPO"), "EKPO_{y}_{m}.json", "ekpo",  3, "PO Lines"),
    ("EKBE", os.path.join(DATA_DIR, "EKBE"), "EKBE_{y}_{m}.json", "ekbe",  4, "PO History/GR/SES"),
    ("ESSR", os.path.join(DATA_DIR, "ESSR"), "ESSR_{y}_{m}.json", "essr",  5, "Entry Sheet Headers"),
    ("ESLL", os.path.join(DATA_DIR, "ESLL"), "ESLL_all.json",     "esll",  6, "Entry Sheet Lines (single file)"),
    ("BSEG", os.path.join(DATA_DIR, "BSEG"), "BSEG_{y}_{m}.json", "bseg",  7, "FI Line Items (LARGEST)"),
    # --- Celonis BSEG Replacement (6 transparent tables) ---
    ("BSIK", os.path.join(DATA_DIR, "BSIK"), "BSIK_{y}_{m}.json", "bsik",  7, "Vendor Open Items"),
    ("BSAK", os.path.join(DATA_DIR, "BSAK"), "BSAK_{y}_{m}.json", "bsak",  7, "Vendor Cleared Items"),
    ("BSID", os.path.join(DATA_DIR, "BSID"), "BSID_{y}_{m}.json", "bsid",  7, "Customer Open Items"),
    ("BSAD", os.path.join(DATA_DIR, "BSAD"), "BSAD_{y}_{m}.json", "bsad",  7, "Customer Cleared Items"),
    ("BSIS", os.path.join(DATA_DIR, "BSIS"), "BSIS_{y}_{m}.json", "bsis",  7, "GL Open Items"),
    ("BSAS", os.path.join(DATA_DIR, "BSAS"), "BSAS_{y}_{m}.json", "bsas",  7, "GL Cleared Items"),
    # --- CDHDR Pipeline ---
    ("CDHDR", os.path.join(DATA_DIR, "CDHDR"), "CDHDR_{y}_{m}.json", "cdhdr",  8, "Change Doc Headers"),
    ("CDPOS", os.path.join(DATA_DIR, "CDPOS"), "CDPOS_all.json",     "cdpos",  9, "Change Doc Items (single file)"),
    # --- P2P Complement ---
    ("EBAN", os.path.join(DATA_DIR, "EBAN"), "EBAN_{y}_{m}.json", "eban", 10, "Purchase Requisitions"),
    ("RBKP", os.path.join(DATA_DIR, "RBKP"), "RBKP_{y}_{m}.json", "rbkp", 11, "Invoice Doc Headers"),
    ("RSEG", os.path.join(DATA_DIR, "RSEG"), "RSEG_{y}_{m}.json", "rseg", 12, "Invoice Doc Lines"),
    # --- B2R Complement ---
    ("FMIOI", os.path.join(DATA_DIR, "FMIOI"), "FMIOI_{y}_{m}.json", "fmioi", 13, "FM Commitments"),
    ("FMBH",  os.path.join(DATA_DIR, "FMBH"),  "FMBH_{y}_{m}.json",  "fmbh",  14, "FM Budget Headers"),
    ("FMBL",  os.path.join(DATA_DIR, "FMBL"),  "FMBL_{y}_{m}.json",  "fmbl",  15, "FM Budget Lines"),
]

# Existing PSM tables already in SQLite (for status display)
EXISTING_SQLITE_TABLES = [
    ("funds",              "Funds Master"),
    ("fund_centers",       "Fund Centers"),
    ("proj",               "Projects"),
    ("prps",               "WBS Elements"),
    ("movements_summary",  "FM Movements Summary"),
    ("fmbdt_summary",      "FM Budget Summary"),
    ("fmavct_summary",     "FM Availability"),
    ("fmifiit_full",       "FM FI Integration"),
    ("ytfm_wrttp_gr",      "WRTTP Groups"),
    ("cts_transports",     "CTS Transports"),
    ("cts_objects",        "CTS Transport Objects"),
    ("tadir_enrichment",   "TADIR Enrichment"),
    ("ytfm_fund_cpl",      "Fund Couples"),
    ("volume_anchors",     "Volume Anchors"),
]

# -----------------------------------------------------------------------------
# INDEX DEFINITIONS -- created after loading for query performance
# Key: sqlite_table -> list of (index_name, column(s))
# -----------------------------------------------------------------------------
TABLE_INDEXES = {
    "bkpf": [
        ("idx_bkpf_belnr_gjahr", "BELNR, GJAHR"),
        ("idx_bkpf_budat", "BUDAT"),
        ("idx_bkpf_tcode", "TCODE"),
        ("idx_bkpf_awkey", "AWKEY"),
    ],
    "bseg": [
        ("idx_bseg_belnr_gjahr", "BELNR, GJAHR"),
        ("idx_bseg_budat", "BUDAT"),
        ("idx_bseg_hkont", "HKONT"),
        ("idx_bseg_ebeln", "EBELN"),
        ("idx_bseg_kostl", "KOSTL"),
    ],
    "ekko": [
        ("idx_ekko_ebeln", "EBELN"),
        ("idx_ekko_bedat", "BEDAT"),
        ("idx_ekko_lifnr", "LIFNR"),
    ],
    "ekpo": [
        ("idx_ekpo_ebeln", "EBELN"),
        ("idx_ekpo_ebeln_ebelp", "EBELN, EBELP"),
    ],
    "ekbe": [
        ("idx_ekbe_ebeln", "EBELN"),
        ("idx_ekbe_ebeln_ebelp", "EBELN, EBELP"),
        ("idx_ekbe_budat", "BUDAT"),
        ("idx_ekbe_belnr", "BELNR"),
    ],
    "essr": [
        ("idx_essr_lblni", "LBLNI"),
        ("idx_essr_ebeln", "EBELN"),
    ],
    "esll": [
        ("idx_esll_packno", "PACKNO"),
    ],
    "bsik": [
        ("idx_bsik_belnr_gjahr", "BELNR, GJAHR"),
        ("idx_bsik_lifnr", "LIFNR"),
        ("idx_bsik_budat", "BUDAT"),
    ],
    "bsak": [
        ("idx_bsak_belnr_gjahr", "BELNR, GJAHR"),
        ("idx_bsak_lifnr", "LIFNR"),
        ("idx_bsak_budat", "BUDAT"),
        ("idx_bsak_augdt", "AUGDT"),
    ],
    "bsid": [
        ("idx_bsid_belnr_gjahr", "BELNR, GJAHR"),
        ("idx_bsid_kunnr", "KUNNR"),
        ("idx_bsid_budat", "BUDAT"),
    ],
    "bsad": [
        ("idx_bsad_belnr_gjahr", "BELNR, GJAHR"),
        ("idx_bsad_kunnr", "KUNNR"),
        ("idx_bsad_budat", "BUDAT"),
        ("idx_bsad_augdt", "AUGDT"),
    ],
    "bsis": [
        ("idx_bsis_belnr_gjahr", "BELNR, GJAHR"),
        ("idx_bsis_hkont", "HKONT"),
        ("idx_bsis_budat", "BUDAT"),
    ],
    "bsas": [
        ("idx_bsas_belnr_gjahr", "BELNR, GJAHR"),
        ("idx_bsas_hkont", "HKONT"),
        ("idx_bsas_budat", "BUDAT"),
        ("idx_bsas_augdt", "AUGDT"),
    ],
    "cdhdr": [
        ("idx_cdhdr_objectclas", "OBJECTCLAS"),
        ("idx_cdhdr_changenr", "CHANGENR"),
        ("idx_cdhdr_udate", "UDATE"),
        ("idx_cdhdr_tcode", "TCODE"),
        ("idx_cdhdr_username", "USERNAME"),
    ],
    "cdpos": [
        ("idx_cdpos_changenr", "CHANGENR"),
        ("idx_cdpos_objectclas", "OBJECTCLAS"),
        ("idx_cdpos_tabname", "TABNAME"),
    ],
    "eban": [
        ("idx_eban_banfn", "BANFN"),
        ("idx_eban_erdat", "ERDAT"),
    ],
    "rbkp": [
        ("idx_rbkp_belnr_gjahr", "BELNR, GJAHR"),
        ("idx_rbkp_budat", "BUDAT"),
        ("idx_rbkp_lifnr", "LIFNR"),
    ],
    "rseg": [
        ("idx_rseg_belnr_gjahr", "BELNR, GJAHR"),
        ("idx_rseg_ebeln", "EBELN"),
    ],
    "fmioi": [
        ("idx_fmioi_fonds", "FONDS"),
        ("idx_fmioi_fmbelnr", "FMBELNR"),
        ("idx_fmioi_wrttp", "WRTTP"),
    ],
    "fmbh": [
        ("idx_fmbh_docnr_gjahr", "DOCNR, GJAHR"),
        ("idx_fmbh_erdat", "ERDAT"),
    ],
    "fmbl": [
        ("idx_fmbl_docnr_gjahr", "DOCNR, GJAHR"),
        ("idx_fmbl_fonds", "FONDS"),
    ],
}


# -----------------------------------------------------------------------------
# CHECKPOINT READER
# -----------------------------------------------------------------------------

def count_checkpoint_rows(tbl_name, chk_dir, file_pattern):
    """Count total rows across all checkpoint files for a table."""
    total = 0
    periods_done = 0
    periods_expected = 36  # 3 years × 12 months

    if "_all.json" in file_pattern:
        # Single file pattern (ESLL_all.json, CDPOS_all.json, etc.)
        fp = os.path.join(chk_dir, file_pattern)
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


# -----------------------------------------------------------------------------
# STATUS REPORT
# -----------------------------------------------------------------------------

def print_status():
    print(f"\n{'='*85}")
    print(f"  SAP EXTRACTION <-> SQLITE COMPARISON REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  SQLite DB: {os.path.basename(DB_PATH)}  ({os.path.getsize(DB_PATH)//1024:,} KB)")
    print(f"{'='*85}")

    if not os.path.exists(DB_PATH):
        print(f"  !! DB not found: {DB_PATH}")
        return

    db = sqlite3.connect(DB_PATH)

    # -- New FI/MM tables (from overnight extraction) --
    print(f"\n  {'P#':<4} {'Table':<8} {'Description':<28} {'Checkpoint':>12} {'SQLite':>12} {'Coverage':>10} {'Status'}")
    print(f"  {'-'*4} {'-'*8} {'-'*28} {'-'*12} {'-'*12} {'-'*10} {'-'*18}")

    total_chk, total_sqlite, total_expected = 0, 0, 0

    for tbl_name, chk_dir, file_pat, sqlite_tbl, priority, desc in TABLE_REGISTRY:
        chk_rows, done, expected = count_checkpoint_rows(tbl_name, chk_dir, file_pat)
        sql_rows = get_sqlite_count(db, sqlite_tbl)

        total_chk    += chk_rows
        total_sqlite += max(sql_rows, 0)
        total_expected += expected

        pct_chk = f"{done}/{expected}"
        if sql_rows < 0:
            coverage = "NOT LOADED"
            status   = "[ ] Pending"
        elif sql_rows == 0 and chk_rows == 0:
            coverage = "0%"
            status   = "[.] No data yet"
        elif sql_rows == 0:
            coverage = "0%"
            status   = "-> Ready to load"
        elif chk_rows > 0 and sql_rows >= chk_rows:
            pct = 100
            coverage = "100%"
            status   = "[OK] Complete"
        elif chk_rows > 0:
            pct = int(sql_rows / chk_rows * 100)
            coverage = f"{pct}%"
            status   = f"[~] Partial ({pct}%)"
        else:
            coverage = "?"
            status   = "[ ] No checkpoint"

        chk_str = f"{chk_rows:,}" if chk_rows > 0 else "--"
        sql_str = f"{sql_rows:,}" if sql_rows >= 0 else "NOT EXIST"

        print(f"  [{priority}]  {tbl_name:<8} {desc:<28} {chk_str:>12} {sql_str:>12} {coverage:>10}  {status}")

    print(f"  {'-'*83}")
    print(f"  {'':4} {'TOTAL':<8} {'FI + MM tables':<28} {total_chk:>12,} {total_sqlite:>12,}")

    # -- Existing PSM tables --
    print(f"\n  {'-'*83}")
    print(f"  EXISTING PSM TABLES (already in SQLite):")
    print(f"  {'-'*83}")
    for sqlite_tbl, desc in EXISTING_SQLITE_TABLES:
        cnt = get_sqlite_count(db, sqlite_tbl)
        status = "[OK] Populated" if cnt > 0 else "[ ] Empty"
        cnt_str = f"{cnt:,}" if cnt >= 0 else "NOT EXIST"
        print(f"  {'':4} {sqlite_tbl:<20} {desc:<30} {cnt_str:>10}  {status}")

    db.close()
    print(f"\n{'='*85}")
    print(f"  NEXT LOAD ORDER (run: python extraction_status.py --load <TABLE>):")
    for tbl_name, _, _, _, priority, desc in sorted(TABLE_REGISTRY, key=lambda x: x[4]):
        print(f"  [{priority}] python extraction_status.py --load {tbl_name:<6}  # {desc}")
    print(f"{'='*85}\n")


# -----------------------------------------------------------------------------
# LOADER
# -----------------------------------------------------------------------------

def infer_sqlite_schema(sample_rows, table_name):
    """Infer column names and types from sample rows."""
    if not sample_rows:
        return None, None
    cols = list(sample_rows[0].keys())
    # All columns as TEXT -- safe for SAP data (amounts, dates all as strings initially)
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    return cols, col_defs


def load_table_into_sqlite(tbl_name, chk_dir, file_pat, sqlite_tbl, clear_first=False):
    """Load all checkpoint files for a table into SQLite."""
    label = f"[{tbl_name}->SQLite]"

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
    if "_all.json" in file_pat:
        fp = os.path.join(chk_dir, file_pat)
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
                print(f"  {label}   [{i+1}/{len(checkpoint_files)}] {fname}: 0 rows -- skip")
                continue

            cols, col_defs = infer_sqlite_schema(rows, tbl_name)
            if not cols:
                continue

            # Create table on first non-empty file
            if not table_created:
                db.execute(f'CREATE TABLE IF NOT EXISTS "{sqlite_tbl}" ({col_defs})')
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

    # Create indexes for query performance
    if sqlite_tbl in TABLE_INDEXES and total_inserted > 0:
        print(f"  {label} Creating indexes...")
        for idx_name, idx_cols in TABLE_INDEXES[sqlite_tbl]:
            try:
                db.execute(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{sqlite_tbl}" ({idx_cols})')
                print(f"  {label}   + {idx_name} ({idx_cols})")
            except Exception as e:
                print(f"  {label}   ! {idx_name} failed: {e}")
        db.commit()

    # Verify final count
    final_count = get_sqlite_count(db, sqlite_tbl)
    print(f"  {label} SQLite count now: {final_count:,}")
    db.close()


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

TABLE_MAP = {r[0]: r for r in TABLE_REGISTRY}   # tbl_name -> full registry entry

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
                print(f"\n  {'-'*60}")
                print(f"  PRIORITY {priority}: {tbl_name} -- {desc}")
                print(f"  {'-'*60}")
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
    print(f"\n  {'='*40}")
    print(f"  UPDATED STATUS after load:")
    print_status()


if __name__ == "__main__":
    main()
