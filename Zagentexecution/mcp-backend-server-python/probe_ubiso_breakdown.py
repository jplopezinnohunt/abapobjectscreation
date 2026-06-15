import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("V01")
def rd(where, fields):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE="REGUH",OPTIONS=[{"TEXT":where}],FIELDS=[{"FIELDNAME":x} for x in fields])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
allrows=[]
for hbk in ("CIT04","CIT21","CIT01"):
    allrows+=rd(f"LAUFD LIKE '2024%' AND HBKID = '{hbk}'",["UBNKS","ZLAND","ZBUKR","HBKID"])
print("2024 Citi pagos:", len(allrows))
print("\n=== por UBISO (banco/clearing) = lo que decide #3 vs #4 ===")
for cc,n in Counter(r["UBNKS"] for r in allrows).most_common():
    node="#3 completo" if cc in("US","CA","PR") else "#4 INCOMPLETO"
    print(f"  UBISO={cc or '(blank)':4} {n:6}  -> {node}")
print("\n=== los del #4 (UBISO=BR): qué ZLAND (dir benef) tienen ===")
br=[r for r in allrows if r["UBNKS"]=="BR"]
print("  ZLAND:", dict(Counter(r["ZLAND"] for r in br).most_common(6)), f" (total {len(br)})")
print("  ZBUKR:", dict(Counter(r["ZBUKR"] for r in br)))
print("\n=== prueba: beneficiarios con dir FR/MG/AR -> qué UBISO tienen? ===")
for z in ("FR","MG","AR","LB","ET"):
    sub=[r for r in allrows if r["ZLAND"]==z]
    print(f"  ZLAND={z}: {len(sub)} pagos, UBISO={dict(Counter(r['UBNKS'] for r in sub))}")
c.close()
