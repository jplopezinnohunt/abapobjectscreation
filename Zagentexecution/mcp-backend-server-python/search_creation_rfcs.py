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

def search_functions(pattern):
    conn = get_conn()
    print(f"\nSearching for functions matching: {pattern}")
    try:
        res = conn.call("RFC_FUNCTION_SEARCH", FUNCNAME=pattern)
        functions = res.get("FUNCTIONS", [])
        for f in functions:
            print(f"  {f['FUNCNAME']} - {f['STEXT']}")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()

if __name__ == "__main__":
    search_functions("*CLASS*CREATE*")
    search_functions("*SIW*CREATE*")
    search_functions("*OBJECT*CREATE*")
