"""Probe whether RPY_PROGRAM_INSERT accepts LDBNAME / APPLICATION params."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

# 1) DELETE existing ZSAPFPAYM_REPLAY via RFC_ABAP_INSTALL_AND_RUN
print("=== DELETE ZSAPFPAYM_REPLAY ===")
del_lines = [
    "REPORT zfix_del_zr.",
    "DELETE REPORT 'ZSAPFPAYM_REPLAY'.",
    "WRITE: / 'Deleted, sy-subrc=', sy-subrc.",
    "COMMIT WORK.",
]
try:
    r = c.call("RFC_ABAP_INSTALL_AND_RUN",
               MODE='F',
               PROGRAMNAME='ZFIX_DEL_ZR',
               PROGRAM=[{"LINE": l} for l in del_lines])
    for w in (r.get("WRITES") or []):
        print(f"  {w.get('LINE') if isinstance(w, dict) else w}")
except Exception as e:
    print(f"  FAIL: {e}")

# 2) Try INSERT with LDBNAME param
print("\n=== INSERT with LDBNAME='FPMF' (test param) ===")
PKG = os.path.join(os.path.dirname(__file__), "..", "..",
                   "extracted_code", "FI", "SAPFPAYM", "ZSAPFPAYM_REPLAY")
with open(os.path.join(PKG, "ZSAPFPAYM_REPLAY.abap"), encoding="utf-8") as f:
    text = f.read()
src_tab = [{"LINE": l[:255]} for l in text.splitlines()]

# Try several param-name variants
for params in [
    {"LDBNAME": "FPMF", "APPLICATION": "F"},
    {"LDB_NAME": "FPMF", "APPL": "F"},
    {"LOGICAL_DATABASE": "FPMF"},
]:
    print(f"\n  Trying {params} ...")
    try:
        c.call("RPY_PROGRAM_INSERT",
               DEVELOPMENT_CLASS="$TMP",
               PROGRAM_NAME="ZSAPFPAYM_REPLAY",
               PROGRAM_TYPE="1",
               TITLE_STRING="Z REPLAY",
               SUPPRESS_DIALOG="X",
               SAVE_INACTIVE="",
               SOURCE_EXTENDED=src_tab,
               **params)
        print(f"    ✓ SUCCESS with {params}")
        break
    except Exception as e:
        emsg = str(e)
        if "RFC_INVALID_PARAMETER" in emsg:
            unknown = emsg.split("field '")[1].split("'")[0] if "field '" in emsg else "?"
            print(f"    ✗ unknown param: {unknown}")
        elif "ALREADY_EXISTS" in emsg:
            print(f"    ✗ ALREADY_EXISTS — DELETE didn't work? Re-running delete...")
            break
        else:
            print(f"    ✗ {emsg[:200]}")

# Verify TRDIR after
print("\n=== TRDIR after attempts ===")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR",
           OPTIONS=[{"TEXT": "NAME = 'ZSAPFPAYM_REPLAY'"}],
           FIELDS=[{"FIELDNAME":"NAME"},{"FIELDNAME":"SUBC"},
                   {"FIELDNAME":"LDBNAME"},{"FIELDNAME":"APPL"}],
           DELIMITER='|')
for row in r.get("DATA",[]):
    print(f"  {row['WA']}")
