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

def deploy_method_metadata(conn, clsname, cmpname, desr, trkorr):
    print(f"Adding Method {cmpname} to {clsname}...")
    try:
        # 1. SEO_METHOD_CREATE_P or SIW_RFC_MODIFY_CLASS? 
        # Most SAP systems have SEO_METHOD_CREATE_P for exactly this.
        
        comp_data = {
            "CLSNAME": clsname,
            "CMPNAME": cmpname,
            "VERSION": "1",
            "CMPTYPE": "1",    # Method
            "MTHTYPE": "0",    # Method
            "EXPOSURE": "2",   # Public
            "STATE": "1",      # Implemented
            "DESCRIPT": desr,
            "Langu": "E"
        }
        
        try:
            conn.call("SEO_METHOD_CREATE_P", I_METHOD=comp_data, I_DEVCLASS="ZCRP", I_CORRNR=trkorr)
            print(f"  [OK] Method {cmpname} metadata created.")
            return True
        except Exception as e:
            print(f"  SEO_METHOD_CREATE_P failed: {e}")
            
            # Alternative: Try generic component update
            try:
                conn.call("SEO_COMPONENT_CREATE_P", I_COMPONENT=comp_data, I_DEVCLASS="ZCRP", I_CORRNR=trkorr)
                print(f"  [OK] Method {cmpname} created via SEO_COMPONENT_CREATE_P.")
                return True
            except:
                return False

    except Exception as e:
        print(f"  Error: {e}")
        return False

if __name__ == "__main__":
    conn = get_conn()
    tr = "D01K9B0EWT"
    cls = "ZCL_CRP_PROCESS_REQ"
    # Test with one core method
    deploy_method_metadata(conn, cls, "RESOLVE_STAFF_FROM_USER", "Resolve staff details from SAP username", tr)
    conn.close()
