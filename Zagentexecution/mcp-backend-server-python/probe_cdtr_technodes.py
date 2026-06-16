import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("D01")
W="TREE_ID = '/CITI/XML/UNESCO/DC_V3_01' AND VERSION = '000'"
def rd(t,f):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
nodes=rd("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","NODE_TYPE","MP_IF_TP","MP_EXIT_FUNC","MP_SC_TAB","MP_SC_FLD","MP_CONST","MP_SC_NODE","MP_SC_REF_NAME"])
byid={n["NODE_ID"]:n for n in nodes}
def src(n):
    if n["MP_EXIT_FUNC"]: return f"EXIT {n['MP_EXIT_FUNC']}"
    if n["MP_SC_FLD"]: return f"{n['MP_SC_TAB']}-{n['MP_SC_FLD']}"
    if n["MP_CONST"]: return f"const '{n['MP_CONST']}'"
    if n["MP_SC_NODE"]: return f"ref NODE {n['MP_SC_REF_NAME']}"
    return "container/atoms"
# technical nodes by name
print("=== Nodos técnicos clave (computan valores usados por condiciones) ===")
TARGETS=["HR","HOUSENUMBER","POCITY","POCITYHR","HOUSENUM","HOUSENO"]
for n in nodes:
    if n["TECH_NAME"] in TARGETS or any(t in n["TECH_NAME"].upper() for t in ("HR","HOUSEN","POCITY")):
        if n["NODE_TYPE"] in ("TN","AT") or n["TECH_NAME"] in TARGETS:
            print(f"  {n['TECH_NAME']:16} ({n['NODE_ID']}, type={n['NODE_TYPE']}) <- {src(n)}")
# specifically resolve refs by reading conditions of Cdtr address children
print("\n=== Resolviendo refs de condiciones (Cdtr StrtNm/PstCd/TwnNm/CtrySubDvsn) ===")
conds=rd("DMEE_TREE_COND",["NODE_ID","ARG1_NODE","ARG1_REF_NAME","OPERATOR","ARG2_CONST","ARG2_REF_NAME","ARG2_NODE"])
seen=set()
for cr in conds:
    for nd,ref in [(cr["ARG1_NODE"],cr["ARG1_REF_NAME"]),(cr["ARG2_NODE"],cr["ARG2_REF_NAME"])]:
        if nd and ref and ref not in seen:
            seen.add(ref)
            tn=byid.get(nd,{})
            print(f"  ref '{ref}' = NODE {nd} ({tn.get('TECH_NAME','?')}) <- {src(tn) if tn else '?'}")
c.close()
