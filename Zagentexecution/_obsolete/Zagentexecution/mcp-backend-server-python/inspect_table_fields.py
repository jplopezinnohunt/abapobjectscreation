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
    print("Executing ABAP Bridge Inspection script...")
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
    # Describe SEOCLASS table
    abap_inspect = """
REPORT Z_INSPECT_TABLE.
DATA: lt_dfies TYPE TABLE OF dfies.
DATA: ls_dfies TYPE dfies.

CALL FUNCTION 'DDIF_FIELDINFO_GET'
  EXPORTING
    tabname    = 'SEOCLASS'
  TABLES
    dfies_tab  = lt_dfies
  EXCEPTIONS
    not_found  = 1
    internal_error = 2
    OTHERS     = 3.

IF sy-subrc = 0.
  WRITE: / 'SEOCLASS has', lines( lt_dfies ), 'fields.'.
  LOOP AT lt_dfies INTO ls_dfies.
    WRITE: / ls_dfies-fieldname, ls_dfies-rollname, ls_dfies-leng.
  ENDLOOP.
ELSE.
  WRITE: / 'Error calling DDIF_FIELDINFO_GET:', sy-subrc.
ENDIF.
"""
    execute_abap_script(abap_inspect)
