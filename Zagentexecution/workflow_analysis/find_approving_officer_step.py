"""Find the workflow that contains the step 'Approving Officer Approves'
(the User Decision step shown in the user's screenshot).
Also broaden Return search across ALL workflows in D01, not just N_MENARD's 9."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))


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
        # 1. Find the step 'Approving Officer Approves' across all workflows
        print("== SWDSTEXT WFD_TEXT = 'Approving Officer Approves' (step title) ==")
        rows = rr(g, "SWDSTEXT",
                  ["WFD_TEXT = 'Approving Officer Approves'", "LANGUAGE = 'E'"],
                  ["WFD_ID","VERSION","NODEID","TEXTTYP","TEXTNUMBER","WFD_TEXT"], 50)
        if isinstance(rows, list):
            print(f"  {len(rows)} hits")
            for r in rows:
                print(f"    {r['WFD_ID']} v{r['VERSION']} node={r['NODEID']} tt={r['TEXTTYP']} '{r['WFD_TEXT']}'")

        # 2. Broad scan: EVERY workflow with SHORTTEXT='Return' (EN) — find who owns them
        print("\n== SWDSWFCTXT SHORTTEXT='Return' (any WFD) ==")
        for lab in ["Return","RETURN"]:
            rows = rr(g, "SWDSWFCTXT",
                      ["LANGUAGE = 'E'", f"SHORTTEXT = '{lab}'"],
                      ["WFD_ID","VERSION","NODEID","ELEMENT","SHORTTEXT"], 500)
            if isinstance(rows, list):
                print(f"  label='{lab}': {len(rows)} rows across {len(set(r['WFD_ID'] for r in rows))} WFDs")
                wfds = sorted(set(r["WFD_ID"] for r in rows))
                for wfd in wfds:
                    w_rows = [r for r in rows if r["WFD_ID"]==wfd]
                    print(f"    {wfd}: {len(w_rows)} row(s), nodes={sorted(set(r['NODEID'] for r in w_rows))}")

        # 3. Ownership for each matching WFD
        print("\n== SWDSHEADER for matching WFDs ==")
        all_rows = rr(g, "SWDSWFCTXT",
                      ["LANGUAGE = 'E'", "SHORTTEXT = 'Return'"],
                      ["WFD_ID","VERSION"], 500)
        if isinstance(all_rows, list):
            wfds = sorted(set(r["WFD_ID"] for r in all_rows))
            for wfd in wfds:
                hdr = rr(g, "SWDSHEADER", [f"WFD_ID = '{wfd}'"],
                         ["WFD_ID","VERSION","CREATED_BY","CREATED_ON","CHANGED_BY","CHANGED_ON"], 3)
                if isinstance(hdr, list) and hdr:
                    h = hdr[-1]  # latest
                    print(f"  {wfd}: cr={h['CREATED_BY']} {h['CREATED_ON']} ch={h['CHANGED_BY']} {h['CHANGED_ON']}")
                # also title
                t = rr(g, "SWDSTEXT",
                       [f"WFD_ID = '{wfd}'","LANGUAGE = 'E'","TEXTTYP = 'HD'"],
                       ["WFD_TEXT"], 3)
                if isinstance(t, list) and t:
                    print(f"    title: {t[0]['WFD_TEXT']}")
    finally:
        g.close()


if __name__ == "__main__":
    main()
