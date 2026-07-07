"""
psm_avc_refresh.py — recurring refresher for the FM Availability Control (AVC) layer
====================================================================================
The AVC layer was a one-off config-frontier pull (2026-06-19) and the FMAVCT totals
were untracked entirely (in neither _gold_sync_log nor a refresh cadence). This script
makes the WHOLE AVC layer a tracked, recurring part of the PSM_FM golden pipeline.

Two halves (run together by default, or independently):

  totals  — re-extract FMAVCT (the live AVC availability balances) for FM areas
            UNES + the 8 institute areas, fiscal years 2024-2026, AVC ledger 9H.
            Lands a WIDE superset of the legacy 7-col pull so that
            `available = budget - consumed` is computable: it keeps the value-type
            leg (ALLOCTYPE_9) AND the record-type leg (RRCTY) AND every HSL period
            bucket (HSLVT + HSL01..HSL16), not just HSL01. Rebuilds fmavct_2024/2025/2026.

  config  — pk-upsert refresh of the AVC config/customizing tables
            (BUAVCTOLASS, FMAVCATGR_001/002, FMAVCBUDFILTB/H, FMAVCLDGRACT/ATT/GAT).
            Self-adapting: reads each table's DDIC field list + key flags at runtime.

Both halves write a `_gold_sync_log` row (so freshness is queryable) and stamp the
`_config_frontier_manifest` with `extracted_at`.

Cadence (operator-driven, mirrors gold_refresh.py — there is no extraction scheduler):
  - config : weekly      (rarely changes)
  - totals : same cadence as fmifiit_full (the FM actuals), since the AVC balances
             drift daily with consumption.

Source = P01 LIVE, read-only RFC_READ_TABLE over SNC/SSO. No Excel. No writes to P01.
The P01 secured wrapper rejects ROWSKIPS -> all reads use ROWCOUNT=0 (full slice),
partitioned by FM area x year to stay well under the row ceiling. The wide FMAVCT
column set exceeds the RFC 512-byte WA buffer, so reads are FIELD-SPLIT into <=7-col
groups and recombined by row position (deterministic for identical WHERE + ROWCOUNT=0,
guarded by an equal-rowcount assertion per group).

Usage:
    python scripts/extraction/psm_avc_refresh.py            # config + totals
    python scripts/extraction/psm_avc_refresh.py totals
    python scripts/extraction/psm_avc_refresh.py config
"""
import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --------------------------------------------------------------- path resolution
# Source lives on a branch/worktree, but the golden DB (~14 GB, gitignored) and the
# RFC .env credentials live ONLY in the main checkout. Resolve to whichever path
# actually has the golden DB so this runs identically from a worktree or from main.
_MAIN = Path(r"c:\Users\jp_lopez\projects\abapobjectscreation")
_REL = Path(__file__).resolve().parents[1]


