"""
enrich_bsis_bsas_fields.py
==========================
Enriches existing BSIS/BSAS tables in Gold DB with missing fields.

Instead of re-extracting the full 3.7M rows, uses the existing keys
(BUKRS+BELNR+GJAHR+BUZEI) filtered by year/period to fetch ONLY the
missing columns from SAP, then patches them into the Gold DB.

Missing fields to add:
  KOSTL, AUFNR, PRCTR, FKBER, PS_PSP_PNR,
  SGTXT, EBELN, EBELP, MWSKZ, AUGDT, AUGBL, ZFBDT, ZTERM

Usage:
    python enrich_bsis_bsas_fields.py                   # All tables, all years
    python enrich_bsis_bsas_fields.py --table BSIS      # Only BSIS
    python enrich_bsis_bsas_fields.py --year 2025       # Only 2025
    python enrich_bsis_bsas_fields.py --dry-run         # Show plan, don't extract
"""

import os
import sys
import json
import time
import sqlite3
import argparse
from datetime import datetime

# -----------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOLD_DB  = os.path.join(BASE_DIR, "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
CHECKPOINT_DIR = os.path.join(BASE_DIR, "extracted_data", "ENRICH_BSIS_BSAS")
YEARS    = [2024, 2025, 2026]
BATCH_SIZE = 5000
THROTTLE   = 3.0

# Fields to add (missing from current 16-field extraction)
NEW_FIELDS = [
    "KOSTL",       # Cost Center
    "AUFNR",       # Internal Order
    "PRCTR",       # Profit Center
    "FKBER",       # Functional Area
    "PS_PSP_PNR",  # WBS Element (internal key -> JOIN with PRPS.PSPNR)
    "SGTXT",       # Item Text
    "EBELN",       # PO Number
    "EBELP",       # PO Item
    "MWSKZ",       # Tax Code
    "AUGDT",       # Clearing Date
    "AUGBL",       # Clearing Document
    "ZFBDT",       # Baseline Date
    "ZTERM",       # Payment Terms
]

# Keys we use to match back (already in Gold DB)
KEY_FIELDS = ["BUKRS", "BELNR", "GJAHR", "BUZEI"]

# What we send to SAP: keys + new fields
SAP_FIELDS = KEY_FIELDS + NEW_FIELDS

# Tables to enrich
TABLES = {
    "BSIS": "BUDAT",  # GL open items, filter by posting date
    "BSAS": "BUDAT",  # GL cleared items, filter by posting date
}


# -----------------------------------------------------------------------
# RFC CONNECTION
# -----------------------------------------------------------------------
sys.path.insert(0, BASE_DIR)
from rfc_helpers import get_connection, rfc_read_paginated


# -----------------------------------------------------------------------
# SQLITE HELPERS
# -----------------------------------------------------------------------

def ensure_columns(db_path, table, new_cols):
    """Add missing columns to an existing SQLite table."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    existing = {r[1].upper() for r in cur.fetchall()}

    added = []
    for col in new_cols:
        if col.upper() not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT DEFAULT ''")
            added.append(col)

    conn.commit()
    conn.close()
    return added


def get_period_keys(db_path, table, year, month):
    """Get distinct document keys for a specific year/period from Gold DB."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    date_from = f"{year}{month:02d}01"
    if month < 12:
        date_to = f"{year}{month+1:02d}01"
        where = f"BUDAT >= '{date_from}' AND BUDAT < '{date_to}'"
    else:
        where = f"BUDAT >= '{date_from}' AND BUDAT <= '{year}1231'"

    cur.execute(f"""
        SELECT BUKRS, BELNR, GJAHR, BUZEI
        FROM {table}
        WHERE {where}
    """)
    keys = cur.fetchall()
    conn.close()
    return keys, where


def update_rows(db_path, table, rows):
    """Update Gold DB rows with enriched fields."""
    if not rows:
        return 0

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    updated = 0
    for row in rows:
        sets = []
        vals = []
        for field in NEW_FIELDS:
            val = row.get(field, "")
            sets.append(f"{field} = ?")
            vals.append(val)

        vals.extend([row["BUKRS"], row["BELNR"], row["GJAHR"], row["BUZEI"]])

        cur.execute(f"""
            UPDATE {table}
            SET {', '.join(sets)}
            WHERE BUKRS = ? AND BELNR = ? AND GJAHR = ? AND BUZEI = ?
        """, vals)
        updated += cur.rowcount

    conn.commit()
    conn.close()
    return updated


