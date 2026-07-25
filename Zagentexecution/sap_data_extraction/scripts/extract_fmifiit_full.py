"""
extract_fmifiit_full.py
========================
Extracts the full FMIFIIT table from SAP P01 in annual batches by fund area.

FMIFIIT = FM FI Integration Item Table
  - Links FM documents (budgets, actuals) to FI accounting documents
  - KEY JOIN: FMIFIIT.BELNR -> BKPF.BELNR (when BKPF is extracted)
  - Size: ~2M rows across 2024-2026 (see volume_anchors table)

Strategy:
  - Filter by RYEAR + FIKRS (fund area) to stay within RFC_READ_TABLE 512-row limit
  - 7 fund areas x 3 years = 21 checkpoints
  - Checkpoints saved to extracted_data/FMIFIIT/

Usage:
    python extract_fmifiit_full.py                  # All years + areas
    python extract_fmifiit_full.py --year 2024      # One year only
    python extract_fmifiit_full.py --area UNES      # One fund area only
    python extract_fmifiit_full.py --check          # Show expected vs actual counts
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

# Load .env
from dotenv import load_dotenv
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPTS_DIR, ".env"))



# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(SCRIPTS_DIR)
DATA_DIR = os.path.join(BASE_DIR, "extracted_data", "FMIFIIT")
SQLITE_DB = os.path.join(BASE_DIR, "sqlite", "p01_gold_master_data.db")
os.makedirs(DATA_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# SAP CONNECTION
# ─────────────────────────────────────────────────────────────────────────────
def get_conn():
    from pyrfc import Connection
    ENV_PATH = os.path.join(BASE_DIR, "..", "mcp-backend-server-python", ".env")
    load_dotenv(os.path.abspath(ENV_PATH))
    def env(k, d=None):
        return os.getenv(f"SAP_P01_{k}") or os.getenv(f"SAP_{k}") or d
    params = {
        "ashost": env("ASHOST"), "sysnr": env("SYSNR", "00"),
        "client": env("CLIENT", "100"), "lang": env("LANG", "EN"),
    }
    if env("SNC_MODE") == "1":
        params["snc_mode"]        = "1"
        params["snc_partnername"] = env("SNC_PARTNERNAME")
        params["snc_qop"]         = env("SNC_QOP", "9")
        if env("SNC_MYNAME"):
            params["snc_myname"]  = env("SNC_MYNAME")
    else:
        params["user"]   = env("USER")
        params["passwd"] = env("PASSWD") or env("PASSWORD")
    return Connection(**params)

# ─────────────────────────────────────────────────────────────────────────────
# KNOWN VOLUME ANCHORS (from volume_anchors SQLite table)
# Used to set expectations and validate extractions
# ─────────────────────────────────────────────────────────────────────────────
VOLUME_ANCHORS = {
    ("FMIFIIT", "2024", "UNES"): 857_633,
    ("FMIFIIT", "2024", "UBO"):   18_367,
    ("FMIFIIT", "2024", "IBE"):    6_012,
    ("FMIFIIT", "2024", "ICTP"):  32_775,
    ("FMIFIIT", "2024", "IIEP"):  20_950,
    ("FMIFIIT", "2024", "MGIE"):   4_207,
    ("FMIFIIT", "2024", "UIS"):    5_109,
    ("FMIFIIT", "2025", "UNES"): 895_221,
    ("FMIFIIT", "2025", "UBO"):   18_570,
    ("FMIFIIT", "2025", "IBE"):    4_503,
    ("FMIFIIT", "2025", "ICTP"):  29_613,
    ("FMIFIIT", "2025", "IIEP"):  21_341,
    ("FMIFIIT", "2025", "MGIE"):   3_631,
    ("FMIFIIT", "2025", "UIS"):    5_416,
    ("FMIFIIT", "2026", "UNES"): 128_280,
    ("FMIFIIT", "2026", "UBO"):    3_017,
    ("FMIFIIT", "2026", "IBE"):      768,
    ("FMIFIIT", "2026", "ICTP"):   4_044,
    ("FMIFIIT", "2026", "IIEP"):   2_942,
    ("FMIFIIT", "2026", "MGIE"):     539,
    ("FMIFIIT", "2026", "UIS"):      724,
}

YEARS      = ["2024", "2025", "2026"]
FUND_AREAS = ["UNES", "UBO", "IBE", "ICTP", "IIEP", "MGIE", "UIS"]

# FMIFIIT fields to extract (verified from DD03L on P01)
# Key fields marked with (K)
FIELDS = [
    # --- Key fields ---
    "FIKRS",     # (K) FM Area (fund area code)
    "GJAHR",     # (K) Fiscal year
    "FMBELNR",   # (K) FM document number   <- KEY for FM docs
    "FMBUZEI",   # (K) FM line item number
    "BTART",     # (K) Budget transaction type
    "RLDNR",     # (K) Ledger
    "STUNR",     # (K) Item number
    # --- Core financial ---
    "FONDS",     # Fund                     <- KEY JOIN to funds table
    "FISTL",     # Fund center              <- KEY JOIN to fund_centers table
    "FIPEX",     # Commitment item
    "FAREA",     # Functional area
    "WRTTP",     # Value type
    "TWAER",     # Currency key
    "FKBTR",     # Amount in FM area currency
    "TRBTR",     # Transaction currency amount
    "PERIO",     # Posting period (001-016)
    "STATS",     # Status
    "VRGNG",     # FM transaction type
    # --- References ---
    "BUKRS",     # Company code
    "HKONT",     # G/L account
    "PRCTR",     # Profit center
    "GRANT_NBR", # Grant number
    "MEASURE",   # Funded program
    "KNBELNR",   # Linked FI doc number     <- KEY JOIN to BKPF.BELNR
    "KNGJAHR",   # Linked FI doc year
    "KNBUZEI",   # Linked FI doc line
    "SGTXT",     # Item text
]

# SAP SAFETY SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
THROTTLE_SEC   = 3      # seconds between RFC calls (be nice to SAP)
MAX_RFC_ROWS   = 5000   # rows per RFC call — small to avoid memory pressure
POSTING_PERIODS = [f"{p:03d}" for p in range(1, 17)]  # 001 to 016 (includes special periods 13-16)

# Areas sorted smallest→largest: test smallest first, UNES (900K/yr) always last
FUND_AREAS_SAFE_ORDER = ["IBE", "UIS", "MGIE", "UBO", "IIEP", "ICTP", "UNES"]


def checkpoint_path(year, area, period=None):
    if period:
        return os.path.join(DATA_DIR, f"FMIFIIT_{year}_{area}_{period}.json")
    return os.path.join(DATA_DIR, f"FMIFIIT_{year}_{area}.json")


def is_period_done(year, area, period):
    path = checkpoint_path(year, area, period)
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("complete", False)


def extract_one_period(conn, year, area, period):
    """Extract one (FIKRS, GJAHR, POPER) slice — no ROWSKIPS needed."""
    path = checkpoint_path(year, area, period)
    all_rows = []
    start    = time.time()
    offset   = 0

    while True:
        try:
            result = conn.call(
                "RFC_READ_TABLE",
                QUERY_TABLE="FMIFIIT",
                DELIMITER="|",
                ROWCOUNT=MAX_RFC_ROWS,
                ROWSKIPS=offset,   # offset within this period slice — small, safe
                FIELDS=[{"FIELDNAME": f} for f in FIELDS],
                OPTIONS=[
                    {"TEXT": f"FIKRS EQ '{area}'"},
                    {"TEXT": f" AND GJAHR EQ '{year}'"},
                    {"TEXT": f" AND PERIO EQ '{period}'"},
                ],
            )
        except Exception as e:
            if "TABLE_WITHOUT_DATA" in str(e):
                break  # 0 rows for this period — normal, move on
            raise  # real error — propagate

        batch  = result.get("DATA", [])
        fields = [f["FIELDNAME"] for f in result.get("FIELDS", [])]

        for row in batch:
            parts = row["WA"].split("|")
            all_rows.append(dict(zip(fields, [p.strip() for p in parts])))

        offset   += len(batch)
        if len(batch) < MAX_RFC_ROWS:
            break  # got all rows for this period
        time.sleep(THROTTLE_SEC)

    # Save checkpoint
    checkpoint = {
        "table":  "FMIFIIT", "year": year, "area": area, "period": period,
        "rows":   len(all_rows), "complete": True,
        "extracted_at": datetime.now().isoformat(),
        "data":   all_rows,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False)

    elapsed = time.time() - start
    print(f"    [{year}/{area}/P{period}] {len(all_rows):,} rows in {elapsed:.1f}s")
    return len(all_rows)


def extract_one_area(conn, year, area, force=False):
    """Extract all 16 periods for one fund area, then auto-load to SQLite."""
    expected = VOLUME_ANCHORS.get(("FMIFIIT", year, area), 0)
    print(f"\n  [{year}/{area}] Expected ~{expected:,} total rows  (16 periods x ~{expected//16:,})")
    total = 0
    for period in POSTING_PERIODS:
        if not force and is_period_done(year, area, period):
            with open(checkpoint_path(year, area, period), encoding="utf-8") as f:
                n = json.load(f).get("rows", 0)
            print(f"    [{year}/{area}/P{period}] SKIP ({n:,} rows already extracted)")
            total += n
            continue
        n = extract_one_period(conn, year, area, period)
        total += n
        time.sleep(THROTTLE_SEC)
    print(f"  [{year}/{area}] COMPLETE: {total:,} rows across all periods")
    # AUTO-LOAD to SQLite immediately
    load_area_to_sqlite(year, area)
    return total


# ─────────────────────────────────────────────────────────────────────────────
# SQLITE AUTO-LOADER — runs after each area completes
# ─────────────────────────────────────────────────────────────────────────────
SQLITE_COLS = [
    "FIKRS","GJAHR","FMBELNR","FMBUZEI","BTART","RLDNR","STUNR",
    "FONDS","FISTL","FIPEX","FAREA","WRTTP","TWAER","FKBTR","TRBTR",
    "PERIO","STATS","VRGNG","BUKRS","HKONT","PRCTR",
    "GRANT_NBR","MEASURE","KNBELNR","KNGJAHR","KNBUZEI","SGTXT"
]

def _ensure_sqlite_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS fmifiit_full (
            FIKRS TEXT, GJAHR TEXT, FMBELNR TEXT, FMBUZEI TEXT,
            BTART TEXT, RLDNR TEXT, STUNR TEXT,
            FONDS TEXT, FISTL TEXT, FIPEX TEXT, FAREA TEXT,
            WRTTP TEXT, TWAER TEXT, FKBTR TEXT, TRBTR TEXT,
            PERIO TEXT, STATS TEXT, VRGNG TEXT,
            BUKRS TEXT, HKONT TEXT, PRCTR TEXT,
            GRANT_NBR TEXT, MEASURE TEXT,
            KNBELNR TEXT, KNGJAHR TEXT, KNBUZEI TEXT,
            SGTXT TEXT
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_fmifiit_fikrs_gjahr ON fmifiit_full(FIKRS, GJAHR)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_fmifiit_fonds ON fmifiit_full(FONDS)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_fmifiit_fistl ON fmifiit_full(FISTL)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_fmifiit_knbelnr ON fmifiit_full(KNBELNR)")


def load_area_to_sqlite(year, area):
    """Load all period checkpoints for one area/year into SQLite."""
    import sqlite3, glob
    db = sqlite3.connect(SQLITE_DB)
    _ensure_sqlite_table(db)

    # Delete existing rows for this area/year (idempotent reload)
    db.execute("DELETE FROM fmifiit_full WHERE FIKRS=? AND GJAHR=?", (area, year))

    placeholders = ",".join(["?"] * len(SQLITE_COLS))
    loaded = 0
    for period in POSTING_PERIODS:
        path = checkpoint_path(year, area, period)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            ck = json.load(f)
        rows = ck.get("data", [])
        if not rows:
            continue
        batch = [tuple(r.get(c, "") for c in SQLITE_COLS) for r in rows]
        db.executemany(f"INSERT INTO fmifiit_full VALUES ({placeholders})", batch)
        loaded += len(batch)

    db.commit()
    total = db.execute("SELECT COUNT(*) FROM fmifiit_full WHERE FIKRS=? AND GJAHR=?",
                       (area, year)).fetchone()[0]
    db.close()
    print(f"    -> SQLite: loaded {loaded:,} rows (verified: {total:,})")



def show_check():
    """Show expected vs extracted (by period) for all combos."""
    print(f"\n{'Year':<6} {'Area':<6} {'Expected':>12} {'Extracted':>12} {'Periods':>8} {'Status'}")
    print(f"{'-'*6} {'-'*6} {'-'*12} {'-'*12} {'-'*8} {'-'*15}")
    for year in YEARS:
        for area in FUND_AREAS:
            expected = VOLUME_ANCHORS.get(("FMIFIIT", year, area), 0)
            total_rows = 0
            periods_done = 0
            for period in POSTING_PERIODS:
                path = checkpoint_path(year, area, period)
                if os.path.exists(path):
                    with open(path, encoding="utf-8") as f:
                        d = json.load(f)
                    if d.get("complete"):
                        total_rows += d.get("rows", 0)
                        periods_done += 1
            if periods_done == 16:
                status = "COMPLETE"
            elif periods_done > 0:
                status = f"{periods_done}/16 periods"
            else:
                status = "not started"
            print(f"{year:<6} {area:<6} {expected:>12,} {total_rows:>12,} {periods_done:>8}/16  {status}")


def main():
    parser = argparse.ArgumentParser(description="FMIFIIT full extraction — safe period-by-period batching")
    parser.add_argument("--year",  help="Extract only this year (2024/2025/2026)")
    parser.add_argument("--area",  help="Extract only this fund area (UNES/UBO/etc)")
    parser.add_argument("--check", action="store_true", help="Show check table only, no extraction")
    parser.add_argument("--force", action="store_true", help="Re-extract even if period checkpoint exists")
    parser.add_argument("--safe",  action="store_true", help="Skip UNES — run all small areas first")
    args = parser.parse_args()

    print(f"\n{'='*65}")
    print(f"  FMIFIIT FULL EXTRACTION  (Period-based, SAP-safe)")
    print(f"  Strategy: {MAX_RFC_ROWS:,} rows/call, {THROTTLE_SEC}s throttle, 16 periods/area")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Output: {DATA_DIR}")
    print(f"{'='*65}")

    if args.check:
        show_check()
        return

    years = [args.year] if args.year else YEARS
    # Use safe order (smallest first) unless specific area requested
    if args.area:
        areas = [args.area]
    elif args.safe:
        areas = [a for a in FUND_AREAS_SAFE_ORDER if a != "UNES"]
        print("  --safe mode: skipping UNES (run separately with --area UNES after testing)")
    else:
        areas = FUND_AREAS_SAFE_ORDER  # smallest first, UNES last

    total_extracted = 0
    try:
        conn = get_conn()
        print("  SAP connection OK\n")
    except Exception as e:
        print(f"\n[FATAL] SAP Connection Failed:\n{e}")
        return

    for year in years:
        for area in areas:
            try:
                n = extract_one_area(conn, year, area, force=args.force)
                total_extracted += n
            except Exception as e:
                print(f"  [{year}/{area}] ERROR: {e}")

    conn.close()
    print(f"\n  EXTRACTION COMPLETE")
    print(f"  Total rows extracted: {total_extracted:,}")
    show_check()
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
