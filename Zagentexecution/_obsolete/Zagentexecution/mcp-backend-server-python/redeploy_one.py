"""Redeploy ONE object from local file with all proper attributes."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

if len(sys.argv) < 2:
    print("Usage: python redeploy_one.py NAME [SUBC] [LDB]")
    sys.exit(1)
NAME = sys.argv[1]
SUBC = sys.argv[2] if len(sys.argv) >= 3 else "I"
LDB  = sys.argv[3] if len(sys.argv) >= 4 else ""

PKG = os.path.join(os.path.dirname(__file__), "..", "..",
                   "extracted_code", "FI", "SAPFPAYM", "ZSAPFPAYM_REPLAY")

CHUNK = 45
def emit_append(line):
    safe = line.replace("`", "")
    if not safe:
        return ["APPEND `` TO lt_src."]
    if len(safe) + 22 <= 72:
        return [f"APPEND `{safe}` TO lt_src."]
    chunks = [safe[i:i+CHUNK] for i in range(0, len(safe), CHUNK)]
    out = []
    for idx, ch in enumerate(chunks):
        if idx == 0: out.append(f"APPEND `{ch}` &&")
        elif idx < len(chunks) - 1: out.append(f"       `{ch}` &&")
        else: out.append(f"       `{ch}` TO lt_src.")
    return out

with open(os.path.join(PKG, NAME + ".abap"), encoding="utf-8") as f:
    src_lines = f.read().splitlines()
print(f"Installing {NAME} (SUBC={SUBC}, LDB='{LDB}'), {len(src_lines)} src lines")

abap = ["REPORT zfix_one.",
        "DATA: lt_src TYPE STANDARD TABLE OF string,",
        "      ls_trdir TYPE trdir."]
for ln in src_lines: abap.extend(emit_append(ln))
abap += [
    f"ls_trdir-name    = '{NAME}'.",
    f"ls_trdir-subc    = '{SUBC}'.",
]
if LDB: abap.append(f"ls_trdir-ldbname = '{LDB}'.")
abap += [
    "ls_trdir-appl    = 'F'.",
    "ls_trdir-uccheck = 'X'.",
    "ls_trdir-rload   = 'D'.",
    "ls_trdir-varcl   = 'X'.",
    "ls_trdir-fixpt   = 'X'.",
    "ls_trdir-cnam    = sy-uname.",
    "ls_trdir-cdat    = sy-datum.",
    "ls_trdir-rmand   = sy-mandt.",
    f"INSERT REPORT '{NAME}'",
    "  FROM lt_src DIRECTORY ENTRY ls_trdir.",
    "WRITE: / 'INSERT sy-subrc=', sy-subrc.",
    "COMMIT WORK.",
]
overlong = [(i+1,l) for i,l in enumerate(abap) if len(l) > 72]
if overlong:
    print(f"WARN {len(overlong)} lines >72")
    for i,l in overlong[:3]: print(f"  {i}({len(l)}): {l}")
    sys.exit(1)

c = get_connection("D01")
r = c.call("RFC_ABAP_INSTALL_AND_RUN", MODE='F', PROGRAMNAME='ZFIX_ONE',
           PROGRAM=[{"LINE": l} for l in abap])
if r.get("ERRORMESSAGE"): print("ERR:", r.get("ERRORMESSAGE"))
for w in (r.get("WRITES") or []):
    print(" ", w.get("ZEILE") if isinstance(w, dict) else w)
