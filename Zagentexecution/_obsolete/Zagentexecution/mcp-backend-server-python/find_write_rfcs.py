"""find_write_rfcs.py — Discovers available RFC functions for writing ABAP source"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

load_dotenv()
def get_conn():
    p = {"ashost":os.getenv("SAP_ASHOST"), "sysnr":os.getenv("SAP_SYSNR"),
         "client":os.getenv("SAP_CLIENT"), "user":os.getenv("SAP_USER"), "lang":"EN"}
    if os.getenv("SAP_PASSWD"): p["passwd"] = os.getenv("SAP_PASSWD")
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"; p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = os.getenv("SAP_SNC_QOP","9")
    return Connection(**p)

conn = get_conn()

candidates = [
    "SIW_RFC_WRITE_REPORT",
    "RPY_REPORT_WRITE",
    "RPY_INCLUDE_WRITE",
    "SEO_SOURCE_WRITE",
    "SIW_RFC_WRITE_INCLUDE",
    "RS_PROGRAM_WRITE",
    "REPS_PROGRAM_WRITE",
    "RFC_ABAP_INSTALL_AND_RUN",
    "SLDAG_RFC_WRITE_REPORT",
    "SIW_RFC_WRITE",
    "TR_WRITE_E070",
]

for fn in candidates:
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TFDIR", DELIMITER="|",
                      OPTIONS=[{"TEXT": f"FUNCNAME = '{fn}'"}],
                      FIELDS=[{"FIELDNAME":"FUNCNAME"},{"FIELDNAME":"REMOTE"}], ROWCOUNT=1)
        rows = r.get("DATA", [])
        if rows:
            print(f"FOUND:     {rows[0]['WA'].strip()}")
        else:
            print(f"NOT FOUND: {fn}")
    except Exception as e:
        print(f"ERR {fn}: {e}")

# Also search by pattern — find anything with WRITE+REPORT or WRITE+SOURCE
print("\n=== Search for *WRITE*REPORT* in TFDIR ===")
try:
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TFDIR", DELIMITER="|",
                  OPTIONS=[{"TEXT": "FUNCNAME LIKE '%WRITE%REPORT%'"}],
                  FIELDS=[{"FIELDNAME":"FUNCNAME"},{"FIELDNAME":"REMOTE"}], ROWCOUNT=20)
    for row in r.get("DATA", []):
        print(f"  {row['WA'].strip()}")
except Exception as e:
    print(f"  Search failed: {e}")

print("\n=== Search for *WRITE*SOURCE* in TFDIR ===")
try:
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TFDIR", DELIMITER="|",
                  OPTIONS=[{"TEXT": "FUNCNAME LIKE '%WRITE%SOURCE%'"}],
                  FIELDS=[{"FIELDNAME":"FUNCNAME"},{"FIELDNAME":"REMOTE"}], ROWCOUNT=20)
    for row in r.get("DATA", []):
        print(f"  {row['WA'].strip()}")
except Exception as e:
    print(f"  Search failed: {e}")

conn.close()
