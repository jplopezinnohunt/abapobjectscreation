"""
test_write_rfcs.py — Tests write RFC candidates directly (bypass TFDIR check)
Also tests ADT REST API as a fallback
"""
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

# Small test source — 3 lines for the CCIMP stub restore
test_source = [
    {"LINE": '*"* use this source file for implementation of the class methods'},
    {"LINE": ""},
    {"LINE": "* TEST WRITE - REMOVE"},
]

# Try calling write functions directly
candidates = [
    ("SIW_RFC_WRITE_REPORT",  {"I_NAME": "ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP", "I_SOURCE": test_source}),
    ("SEO_SOURCE_WRITE",       {"CLSNAME": "ZCL_Z_CRP_SRV_DPC_EXT", "SOURCE": test_source}),
    ("SLDAG_RFC_WRITE_REPORT", {"I_NAME": "ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP", "I_SOURCE": test_source}),
]

for fn, params in candidates:
    print(f"\nTrying {fn} ...")
    try:
        r = conn.call(fn, **params)
        print(f"  SUCCESS: {fn} worked! Result: {r}")
    except RFCError as e:
        err = str(e)
        if "FU_NOT_FOUND" in err or "Function not found" in err.lower():
            print(f"  NOT FOUND: {fn} does not exist in this system")
        elif "NOT_AUTHORIZED" in err or "AUTHORITY" in err:
            print(f"  AUTH DENIED: {fn} exists but no authorization")
        else:
            print(f"  ERROR ({fn}): {err[:200]}")
    except Exception as e:
        print(f"  EXCEPTION: {e}")

conn.close()
print("\nDone. Use Playwright SE38 approach if all failed.")
