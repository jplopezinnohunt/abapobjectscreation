"""
fm_ps_pool_health_matrix.py
============================
UNESCO-wide cross-engine availability matrix.

Extends inc5638_fm_ps_avc_misalignment.py (which only covers HARD-linked
donor funds, TYPE 101-112, ~73% of the universe) to ALL fund TYPEs by
classifying every (Fund, WBS) pair posting in 2024-2026 into 4 link tiers
and 4 health states.

LINK CLASSIFICATION (4 tiers):
  HARD          POSID(10) = GEBER, fund TYPE 101-112 (Earmarked donor)
  DERIVED       Single (Fund, WBS) per WBS, no hard-link
  DERIVED-MULTI WBS has 2-10 funds (proportional allocation by consumption)
  OUTLIER       WBS has >10 funds (common-cost / overhead — single-pool view N/A)

POOL COMPUTATION (per pair, year=2026):
  PS pool  = SUM(BPJA WRTTP=41 WTJHR for OBJNR=this WBS, GJAHR=2026)
              - SUM(COEP WKGBTR for OBJNR=this WBS, GJAHR=2026, WRTTP IN ('04','11'))
              - SUM(COOI WKGBTR for OBJNR=this WBS, GJAHR=2026)
              -- For DERIVED-MULTI: PS pool * fund_proportion_of_consumption
  FM pool  = MIN over each (Fund, FundCenter, CommItem) bucket the WBS posts to:
              SUM(FMIFIIT FKBTR for FONDS=fund, GJAHR=2026, WRTTP=66)   (revenue)
              - SUM(FMIFIIT FKBTR for FONDS=fund, GJAHR=2026, WRTTP=54) (consumption)

STATE (per pair):
  ALIGNED        both > 0
  FM-EXHAUSTED   PS > 0, FM <= 0   <- INC-005638 class
  PS-EXHAUSTED   FM > 0, PS <= 0
  BOTH-EXHAUSTED both <= 0

Outputs:
  - Zagentexecution/quality_checks/fm_ps_pool_health_matrix.csv          (1 row per non-outlier pair)
  - Zagentexecution/quality_checks/fm_ps_pool_health_matrix_outliers.csv (multi-fund WBSs)

Usage:
    python fm_ps_pool_health_matrix.py
"""

from __future__ import annotations

import csv
import os
import sqlite3
import sys
from collections import defaultdict

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD_DB = os.path.join(
    PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
    "p01_gold_master_data.db",
)
OUT_CSV = os.path.join(
    PROJECT_ROOT, "Zagentexecution", "quality_checks",
    "fm_ps_pool_health_matrix.csv",
)
OUT_OUTLIERS = os.path.join(
    PROJECT_ROOT, "Zagentexecution", "quality_checks",
    "fm_ps_pool_health_matrix_outliers.csv",
)

YEAR = "2026"
YEARS_RANGE = ("2024", "2025", "2026")


def _signed(s: str | None) -> float:
    """SAP-format signed number: '123.45-' -> -123.45 ; '123.45' -> 123.45."""
    s = (s or "").strip()
    if not s:
        return 0.0
    if s.endswith("-"):
        try:
            return -float(s[:-1].replace(" ", "").replace(",", ""))
        except ValueError:
            return 0.0
    try:
        return float(s.replace(" ", "").replace(",", ""))
    except ValueError:
        return 0.0


