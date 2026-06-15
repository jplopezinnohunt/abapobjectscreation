import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("V01")
def dfp(d,i):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE="DFPAYG",OPTIONS=[{"TEXT":f"LAUFD = '{d}' AND LAUFI = '{i}'"}],
      FIELDS=[{"FIELDNAME":x} for x in ("GRPNO","FORMI","ZBUKR","HBKID","ANZ_ERZ","ANZ_ERL")])
    offs=[(f["FIELDNAME"],int(f["OFFSET"]),int(f["LENGTH"])) for f in r.get("FIELDS",[])]
    return [{nm:w["WA"][o:o+l].rstrip() for nm,o,l in offs} for w in r.get("DATA",[])]
for d,i,lab in [("20240424","00012B","US"),("20240124","00020B","CA"),("20240131","00010B","BR")]:
    print(f"\n=== {d}/{i} [{lab}] DFPAYG groups ===")
    for r in dfp(d,i):
        mark = " <== CITI" if r["FORMI"]=="/CITI/XML/UNESCO/DC_V3_01" else ""
        print(f"  GRPNO={r['GRPNO']} FORMI={r['FORMI']} {r['ZBUKR']}/{r['HBKID']} erz={r['ANZ_ERZ']} erl={r['ANZ_ERL']}{mark}")
c.close()
