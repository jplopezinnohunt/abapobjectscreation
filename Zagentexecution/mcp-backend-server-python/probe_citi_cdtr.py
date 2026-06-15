import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
W="TREE_ID = '/CITI/XML/UNESCO/DC_V3_01' AND VERSION = '000'"
def rd(t,f):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
nodes=rd("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","PARENT_ID","FIRSTCHILD_ID","BROTHER_ID","NODE_TYPE","MP_EXIT_FUNC","MP_SC_TAB","MP_SC_FLD"])
byid={n["NODE_ID"]:n for n in nodes}
kids={}
for n in nodes: kids.setdefault(n["PARENT_ID"],[]).append(n)
conds=rd("DMEE_TREE_COND",["NODE_ID","COND_NUMBER","ARG1_TAB","ARG1_FLD","ARG1_NODE","ARG1_REF_NAME","OPERATOR","ARG2_TAB","ARG2_FLD","ARG2_CONST","ARG2_NODE","LINK_OPERATOR"])
cby={}
for cr in conds: cby.setdefault(cr["NODE_ID"],[]).append(cr)
def a1(r):
    if r["ARG1_NODE"]: return f"NODE({r['ARG1_REF_NAME']})"
    if r["ARG1_FLD"]: return f"{r['ARG1_TAB']}-{r['ARG1_FLD']}"
    return "?"
def a2(r):
    if r["ARG2_NODE"]: return "NODE"
    if r["ARG2_FLD"]: return f"{r['ARG2_TAB']}-{r['ARG2_FLD']}"
    return f"'{r['ARG2_CONST']}'"
def cs(nid):
    rs=sorted(cby.get(nid,[]),key=lambda r:r["COND_NUMBER"])
    return " ".join(f"{a1(r)} {r['OPERATOR']} {a2(r)} {r['LINK_OPERATOR']}".strip() for r in rs) or "sin cond"
def src(n):
    if n["MP_EXIT_FUNC"]: return f"EXIT {n['MP_EXIT_FUNC'][:26]}"
    if n["MP_SC_FLD"]: return f"{n['MP_SC_TAB']}-{n['MP_SC_FLD']}"
    return "container"
def ordered(pid):
    out=[]; cur=byid.get(byid[pid]["FIRSTCHILD_ID"]); s=0
    while cur and s<40: out.append(cur); cur=byid.get(cur["BROTHER_ID"]); s+=1
    return out
def under(n,tech):
    s=0
    while n and s<30:
        if n["TECH_NAME"]==tech: return True
        n=byid.get(n["PARENT_ID"]); s+=1
    return False
# find Cdtr (NOT UltmtCdtr/CdtrAgt) PstlAdr
cdtrs=[n for n in nodes if n["TECH_NAME"]=="Cdtr"]
print(f"Nodos Cdtr: {len(cdtrs)}")
for cd in cdtrs:
    pst=[k for k in ordered(cd["NODE_ID"]) if k["TECH_NAME"]=="PstlAdr"]
    print(f"\n### Cdtr {cd['NODE_ID']} — PstlAdr: {len(pst)} ###")
    for i,p in enumerate(pst,1):
        ch=[k["TECH_NAME"] for k in kids.get(p["NODE_ID"],[])]
        st="ESTR" if ("StrtNm" in ch or "BldgNb" in ch) else "no-estr"
        print(f"  PstlAdr#{i} {p['NODE_ID']} [{st}] cond: {cs(p['NODE_ID'])}")
        for k in ordered(p["NODE_ID"]):
            cc=cs(k["NODE_ID"])
            tag=f"  cond:{cc}" if cc!="sin cond" else ""
            print(f"       <{k['TECH_NAME']:12}> {src(k):30}{tag}")
c.close()
