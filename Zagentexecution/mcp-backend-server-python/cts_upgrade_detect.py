"""
cts_upgrade_detect.py -- SAP Upgrade / Support Package Detector
================================================================
SAP upgrades are characterized by:
  1. Very HIGH object count (typically 200–10,000+ objects per transport)
  2. Objects are ALL in SAP standard namespace (no Z/Y prefix)
  3. Transport owner = SAP, DDIC, BASIS or I-number service account
  4. TRKORR starts with SAPK*, SAPQ*, SM*, SI*, CE*, HR* etc.
  5. Objects are REPS/PROG/TABL etc. — all standard SAP object types

Strategy:
  - Score each transport on multiple signals (0-100)
  - Threshold >= 60: likely SAP upgrade/SP
  - Print distribution + top candidates

Run:
    python cts_upgrade_detect.py --input cts_10yr_raw.json
"""

import json
import argparse
import re
from collections import Counter, defaultdict

SAP_TRKORR_RE = re.compile(
    r'^(SAPK|SAPQ|SAP_|SAP\d|SM\d\d|SI\d|SW\d|CS\d|CE\d|HR\d|FI\d|CO\d|SD\d|MM\d|PP\d|'
    r'QM\d|PM\d|BC\d|ST\d|SB\d|SR\d|EP\d|XI\d|PI\d|BI\d|BW\d|CRM\d|SRM\d)',
    re.IGNORECASE,
)
SAP_OWNERS = {"SAP", "DDIC", "BASIS", "SAP_SUPPORT"}
SVC_ACCT   = re.compile(r'^I\d{6,}$', re.IGNORECASE)

# Object count thresholds
HIGH_OBJ_THRESHOLD  = 200   # Very likely upgrade
MED_OBJ_THRESHOLD   = 50    # Possibly upgrade