def _resolve_repo():
    for cand in (_REL, _MAIN):
        if (cand / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db").exists():
            return cand
    return _MAIN


REPO = _resolve_repo()
MCP = REPO / "Zagentexecution" / "mcp-backend-server-python"   # rfc_helpers + .env
sys.path.insert(0, str(MCP))
from rfc_helpers import get_connection  # type: ignore  # noqa: E402

GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

# The 9 FM areas: UNES + the 8 institute areas (matches gold_refresh.py FIKRS list).
FM_AREAS = ["UNES", "IIEP", "ICTP", "UIS", "UIL", "IBE", "UBO", "MGIE", "ICBA"]
YEARS = ["2024", "2025", "2026"]
AVC_LEDGER = "9H"

# ----------------------------------------------------------------- FMAVCT schema
# Superset of the legacy 7-col pull (RFIKRS, RFUND, RFUNDSCTR, RCMMTITEM, RYEAR,
# ALLOCTYPE_9, HSL01 all retained -> existing consumers do not break). Added:
#   RLDNR     - AVC ledger (9H)
#   RRCTY     - record type
#   RVERS     - version  /  RTCUR - currency  /  DRCRK - debit-credit  /  RPMAX
#   ROBJNR / COBJNR / SOBJNR - the AVC responsible / consuming / sender object numbers.
#               These complete FMAVCT's real natural key AND carry the cover-group
#               sender/receiver legs -> they distinguish the budget address from the
#               consumption against it. (Verified: without them ~36% of rows collided
#               on the readable dims and budget-vs-consumed was not resolvable.)
#   RFUNCAREA, RGRANT_NBR, RMEASURE, RCVRGRP_9, BUDGET_PD_9, WFSTATE_9 - dimensions
#   HSLVT + HSL01..HSL16 - ALL period buckets in FM-area (local) currency, so the
#               annual figure = HSLVT + sum(HSL01..HSL16), not just period 1.
# Stored key = RLDNR,RRCTY,RVERS,RYEAR,RTCUR,DRCRK,RPMAX,ROBJNR,COBJNR,SOBJNR
# (= FMAVCT's natural key minus the constant RCLNT) -> every row unique, delta-safe.
FMAVCT_DIMS = [
    "RLDNR", "RRCTY", "RVERS", "RYEAR", "RTCUR", "DRCRK", "RPMAX",
    "ROBJNR", "COBJNR", "SOBJNR",
    "RFIKRS", "RFUND", "RFUNDSCTR", "RCMMTITEM",
    "RFUNCAREA", "RGRANT_NBR", "RMEASURE", "RCVRGRP_9", "BUDGET_PD_9", "WFSTATE_9",
    "ALLOCTYPE_9",
]
FMAVCT_AMOUNTS = ["HSLVT"] + [f"HSL{i:02d}" for i in range(1, 17)]
FMAVCT_COLS = FMAVCT_DIMS + FMAVCT_AMOUNTS

# RFC_READ_TABLE 512-byte WA buffer -> read in <=7-col groups, recombine by position.
FMAVCT_READ_GROUPS = [
    ["RLDNR", "RRCTY", "RVERS", "RYEAR", "RTCUR", "DRCRK", "RPMAX"],
    ["ROBJNR", "COBJNR", "SOBJNR"],
    ["RFIKRS", "RFUND", "RFUNDSCTR", "RCMMTITEM", "RFUNCAREA", "RGRANT_NBR"],
    ["RMEASURE", "RCVRGRP_9", "BUDGET_PD_9", "WFSTATE_9", "ALLOCTYPE_9"],
    ["HSLVT", "HSL01", "HSL02", "HSL03", "HSL04", "HSL05", "HSL06"],
    ["HSL07", "HSL08", "HSL09", "HSL10", "HSL11", "HSL12", "HSL13"],
    ["HSL14", "HSL15", "HSL16"],
]

# AVC config/customizing tables (real SAP names confirmed via _config_frontier_manifest).
# gold name == lower(sap name). Refreshed by pk-upsert; key derived live from DD03L.
AVC_CONFIG_TABLES = [
    "BUAVCTOLASS", "FMAVCATGR_001", "FMAVCATGR_002", "FMAVCBUDFILTB",
    "FMAVCBUDFILTH", "FMAVCLDGRACT", "FMAVCLDGRATT", "FMAVCLDGRGAT",
]


# ----------------------------------------------------------------- RFC utilities
def _parse_delim(res, fields):
    """Parse a DELIMITER='|' RFC_READ_TABLE result into a list of value-lists."""
    out = []
    for row in res.get("DATA", []):
        parts = row["WA"].split("|")
        out.append([parts[i].strip() if i < len(parts) else "" for i in range(len(fields))])
    return out


def read_fields(g, table, fields, where):
    """One ROWCOUNT=0 read of `fields` (<=7) with WHERE. Returns list of value-lists."""
    res = g.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                 FIELDS=[{"FIELDNAME": f} for f in fields],
                 OPTIONS=([{"TEXT": where}] if where else []), ROWCOUNT=0)
    return _parse_delim(res, fields)


def read_wide(g, table, groups, where):
    """Field-split read: read each <=7-col group, recombine by row position.
    Safe because identical WHERE + ROWCOUNT=0 yields a deterministic, identical row
    order across calls; an equal-rowcount assertion guards against drift."""
    per_group = []
    n = None
    for grp in groups:
        rows = read_fields(g, table, grp, where)
        if n is None:
            n = len(rows)
        elif len(rows) != n:
            raise RuntimeError(
                f"field-split rowcount mismatch on {table} ({where}): "
                f"group {grp} returned {len(rows)} vs {n}")
        per_group.append(rows)
    if not n:
        return []
    return [sum((per_group[gi][ri] for gi in range(len(groups))), []) for ri in range(n)]


