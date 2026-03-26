import os, sys
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    p = {"ashost": "172.16.4.66", "sysnr": "00", "client": "350", 
         "user": os.getenv("SAP_USER"), "lang": "EN"}
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"; p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = "9"
    return Connection(**p)

conn = get_conn()
try:
    f = "SEO_GET_CLIF_REMOTE"
    print(f"Interface for {f}:")
    res = conn.call("RFC_GET_FUNCTION_INTERFACE", FUNCNAME=f)
    for p in res.get("IMPORT_PARAMETERS", []):
        print(f"  Import: {p['PARAMETER']}")
    for p in res.get("EXPORT_PARAMETERS", []):
        print(f"  Export: {p['PARAMETER']}")
    for p in res.get("TABLES_PARAMETERS", []):
        print(f"  Table: {p['PARAMETER']}")
except Exception as e:
    print(f"Error: {e}")
conn.close()
