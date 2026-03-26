import os, sys
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    p = {"ashost":os.getenv("SAP_ASHOST"), "sysnr":os.getenv("SAP_SYSNR"),
         "client":os.getenv("SAP_CLIENT"), "user":os.getenv("SAP_USER"), "lang":"EN"}
    if os.getenv("SAP_PASSWD"): p["passwd"] = os.getenv("SAP_PASSWD")
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"]="1"; p["snc_partnername"]=os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"]=os.getenv("SAP_SNC_QOP","9")
    return Connection(**p)

def create_empty_class(conn, class_name, package, description, trkorr):
    print(f"Creating empty class {class_name} in package {package}...")
    try:
        # We'll use a standard RFC if available, or try SIW_RFC_CREATE_OBJECT
        # For now, let's try to find an RFC that can create a class.
        # Often SEO_CLASS_CREATE_RFC or similar exists.
        
        # Fallback: Many systems have RS_CREATE_CLASS or SEO_CLASS_CREATE
        # Let's try SEO_CLASS_CREATE_P which is common in newer systems
        
        cls_data = {
            "CLSNAME": class_name,
            "VERSION": "1",
            "Langu": "E",
            "DESCRIPT": description,
            "CATEGORY": "00", # General Class
            "EXPOSURE": "2",  # Public
            "STATE": "1",     # Implemented
            "RELEASE": "0",
            "AUTHOR": os.getenv("SAP_USER"),
            "CREATEDON": "20260310",
        }
        
        # Try SEO_CLASS_CREATE_P
        try:
            conn.call("SEO_CLASS_CREATE_P", I_CLASS=cls_data, I_DEVCLASS=package, I_CORRNR=trkorr)
            print(f"  [OK] Class {class_name} created successfully.")
            return True
        except Exception as e1:
            print(f"  SEO_CLASS_CREATE_P failed: {e1}")
            
            # Alternative: try generic object creation if SEO specialized fails
            try:
                # Some systems use SIW_RFC_CREATE_OBJECT
                conn.call("SIW_RFC_CREATE_OBJECT", I_TYPE="CLAS", I_NAME=class_name, I_DEVCLASS=package, I_TRKORR=trkorr)
                print(f"  [OK] Class {class_name} created via SIW_RFC_CREATE_OBJECT.")
                return True
            except Exception as e2:
                print(f"  SIW_RFC_CREATE_OBJECT failed: {e2}")
                return False

    except Exception as e:
        print(f"  Failed to create class: {e}")
        return False

if __name__ == "__main__":
    conn = get_conn()
    tr = "D01K9B0EWT"
    create_empty_class(conn, "ZCL_CRP_PROCESS_REQ", "ZCRP", "CRP Process Request Delegate", tr)
    conn.close()
