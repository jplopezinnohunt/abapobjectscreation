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

def check_class_remote(clsname):
    conn = get_conn()
    print(f"\nChecking class: {clsname} via SEO_GET_CLIF_REMOTE")
    try:
        res = conn.call("SEO_GET_CLIF_REMOTE", I_CLSNAME=clsname)
        cls_data = res.get("E_CLASS", {})
        if cls_data and cls_data.get("CLSNAME"):
            print(f"  [FOUND] {clsname} exists.")
            print(f"  Version: {cls_data.get('VERSION')}")
            print(f"  Description: {cls_data.get('DESCRIPT')}")
            print(f"  State: {cls_data.get('STATE')}")
            
            # Check methods
            methods = res.get("E_COMPONENT_ODFS", [])
            print(f"  Found {len(methods)} method definitions.")
            for m in methods:
                print(f"    - {m['CMPNAME']}")
        else:
            print(f"  [NOT FOUND] SEO_GET_CLIF_REMOTE returned empty.")
    except Exception as e:
        print(f"  Error: {e}")
    conn.close()

if __name__ == "__main__":
    check_class_remote("ZCL_CRP_PROCESS_REQ")
    check_class_remote("ZCL_Z_CRP_SRV_DPC_EXT")
