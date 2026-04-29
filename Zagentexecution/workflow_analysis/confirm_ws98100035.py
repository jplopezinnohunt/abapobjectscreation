"""Confirm creator + Return outcome for WS98100035 (the workflow in the screenshot)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402


def rr(g, table, where, fields, rc=2000):
    opts=[{"TEXT":w+(" AND" if i<len(where)-1 else "")} for i,w in enumerate(where)]
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
        wfd = "WS98100035"

        print(f"=== WS98100035 header ===")
        h = rr(g, "SWDSHEADER", [f"WFD_ID = '{wfd}'"],
               ["WFD_ID","VERSION","STATUS","CREATED_BY","CREATED_ON","CHANGED_BY","CHANGED_ON"], 10)
        for r in h if isinstance(h,list) else []:
            print(f"  v{r['VERSION']}: status='{r['STATUS']}' cr={r['CREATED_BY']} {r['CREATED_ON']} ch={r['CHANGED_BY']} {r['CHANGED_ON']}")

        print(f"\n=== WS98100035 title (WFD_TEXT HD) ===")
        t = rr(g, "SWDSTEXT", [f"WFD_ID = '{wfd}'","LANGUAGE = 'E'","TEXTTYP = 'HD'"],
               ["VERSION","WFD_TEXT"], 10)
        for r in t if isinstance(t,list) else []:
            print(f"  v{r['VERSION']}: {r['WFD_TEXT']}")

        print(f"\n=== WS98100035 all SHORTTEXT='Return' container hits ===")
        rows = rr(g, "SWDSWFCTXT",
                  [f"WFD_ID = '{wfd}'","LANGUAGE = 'E'", "SHORTTEXT = 'Return'"],
                  ["VERSION","NODEID","CNT_TYPE","CNT_SUBTYPE","ELEMENT","SHORTTEXT"], 50)
        for r in rows if isinstance(rows,list) else []:
            print(f"  v{r['VERSION']} node={r['NODEID']} cnt={r['CNT_TYPE']}/{r['CNT_SUBTYPE']} elem={r['ELEMENT']} short='{r['SHORTTEXT']}'")

        # also scan at node level for step 46 specifically
        print(f"\n=== WS98100035 step 0000000046 container elements (EN) ===")
        rows = rr(g, "SWDSWFCTXT",
                  [f"WFD_ID = '{wfd}'","LANGUAGE = 'E'", "NODEID = '0000000046'"],
                  ["VERSION","NODEID","CNT_TYPE","CNT_SUBTYPE","ELEMENT","DESCRIPT","SHORTTEXT"], 50)
        for r in rows if isinstance(rows,list) else []:
            print(f"  v{r['VERSION']} elem={r['ELEMENT']:20} cnt={r['CNT_TYPE']}/{r['CNT_SUBTYPE']:3} desc='{r['DESCRIPT']}' short='{r['SHORTTEXT']}'")

        # Step 46 details
        print(f"\n=== WS98100035 SWDSDSTEPS node 0000000046 ===")
        rows = rr(g, "SWDSDSTEPS",
                  [f"WFD_ID = '{wfd}'","NODEID = '0000000046'"],
                  ["VERSION","NODEID","EXETYP","FORM_OTYPE","FORM_METHD","FORM_NAME","CREATED_BY","CREATED_ON","CHANGED_BY","CHANGED_ON"], 10)
        for r in rows if isinstance(rows,list) else []:
            print(f"  v{r['VERSION']} exetyp={r['EXETYP']} form={r['FORM_NAME']} ({r['FORM_METHD']}) cr={r['CREATED_BY']} {r['CREATED_ON']} ch={r['CHANGED_BY']} {r['CHANGED_ON']}")

        # Who created/changed ALL steps of WS98100035?
        print(f"\n=== WS98100035 distinct step authors ===")
        rows = rr(g, "SWDSDSTEPS", [f"WFD_ID = '{wfd}'"],
                  ["NODEID","CREATED_BY","CHANGED_BY"], 3000)
        if isinstance(rows, list):
            cr = {}
            ch = {}
            for r in rows:
                cr[r["CREATED_BY"]] = cr.get(r["CREATED_BY"],0)+1
                ch[r["CHANGED_BY"]] = ch.get(r["CHANGED_BY"],0)+1
            print(f"  CREATED_BY counts: {cr}")
            print(f"  CHANGED_BY counts: {ch}")
    finally:
        g.close()


if __name__ == "__main__":
    main()
