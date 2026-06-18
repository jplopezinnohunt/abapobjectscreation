import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("D01")
W="TREE_ID = '/CGI_XML_CT_UNESCO' AND VERSION = '000'"
def rd(t,f):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
nodes=rd("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","PARENT_ID","FIRSTCHILD_ID","BROTHER_ID","MP_IF_TP","MP_EXIT_FUNC","MP_SC_TAB","MP_SC_FLD"])
byid={n["NODE_ID"]:n for n in nodes}
# MP_IF_TP legend
IFTP={'1':'STRUCT-FIELD','2':'CONSTANT','3':'EXIT(BAdI)','4':'AGGREGATION','5':'REF-NODE','6':'OWN/ATOMS','7':'TREE'}
# 1) global: cuántos nodos por tipo de mapeo
print("=== CGI tree — tipo de mapeo de TODOS los nodos (MP_IF_TP) ===")
for k,n in Counter(IFTP.get(x['MP_IF_TP'],x['MP_IF_TP']) for x in nodes).most_common():
    print(f"   {k}: {n}")
# 2) UltmtDbtr CdtTrfTxInf — detalle
def ordch(pid):
    out=[]; cur=byid.get(byid[pid]["FIRSTCHILD_ID"]); s=0
    while cur and s<40: out.append(cur); cur=byid.get(cur["BROTHER_ID"]); s+=1
    return out
ult=[n for n in nodes if n["TECH_NAME"]=="UltmtDbtr" and byid.get(n["PARENT_ID"],{}).get("TECH_NAME")=="CdtTrfTxInf"]
for u in ult:
    pa=[k for k in ordch(u["NODE_ID"]) if k["TECH_NAME"]=="PstlAdr"]
    for p in pa:
        print(f"\n=== CGI UltmtDbtr/PstlAdr {p['NODE_ID']} — detalle de mapeo ===")
        for tag in ordch(p["NODE_ID"]):
            print(f"   <{tag['TECH_NAME']:14}> MP_IF_TP={tag['MP_IF_TP']}({IFTP.get(tag['MP_IF_TP'],'?')}) EXIT={tag['MP_EXIT_FUNC'][:30]} FLD={tag['MP_SC_TAB']}-{tag['MP_SC_FLD']}")
c.close()
