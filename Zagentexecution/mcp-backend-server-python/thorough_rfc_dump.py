import os, sys
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    # Using the working IP connection
    p = {
        "ashost": "172.16.4.66", "sysnr": "00", "client": "350", "user": os.getenv("SAP_USER"), "lang": "EN"
    }
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"; p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME"); p["snc_qop"] = "9"
    return Connection(**p)

conn = get_conn()
try:
    f = "SEO_GET_CLIF_REMOTE"
    print(f"\nINTERFACE DUMP FOR {f}:")
    res = conn.call("RFC_GET_FUNCTION_INTERFACE", FUNCNAME=f)
    
    # Check all parameters
    params = res.get("PARAMS", [])
    for p in params:
        p_class = p.get('PARAMCLASS', '?')
        p_name = p.get('PARAMETER', '?')
        p_type = p.get('TABNAME', '?')
        print(f"  [{p_class}] {p_name} type {p_type}")

except Exception as e:
    print(f"Error: {e}")
conn.close()
