"""Drop the residual 6-line INACTIVE shell of ZABAPGIT_STANDALONE without
touching the active 151,660-line version. Leftover from v1 ADT REST create."""
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
    {"LINE": "REPORT zclean_inactive."},
    {"LINE": "DATA: lt_src TYPE TABLE OF string,"},
    {"LINE": "      lv_n TYPE i."},
    {"LINE": ""},
    {"LINE": "* Pre-state"},
    {"LINE": "READ REPORT 'ZABAPGIT_STANDALONE' INTO lt_src STATE 'A'."},
    {"LINE": "lv_n = lines( lt_src )."},
    {"LINE": "WRITE: / 'PRE active:', lv_n."},
    {"LINE": "READ REPORT 'ZABAPGIT_STANDALONE' INTO lt_src STATE 'I'."},
    {"LINE": "lv_n = lines( lt_src )."},
    {"LINE": "WRITE: / 'PRE inactive:', lv_n."},
    {"LINE": ""},
    {"LINE": "* Delete only the inactive version"},
    {"LINE": "DELETE REPORT 'ZABAPGIT_STANDALONE' STATE 'I'."},
    {"LINE": "WRITE: / 'DELETE inactive subrc=', sy-subrc."},
    {"LINE": ""},
    {"LINE": "* Post-state"},
    {"LINE": "READ REPORT 'ZABAPGIT_STANDALONE' INTO lt_src STATE 'A'."},
    {"LINE": "lv_n = lines( lt_src )."},
    {"LINE": "WRITE: / 'POST active:', lv_n, 'subrc=', sy-subrc."},
    {"LINE": "READ REPORT 'ZABAPGIT_STANDALONE' INTO lt_src STATE 'I'."},
    {"LINE": "lv_n = lines( lt_src )."},
    {"LINE": "WRITE: / 'POST inactive:', lv_n, 'subrc=', sy-subrc."},
]
r = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap, MODE="F")
print(f"WRITES count: {len(r.get('WRITES', []))}")
for w in r.get("WRITES", []):
    print(f"  {w.get('ZEILE', dict(w))}")

# Print error if any
if r.get("ERRORMESSAGE"):
    print(f"ERROR: {r['ERRORMESSAGE']}")

conn.close()
