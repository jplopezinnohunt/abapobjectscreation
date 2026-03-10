import os
from dotenv import load_dotenv
from pyrfc import Connection
import sys

dotenv_path = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python\.env"
load_dotenv(dotenv_path)

params = {
    "ashost": os.getenv("SAP_ASHOST"),
    "sysnr": os.getenv("SAP_SYSNR"),
    "client": os.getenv("SAP_CLIENT"),
    "user": os.getenv("SAP_USER"),
    "lang": os.getenv("SAP_LANG", "EN"),
    "snc_mode": os.getenv("SAP_SNC_MODE"),
    "snc_partnername": os.getenv("SAP_SNC_PARTNERNAME"),
    "snc_qop": os.getenv("SAP_SNC_QOP")
}

print(f"Connecting with: {params['ashost']}, {params['user']}")

try:
    conn = Connection(**params)
    print("Connected successfully!")
    result = conn.call("RFC_READ_TABLE", QUERY_TABLE="FMFINCODE", ROWCOUNT=5)
    print(f"Result: {len(result.get('DATA', []))} rows")
    for row in result.get('DATA', []):
        print(row['WA'])
    conn.close()
except Exception as e:
    print(f"Error: {e}")
