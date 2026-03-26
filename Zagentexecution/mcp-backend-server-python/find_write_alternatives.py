"""
Use alternative approach: write ABAP code directly via RFC_ABAP_INSTALL_AND_RUN
but then call RS_PROGRAM_INSERT_REPORT instead of SIW_RFC_WRITE_REPORT.
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
    # First check which write functions are available
    execute_abap("""
REPORT Z_FIND_WRITERS.
DATA: lt_func TYPE TABLE OF tfdir.
DATA: ls_func TYPE tfdir.
SELECT funcname FROM tfdir INTO TABLE lt_func
  WHERE funcname LIKE 'RS_%REPORT%'
     OR funcname LIKE '%INSERT%REPORT%'
     OR funcname LIKE 'RPY_PROG%'
  ORDER BY funcname.
LOOP AT lt_func INTO ls_func.
  WRITE: / ls_func-funcname.
ENDLOOP.
WRITE: / 'Found:', lines( lt_func ).
""", "ALTERNATIVE WRITE FUNCTIONS")

    # Try RS_CORR_INSERT (insert source into repository)
    execute_abap("""
REPORT Z_CHECK_RPYPRG.
DATA: lt_func TYPE TABLE OF tfdir.
SELECT funcname FROM tfdir INTO TABLE lt_func
  WHERE funcname LIKE 'RPY%'
  ORDER BY funcname.
LOOP AT lt_func INTO DATA(ls).
  WRITE: / ls-funcname.
ENDLOOP.
""", "RPY FUNCTIONS")
