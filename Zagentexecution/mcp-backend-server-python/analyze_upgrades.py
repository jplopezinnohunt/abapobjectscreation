"""
analyze_upgrades.py
===================
Cluster P01 PAT03 support-package history into UPGRADE CAMPAIGNS, enrich with
SHORT_TEXT/STATUS, and produce a complexity scorecard for the last N campaigns.

Reads pat03/uvers/cvers already in the Gold DB; pulls PAT03 text fields once.
A "campaign" = PAT03 implementations whose IMPLE_DATE are within GAP days of
each other (one maintenance/upgrade project, possibly spanning a few days).
"""
import sys, os, sqlite3, json
from collections import defaultdict
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated

GOLD = os.path.join(os.path.dirname(__file__), "..",
                    "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
GAP = 10  # days; implementations within GAP merge into one campaign


def d(s):
    s = (s or "").strip()
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 and s != "00000000" else s


def is_sap_sp(patch):
    """True = real SAP support package (SAPK*), False = adjustment/customer transport."""
    return patch.startswith("SAPK")


def main():
    db = sqlite3.connect(GOLD); db.row_factory = sqlite3.Row
    pat03 = [dict(r) for r in db.execute("SELECT * FROM pat03")]
    cvers = [dict(r) for r in db.execute("SELECT * FROM cvers")]

    # ---- enrich with SHORT_TEXT / STATUS (one RFC read) ----
    conn = get_connection("P01")
    txt = rfc_read_paginated(conn, "PAT03",
                             ["PATCH", "COMPONENT", "SHORT_TEXT", "STATUS", "CONFIRMED"],
                             "", batch_size=1_000_000, throttle=0)
    conn.close()
    tmap = {(t["PATCH"], t["COMPONENT"]): t for t in txt}
    for p in pat03:
        t = tmap.get((p["PATCH"], p["COMPONENT"]), {})
        p["SHORT_TEXT"] = t.get("SHORT_TEXT", "")
        p["STATUS"] = t.get("STATUS", "")
        p["CONFIRMED"] = t.get("CONFIRMED", "")

    # ---- cluster into campaigns by IMPLE_DATE proximity ----
    dated = [p for p in pat03 if p["IMPLE_DATE"] and p["IMPLE_DATE"] != "00000000"]
    dated.sort(key=lambda p: p["IMPLE_DATE"])
    campaigns = []
    cur = []
    last = None
    for p in dated:
        dt = datetime.strptime(p["IMPLE_DATE"], "%Y%m%d")
        if last and (dt - last) > timedelta(days=GAP):
            campaigns.append(cur); cur = []
        cur.append(p); last = dt
    if cur:
        campaigns.append(cur)
    campaigns.sort(key=lambda c: c[0]["IMPLE_DATE"], reverse=True)

    def scorecard(ps):
        sps = [p for p in ps if is_sap_sp(p["PATCH"])]
        adj = [p for p in ps if not is_sap_sp(p["PATCH"])]
        comps = sorted(set(p["COMPONENT"] for p in sps if p["COMPONENT"]))
        dates = sorted(set(p["IMPLE_DATE"] for p in ps))
        # biggest jumps per component (FROM_REL->TO_REL)
        jumps = {}
        for p in sps:
            c = p["COMPONENT"]
            if c and p["FROM_REL"] != p["TO_REL"]:
                jumps.setdefault(c, (p["FROM_REL"], p["TO_REL"]))
        return {
            "start": d(dates[0]), "end": d(dates[-1]),
            "span_days": (datetime.strptime(dates[-1], "%Y%m%d") -
                          datetime.strptime(dates[0], "%Y%m%d")).days + 1,
            "sap_support_packages": len(sps),
            "adjustment_transports": len(adj),
            "components": len(comps),
            "component_list": comps,
            "release_jumps": {k: f"{v[0]}->{v[1]}" for k, v in sorted(jumps.items())},
            "key_components": {c: next((p["SHORT_TEXT"] for p in sps
                                        if p["COMPONENT"] == c and p["SHORT_TEXT"]), "")
                               for c in ["SAP_BASIS", "SAP_ABA", "SAP_APPL", "SAP_HR",
                                         "SAP_BW", "EA-HR", "EA-APPL"] if c in comps},
            "confirmed": sum(1 for p in sps if p["CONFIRMED"] == "C"),
        }

    print("=" * 74)
    print(f"UPGRADE CAMPAIGNS (gap<= {GAP}d). Total campaigns: {len(campaigns)}")
    print("=" * 74)
    out = []
    for i, c in enumerate(campaigns[:8]):
        sc = scorecard(c)
        tag = "   <<< LAST 3" if i < 3 else ""
        print(f"\n[{i}] {sc['start']} -> {sc['end']}  ({sc['span_days']}d){tag}")
        print(f"    SAP support packages : {sc['sap_support_packages']}")
        print(f"    adjustment transports: {sc['adjustment_transports']}  "
              f"(SPDD/SPAU + customer content proxy)")
        print(f"    components touched   : {sc['components']}")
        print(f"    confirmed SPs        : {sc['confirmed']}/{sc['sap_support_packages']}")
        keyj = {k: v for k, v in sc["release_jumps"].items()
                if k in ("SAP_BASIS", "SAP_ABA", "SAP_APPL", "SAP_HR", "SAP_BW",
                         "SAP_GWFND", "SAP_UI", "EA-HR", "EA-APPL", "ST-PI", "ST-A/PI")}
        if keyj:
            print(f"    key release jumps    : " +
                  ", ".join(f"{k} {v}" for k, v in keyj.items()))
        out.append({"rank": i, **sc})

    # current stack highlights
    cstack = {r["COMPONENT"]: f"{r['RELEASE']} SP{r['EXTRELEASE']}" for r in cvers}
    print("\n" + "=" * 74)
    print("CURRENT STACK (CVERS) — key components")
    print("=" * 74)
    for c in ["SAP_BASIS", "SAP_ABA", "SAP_APPL", "SAP_HR", "SAP_HRCAR", "SAP_BW",
              "SAP_GWFND", "SAP_UI", "EA-HR", "EA-APPL", "EA-FINSERV"]:
        if c in cstack:
            print(f"    {c:<14} {cstack[c]}")

    res = os.path.join(os.path.dirname(__file__), "upgrade_campaigns.json")
    with open(res, "w", encoding="utf-8") as fh:
        json.dump({"campaigns": out,
                   "current_stack": cstack,
                   "uvers_release_upgrade": "EhP8 2017-03-24->2017-03-31 (160 comps)"},
                  fh, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {res}")
    db.close()


if __name__ == "__main__":
    main()
