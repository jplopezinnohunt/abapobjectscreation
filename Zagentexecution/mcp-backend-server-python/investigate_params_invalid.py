"""Extract LFPAYGU02 to find which exact parameter triggered PARAMETERS_INVALID."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

# Extract LFPAYGU02 (the include where FI_PAYM_PARAMETERS_PUT lives)
print("=== Extract LFPAYGU02 ===")
r = c.call("RPY_PROGRAM_READ", PROGRAM_NAME="LFPAYGU02",
           WITH_INCLUDELIST='X', WITH_LOWERCASE='X')
src_tab = r.get("SOURCE_EXTENDED") or []
lines = [row.get("LINE","") for row in src_tab]
print(f"  {len(lines)} lines")

# Save and grep for PARAMETERS_INVALID raises
out_path = os.path.join(os.path.dirname(__file__), "..", "..",
                       "extracted_code/FI/SAPFPAYM/LFPAYGU02.abap")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"  saved {out_path}")

# Find context around PARAMETERS_INVALID raises
print("\n=== Lines that RAISE PARAMETERS_INVALID ===")
for i, line in enumerate(lines, 1):
    if "PARAMETERS_INVALID" in line.upper():
        # Print a window around it (5 lines before, 2 after)
        start = max(0, i-6)
        end = min(len(lines), i+2)
        print(f"\n  --- Around line {i} ---")
        for j in range(start, end):
            marker = ">>>" if j+1 == i else "   "
            print(f"  {marker} {j+1:4} {lines[j][:100]}")
