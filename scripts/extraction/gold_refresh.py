"""
gold_refresh.py  — registry-driven, delta-aware golden-DB refresher
-------------------------------------------------------------------
Refresh BY DOMAIN, and within a domain BY TABLE TYPE (user directive 2026-06-22):
    master_data / text / hierarchy  -> DELTA by primary key (new / changed / deleted)
    totals                          -> VALUE-COMPARE per key (amounts old -> new)
    transaction                     -> HIGH-WATER-MARK append (only docs beyond last sync)

Why this exists: the old DROP+CREATE refresher overwrote tables wholesale, so it could
not tell what actually CHANGED ("data creada no actualizada"), and a raw row COUNT is
meaningless for totals/transactions — you need the VALUES. This engine computes a real
delta per table type and writes a `_gold_sync_log` audit row each run.

Reads the contract from brain_v2/gold_table_registry.json (curated specs).
Source = P01 LIVE, read-only RFC_READ_TABLE over SNC/SSO. No Excel. No writes to P01.
P01 secured wrapper REJECTS ROWSKIPS -> read ROWCOUNT=0 partitioned by FIKRS.

Usage:
    python scripts/extraction/gold_refresh.py PSM_FM master_data
    python scripts/extraction/gold_refresh.py PS                 # all types in domain
    python scripts/extraction/gold_refresh.py PSM_FM             # all types
    python scripts/extraction/gold_refresh.py --list             # show domains/types
"""
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MCP = REPO / "Zagentexecution" / "mcp-backend-server-python"
sys.path.insert(0, str(MCP))
from rfc_helpers import get_connection  # type: ignore

GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
REGISTRY = REPO / "brain_v2" / "gold_table_registry.json"
FIKRS = ['UNES', 'IIEP', 'ICTP', 'UIS', 'UIL', 'IBE', 'UBO', 'MGIE', 'ICBA']


