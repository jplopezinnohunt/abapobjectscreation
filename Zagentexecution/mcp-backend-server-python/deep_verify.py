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

def deep_check(conn, cls):
    print(f"\n--- DEEP CHECK: {cls} ---")
    try:
        # Get full class info
        res = conn.call("SEO_GET_CLIF_REMOTE", CLIF_NAME=cls)
        
        # Check methods
        methods = res.get("METHODS", [])
        print(f"  Methods: {len(methods)}")
        for m in methods:
            mname = m['CMPNAME']
            # We don't have source code in this RFC, but we see they exist
            print(f"    - {mname}")

        # Check implementations via SIW_RFC_READ_REPORT for CMxxx
        # We still need the mapping, let's try reading TMDIR again with a different filter
        # Or just try reading the first 20 potential CM includes
        print("  Checking for code in method includes...")
        for i in range(1, 40):
            mincl = cls.ljust(30, '=') + "CM" + str(i).zfill(3)
            try:
                mres = conn.call("SIW_RFC_READ_REPORT", I_NAME=mincl)
                lines = mres.get("E_TAB_CODE", [])
                if len(lines) > 5:
                    # Find which method this is? 
                    # Usually the first line is "METHOD ..."
                    ml0 = lines[0].strip() if lines else ""
                    print(f"    [CODE FOUND] {mincl}: {len(lines)} lines. Start: {ml0}")
            except:
                pass

    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    conn = get_conn()
    deep_check(conn, "ZCL_CRP_PROCESS_REQ")
    deep_check(conn, "ZCL_Z_CRP_SRV_DPC_EXT")
    conn.close()
