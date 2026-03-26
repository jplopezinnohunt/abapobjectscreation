"""
extract_jobs_interfaces.py
==========================
Extract background jobs (TBTCO/TBTCP) and interface tables (RFCDES, ICFSERVICE, EDIDC)
from P01 into JSON checkpoints, then load into Gold SQLite DB.

Usage:
    python extract_jobs_interfaces.py --phase jobs       # TBTCO + TBTCP
    python extract_jobs_interfaces.py --phase interfaces  # RFCDES + ICFSERVICE + EDIDC
    python extract_jobs_interfaces.py --phase all         # Everything
    python extract_jobs_interfaces.py --load              # Load JSONs into SQLite
"""

import argparse
import json
import os
import sqlite3
import time
from pathlib import Path

from rfc_helpers import get_connection, rfc_read_paginated

CHECKPOINT_DIR = Path(__file__).parent / "extracted_data"
CHECKPOINT_DIR.mkdir(exist_ok=True)

SQLITE_PATH = Path(__file__).parent.parent / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"


# ── TBTCO: Background Job Headers (2 years) ─────────────────────────────────

TBTCO_FIELDS = [
    "JOBNAME", "JOBCOUNT", "STATUS", "SDLSTRTDT", "SDLSTRTTM",
    "STRTDATE", "STRTTIME", "ENDDATE", "ENDTIME", "AUTHCKNAM",
    "PRDMINS", "PRDHOURS", "PRDDAYS", "PRDWEEKS", "EVENTID",
]

def extract_tbtco(conn):
    """Extract TBTCO month-by-month for 2024-01 to 2026-03."""
    print("=== TBTCO (Background Jobs) ===")
    total = 0
    for year in [2024, 2025, 2026]:
        max_month = 3 if year == 2026 else 12
        for month in range(1, max_month + 1):
            cp_file = CHECKPOINT_DIR / f"TBTCO_{year}_{month:02d}.json"
            if cp_file.exists():
                with open(cp_file, "r") as f:
                    cached = json.load(f)
                print(f"  TBTCO {year}-{month:02d}: {len(cached):,} rows (cached)")
                total += len(cached)
                continue

            start = f"{year}{month:02d}01"
            end = f"{year}{month:02d}31"
            where = f"SDLSTRTDT >= '{start}' AND SDLSTRTDT <= '{end}'"

            print(f"  TBTCO {year}-{month:02d}: extracting...", end=" ", flush=True)
            try:
                rows = rfc_read_paginated(conn, "TBTCO", TBTCO_FIELDS, where, batch_size=5000, throttle=3.0)
                print(f"{len(rows):,} rows")
                if rows or (year < 2026 or month <= 3):
                    with open(cp_file, "w") as f:
                        json.dump(rows, f)
                total += len(rows)
            except Exception as e:
                print(f"ERROR: {e}")
                # Don't checkpoint errors
    print(f"  TBTCO TOTAL: {total:,} rows")
    return total


# ── TBTCP: Background Job Steps ──────────────────────────────────────────────

TBTCP_FIELDS = [
    "JOBNAME", "JOBCOUNT", "STEPCOUNT", "PROGNAME", "VARIANT",
    "AUTHCKNAM", "TYP", "STATUS",
]

def extract_tbtcp(conn):
    """Extract TBTCP — no date field, extract by JOBNAME prefix ranges."""
    print("=== TBTCP (Job Steps) ===")
    cp_file = CHECKPOINT_DIR / "TBTCP_full.json"
    if cp_file.exists():
        with open(cp_file, "r") as f:
            cached = json.load(f)
        print(f"  TBTCP: {len(cached):,} rows (cached)")
        return len(cached)

    # TBTCP has no date field — extract by prefix ranges to avoid timeout
    prefixes = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["Y", "Z"]
    # Actually, just try full table first — if it times out, split
    print("  TBTCP: extracting full table...", end=" ", flush=True)
    try:
        rows = rfc_read_paginated(conn, "TBTCP", TBTCP_FIELDS, "", batch_size=5000, throttle=3.0)
        print(f"{len(rows):,} rows")
        with open(cp_file, "w") as f:
            json.dump(rows, f)
        return len(rows)
    except Exception as e:
        print(f"full table failed: {e}")

    # Fallback: extract by JOBNAME prefix
    print("  TBTCP: falling back to prefix-based extraction...")
    all_rows = []
    for prefix in "ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789":
        where = f"JOBNAME LIKE '{prefix}%'"
        print(f"    prefix '{prefix}'...", end=" ", flush=True)
        try:
            rows = rfc_read_paginated(conn, "TBTCP", TBTCP_FIELDS, where, batch_size=5000, throttle=3.0)
            print(f"{len(rows):,}")
            all_rows.extend(rows)
        except Exception as e:
            print(f"ERROR: {e}")
    print(f"  TBTCP TOTAL: {len(all_rows):,} rows")
    if all_rows:
        with open(cp_file, "w") as f:
            json.dump(all_rows, f)
    return len(all_rows)


