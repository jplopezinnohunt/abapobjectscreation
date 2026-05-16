"""Extract source of FM FI_CGI_DMEE_EXIT_W_BADI to trace exact data sources used.
Goal: determine 100% which fields the FM reads + dispatch logic, to enable mapping without EXIT.
"""
import os, sys
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
prefix = "SAP_D01_"
def env(k, d=None): return os.getenv(prefix+k) or os.getenv("SAP_"+k) or d

params = dict(ashost=env("ASHOST"), sysnr=env("SYSNR"), client=env("CLIENT"),
              user=env("USER"), lang=env("LANG","EN"))
pw = env("PASSWD") or env("PASSWORD")
if pw: params["passwd"]=pw
if env("SNC_MODE") == "1":
    params["snc_mode"] = "1"
    params["snc_partnername"] = env("SNC_PARTNERNAME")
    params["snc_qop"] = env("SNC_QOP", "9")

conn = Connection(**params)
print("Connected D01")

FM = "FI_CGI_DMEE_EXIT_W_BADI"

# Step 1: Find function group + include via TFDIR
print(f"\n=== TFDIR lookup for {FM} ===")
r = conn.call("RFC_READ_TABLE",
    QUERY_TABLE="TFDIR",
    OPTIONS=[{"TEXT": f"FUNCNAME = '{FM}'"}],
    FIELDS=[{"FIELDNAME":"FUNCNAME"},{"FIELDNAME":"PNAME"},{"FIELDNAME":"INCLUDE"},
            {"FIELDNAME":"FMODE"},{"FIELDNAME":"INFO"}],
    DELIMITER="|", ROWCOUNT=10)
for d in r.get("DATA",[]):
    print(" ", d["WA"])
    parts = d["WA"].split("|")
    pname = parts[1].strip()
    inc_num = parts[2].strip()
    print(f"  Function group/program: {pname}, INCLUDE number: {inc_num}")

# Step 2: Read FM source via RPY_FUNCTIONMODULE_READ
print(f"\n=== RPY_FUNCTIONMODULE_READ_NEW {FM} ===")
try:
    r = conn.call("RPY_FUNCTIONMODULE_READ_NEW", FUNCTIONNAME=FM)
    print("Function exists. Documentation:")
    for k in ["FUNCNAME","GROUPNAME","SHORT_TEXT"]:
        print(f"  {k}: {r.get(k,'')}")
    src_lines = r.get("SOURCE", [])
    print(f"Source lines: {len(src_lines)}")
    print("\n--- FULL SOURCE ---")
    for i, line in enumerate(src_lines):
        print(f"{i+1:4d}: {line}")
except Exception as e:
    print(f"RPY_FUNCTIONMODULE_READ_NEW failed: {e}")

    # Fallback: try RPY_FUNCTIONMODULE_READ (older variant)
    print(f"\n=== Fallback: RPY_FUNCTIONMODULE_READ {FM} ===")
    try:
        r = conn.call("RPY_FUNCTIONMODULE_READ", FUNCTIONNAME=FM)
        src = r.get("FUNCTION_INCLUDE", [])
        for i, line in enumerate(src):
            print(f"{i+1:4d}: {line}")
    except Exception as e2:
        print(f"Also failed: {e2}")
