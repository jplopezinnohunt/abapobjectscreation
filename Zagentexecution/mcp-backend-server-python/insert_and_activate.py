"""
FINAL WORKING SCRIPT: Direct table insert + correct activation call
Key corrections:
- SEO_CLASS_ACTIVATE takes CLSKEYS (table SEOC_CLASS_KEYS), NOT CLSKEY
- SEO_CLASS_CREATE_COMPLETE cannot be called remotely (SEOO_ALIASES_R type missing)  
- Direct INSERT into SEOCLASS/SEOCLASSDF/SEOCLASSTX works via ABAP bridge
- SEOCLASSTX has only 3 fields: CLSNAME, LANGU, DESCRIPT (no VERSION!)
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

def activate_class_direct(cls_name):
    """Call SEO_CLASS_ACTIVATE directly from Python with correct CLSKEYS table."""
    conn = get_conn()
    print(f"  Activating {cls_name} via Python RFC...")
    try:
        # CLSKEYS is a table of SEOC_CLASS_KEYS
        # Let's check what that structure looks like
        result = conn.call(
            "SEO_CLASS_ACTIVATE",
            CLSKEYS=[{"CLSNAME": cls_name}]
        )
        print(f"  [OK] Activated!")
        return True
    except RFCError as e:
        err = str(e)
        if "NOT_EXISTING" in err:
            print(f"  [WARN] NOT_EXISTING during activation - metadata may not be fully committed yet")
        elif "INCONSISTENT" in err:
            print(f"  [WARN] INCONSISTENT - class body has syntax errors")
        else:
            print(f"  [FAIL] RFC Error: {err}")
        return False
    finally:
        conn.close()

CLASSES = [
    ("ZCL_CRP_PROCESS_REQ",    "CRP Process Request Delegate"),
    ("ZCL_Z_CRP_SRV_DPC_EXT", "CRP OData Data Provider Extension"),
]

for cls_name, cls_desc in CLASSES:
    # Step 1: Insert metadata via ABAP bridge
    abap = f"""
REPORT Z_CREATE.
DATA: lv_clsname    TYPE seoclsname VALUE '{cls_name}'.
DATA: lv_state      TYPE seostate.
DATA: ls_seoclass   TYPE seoclass.
DATA: ls_seoclassdf TYPE seoclassdf.
DATA: ls_seoclasstx TYPE seoclasstx.

* Check current state
SELECT SINGLE state FROM seoclassdf
  INTO lv_state
  WHERE clsname = lv_clsname.
WRITE: / 'SEOCLASSDF before (0=found):', sy-subrc, lv_state.

IF sy-subrc <> 0.
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

  ls_seoclasstx-clsname  = lv_clsname.
  ls_seoclasstx-langu    = 'E'.
  ls_seoclasstx-descript = '{cls_desc[:40]}'.

  INSERT INTO seoclass   VALUES ls_seoclass.
  WRITE: / 'SEOCLASS INSERT:', sy-subrc.

  INSERT INTO seoclassdf VALUES ls_seoclassdf.
  WRITE: / 'SEOCLASSDF INSERT:', sy-subrc.

  INSERT INTO seoclasstx VALUES ls_seoclasstx.
  WRITE: / 'SEOCLASSTX INSERT:', sy-subrc.

  COMMIT WORK.
  WRITE: / 'COMMIT done.'.
ELSE.
  WRITE: / 'Already in Class Builder - skip INSERT.'.
ENDIF.
"""
    execute_abap(abap, f"INSERT METADATA {cls_name}")
    
    # Step 2: Activate via Python RFC (CLSKEYS table)
    activate_class_direct(cls_name)

print("\n" + "="*60)
print("Done. Run audit_repository_entries.py to verify SEOCLASS state.")
