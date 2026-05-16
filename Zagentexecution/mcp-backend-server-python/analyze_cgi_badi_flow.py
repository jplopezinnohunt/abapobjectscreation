"""Analyze the CGI BAdI flow that fills Cdtr address today."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")
OUT = os.path.join(os.path.dirname(__file__), "..", "..",
                   "extracted_code/FI/DMEE_full_inventory")
os.makedirs(OUT, exist_ok=True)

print("=== 1) FI_CGI_DMEE_EXIT_W_BADI — entry FM ===")
try:
    r = c.call("RPY_FUNCTIONMODULE_READ_NEW", FUNCTIONNAME="FI_CGI_DMEE_EXIT_W_BADI")
    parts = []
    for tabname in ("IMPORT_PARAMETER","EXPORT_PARAMETER","CHANGING_PARAMETER",
                    "TABLES_PARAMETER","SOURCE","GLOBAL_DATA"):
        tab = r.get(tabname)
        if tab:
            parts.append(f"* === {tabname} ===")
            for row in tab:
                if isinstance(row, dict):
                    parts.append(" | ".join(f"{k}={v}" for k, v in row.items() if v))
                else:
                    parts.append(str(row))
    src = "\n".join(parts)
    out_path = os.path.join(OUT, "FI_CGI_DMEE_EXIT_W_BADI.abap")
    with open(out_path, "w", encoding="utf-8") as f: f.write(src)
    print(f"  Saved: {out_path}")
    # Print SOURCE first 50 lines
    src_tab = r.get("SOURCE") or []
    print(f"  SOURCE lines: {len(src_tab)}")
    print("  --- first 60 lines ---")
    for i, row in enumerate(src_tab[:60], 1):
        l = row.get("LINE","") if isinstance(row, dict) else str(row)
        print(f"  {i:3} {l}")
except Exception as e:
    print(f"  ERR: {e}")

print()
print("=== 2) BAdI Definition FI_CGI_DMEE_EXIT_W_BADI — all methods ===")
try:
    # SXC_EXIT_BADIS gives us BAdI implementation classes
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="SXS_INTER",
               OPTIONS=[{"TEXT": "EXIT_NAME = 'FI_CGI_DMEE_EXIT_W_BADI'"}],
               FIELDS=[{"FIELDNAME":"EXIT_NAME"},{"FIELDNAME":"METHOD"}],
               DELIMITER='|')
    print("  Methods of FI_CGI_DMEE_EXIT_W_BADI BAdI interface:")
    for row in r.get("DATA", []):
        print(f"    {row['WA']}")
except Exception as e:
    print(f"  ERR: {e}")

print()
print("=== 3) Methods of YCL_IDFI_CGI_DMEE_FALLBACK class ===")
try:
    # Read class methods via SEO_METHODS
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="SEOCOMPO",
               OPTIONS=[{"TEXT": "CLSNAME = 'YCL_IDFI_CGI_DMEE_FALLBACK'"}],
               FIELDS=[{"FIELDNAME":"CLSNAME"},{"FIELDNAME":"CMPNAME"},
                       {"FIELDNAME":"CMPTYPE"},{"FIELDNAME":"REFCLSNAME"}],
               ROWCOUNT=80, DELIMITER='|')
    print("  Components of YCL_IDFI_CGI_DMEE_FALLBACK:")
    for row in r.get("DATA", []):
        print(f"    {row['WA']}")
except Exception as e:
    print(f"  ERR: {e}")

print()
print("=== 4) Local files we already have for the CGI BAdI ===")
for fn in os.listdir(OUT):
    if "FALLBACK" in fn or "CGI_DMEE" in fn:
        path = os.path.join(OUT, fn)
        sz = os.path.getsize(path)
        print(f"  {sz:>7}  {fn}")
