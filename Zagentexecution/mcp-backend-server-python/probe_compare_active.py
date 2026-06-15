import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
W="TREE_ID = '/CITI/XML/UNESCO/DC_V3_01' AND VERSION = '000'"
def rd(t,f):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
nodes=rd("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","PARENT_ID","FIRSTCHILD_ID","BROTHER_ID","MP_SC_TAB","MP_SC_FLD","MP_CONST","MP_EXIT_FUNC","NODE_TYPE"])
byid={n["NODE_ID"]:n for n in nodes}
def ordered_children(pid):
    out=[]; cur=byid.get(byid[pid]["FIRSTCHILD_ID"]); s=0
    while cur and s<40:
        out.append(cur); cur=byid.get(cur["BROTHER_ID"]); s+=1
    return out
def src(n):
    if n["MP_EXIT_FUNC"]: return f"EXIT {n['MP_EXIT_FUNC']}"
    if n["MP_SC_FLD"]: return f"{n['MP_SC_TAB']}-{n['MP_SC_FLD']}"
    if n["MP_CONST"]: return f"const '{n['MP_CONST']}'"
    return "(none/container)"
for nid,label,cond in [("N_5197213060","#3 US/CA/PR","= US OR CA OR PR"),
                       ("N_1905437260","#4 RESTO","<> US AND <> CA AND <> PR")]:
    print(f"\n===== {label}  (NODE {nid}, cond: {cond}) =====")
    for ch in ordered_children(nid):
        print(f"   <{ch['TECH_NAME']}>  <- {src(ch)}")
c.close()
