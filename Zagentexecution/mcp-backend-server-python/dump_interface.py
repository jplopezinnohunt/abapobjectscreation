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

def dump_interface(funcname):
    conn = get_conn()
    print(f"\nDumping interface for {funcname}:")
    try:
        res = conn.call("RFC_GET_FUNCTION_INTERFACE", FUNCNAME=funcname)
        params = res.get("IMPORT_PARAMETERS", [])
        for p in params:
            print(f"  Import: {p['PARAMETER']} ({p['PARAMCLASS']})")
        
        exports = res.get("EXPORT_PARAMETERS", [])
        for p in exports:
            print(f"  Export: {p['PARAMETER']} ({p['PARAMCLASS']})")
            
        tables = res.get("TABLES_PARAMETERS", [])
        for p in tables:
            print(f"  Table: {p['PARAMETER']} ({p['PARAMCLASS']})")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()

if __name__ == "__main__":
    dump_interface("SEO_GET_CLIF_REMOTE")
