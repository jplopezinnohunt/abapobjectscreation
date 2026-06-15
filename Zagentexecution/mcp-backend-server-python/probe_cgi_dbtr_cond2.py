import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
W="TREE_ID = '/CGI_XML_CT_UNESCO' AND VERSION = '000'"
def rd(t,f):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
nodes=rd("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","PARENT_ID","FIRSTCHILD_ID","BROTHER_ID","MP_EXIT_FUNC","MP_SC_TAB","MP_SC_FLD"])
byid={n["NODE_ID"]:n for n in nodes}
kids={}
for n in nodes: kids.setdefault(n["PARENT_ID"],[]).append(n)
conds=rd("DMEE_TREE_COND",["NODE_ID","COND_NUMBER","ARG1_TAB","ARG1_FLD","ARG1_NODE","ARG1_REF_NAME","ARG1_TYPE","OPERATOR","ARG2_TAB","ARG2_FLD","ARG2_CONST","ARG2_NODE","ARG2_REF_NAME","ARG2_TYPE","LINK_OPERATOR"])
cby={}
for cr in conds: cby.setdefault(cr["NODE_ID"],[]).append(cr)
def a(r,pfx):
    if r[pfx+"NODE"]: return f"NODE:{r[pfx+'NODE']}({r[pfx+'REF_NAME']})"
    if r[pfx+"FLD"]: return f"{r[pfx+'TAB']}-{r[pfx+'FLD']}"
    if r.get(pfx+"CONST","")!="": return f"'{r[pfx+'CONST']}'"
    return f"(empty,type{r[pfx+'TYPE']},ref={r[pfx+'REF_NAME']})"
PA="N_1160789980"
print(f"CGI Dbtr/PstlAdr = {PA}  tech={byid.get(PA,{}).get('TECH_NAME')}")
for k in kids.get(PA,[]):
    src = (f"EXIT {k['MP_EXIT_FUNC']}" if k['MP_EXIT_FUNC'] else (f"{k['MP_SC_TAB']}-{k['MP_SC_FLD']}" if k['MP_SC_FLD'] else "container"))
    rows=sorted(cby.get(k["NODE_ID"],[]),key=lambda r:r["COND_NUMBER"])
    cstr=" ".join(f"{a(r,'ARG1_')} {r['OPERATOR']} {a(r,'ARG2_')} {r['LINK_OPERATOR']}".strip() for r in rows) if rows else "sin cond"
    print(f"  <{k['TECH_NAME']:12}> src={src:34} cond: {cstr}")
c.close()
