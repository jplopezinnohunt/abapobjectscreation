import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
print("Connecting to P01 (SNC/SSO, read-only)...")
c = get_connection("P01")
def rd(t, where, fields):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=t,OPTIONS=[{"TEXT":where}],FIELDS=[{"FIELDNAME":x} for x in fields])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
# confirm system
info=c.call("RFC_SYSTEM_INFO")["RFCSI_EXPORT"]
print("Reached SYSID:", info.get("RFCSYSID"), "HOST:", info.get("RFCHOST"))
# 1) ALL CITI media ever in P01 -> bank country
rows = rd("REGUT","DTFOR = '/CITI/XML/UNESCO/DC_V3_01'",["BANKS","ZBUKR","LAUFD","XVORL"])
real=[r for r in rows if r["XVORL"]!="X"]
print(f"\n[P01] CITI media (REGUT, no-proposal): {len(real)}  años: {sorted({r['LAUFD'][:4] for r in real})}")
print("=== [P01] BANKS (país del banco) — TODA la historia CITI ===")
for cc,n in Counter(r["BANKS"] for r in real).most_common():
    node="#3 (US/CA/PR)" if cc in("US","CA","PR") else "#4 (resto)"
    print(f"  BANKS={cc or '(blank)':4} {n:7}  -> {node}")
print("=== [P01] ZBUKR (ente pagador) ===")
for cc,n in Counter(r["ZBUKR"] for r in real).most_common():
    print(f"  {cc:5} {n}")
# 2) HBKID routing in P01
dfp = rd("DFPAYG","FORMI = '/CITI/XML/UNESCO/DC_V3_01'",["HBKID","ZBUKR","LAUFD"])
print(f"\n=== [P01] DFPAYG CITI: HBKID que rutean a este formato ===")
for k,n in Counter((r["ZBUKR"],r["HBKID"]) for r in dfp).most_common():
    print(f"  {k}: {n}")
c.close()
