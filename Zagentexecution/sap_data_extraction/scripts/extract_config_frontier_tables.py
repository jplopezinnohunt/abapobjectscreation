"""
extract_config_frontier_tables.py
==================================
LAST-FRONTIER SAP config extraction (2026-06-19). Pulls the customizing tables
that close the unesco-sap-brain's remaining SAP-internal hypotheses:

  HYP-018 / CLM-012/024  GMDERIVE config        (GMDT* / GMDERIVE*) — discovery showed NONE
  HYP-008 / OI-FI-01     Document splitting      (T8G*, FAGL_SPLIT*)
  F3                     New-GL ledger           (T881/T882, FAGLFLEXT, FMGLFLEXT)
  CLM-036 / HYP-003      Full FMDERIVE 26-step   (FMDERIVE*, FMDERIVEFUNC ...)
  HYP-012                AVC tolerance           (FMUP*)

Read-only: RFC_READ_TABLE over SNC/SSO on P01 (compliant — no writes, no ADT).
Config tables are tiny; extracted in full. EMPTY tables are recorded in the
manifest as 0 rows — absence/emptiness is itself the evidence (e.g. FAGLFLEXT
empty => classic GL; T8G17/T8G40 empty => splitting not active; no GMDERIVE* =>
GM derivation not configured).

Output:
  - One lowercase SQLite table per NON-EMPTY config table in p01_gold_master_data.db
  - _config_frontier_manifest  (every probed table incl. empty/absent, with row counts)
  - config_frontier_summary.json  (human-readable run summary)

Run:
    python extract_config_frontier_tables.py
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

MCP = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

HERE = os.path.dirname(__file__)
PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD_DB = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
DISCOVERY = os.path.join(HERE, "config_tables_discovery.json")
SUMMARY = os.path.join(HERE, "config_frontier_summary.json")

# Supplementary GM-module presence probe (characterise "GM unused" vs "GM on, derivation off")
GM_PRESENCE_PROBE = ["GMGR", "GMIA", "GMDS", "GMDERIVE", "GMDT_FIELD", "GMDT_STEP"]


def get_fields(conn, table):
    """Explicit flat field list (names) via RFC_READ_TABLE FIELDS metadata."""
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                    ROWCOUNT=1, OPTIONS=[], FIELDS=[])
    return [f["FIELDNAME"] for f in res.get("FIELDS", [])]


def table_exists(conn, table):
    rows = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD02L", DELIMITER="|",
                     ROWCOUNT=1, OPTIONS=[{"TEXT": f"TABNAME = '{table}' AND AS4LOCAL = 'A'"}],
                     FIELDS=[{"FIELDNAME": "TABNAME"}]).get("DATA", [])
    return len(rows) > 0


def load_to_sqlite(db, table, rows, fields):
    """Replace-and-load a config table (full refresh — config is a snapshot)."""
    tbl = table.lower()
    cols = ", ".join([f'"{f}" TEXT' for f in fields])
    db.execute(f"DROP TABLE IF EXISTS {tbl}")
    db.execute(f"CREATE TABLE {tbl} ({cols})")
    if rows:
        ph = ", ".join(["?"] * len(fields))
        col_list = ", ".join([f'"{f}"' for f in fields])
        batch = [tuple(r.get(f, "") for f in fields) for r in rows]
        db.executemany(f"INSERT INTO {tbl} ({col_list}) VALUES ({ph})", batch)
    db.commit()


def ensure_manifest(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS _config_frontier_manifest (
            grp TEXT, tabname TEXT, system TEXT, exists_in_catalog TEXT,
            n_fields INTEGER, n_rows INTEGER, sqlite_table TEXT,
            note TEXT, extracted_at TEXT
        )""")
    db.commit()


