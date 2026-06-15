import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("V01")
def read(table, where, fields, rc=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=table,
               OPTIONS=[{"TEXT": where}], FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=rc)
    offs=[(f["FIELDNAME"],int(f["OFFSET"]),int(f["LENGTH"])) for f in r.get("FIELDS",[])]
    return [{nm:x["WA"][o:o+l].rstrip() for nm,o,l in offs} for x in r.get("DATA",[])]

print("=== DFPAYG CITI groups in 2024 (LAUFD/LAUFI/GRPNO/ZBUKR/HBKID/RZAWE/ANZ_ERZ) ===")
g = read("DFPAYG", "FORMI = '/CITI/XML/UNESCO/DC_V3_01' AND LAUFD LIKE '2024%'",
         ["LAUFD","LAUFI","GRPNO","ZBUKR","HBKID","RZAWE","ANZ_ERZ"])
print("groups:", len(g))
# group by ZBUKR/HBKID to see the landscape
land = Counter((r["ZBUKR"], r["HBKID"]) for r in g)
print("\nby (ZBUKR,HBKID):")
for k,n in land.most_common():
    print(f"  {k}: {n} groups")
# show some big groups (high ANZ_ERZ) per paying entity
def top(zbukr, hbkid, k=3):
    rows=[r for r in g if r["ZBUKR"]==zbukr and r["HBKID"]==hbkid]
    rows.sort(key=lambda r:int(r["ANZ_ERZ"] or 0), reverse=True)
    print(f"\n-- {zbukr}/{hbkid} top groups by payment count --")
    for r in rows[:k]:
        print(f"  LAUFD={r['LAUFD']} LAUFI={r['LAUFI']} GRPNO={r['GRPNO']} RZAWE={r['RZAWE']} ANZ_ERZ={r['ANZ_ERZ']}")
top("UNES","CIT04")
top("UBO","CIT01")
top("UNES","CIT21")

# For the biggest UNES/CIT04 group, show UBNKS mix of its beneficiaries
def ubnks_mix(laufd, laufi):
    rows = read("REGUH", f"LAUFD = '{laufd}' AND LAUFI = '{laufi}' AND HBKID = 'CIT04'",
                ["LIFNR","UBNKS","ZLAND","WAERS","RBETR","ZNME1"])
    mix = Counter(r["UBNKS"] for r in rows)
    print(f"\n=== UBNKS mix for run {laufd}/{laufi} (CIT04): {dict(mix)} ; n={len(rows)} ===")
    # one example LIFNR per branch
    for tgt,lab in (("US","PstlAdr"),("CA","PstlAdr"),("SE","PstCd")):
        ex=[r for r in rows if r["UBNKS"]==tgt]
        if ex:
            r=ex[0]; print(f"  {lab} {tgt}: LIFNR={r['LIFNR']} {r['WAERS']} {r['RBETR']} ZLAND={r['ZLAND']} | {r['ZNME1'][:28]}")
    # a non-US/CA/PR/SE one (fallback)
    fb=[r for r in rows if r["UBNKS"] not in ("US","CA","PR","SE","")]
    if fb:
        r=fb[0]; print(f"  fallback {r['UBNKS']}: LIFNR={r['LIFNR']} {r['WAERS']} {r['RBETR']} ZLAND={r['ZLAND']} | {r['ZNME1'][:28]}")
if g:
    u=[r for r in g if r["ZBUKR"]=="UNES" and r["HBKID"]=="CIT04"]
    u.sort(key=lambda r:int(r["ANZ_ERZ"] or 0), reverse=True)
    if u: ubnks_mix(u[0]["LAUFD"], u[0]["LAUFI"])
c.close()
