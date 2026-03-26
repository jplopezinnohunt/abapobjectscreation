"""
read_ccimp.py - Reads the CCIMP include of DPC_EXT to see current content
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv()
def get_conn():
    p = {"ashost":os.getenv("SAP_ASHOST"),"sysnr":os.getenv("SAP_SYSNR"),
         "client":os.getenv("SAP_CLIENT"),"user":os.getenv("SAP_USER"),"lang":"EN"}
    if os.getenv("SAP_PASSWD"): p["passwd"]=os.getenv("SAP_PASSWD")
    if os.getenv("SAP_SNC_MODE")=="1":
        p["snc_mode"]="1"; p["snc_partnername"]=os.getenv("SAP_SNC_PARTNERNAME"); p["snc_qop"]=os.getenv("SAP_SNC_QOP","9")
    return Connection(**p)

conn = get_conn()
for inc in ["ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP", "ZCL_Z_CRP_SRV_DPC_EXT=========CCDEF"]:
    print(f"\n=== {inc} ===")
    try:
        res = conn.call("SIW_RFC_READ_REPORT", I_NAME=inc)
        lines = res.get("E_TAB_CODE", [])
        if isinstance(lines, list):
            for l in lines:
                if isinstance(l, dict):
                    print(l.get("LINE",""))
                else:
                    print(str(l))
        print(f"  ({len(lines)} lines)")
    except Exception as e:
        print(f"  Error: {e}")
conn.close()
