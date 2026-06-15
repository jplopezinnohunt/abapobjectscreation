import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("V01")
def read(where, fields):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUH",
               OPTIONS=[{"TEXT": where}], FIELDS=[{"FIELDNAME": f} for f in fields])
    offs=[(f["FIELDNAME"],int(f["OFFSET"]),int(f["LENGTH"])) for f in r.get("FIELDS",[])]
    return [{nm:x["WA"][o:o+l].rstrip() for nm,o,l in offs} for x in r.get("DATA",[])]
def show(laufd,laufi,hbk,label):
    rows=read(f"LAUFD = '{laufd}' AND LAUFI = '{laufi}' AND HBKID = '{hbk}'",
              ["LIFNR","UBNKS","ZLAND","WAERS","RBETR","ZNME1"])
    print(f"\n{label}: {laufd}/{laufi} {hbk} -> n={len(rows)} UBNKS={dict(Counter(r['UBNKS'] for r in rows))}")
    for r in rows[:3]:
        print(f"   LIFNR={r['LIFNR']} {r['WAERS']} {r['RBETR']:>12} ZLAND={r['ZLAND']} UBNKS={r['UBNKS']} | {r['ZNME1'][:30]}")
show("20240124","00002B","CIT21","CA scenario (PstlAdr)")
show("20240326","00008B","CIT01","BR scenario (fallback)")
show("20240531","00001B","CIT04","US scenario (PstlAdr)")
c.close()
