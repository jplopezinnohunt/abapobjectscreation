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

def execute_abap(abap_code, label=""):
    conn = get_conn()
    if label: print(f"\n[{label}]")
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
    # First inspect SEOCLASSTX fields
    execute_abap("""
REPORT Z_INSPECT.
DATA: lt_dfies TYPE TABLE OF dfies.
DATA: ls_dfies TYPE dfies.
CALL FUNCTION 'DDIF_FIELDINFO_GET'
  EXPORTING tabname = 'SEOCLASSTX'
  TABLES dfies_tab = lt_dfies
  EXCEPTIONS OTHERS = 1.
WRITE: / 'SEOCLASSTX fields:'.
LOOP AT lt_dfies INTO ls_dfies.
  WRITE: / ls_dfies-fieldname, ls_dfies-leng.
ENDLOOP.
""", "SEOCLASSTX FIELDS")

    # Then VSEOCLASS fields
    execute_abap("""
REPORT Z_INSPECT2.
DATA: lt_dfies TYPE TABLE OF dfies.
DATA: ls_dfies TYPE dfies.
CALL FUNCTION 'DDIF_FIELDINFO_GET'
  EXPORTING tabname = 'VSEOCLASS'
  TABLES dfies_tab = lt_dfies
  EXCEPTIONS OTHERS = 1.
WRITE: / 'VSEOCLASS fields (first 15):'.
DATA: lv_i TYPE i VALUE 0.
LOOP AT lt_dfies INTO ls_dfies.
  ADD 1 TO lv_i.
  IF lv_i <= 15.
    WRITE: / ls_dfies-fieldname, ls_dfies-leng.
  ENDIF.
ENDLOOP.
""", "VSEOCLASS FIELDS")
