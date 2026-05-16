"""
Definitive verification: read DD02L.TABCLASS for FPAYH/FPAYHX/FPAYP.
Plus extract the real LDB FPMF includes.
TABCLASS legend:
  TRANSP = transparent table (DB-persisted)
  INTTAB = structure (work area only, no DB)
  APPEND = append structure
  CLUSTER = cluster table
  POOL = pooled table
  VIEW = view
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection

guard = get_connection("P01")

print("=== DD02L.TABCLASS — definitive ===")
for name in ("FPAYH","FPAYHX","FPAYP","REGUH","REGUP","BSEG","BKPF","DMEE_TREE_HEAD"):
    try:
        r = guard.call("RFC_READ_TABLE", QUERY_TABLE="DD02L",
                       OPTIONS=[{"TEXT": f"TABNAME = '{name}'"}],
                       FIELDS=[{"FIELDNAME":"TABNAME"},{"FIELDNAME":"TABCLASS"},
                               {"FIELDNAME":"AS4LOCAL"},{"FIELDNAME":"AS4VERS"}],
                       ROWCOUNT=5)
        rows = r.get("DATA", [])
        for row in rows:
            print(f"  {name}: {row['WA']}")
        if not rows:
            print(f"  {name}: NOT IN DD02L")
    except Exception as e:
        print(f"  {name}: ERROR {e}")

# Now pull the REAL LDB FPMF includes
print("\n=== LDB FPMF — extract DBFPMFTOP / DBFPMFNXXX ===")
for inc in ("DBFPMFTOP","DBFPMFNXXX","DBFPMFF001"):
    try:
        r = guard.call("RPY_PROGRAM_READ", PROGRAM_NAME=inc, WITH_INCLUDELIST='X', WITH_LOWERCASE='X')
        src_tab = r.get("SOURCE_EXTENDED") or r.get("SOURCE") or []
        if src_tab and isinstance(src_tab[0], dict):
            key = "LINE" if "LINE" in src_tab[0] else next(iter(src_tab[0].keys()))
            lines = [row[key] for row in src_tab]
        else:
            lines = list(src_tab)
        if not lines:
            print(f"  {inc}: empty / not found")
            continue
        src = "\n".join(lines)
        out = os.path.join(os.path.dirname(__file__), "..", "..", "extracted_code/FI/SAPFPAYM", inc + ".abap")
        with open(out, "w", encoding="utf-8") as f: f.write(src)
        print(f"  {inc}: saved {len(lines)} lines, {len(src)} bytes")
    except Exception as e:
        print(f"  {inc}: ERROR {e}")

# Also: the LDB structure node graph lives in LDBN (LDB nodes)
print("\n=== LDBN (LDB Node graph) for FPMF ===")
try:
    r = guard.call("RFC_READ_TABLE", QUERY_TABLE="LDBN",
                   OPTIONS=[{"TEXT": "LDBNAME = 'FPMF'"}],
                   FIELDS=[{"FIELDNAME":"LDBNAME"},{"FIELDNAME":"NODE"},
                           {"FIELDNAME":"PARENTNODE"},{"FIELDNAME":"DBSTRUCT"}],
                   ROWCOUNT=50)
    for d in r.get("DATA", []):
        print(f"  {d['WA']}")
except Exception as e:
    print(f"  LDBN FPMF: ERROR {e}")

print("\n=== Where does the data actually live? Check FPM_PAYTAB / PAYR / PAYRQ ===")
for name in ("PAYR","PAYRQ","FPAYHT","FPAYPT","DFPAYG","DFPAYGT"):
    try:
        r = guard.call("RFC_READ_TABLE", QUERY_TABLE="DD02L",
                       OPTIONS=[{"TEXT": f"TABNAME = '{name}'"}],
                       FIELDS=[{"FIELDNAME":"TABNAME"},{"FIELDNAME":"TABCLASS"}],
                       ROWCOUNT=5)
        rows = r.get("DATA", [])
        for row in rows:
            print(f"  {name}: {row['WA']}")
        if not rows:
            print(f"  {name}: NOT IN DD02L")
    except Exception as e:
        print(f"  {name}: ERROR {e}")
