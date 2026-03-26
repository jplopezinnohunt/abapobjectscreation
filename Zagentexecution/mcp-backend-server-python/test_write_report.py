import os, sys
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    p = {"ashost":os.getenv("SAP_ASHOST"), "sysnr":os.getenv("SAP_SYSNR"),
         "client":os.getenv("SAP_CLIENT"), "user":os.getenv("SAP_USER"), "lang":"EN"}
    if os.getenv("SAP_PASSWD"): p["passwd"] = os.getenv("SAP_PASSWD")
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"]="1"; p["snc_partnername"]=os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"]=os.getenv("SAP_SNC_QOP","9")
    return Connection(**p)

conn = get_conn()
test_report = "ZCRP_TEST_REPORT"
code = ["REPORT ZCRP_TEST_REPORT.", "WRITE 'SUCCESS'."]

try:
    print(f"Writing to {test_report}...")
    res = conn.call("SIW_RFC_WRITE_REPORT", I_NAME=test_report, I_TAB_CODE=code)
    exc = res.get("E_STR_EXCEPTION", {})
    if exc and exc.get("MSG_TYPE") == "E":
        print(f"  FAILED: {exc.get('MSG_TEXT')}")
    else:
        print("  SUCCESS!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
