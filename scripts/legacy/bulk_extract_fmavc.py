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

def download_rpy(name):
    print(f"Attempting to download {name}...")
    try:
        rfc = get_conn()
        res = rfc.call("RPY_PROGRAM_READ", PROGRAM_NAME=name)
        lines = [l['LINE'] for l in res.get('SOURCE_EXTENDED', [])]
        if not lines:
            print(f"Report {name} is empty or not found.")
            return
        filename = os.path.join(PROJECT_ROOT, f"{name}_RPY.abap")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Successfully downloaded {name}_RPY.abap")
        rfc.close()
    except Exception as e:
        print(f"Failed to download {name}: {e}")

if __name__ == "__main__":
    reps = ["ZXFMCU09", "ZXFMCU10", "ZXFMCU11", "ZXFMCU12", "ZXFMCU14", "ZXFMCU19", "ZXFMCU20", "ZXFMCU21"]
    for rep in reps:
        download_rpy(rep)
