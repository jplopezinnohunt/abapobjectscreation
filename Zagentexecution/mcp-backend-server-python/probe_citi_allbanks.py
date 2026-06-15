import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("V01")
def rd(t, where, fields):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":where}],FIELDS=[{"FIELDNAME":x} for x in fields])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
# 1) ALL CITI media ever (REGUT) -> bank country (BANKS) + paying entity + year
rows = rd("REGUT","DTFOR = '/CITI/XML/UNESCO/DC_V3_01'",["BANKS","ZBUKR","LAUFD","XVORL"])
real=[r for r in rows if r["XVORL"]!="X"]
print(f"CITI media (REGUT, toda la historia, no-proposal): {len(real)}")
print(f"  años: {sorted({r['LAUFD'][:4] for r in real})}")
print(f"\n=== BANKS (país del banco) en TODA la historia CITI ===")
for cc,n in Counter(r["BANKS"] for r in real).most_common():
    node="#3" if cc in("US","CA","PR") else "#4"
    print(f"  BANKS={cc or '(blank)':4} {n:6}  ({node})")
print(f"\n=== ZBUKR (ente pagador) ===")
for cc,n in Counter(r["ZBUKR"] for r in real).most_common():
    print(f"  {cc:5} {n}")
# 2) which HBKID route to CITI (DFPAYG all years) -> confirm no other house banks
dfp = rd("DFPAYG","FORMI = '/CITI/XML/UNESCO/DC_V3_01'",["HBKID","ZBUKR","LAUFD"])
print(f"\n=== DFPAYG CITI (todos los años): HBKID que rutean a este formato ===")
for k,n in Counter((r["ZBUKR"],r["HBKID"]) for r in dfp).most_common():
    print(f"  {k}: {n}")
print(f"  años DFPAYG: {sorted({r['LAUFD'][:4] for r in dfp})}")
c.close()
