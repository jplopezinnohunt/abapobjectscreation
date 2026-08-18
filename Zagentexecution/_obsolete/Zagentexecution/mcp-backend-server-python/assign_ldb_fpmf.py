"""
Assign LDB FPMF + APPL='F' to ZSAPFPAYM_REPLAY in D01 TRDIR.
Uses RFC_ABAP_INSTALL_AND_RUN to execute a one-shot ABAP UPDATE.

Why: RPY_PROGRAM_INSERT/UPDATE in this release does not expose LDBNAME or
APPLICATION as parameters (verified earlier with USER_PROGRAM rejection).
TRDIR is the program-attribute table; updating LDBNAME there wires the
report to LDB FPMF so PM_LAUFD/PM_LAUFI/PM_XVORL/PM_GRPNO selection
parameters and GET FPAYH / GET FPAYP nodes resolve.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

# One-shot ABAP that updates TRDIR for ZSAPFPAYM_REPLAY
# RFC_ABAP_INSTALL_AND_RUN takes a PROGRAM table (each row = 1 ABAP line)
abap_lines = [
"REPORT zfix_trdir_ldb.",
"DATA: lv_count TYPE i.",
"UPDATE trdir SET ldbname = 'FPMF'",
"                 appl    = 'F'",
"           WHERE name = 'ZSAPFPAYM_REPLAY'.",
"lv_count = sy-dbcnt.",
"WRITE: / 'TRDIR rows updated:', lv_count.",
"COMMIT WORK.",
"",
"* Verify",
"DATA: ls_trdir TYPE trdir.",
"SELECT SINGLE * FROM trdir INTO ls_trdir WHERE name = 'ZSAPFPAYM_REPLAY'.",
"WRITE: / 'NAME =', ls_trdir-name,",
"       / 'SUBC =', ls_trdir-subc,",
"       / 'LDBNAME =', ls_trdir-ldbname,",
"       / 'APPL =', ls_trdir-appl,",
"       / 'CNAM =', ls_trdir-cnam.",
]

program_table = [{"LINE": l} for l in abap_lines]

print("=== Running ABAP one-shot to UPDATE TRDIR.LDBNAME ===")
print("--- ABAP source ---")
for i, l in enumerate(abap_lines, 1):
    print(f"  {i:2}  {l}")
print("---")

try:
    r = c.call("RFC_ABAP_INSTALL_AND_RUN",
               MODE='F',                # F = run + free (don't store)
               PROGRAMNAME='ZFIX_TRDIR_LDB',
               PROGRAM=program_table)
    print("\n--- WRITES (ABAP output) ---")
    writes = r.get("WRITES") or []
    for line in writes:
        if isinstance(line, dict):
            txt = line.get("LINE") or line.get("TEXT") or str(line)
            print(f"  {txt}")
        else:
            print(f"  {line}")
    errors = r.get("ERRORS") or []
    if errors:
        print("\n--- ERRORS ---")
        for e in errors:
            print(f"  {e}")
except Exception as e:
    print(f"\nFAIL: {e}")
