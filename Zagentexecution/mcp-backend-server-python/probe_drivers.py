import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("P01")
W="TREE_ID = '/CITI/XML/UNESCO/DC_V3_01' AND VERSION = '000'"
def rdt(t,f,where=None):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":where or W}],FIELDS=[{"FIELDNAME":x} for x in f])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
# 1) HR node mechanics
print("=== Nodo HR_Payment (N_5405523760) — cómo extrae 'P' de LAUFI ===")
for n in rdt("DMEE_TREE_NODE",["NODE_ID","TECH_NAME","MP_SC_TAB","MP_SC_FLD","MP_OFFSET","LENGTH","CV_RULE","MP_CONST"]):
    if n["NODE_ID"]=="N_5405523760":
        print(f"  src={n['MP_SC_TAB']}-{n['MP_SC_FLD']}  offset={n['MP_OFFSET']}  len={n['LENGTH']}  conv={n['CV_RULE']}")
# 2) LAUFI reales UBO Citi (ver cómo se ve payroll)
print("\n=== LAUFI reales (UBO Citi BRL, 2026) ===")
rows=rdt("REGUH",["LAUFI","ZNME1"],where="HBKID = 'CIT01' AND ZBUKR = 'UBO' AND LAUFD LIKE '2026%'")
print("  distribución LAUFI:", dict(Counter(r["LAUFI"] for r in rows).most_common(8)))
# 3) ZPFAC (PO Box) y XSCHK (cheque) cuánto pesan en UBO
rows2=rdt("REGUH",["ZPFAC"],where="HBKID = 'CIT01' AND ZBUKR = 'UBO' AND LAUFD >= '20240101'")
pobox=sum(1 for r in rows2 if r["ZPFAC"])
print(f"\n=== ZPFAC (PO Box) en UBO 2024-26: {pobox}/{len(rows2)} ({100*pobox/max(len(rows2),1):.1f}%) con apartado ===")
# XSCHK - es FPAYHX (runtime), pero RPCALCX0? probamos REGUH-XSCHK si existe
try:
    rows3=rdt("REGUH",["RZAWE"],where="HBKID = 'CIT01' AND ZBUKR = 'UBO' AND LAUFD LIKE '2026%'")
    print(f"  RZAWE (método pago) UBO 2026: {dict(Counter(r['RZAWE'] for r in rows3).most_common(5))}")
except Exception as e: print("  ",e)
c.close()
