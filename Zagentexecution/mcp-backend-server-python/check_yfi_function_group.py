"""Find function group + include of Y_FI_DMEE_ADR so we can deploy the extension."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

print("=== TFDIR for Y_FI_DMEE_ADR ===")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="TFDIR",
           OPTIONS=[{"TEXT": "FUNCNAME = 'Y_FI_DMEE_ADR'"}],
           FIELDS=[{"FIELDNAME":"FUNCNAME"},{"FIELDNAME":"PNAME"},
                   {"FIELDNAME":"INCLUDE"},{"FIELDNAME":"FMODE"}],
           DELIMITER='|')
for row in r.get("DATA", []):
    parts = [x.strip() for x in row['WA'].split('|')]
    print(f"  FUNCNAME = {parts[0]}")
    print(f"  PNAME    = {parts[1]}    (function group main program)")
    print(f"  INCLUDE  = {parts[2]}    (include number, e.g. 01 = U01)")
    print(f"  FMODE    = {parts[3]}")

# Get the function group source structure
# Y_FI_DMEE_ADR is in pname=SAPLY_FI_DMEE_ADR or similar; FM source in LY_FI_DMEE_ADRU01
print("\n=== Read current FM source ===")
try:
    r2 = c.call("RPY_FUNCTIONMODULE_READ_NEW", FUNCTIONNAME="Y_FI_DMEE_ADR")
    src_tab = r2.get("SOURCE") or []
    print(f"  source lines: {len(src_tab)}")
    print("  --- full source ---")
    for i, row in enumerate(src_tab, 1):
        l = row.get("LINE","") if isinstance(row, dict) else str(row)
        print(f"  {i:3} {l}")
except Exception as e:
    print(f"  ERR: {e}")
