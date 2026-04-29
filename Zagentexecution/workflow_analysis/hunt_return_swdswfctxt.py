"""Hunt 'Return' in SWDSWFCTXT (container element text per node).
This is where User Decision outcome Names live.
"""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
N_MENARD_WS_IDS = ["WS98100016","WS98100018","WS98100019","WS98100020",
                   "WS98100021","WS98100022","WS98100023","WS98100026","WS98100027"]


def rr(g, table, where, fields, rc=5000):
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
        report = {}
        for wfd in N_MENARD_WS_IDS:
            hits_all = []
            # Try all casings / variants
            for label in ["Return","RETURN","return","Reject","Rejected","Send back","Send Back"]:
                rows = rr(g, "SWDSWFCTXT",
                          [f"WFD_ID = '{wfd}'",
                           "LANGUAGE = 'E'",
                           f"SHORTTEXT = '{label}'"],
                          ["WFD_ID","VERSION","NODEID","CNT_TYPE","CNT_SUBTYPE",
                           "ELEMENT","DESCRIPT","SHORTTEXT"], 200)
                if isinstance(rows, list) and rows:
                    for r in rows:
                        r["_label_queried"] = label
                    hits_all.extend(rows)
            print(f"\n=== {wfd}: {len(hits_all)} SHORTTEXT hits for Return/Reject/Send back ===")
            nodes_seen = set()
            for r in hits_all:
                key=(r["NODEID"], r["VERSION"], r["SHORTTEXT"])
                if key in nodes_seen: continue
                nodes_seen.add(key)
                print(f"  v{r['VERSION']} node={r['NODEID']} elem={r['ELEMENT']} type={r['CNT_TYPE']}/{r['CNT_SUBTYPE']} short='{r['SHORTTEXT']}' desc='{r['DESCRIPT']}'")
            report[wfd] = hits_all

            # For nodes with Return — fetch the step detail
            if hits_all:
                node_ids = sorted(set(r["NODEID"] for r in hits_all))
                for n in node_ids:
                    sr = rr(g, "SWDSDSTEPS",
                            [f"WFD_ID = '{wfd}'", f"NODEID = '{n}'"],
                            ["WFD_ID","VERSION","NODEID","EXETYP","FORM_OTYPE","FORM_METHD","FORM_NAME"], 5)
                    if isinstance(sr, list):
                        for s in sr:
                            print(f"    STEP node={s['NODEID']} v={s['VERSION']} exetyp={s['EXETYP']} form={s['FORM_NAME']} ({s['FORM_METHD']})")

        # Per-workflow description (WFD title, English)
        print("\n=== Workflow descriptions (EN) ===")
        for wfd in N_MENARD_WS_IDS:
            rows = rr(g, "SWDSTEXT",
                      [f"WFD_ID = '{wfd}'", "LANGUAGE = 'E'", "TEXTTYP = '01'"],
                      ["WFD_ID","VERSION","TEXTTYP","TEXTNUMBER","WFD_TEXT"], 5)
            if isinstance(rows, list):
                for r in rows[:3]:
                    print(f"  {wfd} v{r['VERSION']} textno={r['TEXTNUMBER']}: {r['WFD_TEXT']}")

        with open(os.path.join(OUT,"return_outcomes_final.json"),"w",encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nwrote return_outcomes_final.json")
    finally:
        g.close()


if __name__ == "__main__":
    main()
