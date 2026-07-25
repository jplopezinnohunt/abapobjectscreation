"""
extract_cdpos_by_object.py  —  detailed, scalable CDPOS extraction (field-level changes)
=======================================================================================
CDPOS is VERY large (tens of millions of rows — many field-changes per change document).
A blind full pull is infeasible. This extracts it the RIGHT way:

  * BY OBJECT  — iterate OBJECTCLAS in process-mining priority (EINKBELEG, BANF, BELEG,
    ENTRYSHEET, KRED, FMRESERV, ...). We only need the objects whose lifecycle we mine.
  * IN PARTS   — for each object, window by OBJECTID range (the leading CDPOS key after
    OBJECTCLAS). Each window is one resumable unit. Short WHERE (BETWEEN), no giant IN-list.
  * FIELD-FILTERED — only the PROCESS-RELEVANT fields (FNAME allowlist per object: release,
    status, deletion, key amounts). This is what turns "Change PO" into specific activities
    ("Released", "Blocked", "Quantity changed") AND cuts the volume by ~10-50x. Use --fields all
    to pull everything.
  * RESUMABLE  — checkpoint per (object, window) in cdpos_extract_state.json. Re-run continues.
  * STREAM     — write to SQLite per window (PK dedup, INSERT OR IGNORE), never accumulate in RAM.

RETENTION NOTE: CDPOS is PERMANENT audit data (not a ~15-day log) — full history is available, so
this is a one-time BULK historical extract (+ optional incremental delta on new CHANGENRs later).
The short-retention logs (TBTCO/TBTCP jobs, ST22, SM21) are handled separately by accumulate_logs.py.

🔴 CLUSTER-TABLE CAVEAT (deep-research s079, van der Aalst/RWTH): CDPOS sits behind cluster CDCLS in
classic ECC, where RFC_READ_TABLE / raw SQL CANNOT read it. On EhP8 it is SOMETIMES declustered
(transparent). This script PROBES RFC_READ_TABLE on CDPOS first; if it fails, it STOPS and prints the
ABAP-read fallback (CHANGEDOCUMENT_READ_POSITIONS or SELECT FOR ALL ENTRIES via
RFC_ABAP_INSTALL_AND_RUN). Activity mapping: FNAME / old-vs-new value (CHNGIND I=create,U=update,D=delete).

STATUS: P01 not active -> first run PENDING. Source of CHANGENR/OBJECTID lists = local cdhdr (we have it).

Usage:
  python extract_cdpos_by_object.py --object EINKBELEG          # one object
  python extract_cdpos_by_object.py --all                       # all priority objects
  python extract_cdpos_by_object.py --object EINKBELEG --fields all   # all fields (no filter)
  python extract_cdpos_by_object.py --all --resume              # continue from checkpoint
"""
import os, sys, json, sqlite3, argparse

MCP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP_DIR))
from rfc_helpers import get_connection, rfc_read_paginated  # skill helpers (adaptive width + DATA_LOSS)

ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
STATE = os.path.join(os.path.dirname(__file__), "cdpos_extract_state.json")

CDPOS_FIELDS = ["MANDANT", "OBJECTCLAS", "OBJECTID", "CHANGENR", "TABNAME",
                "TABKEY", "FNAME", "CHNGIND", "VALUE_NEW", "VALUE_OLD"]
PK = ["OBJECTCLAS", "OBJECTID", "CHANGENR", "TABNAME", "FNAME"]

WINDOW = 2000   # OBJECTIDs per extraction window (resumable unit)

# Per OBJECTCLAS: process-mining priority + the activity-relevant FNAME allowlist.
# Allowlists are STARTERS (validate/refine against real CDPOS when P01 is up).
OBJECTS = {
    "EINKBELEG":  {"prio": 1, "fields": ["FRGKE", "FRGZU", "FRGRL", "PROCSTAT", "LOEKZ", "STATU", "MENGE", "NETPR", "BSTYP", "BSART"]},
    "BANF":       {"prio": 1, "fields": ["FRGKZ", "FRGZU", "FRGST", "BANPR", "LOEKZ", "STATU", "MENGE"]},
    "BELEG":      {"prio": 1, "fields": ["AUGBL", "BSTAT", "STBLG", "STGRD", "XREF1", "XREF2", "ZLSPR", "ZFBDT"]},
    "ENTRYSHEET": {"prio": 2, "fields": ["KZABN", "LOEKZ", "LBLNE", "USERF1_TXT"]},
    "KRED":       {"prio": 2, "fields": ["SPERR", "SPERM", "LOEVM", "NODEL", "SPERQ", "ZAHLS"]},
    "FMRESERV":   {"prio": 3, "fields": None},   # None = pull all fields (validate first)
    "MM_SERVICE": {"prio": 3, "fields": None},
}


