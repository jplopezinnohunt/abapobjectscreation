import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import defaultdict
c = get_connection("P01")
def rd(t, where, fields):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":where}],FIELDS=[{"FIELDNAME":x} for x in fields])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
CITI="HBKID = 'CIT04' OR HBKID = 'CIT01' OR HBKID = 'CIT21'"
# 1) cuentas (T012K) + banco (T012)
acc = rd("T012K", CITI, ["BUKRS","HBKID","HKTID","WAERS","BANKN","HKONT"])
t012 = {(r["BUKRS"],r["HBKID"]):r for r in rd("T012", CITI, ["BUKRS","HBKID","BANKS","BANKL"])}
print("=== Cuentas Citi (T012K + T012) ===")
for a in sorted(acc, key=lambda r:(r["BUKRS"],r["HBKID"],r["HKTID"])):
    bk=t012.get((a["BUKRS"],a["HBKID"]),{})
    print(f"  {a['BUKRS']:5} {a['HBKID']:6} acct={a['HKTID']:6} {a['WAERS']:4} país={bk.get('BANKS','?'):3} bankkey={bk.get('BANKL',''):12} N°cuenta={a['BANKN']}")
# 2) volumen por (HBKID,HKTID,UBNKS) por año, 2024-2026
vol=defaultdict(lambda: defaultdict(int))
for hbk in ("CIT04","CIT01","CIT21"):
    rows=rd("REGUH", f"HBKID = '{hbk}' AND LAUFD >= '20240101'", ["ZBUKR","HBKID","HKTID","UBNKS","LAUFD"])
    for r in rows:
        y=r["LAUFD"][:4]
        if y in ("2024","2025","2026"):
            vol[(r["UBNKS"],r["ZBUKR"],r["HBKID"],r["HKTID"])][y]+=1
print("\n=== Volumen de pagos por cuenta (P01, 2024-2026) ===")
print(f"{'País':5}{'Ente':6}{'Banco':7}{'Cuenta':8}{'2024':>7}{'2025':>7}{'2026':>7}{'Total':>8}  Nodo")
for k in sorted(vol, key=lambda k:(k[0],k[1],k[2],k[3])):
    ub,zb,hb,ht=k; d=vol[k]; tot=sum(d.values())
    node="#3 OK" if ub in("US","CA","PR") else "#4 INC"
    print(f"{ub:5}{zb:6}{hb:7}{ht:8}{d.get('2024',0):7}{d.get('2025',0):7}{d.get('2026',0):7}{tot:8}  {node}")
c.close()
