import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import defaultdict
c = get_connection("P01")
r=c.call("RFC_READ_TABLE",QUERY_TABLE="REGUT",OPTIONS=[{"TEXT":"DTFOR = '/CITI/XML/UNESCO/DC_V3_01'"}],
         FIELDS=[{"FIELDNAME":x} for x in ("BANKS","LAUFD","XVORL")])
o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
rows=[{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
real=[x for x in rows if x["XVORL"]!="X"]
yr=defaultdict(lambda: defaultdict(int))
for x in real:
    yr[x["LAUFD"][:4]][x["BANKS"]]+=1
print("[P01] Medios CITI por AÑO y país de banco")
print(f"\n{'Año':5} {'US #3':>7} {'CA #3':>7} {'BR #4inc':>9} {'Total':>7} {'%inc':>6}")
tU=tC=tB=0
for y in sorted(yr):
    us=yr[y].get('US',0); ca=yr[y].get('CA',0); br=yr[y].get('BR',0)
    tot=us+ca+br; tU+=us; tC+=ca; tB+=br
    pct = (100*br/tot) if tot else 0
    print(f"{y:5} {us:7} {ca:7} {br:9} {tot:7} {pct:5.0f}%")
T=tU+tC+tB
print(f"{'TOT':5} {tU:7} {tC:7} {tB:9} {T:7} {100*tB/T:5.0f}%")
# show any OTHER bank country (should be none)
others={x["BANKS"] for x in real} - {"US","CA","BR"}
print("\nOtros países de banco (debería estar vacío):", others or "(ninguno)")
c.close()