# -----------------------------------------------------------------------
# ENRICHMENT LOGIC
# -----------------------------------------------------------------------

def enrich_table(table, date_field, years, dry_run=False):
    """Enrich a single table by year/period."""
    label = f"[{table}]"
    print(f"\n  {label} Starting enrichment...")

    # Step 1: Add missing columns to Gold DB
    added = ensure_columns(GOLD_DB, table.lower(), NEW_FIELDS)
    if added:
        print(f"  {label} Added {len(added)} new columns: {', '.join(added)}")
    else:
        print(f"  {label} All columns already exist")

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    total_updated = 0
    total_sap_rows = 0

    if dry_run:
        for year in years:
            for month in range(1, 13):
                keys, where_clause = get_period_keys(GOLD_DB, table.lower(), year, month)
                if keys:
                    print(f"  {label} {year}/{month:02d}: {len(keys):,} rows to enrich")
                    total_updated += len(keys)
        print(f"  {label} DRY RUN: {total_updated:,} total rows would be enriched")
        return

    # Step 2: Connect to SAP
    print(f"  {label} Connecting to P01...")
    sap_conn = get_connection("P01")
    print(f"  {label} Connected.")

    t_start = time.time()

    for year in years:
        for month in range(1, 13):
            monat = f"{month:02d}"
            checkpoint = os.path.join(CHECKPOINT_DIR, f"{table}_{year}_{monat}.json")

            # Skip if already done
            if os.path.exists(checkpoint):
                with open(checkpoint, encoding="utf-8") as f:
                    meta = json.load(f).get("meta", {})
                print(f"  {label} SKIP {year}/{monat} [{meta.get('enriched', 0)} rows — already done]")
                total_updated += meta.get("enriched", 0)
                continue

            # Get keys for this period from Gold DB
            keys, where_clause = get_period_keys(GOLD_DB, table.lower(), year, month)
            if not keys:
                print(f"  {label} {year}/{monat}: 0 rows — skip")
                # Save empty checkpoint
                _save_checkpoint(checkpoint, table, year, month, 0, 0, 0)
                continue

            print(f"  {label} {year}/{monat}: {len(keys):,} rows to enrich (where: {where_clause})")

            # Query SAP for missing fields, filtered by same date range
            t0 = time.time()
            try:
                sap_rows = rfc_read_paginated(
                    sap_conn, table, SAP_FIELDS, where_clause,
                    batch_size=BATCH_SIZE, throttle=THROTTLE
                )
            except Exception as e:
                print(f"  {label} ERROR {year}/{monat}: {e}")
                # Try to reconnect
                try:
                    sap_conn.close()
                except Exception:
                    pass
                try:
                    sap_conn = get_connection("P01")
                    print(f"  {label} Reconnected.")
                except Exception as ce:
                    print(f"  {label} Reconnect failed: {ce} — stopping")
                    break
                continue

            elapsed = time.time() - t0
            total_sap_rows += len(sap_rows)

            # Update Gold DB
            enriched = update_rows(GOLD_DB, table.lower(), sap_rows)
            total_updated += enriched

            print(f"  {label}   -> SAP returned {len(sap_rows):,} rows, updated {enriched:,} in Gold DB ({elapsed:.0f}s)")

            # Save checkpoint
            _save_checkpoint(checkpoint, table, year, month, len(keys), len(sap_rows), enriched)

            if THROTTLE > 0:
                time.sleep(THROTTLE)

    try:
        sap_conn.close()
    except Exception:
        pass

    elapsed_total = (time.time() - t_start) / 60
    print(f"\n  {label} COMPLETE. {total_updated:,} rows enriched, {total_sap_rows:,} from SAP, {elapsed_total:.1f} min")


