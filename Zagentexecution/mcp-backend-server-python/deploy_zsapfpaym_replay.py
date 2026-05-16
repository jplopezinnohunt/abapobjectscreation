"""
deploy_zsapfpaym_replay.py
==========================
Deploy ZSAPFPAYM_REPLAY + 8 includes to D01 via RFC.

Strategy:
  1) For each include: try RPY_PROGRAM_INSERT with TYP='I' (include).
     If it returns "already exists" → call RPY_PROGRAM_UPDATE.
  2) For the main report: same with TYP='1' (REPORT).

Dev class: $TMP (local, no transport).
NO INVENTING: only uses standard SAP RFC FMs verified available in D01.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

PKG_DIR = os.path.join(os.path.dirname(__file__), "..", "..",
                      "extracted_code", "FI", "SAPFPAYM", "ZSAPFPAYM_REPLAY")

# Order: includes first (so the report can find them on activation), report last.
DEPLOY_ORDER = [
    ("ZFPAYM_TOP",       "I", "Z Replay — Global data declarations"),
    ("ZFPAYM_INI",       "I", "Z Replay — Initialization"),
    ("ZFPAYM_SEL",       "I", "Z Replay — Selection screen"),
    ("ZFPAYM_STA",       "I", "Z Replay — Start of selection (CHECKs removed)"),
    ("ZFPAYM_GET",       "I", "Z Replay — Get payment data + DMEE break-point"),
    ("ZFPAYM_END",       "I", "Z Replay — End of selection + ROLLBACK"),
    ("ZFPAYM_LNS",       "I", "Z Replay — Line selection"),
    ("ZFPAYM_SUB",       "I", "Z Replay — Subroutines"),
    ("ZSAPFPAYM_REPLAY", "1", "Z Payment Medium REPLAY (no checks, ROLLBACK at end)"),
]

DEVCLASS = "$TMP"        # local objects, no transport
SUPPRESS_DIALOG = "X"     # do not open dialog on insert

def read_source(name):
    path = os.path.join(PKG_DIR, name + ".abap")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # SOURCE_EXTENDED is a table; each row is one line (max 255 chars per row)
    lines = text.splitlines()
    return [{"LINE": l[:255]} for l in lines], len(lines)

def insert_or_update(conn, name, ptype, title):
    src_tab, n_lines = read_source(name)
    print(f"  {name} ({ptype}) — {n_lines} lines, title='{title}'")

    # Try RPY_PROGRAM_INSERT first
    try:
        r = conn.call("RPY_PROGRAM_INSERT",
                      DEVELOPMENT_CLASS=DEVCLASS,
                      PROGRAM_NAME=name,
                      PROGRAM_TYPE=ptype,
                      TITLE_STRING=title,
                      SUPPRESS_DIALOG=SUPPRESS_DIALOG,
                      SAVE_INACTIVE='',           # save active
                      SOURCE_EXTENDED=src_tab)
        print(f"    ✓ INSERTED")
        return "INSERTED"
    except Exception as e:
        emsg = str(e)
        if "ALREADY_EXISTS" in emsg or "PROG_EXISTS" in emsg or "DUPLICATE" in emsg:
            print(f"    (already exists — will UPDATE)")
        else:
            print(f"    INSERT error: {emsg[:300]}")

    # Fallback: RPY_PROGRAM_UPDATE (no USER_PROGRAM in this release)
    try:
        r = conn.call("RPY_PROGRAM_UPDATE",
                      PROGRAM_NAME=name,
                      TITLE_STRING=title,
                      SAVE_INACTIVE='',
                      SOURCE_EXTENDED=src_tab)
        print(f"    ✓ UPDATED")
        return "UPDATED"
    except Exception as e:
        print(f"    UPDATE error: {str(e)[:300]}")
        return "FAILED"


def main():
    print(f"[{time.strftime('%H:%M:%S')}] Connecting D01...")
    c = get_connection("D01")
    print(f"[{time.strftime('%H:%M:%S')}] Connected. Devclass={DEVCLASS}.\n")

    results = {}
    for name, ptype, title in DEPLOY_ORDER:
        results[name] = insert_or_update(c, name, ptype, title)

    print(f"\n=== Summary ===")
    for n, status in results.items():
        ok = "✓" if status in ("INSERTED", "UPDATED") else "✗"
        print(f"  {ok} {n:<22} {status}")

    # Final verify: REPOSRC + TRDIR per name (audit bans IN())
    print(f"\n=== Verify in REPOSRC + TRDIR (one by one) ===")
    print(f"  {'NAME':<22} {'REPOSRC?':<10} {'STATE':<6} {'TRDIR?':<8} {'TYP':<4}")
    print(f"  {'-'*22} {'-'*10} {'-'*6} {'-'*8} {'-'*4}")
    for name, ptype, _ in DEPLOY_ORDER:
        rstate = trsubc = "?"
        rok = trok = "no"
        try:
            r = c.call("RFC_READ_TABLE", QUERY_TABLE="REPOSRC",
                       OPTIONS=[{"TEXT": f"PROGNAME = '{name}'"}],
                       FIELDS=[{"FIELDNAME":"PROGNAME"},{"FIELDNAME":"R3STATE"}],
                       ROWCOUNT=5, DELIMITER='|')
            rows = r.get("DATA", [])
            if rows:
                rok = "yes"
                rstate = rows[0]['WA'].split('|')[1].strip()
        except Exception:
            pass
        try:
            r = c.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR",
                       OPTIONS=[{"TEXT": f"NAME = '{name}'"}],
                       FIELDS=[{"FIELDNAME":"NAME"},{"FIELDNAME":"SUBC"}],
                       ROWCOUNT=5, DELIMITER='|')
            rows = r.get("DATA", [])
            if rows:
                trok = "yes"
                trsubc = rows[0]['WA'].split('|')[1].strip()
        except Exception:
            pass
        print(f"  {name:<22} {rok:<10} {rstate:<6} {trok:<8} {trsubc:<4}")


if __name__ == "__main__":
    main()
