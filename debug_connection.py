import os
import sys
from dotenv import load_dotenv

print("Starting debug script...")
dotenv_path = os.path.join(os.path.dirname(r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python\query_table.py"), ".env")
print(f"Loading .env from: {dotenv_path}")
load_dotenv(dotenv_path)

print(f"SAP_USER: {os.getenv('SAP_USER')}")
print(f"SAP_ASHOST: {os.getenv('SAP_ASHOST')}")

try:
    from pyrfc import Connection
    print("pyrfc imported successfully")
except ImportError:
    print("pyrfc import failed")
    sys.exit(1)

params = {
    "ashost": os.getenv("SAP_ASHOST"),
    "sysnr": os.getenv("SAP_SYSNR"),
    "client": os.getenv("SAP_CLIENT"),
    "user": os.getenv("SAP_USER"),
    "passwd": os.getenv("SAP_PASSWORD") or os.getenv("SAP_PASSWD"),
    "lang": os.getenv("SAP_LANG", "EN"),
    "snc_mode": os.getenv("SAP_SNC_MODE"),
    "snc_partnername": os.getenv("SAP_SNC_PARTNERNAME"),
    "snc_qop": os.getenv("SAP_SNC_QOP")
}

print(f"Connecting to {params['ashost']}...")
try:
    conn = Connection(**params)
    print("Connected!")
    conn.close()
except Exception as e:
    print(f"Connection error: {e}")
