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
conds=rd("DMEE_TREE_COND",["NODE_ID","COND_NUMBER","ARG1_TAB","ARG1_FLD","ARG1_NODE","ARG1_REF_NAME","ARG1_XPARAM","OPERATOR","ARG2_FLD","ARG2_TAB","ARG2_CONST","ARG2_NODE","ARG2_XPARAM","LINK_OPERATOR"])
cby={}
for cr in conds: cby.setdefault(cr["NODE_ID"],[]).append(cr)
def arg(r,p):
    if r[p+"NODE"]: return f"{{{r[p+'REF_NAME']}}}"
    if r[p+"FLD"]: return f"{r[p+'TAB']}-{r[p+'FLD']}"
    if r.get(p+"XPARAM",""): return f"param:{r[p+'XPARAM']}"
    if r.get(p+"CONST","")!="": return f"'{r[p+'CONST']}'"
    return "''"
def cs(nid):
    rs=sorted(cby.get(nid,[]),key=lambda r:r["COND_NUMBER"])
    return " ".join(f"{arg(r,'ARG1_')} {r['OPERATOR']} {arg(r,'ARG2_')} {r['LINK_OPERATOR']}".strip() for r in rs)
def src(n):
    if n["MP_EXIT_FUNC"]: return f"exit {n['MP_EXIT_FUNC'].split('/')[-1]}"
    if n["MP_SC_FLD"]: return f"{n['MP_SC_TAB']}-{n['MP_SC_FLD']}"
    return "(container)"
def ordered(pid):
    out=[]; cur=byid.get(byid[pid]["FIRSTCHILD_ID"]); s=0
    while cur and s<40: out.append(cur); cur=byid.get(cur["BROTHER_ID"]); s+=1
    return out
# Cdtr #1 = N_2368849090: per container tag, list atom leaves with cond
print("=== Cdtr PstlAdr #1 — átomos por tag, con condición exacta ===")
for tag in ordered("N_2368849090"):
    atoms=ordered(tag["NODE_ID"])
    if atoms:
        print(f"<{tag['TECH_NAME']}>")
        for at in atoms:
            print(f"    {at['TECH_NAME']:14} <- {src(at):28} IF [{cs(at['NODE_ID'])}]")
    else:
        print(f"<{tag['TECH_NAME']}> <- {src(tag):28} IF [{cs(tag['NODE_ID'])}]")
c.close()
