"""Extract FI_FILL_FPAYHX + its function group so we can see how it dispatches per format
and how it populates REF01 for /CGI_XML_CT_UNESCO.

Goal: answer 'how does FI_FILL_FPAYHX feed FPAYHX-REF01 for /CGI_XML_CT_UNESCO?'

Outputs:
  - knowledge/domains/Payment/phase0/fi_fill_fpayhx_source.txt (full FM source)
  - knowledge/domains/Payment/phase0/fi_fill_fpayhx_group_includes.txt (FG include list)
"""
import os, sys, pathlib
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

OUT_DIR = pathlib.Path(__file__).resolve().parents[2] / "knowledge" / "domains" / "Payment" / "phase0"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FM = "FI_FILL_FPAYHX"

# Step 1: TFDIR is not RFC_READ_TABLE-able on this system; skip and go straight to RPY
pname = None

# Step 2: read FM source via RPY_FUNCTIONMODULE_READ_NEW
print(f"\n=== RPY_FUNCTIONMODULE_READ_NEW {FM} ===")
src_text = None
try:
    r = conn.call("RPY_FUNCTIONMODULE_READ_NEW", FUNCTIONNAME=FM)
    for k in ["FUNCNAME","GROUPNAME","SHORT_TEXT","NAMESPACE","DEVCLASS"]:
        print(f"  {k}: {r.get(k,'')}")
    src_lines = r.get("SOURCE", [])
    print(f"Source lines: {len(src_lines)}")
    src_text = "\n".join(l for l in src_lines)
    fm_path = OUT_DIR / "fi_fill_fpayhx_source.txt"
    fm_path.write_text(src_text, encoding="utf-8")
    print(f"Wrote {fm_path}")
except Exception as e:
    print(f"RPY_FUNCTIONMODULE_READ_NEW failed: {e}")

# Step 3: enumerate includes in the FG (so we know all source files in the FG)
if pname:
    print(f"\n=== TRDIR / D010INC for function group {pname} ===")
    # Use READREPORT or TADIR
    try:
        r = conn.call("RFC_READ_TABLE",
            QUERY_TABLE="TADIR",
            OPTIONS=[{"TEXT": f"PGMID = 'R3TR' AND OBJECT = 'FUGR' AND OBJ_NAME = '{pname[1:] if pname.startswith('S') else pname}'"}],
            FIELDS=[{"FIELDNAME":"OBJ_NAME"},{"FIELDNAME":"DEVCLASS"}],
            DELIMITER="|", ROWCOUNT=5)
        for d in r.get("DATA",[]):
            print(" tadir:", d["WA"])
    except Exception as e:
        print(f"TADIR lookup failed: {e}")

    # List all functions in this group
    print(f"\n=== TFDIR functions in group {pname} ===")
    try:
        r = conn.call("RFC_READ_TABLE",
            QUERY_TABLE="TFDIR",
            OPTIONS=[{"TEXT": f"PNAME = '{pname}'"}],
            FIELDS=[{"FIELDNAME":"FUNCNAME"},{"FIELDNAME":"INCLUDE"},{"FIELDNAME":"FMODE"}],
            DELIMITER="|", ROWCOUNT=200)
        for d in r.get("DATA",[]):
            print(" ", d["WA"])
    except Exception as e:
        print(f"TFDIR group lookup failed: {e}")
