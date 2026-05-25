import os, socket, time
from dotenv import load_dotenv
load_dotenv()

host = os.getenv("SAP_ASHOST")
sysnr = os.getenv("SAP_SYSNR", "00")
port = 3200 + int(sysnr)   # dispatcher
gw_port = 3300 + int(sysnr)  # gateway

print(f"Target: {host}  sysnr={sysnr}")
print(f"Testing TCP reachability...")

for label, p in [("dispatcher", port), ("gateway", gw_port)]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    t0 = time.time()
    try:
        s.connect((host, p))
        print(f"  {label} {host}:{p}  OPEN  ({(time.time()-t0)*1000:.0f} ms)")
        s.close()
    except Exception as e:
        print(f"  {label} {host}:{p}  FAILED  ({(time.time()-t0)*1000:.0f} ms)  -> {e}")

print()
print("Testing RFC logon...")
try:
    from pyrfc import Connection
    p = {"ashost": host, "sysnr": sysnr, "client": os.getenv("SAP_CLIENT"),
         "user": os.getenv("SAP_USER"), "lang": "EN"}
    if os.getenv("SAP_PASSWD"):
        p["passwd"] = os.getenv("SAP_PASSWD")
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"
        p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = os.getenv("SAP_SNC_QOP", "9")
    t0 = time.time()
    conn = Connection(**p)
    print(f"  RFC logon OK  ({(time.time()-t0)*1000:.0f} ms)")
    r = conn.call("STFC_CONNECTION", REQUTEXT="ping")
    print(f"  STFC_CONNECTION echo: {r.get('ECHOTEXT')!r}")
    conn.close()
except Exception as e:
    print(f"  RFC FAILED: {e}")
