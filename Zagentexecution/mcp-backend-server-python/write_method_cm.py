"""
write_method_cm.py
Discovers method CM include names for DPC_EXT and ZCL_CRP_PROCESS_REQ
by reading SEOIMPLEM (SAP class method implementation table) and TRDIR.
Then writes each method body via SIW_RFC_WRITE_REPORT.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv()
def get_conn():
    p = {"ashost":os.getenv("SAP_ASHOST"), "sysnr":os.getenv("SAP_SYSNR"),
         "client":os.getenv("SAP_CLIENT"), "user":os.getenv("SAP_USER"), "lang":"EN"}
    if os.getenv("SAP_PASSWD"): p["passwd"] = os.getenv("SAP_PASSWD")
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"]="1"; p["snc_partnername"]=os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"]=os.getenv("SAP_SNC_QOP","9")
    return Connection(**p)

conn = get_conn()
print(f"Connected: {os.getenv('SAP_ASHOST')}/{os.getenv('SAP_CLIENT')}")

# Query SEOIMPLEM — stores method-to-include mapping
for cls in ["ZCL_Z_CRP_SRV_DPC_EXT", "ZCL_CRP_PROCESS_REQ"]:
    print(f"\n=== SEOIMPLEM for {cls} ===")
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE="SEOIMPLEM", DELIMITER="|",
                      OPTIONS=[{"TEXT": f"CLSNAME = '{cls}'"}],
                      FIELDS=[{"FIELDNAME":"CLSNAME"},{"FIELDNAME":"MTDNAME"},
                               {"FIELDNAME":"INCNAME"}],
                      ROWCOUNT=50)
        rows = r.get("DATA", [])
        if rows:
            for row in rows:
                print(f"  {row['WA'].strip()}")
        else:
            print("  (no entries in SEOIMPLEM)")
    except Exception as e:
        print(f"  Error: {e}")

    # Also check TRDIR for CM includes
    print(f"\n=== TRDIR CM includes for {cls} ===")
    try:
        r2 = conn.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR", DELIMITER="|",
                       OPTIONS=[{"TEXT": f"NAME LIKE '{cls[:28]}%'"}],
                       FIELDS=[{"FIELDNAME":"NAME"},{"FIELDNAME":"SUBC"}],
                       ROWCOUNT=50)
        for row in r2.get("DATA", []):
            print(f"  {row['WA'].strip()}")
        if not r2.get("DATA"):
            print("  (none found)")
    except Exception as e:
        print(f"  Error: {e}")

conn.close()
