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
    abap_source = [{"LINE": line[:72]} for line in abap_code.split('\n')]
    
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap_source)
        writes = res.get("WRITES", [])
        for w in writes:
            val = w.get('ZEILE') or list(w.values())[0]
            print(f"  SAP Log: {val}")
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    # Ultimate Reconstruction Script
    abap_reconstruct = """
REPORT Z_RECONSTRUCT_CLASSES.
TYPES: BEGIN OF ty_meth,
         clsname TYPE seoclsname,
         mtdname TYPE seoclsname,
         descript TYPE seodescr,
       END OF ty_meth.
DATA: lt_methods TYPE TABLE OF ty_meth.
DATA: ls_meth TYPE ty_meth.

DATA: lt_classes TYPE TABLE OF seoclsname.
APPEND 'ZCL_CRP_PROCESS_REQ' TO lt_classes.
APPEND 'ZCL_Z_CRP_SRV_DPC_EXT' TO lt_classes.

WRITE: / 'Starting Reconstruction for Classes...'.

DATA: lv_clsname TYPE seoclsname.
LOOP AT lt_classes INTO lv_clsname.
  WRITE: / '--- Processing Class:', lv_clsname, '---'.
  
  * 1. Check if metadata exists in SEOCLASS
  DATA: ls_seoclass TYPE seoclass.
  SELECT SINGLE * FROM seoclass INTO ls_seoclass WHERE clsname = lv_clsname.
  IF sy-subrc <> 0.
    WRITE: / '   [INFO] Metadata missing in SEOCLASS. Forcing registration...'.
    
    * Force-add entry to SEOCLASS via local function
    CALL FUNCTION 'SEO_CLASS_CREATE_OBJECT'
      EXPORTING
        clsname    = lv_clsname
        devclass   = 'ZCRP'
        corrnr     = 'D01K9B0EWT'
        version    = '1'
        descript   = 'CRP Auto-Registered (AI Bridge)'
      EXCEPTIONS
        existing   = 1
        OTHERS     = 2.
    IF sy-subrc = 0 OR sy-subrc = 1.
       WRITE: / '   [OK] Registration entry ensured.'.
    ELSE.
       WRITE: / '   [ERROR] Registration failed with subrc:', sy-subrc.
       CONTINUE.
    ENDIF.
  ELSE.
    WRITE: / '   [OK] Metadata already present. State:', ls_seoclass-state.
  ENDIF.

  * 2. Register Methods if missing
  * We'll add the core methods for CRP_PROCESS_REQ manually here
  IF lv_clsname = 'ZCL_CRP_PROCESS_REQ'.
     ls_meth-mtdname = 'RESOLVE_STAFF_FROM_USER'. ls_meth-descript = 'Resolve Staff ID'. APPEND ls_meth TO lt_methods.
     ls_meth-mtdname = 'DETERMINE_GL_ACCOUNT'. ls_meth-descript = 'Determine GL Account'. APPEND ls_meth TO lt_methods.
     ls_meth-mtdname = 'SAVE_DATA'. ls_meth-descript = 'Save CRP Data'. APPEND ls_meth TO lt_methods.
     
     LOOP AT lt_methods INTO ls_meth.
       CALL FUNCTION 'SEO_METHOD_CREATE_P'
         EXPORTING
           mtdkey      = VALUE seocpdkey( clsname = lv_clsname cmpname = ls_meth-mtdname )
           mtd         = VALUE v_seomethod( clsname = lv_clsname cmpname = ls_meth-mtdname exposure = '2' )
           descript    = ls_meth-descript
         EXCEPTIONS
           existing    = 1
           OTHERS      = 2.
       IF sy-subrc = 0.
          WRITE: / '   [OK] Method registered:', ls_meth-mtdname.
       ELSE.
          WRITE: / '   [INFO] Method skip/subrc:', ls_meth-mtdname, sy-subrc.
       ENDIF.
     ENDLOOP.
     REFRESH lt_methods.
  ENDIF.

  * 3. Final Activation
  CALL FUNCTION 'SEO_CLASS_ACTIVATE'
    EXPORTING
      clskey = VALUE seoclskey( clsname = lv_clsname )
    EXCEPTIONS
      OTHERS = 1.
  IF sy-subrc = 0.
    WRITE: / '   [OK] Class Activation Success.'.
  ELSE.
    WRITE: / '   [WARNING] Activation failed. Check syntax manually.'.
  ENDIF.
  
ENDLOOP.
"""
    execute_abap_script(abap_reconstruct)
