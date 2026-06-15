import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("P01")
def rd(where, fields):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE="REGUH",OPTIONS=[{"TEXT":where}],FIELDS=[{"FIELDNAME":x} for x in fields])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
# BR/UBO Citi, all 2024-2026: cuántos tienen ZNME2/3/4 != ''
rows=rd("HBKID = 'CIT01' AND ZBUKR = 'UBO' AND LAUFD >= '20240101'",["ZNME2","ZNME3","ZNME4"])
n=len(rows)
n2=sum(1 for r in rows if r["ZNME2"])
n3=sum(1 for r in rows if r["ZNME3"])
n4=sum(1 for r in rows if r["ZNME4"])
any_=sum(1 for r in rows if r["ZNME2"] or r["ZNME3"] or r["ZNME4"])
print(f"BR/UBO Citi pagos 2024-2026: {n}")
print(f"  con ZNME2 != '': {n2}")
print(f"  con ZNME3 != '': {n3}")
print(f"  con ZNME4 != '': {n4}")
print(f"  con ALGUNO (2/3/4) != '': {any_}  ({100*any_/n:.1f}%)")
print("\n  ejemplos con ZNME2 poblado (si hay):")
for r in [x for x in rows if x["ZNME2"]][:5]:
    print(f"     ZNME2='{r['ZNME2']}'")
c.close()
