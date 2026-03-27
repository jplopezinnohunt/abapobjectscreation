"""
extract_payment_config.py — Extract FBZP chain + house bank config for ALL company codes
=========================================================================================
Tables: T001, T042, T042A, T042B, T042C, T042E, T042I, T042Z, T012, T012K
Source: P01 (production truth, SNC/SSO)
Output: Gold DB (INSERT OR REPLACE)

Usage:
    python extract_payment_config.py
"""

import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rfc_helpers import get_connection

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"


def read_table_simple(conn, table, fields, where="", max_rows=50000):
    """Simple RFC_READ_TABLE with auto field-split on DATA_BUFFER_EXCEEDED."""
    from pyrfc import RFCError

    rfc_fields = [{"FIELDNAME": f} for f in fields]
    rfc_options = [{"TEXT": where}] if where else []

    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                           ROWCOUNT=max_rows, ROWSKIPS=0,
                           OPTIONS=rfc_options, FIELDS=rfc_fields)
        return _parse_result(result, fields)
    except RFCError as e:
        err = str(e)
        if "DATA_BUFFER_EXCEEDED" in err:
            print(f"    [SPLIT] {table} too wide with {len(fields)} fields, splitting...")
            return _read_split(conn, table, fields, rfc_options, max_rows)
        if "TABLE_WITHOUT_DATA" in err:
            return []
        if "NOT_AUTHORIZED" in err:
            print(f"    [AUTH] Not authorized for {table}")
            return []
        raise


def _parse_result(result, fields):
    """Parse RFC_READ_TABLE result into list of dicts."""
    raw = result.get("DATA", [])
    hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
    rows = []
    for row in raw:
        parts = row["WA"].split("|")
        rows.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)})
    return rows


def _read_split(conn, table, fields, rfc_options, max_rows):
    """Read with field splitting — try 4 fields, then 3, then 2."""
    for chunk_size in [4, 3, 2]:
        chunks = [fields[i:i+chunk_size] for i in range(0, len(fields), chunk_size)]
        all_data = None
        success = True

        for ci, chunk in enumerate(chunks):
            rfc_fields = [{"FIELDNAME": f} for f in chunk]
            try:
                result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                                   ROWCOUNT=max_rows, ROWSKIPS=0,
                                   OPTIONS=rfc_options, FIELDS=rfc_fields)
                chunk_rows = _parse_result(result, chunk)

                if all_data is None:
                    all_data = [{} for _ in range(len(chunk_rows))]
                for i, row in enumerate(chunk_rows):
                    if i < len(all_data):
                        all_data[i].update(row)
            except Exception as e:
                if "DATA_BUFFER_EXCEEDED" in str(e):
                    success = False
                    break
                raise

        if success and all_data:
            print(f"    [SPLIT] {table}: {len(all_data)} rows via {chunk_size}-field chunks")
            return all_data

    return []


def probe_fields(conn, table):
    """Probe DD03L to discover actual field names for a table."""
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD03L", DELIMITER="|",
                           ROWCOUNT=200, ROWSKIPS=0,
                           OPTIONS=[{"TEXT": f"TABNAME = '{table}' AND FIELDNAME <> '.INCLUDE'"}],
                           FIELDS=[{"FIELDNAME": "FIELDNAME"}, {"FIELDNAME": "DATATYPE"},
                                   {"FIELDNAME": "LENG"}, {"FIELDNAME": "POSITION"}])
        rows = _parse_result(result, ["FIELDNAME", "DATATYPE", "LENG", "POSITION"])
        rows.sort(key=lambda r: int(r.get("POSITION", "0") or "0"))
        return rows
    except Exception as e:
        print(f"    [WARN] DD03L probe failed for {table}: {e}")
        return []


def load_to_sqlite(db, table_name, fields, rows):
    """Load rows into SQLite (full refresh)."""
    if not rows:
        return
    # Use actual fields from rows (may differ from requested if split)
    actual_fields = fields if fields else list(rows[0].keys())
    cols_def = ", ".join(f'"{f}" TEXT' for f in actual_fields)
    db.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    db.execute(f'CREATE TABLE "{table_name}" ({cols_def})')
    placeholders = ", ".join(["?"] * len(actual_fields))
    cols = ", ".join(f'"{f}"' for f in actual_fields)
    db.executemany(
        f'INSERT INTO "{table_name}" ({cols}) VALUES ({placeholders})',
        [[r.get(f, "") for f in actual_fields] for r in rows]
    )
    db.commit()


