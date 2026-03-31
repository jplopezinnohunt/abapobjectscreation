"""
enrich_ekbe_budat.py
====================
Enriches EKBE table in Gold DB with missing fields in 2 passes
(RFC_READ_TABLE buffer limit = ~11 fields max for EKBE):

  Pass 1: BUDAT, DMBTR, WRBTR, WAERS   (keys + 4 = 11 fields)
  Pass 2: BLDAT, BEWTP, MENGE, MEINS    (keys + 4 = 11 fields)

Uses composite key: EBELN+EBELP+ZEKKN+VGABE+GJAHR+BELNR+BUZEI
Queries EKBE from P01 via RFC_READ_TABLE, one year at a time.

Usage:
    python enrich_ekbe_budat.py                # All years
    python enrich_ekbe_budat.py --year 2024    # Only 2024
    python enrich_ekbe_budat.py --dry-run      # Show plan
"""

import os
import sys
import time
import sqlite3
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOLD_DB  = os.path.join(BASE_DIR, "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
YEARS    = ["2024", "2025", "2026"]
BATCH_SIZE = 5000
THROTTLE   = 3.0

KEY_FIELDS = ["EBELN", "EBELP", "ZEKKN", "VGABE", "GJAHR", "BELNR", "BUZEI"]
PASS1_FIELDS = ["BUDAT", "DMBTR", "WRBTR", "WAERS"]
PASS2_FIELDS = ["BLDAT", "BEWTP", "MENGE"]  # MEINS causes auth/buffer error on P01
ALL_ENRICH = PASS1_FIELDS + PASS2_FIELDS

sys.path.insert(0, BASE_DIR)
from rfc_helpers import get_connection


def ensure_columns(db):
    cols = {r[1] for r in db.execute("PRAGMA table_info(EKBE)").fetchall()}
    for col in ALL_ENRICH:
        if col not in cols:
            db.execute(f"ALTER TABLE EKBE ADD COLUMN {col} TEXT DEFAULT ''")
            print(f"  Added column {col} to EKBE")
    db.commit()


def fetch_batch(conn_sap, gjahr, enrich_fields, offset=0, max_retries=3):
    """Fetch key + enrich fields from EKBE for a given year."""
    all_fields = KEY_FIELDS + enrich_fields
    fields_param = [{'FIELDNAME': f} for f in all_fields]
    options = [{'TEXT': f"GJAHR = '{str(gjahr).zfill(4)}'"}]

    for attempt in range(max_retries):
        try:
            result = conn_sap.call('RFC_READ_TABLE',
                QUERY_TABLE='EKBE',
                FIELDS=fields_param,
                OPTIONS=options,
                ROWCOUNT=BATCH_SIZE,
                ROWSKIPS=offset
            )
            return result
        except Exception as e:
            if 'TABLE_WITHOUT_DATA' in str(e):
                return None
            if attempt < max_retries - 1:
                print(f" [retry {attempt+1}]", end="", flush=True)
                conn_sap.connect()
                time.sleep(5)
            else:
                raise


def run_pass(conn_sap, db, year, enrich_fields, pass_name, dry_run=False):
    """Run one enrichment pass for a year."""
    row_count = db.execute(
        "SELECT COUNT(*) FROM EKBE WHERE GJAHR = ?", (str(year),)
    ).fetchone()[0]

    if row_count == 0:
        print(f"    {pass_name}: no rows, skip")
        return 0

    check_field = enrich_fields[0]
    already = db.execute(
        f"SELECT COUNT(*) FROM EKBE WHERE GJAHR = ? AND {check_field} != '' AND {check_field} IS NOT NULL",
        (str(year),)
    ).fetchone()[0]
    if already > row_count * 0.9:
        print(f"    {pass_name}: {already}/{row_count} already done, skip")
        return already

    if dry_run:
        print(f"    {pass_name}: {row_count} rows — would enrich")
        return 0

    print(f"    {pass_name}: {row_count} rows", end="", flush=True)
    t0 = time.time()

    offset = 0
    total_updated = 0
    batch_num = 0

    while True:
        result = fetch_batch(conn_sap, year, enrich_fields, offset)
        if result is None or not result['DATA']:
            break

        finfo = {f['FIELDNAME']: (int(f['OFFSET']), int(f['LENGTH'])) for f in result['FIELDS']}

        for row in result['DATA']:
            wa = row['WA']
            vals = {}
            for f in KEY_FIELDS + enrich_fields:
                o, l = finfo[f]
                vals[f] = wa[o:o+l].strip()

            set_clause = ", ".join(f"{f} = ?" for f in enrich_fields)
            where_clause = " AND ".join(f"{f} = ?" for f in KEY_FIELDS)
            params = [vals[f] for f in enrich_fields] + [vals[f] for f in KEY_FIELDS]
            db.execute(f"UPDATE EKBE SET {set_clause} WHERE {where_clause}", params)

        total_updated += len(result['DATA'])
        batch_num += 1

        if batch_num % 10 == 0:
            db.commit()
            print(f" [{total_updated}]", end="", flush=True)

        if len(result['DATA']) < BATCH_SIZE:
            break
        offset += BATCH_SIZE
        time.sleep(THROTTLE)

    db.commit()
    elapsed = time.time() - t0
    print(f" -> {total_updated} rows ({elapsed:.1f}s)")
    return total_updated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=str)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    years = [args.year] if args.year else YEARS

    db = sqlite3.connect(GOLD_DB)
    db.execute("PRAGMA journal_mode=WAL")
    ensure_columns(db)

    if args.dry_run:
        print("DRY RUN\n")

    conn_sap = get_connection("P01") if not args.dry_run else None

    t0 = time.time()
    for year in years:
        print(f"\n  EKBE Year {year}")
        run_pass(conn_sap, db, year, PASS1_FIELDS, "Pass1 (BUDAT+amounts)", args.dry_run)
        run_pass(conn_sap, db, year, PASS2_FIELDS, "Pass2 (BLDAT+details)", args.dry_run)

    if not args.dry_run:
        conn_sap.close()

    print(f"\n  Done. Total: {(time.time()-t0)/60:.1f} min")
    db.close()


if __name__ == "__main__":
    main()
