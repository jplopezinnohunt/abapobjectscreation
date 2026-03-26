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
    # Check DD02L for tables
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD02L", 
                  OPTIONS=[{"TEXT": "TABNAME LIKE 'SEO%MET%'"}],
                  FIELDS=[{"FIELDNAME":"TABNAME"}])
    for row in r.get("DATA", []):
        print(f"Table: {row['WA'].strip()}")

    # Check SEOMETHOD directly
    print("\nChecking SEOMETHOD for ZCL_CRP_PROCESS_REQ...")
    r2 = conn.call("RFC_READ_TABLE", QUERY_TABLE="SEOMETHOD", 
                   OPTIONS=[{"TEXT": "CLSNAME = 'ZCL_CRP_PROCESS_REQ'"}],
                   FIELDS=[{"FIELDNAME":"CMPNAME"}])
    for row in r2.get("DATA", []):
        print(f"  Method: {row['WA'].strip()}")

except Exception as e:
    print(f"Error: {e}")

conn.close()
