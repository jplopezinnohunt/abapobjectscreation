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
classes = ["ZCL_CRP_PROCESS_REQ", "ZCL_Z_CRP_SRV_DPC_EXT"]

for cls in classes:
    incl = cls.ljust(30, '=') + "CCIMP"
    print(f"Cleaning {incl}...")
    try:
        conn.call("SIW_RFC_WRITE_REPORT", I_NAME=incl, I_TAB_CODE=["* Cleaned by AI"], I_EXTENSION='')
        print(f"  [OK] {incl} emptied.")
    except Exception as e:
        print(f"  [FAIL] {incl}: {e}")

conn.close()
