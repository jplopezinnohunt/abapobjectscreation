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
    print("Executing ABAP Bridge script via RFC_ABAP_INSTALL_AND_RUN...")
    # Formats the ABAP code into a list of dictionaries with field 'LINE'
    # Each line should be limited to 72 chars usually for this RFC
    abap_source = []
    for line in abap_code.split('\n'):
        while len(line) > 72:
            abap_source.append({"LINE": line[:72]})
            line = line[72:]
        abap_source.append({"LINE": line})
    
    try:
        # RFC_ABAP_INSTALL_AND_RUN parameters: 
        # PGMNAME - dummy name
        # PROGRAM - table of lines
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap_source)
        print("  [OK] Script executed.")
        # The output of the WRITE statements is in the 'WRITES' table
        writes = res.get("WRITES", [])
        for w in writes:
            print(f"  SAP Log: {w.get('LINE','')}")
        return writes
    except Exception as e:
        print(f"  FAILED: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    # This ABAP script will try to register the class metadata locally
    abap_reg = """
REPORT Z_AI_REGISTER_CLASS.
DATA: l_class_name TYPE seoclsname VALUE 'ZCL_CRP_PROCESS_REQ'.
DATA: l_class_key  TYPE seoclskey.
l_class_key-clsname = l_class_name.

WRITE: / 'Attempting to register class metadata:', l_class_name.

* 1. Check if metadata exists
DATA: l_seoclass TYPE seoclass.
SELECT SINGLE * FROM seoclass INTO l_seoclass WHERE clsname = l_class_name.
IF sy-subrc <> 0.
  WRITE: / 'Metadata missing in SEOCLASS. Forcing registration...'.
  
  * Use local class builder API
  CALL FUNCTION 'SEO_CLASS_CREATE_P'
    EXPORTING
      i_class    = VALUE v_seoclass( clsname = l_class_name 
                                     category = '00' 
                                     exposure = '2' 
                                     state = '1'
                                     langu = 'E'
                                     descript = 'CRP Process Request Delegate (AI Registered)' )
      i_devclass = 'ZCRP'
      i_corrnr   = 'D01K9B0EWT'
    EXCEPTIONS
      existing   = 1
      OTHERS     = 2.
  IF sy-subrc = 0.
    WRITE: / 'SUCCESS: Class registered in SEOCLASS.'.
  ELSE.
    WRITE: / 'Error in SEO_CLASS_CREATE_P:', sy-subrc.
  ENDIF.
ELSE.
  WRITE: / 'Metadata already exists in SEOCLASS. State:', l_seoclass-state.
ENDIF.

* 2. Activate to force sync
CALL FUNCTION 'SEO_CLASS_ACTIVATE'
  EXPORTING
    clskey = l_class_key
  EXCEPTIONS
    not_found = 1
    OTHERS = 2.
IF sy-subrc = 0.
  WRITE: / 'SUCCESS: Class Activated.'.
ELSE.
  WRITE: / 'Activation failed with subrc:', sy-subrc.
ENDIF.
"""
    execute_abap_script(abap_reg)
