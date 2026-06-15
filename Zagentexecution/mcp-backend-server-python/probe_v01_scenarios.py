import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
from collections import Counter
c = get_connection("V01")
def read(table, where, fields, rc=0):
    try:
        r = c.call("RFC_READ_TABLE", QUERY_TABLE=table,
                   OPTIONS=[{"TEXT": where}] if where else [],
                   FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=rc)
        offs=[(f["FIELDNAME"],int(f["OFFSET"]),int(f["LENGTH"])) for f in r.get("FIELDS",[])]
        return [{nm:x["WA"][o:o+l].rstrip() for nm,o,l in offs} for x in r.get("DATA",[])], None
    except Exception as e:
        return [], str(e)

# 1) Does REGUH carry UBISO / UBNKS / ZREGI ?
print("=== REGUH field existence test ===")
for f in ("UBISO","UBNKS","ZLAND","ZREGI","ZPSTL","ZNME1","UZAWE"):
    rows,err = read("REGUH", "LAUFD LIKE '2024%' AND HBKID = 'CIT04'", [f], rc=1)
    print(f"  {f:7} -> {'OK '+str(rows[0]) if rows else 'MISSING/'+str(err)[:40]}")

# 2) SE across last 2 years (any Citi bank)
print("\n=== SE (Sweden) Citi payments by year ===")
for yr in ("2023","2024","2025","2026"):
    tot=0
    for hbk in ("CIT04","CIT21","CIT01"):
        rows,_ = read("REGUH", f"LAUFD LIKE '{yr}%' AND HBKID='{hbk}' AND ZLAND='SE'",
                      ["LAUFD","LIFNR"], rc=0)
        tot+=len(rows)
    print(f"  {yr}: {tot}")

# 3) concrete examples per scenario (most recent in 2024)
FULL=["LAUFD","LAUFI","ZBUKR","LIFNR","VBLNR","HBKID","RZAWE","WAERS","RBETR","ZLAND","ZNME1"]
def ex(where, label, k=4):
    print(f"\n--- {label} ---")
    best=[]
    for hbk in ("CIT04","CIT21","CIT01"):
        rows,_=read("REGUH", f"{where} AND HBKID='{hbk}'", FULL, rc=0)
        best+=rows
    best.sort(key=lambda r:r["LAUFD"], reverse=True)
    for r in best[:k]:
        print(f"  {r['LAUFD']} LAUFI={r['LAUFI']:6} {r['ZBUKR']} LIFNR={r['LIFNR']} {r['WAERS']} {r['RBETR']:>14} {r['ZLAND']} | {r['ZNME1'][:32]}")
    if not best: print("  (none)")
ex("LAUFD LIKE '2024%' AND ZLAND='US'", "A1 US (PstlAdr)")
ex("LAUFD LIKE '2024%' AND ZLAND='CA'", "A2 CA (PstlAdr)")
ex("LAUFD LIKE '2024%' AND ZLAND='SE'", "B  SE (PstCd) 2024")
ex("LAUFD >= '2023' AND ZLAND='SE'", "B' SE (PstCd) any recent")
ex("LAUFD LIKE '2024%' AND ZLAND='GB'", "C1 GB (fallback)")
ex("LAUFD LIKE '2024%' AND ZLAND='BR'", "C2 BR (fallback/Worldlink)")
c.close()
