"""
write_ccimp_c255.py
SIW_TAB_CODE: declare variable TYPE C LENGTH 255 (most compatible)
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pyrfc import Connection
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

def execute_abap(code, label=""):
    conn = get_conn()
    if label: print(f"\n[{label}]")
    src = [{"LINE": l[:72]} for l in code.split('\n')]
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
        for w in res.get("WRITES", []):
            print(f"  SAP: {w.get('ZEILE') or list(w.values())[0]}")
        if res.get("ERRORMESSAGE"):
            print(f"  ERROR: {res.get('ERRORMESSAGE')}")
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
    finally:
        conn.close()

def write_include_abap(include_name, code_lines):
    """Build long ABAP script that writes all lines to the include."""
    abap_lines = [
        "REPORT Z_WRITE_INCLUDE.",
        "DATA: lt_code TYPE TABLE OF siw_tab_code.",
        "DATA: lv_line(255) TYPE c.",
        "",
    ]
    for line in code_lines:
        escaped = line.replace("'", "''")[:70]
        abap_lines.append(f"lv_line = '{escaped}'.")
        abap_lines.append(f"APPEND lv_line TO lt_code.")
    abap_lines += [
        "",
        f"CALL FUNCTION 'SIW_RFC_WRITE_REPORT'",
        f"  EXPORTING",
        f"    i_name     = '{include_name}'",
        f"    i_tab_code = lt_code.",
        f"WRITE: / 'Write subrc:', sy-subrc.",
    ]
    
    conn = get_conn()
    print(f"\nWriting {len(code_lines)} lines to {include_name}...")
    src = [{"LINE": l[:72]} for l in abap_lines]
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
        for w in res.get("WRITES", []):
            print(f"  SAP: {w.get('ZEILE') or list(w.values())[0]}")
        if res.get("ERRORMESSAGE"):
            print(f"  ERROR: {res.get('ERRORMESSAGE')}")
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Quick test
    test_lines = [
        "CLASS ZCL_CRP_PROCESS_REQ IMPLEMENTATION.",
        "  METHOD resolve_staff_from_user.",
        "    rv_staff_id = '00000001'.",
        "  ENDMETHOD.",
        "ENDCLASS.",
    ]
    write_include_abap("ZCL_CRP_PROCESS_REQ============CCIMP", test_lines)
    
    # Verify
    execute_abap("""
REPORT Z_VERIFY.
DATA: lt_lines TYPE TABLE OF abaptxt255.
DATA: lv_line  TYPE abaptxt255.
CALL FUNCTION 'SIW_RFC_READ_REPORT'
  EXPORTING i_name = 'ZCL_CRP_PROCESS_REQ============CCIMP'
  IMPORTING e_tab_code = lt_lines
  EXCEPTIONS OTHERS = 1.
WRITE: / 'Lines count:', lines( lt_lines ).
LOOP AT lt_lines INTO lv_line.
  WRITE: / lv_line.
ENDLOOP.
""", "VERIFY CCIMP")
