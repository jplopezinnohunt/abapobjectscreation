import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
W="TREE_ID = '/CITI/XML/UNESCO/DC_V3_01' AND VERSION = '000'"
def rd(t,f):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
nodes=rd("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","PARENT_ID","FIRSTCHILD_ID","BROTHER_ID","NODE_TYPE","MP_EXIT_FUNC","MP_SC_TAB","MP_SC_FLD","MP_CONST"])
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
    if n["MP_SC_FLD"]: return f"{n['MP_SC_TAB']}-{n['MP_SC_FLD']}"
    if n["MP_CONST"]: return f"const'{n['MP_CONST']}'"
    return ""
def ordered(pid):
    out=[]; cur=byid.get(byid[pid]["FIRSTCHILD_ID"]); s=0
    while cur and s<40: out.append(cur); cur=byid.get(cur["BROTHER_ID"]); s+=1
    return out
def walk(nid, depth=0):
    for k in ordered(nid):
        cc=cs(k["NODE_ID"]); s=src(k)
        line="  "*depth + f"<{k['TECH_NAME']}>"
        extra=[]
        if s: extra.append(s)
        if cc: extra.append(f"COND[{cc}]")
        print(f"   {line:42} {' | '.join(extra)}")
        walk(k["NODE_ID"], depth+1)
for lab,nid,cond in [("#1 (resto/BR — hibrido)","N_2368849090","<> RU AND <> JP AND <> US/CA/PR"),
                     ("#2 (US/CA/PR — estructurado)","N_1496761000","= US OR CA OR PR")]:
    print(f"\n===== Cdtr PstlAdr {lab}  [{cond}] =====")
    walk(nid)
c.close()
