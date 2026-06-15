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
# 1) field def + data element label for FPAYH ZNME1-4
print("=== FPAYH ZNME1-4 — definición + label ===")
for f in ("ZNME1","ZNME2","ZNME3","ZNME4"):
    dd=rd("DD03L",f"TABNAME = 'FPAYH' AND FIELDNAME = '{f}'",["FIELDNAME","ROLLNAME","LENG"])
    if dd:
        de=dd[0]["ROLLNAME"]
        txt=rd("DD04T",f"ROLLNAME = '{de}' AND DDLANGUAGE = 'E'",["DDTEXT","SCRTEXT_M"])
        lbl=txt[0]["DDTEXT"] if txt else "?"
        print(f"  {f}: dataElem={de} len={dd[0]['LENG']}  label='{lbl}'")
# 2) real values in a BR/UBO Citi payment
print("\n=== valores reales (REGUH, UBO Citi BRL, 2026) ===")
rows=rd("REGUH","HBKID = 'CIT01' AND ZBUKR = 'UBO' AND LAUFD LIKE '2026%'",
        ["LIFNR","ZNME1","ZNME2","ZNME3","ZNME4","ZSTRA","ZORT1"],rc=8)
for r in rows:
    print(f"  LIFNR={r['LIFNR']}")
    print(f"     ZNME1='{r['ZNME1']}'  ZNME2='{r['ZNME2']}'  ZNME3='{r['ZNME3']}'  ZNME4='{r['ZNME4']}'")
    print(f"     ZSTRA(calle)='{r['ZSTRA']}'  ZORT1(ciudad)='{r['ZORT1']}'")
c.close()