# ── RFCDES: RFC Destinations (SM59) ──────────────────────────────────────────

RFCDES_FIELDS = [
    "RFCDEST", "RFCTYPE", "RFCOPTIONS",
]

def extract_rfcdes(conn):
    """Extract RFCDES — small table, single pull."""
    print("=== RFCDES (RFC Destinations / SM59) ===")
    cp_file = CHECKPOINT_DIR / "RFCDES_full.json"
    if cp_file.exists():
        with open(cp_file, "r") as f:
            cached = json.load(f)
        print(f"  RFCDES: {len(cached):,} rows (cached)")
        return len(cached)

    # RFCDES has wide RFCOPTIONS field — try minimal fields first
    # then expand if possible
    print("  RFCDES: extracting...", end=" ", flush=True)
    try:
        rows = rfc_read_paginated(conn, "RFCDES", RFCDES_FIELDS, "", batch_size=5000, throttle=1.0)
        print(f"{len(rows):,} rows")
        if rows:
            with open(cp_file, "w") as f:
                json.dump(rows, f)
        return len(rows)
    except Exception as e:
        print(f"ERROR with 3 fields: {e}")
        # Try just RFCDEST + RFCTYPE
        try:
            rows = rfc_read_paginated(conn, "RFCDES", ["RFCDEST", "RFCTYPE"], "", batch_size=5000, throttle=1.0)
            print(f"  RFCDES (minimal): {len(rows):,} rows")
            if rows:
                with open(cp_file, "w") as f:
                    json.dump(rows, f)
            return len(rows)
        except Exception as e2:
            print(f"  RFCDES FAILED: {e2}")
            return 0


# ── ICFSERVICE: ICF/HTTP Services (SICF) ─────────────────────────────────────

ICFSERVICE_FIELDS = [
    "ICF_NAME", "ICFPARGUID", "ICFACTIVE", "ICF_DOCU",
]

def extract_icfservice(conn):
    """Extract ICFSERVICE — all active HTTP services."""
    print("=== ICFSERVICE (ICF/HTTP Services) ===")
    cp_file = CHECKPOINT_DIR / "ICFSERVICE_full.json"
    if cp_file.exists():
        with open(cp_file, "r") as f:
            cached = json.load(f)
        print(f"  ICFSERVICE: {len(cached):,} rows (cached)")
        return len(cached)

    print("  ICFSERVICE: extracting...", end=" ", flush=True)
    try:
        rows = rfc_read_paginated(conn, "ICFSERVICE", ICFSERVICE_FIELDS, "", batch_size=5000, throttle=1.0)
        print(f"{len(rows):,} rows")
        if rows:
            with open(cp_file, "w") as f:
                json.dump(rows, f)
        return len(rows)
    except Exception as e:
        print(f"ERROR: {e}")
        # Try without ICF_DOCU (may be too wide)
        try:
            rows = rfc_read_paginated(conn, "ICFSERVICE", ["ICF_NAME", "ICFPARGUID", "ICFACTIVE"], "", batch_size=5000, throttle=1.0)
            print(f"  ICFSERVICE (minimal): {len(rows):,} rows")
            if rows:
                with open(cp_file, "w") as f:
                    json.dump(rows, f)
            return len(rows)
        except Exception as e2:
            print(f"  ICFSERVICE FAILED: {e2}")
            return 0


# ── EDIDC: IDoc Headers (2 years) ────────────────────────────────────────────

EDIDC_FIELDS = [
    "DOCNUM", "IDOCTP", "MESTYP", "SNDPRT", "SNDPRN",
    "RCVPRT", "RCVPRN", "STATUS", "CREDAT", "CRETIM",
]

