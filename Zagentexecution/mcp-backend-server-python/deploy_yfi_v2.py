"""
Deploy Y_FI_DMEE_ADR v2 to D01 by replacing the include LYFPAYMU19
(which holds the FUNCTION ... ENDFUNCTION block of Y_FI_DMEE_ADR).

Strategy:
  1) Read current LYFPAYMU19 source for backup verification
  2) Replace with v2 source from local file
  3) INSERT REPORT 'LYFPAYMU19' DIRECTORY ENTRY (preserve type='I')
  4) Verify FM still exists + new source is active
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

INCLUDE = "LYFPAYMU19"
LOCAL_V2 = os.path.join(os.path.dirname(__file__), "..", "..",
                       "extracted_code/FI/DMEE_full_inventory/Y_FI_DMEE_ADR_v2.abap")

print(f"=== 1. Read current {INCLUDE} from D01 ===")
r = c.call("RPY_PROGRAM_READ", PROGRAM_NAME=INCLUDE,
           WITH_INCLUDELIST='X', WITH_LOWERCASE='X')
src_tab = r.get("SOURCE_EXTENDED") or r.get("SOURCE") or []
current_lines = [row.get("LINE","") if isinstance(row,dict) else str(row) for row in src_tab]
print(f"  current source: {len(current_lines)} lines")
print(f"  first line: {current_lines[0] if current_lines else '(empty)'}")
print(f"  last line:  {current_lines[-1] if current_lines else '(empty)'}")

# Save current as backup
backup_path = os.path.join(os.path.dirname(__file__), "..", "..",
                          f"extracted_code/FI/DMEE_full_inventory/{INCLUDE}_v1_backup.abap")
with open(backup_path, "w", encoding="utf-8") as f:
    f.write("\n".join(current_lines))
print(f"  backup saved: {backup_path}")

print(f"\n=== 2. Read v2 from local ===")
with open(LOCAL_V2, encoding="utf-8") as f:
    v2_lines = f.read().splitlines()
print(f"  v2 source: {len(v2_lines)} lines")

print(f"\n=== 3. Read current TRDIR for {INCLUDE} ===")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR",
           OPTIONS=[{"TEXT": f"NAME = '{INCLUDE}'"}],
           FIELDS=[{"FIELDNAME":"NAME"},{"FIELDNAME":"SUBC"},
                   {"FIELDNAME":"CNAM"},{"FIELDNAME":"APPL"},
                   {"FIELDNAME":"UCCHECK"},{"FIELDNAME":"RLOAD"},
                   {"FIELDNAME":"VARCL"},{"FIELDNAME":"FIXPT"}],
           DELIMITER='|')
for row in r.get("DATA", []):
    print(f"  {row['WA']}")

print(f"\n=== 4. Build ABAP installer (chunked APPEND ≤72 chars) ===")
CHUNK = 45
def emit(line):
    safe = line.replace("`", "")
    if not safe:
        return ["APPEND `` TO lt_src."]
    if len(safe) + 22 <= 72:
        return [f"APPEND `{safe}` TO lt_src."]
    chunks = [safe[i:i+CHUNK] for i in range(0, len(safe), CHUNK)]
    out = []
    for idx, ch in enumerate(chunks):
        if idx == 0: out.append(f"APPEND `{ch}` &&")
        elif idx < len(chunks)-1: out.append(f"       `{ch}` &&")
        else: out.append(f"       `{ch}` TO lt_src.")
    return out

abap = ["REPORT zfix_yfiadr.",
        "DATA: lt_src TYPE STANDARD TABLE OF string,",
        "      ls_trdir TYPE trdir."]
for ln in v2_lines: abap.extend(emit(ln))

# Read current TRDIR attrs and preserve them
abap += [
    f"SELECT SINGLE * FROM trdir INTO ls_trdir",
    f"  WHERE name = '{INCLUDE}'.",
    f"INSERT REPORT '{INCLUDE}'",
    f"  FROM lt_src DIRECTORY ENTRY ls_trdir.",
    "WRITE: / 'INSERT sy-subrc=', sy-subrc.",
    "COMMIT WORK.",
    "* Verify FM still readable",
    "DATA: ls_chk TYPE trdir.",
    "SELECT SINGLE * FROM trdir INTO ls_chk",
    f"  WHERE name = '{INCLUDE}'.",
    "WRITE: / 'After: SUBC=', ls_chk-subc, 'UCCHECK=', ls_chk-uccheck.",
]

overlong = [(i+1,l) for i,l in enumerate(abap) if len(l) > 72]
if overlong:
    print(f"  WARN {len(overlong)} lines >72:")
    for i,l in overlong[:3]: print(f"    {i}({len(l)}): {l}")
    sys.exit(1)
print(f"  installer: {len(abap)} lines, all ≤72")

print(f"\n=== 5. Execute via RFC_ABAP_INSTALL_AND_RUN ===")
try:
    r = c.call("RFC_ABAP_INSTALL_AND_RUN", MODE='F',
               PROGRAMNAME='ZFIX_YFIADR',
               PROGRAM=[{"LINE": l} for l in abap])
    if r.get("ERRORMESSAGE"): print(f"  ERR: {r.get('ERRORMESSAGE')}")
    for w in (r.get("WRITES") or []):
        txt = w.get("ZEILE") if isinstance(w, dict) else str(w)
        print(f"  {txt}")
except Exception as e:
    print(f"  FAIL: {e}")

print(f"\n=== 6. Re-read FM source to confirm new version is active ===")
try:
    r2 = c.call("RPY_FUNCTIONMODULE_READ_NEW", FUNCTIONNAME="Y_FI_DMEE_ADR")
    src_tab2 = r2.get("SOURCE") or []
    new_lines = [row.get("LINE","") if isinstance(row,dict) else str(row) for row in src_tab2]
    has_country = any("ls_adrc-country" in l for l in new_lines)
    has_region  = any("ls_adrc-region"  in l for l in new_lines)
    has_name1   = any("ls_adrc-name1"   in l for l in new_lines)
    print(f"  Lines: {len(new_lines)}  has Ctry: {has_country}  has CtrySubDvsn: {has_region}  has Nm: {has_name1}")
    if has_country and has_region and has_name1:
        print("  ✓ V2 ACTIVE — Ctry/CtrySubDvsn/Nm cases present")
    else:
        print("  ! V2 not fully active")
except Exception as e:
    print(f"  ERR: {e}")
