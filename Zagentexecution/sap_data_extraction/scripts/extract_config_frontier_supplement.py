"""
extract_config_frontier_supplement.py
=====================================
Round 2 — the REAL config tables the discovery probe revealed (the brain's
assumed names FMDT_*/FAGL_SPLIT_ACTC/Z000000012 were wrong for EHP8):

  Derivation step master (CLM-036, HYP-003) — the generic Derivation Tool
  "ABDR" framework, NOT FMDT_*:
      TABADR   strategy registry (which step methods are used)
      TABADRT  strategy texts
      TABADRH  strategy/environment header (version, modified_by/on)
      TABADRS  STEP master  (STEP_NO, METHOD MOVE/DRULE/EXIT, IS_SAP_STEP, MODIFIED_BY)
      TABADRSF step source/target FIELDS
      TABADRST step texts

  AVC tolerance/control ledger (HYP-012) — BCS AVC:
      BUAVCTOLASS    tolerance LIMITS (90% W / 100% E)  <-- the "50%/100%" answer
      FMAVCLDGRATT   AVC ledger attributes (TOLPROF assignment per FM-area)
      FMAVCLDGRACT   AVC ledger activation (LDGRSTAT)
      FMAVCLDGRGAT   AVC ledger check-horizon
      FMAVCBUDFILTH/B, FMAVCUPDFILTH/V, FMAVCATGR_001/002, FMAVCACTCD  AVC filters/grouping
      FM01TOL        former-budgeting tolerance (legacy)
      FMR_TOL/FMR_TOLS/FMR_TOLST  funds-reservation tolerance

All FM-scoped via WHERE APPLCLASS='FM' for the TABADR* tables (avoid pulling
CMS/RE/other modules). FMAVC* config tables are tiny -> full pull. The large
AVC transactional tables (FMAVCA/FMAVCP/FMAVCO/FMAVCT) are deliberately NOT here.
"""
import os, sys, sqlite3
from datetime import datetime
MCP = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP))
from rfc_helpers import get_connection, rfc_read_paginated

GOLD_DB = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"

# table -> (WHERE clause, group)
TARGETS = {
    # derivation step master (FM only)
    "TABADR":    ("APPLCLASS = 'FM'", "FMDERIVE 26-step (CLM-036, HYP-003)"),
    "TABADRT":   ("APPLCLASS = 'FM'", "FMDERIVE 26-step (CLM-036, HYP-003)"),
    "TABADRH":   ("APPLCLASS = 'FM'", "FMDERIVE 26-step (CLM-036, HYP-003)"),
    "TABADRS":   ("APPLCLASS = 'FM'", "FMDERIVE 26-step (CLM-036, HYP-003)"),
    "TABADRSF":  ("APPLCLASS = 'FM'", "FMDERIVE 26-step (CLM-036, HYP-003)"),
    "TABADRST":  ("APPLCLASS = 'FM'", "FMDERIVE 26-step (CLM-036, HYP-003)"),
    # AVC tolerance / control ledger
    "BUAVCTOLASS":   ("APPLIC = 'FM'", "AVC tolerance (HYP-012)"),
    "FMAVCLDGRATT":  ("", "AVC tolerance (HYP-012)"),
    "FMAVCLDGRACT":  ("", "AVC tolerance (HYP-012)"),
    "FMAVCLDGRGAT":  ("", "AVC tolerance (HYP-012)"),
    "FMAVCBUDFILTH": ("", "AVC tolerance (HYP-012)"),
    "FMAVCBUDFILTB": ("", "AVC tolerance (HYP-012)"),
    "FMAVCUPDFILTH": ("", "AVC tolerance (HYP-012)"),
    "FMAVCUPDFILTV": ("", "AVC tolerance (HYP-012)"),
    "FMAVCATGR_001": ("", "AVC tolerance (HYP-012)"),
    "FMAVCATGR_002": ("", "AVC tolerance (HYP-012)"),
    "FMAVCACTCD":    ("", "AVC tolerance (HYP-012)"),
    "FM01TOL":       ("", "AVC tolerance (HYP-012)"),
    "FMR_TOL":       ("", "AVC tolerance (HYP-012)"),
    "FMR_TOLS":      ("", "AVC tolerance (HYP-012)"),
    "FMR_TOLST":     ("", "AVC tolerance (HYP-012)"),
    "FMUP03":        ("", "AVC tolerance (HYP-012)"),
}


def get_fields(conn, table):
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|", ROWCOUNT=1, OPTIONS=[], FIELDS=[])
    return [f["FIELDNAME"] for f in res.get("FIELDS", [])]


def load(db, table, rows, fields):
    tbl = table.lower()
    db.execute(f"DROP TABLE IF EXISTS {tbl}")
    db.execute(f"CREATE TABLE {tbl} (" + ", ".join([f'"{f}" TEXT' for f in fields]) + ")")
    if rows:
        ph = ", ".join(["?"] * len(fields))
        cl = ", ".join([f'"{f}"' for f in fields])
        db.executemany(f"INSERT INTO {tbl} ({cl}) VALUES ({ph})",
                       [tuple(r.get(f, "") for f in fields) for r in rows])
    db.commit()


def record(db, grp, tab, n, fields, st, note, ts):
    db.execute("DELETE FROM _config_frontier_manifest WHERE tabname=? AND system=?", (tab, "P01"))
    db.execute("INSERT INTO _config_frontier_manifest VALUES (?,?,?,?,?,?,?,?,?)",
               (grp, tab, "P01", "Y", fields, n, st, note, ts))
    db.commit()


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"=== Supplement extraction | P01 | {ts} ===")
    conn = get_connection("P01")
    db = sqlite3.connect(GOLD_DB)
    total = 0
    for tab, (where, grp) in TARGETS.items():
        try:
            fields = get_fields(conn, tab)
            rows = rfc_read_paginated(conn, tab, fields, where, batch_size=5000, throttle=1.0)
            n = len(rows)
            if n > 0:
                load(db, tab, rows, fields)
                record(db, grp, tab, n, len(fields), tab.lower(), "loaded (supplement)", ts)
                total += n
                print(f"  {tab:<16} {n:>6,} rows -> {tab.lower()}")
            else:
                record(db, grp, tab, 0, len(fields), None, "EMPTY (supplement)", ts)
                print(f"  {tab:<16}      0 rows [EMPTY]")
        except Exception as e:
            print(f"  {tab:<16} ERROR {type(e).__name__}: {str(e).splitlines()[0]}")
    conn.close()
    db.close()
    print(f"\nSupplement loaded {total:,} rows.")


if __name__ == "__main__":
    main()
