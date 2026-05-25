import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-backend-server-python", ".env"))
from pyrfc import Connection

p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
     "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"),
     "passwd": os.getenv("SAP_PASSWD"), "lang": "EN"}
conn = Connection(**p)

# Inline ABAP — counts source lines for active AND inactive
abap = [
    {"LINE": "REPORT zdiag3."},
    {"LINE": "DATA: lt_a TYPE TABLE OF string,"},
    {"LINE": "      lt_i TYPE TABLE OF string,"},
    {"LINE": "      lt_d TYPE TABLE OF string,"},
    {"LINE": "      lv_n TYPE i,"},
    {"LINE": "      lv_l TYPE string."},
    {"LINE": ""},
    {"LINE": "* default"},
    {"LINE": "READ REPORT 'ZABAPGIT_STANDALONE' INTO lt_d."},
    {"LINE": "lv_n = lines( lt_d )."},
    {"LINE": "WRITE: / 'DEFAULT subrc=', sy-subrc, 'lines=', lv_n."},
    {"LINE": ""},
    {"LINE": "* explicit active"},
    {"LINE": "READ REPORT 'ZABAPGIT_STANDALONE' INTO lt_a STATE 'A'."},
    {"LINE": "lv_n = lines( lt_a )."},
    {"LINE": "WRITE: / 'STATE_A subrc=', sy-subrc, 'lines=', lv_n."},
    {"LINE": ""},
    {"LINE": "* explicit inactive"},
    {"LINE": "READ REPORT 'ZABAPGIT_STANDALONE' INTO lt_i STATE 'I'."},
    {"LINE": "lv_n = lines( lt_i )."},
    {"LINE": "WRITE: / 'STATE_I subrc=', sy-subrc, 'lines=', lv_n."},
    {"LINE": ""},
    {"LINE": "* first 3 lines of default (whatever READ REPORT gave us)"},
    {"LINE": "LOOP AT lt_d INTO lv_l FROM 1 TO 3."},
    {"LINE": "  WRITE: / 'D', sy-tabix, ':', lv_l."},
    {"LINE": "ENDLOOP."},
]
r = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap, MODE="F")
print(f"WRITES count: {len(r.get('WRITES', []))}")
for w in r.get("WRITES", []):
    print(f"  {dict(w)}")
# Also print full response keys for debugging
print(f"All keys: {list(r.keys())}")
for k in r:
    if k != "WRITES":
        v = r[k]
        if isinstance(v, list) and v:
            print(f"  {k}: {len(v)} rows, first = {dict(v[0]) if hasattr(v[0],'keys') else v[0]}")
        elif v:
            print(f"  {k}: {v}")

conn.close()