# ----------------------------------------------------------------- RFC reads
def _parse(res):
    meta = res.get("FIELDS", [])
    out = []
    for row in res.get("DATA", []):
        wa = row.get("WA", "")
        out.append({f["FIELDNAME"]: wa[int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
                    for f in meta})
    return out


def read_p01(g, sap, fields, partition=None, where="", part_values=None):
    """ROWCOUNT=0; partitioned (wrapper rejects ROWSKIPS) to stay under the ~60k ceiling.
    partition='FIKRS' -> the 9 institutes; any other field -> caller supplies part_values."""
    if partition:
        parts = part_values if part_values is not None else (FIKRS if partition == "FIKRS" else [None])
    else:
        parts = [None]
    out = []
    for pv in parts:
        clauses = []
        if pv is not None:
            clauses.append(f"{partition} = '{pv}'")
        if where:
            clauses.append(where)
        opt = " AND ".join(clauses)
        try:
            res = g.call("RFC_READ_TABLE", QUERY_TABLE=sap,
                         FIELDS=[{"FIELDNAME": f} for f in fields],
                         OPTIONS=([{"TEXT": opt}] if opt else []), ROWCOUNT=0)
        except Exception as e:
            if "TABLE_WITHOUT_DATA" in str(e):
                continue
            print(f"      [{sap} {pv}] ERR {str(e)[:90]}")
            continue
        out.extend(_parse(res))
    return out


# ----------------------------------------------------------------- sync log
def ensure_log(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS _gold_sync_log (
        ts TEXT, domain TEXT, table_type TEXT, gold TEXT, sap TEXT, strategy TEXT,
        n_new INTEGER, n_changed INTEGER, n_deleted INTEGER, n_total INTEGER, detail TEXT)""")


def log_row(cur, ts, dom, ttype, spec, strat, new, changed, deleted, total, detail=""):
    cur.execute("INSERT INTO _gold_sync_log VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (ts, dom, ttype, spec["gold"], spec.get("sap", ""), strat,
                 new, changed, deleted, total, detail))


# ----------------------------------------------------------------- strategies
def refresh_pk_upsert(g, con, ts, dom, ttype, spec):
    """master_data / text / hierarchy — true delta by PK.
    sap_fields = SAP column names for RFC read; gold_cols = golden-DB column names
    (differ when a SAP col is a SQL reserved word, e.g. PRHI LEFT/RIGHT -> LEFTND/RIGHTND).
    Both are positional-aligned. `key` is given in gold_cols names (PK cols are never renamed)."""
    gold, sap, key = spec["gold"], spec["sap"], spec["key"]
    sap_fields = spec["fields"]
    gold_cols = spec.get("gold_cols", sap_fields)
    where = spec.get("where", "")
    p01 = read_p01(g, sap, sap_fields, spec.get("partition"), where)
    # PK position is identical in sap_fields and gold_cols (never renamed)
    ki = [gold_cols.index(k) for k in key]
    p01_idx = {tuple(r.get(sap_fields[i], "") for i in ki):
               tuple(r.get(f, "") for f in sap_fields) for r in p01}

    cur = con.cursor()
    gold_idx = {}
    try:
        sel = ", ".join(f'"{c}"' for c in gold_cols)
        for row in cur.execute(f'SELECT {sel} FROM "{gold}"'):
            row = tuple("" if v is None else str(v) for v in row)
            gold_idx[tuple(row[i] for i in ki)] = row
    except sqlite3.OperationalError:
        pass  # first load

    new = [k for k in p01_idx if k not in gold_idx]
    deleted = [k for k in gold_idx if k not in p01_idx]
    changed = [k for k in p01_idx if k in gold_idx and p01_idx[k] != gold_idx[k]]

    # apply: ensure schema, UPSERT all P01, DELETE removed keys
    cols_sql = ", ".join(f'"{c}" TEXT' for c in gold_cols)
    pk_sql = ", ".join(f'"{k}"' for k in key)
    cur.execute(f'CREATE TABLE IF NOT EXISTS "{gold}" ({cols_sql}, PRIMARY KEY ({pk_sql}))')
    ph = ",".join("?" * len(gold_cols))
    cur.executemany(f'INSERT OR REPLACE INTO "{gold}" VALUES ({ph})', list(p01_idx.values()))
    if deleted:
        where_pk = " AND ".join(f'"{k}"=?' for k in key)
        cur.executemany(f'DELETE FROM "{gold}" WHERE {where_pk}', deleted)
    con.commit()

    detail = ""
    if new:
        detail += "new=" + ",".join("|".join(k) for k in new[:3]) + ("..." if len(new) > 3 else "") + " "
    if changed:
        detail += "chg=" + ",".join("|".join(k) for k in changed[:3]) + ("..." if len(changed) > 3 else "") + " "
    if deleted:
        detail += "del=" + ",".join("|".join(k) for k in deleted[:3]) + ("..." if len(deleted) > 3 else "")
    log_row(cur, ts, dom, ttype, spec, "pk-upsert", len(new), len(changed), len(deleted), len(p01_idx), detail.strip())
    con.commit()
    print(f"    {gold:24s} total={len(p01_idx):>6}  +{len(new)} new  ~{len(changed)} chg  -{len(deleted)} del   {detail[:70]}")


def refresh_value_compare(g, con, ts, dom, ttype, spec):
    """totals — compare amount VALUES per key (a row count is meaningless for totals).
    SCHEMA-PRESERVING: reads the existing golden columns and re-pulls those same SAP
    columns, partitioned, so we never narrow the table. Computes the value delta BEFORE
    replacing storage (so the change is reported, not blind)."""
    gold, sap, key = spec["gold"], spec["sap"], spec["key"]
    vfields = spec.get("value_fields", [])
    cur = con.cursor()
    cols = [r[1] for r in cur.execute(f'PRAGMA table_info("{gold}")').fetchall()]
    if not cols:
        print(f"    {gold:24s} SKIP value-compare: golden table absent"); return
    if not vfields:
        print(f"    {gold:24s} SKIP value-compare: no value_fields ({spec.get('note','')})")
        log_row(cur, ts, dom, ttype, spec, "value-compare", 0, 0, 0, 0, "no value_fields"); con.commit(); return
    vfields = [v for v in vfields if v in cols]
    # CRITICAL: a totals business key = ALL dimension cols (everything except amounts +
    # MANDT). An incomplete key collapses distinct rows -> data loss. So derive it fully.
    key = [c for c in cols if c not in vfields and c.upper() != "MANDT"]
    part = spec.get("partition")
    pvals = None
    if part and part != "FIKRS":
        pvals = [r[0] for r in cur.execute(f'SELECT DISTINCT "{part}" FROM "{gold}"').fetchall()]
    p01 = read_p01(g, sap, cols, part, part_values=pvals)        # full existing columns
    ki = [cols.index(k) for k in key]
    vi = [cols.index(v) for v in vfields]
    p01_idx = {tuple(r.get(cols[i], "") for i in ki): tuple(r.get(c, "") for c in cols) for r in p01}

    gold_idx = {}
    sel = ",".join(f'"{c}"' for c in cols)
    for row in cur.execute(f'SELECT {sel} FROM "{gold}"'):
        row = tuple("" if v is None else str(v) for v in row)
        gold_idx[tuple(row[i] for i in ki)] = row
    new = [k for k in p01_idx if k not in gold_idx]
    changed = [k for k in p01_idx if k in gold_idx
               and tuple(p01_idx[k][i] for i in vi) != tuple(gold_idx[k][i] for i in vi)]
    gone = [k for k in gold_idx if k not in p01_idx]

    # replace storage with the complete pulled state (delta already computed above)
    cur.execute(f'DELETE FROM "{gold}"')
    cur.executemany(f'INSERT INTO "{gold}" ({sel}) VALUES ({",".join("?" * len(cols))})',
                    list(p01_idx.values()))
    con.commit()

    sample = ""
    if changed:
        k0 = changed[0]
        old_v = tuple(gold_idx[k0][i] for i in vi); new_v = tuple(p01_idx[k0][i] for i in vi)
        sample = f"e.g. {'|'.join(k0)}: {old_v}->{new_v}"
    log_row(cur, ts, dom, ttype, spec, "value-compare", len(new), len(changed), len(gone),
            len(p01_idx), f"vf={vfields} {sample}"); con.commit()
    print(f"    {gold:24s} total={len(p01_idx):>6}  +{len(new)} new  ~{len(changed)} value-changed  "
          f"-{len(gone)} gone  ({','.join(vfields)})  {sample[:50]}")


PERIODS = ["000"] + [f"{i:03d}" for i in range(1, 17)]
YEARS = ["2024", "2025", "2026"]


def _combos(partition):
    """partition = list of field names. Values: FIKRS/FM_AREA->institutes,
    GJAHR/DOCYEAR->YEARS, PERIO->PERIODS. Cartesian product (empty combos skipped at read)."""
    src = {"FIKRS": FIKRS, "FM_AREA": FIKRS, "BUKRS": FIKRS,
           "GJAHR": YEARS, "DOCYEAR": YEARS, "PERIO": PERIODS}
    lists = [[(f, v) for v in src[f]] for f in partition]
    out = [[]]
    for lst in lists:
        out = [c + [item] for c in out for item in lst]
    return out  # list of [(field,val),...]


def refresh_txn_partitioned(g, con, ts, dom, ttype, spec):
    """transaction line items — partitioned full-state DELTA, scoped to recent biennia.
    Same correctness model as totals (key = all non-amount cols → no collapse), but
    REPLACE-BY-PARTITION so each (FIKRS×GJAHR[×PERIO]) combo is re-pulled and swapped
    independently — keeps every RFC call bounded and leaves out-of-scope years intact."""
    gold, sap = spec["gold"], spec["sap"]
    vfields = spec.get("value_fields", [])
    partition = spec.get("partition", [])
    cur = con.cursor()
    cols = [r[1] for r in cur.execute(f'PRAGMA table_info("{gold}")').fetchall()]
    if not cols:
        print(f"    {gold:24s} SKIP: golden table absent"); return
    vfields = [v for v in vfields if v in cols]
    pfields = [f for f in partition if f in cols]
    key = [c for c in cols if c not in vfields and c.upper() != "MANDT"]
    ki = [cols.index(k) for k in key]
    vi = [cols.index(v) for v in vfields]
    sel = ",".join(f'"{c}"' for c in cols)
    ph = ",".join("?" * len(cols))

    tot_new = tot_chg = tot_gone = tot = 0
    combos = _combos(pfields) if pfields else [[]]
    print(f"    {gold:24s} {len(combos)} partitions ({'×'.join(pfields)}), scope GJAHR {YEARS} ...")
    for combo in combos:
        where = " AND ".join(f"{f} = '{v}'" for f, v in combo)
        rows = read_p01(g, sap, cols, None) if not where else \
            g_read(g, sap, cols, where)
        if not rows:
            continue
        p01_idx = {tuple(r.get(cols[i], "") for i in ki): tuple(r.get(c, "") for c in cols) for r in rows}
        # golden rows in this partition
        gwhere = " AND ".join(f'"{f}"=?' for f, v in combo)
        gvals = [v for f, v in combo]
        gold_idx = {}
        q = f'SELECT {sel} FROM "{gold}"' + (f" WHERE {gwhere}" if gwhere else "")
        for row in cur.execute(q, gvals):
            row = tuple("" if v is None else str(v) for v in row)
            gold_idx[tuple(row[i] for i in ki)] = row
        new = sum(1 for k in p01_idx if k not in gold_idx)
        chg = sum(1 for k in p01_idx if k in gold_idx
                  and tuple(p01_idx[k][i] for i in vi) != tuple(gold_idx[k][i] for i in vi))
        gone = sum(1 for k in gold_idx if k not in p01_idx)
        # replace this partition
        if gwhere:
            cur.execute(f'DELETE FROM "{gold}" WHERE {gwhere}', gvals)
        cur.executemany(f'INSERT INTO "{gold}" ({sel}) VALUES ({ph})', list(p01_idx.values()))
        con.commit()
        tot_new += new; tot_chg += chg; tot_gone += gone; tot += len(p01_idx)
        if len(p01_idx) > 1000:
            print(f"      {'/'.join(v for _, v in combo):20s} {len(p01_idx):>7}  +{new} ~{chg} -{gone}")
    log_row(cur, ts, dom, ttype, spec, "txn-partitioned", tot_new, tot_chg, tot_gone, tot,
            f"scope={YEARS} part={pfields}"); con.commit()
    print(f"    {gold:24s} DONE  scoped total={tot:>8}  +{tot_new} new  ~{tot_chg} chg  -{tot_gone} gone")


def g_read(g, sap, cols, where):
    """single ROWCOUNT=0 read with a WHERE (no partition iteration)."""
    return read_p01(g, sap, cols, None, where=where)


STRATS = {"pk-upsert": refresh_pk_upsert, "value-compare": refresh_value_compare,
          "txn-partitioned": refresh_txn_partitioned}


def main():
    args = [a for a in sys.argv[1:]]
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if not args or args[0] == "--list":
        print("Domains × table types in registry:")
        for d, types in reg["domains"].items():
            print(f"  {d:14s} {{ {', '.join(f'{t}:{len(v)}' for t, v in types.items())} }}")
        return

    dom = args[0]
    only_type = args[1] if len(args) > 1 and not args[1].startswith("tables=") else None
    tbl_filter = None
    for a in args[1:]:
        if a.startswith("tables="):
            tbl_filter = set(a.split("=", 1)[1].split(","))
    if dom not in reg["domains"]:
        print(f"Domain '{dom}' not in registry. Use --list."); return

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    con = sqlite3.connect(GOLD)
    ensure_log(con.cursor()); con.commit()

    g = get_connection("P01")
    print(f"Connected P01 (read-only). Refreshing {dom}" + (f" / {only_type}" if only_type else "") + "\n")

    for ttype, specs in reg["domains"][dom].items():
        if only_type and ttype != only_type:
            continue
        curated = [s for s in specs if s.get("source") == "curated"]
        if tbl_filter:
            curated = [s for s in curated if s["gold"] in tbl_filter]
        if not curated:
            continue
        print(f"  [{ttype}]")
        for spec in curated:
            strat = spec.get("delta")
            fn = STRATS.get(strat)
            if not fn:
                print(f"    {spec['gold']}: no strategy '{strat}'"); continue
            try:
                fn(g, con, ts, dom, ttype, spec)
            except Exception as e:
                print(f"    {spec['gold']}: ERR {str(e)[:120]}")
    g.close()

    print("\n[sync log — this run]")
    for r in con.cursor().execute(
            "SELECT gold, strategy, n_new, n_changed, n_deleted, n_total FROM _gold_sync_log WHERE ts=? ORDER BY gold",
            (ts,)):
        print(f"    {r[0]:24s} {r[1]:13s} +{r[2]} ~{r[3]} -{r[4]} / {r[5]}")
    con.close()
    print("\nDONE.")


if __name__ == "__main__":
    main()