def main():
    print("\n  Payment Config Extraction — P01 (Production)")
    print("  " + "=" * 55)

    conn = get_connection("P01")
    print("  Connected to P01 (SNC/SSO).\n")

    db = sqlite3.connect(str(DB_PATH))
    results = {}

    # ── Phase 1: Probe DD03L for key tables to discover exact field names ──
    print("  Phase 1: Probing field structures...\n")
    tables_to_probe = ["T001", "T042", "T042A", "T042B", "T042C", "T042E", "T042I",
                       "T042Z", "T012", "T012K"]
    field_map = {}
    for tbl in tables_to_probe:
        dd_fields = probe_fields(conn, tbl)
        if dd_fields:
            names = [f["FIELDNAME"] for f in dd_fields if f["FIELDNAME"] != "MANDT"]
            field_map[tbl] = names
            print(f"    {tbl:10s} -> {len(names)} fields: {', '.join(names[:8])}{'...' if len(names) > 8 else ''}")
        else:
            field_map[tbl] = []
            print(f"    {tbl:10s} -> DD03L probe failed")
        time.sleep(0.5)

    # ── Phase 2: Extract with targeted field lists ──
    # For each table, select key + essential fields (avoid very wide text fields)
    print("\n  Phase 2: Extracting tables...\n")

    # Define essential fields per table (subset of DD03L results)
    essential = {
        "T001":  ["BUKRS", "BUTXT", "ORT01", "LAND1", "WAERS", "KTOPL", "PERIV"],
        "T042":  ["BUKRS", "ZBUKR"],
        "T042A": None,  # Will use DD03L results, max 8 fields
        "T042B": ["BUKRS", "ZLSCH"],  # Key fields first, expand if works
        "T042C": ["ZBUKR", "LAND1", "ZLSCH", "HBKID", "HKTID", "UZAWE"],
        "T042E": ["LAND1", "ZLSCH", "TEXT1"],
        "T042I": ["ZBUKR", "HBKID", "HKTID", "ZLSCH", "RWKEY"],
        "T042Z": ["LAND1", "ZLSCH"],
        "T012":  ["BUKRS", "HBKID", "BANKS", "BANKL", "BANKN", "SWIFT"],
        "T012K": ["BUKRS", "HBKID", "HKTID", "BANKN", "HKONT", "UKONT"],
    }

    for tbl in tables_to_probe:
        # Use essential fields if defined, else first 8 from DD03L
        if essential.get(tbl) is not None:
            fields = essential[tbl]
        elif field_map.get(tbl):
            fields = field_map[tbl][:8]
        else:
            print(f"  [{tbl}] SKIP — no field info")
            results[tbl] = "SKIPPED"
            continue

        # If DD03L gave us real fields, validate essential fields exist
        if field_map.get(tbl):
            valid = [f for f in fields if f in field_map[tbl]]
            if len(valid) < len(fields):
                removed = set(fields) - set(valid)
                print(f"    [{tbl}] Removed non-existent fields: {removed}")
                fields = valid

        if not fields:
            print(f"  [{tbl}] SKIP — no valid fields")
            results[tbl] = "SKIPPED"
            continue

        print(f"  [{tbl}] Extracting {len(fields)} fields: {', '.join(fields[:6])}...")
        try:
            rows = read_table_simple(conn, tbl, fields)
            print(f"    -> {len(rows):,} rows")
            load_to_sqlite(db, tbl, fields, rows)
            results[tbl] = len(rows)

            # If we got data with minimal fields, try to expand
            if rows and len(fields) < len(field_map.get(tbl, [])):
                expanded = [f for f in field_map[tbl] if f not in fields][:4]
                if expanded:
                    all_fields = fields + expanded
                    print(f"    [EXPAND] Trying +{len(expanded)} fields: {', '.join(expanded)}...")
                    try:
                        rows2 = read_table_simple(conn, tbl, all_fields)
                        if rows2:
                            print(f"    [EXPAND] Success: {len(rows2):,} rows with {len(all_fields)} fields")
                            load_to_sqlite(db, tbl, all_fields, rows2)
                            results[tbl] = len(rows2)
                    except Exception:
                        print(f"    [EXPAND] Failed, keeping {len(fields)}-field version")

        except Exception as e:
            print(f"    [ERROR] {e}")
            results[tbl] = f"ERROR: {str(e)[:80]}"

        time.sleep(1)

    conn.close()
    db.close()

    # Summary
    print(f"\n  {'=' * 55}")
    print("  EXTRACTION SUMMARY")
    print(f"  {'=' * 55}")
    total_rows = 0
    for table, count in results.items():
        if isinstance(count, int):
            total_rows += count
            status = f"{count:>6,} rows"
        else:
            status = count
        print(f"    {table:12s} -> {status}")
    print(f"\n    TOTAL: {total_rows:,} rows across {sum(1 for v in results.values() if isinstance(v, int) and v > 0)} tables")
    print(f"    Gold DB: {DB_PATH}")
    print("  Done.\n")


if __name__ == "__main__":
    main()
