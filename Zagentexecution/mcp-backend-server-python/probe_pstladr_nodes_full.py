import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")

TREES = [("CITI", "/CITI/XML/UNESCO/DC_V3_01"), ("CGI", "/CGI_XML_CT_UNESCO")]
PARTIES = {"Dbtr", "Cdtr", "UltmtDbtr", "UltmtCdtr"}

def rd(tree, t, f):
    W = f"TREE_ID = '{tree}' AND VERSION = '000'"
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=t, OPTIONS=[{"TEXT": W}],
               FIELDS=[{"FIELDNAME": x} for x in f])
    o = [(z["FIELDNAME"], int(z["OFFSET"]), int(z["LENGTH"])) for z in r.get("FIELDS", [])]
    return [{n: w["WA"][a:a+l].rstrip() for n, a, l in o} for w in r.get("DATA", [])]

for tag, tree in TREES:
    nodes = rd(tree, "DMEE_TREE_NODE",
               ["NODE_ID", "TECH_NAME", "PARENT_ID", "FIRSTCHILD_ID", "BROTHER_ID",
                "MP_EXIT_FUNC", "MP_SC_TAB", "MP_SC_FLD", "MP_IF_TP"])
    byid = {n["NODE_ID"]: n for n in nodes}
    conds = rd(tree, "DMEE_TREE_COND",
               ["NODE_ID", "COND_NUMBER", "ARG1_FLD", "ARG1_TAB", "OPERATOR", "ARG2_CONST", "LINK_OPERATOR"])
    cby = {}
    for cr in conds:
        cby.setdefault(cr["NODE_ID"], []).append(cr)

    def cs(nid):
        rs = sorted(cby.get(nid, []), key=lambda r: r["COND_NUMBER"])
        if not rs: return "(no cond)"
        return " ".join(f"{r['ARG1_FLD']} {r['OPERATOR']} '{r['ARG2_CONST']}' {r['LINK_OPERATOR']}".strip() for r in rs)

    def kids(pid):
        out = []; fc = byid.get(pid, {}).get("FIRSTCHILD_ID"); cur = byid.get(fc); s = 0
        while cur and s < 60:
            out.append(cur); cur = byid.get(cur["BROTHER_ID"]); s += 1
        return out

    def src(n):
        if n.get("MP_EXIT_FUNC"): return f"EXIT {n['MP_EXIT_FUNC']}"
        if n.get("MP_SC_FLD"): return f"{n['MP_SC_TAB']}-{n['MP_SC_FLD']}"
        return "container"

    def party_of(nid):
        cur = byid.get(nid); s = 0
        while cur and s < 30:
            if cur["TECH_NAME"] in PARTIES: return cur["TECH_NAME"]
            cur = byid.get(cur["PARENT_ID"]); s += 1
        return "?"

    pa_nodes = [n for n in nodes if n["TECH_NAME"] == "PstlAdr"]
    print(f"\n################ {tag}  ({tree}) — {len(pa_nodes)} PstlAdr nodes ################")
    # group by party, in tree order
    for party in ["Dbtr", "UltmtDbtr", "Cdtr", "UltmtCdtr"]:
        pp = [n for n in pa_nodes if party_of(n["NODE_ID"]) == party]
        print(f"\n=== {party}: {len(pp)} PstlAdr node(s) ===")
        for i, pn in enumerate(pp, 1):
            print(f"  #{i} {pn['NODE_ID']}  COND[{cs(pn['NODE_ID'])}]")
            for ch in kids(pn["NODE_ID"]):
                cc = cs(ch["NODE_ID"])
                cc = "" if cc == "(no cond)" else f"  COND[{cc}]"
                print(f"        <{ch['TECH_NAME']:13}> {src(ch):42}{cc}")
c.close()
