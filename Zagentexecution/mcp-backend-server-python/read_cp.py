"""
read_cp.py — Reads the CP (class pool) include for DPC_EXT and ZCL_CRP_PROCESS_REQ
"""
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
        p["snc_mode"]="1"; p["snc_partnername"]=os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"]=os.getenv("SAP_SNC_QOP","9")
    return Connection(**p)

conn = get_conn()

for include in ["ZCL_Z_CRP_SRV_DPC_EXT=========CP",
                "ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP"]:
    print(f"\n{'='*60}\n{include}\n{'='*60}")
    try:
        r = conn.call("SIW_RFC_READ_REPORT", I_NAME=include)
        lines = r.get("E_TAB_CODE", [])
        print(f"Lines: {len(lines)}")
        for i, line in enumerate(lines[:80], 1):
            print(f"  {i:3}: {line}")
        if len(lines) > 80:
            print(f"  ... ({len(lines)-80} more lines)")
    except Exception as e:
        print(f"Error: {e}")

conn.close()
