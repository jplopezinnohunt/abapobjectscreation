import os, sys
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    p = {"ashost":os.getenv("SAP_ASHOST"), "sysnr":os.getenv("SAP_SYSNR"),
         "client":os.getenv("SAP_CLIENT"), "user":os.getenv("SAP_USER"), "lang":"EN"}
    if os.getenv("SAP_PASSWD"): p["passwd"] = os.getenv("SAP_PASSWD")
    return Connection(**p)

conn = get_conn()
classes = ["ZCL_CRP_PROCESS_REQ", "ZCL_Z_CRP_SRV_DPC_EXT"]

print("--- REPOSITORY CHECK ---")
for cls in classes:
    # Check SEOCLASS
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE="SEOCLASS", 
                      OPTIONS=[{"TEXT": f"CLSNAME = '{cls}'"}],
                      FIELDS=[{"FIELDNAME":"CLSNAME"}, {"FIELDNAME":"VERSION"}, {"FIELDNAME":"STATE"}])
        data = r.get("DATA")
        if data:
            row = data[0]['WA'].split()
            print(f"Object {cls}: EXISTS (State {row[2]})")
        else:
            print(f"Object {cls}: NOT FOUND in SEOCLASS")
    except Exception as e:
        print(f"Error checking {cls}: {e}")

    # Check Components (Methods)
    try:
        r2 = conn.call("RFC_READ_TABLE", QUERY_TABLE="SEOCOMPODF", 
                       OPTIONS=[{"TEXT": f"CLSNAME = '{cls}' AND CMPTYPE = '1'"}], # CMPTYPE 1 = Method
                       FIELDS=[{"FIELDNAME":"CMPNAME"}, {"FIELDNAME":"ALIAS"}], ROWCOUNT=20)
        data = r2.get("DATA", [])
        print(f"  Found {len(data)} methods.")
        for d in data[:5]:
            print(f"    Method: {d['WA'].strip()}")
        if len(data) > 5: print("    ...")
    except Exception as e:
         print(f"  Error checking methods for {cls}: {e}")

conn.close()
