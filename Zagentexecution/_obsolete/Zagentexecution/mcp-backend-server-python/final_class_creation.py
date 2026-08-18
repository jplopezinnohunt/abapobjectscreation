"""
FINAL CLASS CREATION SCRIPT
Uses RFC_ABAP_INSTALL_AND_RUN with correct flat declarations.
Key findings:
- SEOCLASSTX: 3 fields only (CLSNAME, LANGU, DESCRIPT) - no VERSION field!
- VSEOCLASS: full class description view
- ABAP bridge cannot use VALUE(), inline DATA(), or modern ABAP 
- Must use OLD-STYLE ABAP (TYPE declarations, explicit table operations)
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pyrfc import Connection, RFCError
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    p = {"ashost": "172.16.4.66", "sysnr": "00", "client": "350",
         "user": os.getenv("SAP_USER"), "lang": "EN"}
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"
        p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = "9"
    return Connection(**p)

def execute_abap(abap_code, label=""):
    conn = get_conn()
    if label: print(f"\n[{label}]")
    abap_source = [{"LINE": line[:72]} for line in abap_code.split('\n')]
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap_source)
        writes = res.get("WRITES", [])
        for w in writes:
            val = w.get('ZEILE') or list(w.values())[0]
            print(f"  SAP: {val}")
        if res.get("ERRORMESSAGE"):
            print(f"  ERROR: {res.get('ERRORMESSAGE')}")
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
        return None
    finally:
        conn.close()

CLASSES = [
    ("ZCL_CRP_PROCESS_REQ",     "CRP Process Request Delegate"),
    ("ZCL_Z_CRP_SRV_DPC_EXT",  "CRP OData Data Provider Extension"),
]

for cls_name, cls_desc in CLASSES:
    abap = """
REPORT Z_CREATE_CLASS.
DATA: ls_class      TYPE vseoclass.
DATA: ls_clskey     TYPE seoclskey.
DATA: lt_clasdesc   TYPE TABLE OF seoclasstx.
DATA: ls_clasdesc   TYPE seoclasstx.
DATA: lv_state      TYPE c.
DATA: lv_korrnr     TYPE trkorr.

ls_class-clsname   = '$CLSNAME$'.
ls_class-version   = '1'.
ls_class-category  = '00'.
ls_class-exposure  = '2'.
ls_class-state     = '1'.
ls_class-fixpt     = 'X'.
ls_class-unicode   = 'X'.
ls_class-author    = sy-uname.
ls_class-createdon = sy-datum.
ls_class-descript  = '$CLSDESC$'.
ls_class-langu     = 'E'.

ls_clasdesc-clsname  = '$CLSNAME$'.
ls_clasdesc-langu    = 'E'.
ls_clasdesc-descript = '$CLSDESC$'.
APPEND ls_clasdesc TO lt_clasdesc.

ls_clskey-clsname = '$CLSNAME$'.

* Check current state
SELECT SINGLE state FROM seoclassdf
  INTO lv_state
  WHERE clsname = '$CLSNAME$'.
WRITE: / 'SEOCLASSDF subrc:', sy-subrc.

* Create
CALL FUNCTION 'SEO_CLASS_CREATE_COMPLETE'
  CHANGING
    class              = ls_class
  EXPORTING
    devclass           = 'ZCRP'
    corrnr             = 'D01K9B0EWT'
    version            = '1'
    overwrite          = 'X'
    suppress_dialog    = 'X'
    suppress_corr      = ''
    suppress_commit    = ''
    suppress_method_generation = ''
  IMPORTING
    korrnr             = lv_korrnr
  TABLES
    class_descriptions = lt_clasdesc
  EXCEPTIONS
    existing           = 1
    db_error           = 2
    component_error    = 3
    no_access          = 4
    other              = 5.

WRITE: / 'CREATE_COMPLETE subrc:', sy-subrc, 'TR:', lv_korrnr.

* Activate
CALL FUNCTION 'SEO_CLASS_ACTIVATE'
  EXPORTING
    clskey          = ls_clskey
  EXCEPTIONS
    class_not_found = 1
    OTHERS          = 2.
WRITE: / 'ACTIVATE subrc:', sy-subrc.
"""
    # Replace placeholders ensuring within 72-char ABAP line limit
    abap = abap.replace("$CLSNAME$", cls_name).replace("$CLSDESC$", cls_desc[:40])
    execute_abap(abap, f"CREATE {cls_name}")
