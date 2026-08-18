"""
write_ccimp_correct.py
SIW_TAB_CODE is a flat TYPE C table (raw string, no structure).
Use: lt_code TYPE STANDARD TABLE OF siw_tab_code, and set lt_code[] directly.
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pyrfc import Connection
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

def execute_abap(code, label=""):
    conn = get_conn()
    if label: print(f"\n[{label}]")
    src = [{"LINE": l[:72]} for l in code.split('\n')]
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
        for w in res.get("WRITES", []):
            print(f"  SAP: {w.get('ZEILE') or list(w.values())[0]}")
        if res.get("ERRORMESSAGE"):
            print(f"  ERROR: {res.get('ERRORMESSAGE')}")
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Test writing 1 hardcoded line using WRITE to the table directly
    execute_abap("""
REPORT Z_TEST_SIWTAB.
DATA: lt_code TYPE STANDARD TABLE OF siw_tab_code.
DATA: lv_line TYPE siw_tab_code.
lv_line = 'CLASS ZCL_CRP_PROCESS_REQ IMPLEMENTATION.'.
APPEND lv_line TO lt_code.
lv_line = '  METHOD resolve_staff_from_user.'.
APPEND lv_line TO lt_code.
lv_line = '    rv_staff_id = ''00000001''.'.
APPEND lv_line TO lt_code.
lv_line = '  ENDMETHOD.'.
APPEND lv_line TO lt_code.
lv_line = 'ENDCLASS.'.
APPEND lv_line TO lt_code.

CALL FUNCTION 'SIW_RFC_WRITE_REPORT'
  EXPORTING
    i_name     = 'ZCL_CRP_PROCESS_REQ============CCIMP'
    i_tab_code = lt_code.
WRITE: / 'Write subrc:', sy-subrc.
""", "TEST SIW_TAB_CODE with lv_line type")
