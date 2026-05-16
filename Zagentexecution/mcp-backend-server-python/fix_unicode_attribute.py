"""
Fix UCCHECK='X' on all 9 ZSAPFPAYM_REPLAY objects (driver + 8 includes).

Strategy: for each object, run an ABAP one-shot that:
  READ REPORT into lt_src
  SELECT trdir
  set uccheck='X', rload='D', varcl='X', appl='F' (where applicable)
  INSERT REPORT FROM lt_src DIRECTORY ENTRY ls_trdir

This UPSERTs the directory attributes without re-shipping the source bytes.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

# All 9 objects + their proper SUBC + LDB
TARGETS = [
    ("ZFPAYM_TOP",       "I", ""),       # include — no LDB needed
    ("ZFPAYM_INI",       "I", ""),
    ("ZFPAYM_SEL",       "I", ""),
    ("ZFPAYM_STA",       "I", ""),
    ("ZFPAYM_GET",       "I", ""),
    ("ZFPAYM_END",       "I", ""),
    ("ZFPAYM_LNS",       "I", ""),
    ("ZFPAYM_SUB",       "I", ""),
    ("ZSAPFPAYM_REPLAY", "1", "FPMF"),   # report needs LDB
]

def fix_one(name, subc, ldb):
    print(f"\n--- {name} (SUBC={subc}, LDB='{ldb}') ---")
    abap = [
        f"REPORT zfix_attr.",
        f"DATA: lt_src TYPE STANDARD TABLE OF string,",
        f"      ls_trdir TYPE trdir.",
        f"READ REPORT '{name}' INTO lt_src.",
        f"WRITE: / 'READ sy-subrc=', sy-subrc, 'lines=', LINES( lt_src ).",
        f"SELECT SINGLE * FROM trdir INTO ls_trdir",
        f"  WHERE name = '{name}'.",
        f"ls_trdir-uccheck = 'X'.",
        f"ls_trdir-rload   = 'D'.",
        f"ls_trdir-varcl   = 'X'.",
        f"ls_trdir-appl    = 'F'.",
        f"ls_trdir-fixpt   = 'X'.",
    ]
    if ldb:
        abap.append(f"ls_trdir-ldbname = '{ldb}'.")
    abap += [
        f"INSERT REPORT '{name}'",
        f"  FROM lt_src DIRECTORY ENTRY ls_trdir.",
        f"WRITE: / 'INSERT sy-subrc=', sy-subrc.",
        f"COMMIT WORK.",
        # Verify
        f"DATA: ls_chk TYPE trdir.",
        f"SELECT SINGLE * FROM trdir INTO ls_chk",
        f"  WHERE name = '{name}'.",
        f"WRITE: / 'UCCHECK=', ls_chk-uccheck, 'LDB=', ls_chk-ldbname,",
        f"       'APPL=', ls_chk-appl, 'SUBC=', ls_chk-subc.",
    ]
    # Verify all lines ≤72 chars
    overlong = [(i, l) for i, l in enumerate(abap) if len(l) > 72]
    if overlong:
        print(f"  WARN: {len(overlong)} lines too long")
        for i, l in overlong: print(f"    line {i+1} ({len(l)}): {l}")
        return
    try:
        r = c.call("RFC_ABAP_INSTALL_AND_RUN", MODE='F',
                   PROGRAMNAME='ZFIX_ATTR',
                   PROGRAM=[{"LINE": l} for l in abap])
        if r.get("ERRORMESSAGE"):
            print(f"  ERROR: {r.get('ERRORMESSAGE')}")
        for w in (r.get("WRITES") or []):
            txt = w.get("ZEILE") if isinstance(w, dict) else str(w)
            print(f"  {txt}")
    except Exception as e:
        print(f"  FAIL: {e}")

for name, subc, ldb in TARGETS:
    fix_one(name, subc, ldb)

print("\n=== Final verify (all 9) ===")
print(f"  {'NAME':<22} {'SUBC':<5} {'LDBNAME':<8} {'APPL':<5} {'UCCHECK':<8} {'RLOAD':<6}")
for name, _, _ in TARGETS:
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR",
               OPTIONS=[{"TEXT": f"NAME = '{name}'"}],
               FIELDS=[{"FIELDNAME":"SUBC"},{"FIELDNAME":"LDBNAME"},
                       {"FIELDNAME":"APPL"},{"FIELDNAME":"UCCHECK"},
                       {"FIELDNAME":"RLOAD"}],
               DELIMITER='|')
    rows = r.get("DATA", [])
    if not rows:
        print(f"  {name:<22} NOT IN TRDIR")
    for row in rows:
        p = [x.strip() for x in row['WA'].split('|')]
        print(f"  {name:<22} {p[0]:<5} {p[1]:<8} {p[2]:<5} {p[3]:<8} {p[4]:<6}")
