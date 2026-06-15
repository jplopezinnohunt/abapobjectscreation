import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
W="TREE_ID = '/CITI/XML/UNESCO/DC_V3_01' AND VERSION = '000'"
def rd(t,f):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
nodes=rd("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","PARENT_ID","FIRSTCHILD_ID","BROTHER_ID","MP_EXIT_FUNC","MP_SC_TAB","MP_SC_FLD"])
byid={n["NODE_ID"]:n for n in nodes}
conds=rd("DMEE_TREE_COND",["NODE_ID","COND_NUMBER","ARG1_FLD","ARG1_TAB","OPERATOR","ARG2_CONST","LINK_OPERATOR"])
cby={}
for cr in conds: cby.setdefault(cr["NODE_ID"],[]).append(cr)
def cs(nid):
    rs=sorted(cby.get(nid,[]),key=lambda r:r["COND_NUMBER"])
    if not rs: return "sin cond"
    return " ".join(f"{r['ARG1_TAB']}-{r['ARG1_FLD']} {r['OPERATOR']} {r['ARG2_CONST']} {r['LINK_OPERATOR']}".strip() for r in rs)
def kids(pid):
    out=[]; cur=byid.get(byid[pid]["FIRSTCHILD_ID"]); s=0
    while cur and s<40: out.append(cur); cur=byid.get(cur["BROTHER_ID"]); s+=1
    return out
def src(n):
    if n["MP_EXIT_FUNC"]: return f"EXIT {n['MP_EXIT_FUNC'][:24]}"
    if n["MP_SC_FLD"]: return f"{n['MP_SC_TAB']}-{n['MP_SC_FLD']}"
    return "container"
for nid,label in [("N_5197213060","#3 US/CA/PR"),("N_1905437260","#4 RESTO")]:
    print(f"\n===== {label} — tags hijos + condición de cada uno =====")
    for ch in kids(nid):
        print(f"   <{ch['TECH_NAME']:14}> src={src(ch):30} COND: {cs(ch['NODE_ID'])}")
c.close()
