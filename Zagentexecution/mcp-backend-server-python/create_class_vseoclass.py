"""
create_class_vseoclass.py
Call SEO_CLASS_CREATE_COMPLETE with correct VSEOCLASS structure as the mandatory
CLASS changing parameter. This is the definitive reconstruction approach.
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

def get_vseoclass_fields():
    """Get all fields of VSEOCLASS structure for proper population."""
    conn = get_conn()
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD03L", DELIMITER="|",
                      OPTIONS=[{"TEXT": "TABNAME = 'VSEOCLASS'"}],
                      FIELDS=[{"FIELDNAME":"FIELDNAME"}])
        fields = [row['WA'].strip() for row in r['DATA']]
        return fields
    except Exception as e:
        print(f"  Could not get VSEOCLASS fields: {e}")
        return []
    finally:
        conn.close()

def create_class(clsname, description, superclass="", devclass="ZCRP", trkorr="D01K9B0EWT"):
    conn = get_conn()
    print(f"\n{'='*60}")
    print(f"Creating class: {clsname}")
    
    # VSEOCLASS is the view of SEOCLASS + SEOCLASSDF combined
    # Mandatory fields based on SEOCLASSDF analysis:
    # CLSNAME, CLSTYPE(00=class), CATEGORY(00=general), 
    # EXPOSURE(2=public), STATE(1=implemented), VERSION(1=inactive)
    cls_struct = {
        "CLSNAME":   clsname,
        "VERSION":   "1",        # 1=inactive (will be activated next)
        "CATEGORY":  "00",       # General ABAP class
        "EXPOSURE":  "2",        # Public
        "STATE":     "1",        # Implemented (not abstract/final)
        "RELEASE":   "0",
        "AUTHOR":    os.getenv("SAP_USER", "JLOPEZ"),
        "CREATEDON": "20260310",
        "CLSFINAL":  "",         # Not final
        "CLSABSTRCT":"",         # Not abstract
        "REFCLSNAME": superclass,  # Superclass (empty = CX_OBJECT implicitly)
        "CLSBCIMPL": superclass if superclass else "",
        "FIXPT":     "X",        # Fixed point arithmetic
        "UNICODE":   "X",        # Unicode
    }
    
    # Class description
    cls_desc = [{"CLSNAME": clsname, "VERSION": "1", "LANGU": "E", "DESCRIPT": description}]

    try:
        result = conn.call(
            "SEO_CLASS_CREATE_COMPLETE",
            CLASS=cls_struct,
            DEVCLASS=devclass,
            CORRNR=trkorr,
            VERSION="1",
            OVERWRITE="X",
            SUPPRESS_DIALOG="X",
            SUPPRESS_CORR="",
            SUPPRESS_COMMIT="",
            SUPPRESS_METHOD_GENERATION="",
            CLASS_DESCRIPTIONS=cls_desc,
        )
        korrnr = result.get("KORRNR", "")
        print(f"  [OK] Class created! Transport: {korrnr}")
        return True
    except RFCError as e:
        err = str(e)
        if "EXISTING" in err:
            print(f"  [INFO] Class already exists - OK, will activate")
            return True
        print(f"  [FAIL] RFC Error: {err}")
        return False
    except Exception as e:
        print(f"  [ERROR]: {e}")
        return False
    finally:
        conn.close()

def activate_class(clsname):
    conn = get_conn()
    print(f"  Activating {clsname}...")
    cls_key = {"CLSNAME": clsname}
    try:
        conn.call("SEO_CLASS_ACTIVATE", CLSKEY=cls_key)
        print(f"  [OK] Activated!")
        return True
    except RFCError as e:
        print(f"  [WARN] Activation: {e}")
        return False
    finally:
        conn.close()

def verify_class(clsname):
    """Verify class entry in SEOCLASSDF after creation."""
    conn = get_conn()
    print(f"  Verifying {clsname} in SEOCLASSDF...")
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE="SEOCLASSDF", DELIMITER="|",
                      OPTIONS=[{"TEXT": f"CLSNAME = '{clsname}'"}],
                      FIELDS=[{"FIELDNAME":"CLSNAME"},{"FIELDNAME":"STATE"},{"FIELDNAME":"EXPOSURE"}])
        if r["DATA"]:
            print(f"  [OK] Found: {r['DATA'][0]['WA']}")
            return True
        else:
            print(f"  [MISSING] Not found in SEOCLASSDF")
            return False
    except Exception as e:
        print(f"  [ERROR]: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # Show VSEOCLASS fields first
    fields = get_vseoclass_fields()
    print(f"VSEOCLASS has {len(fields)} fields: {fields[:10]}...")

    classes = [
        ("ZCL_CRP_PROCESS_REQ", "CRP Process Request Delegate", ""),
        ("ZCL_Z_CRP_SRV_DPC_EXT", "CRP OData Data Provider Extension", "ZCL_Z_CRP_SRV_DPC"),
    ]

    for cls_name, cls_desc, super_cls in classes:
        ok = create_class(cls_name, cls_desc, super_cls)
        if ok:
            activate_class(cls_name)
            verify_class(cls_name)

    print("\n" + "="*60)
    print("DONE")
