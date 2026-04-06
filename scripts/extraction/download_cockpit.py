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

def download_report(name):
    rfc = get_conn()
    try:
        res = rfc.call("RFC_READ_REPORT", PROGRAM=name)
        lines = [l['LINE'] for l in res.get('SOURCETAB', [])]
        with open(f"{name}.abap", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Downloaded {name}.abap")
    finally:
        rfc.close()

if __name__ == "__main__":
    for rep in ["YFM_COCKPITTOP", "YFM_COCKPITF01"]:
        download_report(rep)
