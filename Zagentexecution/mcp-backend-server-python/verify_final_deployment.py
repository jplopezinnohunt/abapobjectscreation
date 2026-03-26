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

def check_methods(conn, class_name):
    print(f"\n--- Checking Methods for {class_name} ---")
    try:
        # Get method to include mapping
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TMDIR", 
                      OPTIONS=[{"TEXT": f"CLSNAME = '{class_name}'"}],
                      FIELDS=[{"FIELDNAME":"CMPNAME"}, {"FIELDNAME":"CPRI"}])
        
        methods = r.get("DATA", [])
        if not methods:
            print("  No methods found in TMDIR.")
            return

        for m in methods:
            row = m['WA'].split()
            mname = row[0]
            # Include is usually Class (30 chars) + 'CM' + CPRI (3 chars)
            # However CPRI in TMDIR is the sequential number
            cpri = row[1]
            incl = class_name.ljust(30, '=') + "CM" + cpri.zfill(3)
            
            # Read first 5 lines of the method
            try:
                res = conn.call("SIW_RFC_READ_REPORT", I_NAME=incl)
                lines = res.get("E_TAB_CODE", [])
                content = " ".join([l.strip() for l in lines if l.strip()])
                status = "PASTED" if len(lines) > 2 else "EMPTY"
                print(f"  [{status}] {mname} ({incl})")
            except:
                print(f"  [ERROR] Could not read {mname}")

    except Exception as e:
        print(f"  Failed: {e}")

if __name__ == "__main__":
    c = get_conn()
    check_methods(c, "ZCL_Z_CRP_SRV_DPC_EXT")
    check_methods(c, "ZCL_CRP_PROCESS_REQ")
    c.close()
