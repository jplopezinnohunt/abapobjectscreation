"""
extract_gl_costel_comparison.py
===============================
Extract GL accounts + Cost Element tables from BOTH P01 and D01 for comparison.

Tables:
  - SKA1  (Chart of Accounts level GL master)
  - SKAT  (GL account texts)
  - SKB1  (Company Code level GL master)
  - CSKA  (Cost element master - controlling area)
  - CSKU  (Cost element texts)
  - CSKB  (Cost element per CO area)

Output: SQLite DB with {system}_{table} naming (e.g. P01_SKA1, D01_SKA1)
"""

import os
import sys
import json
import sqlite3
import time

# Add parent for rfc_helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python"))
from rfc_helpers import get_connection, rfc_read_paginated

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sqlite", "p01_gold_master_data.db")

# Table definitions: table_name -> fields to extract
TABLES = {
    "SKA1": [
        "KTOPL", "SAKNR", "BILKT", "GVTYP", "KTOKS", "XBILK", "XLOEV",
        "ERDAT", "ERNAM", "XSPEA", "XSPEB", "XSPEP", "FUNC_AREA",
    ],
    "SKAT": [
        "SPRAS", "KTOPL", "SAKNR", "TXT20", "TXT50",
    ],
    "SKB1": [
        "BUKRS", "SAKNR", "BEGRU", "FDLEV", "FSTAG", "MWSKZ", "MITKZ",
        "XOPVW", "XKRES", "WAERS", "ERDAT", "ERNAM", "XSPEB",
        "ALTKT", "XINTB", "ZUESSION",
    ],
    "CSKA": [
        "KTOPL", "KSTAR", "DATBI", "KATYP", "LSTAR", "XLOEK",
        "ERDAT", "ERNAM",
    ],
    "CSKU": [
        "SPRAS", "KTOPL", "KSTAR", "DATBI", "KTEXT", "LTEXT",
    ],
    "CSKB": [
        "KOKRS", "KSTAR", "DATBI", "KATYP", "BUKRS",
        "ERDAT", "ERNAM",
    ],
}

# WHERE clauses - empty = extract all rows (master data tables are small)
WHERE_CLAUSES = {
    "SKA1": "",
    "SKAT": "SPRAS = 'E'",  # English texts only
    "SKB1": "",
    "CSKA": "",
    "CSKU": "SPRAS = 'E'",  # English texts only
    "CSKB": "",
}


def extract_table(conn, table, fields, where, system_id):
    """Extract a single table and return rows."""
    print(f"\n{'='*60}")
    print(f"  [{system_id}] Extracting {table} ({len(fields)} fields)")
    print(f"{'='*60}")

    t0 = time.time()
    rows = rfc_read_paginated(conn, table, fields, where, batch_size=5000, throttle=1.0)
    elapsed = time.time() - t0
    print(f"  [{system_id}] {table}: {len(rows):,} rows in {elapsed:.1f}s")
    return rows


def save_to_sqlite(rows, table_name, db_path):
    """Save rows to SQLite table (drop + create)."""
    if not rows:
        print(f"  [SKIP] {table_name}: 0 rows, skipping SQLite save")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cols = list(rows[0].keys())
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    cursor.execute(f'CREATE TABLE "{table_name}" ({col_defs})')

    placeholders = ", ".join("?" for _ in cols)
    for row in rows:
        values = [row.get(c, "") for c in cols]
        cursor.execute(f'INSERT INTO "{table_name}" VALUES ({placeholders})', values)

    conn.commit()
    conn.close()
    print(f"  [DB] {table_name}: {len(rows):,} rows saved to SQLite")


def main():
    systems = ["P01", "D01"]

    for system_id in systems:
        print(f"\n{'#'*60}")
        print(f"  CONNECTING TO {system_id}")
        print(f"{'#'*60}")

        try:
            guard = get_connection(system_id)
        except Exception as e:
            print(f"  [ERROR] Cannot connect to {system_id}: {e}")
            continue

        for table, fields in TABLES.items():
            where = WHERE_CLAUSES.get(table, "")
            try:
                rows = extract_table(guard, table, fields, where, system_id)
                sqlite_table = f"{system_id}_{table}"
                save_to_sqlite(rows, sqlite_table, DB_PATH)
            except Exception as e:
                print(f"  [ERROR] {system_id}.{table}: {e}")
                # Try to continue with other tables
                continue

        guard.close()
        print(f"\n  [{system_id}] Done. Connection closed.")

    # Summary
    print(f"\n{'#'*60}")
    print(f"  SUMMARY")
    print(f"{'#'*60}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for system_id in systems:
        for table in TABLES:
            tname = f"{system_id}_{table}"
            try:
                count = cursor.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
                print(f"  {tname}: {count:,} rows")
            except:
                print(f"  {tname}: NOT FOUND")
    conn.close()
    print(f"\n  DB: {DB_PATH}")


if __name__ == "__main__":
    main()
