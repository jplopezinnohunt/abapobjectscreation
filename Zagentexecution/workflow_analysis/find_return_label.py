"""Hunt for 'Return' outcome label across the 9 N_MENARD workflows.
Tries SWDSTEXT (most likely) and fallback tables.
"""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
N_MENARD_WS_IDS = [
    "WS98100016","WS98100018","WS98100019","WS98100020",
    "WS98100021","WS98100022","WS98100023","WS98100026","WS98100027",
]


def rr(g, table, where, fields, rc=2000):
    opts = [{"TEXT": w+(" AND" if i<len(where)-1 else "")} for i,w in enumerate(where)]
    try:
        r=g.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                 OPTIONS=opts, FIELDS=[{"FIELDNAME":f} for f in fields], ROWCOUNT=rc)
        cols=[f["FIELDNAME"] for f in r["FIELDS"]]
        return [dict(zip(cols,[v.strip() for v in row["WA"].split("|")])) for row in r["DATA"]]
    except Exception as e:
        return f"ERR: {e}"


def schema(g, table):
    rows = rr(g, "DD03L", [f"TABNAME = '{table}'", "FIELDNAME <> '.INCLUDE'"],
              ["FIELDNAME","POSITION","DATATYPE","LENG","KEYFLAG"], 40)
    if isinstance(rows, list):
        rows.sort(key=lambda r: int(r["POSITION"]) if r["POSITION"].isdigit() else 0)
    return rows


def main():
    g = ConnectionGuard("D01"); g.connect()
    try:
        # Schemas of text-bearing tables
        for t in ["SWDSTEXT", "SWDSWFCTXT", "SWDSCONDEF", "SWDSEXPR"]:
            print(f"\n== schema {t} ==")
            for r in schema(g, t):
                print(f"  {'K' if r['KEYFLAG']=='X' else ' '} pos={r['POSITION']:>4} {r['FIELDNAME']:20} {r['DATATYPE']:8} len={r['LENG']}")

        # Hunt Return labels in SWDSTEXT per workflow
        print("\n== SWDSTEXT: rows with TEXT = 'Return' for each N_MENARD WFD ==")
        summary = {}
        for wfd in N_MENARD_WS_IDS:
            # Include case-insensitive — but SAP RFC_READ_TABLE uses = only.
            # Try both casings and common variants.
            total = []
            for label in ["Return", "RETURN", "return"]:
                rows = rr(g, "SWDSTEXT",
                          [f"WFD_ID = '{wfd}'", f"TEXT = '{label}'"],
                          ["WFD_ID","VERSION","NODEID","LANGU","TEXT"], 50)
                if isinstance(rows, list):
                    total.extend(rows)
            print(f"  {wfd}: {len(total)} rows w/ TEXT='Return'")
            for r in total[:10]:
                print(f"    node={r['NODEID']} v={r['VERSION']} lang={r['LANGU']} text='{r['TEXT']}'")
            summary[wfd] = total

        # Also get full TEXT for any node hit so we know step context
        print("\n== Step context for Return hits ==")
        step_context = {}
        for wfd, rows in summary.items():
            if not rows:
                continue
            node_ids = sorted(set(r["NODEID"] for r in rows))
            step_rows = []
            for n in node_ids:
                sr = rr(g, "SWDSDSTEPS",
                        [f"WFD_ID = '{wfd}'", f"NODEID = '{n}'"],
                        ["WFD_ID","VERSION","NODEID","EXETYP","FORM_OTYPE","FORM_METHD","FORM_NAME","CREATED_BY","CHANGED_BY"], 10)
                if isinstance(sr, list):
                    step_rows.extend(sr)
            print(f"  {wfd}: Return outcomes on nodes {node_ids}")
            for sr in step_rows:
                print(f"    node={sr['NODEID']} exetyp={sr['EXETYP']} form={sr['FORM_NAME']} by={sr['CREATED_BY']}/{sr['CHANGED_BY']}")
            step_context[wfd] = step_rows

        # Also fetch the WORKFLOW description from SWDSHEADER
        print("\n== SWDSHEADER descriptions ==")
        headers = {}
        for wfd in N_MENARD_WS_IDS:
            rows = rr(g, "SWDSHEADER", [f"WFD_ID = '{wfd}'"],
                      ["WFD_ID","VERSION","CREATED_BY","CREATED_ON","CHANGED_BY","CHANGED_ON","STATUS"], 5)
            if isinstance(rows, list):
                for r in rows:
                    print(f"  {wfd} v{r['VERSION']}: status={r['STATUS']} cr={r['CREATED_BY']} {r['CREATED_ON']} ch={r['CHANGED_BY']} {r['CHANGED_ON']}")
                headers[wfd] = rows
            # also get WF title text
            tx = rr(g, "SWDSWFCTXT", [f"WFD_ID = '{wfd}'", "LANGU = 'E'"],
                    ["WFD_ID","VERSION","LANGU","TEXT"], 5)
            if isinstance(tx, list):
                for r in tx:
                    print(f"     title EN v{r['VERSION']}: {r['TEXT']}")

        with open(os.path.join(OUT, "return_outcomes_report.json"), "w", encoding="utf-8") as f:
            json.dump({"return_matches": summary,
                       "step_context": step_context,
                       "headers": headers},
                      f, indent=2, ensure_ascii=False)
        print(f"\nwrote return_outcomes_report.json")
    finally:
        g.close()


if __name__ == "__main__":
    main()
