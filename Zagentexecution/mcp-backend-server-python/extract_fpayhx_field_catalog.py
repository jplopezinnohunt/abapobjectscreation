"""
Extract FPAYHX field catalog from D01 via DDIF_FIELDINFO_GET RFC.
Goal: confirm AUSTO/AUST1/AUST2/AUST3/ZPFST/ZPLOR/ZLISO exist + their lengths
before binding V001 SEPA Dbtr structured leaves.
"""
import os, csv
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
prefix = "SAP_D01_"
def env(k, d=None):
    return os.getenv(prefix + k) or os.getenv("SAP_" + k) or d

params = dict(
    ashost=env("ASHOST"), sysnr=env("SYSNR"), client=env("CLIENT"),
    user=env("USER"), lang=env("LANG", "EN"),
)
pw = env("PASSWD") or env("PASSWORD")
if pw: params["passwd"] = pw
if env("SNC_MODE") == "1":
    params["snc_mode"] = "1"
    params["snc_partnername"] = env("SNC_PARTNERNAME")
    params["snc_qop"] = env("SNC_QOP", "9")

conn = Connection(**params)
result = conn.call("DDIF_FIELDINFO_GET", TABNAME="FPAYHX", LANGU="E")

fields = result.get("DFIES_TAB", [])
print(f"FPAYHX total fields: {len(fields)}")

interest = ["AUSTO","AUST1","AUST2","AUST3","ZPFST","ZPLOR","ZLISO","LDISO",
            "ORT1Z","ZSTRA","ZBSTR","ZBORT","ZBPST","REF01","REF06","ZPSTL"]

print("\n=== Fields of interest ===")
print(f"{'FIELDNAME':15s} {'INTTYPE':5s} {'LENG':6s} {'DECIMALS':8s} {'DOMNAME':20s} {'FIELDTEXT':40s}")
out = []
for f in fields:
    fn = f.get("FIELDNAME","")
    if fn in interest:
        row = (fn, f.get("INTTYPE",""), f.get("LENG",""), f.get("DECIMALS",""),
               f.get("DOMNAME",""), f.get("FIELDTEXT",""))
        print(f"{row[0]:15s} {row[1]:5s} {row[2]:6s} {row[3]:8s} {row[4]:20s} {row[5][:40]}")
        out.append(row)

# Also dump ALL FPAYHX fields to CSV for full traceability
csv_path = os.path.join(os.path.dirname(__file__), "..", "output", "fpayhx_field_catalog_d01.csv")
os.makedirs(os.path.dirname(csv_path), exist_ok=True)
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["FIELDNAME","INTTYPE","LENG","DECIMALS","DOMNAME","ROLLNAME","FIELDTEXT"])
    for fld in fields:
        w.writerow([fld.get("FIELDNAME",""), fld.get("INTTYPE",""), fld.get("LENG",""),
                    fld.get("DECIMALS",""), fld.get("DOMNAME",""), fld.get("ROLLNAME",""),
                    fld.get("FIELDTEXT","")])
print(f"\nFull catalog written: {csv_path}")
print(f"Found {len(out)} of {len(interest)} fields of interest in FPAYHX.")
