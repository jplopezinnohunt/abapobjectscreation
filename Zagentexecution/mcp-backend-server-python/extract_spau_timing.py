"""
extract_spau_timing.py
======================
Measure, per upgrade: (A) SPAU impact (custom-code re-adjustments, from
SMODILOG) and (B) real elapsed time of the import (from TPALOG per-step
timestamps). Read-only P01 SNC/SSO, single-call reads (no ROWSKIPS).
"""
import sys, os, sqlite3, json
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated

GOLD = os.path.join(os.path.dirname(__file__), "..",
                    "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
BIG = 1_000_000

WINDOWS = {  # label: (date_yyyymmdd_start, end) for TPALOG TRTIME + E070 dating
    "2026-06": ("20260601", "20260615"),
    "2024-07": ("20240701", "20240715"),
    "2023-06": ("20230601", "20230620"),
    "2017-03": ("20170320", "20170405"),
}


def read_full(conn, table, fields, where=""):
    return rfc_read_paginated(conn, table, fields, where, batch_size=BIG, throttle=0)


def save(rows, table, cols):
    db = sqlite3.connect(GOLD)
    db.execute(f'DROP TABLE IF EXISTS "{table}"')
    db.execute(f'CREATE TABLE "{table}" ({", ".join(c+" TEXT" for c in cols)})')
    db.executemany(f'INSERT INTO "{table}" VALUES ({",".join("?"*len(cols))})',
                   [[r.get(c, "") for c in cols] for r in rows])
    db.commit(); db.close()
    print(f"  [saved] {table}: {len(rows):,} rows")


def hhmm(t):
    t = (t or "").zfill(6)
    return f"{t[:2]}:{t[2:4]}:{t[4:6]}"


def main():
    conn = get_connection("P01")
    print("[OK] P01\n")

    # ---- (A) SMODILOG (SPAU modification log) ----
    sm_cols = ["OBJ_TYPE", "OBJ_NAME", "MOD_DATE", "MOD_TIME", "MOD_USER",
               "UPGRADE", "SPAU", "TRKORR"]
    smod = read_full(conn, "SMODILOG", sm_cols)
    save(smod, "smodilog", sm_cols)

    # ---- (B) TPALOG per window (real import timing) ----
    tp_cols = ["TRTIME", "TRKORR", "TRSTEP", "RETCODE", "TRUSER", "TARSYSTEM"]
    all_tp = []
    for label, (a, b) in WINDOWS.items():
        rows = read_full(conn, "TPALOG", tp_cols,
                         [{"TEXT": f"TRTIME >= '{a}000000'"},
                          {"TEXT": f"AND TRTIME <= '{b}000000'"}])
        for r in rows:
            r["_win"] = label
        all_tp += rows
        print(f"  TPALOG {label}: {len(rows)} steps")
    save(all_tp, "tpalog_upgrades", tp_cols + ["_win"])

    # ---- date E070 for SMODILOG adjustment transports ----
    spau_trkorr = sorted(set(r["TRKORR"] for r in smod
                             if r["SPAU"].strip() and r["TRKORR"].strip()))
    e070 = {}
    for tk in spau_trkorr:
        rs = read_full(conn, "E070", ["TRKORR", "AS4DATE", "AS4USER"],
                       f"TRKORR = '{tk}'")
        if rs:
            e070[tk] = rs[0]
    conn.close()

    # ================= ANALYSIS =================
    print("\n" + "=" * 72)
    print("SPAU IMPACT (SMODILOG)")
    print("=" * 72)
    total = len(smod)
    spau_flag = [r for r in smod if r["SPAU"].strip()]
    upg_flag = [r for r in smod if r["UPGRADE"].strip()]
    print(f"  total modifications logged : {total}")
    print(f"  flagged SPAU-relevant      : {len(spau_flag)}")
    print(f"  flagged UPGRADE-touched    : {len(upg_flag)}")

    # modifications by MOD_DATE year-month (adjustment activity clusters)
    print("\n  modification/adjustment activity by year-month (top):")
    ym = Counter(r["MOD_DATE"][:6] for r in smod if r["MOD_DATE"].strip()
                 and r["MOD_DATE"] != "00000000")
    for k, v in sorted(ym.items(), reverse=True)[:14]:
        bar = "#" * min(v, 50)
        print(f"    {k[:4]}-{k[4:6]}: {v:>4}  {bar}")

    # SPAU adjustments bucketed by adjustment-transport date (the real per-upgrade count)
    print("\n  SPAU adjustments grouped by adjustment-transport date (E070):")
    by_adj = defaultdict(int)
    for r in spau_flag:
        tk = r["TRKORR"]
        d = e070.get(tk, {}).get("AS4DATE", "")
        if d:
            by_adj[d[:6]] += 1
    for k, v in sorted(by_adj.items(), reverse=True):
        print(f"    {k[:4]}-{k[4:6]}: {v} adjustments")

    print("\n" + "=" * 72)
    print("REAL IMPORT TIMING (TPALOG min->max TRTIME per window)")
    print("=" * 72)
    res_timing = {}
    for label in WINDOWS:
        rows = [r for r in all_tp if r["_win"] == label]
        if not rows:
            print(f"  {label}: no TPALOG rows"); continue
        ts = sorted(r["TRTIME"] for r in rows if r["TRTIME"].strip())
        sp = [r for r in rows if r["TRKORR"].startswith("SAPK")]
        sp_ts = sorted(r["TRTIME"] for r in sp if r["TRTIME"].strip())
        from datetime import datetime
        def parse(t): return datetime.strptime(t.zfill(14), "%Y%m%d%H%M%S")
        span = parse(ts[-1]) - parse(ts[0])
        line = (f"  {label}: {len(rows)} steps | window "
                f"{ts[0][8:10]}:{ts[0][10:12]} {ts[0][:8]} -> "
                f"{ts[-1][8:10]}:{ts[-1][10:12]} {ts[-1][:8]} | "
                f"elapsed {span.total_seconds()/3600:.1f} h")
        print(line)
        if sp_ts:
            spspan = parse(sp_ts[-1]) - parse(sp_ts[0])
            print(f"        SP transports (SAPK*) only: {len(sp)} steps, "
                  f"{spspan.total_seconds()/3600:.1f} h")
        # distinct days touched
        days = sorted(set(t[:8] for t in ts))
        print(f"        days touched: {len(days)} ({', '.join(days)})")
        res_timing[label] = {
            "steps": len(rows), "elapsed_h": round(span.total_seconds()/3600, 1),
            "start": ts[0], "end": ts[-1], "days": days,
            "sp_steps": len(sp)}

    out = os.path.join(os.path.dirname(__file__), "spau_timing.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"smodilog_total": total, "spau_flag": len(spau_flag),
                   "upgrade_flag": len(upg_flag),
                   "spau_by_adj_month": dict(by_adj),
                   "mod_activity_by_month": dict(ym),
                   "timing": res_timing}, fh, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {out}")


if __name__ == "__main__":
    main()
