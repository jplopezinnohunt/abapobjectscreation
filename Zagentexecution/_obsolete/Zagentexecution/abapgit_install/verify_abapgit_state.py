"""Verify ZABAPGIT_STANDALONE state via inline ABAP probe."""
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
    {"LINE": "REPORT zcheck_abapgit."},
    {"LINE": "DATA: lv_state TYPE c LENGTH 1,"},
    {"LINE": "      lv_lines TYPE i,"},
    {"LINE": "      lt_src TYPE TABLE OF string,"},
    {"LINE": "      lv_size TYPE i,"},
    {"LINE": "      lv_line TYPE string."},
    {"LINE": "SELECT SINGLE r3state FROM reposrc INTO lv_state"},
    {"LINE": "  WHERE progname = 'ZABAPGIT_STANDALONE'"},
    {"LINE": "    AND r3state = 'A'."},
    {"LINE": "IF sy-subrc = 0."},
    {"LINE": "  WRITE: / 'REPOSRC active row found, r3state =', lv_state."},
    {"LINE": "ELSE."},
    {"LINE": "  WRITE: / 'NO active REPOSRC row for ZABAPGIT_STANDALONE'."},
    {"LINE": "ENDIF."},
    {"LINE": "READ REPORT 'ZABAPGIT_STANDALONE' INTO lt_src."},
    {"LINE": "IF sy-subrc = 0."},
    {"LINE": "  lv_lines = lines( lt_src )."},
    {"LINE": "  WRITE: / 'READ REPORT lines:', lv_lines."},
    {"LINE": "  READ TABLE lt_src INDEX 1 INTO lv_line."},
    {"LINE": "  WRITE: / 'First line:', lv_line."},
    {"LINE": "ELSE."},
    {"LINE": "  WRITE: / 'READ REPORT failed sy-subrc =', sy-subrc."},
    {"LINE": "ENDIF."},
]
r = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap, MODE="F")
print("OUTPUT:")
for w in r.get("WRITES", []):
    print(f"  {w.get('LINE', w)!r}")
conn.close()
