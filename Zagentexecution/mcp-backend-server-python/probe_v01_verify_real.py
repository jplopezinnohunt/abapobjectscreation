import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("V01")
def rd(table, where, fields):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE=table,
      OPTIONS=[{"TEXT":where}],FIELDS=[{"FIELDNAME":x} for x in fields])
    offs=[(f["FIELDNAME"],int(f["OFFSET"]),int(f["LENGTH"])) for f in r.get("FIELDS",[])]
    return [{nm:w["WA"][o:o+l].rstrip() for nm,o,l in offs} for w in r.get("DATA",[])]
def regut(d,i):
    rows=rd("REGUT",f"LAUFD = '{d}' AND LAUFI = '{i}'",("ZBUKR","GRPNO","WAERS","RBETR","XVORL","DTFOR"))
    return [r for r in rows if r["DTFOR"]=="/CITI/XML/UNESCO/DC_V3_01"]
def reguh(d,i):
    try:
        return rd("REGUH",f"LAUFD = '{d}' AND LAUFI = '{i}'",("LIFNR","UBNKS","ZLAND","WAERS","RBETR","HBKID","ZNME1"))
    except Exception: return []
CAND=[("20240129","00012B","US?"),("20240124","00020B","CA?"),("20240126","00019B","BR?"),
      ("20240424","00012B","scr4"),("20240425","00006B","scr4")]
for d,i,lab in CAND:
    rt=regut(d,i); rh=reguh(d,i)
    print(f"\n=== {d}/{i} [{lab}] ===")
    print("  REGUT:", "NOT real CITI" if not rt else f"ZBUKR={rt[0]['ZBUKR']} GRPNO={rt[0]['GRPNO']} {rt[0]['WAERS']} {rt[0]['RBETR']} XVORL={rt[0]['XVORL']!r}")
    citi=[r for r in rh if r["HBKID"] in ("CIT04","CIT21","CIT01")]
    print(f"  REGUH: total={len(rh)} citi={len(citi)} UBNKS={dict(Counter(r['UBNKS'] for r in citi))}")
    for r in citi[:2]:
        print(f"     LIFNR={r['LIFNR']} {r['WAERS']} {r['RBETR']} ZLAND={r['ZLAND']} UBNKS={r['UBNKS']} {r['HBKID']} | {r['ZNME1'][:22]}")
c.close()
