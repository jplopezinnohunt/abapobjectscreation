"""Deploy Y_FI_DMEE_ADR v4 (Cdtr+Dbtr context detection via PARENT_ID walk-up)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")
SRC = os.path.join(os.path.dirname(__file__), "..", "..",
    "extracted_code/FI/DMEE_full_inventory/Y_FI_DMEE_ADR_v4.abap")
INCLUDE = "LYFPAYMU19"

with open(SRC, encoding="utf-8") as f:
    src_lines = f.read().splitlines()
print(f"v4 source: {len(src_lines)} lines")

# Sanity: check key markers
for marker in ["lv_grandparent_tech", "WHEN 'Cdtr'", "WHEN 'Dbtr'", "REFERENCE(I_EXTENSION)"]:
    found = sum(1 for l in src_lines if marker in l)
    print(f"  marker '{marker}': {found}")

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

abap = ["REPORT zfix_yfi4.",
        "DATA: lt_src TYPE STANDARD TABLE OF string,",
        "      ls_trdir TYPE trdir,",
        "      lv_msg TYPE string,",
        "      lv_n   TYPE i."]
for ln in src_lines: abap.extend(emit(ln))
abap += [
    f"SELECT SINGLE * FROM trdir INTO ls_trdir WHERE name = '{INCLUDE}'.",
    f"INSERT REPORT '{INCLUDE}' FROM lt_src DIRECTORY ENTRY ls_trdir.",
    "WRITE: / 'INSERT rc=', sy-subrc.",
    "COMMIT WORK.",
    "GENERATE REPORT 'SAPLYFPAYM' MESSAGE lv_msg.",
    "WRITE: / 'GENERATE rc=', sy-subrc, 'msg:', lv_msg.",
    "UPDATE fupararef SET reference = 'X'",
    "  WHERE funcname = 'Y_FI_DMEE_ADR'",
    "    AND parameter = 'I_EXTENSION'.",
    "WRITE: / 'UPDATE fupararef rc=', sy-subrc, 'rows=', sy-dbcnt.",
    "COMMIT WORK.",
    "GENERATE REPORT 'SAPLYFPAYM' MESSAGE lv_msg.",
    "SELECT COUNT(*) FROM fupararef INTO lv_n",
    "  WHERE funcname = 'Y_FI_DMEE_ADR'.",
    "WRITE: / 'FUPARAREF count=', lv_n.",
    "WRITE: / 'Deploy v4 OK'.",
]
overlong = [(i+1,l) for i,l in enumerate(abap) if len(l) > 72]
if overlong:
    print(f"WARN {len(overlong)} >72:")
    for i,l in overlong[:3]: print(f"  {i}({len(l)}): {l}")
    sys.exit(1)
print(f"installer: {len(abap)} lines")

r = c.call("RFC_ABAP_INSTALL_AND_RUN", MODE='F', PROGRAMNAME='ZFIX_YFI4',
           PROGRAM=[{"LINE": l} for l in abap])
if r.get("ERRORMESSAGE"): print(f"ERR: {r.get('ERRORMESSAGE')}")
print("--- WRITES ---")
for w in (r.get("WRITES") or []):
    print(" ", w.get("ZEILE"))
