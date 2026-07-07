"""Dump CITI CdtrAgt + Cdtr PstlAdr subtrees for comparison vs CGI (D01, V000 active)."""
import sys, os
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path: sys.path.insert(0, SCRIPTS_DIR)
from rfc_helpers import ConnectionGuard

TREE = "/CITI/XML/UNESCO/DC_V3_01"
F = ["TREE_ID","VERSION","NODE_ID","PARENT_ID","TECH_NAME","NODE_TYPE","MP_SC_TAB","MP_SC_FLD","MP_SC_OFFSET","LENGTH","CV_RULE","MP_EXIT_FUNC"]

g = ConnectionGuard("D01"); g.connect()
r = g.call("RFC_READ_TABLE", QUERY_TABLE="DMEE_TREE_NODE", DELIMITER="|",
    FIELDS=[{"FIELDNAME": f} for f in F],
    OPTIONS=[{"TEXT": f"TREE_ID = '{TREE}'"}], ROWCOUNT=5000)
rows = [dict(zip(F, [v.strip() for v in x["WA"].split("|")])) for x in r.get("DATA", [])]
g.close()

t = [x for x in rows if x["TREE_ID"] == TREE and x["VERSION"] == "000"]
by_id = {x["NODE_ID"]: x for x in t}
kids = {}
for x in t: kids.setdefault(x["PARENT_ID"], []).append(x)

def find_pstladr_under(party):
    out = []
    for pr in [x for x in t if x["TECH_NAME"] == party and x["NODE_TYPE"] == "ELEM"]:
        stack = [pr["NODE_ID"]]
        while stack:
            n = stack.pop()
            for c in kids.get(n, []):
                if c["TECH_NAME"] == "PstlAdr": out.append((pr["NODE_ID"], c["NODE_ID"]))
                stack.append(c["NODE_ID"])
    return out

print(f"CITI {TREE} V000: {len(t)} nodes")
for party in ["CdtrAgt", "Cdtr"]:
    for root, pstl in find_pstladr_under(party):
        print(f"\n===== {party}  root={root}  PstlAdr={pstl} =====")
        print(f"{'TECH_NAME':<26}{'TYP':<5}{'TAB':<8}{'FLD':<12}{'OFF':<5}{'LEN':<6}{'CV':<12}{'EXIT':<28}{'NODE_ID'}")
        for c in kids.get(pstl, []):
            print(f"{c['TECH_NAME']:<26}{c['NODE_TYPE']:<5}{c['MP_SC_TAB']:<8}{c['MP_SC_FLD']:<12}{c['MP_SC_OFFSET']:<5}{c['LENGTH']:<6}{c['CV_RULE']:<12}{(c['MP_EXIT_FUNC'] or ''):<28}{c['NODE_ID']}")
