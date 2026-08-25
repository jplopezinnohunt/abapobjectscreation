"""
extract_fund_center_hierarchy.py
================================
Extract the FM FUND-CENTER STANDARD HIERARCHY (the org responsibility-axis
rollup: office -> region -> sector -> HQ) into the golden DB.

Request: Zagentexecution/sap_data_extraction/pending_from_sap_brain/
         REQUEST_fund_center_hierarchy.md  (from unesco-sap-brain S39)

Background (measured on golden, 2026-06-30):
  - golden HAS the leaf master: fund_centers (787, key FICTR/FIKRS) + text.
  - golden MISSES the hierarchy: SETLEAF/SETNODE/SETHEADER(T) hold only
    set class 0000 (15 basis sets) -- none of the FM fund-center groups.

SAP stores the FM fund-center hierarchy as a SET (group structure). In classic
FM the fund-center groups live under set class '0306', SUBCLASS = FM area
(FIKRS). This script does NOT assume that blindly -- it runs a DISCRIMINATOR
probe first: it asks SAP which SETCLASS actually contains the fund_centers.FICTR
values, then extracts whatever class resolves the leaves into a tree.

Read-only: RFC_READ_TABLE over SNC/SSO on P01 (compliant -- no writes, no ADT).

APPEND semantics (NOT drop-and-replace): the SETLEAF/SETNODE/SETHEADER/SETHEADERT
golden tables already hold set class 0000. We DELETE only the resolved class rows
(idempotent re-run) and INSERT them, preserving the 0000 basis sets.

Output:
  - rows appended to setnode / setleaf / setheader / setheadert (golden, lowercase)
  - _fund_center_hierarchy_manifest  (set class/name used, row counts, leaf coverage)
  - fund_center_hierarchy_summary.json  (human-readable run summary)

Run:
    python extract_fund_center_hierarchy.py
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
SUMMARY = os.path.join(HERE, "fund_center_hierarchy_summary.json")

# Lo que este proyecto YA aprendio de sus propios instrumentos, leido ANTES de minar.
# A12_traverse_hierarchy ya midio que los centros gestores viven en SETCLASS 0312 (y una
# segunda agrupacion numerica en 0303), no en el 0306 que este minero trae por defecto.
sys.path.insert(0, os.path.join(PROJECT_ROOT, "process_mining"))
try:
    from metodo import lo_que_ya_aprendimos as _aprendido  # noqa: E402
except Exception:
    _aprendido = None

# FM areas requested: UNES + the 8 institute FM areas
FM_AREAS = ["UNES", "ICTP", "UIS", "IIEP", "IBE", "UIL", "ICBA", "MGIE", "UBO"]

# The standard FM fund-center group set class. We CONFIRM this empirically via the
# discriminator probe before trusting it; candidates probed in order.
CANDIDATE_SET_CLASSES = ["0306"]

# The four SET tables that together encode the hierarchy
SET_TABLES = ["SETHEADER", "SETHEADERT", "SETNODE", "SETLEAF"]


def get_fields(conn, table):
    """Explicit flat field list (names) via RFC_READ_TABLE FIELDS metadata."""
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                    ROWCOUNT=1, OPTIONS=[], FIELDS=[])
    return [f["FIELDNAME"] for f in res.get("FIELDS", [])]


def sample_fictr(db, n=20):
    """A spread of real FICTR values (one per FM area + extras) to probe with."""
    vals = []
    for area in FM_AREAS:
        row = db.execute("SELECT FICTR FROM fund_centers WHERE FIKRS=? LIMIT 1", (area,)).fetchone()
        if row:
            vals.append(row[0])
    # top up with any others
    for (f,) in db.execute("SELECT FICTR FROM fund_centers LIMIT ?", (n,)):
        if f not in vals:
            vals.append(f)
        if len(vals) >= n:
            break
    return vals


def discriminator_probe(conn, db):
    """Ask SAP which SETCLASS holds the fund_centers.FICTR values.

    Reads SETLEAF rows whose VALFROM matches a spread of real fund-center codes
    (no SETCLASS filter) and tallies which SETCLASS they belong to. The winning
    class is the FM fund-center hierarchy class.
    """
    probe_vals = sample_fictr(db)
    where = f"VALFROM IN {quoted_in(probe_vals)}"
    fields = ["SETCLASS", "SUBCLASS", "SETNAME", "VALFROM", "VALTO"]
    rows = rfc_read_paginated(conn, "SETLEAF", fields, where, batch_size=5000, throttle=1.0)
    tally = {}
    for r in rows:
        cls = r.get("SETCLASS", "")
        tally[cls] = tally.get(cls, 0) + 1
    print(f"  probe FICTR sample ({len(probe_vals)}): {probe_vals}")
    print(f"  SETLEAF SETCLASS tally for those values: {tally}")
    return tally, probe_vals


def append_class(db, sqlite_tbl, set_class, rows, sap_fields):
    """Idempotent append: delete this set class, insert fresh. Preserves 0000.

    Aligns SAP fields to the existing golden table's columns.
    """
    existing_cols = [c[1] for c in db.execute(f"PRAGMA table_info({sqlite_tbl})")]
    if not existing_cols:
        # table absent -> create from SAP field list (shouldn't happen; all 4 exist)
        cols = ", ".join([f'"{f}" TEXT' for f in sap_fields])
        db.execute(f"CREATE TABLE {sqlite_tbl} ({cols})")
        existing_cols = list(sap_fields)
    use_cols = [c for c in existing_cols if c in sap_fields] or existing_cols
    db.execute(f"DELETE FROM {sqlite_tbl} WHERE SETCLASS=?", (set_class,))
    if rows:
        ph = ", ".join(["?"] * len(use_cols))
        col_list = ", ".join([f'"{c}"' for c in use_cols])
        batch = [tuple(r.get(c, "") for c in use_cols) for r in rows]
        db.executemany(f"INSERT INTO {sqlite_tbl} ({col_list}) VALUES ({ph})", batch)
    db.commit()
    return len(rows)


def ensure_manifest(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS _fund_center_hierarchy_manifest (
            set_class TEXT, subclass_scope TEXT, sap_table TEXT, sqlite_table TEXT,
            n_rows INTEGER, note TEXT, extracted_at TEXT
        )""")
    db.commit()


