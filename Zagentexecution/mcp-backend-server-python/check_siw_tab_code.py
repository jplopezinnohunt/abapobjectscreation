"""
check_siw_tab_code.py — Discovers SIW_TAB_CODE structure field name
and tests the correct write call format
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
        p["snc_mode"] = "1"; p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = os.getenv("SAP_SNC_QOP","9")
    return Connection(**p)

conn = get_conn()

# 1. Read DD03L to find SIW_TAB_CODE fields
print("=== SIW_TAB_CODE structure (DD03L) ===")
try:
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD03L", DELIMITER="|",
                  OPTIONS=[{"TEXT": "TABNAME = 'SIW_TAB_CODE'"}],
                  FIELDS=[{"FIELDNAME":"FIELDNAME"},{"FIELDNAME":"ROLLNAME"},{"FIELDNAME":"LENG"}],
                  ROWCOUNT=10)
    for row in r.get("DATA", []):
        print(f"  {row['WA']}")
    if not r.get("DATA"):
        print("  (empty - table not readable)")
except Exception as e:
    print(f"  Error: {e}")

# 2. Try the actual read call and inspect what field name comes back
print("\n=== Reading CCIMP to see actual field name in E_TAB_CODE ===")
try:
    r2 = conn.call("SIW_RFC_READ_REPORT", I_NAME="ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP")
    lines = r2.get("E_TAB_CODE", [])
    if lines:
        first = lines[0]
        print(f"  Type of first element: {type(first)}")
        if isinstance(first, dict):
            print(f"  Keys: {list(first.keys())}")
            print(f"  Content: {first}")
        else:
            print(f"  Raw: {first}")
    else:
        print("  (empty)")
except Exception as e:
    print(f"  Error: {e}")

# 3. Test write with each candidate field name
print("\n=== Testing write with candidate field names ===")
test_line = "*test write line"
for field_name in ["LINE", "TEXT", "CODE", "ABAP_SOURCE", "SOURCE", "CODELINE"]:
    try:
        tab = [{field_name: test_line}]
        conn.call("SIW_RFC_WRITE_REPORT",
                  I_NAME="ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP",
                  I_TAB_CODE=tab)
        print(f"  SUCCESS with field '{field_name}'!")
        break
    except Exception as e:
        err = str(e)
        if "field" in err.lower() and "not found" in err.lower():
            print(f"  '{field_name}': field not found")
        else:
            print(f"  '{field_name}': OTHER error: {err[:120]}")

conn.close()
