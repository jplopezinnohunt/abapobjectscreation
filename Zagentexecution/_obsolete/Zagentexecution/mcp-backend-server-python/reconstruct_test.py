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

def execute_abap_script(abap_code):
    conn = get_conn()
    print("Executing ABAP Bridge Reconstruction script...")
    # Wrap in simple report statement if not provided
    if "REPORT " not in abap_code.upper():
        abap_code = "REPORT Z_AI_TOOL.\n" + abap_code
    
    abap_source = [{"LINE": line[:72]} for line in abap_code.split('\n')]
    
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap_source)
        print("  [OK] Script finished.")
        # Some versions use 'LINE', 'TEXT' or 'ZEILE'
        writes = res.get("WRITES", [])
        for w in writes:
            val = w.get('ZEILE') or w.get('LINE') or w.get('TEXT') or list(w.values())[0]
            print(f"  SAP Log: {val}")
            
        error = res.get("ERRORMESSAGE")
        if error:
            print(f"  SAP ERROR: {error}")
            
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    # Simplified Reconstruction (Test with just one class and one method)
    abap_reconstruct = """
REPORT Z_RECONSTRUCT_CLASSES.
DATA: lv_clsname TYPE seoclsname VALUE 'ZCL_CRP_PROCESS_REQ'.
DATA: l_cls_data TYPE v_seoclass.
l_cls_data-clsname  = lv_clsname.
l_cls_data-category = '00'.
l_cls_data-exposure = '2'. " Public
l_cls_data-state    = '1'.
l_cls_data-langu    = 'E'.
l_cls_data-descript = 'CRP Auto-Registered (AI Bridge)'.

WRITE: / 'Audit:', lv_clsname.

CALL FUNCTION 'SEO_CLASS_CREATE_P'
  EXPORTING
    i_class    = l_cls_data
    i_devclass = 'ZCRP'
    i_corrnr   = 'D01K9B0EWT'
  EXCEPTIONS
    existing   = 1
    OTHERS     = 2.

IF sy-subrc = 0 OR sy-subrc = 1.
  WRITE: / 'OK: Class Builder entry confirmed.'.
ELSE.
  WRITE: / 'ERROR: Class Creation failed subrc:', sy-subrc.
ENDIF.

* Register one method as test
CALL FUNCTION 'SEO_METHOD_CREATE_P'
  EXPORTING
    mtdkey      = VALUE seocpdkey( clsname = lv_clsname cmpname = 'RESOLVE_STAFF_FROM_USER' )
    mtd         = VALUE v_seomethod( clsname = lv_clsname cmpname = 'RESOLVE_STAFF_FROM_USER' exposure = '2' )
    descript    = 'Resolve Staff ID'
  EXCEPTIONS
    existing    = 1
    OTHERS      = 2.
WRITE: / 'Method resolution call subrc:', sy-subrc.

* Activate
CALL FUNCTION 'SEO_CLASS_ACTIVATE'
  EXPORTING
    clskey = VALUE seoclskey( clsname = lv_clsname )
  EXCEPTIONS
    OTHERS = 1.
WRITE: / 'Activation final subrc:', sy-subrc.
"""
    execute_abap_script(abap_reconstruct)
