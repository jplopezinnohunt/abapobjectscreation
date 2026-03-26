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

def deploy_methods_via_direct_write(conn, clsname, trkorr):
    print(f"Bypassing SE24: Pushing Method Definitions for {clsname}...")
    
    # 1. We need to write into the CU (Public Section) include
    # This include contains the CLASS definition (METHODS resolove_staff...)
    include_cu = clsname.ljust(30, '=') + "CU"
    
    code_cu = [
        f"class {clsname} definition",
        "  public",
        "  final",
        "  create public .",
        "",
        "public section.",
        "  CLASS-METHODS resolve_staff_from_user",
        "    IMPORTING",
        "      iv_uname TYPE sy-uname",
        "    EXPORTING",
        "      ev_pernr TYPE pernr_d",
        "      ev_name  TYPE string",
        "      ev_msg   TYPE string .",
        "",
        "  CLASS-METHODS check_budget_availability",
        "    IMPORTING",
        "      iv_amount TYPE p",
        "    RETURNING",
        "      VALUE(rv_ok) TYPE abap_bool .",
        "endclass."
    ]
    
    print(f"  Writing Public Section to {include_cu}...")
    try:
        conn.call("SIW_RFC_WRITE_REPORT", I_NAME=include_cu, I_TAB_CODE=code_cu, I_EXTENSION='')
        print("  [OK] Public Section Saved.")
        
        # 2. Write to CI (Private Section) to close the endclass if needed
        include_ci = clsname.ljust(30, '=') + "CI"
        # Often CU has the starts, CI/CO/CU are merged at runtime.
        
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False

if __name__ == "__main__":
    conn = get_conn()
    deploy_methods_via_direct_write(conn, "ZCL_CRP_PROCESS_REQ", "D01K9B0EWT")
    conn.close()
