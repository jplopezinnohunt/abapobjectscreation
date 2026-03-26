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

try:
    print(f"Checking TADIR for {cls}...")
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR", DELIMITER="|",
                  OPTIONS=[{"TEXT": f"PGMID = 'R3TR' AND OBJECT = 'CLAS' AND OBJ_NAME = '{cls}'"}],
                  FIELDS=[{"FIELDNAME":"OBJ_NAME"},{"FIELDNAME":"DEVCLASS"}])
    rows = r.get("DATA", [])
    if rows:
        for row in rows:
            print(f"  {row['WA']}")
    else:
        print("  Not found in TADIR.")
    conn.close()
except Exception as e:
    print(f"Check failed: {e}")
