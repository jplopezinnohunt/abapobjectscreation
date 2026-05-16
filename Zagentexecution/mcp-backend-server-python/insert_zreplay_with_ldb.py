"""
Re-create ZSAPFPAYM_REPLAY with LDBNAME='FPMF' assigned, using the ABAP
statement `INSERT REPORT ... DIRECTORY ENTRY trdir` via RFC_ABAP_INSTALL_AND_RUN.

This is the ONLY way to pre-populate TRDIR.LDBNAME because:
  - RPY_PROGRAM_INSERT does not expose LDBNAME parameter (verified)
  - UPDATE TRDIR direct fails silently (auth check)
  - INSERT REPORT ... DIRECTORY ENTRY accepts a fully-populated TRDIR row
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

# Read the driver source (23 lines)
PKG = os.path.join(os.path.dirname(__file__), "..", "..",
                   "extracted_code", "FI", "SAPFPAYM", "ZSAPFPAYM_REPLAY")
with open(os.path.join(PKG, "ZSAPFPAYM_REPLAY.abap"), encoding="utf-8") as f:
    src_lines = f.read().splitlines()

# Build the one-shot installer
abap = []
abap.append("REPORT zfix_install_zreplay.")
abap.append("DATA: lt_src TYPE STANDARD TABLE OF string,")
abap.append("      ls_trdir TYPE trdir.")
abap.append("")
# Append each source line. Use ` (backtick) to avoid quote-escape hell.
for line in src_lines:
    # Escape backticks in the source if any (unlikely)
    safe = line.replace("`", "''")
    abap.append(f"APPEND `{safe}` TO lt_src.")
abap.append("")
abap.append("ls_trdir-name    = 'ZSAPFPAYM_REPLAY'.")
abap.append("ls_trdir-subc    = '1'.        \" 1 = REPORT")
abap.append("ls_trdir-ldbname = 'FPMF'.     \" the logical database")
abap.append("ls_trdir-appl    = 'F'.        \" Finance application")
abap.append("ls_trdir-cnam    = sy-uname.")
abap.append("ls_trdir-cdat    = sy-datum.")
abap.append("ls_trdir-uprog   = ' '.")
abap.append("ls_trdir-rstat   = 'P'.        \" P = customer/customer-modified")
abap.append("ls_trdir-rmand   = sy-mandt.")
abap.append("ls_trdir-fixpt   = 'X'.        \" fixed point arithmetic")
abap.append("")
abap.append("INSERT REPORT 'ZSAPFPAYM_REPLAY' FROM lt_src DIRECTORY ENTRY ls_trdir.")
abap.append("WRITE: / 'INSERT REPORT sy-subrc =', sy-subrc.")
abap.append("COMMIT WORK.")
abap.append("")
abap.append("\" Verify")
abap.append("DATA: ls_check TYPE trdir.")
abap.append("SELECT SINGLE * FROM trdir INTO ls_check WHERE name = 'ZSAPFPAYM_REPLAY'.")
abap.append("WRITE: / 'AFTER NAME    =', ls_check-name.")
abap.append("WRITE: / 'AFTER SUBC    =', ls_check-subc.")
abap.append("WRITE: / 'AFTER LDBNAME =', ls_check-ldbname.")
abap.append("WRITE: / 'AFTER APPL    =', ls_check-appl.")

print(f"=== ABAP installer ({len(abap)} lines, src={len(src_lines)} lines) ===")
print("First 5 lines:")
for l in abap[:5]: print("  ", l)
print("... (source lines as APPEND `...` TO lt_src.) ...")
print("Last 12 lines:")
for l in abap[-12:]: print("  ", l)

print("\n=== Execute via RFC_ABAP_INSTALL_AND_RUN ===")
try:
    r = c.call("RFC_ABAP_INSTALL_AND_RUN",
               MODE='F',
               PROGRAMNAME='ZFIX_INSTALL_ZREPLAY',
               PROGRAM=[{"LINE": l} for l in abap])
    print("\n--- WRITES ---")
    for w in (r.get("WRITES") or []):
        txt = w.get("ZEILE") or w.get("LINE") if isinstance(w, dict) else str(w)
        print(f"  {txt}")
    errs = r.get("ERRORS") or []
    if errs:
        print("--- ERRORS ---")
        for e in errs:
            txt = e.get("ZEILE") or e.get("LINE") or str(e) if isinstance(e, dict) else str(e)
            print(f"  {txt}")
except Exception as e:
    print(f"  FAIL: {e}")

# Independent verify via RFC_READ_TABLE
print("\n=== Independent TRDIR verify (RFC_READ_TABLE) ===")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR",
           OPTIONS=[{"TEXT": "NAME = 'ZSAPFPAYM_REPLAY'"}],
           FIELDS=[{"FIELDNAME":"NAME"},{"FIELDNAME":"SUBC"},
                   {"FIELDNAME":"LDBNAME"},{"FIELDNAME":"APPL"},
                   {"FIELDNAME":"CNAM"}],
           DELIMITER='|')
rows = r.get("DATA", [])
if not rows:
    print("  ZSAPFPAYM_REPLAY NOT IN TRDIR — INSERT failed")
for row in rows:
    p = [x.strip() for x in row['WA'].split('|')]
    print(f"  NAME={p[0]} SUBC={p[1]} LDBNAME={p[2]} APPL={p[3]} CNAM={p[4]}")
