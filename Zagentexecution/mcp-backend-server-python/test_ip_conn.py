import os, sys
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

# Use IP directly
IP = "172.16.4.66"

p = {
    "ashost": IP, 
    "sysnr": os.getenv("SAP_SYSNR"),
    "client": os.getenv("SAP_CLIENT"), 
    "user": os.getenv("SAP_USER"), 
    "lang": "EN"
}
if os.getenv("SAP_PASSWD"): p["passwd"] = os.getenv("SAP_PASSWD")
if os.getenv("SAP_SNC_MODE") == "1":
    p["snc_mode"] = "1"
    p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
    p["snc_qop"] = os.getenv("SAP_SNC_QOP","9")

try:
    print(f"Connecting to {IP}...")
    conn = Connection(**p)
    print("Connected successfully!")
    
    # Try a simple call
    r = conn.call("STFC_CONNECTION", REQUTEXT="Hello SAP")
    print(f"Response: {r['ECHOTEXT']}")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
