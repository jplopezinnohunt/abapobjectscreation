"""
extract_cmod_inventory.py
=========================
Closes the CMOD inventory gap flagged by custom_extension_census_check (s111):
the classic user-exit census was known only through the code we extracted, not
from the system's own registry.

  MODACT   CMOD projects and their activation status
  MODSAP   project -> SMOD enhancement / component assignment (the actual wiring)
  MODATTR  project attributes: author, dates, status (who created what, when)

Read-only: RFC_READ_TABLE over SNC/SSO on P01. Tiny tables, extracted in full.
Empty is itself evidence and is recorded in the manifest.

Output: lowercase SQLite tables in p01_gold_master_data.db (bare name = P01
provenance) + rows in _config_frontier_manifest (grp='cmod_inventory').

Run:
    python extract_cmod_inventory.py
"""

import os
import sys
import sqlite3
from datetime import datetime

MCP = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP))
from rfc_helpers import get_connection  # noqa: E402

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD_DB = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")

TABLES = ["MODACT", "MODSAP", "MODATTR"]
GRP = "cmod_inventory"


def get_fields(conn, table):
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                    ROWCOUNT=1, OPTIONS=[], FIELDS=[])
    return [f["FIELDNAME"] for f in res.get("FIELDS", [])]


def load_to_sqlite(db, table, rows, fields):
    tbl = table.lower()
    cols = ", ".join([f'"{f}" TEXT' for f in fields])
    db.execute(f"DROP TABLE IF EXISTS {tbl}")
    db.execute(f"CREATE TABLE {tbl} ({cols})")
    if rows:
        ph = ", ".join(["?"] * len(fields))
        col_list = ", ".join([f'"{f}"' for f in fields])
        db.executemany(f"INSERT INTO {tbl} ({col_list}) VALUES ({ph})",
                       [tuple(r.get(f, "") for f in fields) for r in rows])
    db.commit()


def record(db, tabname, n_fields, n_rows, sqlite_table, ts):
    db.execute("DELETE FROM _config_frontier_manifest WHERE tabname=? AND system='P01'", (tabname,))
    db.execute("INSERT INTO _config_frontier_manifest VALUES (?,?,?,?,?,?,?,?,?)",
               (GRP, tabname, "P01", "Y", n_fields, n_rows, sqlite_table,
                "CMOD classic user-exit inventory (census gap closed s111)", ts))
    db.commit()


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"=== CMOD inventory | P01 | {ts} ===")
    conn = get_connection("P01")
    db = sqlite3.connect(GOLD_DB)

    for table in TABLES:
        fields = get_fields(conn, table)
        # P01 rejects ROWSKIPS ("requires GET_SORTED") on some tables — these are tiny,
        # so read in ONE call, no pagination, cutting rows by FIELDS offset/length.
        res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="",
                        ROWCOUNT=99999, OPTIONS=[],
                        FIELDS=[{"FIELDNAME": f} for f in fields])
        meta = res.get("FIELDS", [])
        rows = []
        for raw in res.get("DATA", []):
            line = raw.get("WA", "")
            rows.append({m["FIELDNAME"]: line[int(m["OFFSET"]):int(m["OFFSET"]) + int(m["LENGTH"])].rstrip()
                         for m in meta})
        load_to_sqlite(db, table, rows, fields)
        record(db, table, len(fields), len(rows), table.lower(), ts)
        print(f"  {table}: {len(rows)} rows, fields: {fields}")

    db.close()
    print("DONE")


if __name__ == "__main__":
    main()
