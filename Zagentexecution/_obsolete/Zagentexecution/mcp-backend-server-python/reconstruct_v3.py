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
    if "REPORT " not in abap_code.upper():
        abap_code = "REPORT Z_AI_TOOL.\n" + abap_code
    
    abap_source = [{"LINE": line[:72]} for line in abap_code.split('\n')]
    
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap_source)
        writes = res.get("WRITES", [])
        for w in writes:
            val = w.get('ZEILE') or w.get('LINE') or w.get('TEXT') or list(w.values())[0]
            print(f"  SAP Log: {val}")
        if res.get("ERRORMESSAGE"):
            print(f"  SAP ERROR: {res.get('ERRORMESSAGE')}")
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    # Test with SEOCLASS directly
    abap_reconstruct = """
REPORT Z_RECONSTRUCT.
DATA: lv_clsname TYPE seoclsname VALUE 'ZCL_CRP_PROCESS_REQ'.
DATA: ls_seoclass TYPE seoclass. " Use table name as type

ls_seoclass-clsname  = lv_clsname.
ls_seoclass-category = '00'.
ls_seoclass-exposure = '2'. 
ls_seoclass-state    = '1'.
ls_seoclass-langu    = 'E'.

WRITE: / 'Attempting registration with SEOCLASS type...'.

CALL FUNCTION 'SEO_CLASS_CREATE_OBJECT'
  EXPORTING
    clskey     = VALUE seoclskey( clsname = lv_clsname )
    devclass   = 'ZCRP'
    corrnr     = 'D01K9B0EWT'
    descript   = 'CRP Auto-Registered (AI Bridge)'
  EXCEPTIONS
    existing   = 1
    OTHERS     = 2.

WRITE: / 'SEO_CLASS_CREATE_OBJECT subrc:', sy-subrc.

CALL FUNCTION 'SEO_CLASS_ACTIVATE'
  EXPORTING
    clskey = VALUE seoclskey( clsname = lv_clsname )
  EXCEPTIONS
    OTHERS = 1.
WRITE: / 'Activation final subrc:', sy-subrc.
"""
    execute_abap_script(abap_reconstruct)
