"""
p01_fm_ps_bcs_masterdata_refresh.py
-----------------------------------
ONE idempotent refresher for the FM/BCS + PS Project-System master-data backbone,
P01 LIVE -> the CANONICAL golden DB
(Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db).

Supersedes the scattered, stale-path scripts:
  * refresh_funds_from_live.py  (funds / fund_centers / FMFINT)         -> folded in
  * p01_proj_prps_sync.py       (proj / prps; wrote to the OLD PSM path) -> folded in + repointed
  * p01_ytfm_biennium_sync.py   (ytfm C/5 model)                         -> still run separately

Scope (verified against P01 2026-06-22, CP-003 evidence):
  FM / BCS dimensions
    FMFINCODE  -> funds                 (Fund master; per-FIKRS, ROWSKIPS-paged: UNES=55k)
    FMFCTR     -> fund_centers          (Funds Center master)
    FMFINT     -> FMFINT                (Fund text, EN; ALL 9 institutes, was only 3)
    FMFCTRT    -> fund_centers_text      [NEW]  (Funds Center text, EN)
    FMCI       -> commitment_items       [NEW]  (Commitment Item master, GJAHR='0000')
    FMCIT      -> commitment_items_text  [NEW]  (Commitment Item text, EN)
    TFKB       -> functional_areas       [NEW]  (Functional Area)
    TFKBT      -> functional_areas_text  [NEW]  (Functional Area text, EN)
  PS Project System
    PROJ       -> proj                  (Project definition; repointed to canonical DB)
    PRPS       -> prps                  (WBS element;        repointed to canonical DB)
    PRHI       -> proj_hierarchy         [NEW]  (Project hierarchy UP/DOWN/LEFT/RIGHT)

NOT in scope (deliberate):
  * FMMEASURE (Funded Program) = 0 rows on P01 -> UNESCO does not use it; "projects" = PS.
  * FMBH/FMBL/BPGE/BPJA = BCS budget DOCUMENTS/TOTALS (transactional, already present) -> not master data.
  * YTFM C/5 custom model -> run scripts/extraction/p01_ytfm_biennium_sync.py.

SOURCE = SAP P01 ONLY, read-only RFC_READ_TABLE over SNC/SSO. No Excel, ever. No writes to P01.
Run:  python scripts/extraction/p01_fm_ps_bcs_masterdata_refresh.py
"""
import os
import sys
import sqlite3
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
MCP = HERE.parents[1] / "Zagentexecution" / "mcp-backend-server-python"
sys.path.insert(0, str(MCP))
from rfc_helpers import get_connection  # type: ignore

REPO = HERE.parents[1]
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

FIKRS = ['UNES', 'IIEP', 'ICTP', 'UIS', 'UIL', 'IBE', 'UBO', 'MGIE', 'ICBA']


# ---------------------------------------------------------------- RFC readers
def _parse(res):
    """Offset-based parse (robust; handles '|' inside data, fixed-width WA)."""
    meta = res.get("FIELDS", [])
    rows = []
    for row in res.get("DATA", []):
        wa = row.get("WA", "")
        rec = {}
        for f in meta:
            off = int(f["OFFSET"]); ln = int(f["LENGTH"])
            rec[f["FIELDNAME"]] = wa[off:off + ln].strip()
        rows.append(rec)
    return rows


def read_whole(g, table, fields, where=""):
    """ROWCOUNT=0 single call. Proven up to ~60k narrow rows on the P01 secured wrapper."""
    res = g.call("RFC_READ_TABLE", QUERY_TABLE=table,
                 FIELDS=[{"FIELDNAME": f} for f in fields],
                 OPTIONS=([{"TEXT": where}] if where else []), ROWCOUNT=0)
    return _parse(res)


def read_by_partition(g, table, fields, part_field, parts, extra=""):
    """One ROWCOUNT=0 call PER partition value. The P01 secured wrapper (class SAIS)
    REJECTS ROWSKIPS (OPTION_NOT_VALID), so we cannot page; instead we partition by
    FIKRS so each call stays under the ~60k-row WA ceiling (UNES FMFINCODE = 55k < 60k,
    proven by PRPS/PRHI whole-table reads of ~59.7k)."""
    out = []
    for pv in parts:
        where = f"{part_field} = '{pv}'" + (f" AND {extra}" if extra else "")
        try:
            res = g.call("RFC_READ_TABLE", QUERY_TABLE=table,
                         FIELDS=[{"FIELDNAME": f} for f in fields],
                         OPTIONS=[{"TEXT": where}], ROWCOUNT=0)
        except Exception as e:
            if "TABLE_WITHOUT_DATA" in str(e):
                continue
            print(f"    [{table} {pv}] ERR: {str(e)[:110]}")
            continue
        out.extend(_parse(res))
    return out


