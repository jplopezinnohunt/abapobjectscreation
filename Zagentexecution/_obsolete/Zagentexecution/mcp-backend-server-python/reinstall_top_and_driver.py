"""
Re-install ZFPAYM_TOP (with REPORT zsapfpaym_replay) and ZSAPFPAYM_REPLAY
from local files. Each via its own ABAP one-shot using INSERT REPORT
DIRECTORY ENTRY trdir with the right attributes (SUBC, UCCHECK, LDBNAME).

Splits each source line into ≤45-char chunks if needed (PROGTAB 72-char limit).
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

PKG = os.path.join(os.path.dirname(__file__), "..", "..",
                   "extracted_code", "FI", "SAPFPAYM", "ZSAPFPAYM_REPLAY")

CHUNK = 45

def emit_append(line):
    safe = line.replace("`", "")
    if not safe:
        return ["APPEND `` TO lt_src."]
    if len(safe) + 22 <= 72:
        return [f"APPEND `{safe}` TO lt_src."]
    chunks = [safe[i:i+CHUNK] for i in range(0, len(safe), CHUNK)]
    out = []
    for idx, ch in enumerate(chunks):
        if idx == 0:
            out.append(f"APPEND `{ch}` &&")
        elif idx < len(chunks) - 1:
            out.append(f"       `{ch}` &&")
        else:
            out.append(f"       `{ch}` TO lt_src.")
    return out

def install(name, subc, ldb):
    print(f"\n=== Install {name} (SUBC={subc}, LDB='{ldb}') ===")
    with open(os.path.join(PKG, name + ".abap"), encoding="utf-8") as f:
        src_lines = f.read().splitlines()
    print(f"  source: {len(src_lines)} lines from {PKG}/{name}.abap")

    abap = [
        "REPORT zfix_install_x.",
        "DATA: lt_src TYPE STANDARD TABLE OF string,",
        "      ls_trdir TYPE trdir.",
    ]
    for ln in src_lines:
        abap.extend(emit_append(ln))
    abap += [
        f"ls_trdir-name    = '{name}'.",
        f"ls_trdir-subc    = '{subc}'.",
    ]
    if ldb:
        abap.append(f"ls_trdir-ldbname = '{ldb}'.")
    abap += [
        "ls_trdir-appl    = 'F'.",
        "ls_trdir-uccheck = 'X'.",
        "ls_trdir-rload   = 'D'.",
        "ls_trdir-varcl   = 'X'.",
        "ls_trdir-fixpt   = 'X'.",
        "ls_trdir-cnam    = sy-uname.",
        "ls_trdir-cdat    = sy-datum.",
        "ls_trdir-rmand   = sy-mandt.",
        f"INSERT REPORT '{name}'",
        f"  FROM lt_src DIRECTORY ENTRY ls_trdir.",
        "WRITE: / 'INSERT sy-subrc=', sy-subrc.",
        "COMMIT WORK.",
        "DATA: ls_chk TYPE trdir.",
        "SELECT SINGLE * FROM trdir INTO ls_chk",
        f"  WHERE name = '{name}'.",
        "WRITE: / 'SUBC=', ls_chk-subc, 'UCCHECK=', ls_chk-uccheck,",
        "       'LDB=', ls_chk-ldbname, 'APPL=', ls_chk-appl.",
    ]
    overlong = [(i+1, l) for i, l in enumerate(abap) if len(l) > 72]
    if overlong:
        print(f"  WARN {len(overlong)} lines >72:")
        for i, l in overlong[:3]: print(f"    {i}({len(l)}): {l}")
        return
    print(f"  ABAP installer: {len(abap)} lines")
    try:
        r = c.call("RFC_ABAP_INSTALL_AND_RUN", MODE='F',
                   PROGRAMNAME='ZFIX_INSTALL_X',
                   PROGRAM=[{"LINE": l} for l in abap])
        if r.get("ERRORMESSAGE"):
            print(f"  ERROR: {r.get('ERRORMESSAGE')}")
        for w in (r.get("WRITES") or []):
            txt = w.get("ZEILE") if isinstance(w, dict) else str(w)
            print(f"  {txt}")
    except Exception as e:
        print(f"  FAIL: {e}")

c = get_connection("D01")

# Install ZFPAYM_STA, ZFPAYM_GET, ZFPAYM_END from local (with the latest fixes),
# then reaffirm ZFPAYM_TOP and ZSAPFPAYM_REPLAY
for nm, sb, lb in [
    ("ZFPAYM_STA", "I", ""),
    ("ZFPAYM_GET", "I", ""),
    ("ZFPAYM_END", "I", ""),
    ("ZFPAYM_TOP", "I", ""),
    ("ZSAPFPAYM_REPLAY", "1", "FPMF"),
]:
    install(nm, sb, lb)

print("\n=== Final verify ===")
for name in ["ZFPAYM_STA", "ZFPAYM_GET", "ZFPAYM_END", "ZFPAYM_TOP", "ZSAPFPAYM_REPLAY"]:
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR",
               OPTIONS=[{"TEXT": f"NAME = '{name}'"}],
               FIELDS=[{"FIELDNAME":"SUBC"},{"FIELDNAME":"LDBNAME"},
                       {"FIELDNAME":"APPL"},{"FIELDNAME":"UCCHECK"},
                       {"FIELDNAME":"RLOAD"}],
               DELIMITER='|')
    for row in r.get("DATA",[]):
        p = [x.strip() for x in row['WA'].split('|')]
        print(f"  {name:<22} SUBC={p[0]} LDB={p[1]:<8} APPL={p[2]} UCCHECK={p[3]} RLOAD={p[4]}")
