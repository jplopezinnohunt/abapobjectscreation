"""Find WHERE the 9 WS templates actually live — different client? different table?"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402

WS = "98100016"  # use one for probing


def rr(g, table, where, fields, rc=10):
    opts=[{"TEXT": w+(" AND" if i<len(where)-1 else "")} for i,w in enumerate(where)]
    try:
        r=g.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                 OPTIONS=opts, FIELDS=[{"FIELDNAME":f} for f in fields], ROWCOUNT=rc)
        cols=[f["FIELDNAME"] for f in r["FIELDS"]]
        return [dict(zip(cols,[v.strip() for v in row["WA"].split("|")])) for row in r["DATA"]]
    except Exception as e:
        return f"ERR: {e}"


def main():
    g = ConnectionGuard("D01"); g.connect()
    try:
        # 1. Loose HRP1000 query — any PLVAR, any OTYPE, just the OBJID
        print(f"== HRP1000 OBJID = {WS} (any OTYPE, any PLVAR) ==")
        rows = rr(g, "HRP1000", [f"OBJID = '{WS}'"],
                  ["OTYPE","OBJID","PLVAR","ISTAT","BEGDA","ENDDA","UNAME","SHORT","STEXT"], 20)
        print(f"  {rows}")

        # 2. TADIR for R3TR PDWS with this OBJ_NAME
        print(f"\n== TADIR R3TR PDWS OBJ_NAME={WS} ==")
        rows = rr(g, "TADIR",
                  ["PGMID = 'R3TR'", "OBJECT = 'PDWS'", f"OBJ_NAME = '{WS}'"],
                  ["OBJ_NAME","AUTHOR","DEVCLASS","CREATED_ON","CHANGED_ON","DELFLAG"], 5)
        print(f"  {rows}")

        # 3. Check PD variants that exist
        print(f"\n== T778P (PD variants) ==")
        rows = rr(g, "T778P", [], ["PLVAR","PTEXT"], 10)
        print(f"  {rows}")

        # 4. Check if workflow is in SWD_HEADER (not the view — try with direct field match)
        print(f"\n== SWD_HEADER for {WS} ==")
        rows = rr(g, "SWD_HEADER", [f"TASK = 'WS{WS}'"],
                  ["TASK","VERSION","CREATOR","CHANGER","CRDATE","CHDATE"], 10)
        print(f"  {rows}")

        # 5. Scan the tables whose name starts HRS1 — what exists in this release
        print(f"\n== DD02L: HRS1% tables ==")
        rows = rr(g, "DD02L", ["TABNAME LIKE 'HRS1%'", "TABCLASS = 'TRANSP'"],
                  ["TABNAME","AS4LOCAL"], 40)
        print(f"  {rows}")

        # 6. Scan for HRSOBJECT too
        print(f"\n== DD02L: HRSOBJECT & HRPAD% & SWD% ==")
        for pat in ["HRSOBJECT", "HRPAD%", "SWD_%", "HRP1%"]:
            rows = rr(g, "DD02L", [f"TABNAME LIKE '{pat}'", "TABCLASS = 'TRANSP'"],
                      ["TABNAME"], 40)
            if isinstance(rows, list):
                names = [r["TABNAME"] for r in rows]
                print(f"  {pat}: {names[:25]}")
    finally:
        g.close()


if __name__ == "__main__":
    main()