def record(db, grp, tabname, system, exists, n_fields, n_rows, sqlite_table, note, ts):
    db.execute("DELETE FROM _config_frontier_manifest WHERE tabname=? AND system=?", (tabname, system))
    db.execute("INSERT INTO _config_frontier_manifest VALUES (?,?,?,?,?,?,?,?,?)",
               (grp, tabname, system, "Y" if exists else "N", n_fields, n_rows, sqlite_table, note, ts))
    db.commit()


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"=== Config-frontier extraction | P01 | {ts} ===")

    with open(DISCOVERY, encoding="utf-8") as fh:
        discovery = json.load(fh)

    conn = get_connection("P01")
    print("Connected to P01 (SNC/SSO).\n")
    db = sqlite3.connect(GOLD_DB)
    ensure_manifest(db)

    summary = {"run_at": ts, "system": "P01", "groups": {}}
    grand_rows = 0
    grand_tables = 0

    for grp, hits in discovery.items():
        print(f"### {grp}")
        g = {"loaded": [], "empty": [], "errors": []}
        for h in hits:
            tab = h["TABNAME"]
            try:
                fields = get_fields(conn, tab)
                rows = rfc_read_paginated(conn, tab, fields, "", batch_size=5000, throttle=1.0)
                n = len(rows)
                if n > 0:
                    load_to_sqlite(db, tab, rows, fields)
                    record(db, grp, tab, "P01", True, len(fields), n, tab.lower(),
                           "loaded", ts)
                    g["loaded"].append({"table": tab, "rows": n, "fields": len(fields)})
                    grand_rows += n
                    grand_tables += 1
                    print(f"  {tab:<22} {n:>6,} rows  -> {tab.lower()}")
                else:
                    record(db, grp, tab, "P01", True, len(fields), 0, None,
                           "EMPTY in client 350 (evidence)", ts)
                    g["empty"].append(tab)
                    print(f"  {tab:<22}      0 rows  [EMPTY — evidence]")
            except Exception as e:
                msg = f"{type(e).__name__}: {str(e).splitlines()[0]}"
                record(db, grp, tab, "P01", True, -1, -1, None, f"ERROR {msg}", ts)
                g["errors"].append({"table": tab, "error": msg})
                print(f"  {tab:<22}  ERROR {msg}")
        summary["groups"][grp] = g
        print()

    # ---- Supplementary GMDERIVE / GM-module presence probe ----------------
    print("### GMDERIVE absence + GM-module presence probe")
    gm = {"absent": [], "present": []}
    for tab in GM_PRESENCE_PROBE:
        try:
            exists = table_exists(conn, tab)
            if not exists:
                record(db, "GMDERIVE (HYP-018, CLM-012/024)", tab, "P01", False, 0, 0, None,
                       "NOT in DD02L catalog — GM derivation/object absent", ts)
                gm["absent"].append(tab)
                print(f"  {tab:<22} absent from catalog")
                continue
            fields = get_fields(conn, tab)
            rows = rfc_read_paginated(conn, tab, fields, "", batch_size=5000, throttle=1.0)
            n = len(rows)
            note = "GM table present" + (" with data" if n else " but EMPTY")
            if n:
                load_to_sqlite(db, tab, rows, fields)
            record(db, "GMDERIVE (HYP-018, CLM-012/024)", tab, "P01", True, len(fields), n,
                   tab.lower() if n else None, note, ts)
            gm["present"].append({"table": tab, "rows": n})
            print(f"  {tab:<22} {n:>6,} rows  ({note})")
        except Exception as e:
            msg = f"{type(e).__name__}: {str(e).splitlines()[0]}"
            print(f"  {tab:<22} ERROR {msg}")
    summary["gm_probe"] = gm
    print()

    conn.close()

    summary["totals"] = {"non_empty_tables_loaded": grand_tables, "rows_loaded": grand_rows}
    with open(SUMMARY, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    # Manifest readout
    print("=== MANIFEST (row counts per table) ===")
    for grp, tab, n, st in db.execute(
        "SELECT grp, tabname, n_rows, sqlite_table FROM _config_frontier_manifest ORDER BY grp, tabname"):
        tag = st if st else ("EMPTY" if n == 0 else "—")
        print(f"  [{n if n>=0 else 'ERR':>5}] {tab:<22} {tag}")
    db.close()

    print(f"\nLoaded {grand_tables} non-empty config tables ({grand_rows:,} rows) into {os.path.basename(GOLD_DB)}")
    print(f"Summary -> {SUMMARY}")


if __name__ == "__main__":
    main()
