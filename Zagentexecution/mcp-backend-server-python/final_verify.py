import os, sys
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    # Use same params as debug_conn.py which works
    p = {
        "ashost": "172.16.4.66",
        "sysnr": "00",
        "client": "350",
        "user": os.getenv("SAP_USER"),
        "passwd": os.getenv("SAP_PASSWD"),
        "lang": "EN"
    }
    return Connection(**p)

try:
    conn = get_conn()
    print("Connected successfully.")
    
    classes = ["ZCL_CRP_PROCESS_REQ", "ZCL_Z_CRP_SRV_DPC_EXT"]
    
    for cls in classes:
        print(f"\n--- Checking {cls} ---")
        try:
            # Check TADIR
            r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR",
                          OPTIONS=[{"TEXT": f"OBJ_NAME = '{cls}' AND OBJECT = 'CLAS'"}],
                          FIELDS=[{"FIELDNAME":"DEVCLASS"}])
            data = r.get("DATA")
            if data:
                print(f"  Package: {data[0]['WA'].strip()}")
            else:
                print(f"  NOT FOUND in TADIR")
                
            # Check SEOCOMPODF for Methods
            r2 = conn.call("RFC_READ_TABLE", QUERY_TABLE="SEOCOMPODF",
                           OPTIONS=[{"TEXT": f"CLSNAME = '{cls}' AND CMPTYPE = '1'"}],
                           FIELDS=[{"FIELDNAME":"CMPNAME"}], ROWCOUNT=10)
            methods = r2.get("DATA", [])
            print(f"  Methods ({len(methods)}):")
            for m in methods:
                print(f"    - {m['WA'].strip()}")

        except Exception as e:
            print(f"  Error checking {cls}: {e}")
            
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
