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
code = ["* TEST"]

# Let's check how the DPC class is identified in TRDIR vs this one
print("Comparing DPC vs PROCESS_REQ in TRDIR...")
try:
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR", DELIMITER="|",
                  OPTIONS=[{"TEXT": f"NAME LIKE 'ZCL_Z_CRP_SRV_DPC_EXT%'"}],
                  FIELDS=[{"FIELDNAME":"NAME"}], ROWCOUNT=5)
    for row in r.get("DATA", []): print(f"  DPC: {row['WA'].strip()}")

    r2 = conn.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR", DELIMITER="|",
                  OPTIONS=[{"TEXT": f"NAME LIKE '{cls}%'"}],
                  FIELDS=[{"FIELDNAME":"NAME"}], ROWCOUNT=10)
    for row in r2.get("DATA", []): print(f"  REQ: {row['WA'].strip()}")

    print("\nAttempting different I_EXTENSION values for REQ class includes...")
    # Based on ABAP kernel, common internal exttypes are C, I, K, etc.
    # SIW_RFC_WRITE_REPORT usually expects something that maps to these.
    for ext in ["", "X", "CLAS", "C", "I"]:
        print(f"Trying name '{cls}=========CCIMP' with extension '{ext}'...")
        try:
            res = conn.call("SIW_RFC_WRITE_REPORT", I_NAME=f"{cls}=========CCIMP", I_TAB_CODE=code, I_EXTENSION=ext)
            exc = res.get("E_STR_EXCEPTION", {})
            if exc and exc.get("MSG_TYPE") == "E":
                print(f"  FAILED: {exc.get('MSG_TEXT')}")
            else:
                print("  SUCCESS!")
                break
        except Exception as e:
            print(f"  ERROR: {e}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
