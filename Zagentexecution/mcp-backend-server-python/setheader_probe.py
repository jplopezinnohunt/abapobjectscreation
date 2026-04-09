"""Probe SETHEADER structure and current values for YBANK sets."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

conn = get_connection("D01")

# Get DD03L fields for SETHEADER
dd03l = rfc_read_paginated(conn, "DD03L",
    ["FIELDNAME", "DATATYPE", "LENG", "POSITION"],
    "TABNAME = 'SETHEADER'", batch_size=200, throttle=0.3)

print("SETHEADER fields:")
for f in sorted(dd03l, key=lambda x: int(x.get("POSITION","0") or "0")):
    print(f"  {f['FIELDNAME']:20s} {f.get('DATATYPE',''):6s} {f.get('LENG',''):6s}")

# Get actual data for YBANK sets
print("\n\nCurrent SETHEADER for YBANK sets:")
rows = rfc_read_paginated(conn, "SETHEADER",
    ["SETCLASS", "SUBCLASS", "SETNAME", "KOKRS",
     "CREUSER", "CREDATE", "CRETIME",
     "UPDUSER", "UPDDATE", "UPDTIME",
     "SETLINES"],
    "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'",
    batch_size=100, throttle=0.3)

for r in sorted(rows, key=lambda x: x.get("SETNAME","")):
    print(f"\n  {r.get('SETNAME','').strip()}")
    print(f"    Created: {r.get('CREUSER','').strip()} {r.get('CREDATE','').strip()} {r.get('CRETIME','').strip()}")
    print(f"    Updated: {r.get('UPDUSER','').strip()} {r.get('UPDDATE','').strip()} {r.get('UPDTIME','').strip()}")
    print(f"    Lines:   {r.get('SETLINES','').strip()}")

conn.close()
