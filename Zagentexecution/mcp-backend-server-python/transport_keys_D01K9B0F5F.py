"""
Decode ALL key entries for transport D01K9B0F5F with full TABKEY.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

conn = get_connection("D01")
tr = "D01K9B0F5F"

# Get tasks
tasks = rfc_read_paginated(conn, "E070",
    ["TRKORR"], f"STRKORR = '{tr}'", batch_size=500, throttle=0.3)
task_ids = [t["TRKORR"].strip() for t in tasks] if tasks else []
search_ids = [tr] + task_ids

all_keys = []
for tid in search_ids:
    e071k = rfc_read_paginated(conn, "E071K",
        ["TRKORR", "PGMID", "OBJECT", "OBJNAME", "MASTERTYPE",
         "MASTERNAME", "TABKEY"],
        f"TRKORR = '{tid}'", batch_size=5000, throttle=0.3)
    if e071k:
        all_keys.extend(e071k)

print(f"Total key entries: {len(all_keys)}")
print()

# Group by MASTERNAME (table)
tables = {}
for k in all_keys:
    tbl = k.get("MASTERNAME", "").strip() or k.get("OBJNAME", "").strip()
    tabkey = k.get("TABKEY", "").strip()
    objname = k.get("OBJNAME", "").strip()
    if tbl not in tables:
        tables[tbl] = []
    tables[tbl].append({"tabkey": tabkey, "objname": objname})

for tbl in sorted(tables.keys()):
    entries = tables[tbl]
    print(f"{tbl} ({len(entries)} entries):")
    for e in sorted(entries, key=lambda x: x["tabkey"]):
        print(f"  {e['tabkey']}")
    print()

conn.close()
