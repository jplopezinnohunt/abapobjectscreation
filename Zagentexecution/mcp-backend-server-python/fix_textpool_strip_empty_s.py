"""
Strip empty/placeholder selection-texts (type S with value 'D       .') from
ZSAPFPAYM_REPLAY textpool, so SAP falls back to data-element labels.
Keep all I, T, R types intact.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

abap = [
    "REPORT zfix_strip_s.",
    "DATA: lt_text TYPE STANDARD TABLE OF textpool,",
    "      lt_keep TYPE STANDARD TABLE OF textpool,",
    "      ls TYPE textpool,",
    "      lv_dropped TYPE i, lv_kept TYPE i.",
    "",
    "READ TEXTPOOL 'ZSAPFPAYM_REPLAY' INTO lt_text",
    "  LANGUAGE 'E'.",
    "WRITE: / 'Before strip:', LINES( lt_text ).",
    "",
    "LOOP AT lt_text INTO ls.",
    "* drop S-type entries that are empty or placeholder",
    "  IF ls-id = 'S'.",
    "    DATA(lv_e) = ls-entry.",
    "    CONDENSE lv_e.",
    "    IF lv_e IS INITIAL OR lv_e CS 'D' AND",
    "       strlen( lv_e ) <= 3.",
    "      lv_dropped = lv_dropped + 1.",
    "      CONTINUE.",
    "    ENDIF.",
    "  ENDIF.",
    "  APPEND ls TO lt_keep.",
    "  lv_kept = lv_kept + 1.",
    "ENDLOOP.",
    "",
    "WRITE: / 'After strip — keep:', lv_kept,",
    "       'dropped:', lv_dropped.",
    "",
    "* Re-write reduced textpool",
    "INSERT TEXTPOOL 'ZSAPFPAYM_REPLAY' FROM lt_keep",
    "  LANGUAGE 'E' STATE 'A'.",
    "WRITE: / 'INSERT sy-subrc=', sy-subrc.",
    "COMMIT WORK.",
    "",
    "* Verify what S entries remain (should be only those with real text)",
    "DATA: lt_chk TYPE STANDARD TABLE OF textpool.",
    "READ TEXTPOOL 'ZSAPFPAYM_REPLAY' INTO lt_chk",
    "  LANGUAGE 'E'.",
    "WRITE: / 'Final entries:', LINES( lt_chk ).",
    "WRITE: / '--- remaining S entries ---'.",
    "LOOP AT lt_chk INTO ls WHERE id = 'S'.",
    "  WRITE: / ls-key, '=', ls-entry.",
    "ENDLOOP.",
]

# Verify ≤72 chars
overlong = [(i+1, l) for i, l in enumerate(abap) if len(l) > 72]
if overlong:
    print(f"WARN {len(overlong)} lines >72:")
    for i, l in overlong: print(f"  line {i} ({len(l)}): {l}")

try:
    r = c.call("RFC_ABAP_INSTALL_AND_RUN", MODE='F',
               PROGRAMNAME='ZFIX_STRIP_S',
               PROGRAM=[{"LINE": l} for l in abap])
    if r.get("ERRORMESSAGE"):
        print(f"ERRORMESSAGE: {r.get('ERRORMESSAGE')}")
    print("--- WRITES ---")
    for w in (r.get("WRITES") or []):
        txt = w.get("ZEILE") if isinstance(w, dict) else str(w)
        print(f"  {txt}")
except Exception as e:
    print(f"FAIL: {e}")
