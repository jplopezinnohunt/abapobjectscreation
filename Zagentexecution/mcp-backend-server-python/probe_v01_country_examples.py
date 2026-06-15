"""Find 2024 Citi-tree payments in V01 bucketed by beneficiary country (UBISO proxy).
READ-ONLY. REGUH WHERE HBKID in Citi banks, LAUFD 2024."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter, defaultdict
c = get_connection("V01")

def read(table, where, fields, rc=0):
    try:
        r = c.call("RFC_READ_TABLE", QUERY_TABLE=table,
                   OPTIONS=[{"TEXT": where}] if where else [],
                   FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=rc)
        flds = [f["FIELDNAME"] for f in r.get("FIELDS", [])]
        offs = [(f["FIELDNAME"], int(f["OFFSET"]), int(f["LENGTH"])) for f in r.get("FIELDS", [])]
        out=[]
        for x in r.get("DATA", []):
            wa=x["WA"]; out.append({nm: wa[o:o+l].rstrip() for nm,o,l in offs})
        return out, None
    except Exception as e:
        return [], str(e)

# REGUH fields: recipient country = ZLAND ; also pull UBISO if it exists on REGUH
FIELDS = ["LAUFD","ZBUKR","LIFNR","HBKID","RZAWE","WAERS","ZLAND"]
allrows=[]
for hbk in ("CIT04","CIT21","CIT01"):
    rows, err = read("REGUH", f"LAUFD LIKE '2024%' AND HBKID = '{hbk}'", FIELDS, rc=0)
    print(f"HBKID={hbk}: {len(rows)} rows {('ERR='+err) if err else ''}")
    allrows += rows
print(f"\nTOTAL 2024 Citi REGUH rows: {len(allrows)}")
bycountry = Counter(r["ZLAND"] for r in allrows)
print("\n=== beneficiary country (ZLAND) distribution, 2024 Citi ===")
for cc,n in bycountry.most_common():
    print(f"  {cc or '(blank)':6} {n}")
# example rows per scenario bucket
def sample(pred, label, k=3):
    print(f"\n--- {label} ---")
    seen=0
    for r in allrows:
        if pred(r):
            print(f"  LAUFD={r['LAUFD']} ZBUKR={r['ZBUKR']} LIFNR={r['LIFNR']} HBKID={r['HBKID']} RZAWE={r['RZAWE']} WAERS={r['WAERS']} ZLAND={r['ZLAND']}")
            seen+=1
            if seen>=k: break
    if not seen: print("  (none)")
sample(lambda r: r["ZLAND"] in ("US","CA","PR"), "Scenario A — PstlAdr (US/CA/PR)")
sample(lambda r: r["ZLAND"]=="SE", "Scenario B — PstCd (SE)")
sample(lambda r: r["ZLAND"] not in ("US","CA","PR","SE","",), "Scenario C — else/fallback (other)")
c.close()
