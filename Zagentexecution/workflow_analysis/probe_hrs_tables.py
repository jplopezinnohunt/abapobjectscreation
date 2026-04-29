"""Probe HRS1201, HRS1217, HRS1222 for N_MENARD's 9 WS templates.
Also scan TFDIR for any RFC-enabled function starting SWD_ / RH_WF / SWU_ /SAP_WAPI_
that could dump a workflow definition."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402

WS_IDS = ["98100016","98100018","98100019","98100020","98100021",
          "98100022","98100023","98100026","98100027"]


def rread(g, table, where, fields, rowcount=10):
    opts=[]
    for i,w in enumerate(where):
        opts.append({"TEXT": w + (" AND" if i<len(where)-1 else "")})
    try:
        r = g.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                   OPTIONS=opts, FIELDS=[{"FIELDNAME":f} for f in fields],
                   ROWCOUNT=rowcount)
        cols=[f["FIELDNAME"] for f in r["FIELDS"]]
        return [dict(zip(cols,[v for v in row["WA"].split("|")])) for row in r["DATA"]]
    except Exception as e:
        return f"ERR: {e}"


def main():
    g = ConnectionGuard("D01"); g.connect()
    try:
        # 1. HRS1201 text lines for the 9 WS
        print("== HRS1201 (task text) for N_MENARD WS ==")
        for wsid in WS_IDS:
            rows = rread(g, "HRS1201",
                         [f"OBJID = '{wsid}'", "OTYPE = 'WS'"],
                         ["OBJID","OTYPE","STEXT","LANGU","SHORT"], 5)
            print(f"  WS {wsid}: {rows}")

        # 2. Discover RFC-enabled workflow functions via TFDIR
        print("\n== TFDIR RFC functions matching workflow patterns ==")
        for pattern in ["SWD_%", "RH_WF%", "SAP_WAPI_READ%", "SWU_WFD%",
                        "SWW_WI_READ%", "RH_GET_WF%", "SWP_%"]:
            rows = rread(g, "TFDIR",
                         [f"FUNCNAME LIKE '{pattern}'", "FMODE = 'R'"],
                         ["FUNCNAME","PNAME"], 50)
            if isinstance(rows, list) and rows:
                print(f"  {pattern}: {len(rows)} fn")
                for r in rows[:20]:
                    print(f"    {r['FUNCNAME']}  pname={r['PNAME'].strip()}")

        # 3. HRS1217 — check the key structure and first 20 bytes of blob
        print("\n== HRS1217 schema ==")
        rows = rread(g, "DD03L",
                     ["TABNAME = 'HRS1217'", "FIELDNAME <> '.INCLUDE'"],
                     ["FIELDNAME","POSITION","DATATYPE","LENG"], 30)
        if isinstance(rows, list):
            for r in rows:
                print(f"  pos={r['POSITION'].strip()} {r['FIELDNAME'].strip():20} {r['DATATYPE'].strip():8} len={r['LENG'].strip()}")

        # 4. HRS1222 schema
        print("\n== HRS1222 schema ==")
        rows = rread(g, "DD03L",
                     ["TABNAME = 'HRS1222'", "FIELDNAME <> '.INCLUDE'"],
                     ["FIELDNAME","POSITION","DATATYPE","LENG"], 30)
        if isinstance(rows, list):
            for r in rows:
                print(f"  pos={r['POSITION'].strip()} {r['FIELDNAME'].strip():20} {r['DATATYPE'].strip():8} len={r['LENG'].strip()}")

        # 5. HRS1201 schema
        print("\n== HRS1201 schema ==")
        rows = rread(g, "DD03L",
                     ["TABNAME = 'HRS1201'", "FIELDNAME <> '.INCLUDE'"],
                     ["FIELDNAME","POSITION","DATATYPE","LENG"], 30)
        if isinstance(rows, list):
            for r in rows:
                print(f"  pos={r['POSITION'].strip()} {r['FIELDNAME'].strip():20} {r['DATATYPE'].strip():8} len={r['LENG'].strip()}")
    finally:
        g.close()


if __name__ == "__main__":
    main()
