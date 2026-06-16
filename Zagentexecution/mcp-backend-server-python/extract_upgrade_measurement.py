"""
extract_upgrade_measurement.py
==============================
Measure the last N upgrades of P01 (read-only, SNC/SSO).

Primary source: UVERS (release/EhP upgrade history) -> STARTDATE/ENDDATE per
component = "when it started" + duration + OLD->NEW release jump.
Enrichment:    PAT03 (every support package + IMPLE_DATE) = SP complexity.
State:         CVERS (current SP level per component) = the endpoint.

Persisted to Gold DB (provenance: P01 -> bare/ p01_ prefix). No ROWSKIPS
(this P01 wrapper forbids it) -> single-call reads via huge batch_size.
"""
import sys, os, sqlite3, json
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated

GOLD = os.path.join(os.path.dirname(__file__), "..",
                    "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
BIG = 1_000_000  # force single page -> ROWSKIPS stays 0


def read_full(conn, table, fields, where=""):
    return rfc_read_paginated(conn, table, fields, where,
                              batch_size=BIG, throttle=0)


def save(rows, table, cols):
    if not rows:
        print(f"  [skip] {table}: 0 rows")
        return
    db = sqlite3.connect(GOLD)
    db.execute(f'DROP TABLE IF EXISTS "{table}"')
    db.execute(f'CREATE TABLE "{table}" ({", ".join(c+" TEXT" for c in cols)})')
    db.executemany(
        f'INSERT INTO "{table}" VALUES ({",".join("?"*len(cols))})',
        [[r.get(c, "") for c in cols] for r in rows])
    db.commit(); db.close()
    print(f"  [saved] {table}: {len(rows):,} rows -> Gold DB")


def d(s):  # YYYYMMDD -> YYYY-MM-DD
    s = (s or "").strip()
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 and s != "00000000" else s


def main():
    conn = get_connection("P01")
    print("[OK] P01\n")

    # ---- 1. UVERS (upgrade history) ----
    uv_cols = ["COMPONENT", "NEWRELEASE", "STARTDATE", "STARTTIME",
               "ENDDATE", "ENDTIME", "PUTSTATUS", "PUTTYPE", "OLDRELEASE"]
    uvers = read_full(conn, "UVERS", uv_cols)
    save(uvers, "uvers", uv_cols)

    # ---- 2. PAT03 (support package history) ----
    p3_cols = ["PATCH", "COMPONENT", "COMP_REL", "FROM_REL", "TO_REL",
               "IMPLE_DATE", "IMPLE_TIME", "PATCH_TYPE"]
    pat03 = read_full(conn, "PAT03", p3_cols)
    save(pat03, "pat03", p3_cols)

    # ---- 3. CVERS (current stack) ----
    cv_cols = ["COMPONENT", "RELEASE", "EXTRELEASE", "COMP_TYPE"]
    cvers = read_full(conn, "CVERS", cv_cols)
    save(cvers, "cvers", cv_cols)

    conn.close()

    # ================= ANALYSIS =================
    print("\n" + "=" * 72)
    print("UPGRADE EVENTS (UVERS grouped by start/end window)")
    print("=" * 72)
    events = defaultdict(list)
    for r in uvers:
        key = (r["STARTDATE"], r["STARTTIME"], r["ENDDATE"], r["ENDTIME"], r["PUTTYPE"])
        events[key].append(r)
    # sort by start desc
    ordered = sorted(events.items(),
                     key=lambda kv: (kv[0][0], kv[0][1]), reverse=True)

    def dur(sd, st, ed, et):
        from datetime import datetime
        try:
            a = datetime.strptime(sd + st.zfill(6), "%Y%m%d%H%M%S")
            b = datetime.strptime(ed + et.zfill(6), "%Y%m%d%H%M%S")
            sec = (b - a).total_seconds()
            return f"{sec/3600:.1f} h ({sec/86400:.1f} d)"
        except Exception:
            return "?"

    summary = []
    for i, (k, rows) in enumerate(ordered):
        sd, st, ed, et, pt = k
        jumps = sorted(set(f"{r['OLDRELEASE']}->{r['NEWRELEASE']}"
                           for r in rows if r['OLDRELEASE'] != r['NEWRELEASE']))
        comps = sorted(set(r["COMPONENT"] for r in rows))
        # SPs applied in this window
        sps = [p for p in pat03 if sd <= p["IMPLE_DATE"] <= (ed or sd)]
        tag = "  <== LAST 3" if i < 3 else ""
        print(f"\n[{i}] {d(sd)} {st[:2]}:{st[2:4]} -> {d(ed)} {et[:2]}:{et[2:4]}"
              f"   dur={dur(sd, st, ed, et)}  PUTTYPE={pt}{tag}")
        print(f"     components moved: {len(comps)} | release jumps: {len(jumps)}")
        print(f"     jumps: {', '.join(jumps[:8])}{' ...' if len(jumps) > 8 else ''}")
        print(f"     support packages implemented in window: {len(sps)}")
        if i < 5:
            summary.append({
                "rank": i, "start": d(sd), "start_t": st, "end": d(ed),
                "end_t": et, "duration": dur(sd, st, ed, et), "puttype": pt,
                "components": len(comps), "release_jumps": jumps,
                "sps_in_window": len(sps),
                "component_list": comps})

    # PAT03 SP campaigns (by IMPLE_DATE cluster)
    print("\n" + "=" * 72)
    print("SUPPORT-PACKAGE CAMPAIGNS (PAT03 grouped by implementation date)")
    print("=" * 72)
    by_date = defaultdict(list)
    for p in pat03:
        if p["IMPLE_DATE"] and p["IMPLE_DATE"] != "00000000":
            by_date[p["IMPLE_DATE"]].append(p)
    for dt in sorted(by_date, reverse=True)[:12]:
        ps = by_date[dt]
        comps = sorted(set(p["COMPONENT"] for p in ps))
        print(f"  {d(dt)}: {len(ps):>3} SPs across {len(comps)} components "
              f"| e.g. {ps[0]['PATCH']} ({ps[0]['COMPONENT']})")

    print(f"\nCVERS: {len(cvers)} components in current stack")
    out = os.path.join(os.path.dirname(__file__), "upgrade_measurement.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"upgrade_events": summary,
                   "sp_campaigns": {d(k): len(v) for k, v in
                                    sorted(by_date.items(), reverse=True)[:20]},
                   "cvers_count": len(cvers)},
                  fh, indent=2, ensure_ascii=False)
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    main()
