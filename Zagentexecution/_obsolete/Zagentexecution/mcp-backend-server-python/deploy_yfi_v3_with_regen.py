"""Deploy Y_FI_DMEE_ADR v3 (REFERENCE interface fix) + regenerate function group."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")
SRC_FILE = os.path.join(os.path.dirname(__file__), "..", "..",
    "extracted_code/FI/DMEE_full_inventory/Y_FI_DMEE_ADR_v3.abap")
INCLUDE = "LYFPAYMU19"

with open(SRC_FILE, encoding="utf-8") as f:
    src_lines = f.read().splitlines()
print(f"Source: {len(src_lines)} lines from v3")
# Verify REFERENCE is in source
ref_count = sum(1 for l in src_lines if "REFERENCE(I_EXTENSION)" in l.upper())
val_count = sum(1 for l in src_lines if "VALUE(I_EXTENSION)" in l.upper())
print(f"  has REFERENCE(I_EXTENSION): {ref_count}, VALUE(I_EXTENSION): {val_count}")
if ref_count != 1 or val_count != 0:
    print("  ABORT — fix not applied locally"); sys.exit(1)

CHUNK = 45
def emit(line):
    safe = line.replace("`", "")
    if not safe: return ["APPEND `` TO lt_src."]
    if len(safe) + 22 <= 72: return [f"APPEND `{safe}` TO lt_src."]
    chunks = [safe[i:i+CHUNK] for i in range(0, len(safe), CHUNK)]
    out = []
    for i, ch in enumerate(chunks):
        if i == 0: out.append(f"APPEND `{ch}` &&")
        elif i < len(chunks)-1: out.append(f"       `{ch}` &&")
        else: out.append(f"       `{ch}` TO lt_src.")
    return out

abap = ["REPORT zfix_yfi3.",
        "DATA: lt_src TYPE STANDARD TABLE OF string,",
        "      ls_trdir TYPE trdir,",
        "      lv_msg TYPE string,",
        "      lv_n   TYPE i."]
for ln in src_lines: abap.extend(emit(ln))
abap += [
    f"SELECT SINGLE * FROM trdir INTO ls_trdir",
    f"  WHERE name = '{INCLUDE}'.",
    f"INSERT REPORT '{INCLUDE}' FROM lt_src",
    f"  DIRECTORY ENTRY ls_trdir.",
    "WRITE: / 'INSERT rc=', sy-subrc.",
    "COMMIT WORK.",
    "* CRITICAL: regenerate function group to refresh FUPARAREF",
    "GENERATE REPORT 'SAPLYFPAYM' MESSAGE lv_msg.",
    "WRITE: / 'GENERATE rc=', sy-subrc, 'msg:', lv_msg.",
    "COMMIT WORK.",
    "* Verify FUPARAREF",
    "SELECT COUNT(*) FROM fupararef INTO lv_n",
    "  WHERE funcname = 'Y_FI_DMEE_ADR'.",
    "WRITE: / 'FUPARAREF count=', lv_n.",
    "WRITE: / 'Deploy + regenerate OK'.",
]
overlong = [(i+1,l) for i,l in enumerate(abap) if len(l) > 72]
if overlong:
    print(f"WARN {len(overlong)} >72:"); [print(f"  {i}({len(l)}): {l}") for i,l in overlong[:3]]
    sys.exit(1)
print(f"installer: {len(abap)} lines, all ≤72")

r = c.call("RFC_ABAP_INSTALL_AND_RUN", MODE='F', PROGRAMNAME='ZFIX_YFI3',
           PROGRAM=[{"LINE": l} for l in abap])
if r.get("ERRORMESSAGE"): print(f"ERR: {r.get('ERRORMESSAGE')}")
print("--- WRITES ---")
for w in (r.get("WRITES") or []):
    print(" ", w.get("ZEILE"))
