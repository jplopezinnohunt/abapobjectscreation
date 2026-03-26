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
cls = "ZCL_CRP_PROCESS_REQ"

print(f"--- PRE-FLIGHT CHECK FOR {cls} ---")
try:
    # Check TRDIR for ANY include
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR", DELIMITER="|",
                  OPTIONS=[{"TEXT": f"NAME LIKE '{cls}%'"}],
                  FIELDS=[{"FIELDNAME":"NAME"}], ROWCOUNT=5)
    data = r.get("DATA", [])
    if data:
        print("Existing includes in TRDIR:")
        for row in data:
            print(f"  {row['WA'].strip()}")
    else:
        print("No includes found in TRDIR. The class might not be created yet.")

    # Try to write Step 1 (CCDEF) with NO extension first
    print(f"\n--- TEST 1: Writing CCDEF to {cls} ---")
    code = [
        "* TEST CCDEF",
        "TYPES: ty_test TYPE string."
    ]
    include = f"{cls}=========CCDEF"
    
    # Try no extension
    print(f"Attempting write to {include} (no extension)...")
    res = conn.call("SIW_RFC_WRITE_REPORT", I_NAME=include, I_TAB_CODE=code)
    exc = res.get("E_STR_EXCEPTION", {})
    if exc and exc.get("MSG_TYPE") == "E":
        print(f"  Result: FAILED - {exc.get('MSG_TEXT')}")
    else:
        print(f"  Result: SUCCESS!")

    conn.close()
except Exception as e:
    print(f"Error during Test 1: {e}")
