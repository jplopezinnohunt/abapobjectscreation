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
include = "ZCL_CRP_PROCESS_REQ=========CCIMP"

try:
    print(f"Reading {include}...")
    r = conn.call("SIW_RFC_READ_REPORT", I_NAME=include)
    lines = r.get("E_TAB_CODE", [])
    print(f"Read {len(lines)} lines.")
    for line in lines[:20]:
        print(line)
    if len(lines) > 20:
        print("...")
    conn.close()
except Exception as e:
    print(f"Read failed: {e}")
