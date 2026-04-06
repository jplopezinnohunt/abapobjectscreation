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
    rfc = get_conn()
    try:
        # RPY_PROGRAM_READ parameters: PROGRAM_NAME
        res = rfc.call("RPY_PROGRAM_READ", PROGRAM_NAME=name)
        lines = [l['LINE'] for l in res.get('SOURCE_EXTENDED', [])]
        if not lines:
            print(f"Report {name} is empty or not found via RPY.")
            return
        with open(f"{name}_RPY.abap", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Downloaded {name}_RPY.abap")
    except Exception as e:
        print(f"Failed to download {name}: {e}")
    finally:
        rfc.close()

if __name__ == "__main__":
    reps = [
        "ZXFMOIU01", "ZXFMOIU04", "ZXFMOIU05", "ZXFMOIU06", "ZXFMOIU07",
        "ZXFMAU01", "ZXFMAU04", "ZXFMAU05",
        "ZXFBEU01",
        "ZXM06U61", "ZXM06U12", "ZXM06U22" # Just a few critical ones first
    ]
    for rep in reps:
        download_rpy(rep)
