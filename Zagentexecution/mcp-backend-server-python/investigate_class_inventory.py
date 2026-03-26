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

def investigate_class_inventory(clsname):
    conn = get_conn()
    print(f"\n[INVESTIGATION: {clsname}]")
    
    # 1. Check TADIR entry again (sanity check)
    print(f"--- Repository Check (TADIR) ---")
    try:
        tadir = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR", 
                          OPTIONS=[{"TEXT": f"OBJ_NAME = '{clsname}' AND OBJECT = 'CLAS'"}])
        if tadir.get("DATA"):
            print(f"  [OK] Class exists in TADIR.")
        else:
            print(f"  [MISSING] Class not found in TADIR.")
            return
    except Exception as e:
        print(f"  TADIR check failed: {e}")

    # 2. Check Class Pool and sections via SIW_RFC_READ_REPORT
    # This is the "report" layer of the class
    sections = [
        ("CP", "Class Pool"),
        ("CU", "Public Section"),
        ("CO", "Protected Section"),
        ("CI", "Private Section")
    ]
    print(f"\n--- Include Layer Check (SIW_RFC_READ_REPORT) ---")
    for suffix, desc in sections:
        incl_name = clsname.ljust(30, '=') + suffix
        try:
            res = conn.call("SIW_RFC_READ_REPORT", I_NAME=incl_name)
            lines = res.get("E_TAB_CODE", [])
            print(f"  {suffix} ({desc}): {len(lines)} lines found.")
            if len(lines) > 0:
                print(f"    First line: {lines[0].strip()}")
        except Exception as e:
            print(f"  {suffix} ({desc}): Failed to read ({e})")

    # 3. Check Method Metadata (The Core Investigation)
    # We use SEO_GET_CLIF_REMOTE with the correct structure
    print(f"\n--- Metadata Check (SEO_GET_CLIF_REMOTE) ---")
    try:
        # Based on dump: [I] CLASS_KEY type SEOCLSKEY
        # SEOCLSKEY has one field: CLSNAME (30 chars)
        res = conn.call("SEO_GET_CLIF_REMOTE", CLASS_KEY={"CLSNAME": clsname})
        
        # Checking for method definitions
        # The export parameters from the dump were:
        # ANONYMOUS_ATTRIBUTES, ATTRIBUTES, IMPLEMENTED_INTERFACES, PARENT_CLASSES
        # Wait, the dump didn't show METHODS. Let's look for other RFCs.
        print(f"  Result Keys: {res.keys()}")
        
    except Exception as e:
        print(f"  SEO_GET_CLIF_REMOTE failed: {e}")

    conn.close()

if __name__ == "__main__":
    investigate_class_inventory("ZCL_CRP_PROCESS_REQ")
    investigate_class_inventory("ZCL_Z_CRP_SRV_DPC_EXT")
