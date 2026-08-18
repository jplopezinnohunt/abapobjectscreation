"""
Read the SIW_TAB_CODE structure field name and correct write approach.
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
    # 1. Get SIW_TAB_CODE fields
    execute_abap("""
REPORT Z_INSPECT_SIWTAB.
DATA: lt_dfies TYPE TABLE OF dfies.
DATA: ls_dfies TYPE dfies.
CALL FUNCTION 'DDIF_FIELDINFO_GET'
  EXPORTING tabname = 'SIW_TAB_CODE'
  TABLES dfies_tab = lt_dfies
  EXCEPTIONS OTHERS = 1.
WRITE: / 'SIW_TAB_CODE fields:'.
LOOP AT lt_dfies INTO ls_dfies.
  WRITE: / ls_dfies-fieldname, ls_dfies-datatype, ls_dfies-leng.
ENDLOOP.
""", "SIW_TAB_CODE FIELDS")

    # 2. Test write with correct field name (try ZEILE, then LINE, then TEXT)
    execute_abap("""
REPORT Z_TEST_WRITE.
DATA: lt_code TYPE TABLE OF siw_tab_code.
DATA: ls_code TYPE siw_tab_code.
ls_code-zeile = '* TEST WRITE OK'.
APPEND ls_code TO lt_code.
CALL FUNCTION 'SIW_RFC_WRITE_REPORT'
  EXPORTING
    i_name     = 'ZCL_CRP_PROCESS_REQ============CCIMP'
    i_tab_code = lt_code.
WRITE: / 'WRITE subrc:', sy-subrc.
""", "TEST WRITE WITH ZEILE FIELD")
