"""Probe additional workflow-related tables for N_MENARD authorship."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402


def probe(g, table, where_lines, fields, rowcount=10):
    options = []
    for i, w in enumerate(where_lines):
        suffix = " AND" if i < len(where_lines) - 1 else ""
        options.append({"TEXT": w + suffix})
    try:
        r = g.call(
            "RFC_READ_TABLE",
            QUERY_TABLE=table, DELIMITER="|",
            OPTIONS=options,
            FIELDS=[{"FIELDNAME": f} for f in fields],
            ROWCOUNT=rowcount,
        )
        cols = [f["FIELDNAME"] for f in r["FIELDS"]]
        rows = [dict(zip(cols, [v.strip() for v in row["WA"].split("|")])) for row in r["DATA"]]
        return len(rows), rows
    except Exception as e:
        return f"ERR: {e}", []


def main():
    g = ConnectionGuard("D01"); g.connect()
    try:
        # What OTYPEs does N_MENARD appear under?
        print("== HRP1000 UNAME=N_MENARD, distinct OTYPE sample ==")
        n, rows = probe(g, "HRP1000", ["UNAME = 'N_MENARD'"],
                        ["OTYPE", "OBJID", "SHORT", "STEXT", "AEDTM"], 40)
        print(f"  {n} rows")
        otypes = {}
        for r in rows:
            otypes.setdefault(r["OTYPE"], []).append(r)
        for ot, rs in otypes.items():
            print(f"  OTYPE={ot}: {len(rs)} — example: OBJID={rs[0]['OBJID']} SHORT={rs[0]['SHORT']} STEXT={rs[0]['STEXT']}")

        # SWD_HEADER — workflow definition table used by SWDD
        print("\n== SWD_HEADER for N_MENARD ==")
        n, rows = probe(g, "SWD_HEADER",
                        ["CREATOR = 'N_MENARD'"],
                        ["TASK", "VERSION", "CREATOR", "CRDATE", "CHANGER", "CHDATE", "TEXT"], 50)
        print(f"  CREATOR: {n}")
        for r in rows[:5] if isinstance(rows, list) else []:
            print(f"    {r}")
        n, rows = probe(g, "SWD_HEADER",
                        ["CHANGER = 'N_MENARD'"],
                        ["TASK", "VERSION", "CREATOR", "CRDATE", "CHANGER", "CHDATE", "TEXT"], 50)
        print(f"  CHANGER: {n}")
        for r in rows[:10] if isinstance(rows, list) else []:
            print(f"    {r}")

        # TADIR — repository objects, look for PDTS/PDWS objects by N_MENARD
        # PDWS = WS workflow, PDTS = standard task
        print("\n== TADIR PDWS/PDTS for N_MENARD ==")
        for pgmid_type in [("R3TR", "PDWS"), ("R3TR", "PDTS")]:
            n, rows = probe(g, "TADIR",
                            [f"PGMID = '{pgmid_type[0]}'",
                             f"OBJECT = '{pgmid_type[1]}'",
                             "AUTHOR = 'N_MENARD'"],
                            ["OBJECT", "OBJ_NAME", "AUTHOR", "DEVCLASS", "CREATED_ON", "CHANGED_ON"], 50)
            print(f"  {pgmid_type}: {n}")
            for r in rows[:20] if isinstance(rows, list) else []:
                print(f"    {r['OBJECT']} {r['OBJ_NAME']} pkg={r['DEVCLASS']} created={r['CREATED_ON']}")
    finally:
        g.close()


if __name__ == "__main__":
    main()
