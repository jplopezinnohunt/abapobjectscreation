"""inspect_write_rfc.py — Get SIW_RFC_WRITE_REPORT parameter interface"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv()
def get_conn():
    p = {"ashost":os.getenv("SAP_ASHOST"), "sysnr":os.getenv("SAP_SYSNR"),
         "client":os.getenv("SAP_CLIENT"), "user":os.getenv("SAP_USER"), "lang":"EN"}
    if os.getenv("SAP_PASSWD"): p["passwd"] = os.getenv("SAP_PASSWD")
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"; p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = os.getenv("SAP_SNC_QOP","9")
    return Connection(**p)

conn = get_conn()
try:
    r = conn.call("RFC_GET_FUNCTION_INTERFACE", FUNCNAME="SIW_RFC_WRITE_REPORT")
    print("=== SIW_RFC_WRITE_REPORT Interface ===")
    for param in r.get("PARAMS", []):
        print(f"  {param.get('PARAMETER',''):<30} TYP={param.get('TYP','')}  "
              f"TAB={param.get('TABNAME','')}  OPT={param.get('OPTIONAL','')}")
except Exception as e:
    print(f"Error: {e}")

# Also test with a 1-liner to see what params it actually accepts at runtime
print("\n=== Testing with empty call to see parameter error message ===")
try:
    conn.call("SIW_RFC_WRITE_REPORT")
except Exception as e:
    print(f"Empty call response: {e}")

conn.close()
