import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("V01")
def reg(laufd,laufi,lifnr,fields):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUH",
        OPTIONS=[{"TEXT": f"LAUFD = '{laufd}' AND LAUFI = '{laufi}' AND LIFNR = '{lifnr}'"}],
        FIELDS=[{"FIELDNAME": f} for f in fields])
    offs=[(f["FIELDNAME"],int(f["OFFSET"]),int(f["LENGTH"])) for f in r.get("FIELDS",[])]
    return [{nm:x["WA"][o:o+l].rstrip() for nm,o,l in offs} for x in r.get("DATA",[])]
ADDR=["LIFNR","ZNME1","ZSTRA","ZPSTL","ZORT1","ZREGI","ZLAND","UBNKS"]
BANK=["LIFNR","UBNKS","UBNKL","UBKNT","SWIFT","ZBNKL","ZBNKN"]
cases=[
 ("1  US clean ",  "20240531","00001B","10002742"),
 ("1  US edge ET", "20240531","00001B","10002080"),
 ("1b CA       ",  "20240124","00002B","10015688"),
 ("2  BR fallbk",  "20240326","00008B","0000344663"),
]
for lab,d,i,l in cases:
    rows=reg(d,i,l,ADDR)
    print(f"\n=== {lab} | {d}/{i} LIFNR={l} ===")
    if not rows: print("  (no REGUH row)"); continue
    r=rows[0]
    print(f"  ZNME1={r['ZNME1']!r}")
    print(f"  ZSTRA(street)={r['ZSTRA']!r}  ZPSTL={r['ZPSTL']!r}  ZORT1(city)={r['ZORT1']!r}")
    print(f"  ZREGI(state)={r['ZREGI']!r}  ZLAND(addr ctry)={r['ZLAND']!r}  UBNKS(bank ctry)={r['UBNKS']!r}")
    try:
        b=reg(d,i,l,BANK)[0]
        print(f"  bank: UBNKL={b['UBNKL']!r} UBKNT={b['UBKNT']!r} SWIFT={b['SWIFT']!r}")
    except Exception as e: print("  bank read:",e)
c.close()
