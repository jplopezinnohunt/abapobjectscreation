"""
v2: split each source line into ≤45-char chunks concatenated with `&&` so each
ABAP installer line stays under the 72-char PROGTAB limit.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

PKG = os.path.join(os.path.dirname(__file__), "..", "..",
                   "extracted_code", "FI", "SAPFPAYM", "ZSAPFPAYM_REPLAY")
with open(os.path.join(PKG, "ZSAPFPAYM_REPLAY.abap"), encoding="utf-8") as f:
    src_lines = f.read().splitlines()

CHUNK = 45  # chars per backtick chunk
ABAP_LINE_LIMIT = 72

def emit_append(line):
    """Emit ABAP statement(s) that APPEND a single source line to lt_src,
    splitting into chunks so each emitted line is ≤72 chars."""
    safe = line.replace("`", "")  # backticks aren't valid in our source anyway
    if not safe:
        return ["APPEND `` TO lt_src."]
    if len(safe) + 22 <= ABAP_LINE_LIMIT:  # "APPEND `...` TO lt_src." = 22 + len
        return [f"APPEND `{safe}` TO lt_src."]
    # Split into chunks
    chunks = [safe[i:i+CHUNK] for i in range(0, len(safe), CHUNK)]
    out = []
    for idx, ch in enumerate(chunks):
        if idx == 0:
            out.append(f"APPEND `{ch}` &&")
        elif idx < len(chunks) - 1:
            out.append(f"       `{ch}` &&")
        else:
            out.append(f"       `{ch}` TO lt_src.")
    return out

abap = [
    "REPORT zfix_install_zr.",
    "DATA: lt_src TYPE STANDARD TABLE OF string,",
    "      ls_trdir TYPE trdir.",
]
for line in src_lines:
    abap.extend(emit_append(line))

abap.extend([
    "ls_trdir-name    = 'ZSAPFPAYM_REPLAY'.",
    "ls_trdir-subc    = '1'.",
    "ls_trdir-ldbname = 'FPMF'.",
    "ls_trdir-appl    = 'F'.",
    "ls_trdir-uccheck = 'X'.",
    "ls_trdir-rload   = 'D'.",
    "ls_trdir-varcl   = 'X'.",
    "ls_trdir-fixpt   = 'X'.",
    "ls_trdir-cnam    = sy-uname.",
    "ls_trdir-cdat    = sy-datum.",
    "ls_trdir-rmand   = sy-mandt.",
    "ls_trdir-rstat   = 'P'.",
    "INSERT REPORT 'ZSAPFPAYM_REPLAY'",
    "  FROM lt_src DIRECTORY ENTRY ls_trdir.",
    "WRITE: / 'INSERT sy-subrc =', sy-subrc.",
    "COMMIT WORK.",
    "DATA: ls_chk TYPE trdir.",
    "SELECT SINGLE * FROM trdir INTO ls_chk",
    "  WHERE name = 'ZSAPFPAYM_REPLAY'.",
    "WRITE: / 'NAME=', ls_chk-name.",
    "WRITE: / 'SUBC=', ls_chk-subc.",
    "WRITE: / 'LDB =', ls_chk-ldbname.",
    "WRITE: / 'APPL=', ls_chk-appl.",
    "WRITE: / 'UCCHECK=', ls_chk-uccheck.",
    "WRITE: / 'RLOAD=', ls_chk-rload.",
])

# Verify all lines ≤72 chars
print(f"Total ABAP lines: {len(abap)}")
overlong = [(i+1, l) for i, l in enumerate(abap) if len(l) > 72]
if overlong:
    print(f"  WARNING: {len(overlong)} lines >72 chars")
    for i, l in overlong[:5]:
        print(f"    line {i} ({len(l)} chars): {l}")
else:
    print("  All lines ≤72 chars ✓")

print("\n=== Execute ===")
try:
    r = c.call("RFC_ABAP_INSTALL_AND_RUN", MODE='F',
               PROGRAMNAME='ZFIX_INSTALL_ZR',
               PROGRAM=[{"LINE": l} for l in abap])
    if r.get("ERRORMESSAGE"):
        print(f"  ERRORMESSAGE: {r.get('ERRORMESSAGE')}")
    print(f"  WRITES count: {len(r.get('WRITES') or [])}")
    for w in (r.get("WRITES") or []):
        txt = w.get("ZEILE") if isinstance(w, dict) else str(w)
        print(f"    {txt}")
except Exception as e:
    print(f"  FAIL: {e}")

# Independent verify
print("\n=== Independent TRDIR verify ===")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR",
           OPTIONS=[{"TEXT": "NAME = 'ZSAPFPAYM_REPLAY'"}],
           FIELDS=[{"FIELDNAME":"NAME"},{"FIELDNAME":"SUBC"},
                   {"FIELDNAME":"LDBNAME"},{"FIELDNAME":"APPL"}],
           DELIMITER='|')
for row in r.get("DATA",[]): print(f"  {row['WA']}")
if not r.get("DATA"): print("  NOT IN TRDIR")
