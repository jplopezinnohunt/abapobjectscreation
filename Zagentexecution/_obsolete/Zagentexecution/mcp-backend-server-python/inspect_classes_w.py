"""
Use SEO_CLASS_CREATE with SEOC_CLASSES_W table parameter (the correct simple API).
Must inspect SEOC_CLASSES_W fields first, then call via ABAP bridge.
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pyrfc import Connection, RFCError
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
    # Step 1: Get SEOC_CLASSES_W fields
    execute_abap("""
REPORT Z_INSPECT_CLASSES_W.
DATA: lt_dfies TYPE TABLE OF dfies.
DATA: ls_dfies TYPE dfies.
CALL FUNCTION 'DDIF_FIELDINFO_GET'
  EXPORTING tabname = 'SEOC_CLASSES_W'
  TABLES dfies_tab = lt_dfies
  EXCEPTIONS OTHERS = 1.
LOOP AT lt_dfies INTO ls_dfies.
  WRITE: / ls_dfies-fieldname, ls_dfies-leng.
ENDLOOP.
""", "SEOC_CLASSES_W FIELDS")
