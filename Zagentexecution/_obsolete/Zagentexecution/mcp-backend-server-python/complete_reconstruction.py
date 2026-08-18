import os, sys
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    p = {"ashost": "172.16.4.66", "sysnr": "00", "client": "350", 
         "user": os.getenv("SAP_USER"), "lang": "EN"}
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"; p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = "9"
    return Connection(**p)

def execute_abap(abap_code, label=""):
    conn = get_conn()
    if label:
        print(f"\n[{label}]")
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

if __name__ == "__main__":
    classes = [
        ("ZCL_CRP_PROCESS_REQ", "CRP Process Request Delegate"),
        ("ZCL_Z_CRP_SRV_DPC_EXT", "CRP Data Provider Extension"),
    ]
    
    for cls_name, cls_desc in classes:
        # Get the interface for SEO_CLASS_CREATE
        abap_code = f"""
REPORT Z_RECONSTRUCT_CLASS.
DATA: lv_clsname TYPE seoclsname VALUE '{cls_name}'.
DATA: lv_state   TYPE seostate.

* 1. Check if entry already exists
SELECT SINGLE state FROM seoclassdf
  INTO lv_state
  WHERE clsname = lv_clsname.

WRITE: / 'Current state in SEOCLASSDF:', sy-subrc, lv_state.

IF sy-subrc <> 0.
  WRITE: / 'Class NOT in ClassBuilder, forced registration needed'.
ELSE.
  WRITE: / 'Class already in ClassBuilder - state:', lv_state.
ENDIF.

* 2. Get the class source (main CU include = class definition)
DATA: lt_source TYPE abaptxt255_tab.
CALL FUNCTION 'SEO_CLASS_CREATE_SOURCE'
  EXPORTING
    clskey           = VALUE seoclskey( clsname = lv_clsname )
  IMPORTING
    result           = lt_source
  EXCEPTIONS
    class_not_found  = 1
    not_class        = 2
    OTHERS           = 3.
WRITE: / 'SEO_CLASS_CREATE_SOURCE subrc:', sy-subrc.

IF sy-subrc = 0.
  WRITE: / 'Generated source has', lines( lt_source ), 'lines'.
ENDIF.

* 3. Try full class creation via SEO_CLASS_CREATE_COMPLETE
CALL FUNCTION 'SEO_CLASS_CREATE_COMPLETE'
  EXPORTING
    clskey           = VALUE seoclskey( clsname = lv_clsname )
    devclass         = 'ZCRP'
    corrnr           = 'D01K9B0EWT'
    version          = '1'
  EXCEPTIONS
    class_already_existing = 1
    class_not_creatable    = 2
    OTHERS                 = 3.
WRITE: / 'SEO_CLASS_CREATE_COMPLETE subrc:', sy-subrc.

* 4. Activate once metadata is in place
CALL FUNCTION 'SEO_CLASS_ACTIVATE'
  EXPORTING
    clskey           = VALUE seoclskey( clsname = lv_clsname )
  EXCEPTIONS
    class_not_found  = 1
    OTHERS           = 2.
WRITE: / 'SEO_CLASS_ACTIVATE subrc:', sy-subrc.
"""
        execute_abap(abap_code, f"RECONSTRUCT {cls_name}")
