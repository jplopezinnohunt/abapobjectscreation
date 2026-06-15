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
# full cond decode incl node refs
conds=rd("DMEE_TREE_COND",["NODE_ID","COND_NUMBER","ARG1_TAB","ARG1_FLD","ARG1_NODE","ARG1_REF_NAME","ARG1_TYPE","OPERATOR","ARG2_TAB","ARG2_FLD","ARG2_CONST","ARG2_NODE","ARG2_TYPE","LINK_OPERATOR"])
cby={}
for cr in conds: cby.setdefault(cr["NODE_ID"],[]).append(cr)
def a1(r):
    if r["ARG1_NODE"]: return f"NODE:{r['ARG1_NODE']}({r['ARG1_REF_NAME']})"
    if r["ARG1_FLD"]: return f"{r['ARG1_TAB']}-{r['ARG1_FLD']}"
    return f"type{r['ARG1_TYPE']}/{r['ARG1_REF_NAME']}"
def a2(r):
    if r["ARG2_NODE"]: return f"NODE:{r['ARG2_NODE']}"
    if r["ARG2_FLD"]: return f"{r['ARG2_TAB']}-{r['ARG2_FLD']}"
    return f"'{r['ARG2_CONST']}'(type{r['ARG2_TYPE']})"
# Dbtr PstlAdr node + its StrtNm/PstCd/TwnNm children
dbtr=[n for n in nodes if n["TECH_NAME"]=="Dbtr"][0]
def find_pstladr(pid):
    for k in kids.get(pid,[]):
        if k["TECH_NAME"]=="PstlAdr": return k
        r=find_pstladr(k["NODE_ID"])
        if r: return r
pa=find_pstladr(dbtr["NODE_ID"])
print(f"CGI Dbtr/PstlAdr = {pa['NODE_ID']}")
for k in kids.get(pa["NODE_ID"],[]):
    src = (f"EXIT {k['MP_EXIT_FUNC']}" if k['MP_EXIT_FUNC'] else (f"{k['MP_SC_TAB']}-{k['MP_SC_FLD']}" if k['MP_SC_FLD'] else "container"))
    rows=sorted(cby.get(k["NODE_ID"],[]),key=lambda r:r["COND_NUMBER"])
    cstr=" ".join(f"{a1(r)} {r['OPERATOR']} {a2(r)} {r['LINK_OPERATOR']}".strip() for r in rows) if rows else "sin cond"
    print(f"  <{k['TECH_NAME']:12}> src={src:32} cond: {cstr}")
c.close()
