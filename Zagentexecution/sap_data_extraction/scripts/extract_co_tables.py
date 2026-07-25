"""
extract_co_tables.py
====================
B3: Extract CO tables (COOI, COEP, RPSCO) from P01 -> Gold DB.
Scope: GJAHR 2024-2026 only.

Tables (DD03L-verified 2026-04-03):
  COOI  (51 fields) - CO Commitments. ~385K total.
  COEP  (80 fields) - CO Actuals/Plan. ~616K total.
  RPSCO (48 fields) - PS Period Summary (pivoted WLP/WTP). ~637K total.

Strategy:
  - Extract by GJAHR + PERIO (period 001-016) for VPN resilience
  - Fresh RFC connection per period batch
  - Persist each period immediately to SQLite
  - Skip already-loaded table/year combos

Usage:
    python extract_co_tables.py                   # Full extraction
    python extract_co_tables.py --table COEP      # Single table
    python extract_co_tables.py --year 2025       # Single year
"""

import os
import sys
import time
import sqlite3
import argparse
from datetime import datetime

# Add parent dir for rfc_helpers
MCP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP_DIR))
from rfc_helpers import get_connection, rfc_read_paginated

# -----------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------
PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD_DB = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
YEARS = [2024, 2025, 2026]
PERIODS = [f"{p:03d}" for p in range(0, 17)]  # 000-016
BATCH_SIZE = 5000
THROTTLE = 3.0

# -----------------------------------------------------------------------
# FIELD LISTS -- DD03L-verified 2026-04-03
# -----------------------------------------------------------------------

# COOI: CO Commitments (cost element = SAKTO, doc ref = REFBN+RFPOS)
COOI_FIELDS = [
    "OBJNR", "GJAHR", "WRTTP", "VERSN", "SAKTO", "HRKFT",
    "TWAER", "WTGBTR", "WKGBTR", "WOGBTR",
    "REFBN", "RFPOS", "REFBT", "VRGNG",
    "LIFNR", "BUKRS", "KOKRS", "PERIO", "BUDAT", "BLDAT",
    "SGTXT", "LOEKZ",
]

# COEP: CO Actuals/Plan (KSTAR, BELNR+BUZEI, EBELN+EBELP)
COEP_FIELDS = [
    "OBJNR", "GJAHR", "WRTTP", "VERSN", "KSTAR", "HRKFT",
    "TWAER", "WKGBTR", "WKFBTR", "WOGBTR", "WTGBTR",
    "KOKRS", "BELNR", "BUZEI", "PERIO", "VRGNG",
    "BUKRS", "EBELN", "EBELP",
    "GRANT_NBR", "GEBER", "FKBER",
    "SGTXT",
]

# RPSCO: PS Period Summary (pivoted WLP01-16 + WTP01-16)
# RPSCO does NOT have PERIO -- uses PERBL for period block
# Extract without period splitting (use year only)
RPSCO_FIELDS = [
    "OBJNR", "GJAHR", "WRTTP", "VERSN", "ACPOS", "VORGA",
    "LEDNR", "TRGKZ", "ABKAT", "GEBER", "TWAER", "PERBL", "BELTP",
    "WLP00", "WLP01", "WLP02", "WLP03", "WLP04", "WLP05", "WLP06",
    "WLP07", "WLP08", "WLP09", "WLP10", "WLP11", "WLP12",
    "WLP13", "WLP14", "WLP15", "WLP16",
    "WTP00", "WTP01", "WTP02", "WTP03", "WTP04", "WTP05", "WTP06",
    "WTP07", "WTP08", "WTP09", "WTP10", "WTP11", "WTP12",
    "WTP13", "WTP14", "WTP15", "WTP16",
]

TABLE_CONFIGS = {
    "COOI": {
        "fields": COOI_FIELDS,
        "description": "CO Commitments (~385K total)",
        "has_perio": True,
    },
    "COEP": {
        "fields": COEP_FIELDS,
        "description": "CO Actuals/Plan (~616K total)",
        "has_perio": True,
    },
    "RPSCO": {
        "fields": RPSCO_FIELDS,
        "description": "PS Period Summary (~637K total)",
        "has_perio": False,  # Uses PERBL, not PERIO -- extract by year only
    },
}


# -----------------------------------------------------------------------
# SQLITE HELPERS
# -----------------------------------------------------------------------
def ensure_table(db, table_name, fields):
    """Create SQLite table if not exists."""
    cols = ", ".join([f'"{f}" TEXT' for f in fields])
    db.execute(f'CREATE TABLE IF NOT EXISTS {table_name.lower()} ({cols})')
    db.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name.lower()}_gjahr ON {table_name.lower()}(GJAHR)')
    db.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name.lower()}_objnr ON {table_name.lower()}(OBJNR)')
    db.commit()


def load_period_to_sqlite(db, table_name, fields, rows, year, period=None):
    """Load rows for one period into SQLite. Replaces existing period data."""
    if not rows:
        return 0
    tbl = table_name.lower()
    if period is not None:
        db.execute(f'DELETE FROM {tbl} WHERE GJAHR = ? AND PERIO = ?', (str(year), period))
    else:
        db.execute(f'DELETE FROM {tbl} WHERE GJAHR = ?', (str(year),))
    placeholders = ", ".join(["?"] * len(fields))
    col_names = ", ".join([f'"{f}"' for f in fields])
    batch = [tuple(r.get(f, "") for f in fields) for r in rows]
    db.executemany(f"INSERT INTO {tbl} ({col_names}) VALUES ({placeholders})", batch)
    db.commit()
    return len(batch)


