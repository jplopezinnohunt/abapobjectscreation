"""
enrich_fmifiit_objnrz.py
========================
Fetches OBJNRZ (Object Number) from FMIFIIT using existing keys
(BUKRS+KNBELNR+KNGJAHR+KNBUZEI), one period at a time.

OBJNRZ = PRPS.OBJNR -> gives POSID (WBS Element) + POST1 (description).

Usage:
    python enrich_fmifiit_objnrz.py                # All years
    python enrich_fmifiit_objnrz.py --year 2025    # Only 2025
    python enrich_fmifiit_objnrz.py --dry-run      # Show plan
"""

import os
import sys
import time
import sqlite3
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOLD_DB  = os.path.join(BASE_DIR, "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
YEARS    = [2024, 2025, 2026]
BATCH_SIZE = 5000
THROTTLE   = 3.0

sys.path.insert(0, BASE_DIR)
from rfc_helpers import get_connection


def ensure_column(db, table, col, col_type="TEXT"):
    cols = {r[1] for r in db.execute(f"PRAGMA table_info({table})").fetchall()}
    if col not in cols:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type} DEFAULT ''")
        db.commit()
        print(f"  Added column {col} to {table}")


def fetch_objnrz_batch(conn_sap, fikrs, gjahr, perio, max_retries=3):
    """Fetch OBJNRZ from FMIFIIT for a given period. Returns dict {(knbelnr,knbuzei,bukrs): objnrz}."""
    result_map = {}
    offset = 0
    while True:
        result = None
        for attempt in range(max_retries):
            try:
                result = conn_sap.call('RFC_READ_TABLE',
                    QUERY_TABLE='FMIFIIT',
                    FIELDS=[
                        {'FIELDNAME': 'KNBELNR'},
                        {'FIELDNAME': 'KNBUZEI'},
                        {'FIELDNAME': 'BUKRS'},
                        {'FIELDNAME': 'OBJNRZ'}
                    ],
                    OPTIONS=[
                        {'TEXT': f"FIKRS = '{fikrs}' AND GJAHR = '{gjahr}' AND PERIO = '{perio:03d}'"},
                    ],
                    ROWCOUNT=BATCH_SIZE,
                    ROWSKIPS=offset
                )
                break  # success
            except Exception as e:
                if 'TABLE_WITHOUT_DATA' in str(e):
                    return result_map  # no data for this period/fikrs
                if attempt < max_retries - 1:
                    print(f" [retry {attempt+1}]", end="", flush=True)
                    conn_sap.connect()
                    time.sleep(5)
                else:
                    raise

        if result is None or not result['DATA']:
            break

        finfo = {f['FIELDNAME']: (int(f['OFFSET']), int(f['LENGTH'])) for f in result['FIELDS']}
        for row in result['DATA']:
            wa = row['WA']
            knbelnr = wa[finfo['KNBELNR'][0]:finfo['KNBELNR'][0]+finfo['KNBELNR'][1]].strip()
            knbuzei = wa[finfo['KNBUZEI'][0]:finfo['KNBUZEI'][0]+finfo['KNBUZEI'][1]].strip()
            bukrs   = wa[finfo['BUKRS'][0]:finfo['BUKRS'][0]+finfo['BUKRS'][1]].strip()
            objnrz  = wa[finfo['OBJNRZ'][0]:finfo['OBJNRZ'][0]+finfo['OBJNRZ'][1]].strip()

            if objnrz:
                result_map[(knbelnr, knbuzei, bukrs)] = objnrz

        if len(result['DATA']) < BATCH_SIZE:
            break
        offset += BATCH_SIZE
        time.sleep(THROTTLE)

    return result_map


def enrich_year(conn_sap, db, year, dry_run=False):
    """Enrich FMIFIIT with OBJNRZ for all periods in a year."""
    # Get distinct periods
    cur = db.execute(
        "SELECT DISTINCT PERIO FROM fmifiit_full WHERE GJAHR = ? ORDER BY PERIO",
        (str(year),)
    )
    periods = [r[0] for r in cur.fetchall()]
    if not periods:
        print(f"  No data for {year}")
        return 0

    # Get distinct FIKRS
    cur = db.execute(
        "SELECT DISTINCT FIKRS FROM fmifiit_full WHERE GJAHR = ?", (str(year),)
    )
    fikrs_list = [r[0] for r in cur.fetchall()]

    total_updated = 0
    for period in periods:
        cur = db.execute(
            "SELECT COUNT(*) FROM fmifiit_full WHERE GJAHR = ? AND PERIO = ?",
            (str(year), period)
        )
        row_count = cur.fetchone()[0]
        if row_count == 0:
            continue

        # Check already enriched — if ANY rows have OBJNRZ, period was processed
        cur = db.execute(
            "SELECT COUNT(*) FROM fmifiit_full WHERE GJAHR = ? AND PERIO = ? AND OBJNRZ != ''",
            (str(year), period)
        )
        already = cur.fetchone()[0]
        if already > 0:
            print(f"  {year}/{period}: {row_count} rows, {already} OBJNRZ — already done, skip")
            total_updated += already
            continue

        if dry_run:
            print(f"  {year}/{period}: {row_count} rows — would enrich")
            continue

        print(f"  {year}/{period}: {row_count} rows", end="", flush=True)
        t0 = time.time()

        period_count = 0
        for fikrs in fikrs_list:
            perio_int = int(period)
            sap_rows = fetch_objnrz_batch(conn_sap, fikrs, year, perio_int)

            if sap_rows:
                for (knbelnr, knbuzei, bukrs), objnrz in sap_rows.items():
                    db.execute(
                        "UPDATE fmifiit_full SET OBJNRZ = ? WHERE BUKRS = ? AND KNBELNR = ? AND KNGJAHR = ? AND KNBUZEI = ?",
                        (objnrz, bukrs, knbelnr, str(year), knbuzei)
                    )
                period_count += len(sap_rows)

            time.sleep(THROTTLE)

        db.commit()
        elapsed = time.time() - t0
        total_updated += period_count
        print(f" -> {period_count} OBJNRZ updated ({elapsed:.1f}s)")

    return total_updated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    years = [args.year] if args.year else YEARS

    db = sqlite3.connect(GOLD_DB)
    db.execute("PRAGMA journal_mode=WAL")

    ensure_column(db, "fmifiit_full", "OBJNRZ")

    if args.dry_run:
        print("DRY RUN\n")

    conn_sap = get_connection("P01") if not args.dry_run else None

    t0 = time.time()
    for year in years:
        print(f"\n  FMIFIIT Year {year}")
        enrich_year(conn_sap, db, year, args.dry_run)

    if not args.dry_run:
        conn_sap.close()

    print(f"\n  Done. Total: {(time.time()-t0)/60:.1f} min")
    db.close()


if __name__ == "__main__":
    main()
