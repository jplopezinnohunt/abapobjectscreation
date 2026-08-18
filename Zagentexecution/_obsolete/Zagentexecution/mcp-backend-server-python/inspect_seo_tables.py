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

    # 1. Inspect SEOCLASSDF fields (the actual descriptor table)
    execute_abap("""
REPORT Z_INSPECT_SEOFIELDS.
DATA: lt_dfies TYPE TABLE OF dfies.
DATA: ls_dfies TYPE dfies.

CALL FUNCTION 'DDIF_FIELDINFO_GET'
  EXPORTING
    tabname    = 'SEOCLASSDF'
  TABLES
    dfies_tab  = lt_dfies
  EXCEPTIONS
    OTHERS     = 1.
WRITE: / 'SEOCLASSDF fields:'.
LOOP AT lt_dfies INTO ls_dfies.
  WRITE: / ls_dfies-fieldname, ls_dfies-rollname, ls_dfies-leng.
ENDLOOP.
""", "SEOCLASSDF FIELDS")

    # 2. Check if SEOCLASS entry exists for ZCL_CRP_PROCESS_REQ
    execute_abap("""
REPORT Z_CHECK_CLS.
DATA: ls_seoclass TYPE seoclass.
SELECT SINGLE * FROM seoclass INTO ls_seoclass 
  WHERE clsname = 'ZCL_CRP_PROCESS_REQ'.
IF sy-subrc = 0.
  WRITE: / 'SEOCLASS FOUND. UUID:', ls_seoclass-uuid.
ELSE.
  WRITE: / 'SEOCLASS NOT FOUND (subrc=', sy-subrc, ')'.
ENDIF.

DATA: ls_seoclassdf TYPE seoclassdf.
SELECT SINGLE * FROM seoclassdf INTO ls_seoclassdf 
  WHERE clsname = 'ZCL_CRP_PROCESS_REQ'.
IF sy-subrc = 0.
  WRITE: / 'SEOCLASSDF FOUND. State:', ls_seoclassdf-state, 
              ' Descript:', ls_seoclassdf-descript.
ELSE.
  WRITE: / 'SEOCLASSDF NOT FOUND'.
ENDIF.
""", "CLASS METADATA EXISTENCE CHECK")
