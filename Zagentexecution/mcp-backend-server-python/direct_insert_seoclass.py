"""
seo_class_create_via_bridge.py
Use SEO_CLASS_CREATE with SEOC_CLASSES_W table via ABAP bridge (RFC_ABAP_INSTALL_AND_RUN).
SEOC_CLASSES_W appears to be empty on this system - so use alternative CDS/direct INSERT approach.
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

if __name__ == "__main__":
    classes = [
        ("ZCL_CRP_PROCESS_REQ",    "CRP Process Request Delegate"),
        ("ZCL_Z_CRP_SRV_DPC_EXT", "CRP OData Data Provider Extension"),
    ]
    
    for cls_name, cls_desc in classes:
        # Strategy: Use the simpler SEO_CLASS_CREATE via ABAP bridge
        # Pass CLASSES table with one row
        # SEO_CLASS_CREATE uses SEOC_CLASSES_W which may be dynamically resolved
        abap = f"""
REPORT Z_CREATE.
DATA: lv_clsname TYPE seoclsname VALUE '{cls_name}'.
DATA: lv_state   TYPE seostate.
DATA: ls_clskey  TYPE seoclskey.

ls_clskey-clsname = lv_clsname.

* 1. Check if class exists in class builder already
SELECT SINGLE state FROM seoclassdf
  INTO lv_state
  WHERE clsname = lv_clsname.
WRITE: / 'State in SEOCLASSDF (0=found):', sy-subrc, lv_state.

* 2. Try insert into SEOCLASS and SEOCLASSDF directly
DATA: ls_seoclass   TYPE seoclass.
DATA: ls_seoclassdf TYPE seoclassdf.

ls_seoclass-clsname = lv_clsname.
ls_seoclass-clstype = '00'.

ls_seoclassdf-clsname   = lv_clsname.
ls_seoclassdf-version   = '1'.
ls_seoclassdf-category  = '00'.
ls_seoclassdf-exposure  = '2'.
ls_seoclassdf-state     = '1'.
ls_seoclassdf-release   = '0'.
ls_seoclassdf-author    = sy-uname.
ls_seoclassdf-createdon = sy-datum.
ls_seoclassdf-fixpt     = 'X'.
ls_seoclassdf-unicode   = 'X'.

INSERT INTO seoclass VALUES ls_seoclass.
WRITE: / 'SEOCLASS INSERT subrc:', sy-subrc.

INSERT INTO seoclassdf VALUES ls_seoclassdf.
WRITE: / 'SEOCLASSDF INSERT subrc:', sy-subrc.

DATA: ls_seoclasstx TYPE seoclasstx.
ls_seoclasstx-clsname  = lv_clsname.
ls_seoclasstx-langu    = 'E'.
ls_seoclasstx-descript = '{cls_desc[:40]}'.
INSERT INTO seoclasstx VALUES ls_seoclasstx.
WRITE: / 'SEOCLASSTX INSERT subrc:', sy-subrc.

COMMIT WORK.

* 3. Now activate
CALL FUNCTION 'SEO_CLASS_ACTIVATE'
  EXPORTING
    clskey          = ls_clskey
  EXCEPTIONS
    class_not_found = 1
    OTHERS          = 2.
WRITE: / 'ACTIVATE subrc:', sy-subrc.
"""
        execute_abap(abap, f"CREATE+ACTIVATE {cls_name}")
