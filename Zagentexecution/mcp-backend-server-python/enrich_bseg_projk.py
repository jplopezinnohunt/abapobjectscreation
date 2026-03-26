"""
enrich_bseg_projk.py
====================
Fetches PROJK (WBS internal key) from BSEG using existing BSIS/BSAS
document keys (BUKRS+BELNR+GJAHR), then stores it in BSIS/BSAS.

PROJK JOINed with PRPS.PSPNR gives POSID = WBS Element.

Rule: use existing keys, fetch only missing field, one period at a time.
BSEG key: BUKRS + BELNR + GJAHR + BUZEI (no BUDAT/MONAT).
Strategy: filter by BUKRS + GJAHR + BELNR range per period.

Usage:
    python enrich_bseg_projk.py                   # All years
    python enrich_bseg_projk.py --year 2025       # Only 2025
    python enrich_bseg_projk.py --table BSIS      # Only BSIS
    python enrich_bseg_projk.py --dry-run         # Show plan
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


def fetch_projk_from_bseg(conn_sap, bukrs, gjahr, belnr_min, belnr_max):
    """Fetch PROJK from BSEG for a BELNR range. Returns dict {(belnr,buzei): projk}."""
    result_map = {}
    offset = 0
    while True:
        try:
            result = conn_sap.call('RFC_READ_TABLE',
                QUERY_TABLE='BSEG',
                FIELDS=[
                    {'FIELDNAME': 'BELNR'},
                    {'FIELDNAME': 'BUZEI'},
                    {'FIELDNAME': 'PROJK'}
                ],
                OPTIONS=[
                    {'TEXT': f"BUKRS = '{bukrs}' AND GJAHR = '{gjahr}'"},
                    {'TEXT': f" AND BELNR >= '{belnr_min}' AND BELNR <= '{belnr_max}'"},
                ],
                ROWCOUNT=BATCH_SIZE,
                ROWSKIPS=offset
            )
        except Exception as e:
            if 'TABLE_WITHOUT_DATA' in str(e):
                break
            raise

        if not result['DATA']:
            break

        finfo = {f['FIELDNAME']: (int(f['OFFSET']), int(f['LENGTH'])) for f in result['FIELDS']}
        for row in result['DATA']:
            wa = row['WA']
            belnr = wa[finfo['BELNR'][0]:finfo['BELNR'][0]+finfo['BELNR'][1]].strip()
            buzei = wa[finfo['BUZEI'][0]:finfo['BUZEI'][0]+finfo['BUZEI'][1]].strip()
            projk = wa[finfo['PROJK'][0]:finfo['PROJK'][0]+finfo['PROJK'][1]].strip()
            if projk and projk != '00000000':
                result_map[(belnr, buzei)] = projk

        if len(result['DATA']) < BATCH_SIZE:
            break
        offset += BATCH_SIZE
        time.sleep(THROTTLE)

    return result_map


def enrich_table(conn_sap, db, table, year, dry_run=False):
    """Fetch PROJK from BSEG for all docs in table/year."""
    cur = db.execute(
        f"SELECT DISTINCT MONAT FROM {table} WHERE GJAHR = ? ORDER BY MONAT",
        (str(year),)
    )
    periods = [r[0] for r in cur.fetchall()]
    if not periods:
        print(f"  [{table}] No data for {year}")
        return 0

    total_updated = 0
    for period in periods:
        cur = db.execute(
            f"SELECT COUNT(*) FROM {table} WHERE GJAHR = ? AND MONAT = ?",
            (str(year), period)
        )
        row_count = cur.fetchone()[0]
        if row_count == 0:
            continue

        # Check already enriched
        cur = db.execute(
            f"SELECT COUNT(*) FROM {table} WHERE GJAHR = ? AND MONAT = ? AND PROJK != ''",
            (str(year), period)
        )
        already = cur.fetchone()[0]
        if already == row_count:
            print(f"  [{table}] {year}/{period}: {row_count} rows — already done, skip")
            total_updated += already
            continue

        if dry_run:
            print(f"  [{table}] {year}/{period}: {row_count} rows — would enrich")
            continue

        print(f"  [{table}] {year}/{period}: {row_count} rows", end="", flush=True)
        t0 = time.time()

        # Get BELNR range per BUKRS for this period
        cur = db.execute(
            f"SELECT BUKRS, MIN(BELNR), MAX(BELNR) FROM {table} WHERE GJAHR = ? AND MONAT = ? GROUP BY BUKRS",
            (str(year), period)
        )
        bukrs_ranges = cur.fetchall()

        period_count = 0
        for bukrs, belnr_min, belnr_max in bukrs_ranges:
            sap_rows = fetch_projk_from_bseg(conn_sap, bukrs, year, belnr_min, belnr_max)

            if sap_rows:
                for (belnr, buzei), projk in sap_rows.items():
                    db.execute(
                        f"UPDATE {table} SET PROJK = ? WHERE BUKRS = ? AND BELNR = ? AND GJAHR = ? AND BUZEI = ?",
                        (projk, bukrs, belnr, str(year), buzei)
                    )
                period_count += len(sap_rows)

            time.sleep(THROTTLE)

        db.commit()
        elapsed = time.time() - t0
        total_updated += period_count
        print(f" -> {period_count} PROJK updated ({elapsed:.1f}s)")

    return total_updated


def rebuild_view(db):
    """Rebuild bseg_union view."""
    db.execute("DROP VIEW IF EXISTS bseg_union")
    all_tables = ['bsis', 'bsas', 'bsik', 'bsak', 'bsid', 'bsad']
    col_sets = {}
    for t in all_tables:
        col_sets[t] = [r[1] for r in db.execute(f"PRAGMA table_info({t})").fetchall()]

    base_cols = col_sets['bsis']  # widest after enrichment

    parts = []
    for t in all_tables:
        t_cols = set(col_sets[t])
        selects = []
        for c in base_cols:
            selects.append(c if c in t_cols else f"'' AS {c}")
        selects.append(f"'{t}' AS source_table")
        parts.append(f"SELECT {', '.join(selects)} FROM {t}")

    db.execute(f"CREATE VIEW bseg_union AS {' UNION ALL '.join(parts)}")
    db.commit()

    cur = db.execute("SELECT COUNT(*) FROM bseg_union")
    cols = [r[1] for r in db.execute("PRAGMA table_info(bseg_union)").fetchall()]
    print(f"\n  [VIEW] bseg_union rebuilt: {len(cols)} columns, {cur.fetchone()[0]:,} rows")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int)
    parser.add_argument("--table", choices=["BSIS", "BSAS"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    years = [args.year] if args.year else YEARS
    tables = [args.table] if args.table else ["BSIS", "BSAS"]

    db = sqlite3.connect(GOLD_DB)
    db.execute("PRAGMA journal_mode=WAL")

    for t in ["bsis", "bsas"]:
        ensure_column(db, t, "PROJK")

    if args.dry_run:
        print("DRY RUN\n")

    conn_sap = get_connection("P01") if not args.dry_run else None

    t0 = time.time()
    for table in tables:
        for year in years:
            print(f"\n  [{table}] Year {year}")
            enrich_table(conn_sap, db, table.lower(), year, args.dry_run)

    if not args.dry_run:
        rebuild_view(db)
        conn_sap.close()

    print(f"\n  Done. Total: {(time.time()-t0)/60:.1f} min")
    db.close()


if __name__ == "__main__":
    main()
