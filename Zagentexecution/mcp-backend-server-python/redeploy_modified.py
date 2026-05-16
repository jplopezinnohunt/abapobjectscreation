"""
Re-deploy ONLY the 3 modified Z includes (ZFPAYM_STA, ZFPAYM_GET, ZFPAYM_END)
plus the driver ZSAPFPAYM_REPLAY.

Strategy:
  1) DELETE REPORT via RFC_ABAP_INSTALL_AND_RUN (1 call, deletes all 4)
  2) RPY_PROGRAM_INSERT for each (already verified working)
  3) UPDATE TRDIR.LDBNAME='FPMF', APPL='F' for ZSAPFPAYM_REPLAY (via RFC_ABAP_INSTALL_AND_RUN)
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

PKG_DIR = os.path.join(os.path.dirname(__file__), "..", "..",
                       "extracted_code", "FI", "SAPFPAYM", "ZSAPFPAYM_REPLAY")

REDEPLOY = [
    ("ZFPAYM_STA",       "I", "Z Replay - Start of selection (CHECKs removed)"),
    ("ZFPAYM_GET",       "I", "Z Replay - Get payment data + DMEE break-point"),
    ("ZFPAYM_END",       "I", "Z Replay - End of selection + ROLLBACK"),
    ("ZSAPFPAYM_REPLAY", "1", "Z Payment Medium REPLAY (no checks, ROLLBACK at end)"),
]

c = get_connection("D01")

# === Step 1: DELETE the 4 reports/includes via ABAP one-shot ===
print("=== Step 1: DELETE REPORT for the 4 modified objects ===")
del_lines = ["REPORT zfix_delete."]
for name, _, _ in REDEPLOY:
    del_lines.append(f"DELETE REPORT '{name}'.")
    del_lines.append(f"WRITE: / 'Deleted', '{name}', sy-subrc.")
del_lines.append("COMMIT WORK.")

try:
    r = c.call("RFC_ABAP_INSTALL_AND_RUN",
               MODE='F',
               PROGRAMNAME='ZFIX_DELETE',
               PROGRAM=[{"LINE": l} for l in del_lines])
    for w in (r.get("WRITES") or []):
        txt = w.get("LINE") if isinstance(w, dict) else str(w)
        print(f"  {txt}")
    for e in (r.get("ERRORS") or []):
        txt = e.get("LINE") if isinstance(e, dict) else str(e)
        print(f"  ERR: {txt}")
except Exception as e:
    print(f"  FAIL: {e}")

# === Step 2: RPY_PROGRAM_INSERT each ===
print("\n=== Step 2: RPY_PROGRAM_INSERT (re-create) ===")
for name, ptype, title in REDEPLOY:
    path = os.path.join(PKG_DIR, name + ".abap")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    src_tab = [{"LINE": l[:255]} for l in text.splitlines()]
    try:
        c.call("RPY_PROGRAM_INSERT",
               DEVELOPMENT_CLASS="$TMP",
               PROGRAM_NAME=name,
               PROGRAM_TYPE=ptype,
               TITLE_STRING=title,
               SUPPRESS_DIALOG="X",
               SAVE_INACTIVE="",
               SOURCE_EXTENDED=src_tab)
        print(f"  ✓ {name} ({ptype}) — {len(src_tab)} lines INSERTED")
    except Exception as e:
        print(f"  ✗ {name} INSERT FAIL: {str(e)[:200]}")

# === Step 3: Assign LDB FPMF + APPL='F' to ZSAPFPAYM_REPLAY ===
print("\n=== Step 3: UPDATE TRDIR — assign LDB FPMF ===")
trdir_lines = [
    "REPORT zfix_trdir_ldb.",
    "DATA: lv_count TYPE i.",
    "UPDATE trdir SET ldbname = 'FPMF'",
    "                 appl    = 'F'",
    "           WHERE name = 'ZSAPFPAYM_REPLAY'.",
    "lv_count = sy-dbcnt.",
    "WRITE: / 'TRDIR rows updated:', lv_count.",
    "COMMIT WORK.",
    "DATA: ls_trdir TYPE trdir.",
    "SELECT SINGLE * FROM trdir INTO ls_trdir WHERE name = 'ZSAPFPAYM_REPLAY'.",
    "WRITE: / 'Verify NAME    =', ls_trdir-name.",
    "WRITE: / 'Verify SUBC    =', ls_trdir-subc.",
    "WRITE: / 'Verify LDBNAME =', ls_trdir-ldbname.",
    "WRITE: / 'Verify APPL    =', ls_trdir-appl.",
]
try:
    r = c.call("RFC_ABAP_INSTALL_AND_RUN",
               MODE='F',
               PROGRAMNAME='ZFIX_TRDIR_LDB',
               PROGRAM=[{"LINE": l} for l in trdir_lines])
    for w in (r.get("WRITES") or []):
        txt = w.get("LINE") if isinstance(w, dict) else str(w)
        print(f"  {txt}")
    for e in (r.get("ERRORS") or []):
        txt = e.get("LINE") if isinstance(e, dict) else str(e)
        print(f"  ERR: {txt}")
except Exception as e:
    print(f"  FAIL: {e}")
