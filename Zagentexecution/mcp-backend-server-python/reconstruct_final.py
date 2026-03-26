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

# Critical insight: VALUE() constructors NOT supported in RFC_ABAP_INSTALL_AND_RUN
# Must use explicit DATA declarations and assignments.

if __name__ == "__main__":
    classes = [
        ("ZCL_CRP_PROCESS_REQ", "CRP Process Request Delegate"),
        ("ZCL_Z_CRP_SRV_DPC_EXT", "CRP Data Provider Extension"),
    ]
    
    for cls_name, cls_desc in classes:
        # Use explicit DATA type declarations - no VALUE() constructors, no inline decls
        abap_code = f"""
REPORT Z_RECONSTRUCT_{cls_name[:10]}.
DATA: lv_clsname TYPE seoclsname.
DATA: lv_devclass TYPE devclass.
DATA: lv_corrnr TYPE trkorr.
DATA: lv_state TYPE seostate.
DATA: ls_clskey TYPE seoclskey.

lv_clsname = '{cls_name}'.
lv_devclass = 'ZCRP'.
lv_corrnr = 'D01K9B0EWT'.

ls_clskey-clsname = lv_clsname.

WRITE: / 'Processing:', lv_clsname.

* 1. Check if entry already exists
SELECT SINGLE state FROM seoclassdf
  INTO lv_state
  WHERE clsname = lv_clsname.
WRITE: / 'SEOCLASSDF subrc:', sy-subrc, 'state:', lv_state.

* 2. Try SEO_CLASS_CREATE_COMPLETE - creates full metadata
CALL FUNCTION 'SEO_CLASS_CREATE_COMPLETE'
  EXPORTING
    clskey    = ls_clskey
    devclass  = lv_devclass
    corrnr    = lv_corrnr
    version   = '1'
  EXCEPTIONS
    class_already_existing = 1
    class_not_creatable    = 2
    OTHERS                 = 3.
WRITE: / 'CREATE_COMPLETE subrc:', sy-subrc.

* 3. Activate
CALL FUNCTION 'SEO_CLASS_ACTIVATE'
  EXPORTING
    clskey    = ls_clskey
  EXCEPTIONS
    class_not_found = 1
    OTHERS          = 2.
WRITE: / 'ACTIVATE subrc:', sy-subrc.
"""
        execute_abap(abap_code, f"RECONSTRUCT {cls_name}")
