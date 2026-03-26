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

try:
    print(f"Checking TRDIR for {cls} main program...")
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR", DELIMITER="|",
                  OPTIONS=[{"TEXT": f"NAME = '{cls}==============================CP'"}],
                  FIELDS=[{"FIELDNAME":"NAME"}])
    rows = r.get("DATA", [])
    if rows:
        print(f"  Found: {rows[0]['WA']}")
    else:
        print("  Main program (CP) not found in TRDIR.")
    conn.close()
except Exception as e:
    print(f"Check failed: {e}")
