"""
write_via_bridge.py - Write ABAP code via ABAP bridge (RFC_ABAP_INSTALL_AND_RUN).
SIW_TAB_CODE is a flat string table. Call SIW_RFC_WRITE_REPORT inside ABAP bridge
to avoid remote field resolution issues.
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

def write_include_via_bridge(include_name, code_lines):
    """Write code via ABAP bridge which can handle flat SIW_TAB_CODE directly."""
    conn = get_conn()
    print(f"\nWriting {len(code_lines)} lines to {include_name} via ABAP bridge...")
    
    # Build the ABAP script that writes the lines
    abap_lines = [
        f"REPORT Z_WRITE_INCL.",
        f"DATA: lt_code TYPE TABLE OF siw_tab_code WITH HEADER LINE.",
        f"",
    ]
    for line in code_lines:
        escaped = line.replace("'", "''")
        abap_lines.append(f"  lt_code = '{escaped[:70]}'.")
        abap_lines.append(f"  APPEND lt_code.")
    abap_lines += [
        f"",
        f"CALL FUNCTION 'SIW_RFC_WRITE_REPORT'",
        f"  EXPORTING",
        f"    i_name     = '{include_name}'",
        f"    i_tab_code = lt_code.",
        f"IF sy-subrc = 0.",
        f"  WRITE: / 'Write OK'.",
        f"ELSE.",
        f"  WRITE: / 'Write FAILED:', sy-subrc.",
        f"ENDIF.",
    ]
    
    abap_source = [{"LINE": l[:72]} for l in abap_lines]
    
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap_source)
        for w in res.get("WRITES", []):
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

if __name__ == "__main__":
    # Test: Write 3 lines to ZCL_CRP_PROCESS_REQ============CCIMP
    test_lines = [
        "CLASS ZCL_CRP_PROCESS_REQ IMPLEMENTATION.",
        "  METHOD resolve_staff_from_user.",
        "    rv_staff_id = '00000001'.", 
        "  ENDMETHOD.",
        "ENDCLASS.",
    ]
    write_include_via_bridge("ZCL_CRP_PROCESS_REQ============CCIMP", test_lines)
    
    # Verify by reading back
    execute_abap("""
REPORT Z_READ.
DATA: lt_lines TYPE TABLE OF abaptxt255.
DATA: lv_line  TYPE abaptxt255.
CALL FUNCTION 'SIW_RFC_READ_REPORT'
  EXPORTING i_name = 'ZCL_CRP_PROCESS_REQ============CCIMP'
  IMPORTING e_tab_code = lt_lines
  EXCEPTIONS OTHERS = 1.
WRITE: / 'CCIMP lines:', sy-subrc, lines( lt_lines ).
LOOP AT lt_lines INTO lv_line.
  WRITE: / lv_line.
ENDLOOP.
""", "VERIFY CCIMP AFTER WRITE")
