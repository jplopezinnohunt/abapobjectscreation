"""
activate_and_deploy.py
Step 1: Activate classes via ABAP bridge (SEO_CLASS_ACTIVATE with table CLSKEYS)
Step 2: Write CCIMP implementation code via SIW_RFC_WRITE_REPORT
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pyrfc import Connection, RFCError
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    p = {"ashost": "172.16.4.66", "sysnr": "00", "client": "350",
         "user": os.getenv("SAP_USER"), "lang": "EN"}
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"
        p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = "9"
    return Connection(**p)

def execute_abap(abap_code, label=""):
    conn = get_conn()
    if label: print(f"\n[{label}]")
    abap_source = [{"LINE": line[:72]} for line in abap_code.split('\n')]
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap_source)
        writes = res.get("WRITES", [])
        for w in writes:
            val = w.get('ZEILE') or list(w.values())[0]
            print(f"  SAP: {val}")
        if res.get("ERRORMESSAGE"):
            print(f"  ERROR: {res.get('ERRORMESSAGE')}")
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
        return None
    finally:
        conn.close()

def write_include(include_name, code_lines):
    """Write ABAP code to a class include via SIW_RFC_WRITE_REPORT."""
    conn = get_conn()
    print(f"  Writing {len(code_lines)} lines to {include_name}...")
    tab_code = [{"LINE": l[:255]} for l in code_lines]
    try:
        conn.call("SIW_RFC_WRITE_REPORT", I_NAME=include_name, I_TAB_CODE=tab_code)
        print(f"  [OK] Written.")
        return True
    except RFCError as e:
        print(f"  [FAIL]: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    classes = ["ZCL_CRP_PROCESS_REQ", "ZCL_Z_CRP_SRV_DPC_EXT"]

    # Step 1: Activate via ABAP bridge (resolves SEOC_CLASS_KEYS locally)
    for cls_name in classes:
        activate_abap = f"""
REPORT Z_ACTIVATE.
DATA: lv_clsname TYPE seoclsname VALUE '{cls_name}'.
DATA: lt_clskeys TYPE TABLE OF seoclskey.
DATA: ls_clskey  TYPE seoclskey.

ls_clskey-clsname = lv_clsname.
APPEND ls_clskey TO lt_clskeys.

CALL FUNCTION 'SEO_CLASS_ACTIVATE'
  TABLES
    clskeys      = lt_clskeys
  EXCEPTIONS
    inconsistent = 1
    not_existing = 2
    not_specified = 3
    OTHERS       = 4.

WRITE: / 'ACTIVATE subrc:', sy-subrc.

* Also check state after activation
DATA: lv_state TYPE seostate.
SELECT SINGLE state FROM seoclassdf
  INTO lv_state
  WHERE clsname = lv_clsname.
WRITE: / 'State after activate:', lv_state.
"""
        execute_abap(activate_abap, f"ACTIVATE {cls_name}")

    # Step 2: Read current CCIMP content to understand state
    print("\n\n--- CCIMP content check ---")
    for cls_name in classes:
        incl_name = cls_name.ljust(30, '=') + "CCIMP"
        conn = get_conn()
        try:
            r = conn.call("SIW_RFC_READ_REPORT", I_NAME=incl_name)
            lines = r.get("E_TAB_CODE", [])
            print(f"\n  {incl_name}: {len(lines)} lines")
            for l in lines[:5]:
                print(f"    {l}")
        except Exception as e:
            print(f"  Error reading {incl_name}: {e}")
        finally:
            conn.close()
