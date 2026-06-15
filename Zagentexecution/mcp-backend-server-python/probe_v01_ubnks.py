import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("V01")
def read(where, fields, rc=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUH",
               OPTIONS=[{"TEXT": where}], FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=rc)
    offs=[(f["FIELDNAME"],int(f["OFFSET"]),int(f["LENGTH"])) for f in r.get("FIELDS",[])]
    return [{nm:x["WA"][o:o+l].rstrip() for nm,o,l in offs} for x in r.get("DATA",[])]
F=["LAUFD","LAUFI","ZBUKR","LIFNR","WAERS","RBETR","ZLAND","UBNKS","ZNME1"]
allrows=[]
for hbk in ("CIT04","CIT21","CIT01"):
    rows = read(f"LAUFD LIKE '2024%' AND HBKID = '{hbk}'", F)
    allrows += rows
print("2024 Citi rows:", len(allrows))
dist = Counter(r["UBNKS"] for r in allrows)
print("\n=== UBNKS (beneficiary BANK country) distribution, 2024 Citi ===")
for cc,n in dist.most_common(40):
    tag = " <-A PstlAdr" if cc in("US","CA","PR") else (" <-B PstCd" if cc=="SE" else "")
    print(f"  {cc or '(blank)':6} {n}{tag}")
def ex(pred,label,k=4):
    print(f"\n--- {label} ---")
    rows=sorted([r for r in allrows if pred(r)], key=lambda r:r["LAUFD"], reverse=True)
    for r in rows[:k]:
        print(f"  {r['LAUFD']} LAUFI={r['LAUFI']:6} {r['ZBUKR']} LIFNR={r['LIFNR']} {r['WAERS']} {r['RBETR']:>14} ZLAND={r['ZLAND']} UBNKS={r['UBNKS']} | {r['ZNME1'][:30]}")
    print(f"  (total {len(rows)})")
ex(lambda r:r["UBNKS"] in("US","CA","PR"), "A US/CA/PR -> PstlAdr")
ex(lambda r:r["UBNKS"]=="SE", "B SE -> PstCd")
ex(lambda r:r["UBNKS"] not in("US","CA","PR","SE",""), "C other -> fallback")
# SE across years by UBNKS
print("\n=== SE (UBNKS) by year ===")
for yr in ("2023","2024","2025","2026"):
    t=0
    for hbk in ("CIT04","CIT21","CIT01"):
        t+=len(read(f"LAUFD LIKE '{yr}%' AND HBKID = '{hbk}' AND UBNKS = 'SE'", ["LAUFD"]))
    print(f"  {yr}: {t}")
c.close()
