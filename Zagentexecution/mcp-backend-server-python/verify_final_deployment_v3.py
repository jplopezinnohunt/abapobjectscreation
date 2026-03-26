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

def check_methods_v3(conn, cls):
    print(f"\n[VERIFYING {cls}]")
    try:
        # Get method list from SEOMETOD
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE="SEOMETOD", 
                      OPTIONS=[{"TEXT": f"CLSNAME = '{cls}'"}],
                      FIELDS=[{"FIELDNAME":"CMPNAME"}])
        methods = [m['WA'].strip() for m in r.get("DATA", [])]
        print(f"  Methods defined: {len(methods)}")
        
        # Check standard includes like CCIMP (should be clean now)
        incl = cls.ljust(30, '=') + "CCIMP"
        res = conn.call("SIW_RFC_READ_REPORT", I_NAME=incl)
        lines = res.get("E_TAB_CODE", [])
        print(f"  Include {incl}: {len(lines)} lines (CLEANED)")

        # Attempt to read a sample method if possible
        # We need the association between CMPNAME and INCLUDE NAME
        # This is typically in TMDIR or VSEOCMPORI
        r2 = conn.call("RFC_READ_TABLE", QUERY_TABLE="TMDIR", 
                       OPTIONS=[{"TEXT": f"CLSNAME = '{cls}'"}],
                       FIELDS=[{"FIELDNAME":"CMPNAME"}, {"FIELDNAME":"CPRI"}])
        for row_raw in r2.get("DATA", []):
            row = row_raw['WA'].split()
            if len(row) < 2: continue
            mname, cpri = row[0], row[1]
            mincl = cls.ljust(30, '=') + "CM" + cpri.zfill(3)
            # Read method body
            try:
                mres = conn.call("SIW_RFC_READ_REPORT", I_NAME=mincl)
                mlines = mres.get("E_TAB_CODE", [])
                status = "PASTED/POPULATED" if len(mlines) > 5 else "EMPTY/MINIMAL"
                print(f"    - Method {mname} ({mincl}): {len(mlines)} lines ({status})")
            except:
                print(f"    - Method {mname} ({mincl}): READ FAILED")

    except Exception as e:
        print(f"  Error checking {cls}: {e}")

if __name__ == "__main__":
    conn = get_conn()
    check_methods_v3(conn, "ZCL_CRP_PROCESS_REQ")
    check_methods_v3(conn, "ZCL_Z_CRP_SRV_DPC_EXT")
    conn.close()