def score_transport(t: dict) -> tuple[int, list]:
    """Return (score 0-100, list of signals)."""
    score   = 0
    signals = []
    trkorr  = t.get("trkorr", "")
    owner   = t.get("owner", "").upper().strip()
    objs    = t.get("objects", [])
    obj_cnt = len(objs)

    # Signal 1: TRKORR naming pattern (30 pts)
    if SAP_TRKORR_RE.match(trkorr):
        score += 30
        signals.append(f"TRKORR pattern ({trkorr[:10]})")

    # Signal 2: Owner (20 pts)
    if owner in SAP_OWNERS:
        score += 20
        signals.append(f"SAP owner ({owner})")
    elif SVC_ACCT.match(owner):
        score += 10
        signals.append(f"Service acct ({owner})")

    # Signal 3: Object count (30 pts)
    if obj_cnt >= HIGH_OBJ_THRESHOLD:
        score += 30
        signals.append(f"High obj count ({obj_cnt})")
    elif obj_cnt >= MED_OBJ_THRESHOLD:
        score += 15
        signals.append(f"Med obj count ({obj_cnt})")

    # Signal 4: Namespace — SAP standard objects (no Z/Y) (20 pts)
    if obj_cnt > 0:
        z_count = sum(
            1 for o in objs
            if o.get("obj_name", "").upper().startswith(("Z", "Y", "/UN", "/IDF"))
        )
        sap_ratio = 1.0 - (z_count / obj_cnt)
        if sap_ratio >= 0.95:
            score += 20
            signals.append(f"Pure SAP namespace ({sap_ratio:.0%})")
        elif sap_ratio >= 0.80:
            score += 10
            signals.append(f"Mostly SAP namespace ({sap_ratio:.0%})")

    return min(score, 100), signals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="cts_10yr_raw.json")
    parser.add_argument("--threshold", type=int, default=60)
    args = parser.parse_args()

    print(f"\n  SAP UPGRADE DETECTOR")
    print(f"  Input    : {args.input}")
    print(f"  Threshold: score >= {args.threshold}")
    print("=" * 60)

    with open(args.input, encoding="utf-8") as f:
        raw = json.load(f)

    transports = raw.get("transports", [])
    print(f"  Loaded   : {len(transports)} transports")

    scored = []
    for t in transports:
        score, signals = score_transport(t)
        scored.append((score, t, signals))

    # Split: upgrades vs user
    upgrades = [(s, t, sig) for s, t, sig in scored if s >= args.threshold]
    user_chg = [(s, t, sig) for s, t, sig in scored if s <  args.threshold]

    upg_objs  = sum(t.get("obj_count", 0) for _, t, _ in upgrades)
    user_objs = sum(t.get("obj_count", 0) for _, t, _ in user_chg)
    total_obj = upg_objs + user_objs

    print(f"\n  RESULTS:")
    print(f"  {'Category':<22} {'Transports':>12} {'Objects':>12}  {'% of Objects':>12}")
    print(f"  {'-'*60}")
    print(f"  {'SAP Upgrade/SP':<22} {len(upgrades):>12,} {upg_objs:>12,}  {upg_objs/total_obj*100:>11.1f}%")
    print(f"  {'User-Driven Changes':<22} {len(user_chg):>12,} {user_objs:>12,}  {user_objs/total_obj*100:>11.1f}%")
    print(f"  {'TOTAL':<22} {len(transports):>12,} {total_obj:>12,}  {'100.0%':>12}")

    # Score distribution
    print(f"\n  SCORE DISTRIBUTION:")
    score_buckets = Counter((s // 10) * 10 for s, _, _ in scored)
    for bucket in sorted(score_buckets):
        bar = "#" * (score_buckets[bucket] // 10)
        marker = " <-- UPGRADE THRESHOLD" if bucket == (args.threshold // 10) * 10 else ""
        print(f"    Score {bucket:>3}-{bucket+9:<3}: {score_buckets[bucket]:>5}  {bar}{marker}")

    # Year breakdown: upgrades vs users
    print(f"\n  YEAR BREAKDOWN (SAP Upgrades identified):")
    by_year = defaultdict(lambda: {"upg": 0, "user": 0, "upg_obj": 0, "user_obj": 0})
    for s, t, _ in scored:
        year = t.get("date", "00000000")[:4]
        obj_c = t.get("obj_count", 0)
        if s >= args.threshold:
            by_year[year]["upg"]     += 1
            by_year[year]["upg_obj"] += obj_c
        else:
            by_year[year]["user"]     += 1
            by_year[year]["user_obj"] += obj_c

    print(f"    {'Year':<6} {'Upgrades':>9} {'Upg Obj':>10} {'User Trx':>10} {'User Obj':>10}")
    for year in sorted(by_year):
        d = by_year[year]
        print(f"    {year:<6} {d['upg']:>9,} {d['upg_obj']:>10,} {d['user']:>10,} {d['user_obj']:>10,}")

    # Top 20 upgrade candidates by score
    upgrades_sorted = sorted(upgrades, key=lambda x: (-x[0], -x[1].get("obj_count", 0)))
    print(f"\n  TOP 20 LIKELY SAP UPGRADES (by score + object count):")
    print(f"    {'Score':>6} {'TRKORR':<22} {'Owner':<15} {'Objects':>8}  Signals")
    for score, t, signals in upgrades_sorted[:20]:
        print(f"    {score:>6}  {t['trkorr']:<22} {t['owner']:<15} {t.get('obj_count',0):>8}  {', '.join(signals)}")

    # Recalculate UNKNOWN bucket from the original analysis
    unknown_now = [t for _, t, _ in scored if t.get("_classification", "") == "UNKNOWN" or True]

    print(f"\n  SIGNAL MIX for upgrade candidates:")
    sig_counter = Counter()
    for _, _, sigs in upgrades:
        for s in sigs:
            # Normalize to signal type
            if "TRKORR" in s:   sig_counter["TRKORR pattern"] += 1
            elif "owner" in s.lower(): sig_counter["SAP owner"] += 1
            elif "obj count" in s.lower(): sig_counter["High obj count"] += 1
            elif "namespace" in s.lower(): sig_counter["SAP namespace"] += 1
    for sig, cnt in sig_counter.most_common():
        print(f"    {sig:<25} {cnt:>6}")

    print(f"\n  RECOMMENDATION:")
    if upg_objs / total_obj > 0.5:
        print(f"  WARNING: SAP upgrades account for {upg_objs/total_obj*100:.1f}% of objects!")
        print(f"  The dashboard 'objects changed' KPI is dominated by SAP-delivered content.")
        print(f"  Consider filtering upgrades OUT when measuring team productivity.")
    else:
        print(f"  SAP upgrades represent {upg_objs/total_obj*100:.1f}% of objects —")
        print(f"  {user_objs/total_obj*100:.1f}% ({user_objs:,} objects) are genuine user-driven changes.")


if __name__ == "__main__":
    main()
