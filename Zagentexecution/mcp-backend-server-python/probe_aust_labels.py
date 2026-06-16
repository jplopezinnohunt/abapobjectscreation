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
print("=== labels (DD03L -> DD04T) de los campos AdrLine ===")
for tab,fld in [("FPAYHX","AUSTO"),("FPAYHX","AUST2"),("FPAYHX","AUST3"),
                ("FPAYHX","AGNT1STRAS"),("FPAYHX","AGNT2STRAS")]:
    dd=rd("DD03L",f"TABNAME = '{tab}' AND FIELDNAME = '{fld}'",["ROLLNAME","LENG"])
    lbl="?"
    if dd and dd[0]["ROLLNAME"]:
        t=rd("DD04T",f"ROLLNAME = '{dd[0]['ROLLNAME']}' AND DDLANGUAGE = 'E'",["DDTEXT"])
        lbl=t[0]["DDTEXT"] if t else "?"
    print(f"  {tab}-{fld:11} (de={dd[0]['ROLLNAME'] if dd else '?'}, len={dd[0]['LENG'] if dd else '?'}) = '{lbl}'")
# valores reales del Dbtr AUST* (UNES, un pago US Citi) para ver qué llevan
print("\n=== valores reales AUST* (no en REGUH; intentamos REGUP/FPAYHX no persiste) ===")
print("  (AUST* es buffer FPAYHX en runtime; se ve en el XML, no en REGUH)")
c.close()
