"""Add the 2 missing selection-texts (PAR_BELP, PAR_XFIL) to ZSAPFPAYM_REPLAY."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

abap = [
    "REPORT zfix_seltext.",
    "DATA: lt_text TYPE STANDARD TABLE OF textpool,",
    "      ls TYPE textpool.",
    "READ TEXTPOOL 'ZSAPFPAYM_REPLAY' INTO lt_text",
    "  LANGUAGE 'E'.",
    "",
    "* Add PAR_BELP if missing",
    "READ TABLE lt_text INTO ls",
    "  WITH KEY id = 'S' key = 'PAR_BELP'.",
    "IF sy-subrc <> 0.",
    "  ls-id = 'S'. ls-key = 'PAR_BELP'.",
    "  ls-entry = 'Payment Document Validation'.",
    "  APPEND ls TO lt_text.",
    "  WRITE: / 'Added PAR_BELP'.",
    "ENDIF.",
    "",
    "* Add PAR_XFIL if missing",
    "READ TABLE lt_text INTO ls",
    "  WITH KEY id = 'S' key = 'PAR_XFIL'.",
    "IF sy-subrc <> 0.",
    "  ls-id = 'S'. ls-key = 'PAR_XFIL'.",
    "  ls-entry = 'Output to file system'.",
    "  APPEND ls TO lt_text.",
    "  WRITE: / 'Added PAR_XFIL'.",
    "ENDIF.",
    "",
    "* Add PAR_FILE if missing",
    "READ TABLE lt_text INTO ls",
    "  WITH KEY id = 'S' key = 'PAR_FILE'.",
    "IF sy-subrc <> 0.",
    "  ls-id = 'S'. ls-key = 'PAR_FILE'.",
    "  ls-entry = 'File name'.",
    "  APPEND ls TO lt_text.",
    "  WRITE: / 'Added PAR_FILE'.",
    "ENDIF.",
    "",
    "* Add PAR_SCRN",
    "READ TABLE lt_text INTO ls",
    "  WITH KEY id = 'S' key = 'PAR_SCRN'.",
    "IF sy-subrc <> 0.",
    "  ls-id = 'S'. ls-key = 'PAR_SCRN'.",
    "  ls-entry = 'Screen Output'.",
    "  APPEND ls TO lt_text.",
    "  WRITE: / 'Added PAR_SCRN'.",
    "ENDIF.",
    "",
    "* Add PAR_VARI",
    "READ TABLE lt_text INTO ls",
    "  WITH KEY id = 'S' key = 'PAR_VARI'.",
    "IF sy-subrc <> 0.",
    "  ls-id = 'S'. ls-key = 'PAR_VARI'.",
    "  ls-entry = 'Payment Summary Layout'.",
    "  APPEND ls TO lt_text.",
    "  WRITE: / 'Added PAR_VARI'.",
    "ENDIF.",
    "",
    "* Persist",
    "INSERT TEXTPOOL 'ZSAPFPAYM_REPLAY' FROM lt_text",
    "  LANGUAGE 'E' STATE 'A'.",
    "WRITE: / 'INSERT sy-subrc=', sy-subrc.",
    "COMMIT WORK.",
]
overlong = [(i+1, l) for i, l in enumerate(abap) if len(l) > 72]
if overlong:
    print(f"WARN {len(overlong)} >72:")
    for i, l in overlong: print(f"  {i}({len(l)}): {l}")

r = c.call("RFC_ABAP_INSTALL_AND_RUN", MODE='F',
           PROGRAMNAME='ZFIX_SELTEXT',
           PROGRAM=[{"LINE": l} for l in abap])
if r.get("ERRORMESSAGE"): print("ERR:", r.get("ERRORMESSAGE"))
for w in (r.get("WRITES") or []):
    print(" ", w.get("ZEILE") if isinstance(w, dict) else w)
