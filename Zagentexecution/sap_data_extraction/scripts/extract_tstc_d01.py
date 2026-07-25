"""
extract_tstc_d01.py
===================
Extract TSTC (transaction -> program) and TSTCT (transaction texts) from D01
into the Gold DB. These are standard definition tables (identical across systems
for SAP-delivered tcodes; Z tcodes are transported to D01), so D01 is a valid
read source. Purpose: feed the connective ingestor's TRANSACTION -EXECUTES_PROGRAM->
PROGRAM edge (closes the tcode->code hop, e.g. F.05 -> SAPF100).

Read-only. RFC_READ_TABLE (compliant, not affected by SAP Note 3255746).
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


def read_all(conn, table, fields, where=""):
    """Single unlimited call (ROWSKIPS=0). D01's enhanced RFC_READ_TABLE rejects
    ROWSKIPS paging without GET_SORTED, so we pull the whole (small) table at once."""
    rfc_fields = [{"FIELDNAME": f} for f in fields] if fields else []
    rfc_opts = [{"TEXT": where}] if where else []
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                    ROWCOUNT=0, ROWSKIPS=0,
                    OPTIONS=rfc_opts, FIELDS=rfc_fields)
    headers = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
    all_rows = []
    for row in res.get("DATA", []):
        parts = row["WA"].split("|")
        all_rows.append([parts[i].strip() if i < len(parts) else "" for i in range(len(headers))])
    print(f"    {table}: {len(all_rows)} rows")
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
    conn = get_connection("D01")
    sql_db = sqlite3.connect(GOLD_DB)
    try:
        # PROVENANCE: persisted as d01_* because the Gold DB is otherwise P01.
        # Transaction definitions are SAP-standard/system-invariant, so D01 is a
        # valid content source — but the name must never imply P01.
        print("\n==> TSTC (transaction -> program)  [D01 -> d01_tstc]")
        # keep fields narrow to stay under RFC_READ_TABLE 512-char row width
        rows, hdrs = read_all(conn, "TSTC", ["TCODE", "PGMNA", "MENUE"])
        persist(sql_db, "d01_tstc", rows, hdrs)

        print("\n==> TSTCT (transaction texts, English)  [D01 -> d01_tstct]")
        rows, hdrs = read_all(conn, "TSTCT", ["SPRSL", "TCODE", "TTEXT"],
                              where="SPRSL = 'E'")
        persist(sql_db, "d01_tstct", rows, hdrs)

        print("\n==> TSTCP (parameter/report tcodes)  [D01 -> d01_tstcp]")
        rows, hdrs = read_all(conn, "TSTCP", ["TCODE", "PARAM"])
        persist(sql_db, "d01_tstcp", rows, hdrs)

        # quick sanity: how many tcodes map to a program, and do our bkpf tcodes resolve?
        cur = sql_db.cursor()
        tot = cur.execute("SELECT COUNT(*) FROM d01_tstc").fetchone()[0]
        withprog = cur.execute("SELECT COUNT(*) FROM d01_tstc WHERE PGMNA <> ''").fetchone()[0]
        print(f"\n  d01_tstc: {tot} tcodes, {withprog} with a direct program (PGMNA).")
        sample = cur.execute(
            "SELECT TCODE, PGMNA FROM d01_tstc WHERE TCODE IN ('F.05','F110','FB01','OB09','ML81')"
        ).fetchall()
        print("  sample:", sample)
    finally:
        sql_db.close()
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
