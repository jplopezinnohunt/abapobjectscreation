import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter, defaultdict
c = get_connection("V01")
def rd(where, fields):
    r=c.call("RFC_READ_TABLE",QUERY_TABLE="REGUH",OPTIONS=[{"TEXT":where}],FIELDS=[{"FIELDNAME":x} for x in fields])
    o=[(z["FIELDNAME"],int(z["OFFSET"]),int(z["LENGTH"])) for z in r.get("FIELDS",[])]
    return [{n:w["WA"][a:a+l].rstrip() for n,a,l in o} for w in r.get("DATA",[])]
allrows=[]
for hbk in ("CIT04","CIT21","CIT01"):
    allrows+=rd(f"LAUFD LIKE '2024%' AND HBKID = '{hbk}'",["UBNKS","ZLAND"])
# group by ZLAND, split #3 (UBISO in US/CA/PR) vs #4 (rest)
tot=Counter(); inc=Counter()
for r in allrows:
    z=r["ZLAND"] or "(blank)"
    tot[z]+=1
    if r["UBNKS"] not in ("US","CA","PR"): inc[z]+=1   # #4 = incompleto
print(f"2024 Citi pagos: {len(allrows)} | países (ZLAND): {len(tot)}")
print(f"\n{'País':6} {'Total':>7} {'#3 OK':>7} {'#4 INC':>7}")
for z,n in tot.most_common():
    print(f"{z:6} {n:7} {n-inc[z]:7} {inc[z]:7}")
print(f"\nTOTAL incompletos (#4): {sum(inc.values())}")
c.close()
