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
classes = ["ZCL_CRP_PROCESS_REQ", "ZCL_Z_CRP_SRV_DPC_EXT"]

for cls in classes:
    print(f"\nListing ALL includes for {cls}:")
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR",
                      OPTIONS=[{"TEXT": f"NAME LIKE '{cls}%'"}],
                      FIELDS=[{"FIELDNAME":"NAME"}])
        for row in r.get("DATA", []):
            name = row['WA'].strip()
            print(f"  - {name}")
    except Exception as e:
        print(f"  Error: {e}")

conn.close()
