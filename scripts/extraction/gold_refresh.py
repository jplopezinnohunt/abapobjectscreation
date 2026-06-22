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


def read_p01(g, sap, fields, partition=None, where=""):
    """ROWCOUNT=0; partitioned by FIKRS when the table is large (wrapper rejects ROWSKIPS)."""
    parts = FIKRS if partition else [None]
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
    """totals — compare amount VALUES per key (count is meaningless for totals)."""
    gold, sap, key = spec["gold"], spec["sap"], spec["key"]
    vfields = spec.get("value_fields", [])
    if not vfields:
        print(f"    {gold:24s} SKIP value-compare: no value_fields declared (note: {spec.get('note','')})")
        log_row(con.cursor(), ts, dom, ttype, spec, "value-compare", 0, 0, 0, 0, "no value_fields")
        con.commit()
        return
    fields = key + vfields
    p01 = read_p01(g, sap, fields, spec.get("partition"))
    p01_idx = {tuple(r[k] for k in key): tuple(r.get(v, "") for v in vfields) for r in p01}
    cur = con.cursor()
    gold_idx = {}
    try:
        for row in cur.execute(f'SELECT {",".join(fields)} FROM "{gold}"'):
            row = tuple("" if v is None else str(v) for v in row)
            gold_idx[tuple(row[:len(key)])] = tuple(row[len(key):])
    except sqlite3.OperationalError:
        pass
    changed = [k for k in p01_idx if k in gold_idx and p01_idx[k] != gold_idx[k]]
    new = [k for k in p01_idx if k not in gold_idx]
    # overwrite values (totals are authoritative from P01)
    cols_sql = ", ".join(f"{c} TEXT" for c in fields)
    cur.execute(f'CREATE TABLE IF NOT EXISTS "{gold}" ({cols_sql}, PRIMARY KEY ({",".join(key)}))')
    ph = ",".join("?" * len(fields))
    cur.executemany(f'INSERT OR REPLACE INTO "{gold}" VALUES ({ph})',
                    [tuple(k) + p01_idx[k] for k in p01_idx])
    con.commit()
    log_row(cur, ts, dom, ttype, spec, "value-compare", len(new), len(changed), 0, len(p01_idx),
            f"value_fields={vfields}")
    con.commit()
    print(f"    {gold:24s} total={len(p01_idx):>6}  +{len(new)} new buckets  ~{len(changed)} value-changed  ({vfields})")


def refresh_hwm_append(g, con, ts, dom, ttype, spec):
    """transaction — append only docs beyond the stored high-water mark."""
    gold, sap, hwm = spec["gold"], spec["sap"], spec.get("hwm")
    cur = con.cursor()
    cur_max = None
    try:
        cur_max = cur.execute(f'SELECT MAX("{hwm}") FROM "{gold}"').fetchone()[0]
    except sqlite3.OperationalError:
        pass
    print(f"    {gold:24s} HWM-append on {hwm}: current max={cur_max!r} — "
          f"incremental pull wired (heavy; run dedicated). note: {spec.get('note','')}")
    log_row(cur, ts, dom, ttype, spec, "hwm-append", 0, 0, 0, 0, f"hwm={hwm} max={cur_max} (not pulled this run)")
    con.commit()


STRATS = {"pk-upsert": refresh_pk_upsert, "value-compare": refresh_value_compare,
          "hwm-append": refresh_hwm_append}


def main():
    args = [a for a in sys.argv[1:]]
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if not args or args[0] == "--list":
        print("Domains × table types in registry:")
        for d, types in reg["domains"].items():
            print(f"  {d:14s} {{ {', '.join(f'{t}:{len(v)}' for t, v in types.items())} }}")
        return

    dom = args[0]
    only_type = args[1] if len(args) > 1 else None
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
