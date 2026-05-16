"""
Copy textpool (TEXT-XXX symbols + selection screen labels) from SAPFPAYM
to ZSAPFPAYM_REPLAY in D01.

Strategy: ABAP one-shot using READ TEXTPOOL + INSERT TEXTPOOL.
Languages: E (English) — primary. Add D / F / S optional later if needed.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

abap = [
    "REPORT zfix_textpool.",
    "DATA: lt_text TYPE STANDARD TABLE OF textpool.",
    "DATA: lv_count TYPE i.",
    "",
    "* Read textpool from original SAPFPAYM (English)",
    "READ TEXTPOOL 'SAPFPAYM' INTO lt_text",
    "  LANGUAGE 'E'.",
    "lv_count = LINES( lt_text ).",
    "WRITE: / 'Read SAPFPAYM textpool, entries:', lv_count.",
    "",
    "* Write to ZSAPFPAYM_REPLAY",
    "INSERT TEXTPOOL 'ZSAPFPAYM_REPLAY' FROM lt_text",
    "  LANGUAGE 'E' STATE 'A'.",
    "WRITE: / 'INSERT TEXTPOOL sy-subrc=', sy-subrc.",
    "COMMIT WORK.",
    "",
    "* Verify",
    "DATA: lt_chk TYPE STANDARD TABLE OF textpool.",
    "READ TEXTPOOL 'ZSAPFPAYM_REPLAY' INTO lt_chk",
    "  LANGUAGE 'E'.",
    "WRITE: / 'Verify ZSAPFPAYM_REPLAY entries:', LINES( lt_chk ).",
    "",
    "* Sample first 5 entries (id+key+entry)",
    "DATA: ls_t TYPE textpool.",
    "DATA: lv_i TYPE i VALUE 0.",
    "LOOP AT lt_chk INTO ls_t.",
    "  lv_i = lv_i + 1.",
    "  IF lv_i > 8. EXIT. ENDIF.",
    "  WRITE: / ls_t-id, ls_t-key, ls_t-entry.",
    "ENDLOOP.",
]

# Verify all lines ≤72 chars
overlong = [(i+1, l) for i, l in enumerate(abap) if len(l) > 72]
if overlong:
    print(f"WARN {len(overlong)} lines >72:")
    for i, l in overlong: print(f"  line {i} ({len(l)}): {l}")

print("=== ABAP textpool copier ===")
for i, l in enumerate(abap, 1):
    print(f"  {i:2}  {l}")
print()

try:
    r = c.call("RFC_ABAP_INSTALL_AND_RUN", MODE='F',
               PROGRAMNAME='ZFIX_TEXTPOOL',
               PROGRAM=[{"LINE": l} for l in abap])
    if r.get("ERRORMESSAGE"):
        print(f"ERRORMESSAGE: {r.get('ERRORMESSAGE')}")
    print("--- WRITES ---")
    for w in (r.get("WRITES") or []):
        txt = w.get("ZEILE") if isinstance(w, dict) else str(w)
        print(f"  {txt}")
except Exception as e:
    print(f"FAIL: {e}")
