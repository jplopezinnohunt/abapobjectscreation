"""
extract_yfmxchk_control_tables.py
==================================
Pulls the three custom control tables behind the posting-perimeter gates that the
brain flagged as unlanded (s110 pending block, unlanded_discovery_detector):

  YFMXCHK   special-budget-code funds  — read by YRGGBS00::U913 (FI validation,
            step 002 VALID='UNES'), ZXFMDTU02 (FMDERIVE), ZXFMYU22, YFM_ACCTCHK.
            A fund listed here with XCHECK='T' makes U913 return TRUE.
  YFMXCHKP  the UNESCO FM fiscal gate — CHTYP ('FY','BB','BE') x BUKRS x GJAHR x
            MONAT x ACTIV: blocks postings regardless of OB52.
  YXUSER    the bypass table — XTYPE ('FM','FRTL','BC') x UNAME: users allowed to
            skip the gates. U913 checks XTYPE='BC'.

Read-only: RFC_READ_TABLE over SNC/SSO on P01. Tables are tiny; extracted in full.
Empty is itself evidence and is recorded in the manifest.

Output: lowercase SQLite tables in p01_gold_master_data.db (bare name = P01
provenance) + rows in _config_frontier_manifest (grp='posting_gate_controls').

Run:
    python extract_yfmxchk_control_tables.py
"""

import os
import sys
import sqlite3
from datetime import datetime

MCP = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD_DB = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")

TABLES = ["YFMXCHK", "YFMXCHKP", "YXUSER"]
GRP = "posting_gate_controls"


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
        batch = [tuple(r.get(f, "") for f in fields) for r in rows]
        db.executemany(f"INSERT INTO {tbl} ({col_list}) VALUES ({ph})", batch)
    db.commit()


def record(db, tabname, n_fields, n_rows, sqlite_table, note, ts):
    db.execute("""
        CREATE TABLE IF NOT EXISTS _config_frontier_manifest (
            grp TEXT, tabname TEXT, system TEXT, exists_in_catalog TEXT,
            n_fields INTEGER, n_rows INTEGER, sqlite_table TEXT,
            note TEXT, extracted_at TEXT
        )""")
    db.execute("DELETE FROM _config_frontier_manifest WHERE tabname=? AND system='P01'", (tabname,))
    db.execute("INSERT INTO _config_frontier_manifest VALUES (?,?,?,?,?,?,?,?,?)",
               (GRP, tabname, "P01", "Y", n_fields, n_rows, sqlite_table, note, ts))
    db.commit()


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"=== Posting-gate control tables | P01 | {ts} ===")
    conn = get_connection("P01")
    db = sqlite3.connect(GOLD_DB)

    for table in TABLES:
        fields = get_fields(conn, table)
        rows = rfc_read_paginated(conn, table, fields=fields, where=[], throttle=0.5)
        load_to_sqlite(db, table, rows, fields)
        record(db, table, len(fields), len(rows), table.lower(),
               "posting-perimeter gate control table (U913/ZXFMDTU02/ZXFMYU22/YFM_ACCTCHK)", ts)
        print(f"  {table}: {len(rows)} rows, {len(fields)} fields -> {table.lower()}")
        for r in rows[:60]:
            print("    " + " | ".join(f"{f}={r.get(f,'').strip()}" for f in fields))
        if len(rows) > 60:
            print(f"    ... ({len(rows)-60} more)")

    db.close()
    print("DONE")


if __name__ == "__main__":
    main()
