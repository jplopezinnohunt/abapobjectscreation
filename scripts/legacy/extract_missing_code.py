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
        "snc_partnername": f"{os.getenv('SAP_P01_SNC_PARTNERNAME')}",
        "snc_qop": "9"
    }
    return Connection(**params)

def download_rpy(name, output_name=None):
    print(f"Attempting to download {name}...")
    if output_name is None:
        output_name = f"{name}_RPY.abap"
    try:
        rfc = get_conn()
        res = rfc.call("RPY_PROGRAM_READ", PROGRAM_NAME=name)
        lines = [l['LINE'] for l in res.get('SOURCE_EXTENDED', [])]
        if not lines:
            print(f"Report {name} is empty or not found.")
            return
        filename = os.path.join(PROJECT_ROOT, output_name)
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Successfully downloaded {name} to {filename}")
        rfc.close()
    except Exception as e:
        print(f"Failed to download {name}: {e}")

if __name__ == "__main__":
    reps = [
        "YCL_SAP_TO_WORD===============CU", 
        "YCL_SAP_TO_WORD===============CP", 
        "YCL_SAP_TO_WORD===============CM001",
        "YCL_YPS8_BCS_BL===============CM004", # Try next method
        "YCL_YPS8_BCS_BL===============CM005"
    ]
    for rep in reps:
        download_rpy(rep)
