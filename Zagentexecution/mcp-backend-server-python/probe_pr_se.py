import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("V01")
def search(field, val):
    try:
        r=c.call("RFC_READ_TABLE",QUERY_TABLE="REGUH",
          OPTIONS=[{"TEXT":f"{field} = '{val}'"}],
          FIELDS=[{"FIELDNAME":x} for x in ("LAUFD","LAUFI","LIFNR","ZLAND","UBNKS","WAERS","HBKID","ZNME1")])
        offs=[(f["FIELDNAME"],int(f["OFFSET"]),int(f["LENGTH"])) for f in r.get("FIELDS",[])]
        return [{nm:w["WA"][o:o+l].rstrip() for nm,o,l in offs} for w in r.get("DATA",[])]
    except Exception as e:
        if "TABLE_WITHOUT_DATA" in str(e): return []
        print("   ERR", str(e)[:60]); return []
for field,val in [("UBNKS","PR"),("UBNKS","SE"),("ZLAND","PR"),("ZLAND","SE")]:
    rows=search(field,val)
    citi=[r for r in rows if r["HBKID"] in ("CIT01","CIT04","CIT21")]
    print(f"\n=== REGUH {field} = '{val}': total={len(rows)}  citi-bank={len(citi)} ===")
    if rows:
        print("   years:", dict(Counter(r['LAUFD'][:4] for r in rows)))
        print("   HBKID:", dict(Counter(r['HBKID'] for r in rows)))
        print("   UBNKS:", dict(Counter(r['UBNKS'] for r in rows)), " ZLAND:", dict(Counter(r['ZLAND'] for r in rows)))
        for r in rows[:5]:
            print(f"     {r['LAUFD']}/{r['LAUFI']} LIFNR={r['LIFNR']} {r['WAERS']} ZLAND={r['ZLAND']} UBNKS={r['UBNKS']} {r['HBKID']} | {r['ZNME1'][:24]}")
c.close()