def record(db, set_class, scope, sap_table, sqlite_tbl, n_rows, note, ts):
    db.execute("DELETE FROM _fund_center_hierarchy_manifest WHERE set_class=? AND sap_table=?",
               (set_class, sap_table))
    db.execute("INSERT INTO _fund_center_hierarchy_manifest VALUES (?,?,?,?,?,?,?)",
               (set_class, scope, sap_table, sqlite_tbl, n_rows, note, ts))
    db.commit()


def leaf_coverage(db, set_class):
    """How many distinct fund_centers.FICTR are resolved by the extracted leaves?"""
    total = db.execute("SELECT COUNT(DISTINCT FICTR) FROM fund_centers").fetchone()[0]
    # SETLEAF single-value leaves (VALFROM=VALTO) cover discrete fund centers.
    covered = db.execute("""
        SELECT COUNT(DISTINCT fc.FICTR) FROM fund_centers fc
        WHERE EXISTS (
            SELECT 1 FROM setleaf sl
            WHERE sl.SETCLASS=?
              AND TRIM(fc.FICTR) BETWEEN TRIM(sl.VALFROM) AND
                  CASE WHEN TRIM(sl.VALTO)='' THEN TRIM(sl.VALFROM) ELSE TRIM(sl.VALTO) END
        )""", (set_class,)).fetchone()[0]
    return covered, total


