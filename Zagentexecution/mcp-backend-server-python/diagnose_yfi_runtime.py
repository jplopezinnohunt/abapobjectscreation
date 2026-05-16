"""Diagnose why Dbtr/PstlAdr leaves are missing/blank in the XML output."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

# 1. Confirm Y_FI_DMEE_ADR runtime is v2 — read source again
print("=== 1. Verify FM Y_FI_DMEE_ADR ACTIVE runtime ===")
r = c.call("RPY_FUNCTIONMODULE_READ_NEW", FUNCTIONNAME="Y_FI_DMEE_ADR")
src_tab = r.get("SOURCE") or []
lines = [row.get("LINE","") if isinstance(row,dict) else str(row) for row in src_tab]
print(f"  source lines: {len(lines)}")
ctry = sum(1 for l in lines if "ls_adrc-country" in l.lower())
strt = sum(1 for l in lines if "ls_adrc-street" in l.lower())
bldg = sum(1 for l in lines if "ls_adrc-house_num1" in l.lower())
print(f"  has 'ls_adrc-country': {ctry}, 'ls_adrc-street': {strt}, 'ls_adrc-house_num1': {bldg}")

# 2. Check FUPARAREF — generation status
print("\n=== 2. FUPARAREF generation status ===")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="REPOSRC",
           OPTIONS=[{"TEXT": "PROGNAME = 'LYFPAYMU19'"}],
           FIELDS=[{"FIELDNAME":"PROGNAME"},{"FIELDNAME":"R3STATE"},
                   {"FIELDNAME":"UDAT"},{"FIELDNAME":"UTIME"}],
           DELIMITER='|')
for row in r.get("DATA", []):
    print(f"  {row['WA']}")

# 3. List DMEE_TREE_COND for SEPA_CT_UNES V001 — filter to Dbtr
print("\n=== 3. DMEE_TREE_COND for Dbtr nodes (V001) ===")
cond_rows = rfc_read_paginated(c, "DMEE_TREE_COND",
    fields=["NODE_ID","COND_ID","COND_TAB","COND_FLD","COND_OP","COND_VALUE"],
    where="TREE_ID = '/SEPA_CT_UNES' AND VERSION = '001'",
    batch_size=200, throttle=0.0)
print(f"  total cond rows: {len(cond_rows)}")
# Show all
for r in cond_rows[:30]:
    print(f"  {r}")

# 4. Read CSV to find Dbtr/PstlAdr leaf NODE_IDs and check their EX_STATUS
print("\n=== 4. V001 Dbtr/PstlAdr leaves status ===")
import csv
csv_path = os.path.join(os.path.dirname(__file__), "..", "..",
    "knowledge/domains/Payment/phase0/dmee_full",
    "dmee_tree_node_d01_sepa_v001_fresh.csv")
nodes = []
with open(csv_path, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        nodes.append(row)
by_id = {n["NODE_ID"]: n for n in nodes}
def xpath(nid, _seen=None):
    if _seen is None: _seen=set()
    if nid in _seen or nid not in by_id: return ""
    _seen.add(nid)
    n = by_id[nid]
    p = n.get("PARENT_ID","").strip()
    t = (n.get("TECH_NAME") or "").strip()
    if p and p in by_id and p != nid:
        return f"{xpath(p,_seen)}/{t}" if t else xpath(p,_seen)
    return f"/{t}" if t else ""

print(f"  {'NODE_ID':<14} {'TECH_NAME':<15} {'NODE_TYPE':<10} {'XPath':<60}")
for n in nodes:
    xp = xpath(n["NODE_ID"])
    if "Dbtr/PstlAdr" in xp and n.get("NODE_TYPE") in ("ELEM","COND"):
        print(f"  {n['NODE_ID']:<14} {n.get('TECH_NAME',''):<15} {n.get('NODE_TYPE',''):<10} {xp}")
