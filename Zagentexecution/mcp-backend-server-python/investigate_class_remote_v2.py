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
        # Based on deep_verify.py usage
        res = conn.call("SEO_GET_CLIF_REMOTE", CLIF_NAME=clsname)
        
        # Check if we got something back
        # The fields might be different depending on SAP version
        methods = res.get("DESCRIPTION_ODFS", []) # Try multiple potential fields
        comp_odfs = res.get("COMPONENT_ODFS", [])
        methods_list = res.get("METHODS", [])
        
        print(f"  Result keys: {res.keys()}")
        
        if methods_list:
            print(f"  [FOUND] {clsname} has {len(methods_list)} methods.")
            for m in methods_list:
                print(f"    - {m.get('CMPNAME')}")
        else:
            print(f"  [NOT FOUND] No methods found in list.")
            
    except Exception as e:
        print(f"  Error: {e}")
    conn.close()

if __name__ == "__main__":
    check_class_remote("ZCL_CRP_PROCESS_REQ")
    check_class_remote("ZCL_Z_CRP_SRV_DPC_EXT")