# -----------------------------------------------------------------------
# EXTRACTION - period by period for VPN resilience
# -----------------------------------------------------------------------
def extract_table_by_period(table_name, fields, year, db):
    """Extract one table for one year, period by period. Fresh connection per period."""
    year_total = 0
    print(f"\n  [{table_name}] Year {year} -- extracting by period...")
    t0 = time.time()

    for period in PERIODS:
        where = f"GJAHR = '{year}' AND PERIO = '{period}'"

        # Check if already loaded
        tbl = table_name.lower()
        try:
            existing = db.execute(
                f'SELECT COUNT(*) FROM {tbl} WHERE GJAHR = ? AND PERIO = ?',
                (str(year), period)
            ).fetchone()[0]
            if existing > 0:
                print(f"    P{period}: skip ({existing:,} rows)")
                year_total += existing
                continue
        except Exception:
            pass

        # Fresh connection per period
        try:
            conn = get_connection("P01")
        except Exception as e:
            print(f"    P{period}: CONNECTION FAILED -- {e}")
            print(f"    Stopping year {year}. Resume later.")
            return year_total

        try:
            rows = rfc_read_paginated(conn, table_name, fields, where,
                                       batch_size=BATCH_SIZE, throttle=THROTTLE)
            if rows:
                loaded = load_period_to_sqlite(db, table_name, fields, rows, year, period)
                print(f"    P{period}: {loaded:,} rows")
                year_total += loaded
            else:
                print(f"    P{period}: 0 rows")
        except Exception as e:
            print(f"    P{period}: ERROR -- {e}")
            print(f"    Stopping year {year}. Resume later.")
            try:
                conn.close()
            except Exception:
                pass
            return year_total
        finally:
            try:
                conn.close()
            except Exception:
                pass

    elapsed = time.time() - t0
    print(f"  [{table_name}] Year {year}: {year_total:,} rows total in {elapsed:.0f}s")
    return year_total


def extract_table_by_year(table_name, fields, year, db):
    """Extract one table for one year (no period split). For RPSCO."""
    print(f"\n  [{table_name}] Year {year} -- extracting full year...")
    t0 = time.time()

    # Check if already loaded
    tbl = table_name.lower()
    try:
        existing = db.execute(
            f'SELECT COUNT(*) FROM {tbl} WHERE GJAHR = ?', (str(year),)
        ).fetchone()[0]
        if existing > 0:
            print(f"  [{table_name}] Year {year}: SKIP ({existing:,} rows already loaded)")
            return existing
    except Exception:
        pass

    try:
        conn = get_connection("P01")
    except Exception as e:
        print(f"  [{table_name}] CONNECTION FAILED -- {e}")
        return 0

    try:
        where = f"GJAHR = '{year}'"
        rows = rfc_read_paginated(conn, table_name, fields, where,
                                   batch_size=BATCH_SIZE, throttle=THROTTLE)
        if rows:
            loaded = load_period_to_sqlite(db, table_name, fields, rows, year)
            elapsed = time.time() - t0
            print(f"  [{table_name}] Year {year}: {loaded:,} rows in {elapsed:.0f}s")
            return loaded
        else:
            print(f"  [{table_name}] Year {year}: 0 rows")
            return 0
    except Exception as e:
        print(f"  [{table_name}] Year {year}: ERROR -- {e}")
        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass


# -----------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Extract CO tables from P01")
    parser.add_argument("--table", type=str, help="Single table (COOI, COEP, RPSCO)")
    parser.add_argument("--year", type=int, help="Single year")
    args = parser.parse_args()

    years = [args.year] if args.year else YEARS
    tables = {args.table: TABLE_CONFIGS[args.table]} if args.table else TABLE_CONFIGS

    print(f"\n{'='*60}")
    print(f"  CO Tables Extraction | P01 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Tables: {list(tables.keys())} | Years: {years}")
    print(f"  Strategy: period-by-period with fresh connections")
    print(f"{'='*60}\n")

    db = sqlite3.connect(GOLD_DB)
    grand_total = 0
    t_start = time.time()

    for tbl, cfg in tables.items():
        fields = cfg["fields"]
        ensure_table(db, tbl, fields)
        print(f"\n=== {tbl}: {cfg['description']} ===")

        for year in years:
            if cfg["has_perio"]:
                count = extract_table_by_period(tbl, fields, year, db)
            else:
                count = extract_table_by_year(tbl, fields, year, db)
            grand_total += count

    # Verify totals
    print(f"\n{'='*60}")
    print(f"  VERIFICATION")
    print(f"{'='*60}")
    for tbl in tables:
        total = db.execute(f"SELECT COUNT(*) FROM {tbl.lower()}").fetchone()[0]
        per_year = {}
        for y in years:
            c = db.execute(f"SELECT COUNT(*) FROM {tbl.lower()} WHERE GJAHR = ?", (str(y),)).fetchone()[0]
            per_year[y] = c
        print(f"  {tbl}: {total:,} total -- {per_year}")

    db.close()
    elapsed = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"  COMPLETE | {grand_total:,} rows | {elapsed/60:.1f} min")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
