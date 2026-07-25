"""
extract_setleaf_ybank.py
=========================
Extract SETLEAF / SETNODE / SETHEADER / SETHEADERT for the YBANK_ACCOUNTS_*
family from P01 -> Gold DB (p01_gold_master_data.db).

Context: INC-000006906 + INC-000005586. The Gold DB has T012 / T012K / SKA*
but no SET* tables. We extract only the YBANK_ACCOUNTS_* family to keep the
extract minimal.
"""

import os
import sys
import sqlite3

MCP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP_DIR))
from rfc_helpers import get_connection

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD_DB = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction",
                      "sqlite", "p01_gold_master_data.db")


def read_all(conn, table, fields, where, batch_size=2000):
    """Return (rows_as_list_of_list, headers)."""
    rfc_fields = [{"FIELDNAME": f} for f in fields] if fields else []
    rfc_opts = [{"TEXT": where}] if where else []
    offset = 0
    all_rows = []
    headers = None
    while True:
        res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                        ROWCOUNT=batch_size, ROWSKIPS=offset,
                        OPTIONS=rfc_opts, FIELDS=rfc_fields)
        hdrs = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
        if headers is None:
            headers = hdrs
        raw = res.get("DATA", [])
        for row in raw:
            parts = row["WA"].split("|")
            all_rows.append([parts[i].strip() if i < len(parts) else "" for i in range(len(headers))])
        got = len(raw)
        print(f"    {table} offset={offset}: {got} rows (running {len(all_rows)})")
        if got < batch_size:
            break
        offset += batch_size
    return all_rows, headers or fields


def persist(sql_db, table, rows, headers):
    cur = sql_db.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {table}")
    cols = ", ".join(f'"{h}" TEXT' for h in headers)
    cur.execute(f"CREATE TABLE {table} ({cols})")
    ph = ",".join("?" * len(headers))
    cur.executemany(f"INSERT INTO {table} VALUES ({ph})", rows)
    sql_db.commit()
    print(f"    persisted {len(rows)} rows into {table}  cols={headers}")


def main():
    conn = get_connection("P01")
    sql_db = sqlite3.connect(GOLD_DB)
    try:
        # Note: underscore is a LIKE wildcard; use YBANK% pattern then filter
        # in SQLite post-load (all YBANK* sets in this system are YBANK_ACCOUNTS_*)
        where = "SETNAME LIKE 'YBANK%'"

        # SETLEAF — pin down minimal fields
        leaf_fields = ["MANDT", "SETCLASS", "SUBCLASS", "SETNAME",
                       "LINEID", "VALSIGN", "VALOPTION", "VALFROM", "VALTO", "SEQNR"]
        print("\n==> SETLEAF")
        rows, hdrs = read_all(conn, "SETLEAF", leaf_fields, where)
        persist(sql_db, "SETLEAF", rows, hdrs)

        # SETNODE — minimal fields
        node_fields = ["MANDT", "SETCLASS", "SUBCLASS", "SETNAME",
                       "LINEID", "SUBSETCLS", "SUBSETSCLS", "SUBSETNAME"]
        print("\n==> SETNODE")
        rows, hdrs = read_all(conn, "SETNODE", node_fields, where)
        persist(sql_db, "SETNODE", rows, hdrs)

        # SETHEADER — take all fields (23)
        print("\n==> SETHEADER")
        rows, hdrs = read_all(conn, "SETHEADER", [], where)
        persist(sql_db, "SETHEADER", rows, hdrs)

        # SETHEADERT — text
        print("\n==> SETHEADERT")
        rows, hdrs = read_all(conn, "SETHEADERT", [], where)
        persist(sql_db, "SETHEADERT", rows, hdrs)
    finally:
        sql_db.close()


if __name__ == "__main__":
    main()
