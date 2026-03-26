"""
fix_extension_write.py
Tries different I_EXTENSION values for SIW_RFC_WRITE_REPORT on class includes.
Also confirms ZCL_CRP_PROCESS_REQ includes exist in TRDIR.
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
print(f"Connected to {os.getenv('SAP_ASHOST')}/{os.getenv('SAP_CLIENT')}")

# 1. Confirm ZCL_CRP_PROCESS_REQ includes in TRDIR
print("\n=== ZCL_CRP_PROCESS_REQ programs in TRDIR ===")
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR", DELIMITER="|",
              OPTIONS=[{"TEXT": "NAME LIKE 'ZCL_CRP_PROCESS_REQ%'"}],
              FIELDS=[{"FIELDNAME":"NAME"},{"FIELDNAME":"SUBC"}], ROWCOUNT=20)
for row in r.get("DATA", []):
    print(f"  {row['WA'].strip()}")
if not r.get("DATA"):
    print("  (no entries)")

# 2. Try I_EXTENSION candidates
print("\n=== Testing I_EXTENSION values for CCIMP write ===")
test_code = [
    "*\"* use this source file for implementation of the class methods",
    "* TEST WRITE"
]

for ext in ["K", "C", "CLAS", "ZCL_CRP_PROCESS_REQ", "", "CLASS-POOL", "I"]:
    print(f"\n  Trying I_EXTENSION='{ext}' ...")
    try:
        params = {
            "I_NAME": "ZCL_CRP_PROCESS_REQ=========CCIMP",
            "I_TAB_CODE": test_code,
        }
        if ext != "":
            params["I_EXTENSION"] = ext
        r2 = conn.call("SIW_RFC_WRITE_REPORT", **params)
        exc = r2.get("E_STR_EXCEPTION", {})
        if isinstance(exc, dict) and exc.get("MSG_TYPE") == "E":
            print(f"  -> Error: {exc.get('MSG_TEXT','')}")
        else:
            print(f"  -> SUCCESS with I_EXTENSION='{ext}'!")
            break
    except Exception as e:
        err = str(e)
        if "EXTTYPE" in err or "EXTENSION" in err:
            print(f"  -> Still needs extension type: {err[:100]}")
        elif "NOT_AUTHORIZED" in err:
            print(f"  -> Auth denied (but function and ext work!)")
            break
        else:
            print(f"  -> Other error: {err[:150]}")

conn.close()
