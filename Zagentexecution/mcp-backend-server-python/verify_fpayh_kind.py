"""
verify_fpayh_kind.py
====================
Verify whether FPAYH/FPAYHX/FPAYP are STRUCTURES or TABLES, and pull SAPDBFPMF
(the LDB of SAPFPAYM) to confirm where the data actually persists.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection

guard = get_connection("P01")

print("=== TADIR for FPAYH / FPAYHX / FPAYP / FPAYG ===")
for name in ("FPAYH","FPAYHX","FPAYP","FPAYG","FPAYHM","FPAYPX"):
    try:
        # TADIR R3TR / object types
        r = guard.call("RFC_READ_TABLE", QUERY_TABLE="TADIR",
                       OPTIONS=[{"TEXT": f"OBJ_NAME = '{name}'"}],
                       FIELDS=[{"FIELDNAME":"PGMID"},{"FIELDNAME":"OBJECT"},{"FIELDNAME":"OBJ_NAME"}],
                       ROWCOUNT=20)
        rows = [r["DATA"][i]["WA"] for i in range(len(r["DATA"]))]
        print(f"  {name}: {rows}")
    except Exception as e:
        print(f"  {name}: ERROR {e}")

print("\n=== DDIF X030L (TABCLASS) — definitive structure-vs-table distinction ===")
for name in ("FPAYH","FPAYHX","FPAYP","REGUH","REGUP"):
    try:
        r = guard.call("DDIF_FIELDINFO_GET", TABNAME=name, ALL_TYPES='X')
        x = r.get("X030L_WA") or {}
        # TABCLASS values: TRANSP=transparent table, INTTAB=structure, APPEND=append struct,
        #                  CLUSTER=cluster table, POOL=pooled, VIEW=view
        print(f"  {name}: TABCLASS={x.get('TABCLASS')} TABNAME={x.get('TABNAME')} "
              f"FIELDS={len(r.get('DFIES_TAB') or [])}")
    except Exception as e:
        print(f"  {name}: ERROR {e}")

print("\n=== SAPDBFPMF — the LDB that drives SAPFPAYM ===")
try:
    r = guard.call("RPY_PROGRAM_READ", PROGRAM_NAME="SAPDBFPMF",
                   WITH_INCLUDELIST='X', WITH_LOWERCASE='X')
    src_tab = r.get("SOURCE_EXTENDED") or r.get("SOURCE") or []
    if src_tab and isinstance(src_tab[0], dict):
        key = "LINE" if "LINE" in src_tab[0] else next(iter(src_tab[0].keys()))
        lines = [row[key] for row in src_tab]
    else:
        lines = list(src_tab)
    src = "\n".join(lines)
    out = "extracted_code/FI/SAPFPAYM/SAPDBFPMF.abap"
    out_path = os.path.join(os.path.dirname(__file__), "..", "..", out)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(src)
    inctab = r.get("INCLUDETAB") or []
    print(f"  Saved {out_path} — {len(lines)} lines, {len(src)} bytes, {len(inctab)} includes from INCLUDETAB")
    # also dump first 30 lines so we can eyeball the LDB structure declaration
    print("  --- first 25 lines ---")
    for i, l in enumerate(lines[:25], 1):
        print(f"  {i:3} {l}")
except Exception as e:
    print(f"  SAPDBFPMF: ERROR {e}")

print("\n=== DBNTAB (LDB nodes) for FPMF ===")
try:
    r = guard.call("RFC_READ_TABLE", QUERY_TABLE="DBNTAB",
                   OPTIONS=[{"TEXT": "DBNAME = 'FPMF'"}],
                   FIELDS=[{"FIELDNAME":"DBNAME"},{"FIELDNAME":"DBSTRUCT"},
                           {"FIELDNAME":"NODE"},{"FIELDNAME":"NODESUPER"}],
                   ROWCOUNT=50)
    for d in r.get("DATA", []):
        print(f"  {d['WA']}")
except Exception as e:
    print(f"  DBNTAB FPMF: ERROR {e}")