def main() -> int:
    db = sqlite3.connect(GOLD_DB)
    db.row_factory = sqlite3.Row
    print("=" * 72)
    print("  FM-PS POOL HEALTH MATRIX  —  build", YEAR)
    print("=" * 72)

    # ------------------------------------------------------------------
    # 1. Fund master — TYPE lookup
    # ------------------------------------------------------------------
    print("[1/8] Loading fund master (TYPE) ...")
    fund_type: dict[str, str] = {}
    for r in db.execute(
        "SELECT FINCODE, TYPE FROM funds WHERE FIKRS='UNES' OR FIKRS=''"
    ):
        fund_type[(r["FINCODE"] or "").strip()] = (r["TYPE"] or "").strip()
    print(f"      {len(fund_type)} funds loaded")

    # ------------------------------------------------------------------
    # 2. Universe of (Fund, WBS-OBJNR) pairs with COEP postings 2024-2026
    # ------------------------------------------------------------------
    print("[2/8] Building universe of (Fund, WBS) pairs from COEP 2024-2026 ...")
    # postings_count and last_posting_date per (fund, objnr)
    pair_postings: dict[tuple[str, str], dict] = {}
    for r in db.execute(f"""
        SELECT GEBER, OBJNR, COUNT(*) AS n,
               MAX(SUBSTR(BELNR,1,1) || GJAHR || PERIO) AS proxy_date
        FROM coep
        WHERE GJAHR IN ({",".join("?"*len(YEARS_RANGE))})
          AND GEBER IS NOT NULL AND GEBER != ''
          AND OBJNR LIKE 'PR%'
        GROUP BY GEBER, OBJNR
    """, YEARS_RANGE):
        f = (r["GEBER"] or "").strip()
        o = (r["OBJNR"] or "").strip()
        pair_postings[(f, o)] = {
            "n": r["n"],
            "proxy_date": r["proxy_date"] or "",
        }
    print(f"      {len(pair_postings)} (Fund, WBS) pairs in universe")

    # Per-WBS: number of distinct funds + per-pair fund consumption share
    wbs_fund_share: dict[str, dict[str, float]] = defaultdict(dict)
    for r in db.execute(f"""
        SELECT GEBER, OBJNR, WKGBTR
        FROM coep
        WHERE GJAHR IN ({",".join("?"*len(YEARS_RANGE))})
          AND GEBER IS NOT NULL AND GEBER != ''
          AND OBJNR LIKE 'PR%'
          AND WRTTP IN ('04','11')
    """, YEARS_RANGE):
        f = (r["GEBER"] or "").strip()
        o = (r["OBJNR"] or "").strip()
        v = abs(_signed(r["WKGBTR"]))
        wbs_fund_share[o][f] = wbs_fund_share[o].get(f, 0.0) + v

    wbs_fund_count: dict[str, int] = {o: len(d) for o, d in wbs_fund_share.items()}
    # singletons WBS we might have missed (no WRTTP 04/11 yet)
    for (f, o) in pair_postings.keys():
        if o not in wbs_fund_count:
            wbs_fund_count[o] = 1
            wbs_fund_share[o][f] = 1.0

    # ------------------------------------------------------------------
    # 3. WBS master (POSID + POST1)
    # ------------------------------------------------------------------
    print("[3/8] Loading WBS master (prps) ...")
    wbs_master: dict[str, dict] = {}
    for r in db.execute(
        "SELECT OBJNR, POSID, POST1 FROM prps WHERE OBJNR LIKE 'PR%'"
    ):
        wbs_master[r["OBJNR"]] = {
            "POSID": (r["POSID"] or "").strip(),
            "POST1": (r["POST1"] or "").strip(),
        }
    print(f"      {len(wbs_master)} WBSs loaded")

    # ------------------------------------------------------------------
    # 4. PS POOL — per WBS for YEAR
    #    PS pool = budget - actuals - commitments  (all GJAHR=YEAR)
    # ------------------------------------------------------------------
    print(f"[4/8] Computing PS pool per WBS for GJAHR={YEAR} ...")
    ps_budget: dict[str, float] = defaultdict(float)
    ps_actuals: dict[str, float] = defaultdict(float)
    ps_cmt: dict[str, float] = defaultdict(float)

    # Budget (BPJA WRTTP=41)
    for r in db.execute(
        f"SELECT OBJNR, WTJHR FROM bpja_{YEAR} "
        f"WHERE WRTTP='41' AND OBJNR LIKE 'PR%'"
    ):
        ps_budget[r["OBJNR"]] += _signed(r["WTJHR"])

    # Actuals (COEP WRTTP IN 04, 11) — note: WKGBTR for actuals is signed
    for r in db.execute(
        "SELECT OBJNR, WKGBTR FROM coep "
        "WHERE GJAHR=? AND WRTTP IN ('04','11') AND OBJNR LIKE 'PR%'",
        (YEAR,),
    ):
        # Posting expense -> WKGBTR positive; flip to subtract from pool
        ps_actuals[r["OBJNR"]] += _signed(r["WKGBTR"])

    # Commitments (COOI)
    for r in db.execute(
        "SELECT OBJNR, WKGBTR FROM cooi "
        "WHERE GJAHR=? AND OBJNR LIKE 'PR%'",
        (YEAR,),
    ):
        ps_cmt[r["OBJNR"]] += _signed(r["WKGBTR"])

    # Note on signs: SAP convention — costs are stored positive in WKGBTR;
    # budget WTJHR is positive; pool = budget - costs - cmt
    ps_pool: dict[str, float] = {}
    for o in wbs_master:
        ps_pool[o] = ps_budget.get(o, 0.0) - ps_actuals.get(o, 0.0) - ps_cmt.get(o, 0.0)
    print(f"      computed PS pool for {len(ps_pool)} WBSs")

    # ------------------------------------------------------------------
    # 5. FM POOL — per (Fund, FundCenter, CommItem) bucket for YEAR
    # ------------------------------------------------------------------
    print(f"[5/8] Computing FM pool per (Fund, FC, FIPEX) bucket for GJAHR={YEAR} ...")
    fm_revenue: dict[tuple[str, str, str], float] = defaultdict(float)
    fm_consumption: dict[tuple[str, str, str], float] = defaultdict(float)
    for r in db.execute(
        "SELECT FONDS, FISTL, FIPEX, WRTTP, FKBTR FROM fmifiit_full "
        "WHERE GJAHR=? AND BUKRS='UNES' AND WRTTP IN ('54','66')",
        (YEAR,),
    ):
        key = (
            (r["FONDS"] or "").strip(),
            (r["FISTL"] or "").strip(),
            (r["FIPEX"] or "").strip(),
        )
        v = _signed(r["FKBTR"])
        if r["WRTTP"] == "66":
            fm_revenue[key] += v
        else:  # 54
            fm_consumption[key] += v

    # Per-fund bucket pools
    fund_buckets: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    all_keys = set(fm_revenue.keys()) | set(fm_consumption.keys())
    for key in all_keys:
        fund, fc, fipex = key
        if not fund:
            continue
        pool = fm_revenue.get(key, 0.0) - fm_consumption.get(key, 0.0)
        fund_buckets[fund].append((fc, fipex, pool))

    # ------------------------------------------------------------------
    # 6. WBS -> set of (Fund, FC, FIPEX) buckets actually used in YEAR
    # ------------------------------------------------------------------
    print(f"[6/8] Mapping each WBS to its (Fund, FC, FIPEX) buckets via FMIFIIT ...")
    wbs_buckets: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    # OBJNRZ in fmifiit_full holds the WBS objnr for AVC-relevant rows
    for r in db.execute(
        "SELECT FONDS, FISTL, FIPEX, OBJNRZ FROM fmifiit_full "
        "WHERE GJAHR=? AND BUKRS='UNES' AND WRTTP IN ('54','66')"
        "  AND OBJNRZ LIKE 'PR%'",
        (YEAR,),
    ):
        f = (r["FONDS"] or "").strip()
        o = (r["OBJNRZ"] or "").strip()
        wbs_buckets[(f, o)].add((
            (r["FISTL"] or "").strip(),
            (r["FIPEX"] or "").strip(),
        ))
    print(f"      mapped {len(wbs_buckets)} (Fund, WBS) pairs to FM buckets")

    # ------------------------------------------------------------------
    # 7. Tier classification + state computation
    # ------------------------------------------------------------------
    print("[7/8] Classifying tiers and states ...")

    state_counts = {"ALIGNED": 0, "FM-EXHAUSTED": 0, "PS-EXHAUSTED": 0,
                    "BOTH-EXHAUSTED": 0}
    tier_counts = {"HARD": 0, "DERIVED": 0, "DERIVED-MULTI": 0, "OUTLIER": 0}

    rows: list[dict] = []
    outlier_rows: list[dict] = []

    for (fund, objnr), pinfo in pair_postings.items():
        if not fund or not objnr:
            continue
        nfunds = wbs_fund_count.get(objnr, 1)
        wbs = wbs_master.get(objnr, {"POSID": "", "POST1": ""})
        ftype = fund_type.get(fund, "")

        # Outliers (>10 funds) — separate file
        if nfunds > 10:
            tier_counts["OUTLIER"] += 1
            total_consumption = sum(wbs_fund_share.get(objnr, {}).values())
            outlier_rows.append({
                "wbs_objnr": objnr,
                "wbs_posid": wbs["POSID"],
                "wbs_post1": wbs["POST1"],
                "fund": fund,
                "fund_type": ftype,
                "fund_count_on_wbs": nfunds,
                "fund_consumption_2024_26": round(
                    wbs_fund_share.get(objnr, {}).get(fund, 0.0), 2),
                "total_consumption_2024_26": round(total_consumption, 2),
                "fund_share_pct": round(
                    100.0 * wbs_fund_share.get(objnr, {}).get(fund, 0.0)
                    / total_consumption, 2) if total_consumption else 0.0,
                "postings_count_2024_26": pinfo["n"],
            })
            continue

        # Determine tier
        is_hard = False
        try:
            posid_10 = wbs["POSID"][:10] if wbs["POSID"] else ""
            ftype_int = int(ftype) if ftype else 0
            if posid_10 == fund and 101 <= ftype_int <= 112:
                is_hard = True
        except (ValueError, TypeError):
            pass

        if is_hard:
            tier = "HARD"
        elif nfunds == 1:
            tier = "DERIVED"
        else:
            tier = "DERIVED-MULTI"
        tier_counts[tier] += 1

        # FM pool — MIN across buckets WBS uses for this fund
        bks = wbs_buckets.get((fund, objnr), set())
        # Fallback: if WBS->bucket map empty, use ALL buckets for this fund
        bucket_pools: list[tuple[str, str, float]] = []
        if bks:
            for (fc, fipex) in bks:
                pool = (fm_revenue.get((fund, fc, fipex), 0.0)
                        - fm_consumption.get((fund, fc, fipex), 0.0))
                bucket_pools.append((fc, fipex, pool))
        if not bucket_pools:
            bucket_pools = fund_buckets.get(fund, [])

        if bucket_pools:
            fm_pool = min(p for _, _, p in bucket_pools)
            blocking = min(bucket_pools, key=lambda x: x[2])
            fm_blocking_bucket = f"{blocking[0]}/{blocking[1]}"
        else:
            fm_pool = 0.0
            fm_blocking_bucket = ""

        # PS pool — full WBS pool for DERIVED / HARD; proportional for DERIVED-MULTI
        ps_pool_for_pair = ps_pool.get(objnr, 0.0)
        if tier == "DERIVED-MULTI":
            shares = wbs_fund_share.get(objnr, {})
            tot = sum(shares.values())
            if tot > 0:
                ps_pool_for_pair *= shares.get(fund, 0.0) / tot

        # State
        ps_pos = ps_pool_for_pair > 0
        fm_pos = fm_pool > 0
        if ps_pos and fm_pos:
            state = "ALIGNED"
        elif ps_pos and not fm_pos:
            state = "FM-EXHAUSTED"
        elif fm_pos and not ps_pos:
            state = "PS-EXHAUSTED"
        else:
            state = "BOTH-EXHAUSTED"
        state_counts[state] += 1

        # severity rank: most negative = worst
        worst_pool = min(ps_pool_for_pair, fm_pool)
        rows.append({
            "fund": fund,
            "fund_type": ftype,
            "fund_desc": "",  # no desc field in funds master; left for future enrichment
            "wbs_objnr": objnr,
            "wbs_posid": wbs["POSID"],
            "wbs_post1": wbs["POST1"],
            "link_tier": tier,
            "ps_pool_2026": round(ps_pool_for_pair, 2),
            "fm_pool_2026_min": round(fm_pool, 2),
            "fm_blocking_bucket": fm_blocking_bucket,
            "state": state,
            "deficit_severity_rank": round(worst_pool, 2),
            "postings_count_2024_26": pinfo["n"],
            "wbs_fund_count": nfunds,
        })

    # severity rank ordering: most negative => rank 1
    rows_sorted_severity = sorted(rows, key=lambda r: r["deficit_severity_rank"])
    for i, rr in enumerate(rows_sorted_severity, start=1):
        rr["deficit_severity_rank"] = i

    # ------------------------------------------------------------------
    # 8. Write CSVs + summary
    # ------------------------------------------------------------------
    print("[8/8] Writing CSVs ...")
    if rows:
        with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"      wrote {len(rows)} pair rows -> {OUT_CSV}")

    if outlier_rows:
        with open(OUT_OUTLIERS, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(outlier_rows[0].keys()))
            w.writeheader()
            w.writerows(outlier_rows)
        print(f"      wrote {len(outlier_rows)} outlier rows -> {OUT_OUTLIERS}")

    print()
    print("=" * 72)
    print("  STATE DISTRIBUTION")
    print("=" * 72)
    total = sum(state_counts.values())
    for k, v in state_counts.items():
        pct = 100.0 * v / total if total else 0
        print(f"  {k:<20} {v:>6,}  ({pct:5.1f}%)")
    print(f"  {'TOTAL':<20} {total:>6,}")

    print()
    print("=" * 72)
    print("  TIER DISTRIBUTION")
    print("=" * 72)
    total = sum(tier_counts.values())
    for k, v in tier_counts.items():
        pct = 100.0 * v / total if total else 0
        print(f"  {k:<20} {v:>6,}  ({pct:5.1f}%)")
    print(f"  {'TOTAL':<20} {total:>6,}")

    print()
    print("=" * 72)
    print("  TOP 20 WORST PAIRS BY DEFICIT")
    print("=" * 72)
    bad = [r for r in rows if r["state"] != "ALIGNED"]
    bad_sorted = sorted(bad, key=lambda r: r["fm_pool_2026_min"])
    for r in bad_sorted[:20]:
        print(f"  [{r['state']}] T:{r['link_tier']:<14} {r['fund']:<14} "
              f"WBS={r['wbs_posid']:<12} FM={r['fm_pool_2026_min']:>14,.2f} "
              f"PS={r['ps_pool_2026']:>14,.2f}")

    print()
    print("=" * 72)
    print("  TOP 10 FUNDS BY TICKET-RISK (proactive FMAVCREINIT candidates)")
    print("=" * 72)
    fund_risk: dict[str, float] = defaultdict(float)
    for r in rows:
        if r["state"] in ("FM-EXHAUSTED", "BOTH-EXHAUSTED"):
            fund_risk[r["fund"]] += min(0.0, r["fm_pool_2026_min"])
    fund_risk_sorted = sorted(fund_risk.items(), key=lambda x: x[1])
    for fund, agg_deficit in fund_risk_sorted[:10]:
        ftype = fund_type.get(fund, "")
        marker = "  <-- INC-005638" if fund == "196EAR4042" else ""
        print(f"  {fund:<14} (TYPE {ftype}) agg FM deficit = {agg_deficit:>14,.2f}{marker}")

    print()
    print("=" * 72)
    print("  INC-000005638 footprint (196EAR4042)")
    print("=" * 72)
    for r in rows:
        if r["fund"] == "196EAR4042":
            print(f"  T:{r['link_tier']:<14} WBS={r['wbs_posid']} "
                  f"PS={r['ps_pool_2026']:>14,.2f} "
                  f"FM={r['fm_pool_2026_min']:>14,.2f} "
                  f"state={r['state']}")

    print()
    print(f"OUTLIERS (>10 funds) — {len(set(r['wbs_objnr'] for r in outlier_rows))} WBSs")
    seen = set()
    for r in outlier_rows:
        if r["wbs_objnr"] not in seen:
            seen.add(r["wbs_objnr"])
            print(f"  {r['wbs_objnr']} (POSID={r['wbs_posid']}): "
                  f"{r['fund_count_on_wbs']} funds — {r['wbs_post1']}")

    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
