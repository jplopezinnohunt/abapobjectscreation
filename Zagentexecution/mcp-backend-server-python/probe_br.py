import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("V01")
def reguh(d,i):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE="REGUH",OPTIONS=[{"TEXT":f"LAUFD = '{d}' AND LAUFI = '{i}'"}],
      FIELDS=[{"FIELDNAME":x} for x in ("UBNKS","HBKID","RBETR")])
    offs=[(f["FIELDNAME"],int(f["OFFSET"]),int(f["LENGTH"])) for f in r.get("FIELDS",[])]
    rows=[{nm:w["WA"][o:o+l].rstrip() for nm,o,l in offs} for w in r.get("DATA",[])]
    return [x for x in rows if x["HBKID"] in ("CIT01","CIT04","CIT21")]
for d,i in [("20240111","00003B"),("20240116","00010B"),("20240126","00011B"),
            ("20240131","00010B"),("20240201","00039B"),("20240117","00023B")]:
    rh=reguh(d,i)
    print(f"  {d}/{i}: citi pmts={len(rh)} UBNKS={dict(Counter(r['UBNKS'] for r in rh))}")
c.close()
