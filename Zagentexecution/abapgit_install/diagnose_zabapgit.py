"""Exhaustive diagnostic of ZABAPGIT_STANDALONE state on D01.
Checks TADIR, TRDIR, REPOSRC (all r3state values), reads source for each version,
counts lines, first/last line preview.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-backend-server-python", ".env"))
from pyrfc import Connection

p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
     "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"),
     "passwd": os.getenv("SAP_PASSWD"), "lang": "EN"}
conn = Connection(**p)

abap = [
    {"LINE": "REPORT zdiag_zabapgit."},
    {"LINE": "DATA: lt_src TYPE TABLE OF string,"},
    {"LINE": "      lv_line TYPE string,"},
    {"LINE": "      lv_lines TYPE i."},
    {"LINE": ""},
    {"LINE": "WRITE: / '=== TADIR ==='."},
    {"LINE": "SELECT pgmid object obj_name devclass author created_on edtflag"},
    {"LINE": "  FROM tadir INTO TABLE @DATA(lt_tadir)"},
    {"LINE": "  WHERE obj_name = 'ZABAPGIT_STANDALONE'."},
    {"LINE": "LOOP AT lt_tadir ASSIGNING FIELD-SYMBOL(<t>)."},
    {"LINE": "  WRITE: / <t>-pgmid, <t>-object, <t>-obj_name, 'DEVC=', <t>-devclass,"},
    {"LINE": "           'AUTH=', <t>-author, 'CR=', <t>-created_on, 'EDT=', <t>-edtflag."},
    {"LINE": "ENDLOOP."},
    {"LINE": ""},
    {"LINE": "WRITE: / '=== TRDIR ==='."},
    {"LINE": "SELECT name subc cnam cdat unam udat"},
    {"LINE": "  FROM trdir INTO TABLE @DATA(lt_trdir)"},
    {"LINE": "  WHERE name = 'ZABAPGIT_STANDALONE'."},
    {"LINE": "LOOP AT lt_trdir ASSIGNING FIELD-SYMBOL(<r>)."},
    {"LINE": "  WRITE: / <r>-name, 'SUBC=', <r>-subc,"},
    {"LINE": "           'CR_USER=', <r>-cnam, 'CR_DATE=', <r>-cdat,"},
    {"LINE": "           'CHG_USER=', <r>-unam, 'CHG_DATE=', <r>-udat."},
    {"LINE": "ENDLOOP."},
    {"LINE": ""},
    {"LINE": "WRITE: / '=== REPOSRC (all r3state values) ==='."},
    {"LINE": "SELECT progname r3state unam udat utime versno"},
    {"LINE": "  FROM reposrc INTO TABLE @DATA(lt_repos)"},
    {"LINE": "  WHERE progname = 'ZABAPGIT_STANDALONE'."},
    {"LINE": "LOOP AT lt_repos ASSIGNING FIELD-SYMBOL(<s>)."},
    {"LINE": "  WRITE: / <s>-progname, 'R3STATE=', <s>-r3state,"},
    {"LINE": "           'UNAM=', <s>-unam, 'UDAT=', <s>-udat,"},
    {"LINE": "           'UTIME=', <s>-utime, 'VERSNO=', <s>-versno."},
    {"LINE": "ENDLOOP."},
    {"LINE": ""},
    {"LINE": "WRITE: / '=== READ REPORT (default = active) ==='."},
    {"LINE": "CLEAR lt_src."},
    {"LINE": "READ REPORT 'ZABAPGIT_STANDALONE' INTO lt_src."},
    {"LINE": "IF sy-subrc = 0."},
    {"LINE": "  lv_lines = lines( lt_src )."},
    {"LINE": "  WRITE: / 'Lines (active):', lv_lines."},
    {"LINE": "  READ TABLE lt_src INDEX 1 INTO lv_line."},
    {"LINE": "  WRITE: / 'L1:', lv_line."},
    {"LINE": "  READ TABLE lt_src INDEX 6 INTO lv_line."},
    {"LINE": "  WRITE: / 'L6:', lv_line."},
    {"LINE": "  IF lv_lines > 100."},
    {"LINE": "    READ TABLE lt_src INDEX lv_lines INTO lv_line."},
    {"LINE": "    WRITE: / 'LAST:', lv_line."},
    {"LINE": "  ENDIF."},
    {"LINE": "ELSE."},
    {"LINE": "  WRITE: / 'READ REPORT default failed sy-subrc =', sy-subrc."},
    {"LINE": "ENDIF."},
    {"LINE": ""},
    {"LINE": "WRITE: / '=== READ REPORT STATE = I (inactive) ==='."},
    {"LINE": "CLEAR lt_src."},
    {"LINE": "READ REPORT 'ZABAPGIT_STANDALONE' INTO lt_src STATE 'I'."},
    {"LINE": "IF sy-subrc = 0."},
    {"LINE": "  lv_lines = lines( lt_src )."},
    {"LINE": "  WRITE: / 'Lines (inactive):', lv_lines."},
    {"LINE": "  IF lv_lines >= 1."},
    {"LINE": "    READ TABLE lt_src INDEX 1 INTO lv_line."},
    {"LINE": "    WRITE: / 'L1:', lv_line."},
    {"LINE": "  ENDIF."},
    {"LINE": "  IF lv_lines >= 6."},
    {"LINE": "    READ TABLE lt_src INDEX 6 INTO lv_line."},
    {"LINE": "    WRITE: / 'L6:', lv_line."},
    {"LINE": "  ENDIF."},
    {"LINE": "ELSE."},
    {"LINE": "  WRITE: / 'No inactive version sy-subrc =', sy-subrc."},
    {"LINE": "ENDIF."},
    {"LINE": ""},
    {"LINE": "WRITE: / '=== READ REPORT STATE = A (active explicit) ==='."},
    {"LINE": "CLEAR lt_src."},
    {"LINE": "READ REPORT 'ZABAPGIT_STANDALONE' INTO lt_src STATE 'A'."},
    {"LINE": "IF sy-subrc = 0."},
    {"LINE": "  lv_lines = lines( lt_src )."},
    {"LINE": "  WRITE: / 'Lines (active explicit):', lv_lines."},
    {"LINE": "ELSE."},
    {"LINE": "  WRITE: / 'No active version sy-subrc =', sy-subrc."},
    {"LINE": "ENDIF."},
]
r = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap, MODE="F")
print("OUTPUT:")
for w in r.get("WRITES", []):
    line = w.get("LINE") or w.get("ZEILE", "")
    print(f"  {line}")
conn.close()
