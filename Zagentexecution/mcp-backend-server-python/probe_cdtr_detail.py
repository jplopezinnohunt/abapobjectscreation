import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("P01")
def rd(t, where, fields, rc=0):
    kw=dict(QUERY_TABLE=t,OPTIONS=[{"TEXT":where}] if where else [],FIELDS=[{"FIELDNAME":x} for x in fields])
    if rc: kw["ROWCOUNT"]=rc
    r=c.call("RFC_READ_TABLE",**kw)
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
def lbl(tab,fld):
    dd=rd("DD03L",f"TABNAME = '{tab}' AND FIELDNAME = '{fld}'",["ROLLNAME","LENG"])
    if not dd or not dd[0]["ROLLNAME"]: return f"{fld}: (?)"
    t=rd("DD04T",f"ROLLNAME = '{dd[0]['ROLLNAME']}' AND DDLANGUAGE = 'E'",["DDTEXT"])
    return f"{tab}-{fld:9} = '{t[0]['DDTEXT'] if t else '?'}' (len {dd[0]['LENG']})"
print("=== labels de campos del Cdtr ===")
for tab,f in [("FPAYHX","REF02"),("FPAYH","ZPFAC"),("FPAYH","ZPST2"),("FPAYH","ZPFOR"),
              ("FPAYH","ZORT1"),("FPAYH","ZREGI"),("FPAYHX","ZLISO"),("FPAYHX","XSCHK"),("FPAYH","LAUFI")]:
    print("  ", lbl(tab,f))
# decode PstCd POBoxPc condition fully
print("\n=== condición del PstCd/POBoxPc (CITI Cdtr) ===")
W="TREE_ID = '/CITI/XML/UNESCO/DC_V3_01' AND VERSION = '000'"
c.call  # reuse same conn but different where
def rdt(t,f):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":W}],FIELDS=[{"FIELDNAME":x} for x in f])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
nodes=rdt("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","MP_SC_TAB","MP_SC_FLD"])
byid={n["NODE_ID"]:n for n in nodes}
pob=[n for n in nodes if n["TECH_NAME"]=="POBoxPc"]
cd=rdt("DMEE_TREE_COND",["NODE_ID","ARG1_TAB","ARG1_FLD","ARG1_NODE","ARG1_REF_NAME","ARG1_XPARAM","OPERATOR","ARG2_CONST"])
for p in pob:
    for r in cd:
        if r["NODE_ID"]==p["NODE_ID"]:
            a1 = f"NODE({r['ARG1_REF_NAME']})" if r['ARG1_NODE'] else (f"{r['ARG1_TAB']}-{r['ARG1_FLD']}" if r['ARG1_FLD'] else f"XPARAM={r['ARG1_XPARAM']}")
            print(f"  POBoxPc {p['NODE_ID']} src={p['MP_SC_TAB']}-{p['MP_SC_FLD']}: {a1} {r['OPERATOR']} '{r['ARG2_CONST']}'")
c.close()
