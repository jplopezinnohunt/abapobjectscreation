"""
Final Phase 2 — for N_MENARD's 9 WS templates:
  1. List all steps (SWDSDSTEPS) to find User Decision steps
  2. Query command texts (SWDPCMDT) for outcome labels = 'Return'
  3. Report which workflows contain a 'Return' outcome

Also: pick up any additional WFD_IDs authored by N_MENARD that we missed
(by querying SWDSDSTEPS CREATED_BY = 'N_MENARD').
"""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

N_MENARD_WS_IDS = [
    "WS98100016", "WS98100018", "WS98100019", "WS98100020",
    "WS98100021", "WS98100022", "WS98100023", "WS98100026", "WS98100027",
]


def rr(g, table, where, fields, rc=2000):
    opts = []
    for i, w in enumerate(where):
        opts.append({"TEXT": w + (" AND" if i < len(where) - 1 else "")})
    try:
        r = g.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                   OPTIONS=opts, FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=rc)
        cols = [f["FIELDNAME"] for f in r["FIELDS"]]
        return [dict(zip(cols, [v.strip() for v in row["WA"].split("|")])) for row in r["DATA"]]
    except Exception as e:
        return f"ERR: {e}"


def schema(g, table):
    rows = rr(g, "DD03L", [f"TABNAME = '{table}'", "FIELDNAME <> '.INCLUDE'"],
              ["FIELDNAME", "POSITION", "DATATYPE", "LENG", "KEYFLAG"], 40)
    if isinstance(rows, list):
        rows.sort(key=lambda r: int(r["POSITION"]) if r["POSITION"].isdigit() else 0)
    return rows


def main():
    g = ConnectionGuard("D01"); g.connect()
    try:
        # Discover the command-per-step linkage table. Typical name: SWDPPRCMD.
        print("== DD02L SWD*CMD* + SWD*TXT* ==")
        for pat in ["SWD%CMD%", "SWD%TXT%", "SWD%DEC%", "SWD%OUT%", "SWDS%", "SWDP%"]:
            rows = rr(g, "DD02L", [f"TABNAME LIKE '{pat}'", "TABCLASS = 'TRANSP'"],
                      ["TABNAME"], 40)
            if isinstance(rows, list) and rows:
                print(f"  {pat}: {[r['TABNAME'] for r in rows]}")

        # Schema of anything that links step -> command / outcome
        for t in ["SWDPPRCMD", "SWDPPRCMEX", "SWDPTEXTS", "SWDSDSTEPS"]:
            print(f"\n== schema {t} ==")
            for r in schema(g, t):
                print(f"  {'K' if r['KEYFLAG']=='X' else ' '} pos={r['POSITION']:>4} {r['FIELDNAME']:20} {r['DATATYPE']:8} len={r['LENG']}")

        # Steps for the 9 WFD_IDs — get step counts and samples
        print("\n== SWDSDSTEPS steps per WFD_ID ==")
        all_steps = {}
        for wfd in N_MENARD_WS_IDS:
            rows = rr(g, "SWDSDSTEPS", [f"WFD_ID = '{wfd}'"],
                      ["WFD_ID", "VERSION", "NODEID", "FORM_OTYPE", "FORM_METHD",
                       "FORM_NAME", "CREATED_BY"], 500)
            if isinstance(rows, list):
                print(f"  {wfd}: {len(rows)} step rows. Creators: "
                      f"{sorted(set(r['CREATED_BY'] for r in rows))}")
                all_steps[wfd] = rows
            else:
                print(f"  {wfd}: {rows}")

        # Save for downstream parsing
        with open(os.path.join(OUT_DIR, "menard_steps_raw.json"), "w", encoding="utf-8") as f:
            json.dump(all_steps, f, indent=2, ensure_ascii=False)
        print(f"\nwrote menard_steps_raw.json ({sum(len(v) for v in all_steps.values())} rows)")
    finally:
        g.close()


if __name__ == "__main__":
    main()
