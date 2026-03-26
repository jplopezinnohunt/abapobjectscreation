import os, sys
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    # Using the working IP connection
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
        p["snc_qop"] = "9"
    return Connection(**p)

def deploy_definition(conn, clsname, definition_file):
    print(f"\n[DEPLOYING DEFINITION: {clsname}]")
    
    with open(definition_file, 'r') as f:
        full_code = f.readlines()
    
    # Extract Sections
    public_section = []
    protected_section = []
    private_section = []
    
    current_sec = None
    for line in full_code:
        upper = line.upper().strip()
        if "PUBLIC SECTION." in upper: current_sec = "PUBLIC"
        elif "PROTECTED SECTION." in upper: current_sec = "PROTECTED"
        elif "PRIVATE SECTION." in upper: current_sec = "PRIVATE"
        elif "ENDCLASS." in upper: current_sec = None
        
        if current_sec == "PUBLIC" and "PUBLIC SECTION." not in upper:
            public_section.append(line.rstrip())
        elif current_sec == "PROTECTED" and "PROTECTED SECTION." not in upper:
            protected_section.append(line.rstrip())
        elif current_sec == "PRIVATE" and "PRIVATE SECTION." not in upper:
            private_section.append(line.rstrip())

    # Includes
    incl_cu = clsname.ljust(30, '=') + "CU"
    incl_co = clsname.ljust(30, '=') + "CO"
    incl_ci = clsname.ljust(30, '=') + "CI"

    # Push to SAP
    try:
        print(f"  Pushing Public Section ({len(public_section)} lines)...")
        conn.call("SIW_RFC_WRITE_REPORT", I_NAME=incl_cu, I_TAB_CODE=public_section, I_EXTENSION='')
        
        print(f"  Pushing Protected Section ({len(protected_section)} lines)...")
        conn.call("SIW_RFC_WRITE_REPORT", I_NAME=incl_co, I_TAB_CODE=protected_section, I_EXTENSION='')
        
        print(f"  Pushing Private Section ({len(private_section)} lines)...")
        conn.call("SIW_RFC_WRITE_REPORT", I_NAME=incl_ci, I_TAB_CODE=private_section, I_EXTENSION='')
        
        print(f"  [OK] Sections written for {clsname}")
        
        # Force Activation
        print(f"  Activating {clsname}...")
        conn.call("SEO_CLASS_ACTIVATE", CLSNAME=clsname)
        print("  [OK] Activation call finished.")
        
    except Exception as e:
        print(f"  FAILED: {e}")

if __name__ == "__main__":
    conn = get_conn()
    # 1. First the processing class
    deploy_definition(conn, "ZCL_CRP_PROCESS_REQ", r"c:\Users\jp_lopez\projects\unescrp\src\abap\classes\PASTE_ZCL_CRP_PROCESS_REQ_DEFINITION.abap")
    conn.close()
