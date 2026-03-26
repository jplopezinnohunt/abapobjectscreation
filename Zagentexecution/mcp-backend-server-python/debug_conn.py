import os, sys, time
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

p = {
    "ashost": "172.16.4.66", 
    "sysnr": "00",
    "client": "350", 
    "user": "jp_lopez", 
    "lang": "EN"
}
if os.getenv("SAP_SNC_MODE") == "1":
    p["snc_mode"] = "1"
    p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
    p["snc_qop"] = "9"

print("Starting connection attempt...")
start = time.time()
try:
    conn = Connection(**p)
    end = time.time()
    print(f"Connected in {end-start:.2f} seconds")
    conn.close()
except Exception as e:
    end = time.time()
    print(f"Failed after {end-start:.2f} seconds: {e}")
