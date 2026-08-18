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
    print("Executing ABAP Bridge script...")
    abap_source = [{"LINE": line[:72]} for line in abap_code.split('\n')]
    
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap_source)
        print("  [OK] Script finished.")
        # The structure is LISTZEILE, field is ZEILE
        writes = res.get("WRITES", [])
        for w in writes:
            print(f"  SAP Log: {w.get('ZEILE','')}")
        return writes
    except Exception as e:
        print(f"  FAILED: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    # This ABAP script will try to fix the registration locally
    # It first tries to create the entry if missing
    abap_reg = """
REPORT Z_AI_REGISTER_CLASS.
DATA: l_class_name TYPE seoclsname VALUE 'ZCL_CRP_PROCESS_REQ'.
DATA: l_class_key  TYPE seoclskey.
l_class_key-clsname = l_class_name.

* Use a structure for class definition
DATA: l_cls_data TYPE v_seoclass.
l_cls_data-clsname  = l_class_name.
l_cls_data-category = '00'.
l_cls_data-exposure = 'Public'. " or 2
l_cls_data-state    = '1'.
l_cls_data-langu    = 'E'.
l_cls_data-descript = 'CRP Process Request Delegate (AI Bootstrap)'.

WRITE: / 'Audit:', l_class_name.

CALL FUNCTION 'SEO_CLASS_CREATE_P'
  EXPORTING
    i_class    = l_cls_data
    i_devclass = 'ZCRP'
    i_corrnr   = 'D01K9B0EWT'
  EXCEPTIONS
    existing   = 1
    OTHERS     = 2.

IF sy-subrc = 0.
  WRITE: / 'Class registration created successfully.'.
ELSEIF sy-subrc = 1.
  WRITE: / 'Class already exists in Class Builder.'.
ELSE.
  WRITE: / 'Failed to ensure class creation. Subrc:', sy-subrc.
ENDIF.

* Try activation
CALL FUNCTION 'SEO_CLASS_ACTIVATE'
  EXPORTING
    clskey = l_class_key
  EXCEPTIONS
    not_found = 1
    OTHERS = 2.
WRITE: / 'Activation return code:', sy-subrc.
"""
    execute_abap_script(abap_reg)
