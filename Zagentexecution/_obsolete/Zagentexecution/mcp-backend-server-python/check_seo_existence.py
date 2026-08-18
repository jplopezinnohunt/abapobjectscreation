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
    # The issue is that SEOCLASSDF has SEOSTATE/SEOEXPOSE fields
    # RFC_ABAP_INSTALL_AND_RUN runs in limited context where some type symbols 
    # are not available. We need to use pure table fields (TYPE seoclass / seoclassdf)
    # or flat field declarations.
    
    # Strategy: Use SEO_CLASS_CREATE (table method) with correct SEOC_CLASSES_W type
    # This was revealed by the earlier RFC function interface dump
    
    execute_abap("""
REPORT Z_CHECK_SEO_EXISTENCE.
DATA: lv_clsname TYPE seoclsname VALUE 'ZCL_CRP_PROCESS_REQ'.
DATA: lv_uuid    TYPE sysuuid_x.
DATA: lv_subrc   TYPE sysubrc.

* Read SEOCLASS directly (transparent table)
SELECT SINGLE clsname uuid FROM seoclass
  INTO (DATA(lv_cls_found), lv_uuid)
  WHERE clsname = lv_clsname.
lv_subrc = sy-subrc.

IF lv_subrc = 0.
  WRITE: / 'SEOCLASS: FOUND - UUID length', STRLEN( lv_uuid ).
ELSE.
  WRITE: / 'SEOCLASS: NOT IN TABLE (missing registration)'.
ENDIF.

* Also check SEOCLASSDF
DATA: lv_state TYPE seostate.
SELECT SINGLE state FROM seoclassdf
  INTO lv_state
  WHERE clsname = lv_clsname.
IF sy-subrc = 0.
  WRITE: / 'SEOCLASSDF: state=', lv_state.
ELSE.
  WRITE: / 'SEOCLASSDF: NOT FOUND'.
ENDIF.
""", "CHECK SEOCLASS EXISTENCE")

    # Step 2: Check if SEO_CLASS_CREATE_OBJECT exists locally in this system
    execute_abap("""
REPORT Z_CHECK_FUNC.
DATA: lt_func TYPE TABLE OF tfdir.
SELECT funcname FROM tfdir INTO TABLE lt_func
  WHERE funcname LIKE 'SEO%CLASS%CREATE%'
  OR funcname LIKE 'SEO%OBJECT%CRE%'.
LOOP AT lt_func INTO DATA(ls_func).
  WRITE: / ls_func-funcname.
ENDLOOP.
IF lines( lt_func ) = 0.
  WRITE: / 'No matching functions found'.
ENDIF.
""", "AVAILABLE CLASS CREATION FUNCTIONS")
