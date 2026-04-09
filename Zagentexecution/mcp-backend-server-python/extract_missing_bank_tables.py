"""
extract_missing_bank_tables.py
===============================
Extract house bank config tables missing from Gold DB.
Tables: T030H, T035D, T018V, TIBAN, FCLM_BSM_CUST, T012T, BNKA
All from P01, small tables, no pagination needed.
"""
import sys, os, io, sqlite3, time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

DB = os.path.join(os.path.dirname(__file__), "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
SYSTEM = "P01"

TABLES = [
    {"name": "T030H", "where": "KTOPL = 'UNES'",
     "fields": ["KTOPL","HKONT","CURTP","LKORR","LSREA","LHREA","LSBEW","LHBEW"]},
    {"name": "T035D", "where": "BUKRS = 'UNES'",
     "fields": ["BUKRS","DISKB","BNKKO"]},
    {"name": "T018V", "where": "BUKRS = 'UNES'",
     "fields": ["BUKRS","HBKID","HKTID","GEHVK","WAERS","ZLSCH"]},
    {"name": "TIBAN", "where": "BUKRS = 'UNES'",
     "fields": ["BUKRS","HBKID","HKTID","BANKL","BANKN","IBAN"]},
    {"name": "FCLM_BSM_CUST", "where": "BUKRS = 'UNES'",
     "fields": ["BUKRS","HOUSEBANK","ACCOUNTID","WAESSION"]},
    {"name": "T012T", "where": "BUKRS = 'UNES'",
     "fields": ["BUKRS","HBKID","HKTID","TEXT1","SPRAS"]},
]


def safe_read(conn, table, fields, where):
    from pyrfc import RFCError
    try:
        return rfc_read_paginated(conn, table, fields, where,
                                  batch_size=5000, throttle=0.5)
    except RFCError as e:
        err = str(e)
        if "TABLE_NOT_AVAILABLE" in err or "NOT_AUTHORIZED" in err:
            print(f"  [WARN] {table}: {err[:100]}")
            # Try with fewer fields
            if len(fields) > 3:
                print(f"  [RETRY] Trying with first 3 fields only...")
                try:
                    return rfc_read_paginated(conn, table, fields[:3], where,
                                              batch_size=5000, throttle=0.5)
                except RFCError:
                    pass
            return None
        if "DATA_BUFFER_EXCEEDED" in err:
            print(f"  [WARN] {table}: buffer exceeded, trying smaller field list")
            return None
        raise


def load_to_sqlite(db_path, table_name, rows, fields):
    """Load rows into SQLite Gold DB."""
    if not rows:
        return 0

    conn = sqlite3.connect(db_path)
    # Drop existing
    conn.execute(f"DROP TABLE IF EXISTS [{table_name}]")

    # Create table
    col_defs = ", ".join(f"[{f}] TEXT" for f in fields)
    conn.execute(f"CREATE TABLE [{table_name}] ({col_defs})")

    # Insert
    placeholders = ", ".join("?" for _ in fields)
    inserted = 0
    for row in rows:
        values = [str(row.get(f, "")).strip() for f in fields]
        conn.execute(f"INSERT INTO [{table_name}] VALUES ({placeholders})", values)
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def run():
    print("="*70)
    print(f"  Extracting missing bank config tables from {SYSTEM}")
    print("="*70)

    sap_conn = get_connection(SYSTEM)

    for tbl in TABLES:
        name = tbl["name"]
        fields = tbl["fields"]
        where = tbl["where"]

        print(f"\n  {name}...")
        rows = safe_read(sap_conn, name, fields, where)

        if rows is None:
            print(f"  [SKIP] {name}: not accessible")
            continue

        print(f"  [OK] {name}: {len(rows)} rows extracted")

        if rows:
            loaded = load_to_sqlite(DB, name, rows, fields)
            print(f"  [LOADED] {name}: {loaded} rows into Gold DB")
        else:
            print(f"  [EMPTY] {name}: 0 rows")

        time.sleep(1)

    sap_conn.close()

    # Verify
    print(f"\n{'='*70}")
    print("  VERIFICATION")
    print("="*70)
    db_conn = sqlite3.connect(DB)
    for tbl in TABLES:
        name = tbl["name"]
        try:
            cnt = db_conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
            print(f"  {name:20s}: {cnt} rows")
        except Exception as e:
            print(f"  {name:20s}: NOT LOADED ({e})")
    db_conn.close()


if __name__ == "__main__":
    run()