# ---------------------------------------------------------------- persistence
def write_table(cur, db_table, create_sql, cols, recs):
    before = 0
    try:
        before = cur.execute(f"SELECT COUNT(*) FROM \"{db_table}\"").fetchone()[0]
    except sqlite3.OperationalError:
        before = None  # table did not exist
    cur.execute(f"DROP TABLE IF EXISTS \"{db_table}\"")
    cur.execute(create_sql)
    ph = ",".join("?" * len(cols))
    cur.executemany(f"INSERT OR REPLACE INTO \"{db_table}\" VALUES ({ph})",
                    [tuple(r.get(c, "") for c in cols) for r in recs])
    after = cur.execute(f"SELECT COUNT(*) FROM \"{db_table}\"").fetchone()[0]
    tag = "NEW" if before is None else f"{before}->{after} ({after - before:+d})"
    print(f"  {db_table:22s} {after:>7} rows   [{tag}]")
    return after


def main():
    print(f"Canonical Golden DB: {GOLD}\n")
    g = get_connection("P01")
    print("Connected P01 (read-only RFC).\n")

    extracted = {}

    print("[FM/BCS] reading from P01 ...")
    # Fund master — per-FIKRS paged (UNES is 55k)
    extracted["funds"] = read_by_partition(
        g, "FMFINCODE", ["FIKRS", "FINCODE", "TYPE", "ERFDAT", "ERFNAME"], "FIKRS", FIKRS)
    # Funds Center master — narrow, whole per FIKRS
    extracted["fund_centers"] = read_by_partition(
        g, "FMFCTR", ["FIKRS", "FICTR", "ERFDAT", "ERFNAME"], "FIKRS", FIKRS)
    # Fund text (EN) — ALL institutes
    extracted["FMFINT"] = read_by_partition(
        g, "FMFINT", ["FIKRS", "FINCODE", "SPRAS", "BEZEICH", "BESCHR"], "FIKRS", FIKRS,
        extra="SPRAS = 'E'")
    # Funds Center text (EN) [NEW]
    extracted["fund_centers_text"] = read_by_partition(
        g, "FMFCTRT", ["FIKRS", "FICTR", "SPRAS", "BEZEICH", "BESCHR"], "FIKRS", FIKRS,
        extra="SPRAS = 'E'")
    # Commitment Item master [NEW] (GJAHR='0000', tiny)
    extracted["commitment_items"] = read_by_partition(
        g, "FMCI", ["FIKRS", "GJAHR", "FIPEX", "KATEG", "FIVOR", "FICTR"], "FIKRS", FIKRS)
    extracted["commitment_items_text"] = read_by_partition(
        g, "FMCIT", ["FIKRS", "FIPEX", "SPRAS", "BEZEI", "TEXT1"], "FIKRS", FIKRS,
        extra="SPRAS = 'E'")
    # Functional Area [NEW] — whole table (9 / 36 rows)
    extracted["functional_areas"] = read_whole(g, "TFKB", ["FKBER", "AUTHGRP", "DATAB", "DATBIS"])
    extracted["functional_areas_text"] = read_whole(
        g, "TFKBT", ["FKBER", "SPRAS", "FKBTX"], "SPRAS = 'E'")

    print("\n[PS] reading from P01 ...")
    extracted["proj"] = read_whole(g, "PROJ", ["VBUKR", "PSPID", "POST1", "VERNR", "ERDAT", "PSPNR"])
    extracted["prps"] = read_whole(
        g, "PRPS", ["PBUKR", "POSID", "POST1", "VERNR", "ERDAT", "PSPHI", "PSPNR", "OBJNR", "ERNAM"])
    extracted["proj_hierarchy"] = read_whole(
        g, "PRHI", ["POSNR", "PSPHI", "UP", "DOWN", "LEFT", "RIGHT"])

    g.close()

    # ---------------------------------------------------------------- persist
    print("\n[WRITE] overwriting canonical golden DB ...")
    con = sqlite3.connect(GOLD)
    cur = con.cursor()

    SPECS = [
        ("funds", """CREATE TABLE funds (FIKRS TEXT, FINCODE TEXT, TYPE TEXT, ERFDAT TEXT,
                     ERFNAME TEXT, PRIMARY KEY (FIKRS, FINCODE))""",
         ["FIKRS", "FINCODE", "TYPE", "ERFDAT", "ERFNAME"]),
        ("fund_centers", """CREATE TABLE fund_centers (FIKRS TEXT, FICTR TEXT, ERFDAT TEXT,
                     ERFNAME TEXT, PRIMARY KEY (FIKRS, FICTR))""",
         ["FIKRS", "FICTR", "ERFDAT", "ERFNAME"]),
        ("FMFINT", """CREATE TABLE FMFINT (FIKRS TEXT, FINCODE TEXT, SPRAS TEXT, BEZEICH TEXT,
                     BESCHR TEXT, PRIMARY KEY (FIKRS, FINCODE, SPRAS))""",
         ["FIKRS", "FINCODE", "SPRAS", "BEZEICH", "BESCHR"]),
        ("fund_centers_text", """CREATE TABLE fund_centers_text (FIKRS TEXT, FICTR TEXT, SPRAS TEXT,
                     BEZEICH TEXT, BESCHR TEXT, PRIMARY KEY (FIKRS, FICTR, SPRAS))""",
         ["FIKRS", "FICTR", "SPRAS", "BEZEICH", "BESCHR"]),
        ("commitment_items", """CREATE TABLE commitment_items (FIKRS TEXT, GJAHR TEXT, FIPEX TEXT,
                     KATEG TEXT, FIVOR TEXT, FICTR TEXT, PRIMARY KEY (FIKRS, GJAHR, FIPEX))""",
         ["FIKRS", "GJAHR", "FIPEX", "KATEG", "FIVOR", "FICTR"]),
        ("commitment_items_text", """CREATE TABLE commitment_items_text (FIKRS TEXT, FIPEX TEXT,
                     SPRAS TEXT, BEZEI TEXT, TEXT1 TEXT, PRIMARY KEY (FIKRS, FIPEX, SPRAS))""",
         ["FIKRS", "FIPEX", "SPRAS", "BEZEI", "TEXT1"]),
        ("functional_areas", """CREATE TABLE functional_areas (FKBER TEXT, AUTHGRP TEXT, DATAB TEXT,
                     DATBIS TEXT, PRIMARY KEY (FKBER))""",
         ["FKBER", "AUTHGRP", "DATAB", "DATBIS"]),
        ("functional_areas_text", """CREATE TABLE functional_areas_text (FKBER TEXT, SPRAS TEXT,
                     FKBTX TEXT, PRIMARY KEY (FKBER, SPRAS))""",
         ["FKBER", "SPRAS", "FKBTX"]),
        ("proj", """CREATE TABLE proj (VBUKR TEXT, PSPID TEXT, POST1 TEXT, VERNR TEXT, ERDAT TEXT,
                     PSPNR TEXT, PRIMARY KEY (PSPID))""",
         ["VBUKR", "PSPID", "POST1", "VERNR", "ERDAT", "PSPNR"]),
        ("prps", """CREATE TABLE prps (PBUKR TEXT, POSID TEXT, POST1 TEXT, VERNR TEXT, ERDAT TEXT,
                     PSPHI TEXT, PSPNR TEXT, OBJNR TEXT, ERNAM TEXT, PRIMARY KEY (POSID))""",
         ["PBUKR", "POSID", "POST1", "VERNR", "ERDAT", "PSPHI", "PSPNR", "OBJNR", "ERNAM"]),
        ("proj_hierarchy", """CREATE TABLE proj_hierarchy (POSNR TEXT, PSPHI TEXT, UP TEXT, DOWN TEXT,
                     LEFTND TEXT, RIGHTND TEXT, PRIMARY KEY (POSNR))""",
         ["POSNR", "PSPHI", "UP", "DOWN", "LEFT", "RIGHT"]),
    ]

    counts = {}
    for db_table, create_sql, cols in SPECS:
        counts[db_table] = write_table(cur, db_table, create_sql, cols, extracted[db_table])
    con.commit()

    # ---------------------------------------------------------------- verify
    print("\n[VERIFY] by FIKRS / company code:")
    for r in cur.execute("SELECT FIKRS, COUNT(*) FROM funds GROUP BY FIKRS ORDER BY 2 DESC"):
        pass
    fc = dict(cur.execute("SELECT FIKRS, COUNT(*) FROM funds GROUP BY FIKRS").fetchall())
    print(f"  funds by FIKRS: {fc}")
    pc = dict(cur.execute("SELECT VBUKR, COUNT(*) FROM proj GROUP BY VBUKR").fetchall())
    print(f"  proj  by VBUKR: {pc}")
    print(f"  proj max ERDAT: {cur.execute('SELECT MAX(ERDAT) FROM proj').fetchone()[0]}")

    con.close()
    print("\nDONE. (P01 RFC read-only; no Excel; canonical golden DB updated.)")


if __name__ == "__main__":
    main()
