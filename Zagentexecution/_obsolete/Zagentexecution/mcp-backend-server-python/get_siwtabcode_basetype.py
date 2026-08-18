"""
get_siwtabcode_basetype.py
Get the raw/base type of SIW_TAB_CODE to understand how to populate it.
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

if __name__ == "__main__":
    # Inspect SIW_TAB_CODE vs PROGTAB structures
    execute_abap("""
REPORT Z_INSPECT_SIWTAB.
DATA: ls_tab_type TYPE dd40l.
SELECT SINGLE * FROM dd40l INTO ls_tab_type
  WHERE typename = 'SIW_TAB_CODE'.
WRITE: / 'SIW_TAB_CODE tyepkind:', ls_tab_type-typekind.
WRITE: / 'SIW_TAB_CODE tabkind:', ls_tab_type-tabkind.
WRITE: / 'SIW_TAB_CODE rowtype:', ls_tab_type-rowtype.
WRITE: / 'SIW_TAB_CODE exid:', ls_tab_type-exid.

* Also check the element type
DATA: ls_el TYPE dd04l.
SELECT SINGLE * FROM dd04l INTO ls_el
  WHERE typename = 'SIW_TAB_CODE'.
WRITE: / 'SIW_TAB_CODE domain datatype:', ls_el-datatype, ls_el-leng, ls_el-domname.
""", "SIW_TAB_CODE BASE TYPE")

    # Check PROGTAB (used by RFC_ABAP_INSTALL_AND_RUN)
    execute_abap("""
REPORT Z_INSPECT_PROGTAB.
DATA: lt_dfies TYPE TABLE OF dfies.
DATA: ls_dfies TYPE dfies.
CALL FUNCTION 'DDIF_FIELDINFO_GET'
  EXPORTING tabname = 'PROGTAB'
  TABLES dfies_tab = lt_dfies
  EXCEPTIONS OTHERS = 1.
WRITE: / 'PROGTAB fields:'.
LOOP AT lt_dfies INTO ls_dfies.
  WRITE: / ls_dfies-fieldname, ls_dfies-datatype, ls_dfies-leng.
ENDLOOP.
""", "PROGTAB FIELDS")
