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
try:
    print("Searching for ANY function related to 'SEO' or 'CREATE'...")
    # Search for SEO
    r1 = conn.call("RFC_FUNCTION_SEARCH", FUNCNAME="SEO*", GROUPNAME="*")
    funcs = r1.get("FUNCTIONS", [])
    print(f"Found {len(funcs)} SEO functions.")
    for f in funcs[:10]:
        print(f"  {f['FUNCNAME']}")
    if len(funcs) > 10: print("  ...")

    # Search for TR_COPY
    r2 = conn.call("RFC_FUNCTION_SEARCH", FUNCNAME="TR_COPY*", GROUPNAME="*")
    for f in r2.get("FUNCTIONS", []):
        print(f"  {f['FUNCNAME']}")

    conn.close()
except Exception as e:
    print(f"Search failed: {e}")
