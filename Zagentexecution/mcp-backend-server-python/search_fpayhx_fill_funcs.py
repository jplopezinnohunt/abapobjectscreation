"""Search D01 for any FM whose name suggests it fills FPAYHX (FI_FILL_*, *FPAYHX*).
Also list all FMs in function group FPAYM* / FBPM* / FBSEPA* / SAPFPAYM source area.
"""
import os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
prefix = "SAP_D01_"
def env(k, d=None): return os.getenv(prefix+k) or os.getenv("SAP_"+k) or d

params = dict(ashost=env("ASHOST"), sysnr=env("SYSNR"), client=env("CLIENT"),
              user=env("USER"), lang=env("LANG","EN"))
pw = env("PASSWD") or env("PASSWORD")
if pw: params["passwd"]=pw

conn = Connection(**params)

# Try various candidates by directly probing RPY_FUNCTIONMODULE_READ_NEW
candidates = [
    "FI_FILL_FPAYHX",
    "FI_PAYMEDIUM_FILL_FPAYHX",
    "FI_PAYM_FILL_FPAYHX",
    "FI_PAYMEDIUM_FILL_REF_FIELDS",
    "FI_PAYMEDIUM_FREF_FILL",
    "FI_PAYMEDIUM_FREF",
    "FI_FILL_FREF",
    "FI_FILL_PAYM_FPAYHX",
    "FI_FPAYHX_FREF_FILL",
    "FI_PAYMEDIUM_DMEE_FILL_FPAYHX",
    "FI_FILL_PAYMEDIUM_FPAYHX",
]
for fm in candidates:
    try:
        r = conn.call("RPY_FUNCTIONMODULE_READ_NEW", FUNCTIONNAME=fm)
        src = r.get("SOURCE", [])
        g = r.get("GROUPNAME","")
        t = r.get("SHORT_TEXT","")
        if src or g:
            print(f"FOUND {fm}: group={g} lines={len(src)} text='{t}'")
        else:
            print(f"  empty {fm}")
    except Exception as e:
        msg = str(e)[:120]
        print(f"  err {fm}: {msg}")