def main():
    if _aprendido:
        _aprendido("setclass", "fund centre", "fund_center", "hierarch",
                   "rfc_read_table").avisar()

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"=== FM fund-center hierarchy extraction | P01 | {ts} ===\n")

    db = sqlite3.connect(GOLD_DB)
    ensure_manifest(db)

    conn = get_connection("P01")
    print("Connected to P01 (SNC/SSO).\n")

    # ---- 1. DISCRIMINATOR: which SETCLASS holds the fund centers? ----------
    print("### Discriminator probe (which SETCLASS resolves fund_centers.FICTR)")
    tally, probe_vals = discriminator_probe(conn, db)
    # exclude 0000 (basis sets) from candidates; pick the dominant non-0000 class
    non_basis = {c: n for c, n in tally.items() if c and c != "0000"}
    resolved_class = None
    if non_basis:
        resolved_class = max(non_basis, key=non_basis.get)
    elif CANDIDATE_SET_CLASSES:
        resolved_class = CANDIDATE_SET_CLASSES[0]  # fall back to documented default
    print(f"  -> resolved set class = {resolved_class!r}\n")

    if not resolved_class:
        print("!! No set class resolved the fund-center values. Aborting (nothing to land).")
        conn.close(); db.close(); return

    # ---- 2. EXTRACT the four SET tables for the resolved class -------------
    scope = quoted_in(FM_AREAS)
    print(f"### Extract SET tables for SETCLASS={resolved_class}, SUBCLASS IN {scope}")
    summary = {"run_at": ts, "system": "P01", "resolved_set_class": resolved_class,
               "discriminator_tally": tally, "probe_values": probe_vals,
               "fm_areas": FM_AREAS, "tables": {}}

    for sap_table in SET_TABLES:
        fields = get_fields(conn, sap_table)
        # SUBCLASS = FM area for SETNODE/SETLEAF/SETHEADER/SETHEADERT
        where = f"SETCLASS = '{resolved_class}' AND SUBCLASS IN {scope}"
        rows = rfc_read_paginated(conn, sap_table, fields, where, batch_size=5000, throttle=1.0)
        # Fallback: some installs leave SUBCLASS blank -> retry class-only
        scope_note = f"SUBCLASS IN {scope}"
        if not rows:
            where2 = f"SETCLASS = '{resolved_class}'"
            rows = rfc_read_paginated(conn, sap_table, fields, where2, batch_size=5000, throttle=1.0)
            scope_note = "SETCLASS only (SUBCLASS blank in this install)"
        n = append_class(db, sap_table.lower(), resolved_class, rows, fields)
        record(db, resolved_class, scope_note, sap_table, sap_table.lower(), n, "loaded", ts)
        summary["tables"][sap_table] = {"rows": n, "scope": scope_note}
        print(f"  {sap_table:<12} {n:>6,} rows  -> {sap_table.lower()}  [{scope_note}]")

    # ---- 3. VALIDATE leaf <-> fund_centers.FICTR coverage -----------------
    covered, total = leaf_coverage(db, resolved_class)
    pct = (100.0 * covered / total) if total else 0.0
    print(f"\n### Leaf coverage: {covered}/{total} fund_centers.FICTR resolved "
          f"by set class {resolved_class} leaves ({pct:.1f}%)")
    summary["leaf_coverage"] = {"covered": covered, "total": total, "pct": round(pct, 1)}
    record(db, resolved_class, "validation", "(fund_centers.FICTR coverage)", None,
           covered, f"{covered}/{total} FICTR resolved ({pct:.1f}%)", ts)

    conn.close()

    with open(SUMMARY, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print("\n=== MANIFEST (_fund_center_hierarchy_manifest) ===")
    for sc, scope_n, tab, st, n, note in db.execute(
        "SELECT set_class, subclass_scope, sap_table, sqlite_table, n_rows, note "
        "FROM _fund_center_hierarchy_manifest ORDER BY sap_table"):
        print(f"  [{n:>5}] class={sc} {tab:<28} -> {st or '-':<12} {note}")
    db.close()
    print(f"\nSummary -> {SUMMARY}")


if __name__ == "__main__":
    main()
