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

def verify_code(conn, cls):
    print(f"\n--- CODE VERIFICATION: {cls} ---")
    cp_name = cls.ljust(30, '=') + "CP"
    try:
        res = conn.call("SIW_RFC_READ_REPORT", I_NAME=cp_name)
        lines = res.get("E_TAB_CODE", [])
        print(f"  Class Pool {cp_name} read. Scanning for method includes...")
        
        # Scan for "include ... cm..."
        for line in lines:
            if "INCLUDE" in line.upper() and "CM" in line.upper():
                # Extract include name
                parts = line.split()
                if len(parts) >= 2:
                    mincl = parts[1].strip('.').strip()
                    # Now read the include
                    try:
                        mres = conn.call("SIW_RFC_READ_REPORT", I_NAME=mincl)
                        mlines = mres.get("E_TAB_CODE", [])
                        status = "OK (Populated)" if len(mlines) > 5 else "EMPTY"
                        print(f"    - Include {mincl}: {len(mlines)} lines ({status})")
                        if len(mlines) > 0:
                            print(f"      First line: {mlines[0].strip()}")
                    except:
                         print(f"    - Include {mincl}: READ FAILED")
    except Exception as e:
        print(f"  Error reading Class Pool: {e}")

if __name__ == "__main__":
    conn = get_conn()
    verify_code(conn, "ZCL_CRP_PROCESS_REQ")
    verify_code(conn, "ZCL_Z_CRP_SRV_DPC_EXT")
    conn.close()
