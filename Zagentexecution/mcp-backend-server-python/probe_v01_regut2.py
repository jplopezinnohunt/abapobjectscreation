import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("V01")
def read(where, fields, rc=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUT",
        OPTIONS=[{"TEXT": where}], FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=rc)
    offs=[(f["FIELDNAME"],int(f["OFFSET"]),int(f["LENGTH"])) for f in r.get("FIELDS",[])]
    return [{nm:x["WA"][o:o+l].rstrip() for nm,o,l in offs} for x in r.get("DATA",[])]
F=["LAUFD","LAUFI","XVORL","ZBUKR","GRPNO","WAERS","RBETR","TSUSR"]
rows = read("DTFOR = '/CITI/XML/UNESCO/DC_V3_01' AND LAUFD LIKE '2024%'", F)
# real media only (not proposals)
real=[r for r in rows if r["XVORL"]!="X"]
real.sort(key=lambda r:(r["LAUFD"], r["LAUFI"]))
print(f"REAL CITI media in V01 (REGUT, 2024, non-proposal): {len(real)}")
print(f"{'LAUFD':10} {'LAUFI':8} {'ZBUKR':5} {'GRPNO':6} {'WAERS':4} {'RBETR':>16} {'TSUSR':10}")
for r in real:
    print(f"{r['LAUFD']:10} {r['LAUFI']:8} {r['ZBUKR']:5} {r['GRPNO']:>6} {r['WAERS']:4} {r['RBETR']:>16} {r['TSUSR']:10}")
# also confirm the LAUFI length / exact form
if real:
    print("\nLAUFI sample repr:", [r['LAUFI'] for r in real[:5]])
c.close()