def _save_checkpoint(path, table, year, month, db_rows, sap_rows, enriched):
    data = {
        "meta": {
            "table": table, "year": year, "month": month,
            "db_rows": db_rows, "sap_rows": sap_rows, "enriched": enriched,
            "timestamp": datetime.now().isoformat(),
        }
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# -----------------------------------------------------------------------
# REBUILD BSEG_UNION VIEW
# -----------------------------------------------------------------------

def rebuild_bseg_union():
    """Rebuild the bseg_union view with all available fields."""
    conn = sqlite3.connect(GOLD_DB)
    cur = conn.cursor()

    # Get current columns for each table
    table_cols = {}
    for tbl in ["bsis", "bsas", "bsik", "bsak", "bsid", "bsad"]:
        cur.execute(f"PRAGMA table_info({tbl})")
        table_cols[tbl] = [r[1] for r in cur.fetchall()]

    # Find common columns across all 6 tables
    common = set(table_cols["bsis"])
    for tbl in table_cols:
        common = common & set(table_cols[tbl])

    # Order: keys first, then alphabetical
    key_order = ["MANDT", "BUKRS", "BELNR", "GJAHR", "BUZEI", "BUDAT", "BLDAT",
                 "MONAT", "BSCHL", "HKONT", "SHKZG", "DMBTR", "DMBE2", "WRBTR", "WAERS", "GSBER"]
    ordered = [f for f in key_order if f in common]
    ordered += sorted(f for f in common if f not in ordered)

    # Add non-common fields with NULL fallback
    all_fields = set()
    for cols in table_cols.values():
        all_fields.update(cols)
    extra = sorted(all_fields - common)

    # Build UNION ALL
    selects = []
    for tbl in ["bsis", "bsas", "bsik", "bsak", "bsid", "bsad"]:
        cols = table_cols[tbl]
        parts = []
        for f in ordered + extra:
            if f in cols:
                parts.append(f"[{f}]")
            else:
                parts.append(f"'' as [{f}]")
        parts.append(f"'{tbl}' as source_table")
        selects.append(f"SELECT {', '.join(parts)} FROM [{tbl}]")

    view_sql = "CREATE VIEW bseg_union AS " + " UNION ALL ".join(selects)

    # Drop and recreate
    cur.execute("DROP VIEW IF EXISTS bseg_union")
    cur.execute(view_sql)
    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM bseg_union")
    total = cur.fetchone()[0]
    cur.execute("PRAGMA table_info(bseg_union)")
    ncols = len(cur.fetchall())
    conn.close()

    print(f"\n  [VIEW] bseg_union rebuilt: {ncols} columns, {total:,} rows")
    return ncols, total


# -----------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Enrich BSIS/BSAS with missing fields (KOSTL, PS_PSP_PNR, SGTXT, etc.)"
    )
    parser.add_argument("--table", type=str, default=None, help="BSIS or BSAS only")
    parser.add_argument("--year", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Show plan without extracting")
    parser.add_argument("--rebuild-view", action="store_true", help="Only rebuild bseg_union view")
    args = parser.parse_args()

    years = [args.year] if args.year else YEARS

    t_start = datetime.now()
    print(f"\n{'='*70}")
    print(f"  BSIS/BSAS Field Enrichment | P01 | {t_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Years={years}  New fields={len(NEW_FIELDS)}")
    print(f"  Fields: {', '.join(NEW_FIELDS)}")
    print(f"  Gold DB: {GOLD_DB}")
    print(f"{'='*70}")

    if args.rebuild_view:
        rebuild_bseg_union()
        return

    tables_to_run = {}
    if args.table:
        tbl = args.table.upper()
        if tbl in TABLES:
            tables_to_run[tbl] = TABLES[tbl]
        else:
            print(f"  ERROR: Unknown table {tbl}. Choose BSIS or BSAS.")
            return
    else:
        tables_to_run = TABLES

    for tbl, date_field in tables_to_run.items():
        enrich_table(tbl, date_field, years, dry_run=args.dry_run)

    # Rebuild the view after enrichment
    if not args.dry_run:
        rebuild_bseg_union()

    elapsed = (datetime.now() - t_start).total_seconds()
    print(f"\n  Done. Total: {elapsed/60:.1f} min")


if __name__ == "__main__":
    main()
