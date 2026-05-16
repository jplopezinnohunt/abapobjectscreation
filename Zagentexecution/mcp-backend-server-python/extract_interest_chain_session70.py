"""
extract_interest_chain_session70.py
====================================
Session #070 — Pull T030/T030B (OB09), T028H/I (EBS posting-rule → GL determination),
T044A (valuation methods), and any remaining T030* fallback tables for the
interest auto-posting + revaluation chain.

Source: P01 (production, SNC/SSO read-only)
Output: Gold DB at p01_gold_master_data.db (full refresh per table)
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
            return _read_split(conn, table, fields, rfc_options, max_rows)
        if "TABLE_WITHOUT_DATA" in err:
            return []
        if "NOT_AUTHORIZED" in err:
            print(f"    [AUTH] Not authorized for {table}")
            return []
        if "TABLE_NOT_AVAILABLE" in err:
            print(f"    [N/A] {table} not available")
            return []
        raise


def _parse_result(result, fields):
    raw = result.get("DATA", [])
    hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
    rows = []
    for row in raw:
        parts = row["WA"].split("|")
        rows.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)})
    return rows


def _read_split(conn, table, fields, rfc_options, max_rows):
    for chunk_size in [4, 3, 2]:
        chunks = [fields[i:i + chunk_size] for i in range(0, len(fields), chunk_size)]
        all_data = None
        success = True
        for chunk in chunks:
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
            print(f"    [SPLIT] {len(all_data)} rows via {chunk_size}-field chunks")
            return all_data
    return []


def probe_fields(conn, table):
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
    print("\n  Interest-chain Extraction — P01 (Session #070)")
    print("  " + "=" * 60)

    conn = get_connection("P01")
    print("  Connected to P01 (SNC/SSO).\n")

    db = sqlite3.connect(str(DB_PATH))
    results = {}

    # OB09 + revaluation fallback + EBS account determination + valuation methods
    target_tables = [
        # OB09 / OBA1 chain
        "T030",      # Standard accounts (Trans key + chart → GL)
        "T030B",     # Standard accounts per currency
        "T030D",     # Account determination for FX clearing
        "T030F",     # Special G/L → reconciliation
        "T030R",     # FX rate determination per chart
        "T030S",     # Carry forward
        "T030U",     # Special G/L indicator account determination
        # Valuation
        "T044A",     # Valuation methods (KU-2026-070-01)
        # EBS posting-rule → GL (the missing link from earlier analysis)
        "T028H",     # EBS posting rule → GL determination
        "T028I",     # EBS internal table (sometimes referenced)
        "T028C",     # EBS additional rules
        # OBV2 / interest scale (legacy but may still be active for accrual)
        "T056",      # Interest indicator
        "T056A",     # Interest indicator names
        "T056P",     # Interest scale: postings
        "T056Z",     # Interest scale: rate
    ]

    print("  Phase 1: Probe DD03L for each table\n")
    field_map = {}
    for tbl in target_tables:
        dd_fields = probe_fields(conn, tbl)
        if dd_fields:
            names = [f["FIELDNAME"] for f in dd_fields if f["FIELDNAME"] != "MANDT"]
            field_map[tbl] = names
            print(f"    {tbl:8s} -> {len(names):>3} fields: {', '.join(names[:8])}{'...' if len(names) > 8 else ''}")
        else:
            field_map[tbl] = []
            print(f"    {tbl:8s} -> NOT FOUND or no access")
        time.sleep(0.2)

    print(f"\n  Phase 2: Extract\n")
    for tbl in target_tables:
        if not field_map.get(tbl):
            print(f"  [{tbl:8s}] SKIP — no fields")
            results[tbl] = {"rows": 0, "status": "NOT_FOUND"}
            continue
        extract_fields = field_map[tbl][:8]
        print(f"  [{tbl:8s}] Extracting {len(extract_fields)}/{len(field_map[tbl])} fields: {', '.join(extract_fields[:6])}...")
        try:
            rows = read_table_simple(conn, tbl, extract_fields)
            print(f"    -> {len(rows):,} rows")
            load_to_sqlite(db, tbl, extract_fields, rows)
            results[tbl] = {"rows": len(rows), "status": "OK", "fields": len(extract_fields)}
            # Expand
            if rows and len(extract_fields) < len(field_map[tbl]):
                remaining = [f for f in field_map[tbl] if f not in extract_fields]
                for batch_start in range(0, len(remaining), 4):
                    batch = remaining[batch_start:batch_start + 4]
                    expanded = extract_fields + batch
                    try:
                        rows2 = read_table_simple(conn, tbl, expanded)
                        if rows2:
                            load_to_sqlite(db, tbl, expanded, rows2)
                            extract_fields = expanded
                            results[tbl]["fields"] = len(expanded)
                    except Exception:
                        break
                print(f"    [EXPAND] Final: {results[tbl]['fields']} fields")
        except Exception as e:
            err = str(e)
            if "TABLE_WITHOUT_DATA" in err:
                print(f"    -> 0 rows")
                results[tbl] = {"rows": 0, "status": "EMPTY"}
            else:
                print(f"    [ERR] {err[:120]}")
                results[tbl] = {"rows": 0, "status": "ERROR", "err": err[:120]}
        time.sleep(0.3)

    db.close()
    print("\n  " + "=" * 60)
    print("  Summary:")
    for tbl, info in results.items():
        print(f"    {tbl:8s} {info.get('status'):20s} rows={info.get('rows', 0)} fields={info.get('fields', '-')}")


if __name__ == "__main__":
    main()
