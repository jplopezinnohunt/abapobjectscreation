import os
from dotenv import load_dotenv
from pyrfc import Connection

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
DOTENV_PATH = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python", ".env")

def get_conn():
    load_dotenv(DOTENV_PATH)
    params = {
        "ashost": os.getenv("SAP_P01_ASHOST"),
        "sysnr": os.getenv("SAP_P01_SYSNR"),
        "client": os.getenv("SAP_P01_CLIENT"),
        "user": os.getenv("SAP_P01_USER"),
        "lang": "EN",
        "snc_mode": "1",
        "snc_partnername": os.getenv("SAP_P01_SNC_PARTNERNAME"),
        "snc_qop": "9"
    }
    return Connection(**params)

def read_class(class_name):
    rfc = get_conn()
    try:
        # Get includes for the class
        res = rfc.call('SEO_CLASS_GET_METHOD_INCLUDES', CLSKEY={'CLSNAME': class_name})
        includes = res.get('INCLUDES', [])
        
        all_code = []
        for inc in includes:
            inc_name = inc.get('INCUDENAME', inc.get('INCNAME'))
            if not inc_name:
                continue
            try:
                prog = rfc.call('RFC_READ_REPORT', PROGRAM=inc_name)
                source = [line['LINE'] for line in prog.get('SOURCETAB', [])]
                all_code.append(f"\n* METHOD INCLUDE: {inc_name} *\n")
                all_code.extend(source)
            except Exception as e:
                print(f"Failed to read {inc_name}: {e}")
                
        with open(f"{class_name}.abap", "w", encoding="utf-8") as f:
            f.write("\n".join(all_code))
        print(f"Success. Wrote {class_name}.abap")
    except Exception as e:
        print(f"Error reading class: {e}")
    finally:
        rfc.close()

if __name__ == "__main__":
    read_class("YCL_YPS8_BCS_BL")
