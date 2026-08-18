import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-backend-server-python", ".env"))
from pyrfc import Connection

p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
     "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"),
     "passwd": os.getenv("SAP_PASSWD"), "lang": "EN"}
conn = Connection(**p)

# REPOSRC for ZABAPGIT_STANDALONE
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="REPOSRC", DELIMITER="|",
              OPTIONS=[{"TEXT": "PROGNAME = 'ZABAPGIT_STANDALONE'"}],
              FIELDS=[{"FIELDNAME": "PROGNAME"}, {"FIELDNAME": "R3STATE"},
                      {"FIELDNAME": "UNAM"}, {"FIELDNAME": "UDAT"},
                      {"FIELDNAME": "VERSNO"}, {"FIELDNAME": "CNAM"}])
print(f"=== REPOSRC rows: {len(r.get('DATA', []))} ===")
for row in r.get("DATA", []):
    print(f"  {row['WA']}")

# REPOTEXT (source storage) — check row counts per state
print()
abap = [
    {"LINE": "REPORT zd2."},
    {"LINE": "DATA: lt_src TYPE TABLE OF string,"},
    {"LINE": "      lv_n TYPE i,"},
    {"LINE": "      lv_l TYPE string."},
    {"LINE": "READ REPORT 'ZABAPGIT_STANDALONE' INTO lt_src."},
    {"LINE": "lv_n = lines( lt_src )."},
    {"LINE": "WRITE: / 'default subrc=', sy-subrc, 'lines=', lv_n."},
    {"LINE": "IF lv_n > 0."},
    {"LINE": "  READ TABLE lt_src INDEX 1 INTO lv_l."},
    {"LINE": "  WRITE: / 'first:', lv_l."},
    {"LINE": "ENDIF."},
    {"LINE": "IF lv_n > 100."},
    {"LINE": "  READ TABLE lt_src INDEX lv_n INTO lv_l."},
    {"LINE": "  WRITE: / 'last:', lv_l."},
    {"LINE": "ENDIF."},
]
r = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap, MODE="F")
print(f"=== INSTALL_AND_RUN WRITES ({len(r.get('WRITES', []))} rows) ===")
for w in r.get("WRITES", []):
    print(f"  {dict(w)}")
print(f"=== other keys: {[k for k in r.keys() if k != 'WRITES']} ===")
for k in r.keys():
    if k != "WRITES":
        v = r[k]
        if isinstance(v, list) and v:
            print(f"  {k}[0]: {dict(v[0]) if hasattr(v[0],'keys') else v[0]}")
        else:
            print(f"  {k}: {v}")

conn.close()