def dd03l_fields(g, table):
    """Return (all_field_names_excluding_includes, key_field_names) for a table."""
    res = g.call("RFC_READ_TABLE", QUERY_TABLE="DD03L", DELIMITER="|",
                 FIELDS=[{"FIELDNAME": x} for x in ["FIELDNAME", "POSITION", "KEYFLAG"]],
                 OPTIONS=[{"TEXT": f"TABNAME = '{table}' AND AS4LOCAL = 'A'"}], ROWCOUNT=0)
    rows = _parse_delim(res, ["FIELDNAME", "POSITION", "KEYFLAG"])
    rows.sort(key=lambda r: int(r[1] or 0))
    allf = [r[0] for r in rows if not r[0].startswith(".")]
    keys = [r[0] for r in rows if r[2] == "X" and not r[0].startswith(".")]
    return allf, keys


# ----------------------------------------------------------------- sync log / manifest
def ensure_log(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS _gold_sync_log (
        ts TEXT, domain TEXT, table_type TEXT, gold TEXT, sap TEXT, strategy TEXT,
        n_new INTEGER, n_changed INTEGER, n_deleted INTEGER, n_total INTEGER, detail TEXT)""")


def log_row(cur, ts, ttype, gold, sap, strat, new, chg, dele, total, detail=""):
    cur.execute("INSERT INTO _gold_sync_log VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (ts, "PSM_FM", ttype, gold, sap, strat, new, chg, dele, total, detail))


def manifest_stamp(cur, ts_human, sap, gold, n_fields, n_rows, note):
    cur.execute("""CREATE TABLE IF NOT EXISTS _config_frontier_manifest (
        grp TEXT, tabname TEXT, system TEXT, exists_in_catalog TEXT, n_fields INTEGER,
        n_rows INTEGER, sqlite_table TEXT, note TEXT, extracted_at TEXT)""")
    cur.execute("DELETE FROM _config_frontier_manifest WHERE tabname=? AND sqlite_table IS ?", (sap, gold))
    cur.execute("DELETE FROM _config_frontier_manifest WHERE tabname=? AND sqlite_table=?", (sap, gold))
    cur.execute("INSERT INTO _config_frontier_manifest VALUES (?,?,?,?,?,?,?,?,?)",
                ("AVC layer (recurring, psm_avc_refresh.py)", sap, "P01", "Y",
                 n_fields, n_rows, gold, note, ts_human))


# ----------------------------------------------------------------- totals (FMAVCT)
def refresh_totals(g, con, ts, ts_human):
    cur = con.cursor()
    print(f"\n[totals] FMAVCT  ledger={AVC_LEDGER}  areas={FM_AREAS}  years={YEARS}")
    for year in YEARS:
        gold = f"fmavct_{year}"
        # snapshot "before" for an honest delta line (legacy schema is narrow -> just count/sum)
        before_n, before_hsl01 = 0, 0.0
        try:
            before_n = cur.execute(f'SELECT COUNT(*) FROM "{gold}"').fetchone()[0]
            cols_before = [r[1] for r in cur.execute(f'PRAGMA table_info("{gold}")').fetchall()]
            if "HSL01" in cols_before:
                before_hsl01 = cur.execute(
                    f'SELECT TOTAL(CAST(replace(replace(HSL01,",",""),"-","") AS REAL)) FROM "{gold}"'
                ).fetchone()[0] or 0.0
        except sqlite3.OperationalError:
            pass

        all_rows = []
        for area in FM_AREAS:
            where = f"RLDNR = '{AVC_LEDGER}' AND RFIKRS = '{area}' AND RYEAR = '{year}'"
            try:
                rows = read_wide(g, "FMAVCT", FMAVCT_READ_GROUPS, where)
            except Exception as e:
                print(f"    [{gold} {area}] ERR {str(e)[:120]}")
                continue
            if rows:
                print(f"    {gold}  {area:5s}  +{len(rows)} rows")
                all_rows.extend(rows)

        # rebuild the table with the WIDE superset schema
        cur.execute(f'DROP TABLE IF EXISTS "{gold}"')
        cols_sql = ", ".join(f'"{c}" TEXT' for c in FMAVCT_COLS)
        cur.execute(f'CREATE TABLE "{gold}" ({cols_sql})')
        ph = ",".join("?" * len(FMAVCT_COLS))
        cur.executemany(f'INSERT INTO "{gold}" VALUES ({ph})', all_rows)
        con.commit()

        # legs present (budget vs consumption) for the run log
        legs = cur.execute(
            f'SELECT RRCTY, ALLOCTYPE_9, COUNT(*) FROM "{gold}" GROUP BY RRCTY, ALLOCTYPE_9 ORDER BY 3 DESC'
        ).fetchall()
        legs_txt = " ".join(f"RRCTY={r[0]}/{r[1]}:{r[2]}" for r in legs[:6])
        detail = (f"WIDE rebuild (legacy {before_n} rows narrow->{len(all_rows)} rows {len(FMAVCT_COLS)}cols, "
                  f"9 areas, ledger {AVC_LEDGER}); legs[{legs_txt}]")
        log_row(cur, ts, "totals", gold, "FMAVCT", "value-compare-fieldsplit",
                len(all_rows), 0, 0, len(all_rows), detail)
        manifest_stamp(cur, ts_human, "FMAVCT", gold, len(FMAVCT_COLS), len(all_rows),
                       f"AVC totals {year} (9 areas, ledger {AVC_LEDGER}, budget+consumption legs)")
        con.commit()
        print(f"    {gold:14s} total={len(all_rows):>7}  cols={len(FMAVCT_COLS)}  {legs_txt}")


# ----------------------------------------------------------------- config tables
def refresh_config(g, con, ts, ts_human):
    cur = con.cursor()
    print(f"\n[config] AVC customizing tables ({len(AVC_CONFIG_TABLES)})")
    for sap in AVC_CONFIG_TABLES:
        gold = sap.lower()
        try:
            fields, keys = dd03l_fields(g, sap)
        except Exception as e:
            print(f"    {gold}: DD03L ERR {str(e)[:100]}"); continue
        if not keys:
            keys = fields  # degenerate: treat whole row as key
        # read in <=7-col groups (some config rows are wide-ish) and recombine
        groups = [fields[i:i + 7] for i in range(0, len(fields), 7)]
        try:
            rows = read_wide(g, sap, groups, "")
        except Exception as e:
            print(f"    {gold}: READ ERR {str(e)[:100]}"); continue

        # delta vs existing gold (by key)
        ki = [fields.index(k) for k in keys]
        new_idx = {tuple(r[i] for i in ki): r for r in rows}
        old_idx = {}
        try:
            sel = ",".join(f'"{c}"' for c in fields)
            for orow in cur.execute(f'SELECT {sel} FROM "{gold}"'):
                orow = ["" if v is None else str(v) for v in orow]
                old_idx[tuple(orow[i] for i in ki)] = orow
        except sqlite3.OperationalError:
            pass
        n_new = sum(1 for k in new_idx if k not in old_idx)
        n_chg = sum(1 for k in new_idx if k in old_idx and new_idx[k] != old_idx[k])
        n_del = sum(1 for k in old_idx if k not in new_idx)

        cols_sql = ", ".join(f'"{c}" TEXT' for c in fields)
        pk_sql = ", ".join(f'"{k}"' for k in keys)
        cur.execute(f'DROP TABLE IF EXISTS "{gold}"')
        cur.execute(f'CREATE TABLE "{gold}" ({cols_sql}, PRIMARY KEY ({pk_sql}))')
        ph = ",".join("?" * len(fields))
        cur.executemany(f'INSERT OR REPLACE INTO "{gold}" VALUES ({ph})', list(new_idx.values()))
        con.commit()
        log_row(cur, ts, "config", gold, sap, "pk-upsert",
                n_new, n_chg, n_del, len(new_idx), f"key={keys}")
        manifest_stamp(cur, ts_human, sap, gold, len(fields), len(new_idx),
                       "AVC config (recurring)")
        con.commit()
        print(f"    {gold:16s} total={len(new_idx):>5}  +{n_new} ~{n_chg} -{n_del}  key={keys}")


# ----------------------------------------------------------------- main
def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    if mode not in ("all", "totals", "config"):
        print("Usage: python psm_avc_refresh.py [all|totals|config]"); return 1
    if not GOLD.exists():
        print(f"FATAL: golden DB not found at {GOLD}"); return 2

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ts_human = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    con = sqlite3.connect(GOLD)
    ensure_log(con.cursor()); con.commit()

    g = get_connection("P01")
    print(f"Connected P01 (read-only). AVC refresh mode={mode}  -> {GOLD}")

    if mode in ("all", "config"):
        refresh_config(g, con, ts, ts_human)
    if mode in ("all", "totals"):
        refresh_totals(g, con, ts, ts_human)
    g.close()

    print("\n[sync log — this run]")
    for r in con.cursor().execute(
            "SELECT table_type, gold, strategy, n_new, n_changed, n_deleted, n_total "
            "FROM _gold_sync_log WHERE ts=? ORDER BY table_type, gold", (ts,)):
        print(f"    {r[0]:8s} {r[1]:16s} {r[2]:24s} +{r[3]} ~{r[4]} -{r[5]} / {r[6]}")
    con.close()
    print("\nDONE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
