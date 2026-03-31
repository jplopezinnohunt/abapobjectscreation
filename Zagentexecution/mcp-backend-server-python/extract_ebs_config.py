"""
extract_ebs_config.py — Extract EBS (Electronic Bank Statement) config tables from P01
=======================================================================================
Tables: FEBEP, FEBKO, YBASUBST, YTFI_BA_SUBST, T028B, T028D, T028G, T028R
Source: P01 (production truth, SNC/SSO)
Output: Gold DB (full refresh per table)

Session #029 — Bank Statement & Reconciliation Deep Knowledge
These tables bridge EBS configuration to production reality.

Usage:
    python extract_ebs_config.py
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
    print("\n  EBS Config Extraction — P01 (Production)")
    print("  " + "=" * 60)
    print("  Session #029: Bank Statement & Reconciliation Deep Knowledge")
    print("  " + "=" * 60)

    conn = get_connection("P01")
    print("  Connected to P01 (SNC/SSO).\n")

    db = sqlite3.connect(str(DB_PATH))
    results = {}

    # ── EBS Config Tables ──
    # Define tables with their essential fields.
    # For unknown/custom tables, we probe DD03L first then extract all non-MANDT fields.

    ebs_tables = {
        # Standard EBS config
        "T028B": {
            "desc": "EBS Posting Rules (ext code -> posting rule)",
            "fields": None,  # probe DD03L
        },
        "T028D": {
            "desc": "EBS Search String Definitions",
            "fields": None,
        },
        "T028G": {
            "desc": "EBS Account Symbols (BANK, BANK_SUB, etc.)",
            "fields": None,
        },
        "T028R": {
            "desc": "EBS Transaction Types (ext transaction defs)",
            "fields": None,
        },
        # Custom BA substitution tables
        "YBASUBST": {
            "desc": "Legacy Business Area Substitution (1:1 mapping)",
            "fields": None,
        },
        "YTFI_BA_SUBST": {
            "desc": "Modern Business Area Substitution (range-based, post 10/2022)",
            "fields": None,
        },
        # EBS posting data (verify row counts)
        "FEBKO": {
            "desc": "EBS Header (bank statement headers)",
            "fields": None,
        },
        "FEBEP": {
            "desc": "EBS Line Items (bank statement posting items)",
            "fields": None,
        },
    }

    # ── Phase 1: Probe DD03L for all tables ──
    print("  Phase 1: Probing field structures via DD03L...\n")
    field_map = {}
    for tbl in ebs_tables:
        dd_fields = probe_fields(conn, tbl)
        if dd_fields:
            names = [f["FIELDNAME"] for f in dd_fields if f["FIELDNAME"] != "MANDT"]
            field_map[tbl] = names
            print(f"    {tbl:20s} -> {len(names):>3} fields: {', '.join(names[:8])}{'...' if len(names) > 8 else ''}")
        else:
            field_map[tbl] = []
            print(f"    {tbl:20s} -> NOT FOUND or no access")
        time.sleep(0.3)

    # ── Phase 2: Extract each table ──
    print(f"\n  Phase 2: Extracting {len(ebs_tables)} tables...\n")

    for tbl, cfg in ebs_tables.items():
        desc = cfg["desc"]

        # Determine fields to extract
        if cfg["fields"]:
            fields = cfg["fields"]
        elif field_map.get(tbl):
            # Use all non-MANDT fields from DD03L (these are small config tables)
            fields = field_map[tbl]
        else:
            print(f"  [{tbl:20s}] SKIP — table not found in DD03L")
            results[tbl] = {"rows": 0, "status": "NOT_FOUND", "desc": desc}
            continue

        # For FEBEP/FEBKO: first just probe count (may be huge or zero)
        if tbl in ("FEBEP", "FEBKO"):
            print(f"  [{tbl:20s}] Probing row count first...")
            try:
                # Try reading just 1 row with key field to check if data exists
                key_field = fields[0] if fields else "MANDT"
                probe = conn.call("RFC_READ_TABLE", QUERY_TABLE=tbl, DELIMITER="|",
                                  ROWCOUNT=1, ROWSKIPS=0,
                                  FIELDS=[{"FIELDNAME": key_field}])
                row_count = len(probe.get("DATA", []))
                if row_count == 0:
                    print(f"    -> 0 rows (confirmed empty). {desc}")
                    results[tbl] = {"rows": 0, "status": "EMPTY_CONFIRMED", "desc": desc}
                    continue
                else:
                    print(f"    -> Has data! Extracting...")
            except Exception as e:
                err = str(e)
                if "TABLE_WITHOUT_DATA" in err:
                    print(f"    -> 0 rows (TABLE_WITHOUT_DATA). {desc}")
                    results[tbl] = {"rows": 0, "status": "EMPTY_CONFIRMED", "desc": desc}
                    continue
                elif "NOT_AUTHORIZED" in err:
                    print(f"    -> NOT AUTHORIZED. {desc}")
                    results[tbl] = {"rows": 0, "status": "NOT_AUTHORIZED", "desc": desc}
                    continue
                print(f"    [WARN] Probe error: {err[:80]}")

        # Extract with max 8 fields first to avoid buffer issues, expand if works
        extract_fields = fields[:8] if len(fields) > 8 else fields
        print(f"  [{tbl:20s}] Extracting {len(extract_fields)} fields: {', '.join(extract_fields[:6])}...")

        try:
            rows = read_table_simple(conn, tbl, extract_fields)
            print(f"    -> {len(rows):,} rows")
            load_to_sqlite(db, tbl, extract_fields, rows)
            results[tbl] = {"rows": len(rows), "status": "OK", "desc": desc, "fields": len(extract_fields)}

            # Try expanding to all fields if we got data and there are more fields
            if rows and len(extract_fields) < len(fields):
                remaining = [f for f in fields if f not in extract_fields]
                # Try adding 4 more fields at a time
                for batch_start in range(0, len(remaining), 4):
                    batch = remaining[batch_start:batch_start+4]
                    expanded = extract_fields + batch
                    print(f"    [EXPAND] Trying +{len(batch)} fields: {', '.join(batch)}...")
                    try:
                        rows2 = read_table_simple(conn, tbl, expanded)
                        if rows2:
                            print(f"    [EXPAND] OK: {len(rows2):,} rows with {len(expanded)} fields")
                            load_to_sqlite(db, tbl, expanded, rows2)
                            extract_fields = expanded
                            results[tbl]["fields"] = len(expanded)
                    except Exception:
                        print(f"    [EXPAND] Failed at {len(expanded)} fields, keeping {len(extract_fields)}")
                        break

        except Exception as e:
            err = str(e)
            if "TABLE_WITHOUT_DATA" in err:
                print(f"    -> 0 rows")
                results[tbl] = {"rows": 0, "status": "EMPTY", "desc": desc}
            elif "NOT_AUTHORIZED" in err:
                print(f"    -> NOT AUTHORIZED")
                results[tbl] = {"rows": 0, "status": "NOT_AUTHORIZED", "desc": desc}
            else:
                print(f"    [ERROR] {err[:100]}")
                results[tbl] = {"rows": 0, "status": f"ERROR: {err[:80]}", "desc": desc}

        time.sleep(0.5)

    conn.close()
    db.close()

    # ── Summary ──
    print(f"\n  {'=' * 60}")
    print("  EBS CONFIG EXTRACTION SUMMARY")
    print(f"  {'=' * 60}")
    total_rows = 0
    for tbl, info in results.items():
        rows = info["rows"]
        status = info["status"]
        desc = info["desc"]
        total_rows += rows
        fields_str = f" ({info.get('fields', '?')} fields)" if rows > 0 else ""
        print(f"    {tbl:20s} -> {rows:>6,} rows  [{status}]{fields_str}  | {desc}")

    ok_count = sum(1 for v in results.values() if v["rows"] > 0)
    print(f"\n    TOTAL: {total_rows:,} rows across {ok_count} tables")
    print(f"    Gold DB: {DB_PATH}")

    # Key findings
    print(f"\n  KEY FINDINGS:")
    for tbl in ["FEBEP", "FEBKO"]:
        if tbl in results:
            if results[tbl]["status"] == "EMPTY_CONFIRMED":
                print(f"    {tbl}: CONFIRMED EMPTY — EBS posts directly to BKPF/BSIS (by design)")
            elif results[tbl]["rows"] > 0:
                print(f"    {tbl}: HAS DATA ({results[tbl]['rows']} rows) — EBS framework IS active!")

    for tbl in ["YBASUBST", "YTFI_BA_SUBST"]:
        if tbl in results and results[tbl]["rows"] > 0:
            print(f"    {tbl}: {results[tbl]['rows']} entries — BA substitution config extracted")

    print("  Done.\n")


if __name__ == "__main__":
    main()
