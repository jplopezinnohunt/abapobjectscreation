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
test_code = ["* TEST"]

for ext in ["CP", "CI", "CD", "CU", "CO", "CT", "CS"]:
    print(f"Trying I_EXTENSION='{ext}'...")
    try:
        r = conn.call("SIW_RFC_WRITE_REPORT", I_NAME="ZCL_CRP_PROCESS_REQ=========CCIMP", I_TAB_CODE=test_code, I_EXTENSION=ext)
        exc = r.get("E_STR_EXCEPTION", {})
        if isinstance(exc, dict) and exc.get("MSG_TYPE") == "E":
            print(f"  Result: FAIL - {exc.get('MSG_TEXT')}")
        else:
            print(f"  Result: SUCCESS!")
            break
    except Exception as e:
        print(f"  Error: {e}")

conn.close()
