"""
analyze_2026_phases.py
=====================
For the 2026-06-07 upgrade: (1) separate SPAM / tools / main stack, (2) find
post-import activities (XPRA/generation/SPAU/confirmation) and when they ran.
Reads Gold DB tpalog_upgrades/pat03/smodilog; one RFC read of E070 to time the
2026 SPAU adjustment transports.
"""
import sys, os, sqlite3
from datetime import datetime
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated

GOLD = os.path.join(os.path.dirname(__file__), "..",
                    "sap_data_extraction", "sqlite", "p01_gold_master_data.db")


def P(t): return datetime.strptime(t.zfill(14), "%Y%m%d%H%M%S")
def hm(t): return f"{t[8:10]}:{t[10:12]}"


def main():
    db = sqlite3.connect(GOLD); db.row_factory = sqlite3.Row
    comp = {r["PATCH"]: r["COMPONENT"] for r in db.execute("SELECT PATCH,COMPONENT FROM pat03")}
    sapk = [dict(r) for r in db.execute(
        "SELECT TRTIME,TRKORR,TRSTEP FROM tpalog_upgrades "
        "WHERE _win='2026-06' AND TRKORR LIKE 'SAPK%'")]

    def cat(tk):
        c = comp.get(tk, "")
        if tk.startswith("SAPKD") or c == "SAP_OCS":     return "SPAM tool (SAP_OCS)"
        if c in ("ST-PI", "ST-A/PI") or "ITAB" in tk:    return "Tools (ST-PI / ST-A-PI)"
        return "Main stack"

    print("=== 2026-06-07: queue content separated ===")
    g = defaultdict(list)
    for r in sapk:
        g[cat(r["TRKORR"])].append(r["TRTIME"])
    for k in sorted(g):
        ts = sorted(g[k])
        print(f"   {k:<26} steps={len(ts):>4} | {hm(ts[0])} -> {hm(ts[-1])}")
    sapkd = [r for r in sapk if r["TRKORR"].startswith("SAPKD")]
    print(f"   --> SPAM update packages (SAPKD*) present: {len(sapkd)}")
    tool_pkgs = sorted(set(r["TRKORR"] for r in sapk if cat(r["TRKORR"]) != "Main stack"))
    print(f"   tool packages: {', '.join(tool_pkgs)}")

    print("\n=== ALL TRSTEP codes on 2026-06-07 (ordered by first occurrence) ===")
    allr = [dict(r) for r in db.execute(
        "SELECT TRTIME,TRSTEP FROM tpalog_upgrades "
        "WHERE _win='2026-06' AND substr(TRTIME,1,8)='20260607'")]
    byst = defaultdict(list)
    for r in allr:
        byst[r["TRSTEP"]].append(r["TRTIME"])
    order = sorted(byst.keys(), key=lambda k: min(byst[k]))
    for st in order:
        ts = sorted(byst[st])
        print(f"   step='{st}': n={len(ts):>4} | {hm(ts[0])} -> {hm(ts[-1])}")

    print("\n=== activity AFTER main import (after 06:39 on 06-07, and later days) ===")
    for r in db.execute(
        "SELECT substr(TRTIME,1,8) d, COUNT(*) n, MIN(TRTIME) mn, MAX(TRTIME) mx "
        "FROM tpalog_upgrades WHERE _win='2026-06' AND TRTIME>'20260607063917' "
        "GROUP BY d ORDER BY d"):
        print(f"   {r['d']}: {r['n']:>4} steps | {hm(r['mn'])} -> {hm(r['mx'])}")

    # ---- SPAU adjustments for 2026: when (post-import?) ----
    smod = [dict(r) for r in db.execute(
        "SELECT TRKORR FROM smodilog WHERE TRIM(SPAU)<>'' AND TRIM(TRKORR)<>''")]
    spau_trk = set(r["TRKORR"] for r in smod)
    conn = get_connection("P01")
    e070 = rfc_read_paginated(conn, "E070", ["TRKORR", "AS4DATE", "AS4TIME", "AS4USER"],
                              [{"TEXT": "AS4DATE >= '20260601'"},
                               {"TEXT": "AND AS4DATE <= '20260615'"}],
                              batch_size=1_000_000, throttle=0)
    conn.close()
    spau_2026 = [r for r in e070 if r["TRKORR"] in spau_trk]
    print(f"\n=== 2026 SPAU adjustment transports (post-import work): {len(spau_2026)} ===")
    by_day = defaultdict(lambda: [None, None, 0])
    for r in spau_2026:
        k = r["AS4DATE"]
        t = r["AS4DATE"] + r["AS4TIME"]
        d = by_day[k]
        d[0] = t if d[0] is None else min(d[0], t)
        d[1] = t if d[1] is None else max(d[1], t)
        d[2] += 1
    for k in sorted(by_day):
        mn, mx, n = by_day[k]
        print(f"   {k[:4]}-{k[4:6]}-{k[6:8]}: {n:>3} transports | "
              f"{hm(mn)} -> {hm(mx)}")
    users = defaultdict(int)
    for r in spau_2026:
        users[r["AS4USER"].strip()] += 1
    print("   by user: " + ", ".join(f"{u}={n}" for u, n in
                                      sorted(users.items(), key=lambda x: -x[1])))
    db.close()


if __name__ == "__main__":
    main()
