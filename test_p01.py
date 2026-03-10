import os
from dotenv import load_dotenv
from pyrfc import Connection
import sys

project_root = r"c:\Users\jp_lopez\projects\abapobjectscreation"
dotenv_path = os.path.join(project_root, "Zagentexecution", "mcp-backend-server-python", ".env")
print(f"Loading .env from: {dotenv_path}")
load_dotenv(dotenv_path)

params = {
    "ashost": os.getenv("SAP_P01_ASHOST"),
    "sysnr": os.getenv("SAP_P01_SYSNR"),
    "client": os.getenv("SAP_P01_CLIENT"),
    "user": os.getenv("SAP_P01_USER"),
    "lang": os.getenv("SAP_P01_LANG", "EN"),
    "snc_mode": os.getenv("SAP_P01_SNC_MODE"),
    "snc_partnername": os.getenv("SAP_P01_SNC_PARTNERNAME"),
    "snc_qop": os.getenv("SAP_P01_SNC_QOP")
}

print(f"Connecting to P01: {params['ashost']}, {params['user']}")

try:
    conn = Connection(**params)
    print("Connected successfully to P01!")
    result = conn.call("RFC_READ_TABLE", QUERY_TABLE="FMFINCODE", ROWCOUNT=2, OPTIONS=[{'TEXT': "FIKRS = 'UNES'"}])
    print(f"Result: {len(result.get('DATA', []))} rows")
    for row in result.get('DATA', []):
        print(row['WA'])
    conn.close()
except Exception as e:
    print(f"Error: {e}")
