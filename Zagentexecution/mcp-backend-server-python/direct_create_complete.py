"""
direct_create_complete.py
Call SEO_CLASS_CREATE_COMPLETE directly from Python (no ABAP bridge needed),
using the verified parameter interface.
This is the RIGHT approach: call it as a remote-capable function.
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

def create_class_complete(clsname, description, devclass="ZCRP", trkorr="D01K9B0EWT"):
    conn = get_conn()
    print(f"\n{'='*60}")
    print(f"Creating class: {clsname}")
    print(f"  Package: {devclass}, Transport: {trkorr}")
    
    # Build the class key
    cls_key = {"CLSNAME": clsname}
    
    # Class descriptions table entry
    cls_desc = [{"CLSNAME": clsname, "VERSION": "1", "LANGU": "E", "DESCRIPT": description}]
    
    try:
        result = conn.call(
            "SEO_CLASS_CREATE_COMPLETE",
            CLSKEY=cls_key,
            DEVCLASS=devclass,
            CORRNR=trkorr,
            VERSION="1",         # SEOC_VERSION_INACTIVE = 1
            OVERWRITE="X",       # SEOX_TRUE
            SUPPRESS_DIALOG="X", # Skip any dialog boxes
            CLASS_DESCRIPTIONS=cls_desc
        )
        print(f"  [OK] Class created successfully")
        korrnr = result.get("KORRNR", "")
        print(f"  Transport used: {korrnr}")
        return True
    except RFCError as e:
        err = str(e)
        if "EXISTING" in err or "existing" in err.lower():
            print(f"  [INFO] Class already exists in Class Builder - this is OK")
            return True
        print(f"  [FAIL] RFC Error: {err}")
        return False
    except Exception as e:
        print(f"  [ERROR] Unexpected error: {e}")
        return False
    finally:
        conn.close()

def activate_class(clsname):
    conn = get_conn()
    print(f"\nActivating class: {clsname}")
    cls_key = {"CLSNAME": clsname}
    try:
        conn.call("SEO_CLASS_ACTIVATE", CLSKEY=cls_key)
        print(f"  [OK] Class activated.")
        return True
    except RFCError as e:
        err = str(e)
        if "CLASS_NOT_FOUND" in err or "not_found" in err.lower():
            print(f"  [WARN] Class not found during activation: {err}")
        else:
            print(f"  [FAIL] Activation error: {err}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    classes = [
        ("ZCL_CRP_PROCESS_REQ", "CRP Process Request Delegate"),
        ("ZCL_Z_CRP_SRV_DPC_EXT", "CRP OData Data Provider Extension"),
    ]
    
    for cls_name, cls_desc in classes:
        ok = create_class_complete(cls_name, cls_desc)
        if ok:
            activate_class(cls_name)

    print("\n" + "="*60)
    print("DONE. Verify in SAP via SE24.")
