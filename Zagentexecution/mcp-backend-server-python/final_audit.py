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

conn = get_conn()
classes = ["ZCL_CRP_PROCESS_REQ", "ZCL_Z_CRP_SRV_DPC_EXT"]

print("============================================================")
print("FINAL DEPLOYMENT AUDIT - SAP D01 (CLIENT 350)")
print("============================================================")

for cls in classes:
    print(f"\n[CLASS: {cls}]")
    
    # 1. Existence and Package
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR",
                      OPTIONS=[{"TEXT": f"OBJ_NAME = '{cls}' AND OBJECT = 'CLAS'"}],
                      FIELDS=[{"FIELDNAME":"DEVCLASS"}])
        if r.get("DATA"):
            print(f"  - Package: {r['DATA'][0]['WA'].strip()} (OK)")
        else:
            print(f"  - Repository: MISSING (Not in TADIR)")
    except Exception as e:
        print(f"  - Repository Check Error: {e}")

    # 2. Method Source Check
    print("  - Methods Check:")
    try:
        # Search TRDIR for CM (Method Implementation) includes
        search_name = cls.ljust(30, '=') + "CM%"
        r2 = conn.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR",
                       OPTIONS=[{"TEXT": f"NAME LIKE '{search_name}'"}],
                       FIELDS=[{"FIELDNAME":"NAME"}])
        includes = [i['WA'].strip() for i in r2.get("DATA", [])]
        
        if not includes:
            print("    [!] No method implementation includes (CMxxx) found in TRDIR.")
        else:
            for i in sorted(includes):
                try:
                    mres = conn.call("SIW_RFC_READ_REPORT", I_NAME=i)
                    mlines = mres.get("E_TAB_CODE", [])
                    status = f"OK ({len(mlines)} lines)" if len(mlines) > 5 else "EMPTY/DUMMY"
                    # Try to get method name from the code
                    mname = "Unknown"
                    for l in mlines:
                        if "METHOD" in l.upper():
                            mname = l.strip().replace('METHOD', '').replace('.', '').strip()
                            break
                    print(f"    - {i} -> Method {mname}: {status}")
                except:
                    print(f"    - {i}: READ FAILED")
    except Exception as e:
        print(f"    - Error reading TRDIR: {e}")

print("\n============================================================")
print("AUDIT COMPLETE")
print("============================================================")
conn.close()