def ensure_table(db):
    cols = ", ".join(f'"{c}" TEXT' for c in CDPOS_FIELDS)
    pk = ", ".join(f'"{k}"' for k in PK)
    db.execute(f"CREATE TABLE IF NOT EXISTS cdpos ({cols}, PRIMARY KEY ({pk}))")


def load_state():
    return json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}


def save_state(s):
    json.dump(s, open(STATE, "w", encoding="utf-8"), indent=2)


def object_id_windows(db, objclass):
    """Sorted distinct OBJECTIDs (from local cdhdr) grouped into BETWEEN windows."""
    ids = [r[0] for r in db.execute(
        "SELECT DISTINCT OBJECTID FROM cdhdr WHERE OBJECTCLAS=? ORDER BY OBJECTID", (objclass,))]
    for i in range(0, len(ids), WINDOW):
        chunk = ids[i:i + WINDOW]
        yield i // WINDOW, chunk[0], chunk[-1], len(chunk)


def fname_clause(spec, use_all):
    if use_all or not spec.get("fields"):
        return ""
    flds = "','".join(spec["fields"])
    return f" AND FNAME IN ('{flds}')"


def extract_object(conn, db, objclass, spec, state, use_all):
    done = set(state.get(objclass, {}).get("windows_done", []))
    total_new = 0
    windows = list(object_id_windows(db, objclass))
    print(f"[{objclass}] {len(windows)} windows (OBJECTID ranges of {WINDOW})")
    for widx, lo, hi, n in windows:
        if widx in done:
            continue
        where = (f"OBJECTCLAS = '{objclass}' AND OBJECTID >= '{lo}' AND OBJECTID <= '{hi}'"
                 + fname_clause(spec, use_all))
        rows = rfc_read_paginated(conn, "CDPOS", CDPOS_FIELDS, where, batch_size=5000, throttle=1.0)
        before = db.execute("SELECT COUNT(*) FROM cdpos").fetchone()[0]
        ph = ",".join("?" * len(CDPOS_FIELDS))
        db.executemany(f"INSERT OR IGNORE INTO cdpos VALUES ({ph})", [list(r) for r in rows])
        db.commit()
        after = db.execute("SELECT COUNT(*) FROM cdpos").fetchone()[0]
        total_new += after - before
        done.add(widx)
        state.setdefault(objclass, {})["windows_done"] = sorted(done)
        save_state(state)
        print(f"  [{objclass}] window {widx} ({lo}..{hi}): pulled {len(rows)}, +{after-before} new (total cdpos {after})")
    state.setdefault(objclass, {})["complete"] = True
    save_state(state)
    print(f"[{objclass}] DONE — +{total_new} rows this run")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--object")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--fields", choices=["activity", "all"], default="activity")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    db = sqlite3.connect(GOLD, timeout=120)
    ensure_table(db)
    state = load_state() if args.resume else load_state()
    use_all = args.fields == "all"

    targets = ([args.object] if args.object else
               [o for o, s in sorted(OBJECTS.items(), key=lambda kv: kv[1]["prio"])] if args.all else [])
    if not targets:
        print("specify --object <OBJECTCLAS> or --all. Priority objects:",
              [o for o, s in sorted(OBJECTS.items(), key=lambda kv: kv[1]["prio"])])
        return

    print(f"Connecting to P01 ... extracting CDPOS for {targets} (fields={args.fields})")
    conn = get_connection("P01")
    # PROBE: is CDPOS readable via RFC_READ_TABLE on this kernel, or is it clustered (CDCLS)?
    try:
        probe = rfc_read_paginated(conn, "CDPOS", ["OBJECTCLAS", "OBJECTID", "CHANGENR", "FNAME"],
                                   "OBJECTCLAS = 'EINKBELEG'", batch_size=5)
        print(f"  CDPOS RFC_READ_TABLE probe OK ({len(probe)} sample rows) — declustered/transparent. Proceeding.")
    except Exception as e:
        print("  🔴 CDPOS NOT readable via RFC_READ_TABLE (likely CLUSTER table behind CDCLS).")
        print(f"     error: {str(e)[:120]}")
        print("     FALLBACK: extract via ABAP — CHANGEDOCUMENT_READ_POSITIONS per CHANGENR, OR a custom")
        print("     SELECT FROM cdpos FOR ALL ENTRIES (CHANGENR from cdhdr) via RFC_ABAP_INSTALL_AND_RUN.")
        print("     This script's RFC path won't work; use the ABAP path. Stopping.")
        conn.close(); db.close(); return
    try:
        for obj in targets:
            spec = OBJECTS.get(obj, {"prio": 9, "fields": None})
            extract_object(conn, db, obj, spec, state, use_all)
    finally:
        try: conn.close()
        except Exception: pass
        db.close()
    print(f"State: {STATE}")


if __name__ == "__main__":
    main()
