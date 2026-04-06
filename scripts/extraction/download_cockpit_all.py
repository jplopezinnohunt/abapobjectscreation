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
        res = rfc.call("RPY_PROGRAM_READ", PROGRAM_NAME=name)
        source = res.get('SOURCE_EXTENDED', res.get('SOURCE', []))
        lines = [l['LINE'] for l in source]
        if not lines:
            print(f"Report {name} empty via RPY.")
            return
        filename = f"{name}_RPY.abap"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Downloaded {filename}")
    except Exception as e:
        print(f"Failed {name} via RPY: {e}")
    finally:
        rfc.close()

if __name__ == "__main__":
    reps = ["YFM_COCKPITI01", "YFM_COCKPITO01", "YFM_COCKPITTOP", "YFM_COCKPITF01"]
    for rep in reps:
        download_rpy(rep)
