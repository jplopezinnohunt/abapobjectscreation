"""
extract_ebs_d01_session71.py
=============================
Extract current EBS customizing tables from D01 to validate INC-000008088 routing
state. Compares against the user's screenshot evidence in P01.

Tables: T028V, T028G, T028B, T033F, T033G, T028D
Output: Gold DB at p01_gold_master_data.db with table prefix d01_
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
        if "TABLE_WITHOUT_DATA" in err:
            return []
        if "NOT_AUTHORIZED" in err:
            print(f"    [AUTH] Not authorized for {table}")
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
    print("\n  D01 EBS Customizing Extraction (Session #071)")
    print("  " + "=" * 60)

    conn = get_connection("D01")
    print("  Connected to D01.\n")

    db = sqlite3.connect(str(DB_PATH))

    # Tables relevant to INC-000008088
    target_tables = [
        ("T028V", ["VGTYP"]),                    # VGTYP catalog (label only)
        ("T028D", ["VGINT"]),                    # Posting rule key catalog
        ("T028G", ["VGTYP", "VGEXT", "VOZPM", "VGINT", "PFORM", "INTAG"]),  # Routing matrix
        ("T028B", ["BANKL", "KTONR", "VGTYP", "BUKRS", "BNKKO"]),           # Bank → VGTYP binding
        ("T033F", ["ANWND", "EIGR1", "BSCH1", "SHBK1", "KTOS1"]),           # Posting rules
        ("T033G", ["ANWND", "KTOPL", "KTOSY", "KOMO1", "KOMO2", "KONTO"]),  # Symbol → GL mask
    ]

    results = {}
    for tbl, fields in target_tables:
        print(f"\n  Extracting {tbl} ({len(fields)} fields)...")
        try:
            # First probe full field list
            dd_fields = probe_fields(conn, tbl)
            full_fields = [f["FIELDNAME"] for f in dd_fields if f["FIELDNAME"] != "MANDT"][:8]
            if not full_fields:
                full_fields = fields
            rows = read_table_simple(conn, tbl, full_fields)
            target_name = f"d01_{tbl.lower()}"
            load_to_sqlite(db, target_name, full_fields, rows)
            results[tbl] = {"rows": len(rows), "status": "OK", "saved_as": target_name}
            print(f"    -> {len(rows):,} rows saved to {target_name}")
        except Exception as e:
            err = str(e)[:120]
            print(f"    [ERR] {err}")
            results[tbl] = {"rows": 0, "status": "ERROR", "err": err}
        time.sleep(0.3)

    db.close()

    print("\n  " + "=" * 60)
    print("  Summary:")
    for tbl, info in results.items():
        print(f"    {tbl:8s} {info.get('status'):10s} rows={info.get('rows', 0)}")


if __name__ == "__main__":
    main()
