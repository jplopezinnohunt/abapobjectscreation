"""
Copy COMPLETE textpool (all types: I, S, T, R, H) from SAPFPAYM
to ZSAPFPAYM_REPLAY in D01.

Key fact: READ TEXTPOOL fetches ALL text-pool entries regardless of type.
The previous "I only" appearance was just because the LOOP printed first 8.
This script verifies type distribution and re-copies if needed, then prints
selection-texts (S) and title (T) explicitly.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

abap = [
    "REPORT zfix_tp_full.",
    "DATA: lt_src TYPE STANDARD TABLE OF textpool,",
    "      lt_dst TYPE STANDARD TABLE OF textpool,",
    "      ls    TYPE textpool,",
    "      lv_i  TYPE i, lv_s TYPE i,",
    "      lv_t  TYPE i, lv_r TYPE i, lv_h TYPE i.",
    "",
    "READ TEXTPOOL 'SAPFPAYM' INTO lt_src",
    "  LANGUAGE 'E'.",
    "WRITE: / 'SRC total entries:', LINES( lt_src ).",
    "",
    "LOOP AT lt_src INTO ls.",
    "  CASE ls-id.",
    "    WHEN 'I'. lv_i = lv_i + 1.",
    "    WHEN 'S'. lv_s = lv_s + 1.",
    "    WHEN 'T'. lv_t = lv_t + 1.",
    "    WHEN 'R'. lv_r = lv_r + 1.",
    "    WHEN 'H'. lv_h = lv_h + 1.",
    "  ENDCASE.",
    "ENDLOOP.",
    "WRITE: / 'SRC by type — I:', lv_i, 'S:', lv_s,",
    "       'T:', lv_t, 'R:', lv_r, 'H:', lv_h.",
    "",
    "INSERT TEXTPOOL 'ZSAPFPAYM_REPLAY' FROM lt_src",
    "  LANGUAGE 'E' STATE 'A'.",
    "WRITE: / 'INSERT TEXTPOOL sy-subrc=', sy-subrc.",
    "COMMIT WORK.",
    "",
    "READ TEXTPOOL 'ZSAPFPAYM_REPLAY' INTO lt_dst",
    "  LANGUAGE 'E'.",
    "WRITE: / 'DST verify entries:', LINES( lt_dst ).",
    "",
    "* Print all selection-texts (type S) — these are PARAMETERS labels",
    "WRITE: / '--- Selection-texts (type S) ---'.",
    "LOOP AT lt_dst INTO ls WHERE id = 'S'.",
    "  WRITE: / ls-key, '=', ls-entry.",
    "ENDLOOP.",
    "",
    "* Print title (type R)",
    "WRITE: / '--- Title (R) ---'.",
    "LOOP AT lt_dst INTO ls WHERE id = 'R'.",
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
               PROGRAMNAME='ZFIX_TP_FULL',
               PROGRAM=[{"LINE": l} for l in abap])
    if r.get("ERRORMESSAGE"):
        print(f"ERRORMESSAGE: {r.get('ERRORMESSAGE')}")
    print("--- WRITES ---")
    for w in (r.get("WRITES") or []):
        txt = w.get("ZEILE") if isinstance(w, dict) else str(w)
        print(f"  {txt}")
except Exception as e:
    print(f"FAIL: {e}")
