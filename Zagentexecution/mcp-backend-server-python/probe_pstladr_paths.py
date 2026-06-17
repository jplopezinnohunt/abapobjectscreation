import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
TREES = [("CITI", "/CITI/XML/UNESCO/DC_V3_01"), ("CGI", "/CGI_XML_CT_UNESCO")]

def rd(tree, t, f):
    W = f"TREE_ID = '{tree}' AND VERSION = '000'"
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=t, OPTIONS=[{"TEXT": W}],
               FIELDS=[{"FIELDNAME": x} for x in f])
    o = [(z["FIELDNAME"], int(z["OFFSET"]), int(z["LENGTH"])) for z in r.get("FIELDS", [])]
    return [{n: w["WA"][a:a+l].rstrip() for n, a, l in o} for w in r.get("DATA", [])]

for tag, tree in TREES:
    nodes = rd(tree, "DMEE_TREE_NODE", ["NODE_ID", "TECH_NAME", "PARENT_ID"])
    byid = {n["NODE_ID"]: n for n in nodes}
    conds = rd(tree, "DMEE_TREE_COND", ["NODE_ID", "COND_NUMBER", "ARG1_FLD", "OPERATOR", "ARG2_CONST", "LINK_OPERATOR"])
    cby = {}
    for cr in conds: cby.setdefault(cr["NODE_ID"], []).append(cr)
    def cs(nid):
        rs = sorted(cby.get(nid, []), key=lambda r: r["COND_NUMBER"])
        return " ".join(f"{r['ARG1_FLD']}{r['OPERATOR']}{r['ARG2_CONST']} {r['LINK_OPERATOR']}".strip() for r in rs) or "(none)"
    def path(nid):
        out = []; cur = byid.get(nid); s = 0
        while cur and s < 40:
            out.append(cur["TECH_NAME"]); cur = byid.get(cur["PARENT_ID"]); s += 1
        return "/".join(reversed(out))
    print(f"\n######## {tag} — every PstlAdr node, FULL path + condition ########")
    for n in nodes:
        if n["TECH_NAME"] == "PstlAdr":
            print(f"  {n['NODE_ID']}  COND[{cs(n['NODE_ID'])}]")
            print(f"      PATH: {path(n['NODE_ID'])}")
c.close()
