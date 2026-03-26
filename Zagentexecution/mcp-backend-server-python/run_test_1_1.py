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
cls = "ZCL_Z_CRP_SRV_DPC_EXT"

print(f"--- TEST 1.1: Writing to EXISTING class {cls} ---")
try:
    code = [
        "* TEST CCIMP FOR EXISTING CLASS",
        "** DO NOT DELETE **"
    ]
    include = f"{cls}=========CCIMP"
    
    # Try with I_EXTENSION='' first
    print(f"Attempting write to {include} (no extension)...")
    res = conn.call("SIW_RFC_WRITE_REPORT", I_NAME=include, I_TAB_CODE=code)
    exc = res.get("E_STR_EXCEPTION", {})
    if exc and exc.get("MSG_TYPE") == "E":
        print(f"  Result: FAILED - {exc.get('MSG_TEXT')}")
    else:
        print(f"  Result: SUCCESS!")

    conn.close()
except Exception as e:
    print(f"Error during Test 1.1: {e}")
