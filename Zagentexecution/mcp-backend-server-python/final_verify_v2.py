import os, sys
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    p = {
        "ashost": "172.16.4.66",
        "sysnr": "00",
        "client": "350",
        "user": os.getenv("SAP_USER"),
        "lang": "EN"
    }
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"
        p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = os.getenv("SAP_SNC_QOP", "9")
    elif os.getenv("SAP_PASSWD"):
        p["passwd"] = os.getenv("SAP_PASSWD")
    return Connection(**p)

try:
    conn = get_conn()
    print("Connected to D01.")
    
    classes = ["ZCL_CRP_PROCESS_REQ", "ZCL_Z_CRP_SRV_DPC_EXT"]
    
    for cls in classes:
        print(f"\n[CLASS: {cls}]")
        # 1. Check TADIR entry
        try:
            r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR",
                          OPTIONS=[{"TEXT": f"OBJ_NAME = '{cls}' AND OBJECT = 'CLAS'"}],
                          FIELDS=[{"FIELDNAME":"DEVCLASS"}])
            if r.get("DATA"):
                print(f"  - Package: {r['DATA'][0]['WA'].strip()}")
            else:
                print(f"  - NOT FOUND in TADIR (Repository)")
        except Exception as e:
            print(f"  - TADIR Check Error: {e}")

        # 2. Check Methods in SEOCOMPODF
        try:
            r2 = conn.call("RFC_READ_TABLE", QUERY_TABLE="SEOCOMPODF",
                           OPTIONS=[{"TEXT": f"CLSNAME = '{cls}' AND CMPTYPE = '1'"}],
                           FIELDS=[{"FIELDNAME":"CMPNAME"}])
            methods = [m['WA'].strip() for m in r2.get("DATA", [])]
            print(f"  - Methods Found: {len(methods)}")
            if methods:
                print(f"    Sample: {', '.join(methods[:5])}...")
        except Exception as e:
             print(f"  - SEOCOMPODF Check Error: {e}")

    conn.close()
    print("\n--- CHECK COMPLETE ---")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