def extract_edidc(conn):
    """Extract EDIDC month-by-month for 2024-2026."""
    print("=== EDIDC (IDoc Headers) ===")
    total = 0
    for year in [2024, 2025, 2026]:
        max_month = 3 if year == 2026 else 12
        for month in range(1, max_month + 1):
            cp_file = CHECKPOINT_DIR / f"EDIDC_{year}_{month:02d}.json"
            if cp_file.exists():
                with open(cp_file, "r") as f:
                    cached = json.load(f)
                print(f"  EDIDC {year}-{month:02d}: {len(cached):,} rows (cached)")
                total += len(cached)
                continue

            start = f"{year}{month:02d}01"
            end = f"{year}{month:02d}31"
            where = f"CREDAT >= '{start}' AND CREDAT <= '{end}'"

            print(f"  EDIDC {year}-{month:02d}: extracting...", end=" ", flush=True)
            try:
                rows = rfc_read_paginated(conn, "EDIDC", EDIDC_FIELDS, where, batch_size=5000, throttle=3.0)
                print(f"{len(rows):,} rows")
                # Checkpoint even 0 rows for completed months
                if rows or (year < 2026 or month <= 2):
                    with open(cp_file, "w") as f:
                        json.dump(rows, f)
                total += len(rows)
            except Exception as e:
                print(f"ERROR: {e}")
                # Don't checkpoint errors — allow retry
    print(f"  EDIDC TOTAL: {total:,} rows")
    return total


# ── SQLite Loader ─────────────────────────────────────────────────────────────

def load_table_to_sqlite(table_name, json_pattern):
    """Load extracted JSON files into SQLite Gold DB."""
    print(f"\n=== Loading {table_name} into SQLite ===")
    files = sorted(CHECKPOINT_DIR.glob(json_pattern))
    if not files:
        print(f"  No files matching {json_pattern}")
        return 0

    all_rows = []
    for f in files:
        with open(f, "r") as fp:
            rows = json.load(fp)
            all_rows.extend(rows)

    if not all_rows:
        print(f"  0 rows total, skipping")
        return 0

    print(f"  {len(all_rows):,} rows from {len(files)} files")

    db = sqlite3.connect(str(SQLITE_PATH))
    cursor = db.cursor()

    # Drop and recreate
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    columns = list(all_rows[0].keys())
    col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
    cursor.execute(f"CREATE TABLE {table_name} ({col_defs})")

    # Batch insert
    placeholders = ", ".join("?" for _ in columns)
    batch = []
    for row in all_rows:
        batch.append(tuple(row.get(c, "") for c in columns))
        if len(batch) >= 10000:
            cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", batch)
            batch = []
    if batch:
        cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", batch)

    db.commit()

    # Create indexes
    if table_name == "tbtco":
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tbtco_jobname ON tbtco(JOBNAME)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tbtco_sdlstrtdt ON tbtco(SDLSTRTDT)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tbtco_status ON tbtco(STATUS)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tbtco_authcknam ON tbtco(AUTHCKNAM)")
    elif table_name == "tbtcp":
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tbtcp_jobname ON tbtcp(JOBNAME, JOBCOUNT)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tbtcp_progname ON tbtcp(PROGNAME)")
    elif table_name == "rfcdes":
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rfcdes_dest ON rfcdes(RFCDEST)")
    elif table_name == "icfservice":
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_icf_name ON icfservice(ICF_NAME)")
    elif table_name == "edidc":
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edidc_credat ON edidc(CREDAT)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edidc_idoctp ON edidc(IDOCTP)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edidc_mestyp ON edidc(MESTYP)")

    db.commit()
    db.close()
    print(f"  {table_name}: {len(all_rows):,} rows loaded + indexed")
    return len(all_rows)


def load_all():
    """Load all extracted tables into SQLite."""
    totals = {}
    totals["tbtco"] = load_table_to_sqlite("tbtco", "TBTCO_*.json")
    totals["tbtcp"] = load_table_to_sqlite("tbtcp", "TBTCP_full.json")
    totals["rfcdes"] = load_table_to_sqlite("rfcdes", "RFCDES_full.json")
    totals["icfservice"] = load_table_to_sqlite("icfservice", "ICFSERVICE_full.json")
    totals["edidc"] = load_table_to_sqlite("edidc", "EDIDC_*.json")
    print(f"\n=== LOAD COMPLETE ===")
    for t, n in totals.items():
        print(f"  {t}: {n:,} rows")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extract jobs & interfaces from P01")
    parser.add_argument("--phase", choices=["jobs", "interfaces", "all"], default="all")
    parser.add_argument("--load", action="store_true", help="Load JSONs into SQLite")
    args = parser.parse_args()

    if args.load:
        load_all()
        return

    conn = get_connection("P01")
    print(f"Connected to P01\n")

    try:
        if args.phase in ("jobs", "all"):
            extract_tbtco(conn)
            extract_tbtcp(conn)

        if args.phase in ("interfaces", "all"):
            extract_rfcdes(conn)
            extract_icfservice(conn)
            extract_edidc(conn)
    finally:
        conn.close()
        print("\nConnection closed.")

    print("\nExtraction complete. Run with --load to load into SQLite.")


if __name__ == "__main__":
    main()
