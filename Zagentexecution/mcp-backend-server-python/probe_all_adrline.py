import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
W="TREE_ID = '/CITI/XML/UNESCO/DC_V3_01' AND VERSION = '000'"
def rd(t,f):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
nodes=rd("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","PARENT_ID","MP_EXIT_FUNC","MP_SC_TAB","MP_SC_FLD","MP_OFFSET","LENGTH"])
byid={n["NODE_ID"]:n for n in nodes}
conds=rd("DMEE_TREE_COND",["NODE_ID","COND_NUMBER","ARG1_TAB","ARG1_FLD","ARG1_NODE","ARG1_REF_NAME","OPERATOR","ARG2_FLD","ARG2_TAB","ARG2_CONST","ARG2_NODE","LINK_OPERATOR"])
cby={}
for cr in conds: cby.setdefault(cr["NODE_ID"],[]).append(cr)
def a1(r): return f"NODE({r['ARG1_REF_NAME']})" if r["ARG1_NODE"] else (f"{r['ARG1_TAB']}-{r['ARG1_FLD']}" if r['ARG1_FLD'] else "?")
def a2(r): return "NODE" if r["ARG2_NODE"] else (f"{r['ARG2_TAB']}-{r['ARG2_FLD']}" if r['ARG2_FLD'] else f"'{r['ARG2_CONST']}'")
def cs(nid):
    rs=sorted(cby.get(nid,[]),key=lambda r:r["COND_NUMBER"])
    return " ".join(f"{a1(r)} {r['OPERATOR']} {a2(r)} {r['LINK_OPERATOR']}".strip() for r in rs)
def src(n):
    if n["MP_EXIT_FUNC"]: return f"EXIT {n['MP_EXIT_FUNC']}"
    if n["MP_SC_FLD"]:
        off=f"[off{n['MP_OFFSET']},len{n['LENGTH']}]" if n['MP_OFFSET'] not in('','0','000') else ""
        return f"{n['MP_SC_TAB']}-{n['MP_SC_FLD']}{off}"
    return "container"
def party(n):
    s=0
    while n and s<30:
        if n["TECH_NAME"] in ("Cdtr","Dbtr","CdtrAgt","UltmtCdtr","UltmtDbtr","DbtrAgt"): return n["TECH_NAME"]
        n=byid.get(n["PARENT_ID"]); s+=1
    return "?"
# group AdrLine by (party, parent PstlAdr)
from collections import defaultdict
groups=defaultdict(list)
for n in nodes:
    if n["TECH_NAME"]=="AdrLine":
        groups[(party(n), n["PARENT_ID"])].append(n)
for (pty,par),adrs in sorted(groups.items()):
    pn=byid.get(par,{})
    print(f"\n=== {pty} / parent {pn.get('TECH_NAME')} ({par}) — {len(adrs)} AdrLine ===")
    for a in adrs:
        cc=cs(a["NODE_ID"])
        print(f"   AdrLine <- {src(a):28} {'COND['+cc+']' if cc else ''}")
c.close()
