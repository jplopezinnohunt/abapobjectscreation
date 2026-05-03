"""
inc5638_fm_ps_avc_misalignment.py
==================================
INC-000005638 (extension) — class detector for the FM-AVC vs PS-AVC
misalignment pattern at UNESCO.

For every (Fund, FundCenter, AVC-Bucket, Year) triple in UNES across
2024-2026, computes:
  - FM-AVC bucket pool = revenue (per FIPEX in derivation range) − KBFC
    consumption (per RCMMTITEM in FMAVCT).
  - PS-AVC project pool = sum cumulative budget − sum cumulative actuals
    + commitments at the project linked to the fund (10-digit hard link).

Tiers the result into:
  - Tier 1: BOTH engines blocking (critical, no escape route).
  - Tier 2: FM blocking only — INC-000005638 class.
  - Tier 3: PS blocking only.
  - Tier 4: Neither.

Outputs a CSV + a tiered count summary.

Usage:
    python inc5638_fm_ps_avc_misalignment.py
    python inc5638_fm_ps_avc_misalignment.py --year 2026
    python inc5638_fm_ps_avc_misalignment.py --fund 196EAR4042
"""

from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import sys

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD_DB = os.path.join(
    PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
    "p01_gold_master_data.db",
)
OUT_CSV = os.path.join(
    PROJECT_ROOT, "Zagentexecution", "quality_checks",
    "inc5638_fm_ps_avc_misalignment.csv",
)


def _abs_value(s: str) -> float:
    """Convert SAP RFC-export amount to absolute value."""
    s = (s or "").strip()
    if not s:
        return 0.0
    if s.endswith("-"):
        return float(s[:-1].replace(" ", ""))
    return float(s.replace(" ", ""))


def build_avc_derivation_index(db) -> dict:
    """Build (fund) -> list of {bucket, fipex_from, fipex_to} from FMAFMAP013500109.

    Returns dict[fund] = [{'bucket': 'TC', 'fipex_from': "10'", 'fipex_to': '50'}, ...]
    """
    idx: dict = {}
    for r in db.execute(
        "SELECT SOUR1_FROM, SOUR1_TO, SOUR2_FROM, SOUR2_TO, SOUR3_FROM, SOUR3_TO, TARGET1 "
        "FROM fmafmap013500109"
    ):
        # SOUR2 is the fund range. We assume SOUR2_FROM = SOUR2_TO for a single-fund rule.
        f_from = (r["SOUR2_FROM"] or "").strip()
        f_to = (r["SOUR2_TO"] or "").strip()
        bucket = (r["TARGET1"] or "").strip()
        s3_from = (r["SOUR3_FROM"] or "").strip()
        s3_to = (r["SOUR3_TO"] or "").strip()
        if not bucket:
            continue
        # If single-fund rule, key by that fund. If range, expand the range
        # by walking the funds table.
        if f_from == f_to:
            idx.setdefault(f_from, []).append({
                "bucket": bucket,
                "fipex_from": s3_from,
                "fipex_to": s3_to,
            })
    return idx


def fipex_in_range(fipex: str, lo: str, hi: str) -> bool:
    """SAP CmtItem comparison — string lex order is the SAP convention."""
    return lo <= fipex <= hi


def fund_to_avc_bucket(fipex: str, rules: list[dict]) -> str:
    """Map (fipex) -> AVC bucket name using the rules for that fund.

    Returns the TARGET1 (e.g. 'TC') or the literal fipex if no rule matches.
    """
    for rule in rules:
        if fipex_in_range(fipex, rule["fipex_from"], rule["fipex_to"]):
            return rule["bucket"]
    return fipex


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", default="2026", help="Year to analyse")
    ap.add_argument("--fund", default=None, help="Restrict to a single fund")
    ap.add_argument("--type-101-112-only", action="store_true",
                    help="Restrict to donor/earmarked Type 101-112 funds")
    args = ap.parse_args()

    db = sqlite3.connect(GOLD_DB)
    db.row_factory = sqlite3.Row

    print(f"=== FM-AVC vs PS-AVC misalignment classifier — year {args.year} ===")
    print()

    # 1. Load AVC derivation rules
    deriv = build_avc_derivation_index(db)
    print(f"Loaded {sum(len(v) for v in deriv.values())} derivation rules across {len(deriv)} funds")

    # 2. Get the universe of UNESCO funds with FM activity in this year
    fund_filter = ""
    fund_args: list = []
    if args.fund:
        fund_filter = " AND FONDS = ?"
        fund_args = [args.fund]

    # FM consumption + revenue per (Fund, FundCenter, FIPEX) for the year
    print("Aggregating FM ledger (fmifiit_full)...")
    fm_aggr: dict = {}  # (fund, fc, fipex) -> {actuals, revenue}
    for r in db.execute(
        "SELECT FONDS, FISTL, FIPEX, WRTTP, FKBTR FROM fmifiit_full "
        "WHERE GJAHR=? AND BUKRS='UNES' AND WRTTP IN ('54', '66')" + fund_filter,
        (args.year, *fund_args),
    ):
        key = (r["FONDS"], r["FISTL"], (r["FIPEX"] or "").strip())
        d = fm_aggr.setdefault(key, {"actuals": 0.0, "revenue": 0.0})
        v = _abs_value(r["FKBTR"])
        if r["WRTTP"] == "54":
            d["actuals"] += v
        elif r["WRTTP"] == "66":
            d["revenue"] += v

    # Open commitments (cumulative — fmioi has no GJAHR filter logic for AVC)
    print("Aggregating fmioi commitments...")
    fm_cmt: dict = {}  # (fund, fc, fipex) -> open_cmt
    for r in db.execute(
        "SELECT FONDS, FISTL, FIPEX, FKBTR FROM fmioi "
        "WHERE BUKRS='UNES' AND WRTTP='51'" + fund_filter,
        fund_args,
    ):
        key = (r["FONDS"], r["FISTL"], (r["FIPEX"] or "").strip())
        fm_cmt[key] = fm_cmt.get(key, 0.0) + _abs_value(r["FKBTR"])

    # 3. Pull FMAVCT KBFC consumption by (fund, fc, RCMMTITEM)
    print(f"Loading fmavct_{args.year}...")
    avc_consumption: dict = {}  # (fund, fc, bucket) -> KBFC sum
    for r in db.execute(
        f"SELECT RFUND, RFUNDSCTR, RCMMTITEM, HSL01 FROM fmavct_{args.year} "
        f"WHERE RFIKRS='UNES' AND ALLOCTYPE_9='KBFC'"
    ):
        key = (
            (r["RFUND"] or "").strip(),
            (r["RFUNDSCTR"] or "").strip(),
            (r["RCMMTITEM"] or "").strip(),
        )
        avc_consumption[key] = avc_consumption.get(key, 0.0) + _abs_value(r["HSL01"])

    # 4. Build the (fund × fc × bucket) pool per the AVC engine
    print("Building per-AVC-bucket FM pools...")
    avc_pools: dict = {}  # (fund, fc, bucket) -> {revenue, actuals, ...}
    for (fund, fc, fipex), fm_d in fm_aggr.items():
        rules = deriv.get(fund, [])
        bucket = fund_to_avc_bucket(fipex, rules)
        akey = (fund, fc, bucket)
        a = avc_pools.setdefault(akey, {
            "revenue_per_fipex_in_range": 0.0,
            "actuals_per_fipex_in_range": 0.0,
            "open_cmt_per_fipex_in_range": 0.0,
            "constituent_fipex": set(),
        })
        a["revenue_per_fipex_in_range"] += fm_d["revenue"]
        a["actuals_per_fipex_in_range"] += fm_d["actuals"]
        a["constituent_fipex"].add(fipex)
        # Add commitments for the same key
        cmt = fm_cmt.get((fund, fc, fipex), 0.0)
        a["open_cmt_per_fipex_in_range"] += cmt

    # 5. Resolve PS pool per project (where the fund hard-links)
    # The 10-digit FM-PS hard-link: project PSPID == FUND (substr(POSID,1,10)).
    print("Building PS-AVC project pools...")
    proj_pools: dict = {}  # fund -> {budget_cum, actuals_cum, cmt_cum}
    # For all funds appearing in fm_aggr or avc_consumption, get project objnrs
    funds_to_check = set()
    for (fund, _, _) in fm_aggr.keys():
        funds_to_check.add(fund)
    for (fund, _, _) in avc_consumption.keys():
        funds_to_check.add(fund)

    for fund in funds_to_check:
        if not fund:
            continue
        # Get all WBS objnrs for this fund-as-project
        objnrs = [
            r["OBJNR"]
            for r in db.execute(
                "SELECT OBJNR FROM prps WHERE substr(POSID,1,10)=?",
                (fund,),
            )
        ]
        if not objnrs:
            proj_pools[fund] = {
                "ps_budget_cum_usd": 0.0,
                "ps_actuals_cum_usd": 0.0,
                "ps_cmt_cum_usd": 0.0,
                "ps_pool_usd": 0.0,
                "wbs_count": 0,
                "ps_present": False,
            }
            continue
        in_clause = "(" + ",".join("?" * len(objnrs)) + ")"
        # Cumulative budget WRTTP=41 across BPJA 2024+2025+2026
        budget_cum = 0.0
        for tbl in ("bpja_2024", "bpja_2025", "bpja_2026"):
            for r in db.execute(
                f"SELECT WTJHR FROM {tbl} WHERE WRTTP='41' AND OBJNR IN {in_clause}",
                objnrs,
            ):
                budget_cum += _abs_value(r["WTJHR"]) * (
                    -1 if (r["WTJHR"] or "").strip().endswith("-") else 1
                )
        # Cumulative actuals/commitments — sum WTG001+002+003 across cosp 2024+2025+2026
        actuals_cum = 0.0
        cmt_cum = 0.0
        for tbl in ("cosp_2024", "cosp_2025", "cosp_2026"):
            for r in db.execute(
                f"SELECT WRTTP,WTG001,WTG002,WTG003 FROM {tbl} WHERE OBJNR IN {in_clause}",
                objnrs,
            ):
                v = (
                    _abs_value(r["WTG001"]) * (-1 if (r["WTG001"] or "").strip().endswith("-") else 1)
                    + _abs_value(r["WTG002"]) * (-1 if (r["WTG002"] or "").strip().endswith("-") else 1)
                    + _abs_value(r["WTG003"]) * (-1 if (r["WTG003"] or "").strip().endswith("-") else 1)
                )
                if r["WRTTP"] == "04":
                    actuals_cum += v
                elif r["WRTTP"] == "22":
                    cmt_cum += v
        proj_pools[fund] = {
            "ps_budget_cum_usd": round(budget_cum, 2),
            "ps_actuals_cum_usd": round(actuals_cum, 2),
            "ps_cmt_cum_usd": round(cmt_cum, 2),
            "ps_pool_usd": round(budget_cum - actuals_cum - cmt_cum, 2),
            "wbs_count": len(objnrs),
            "ps_present": True,
        }

    # 6. Tier each (fund, fc, bucket) row
    print("Tiering and writing CSV...")
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0, "no_ps_link": 0}
    rows: list[dict] = []

    # Type filter
    type_filter_funds = set()
    if args.type_101_112_only:
        for r in db.execute(
            "SELECT FINCODE FROM funds WHERE CAST(TYPE AS INTEGER) BETWEEN 101 AND 112"
        ):
            type_filter_funds.add(r["FINCODE"])

    # Iterate over avc_pools (each (fund, fc, bucket))
    for (fund, fc, bucket), p in avc_pools.items():
        if args.type_101_112_only and fund not in type_filter_funds:
            continue
        # FM AVC consumption from fmavct (KBFC)
        fm_kbfc = avc_consumption.get((fund, fc, bucket), 0.0)
        # If fmavct has no row for the bucket, fall back to actuals+open_cmt
        # (it just means there hasn't been a posting yet, pool = revenue).
        revenue = p["revenue_per_fipex_in_range"]
        actuals = p["actuals_per_fipex_in_range"]
        open_cmt = p["open_cmt_per_fipex_in_range"]
        # FM bucket pool: prefer FMAVCT (real engine view); fallback to fmifiit
        if fm_kbfc > 0:
            fm_pool = revenue - fm_kbfc
            fm_pool_method = "fmavct_kbfc"
        else:
            fm_pool = revenue - actuals - open_cmt
            fm_pool_method = "fmifiit_fmioi"
        fm_pool = round(fm_pool, 2)
        fm_blocking = fm_pool < 0

        # PS pool
        proj = proj_pools.get(fund, {
            "ps_budget_cum_usd": 0.0,
            "ps_actuals_cum_usd": 0.0,
            "ps_cmt_cum_usd": 0.0,
            "ps_pool_usd": 0.0,
            "ps_present": False,
            "wbs_count": 0,
        })
        ps_blocking = proj["ps_present"] and proj["ps_pool_usd"] < 0

        if not proj["ps_present"]:
            tier = "no_ps_link"
        elif fm_blocking and ps_blocking:
            tier = 1
        elif fm_blocking:
            tier = 2
        elif ps_blocking:
            tier = 3
        else:
            tier = 4
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        rows.append({
            "fund": fund,
            "fund_center": fc,
            "avc_bucket": bucket,
            "year": args.year,
            "fm_revenue_usd": round(revenue, 2),
            "fm_actuals_usd": round(actuals, 2),
            "fm_open_cmt_usd": round(open_cmt, 2),
            "fmavct_kbfc_usd": round(fm_kbfc, 2),
            "fm_pool_usd": fm_pool,
            "fm_pool_method": fm_pool_method,
            "ps_budget_cum_usd": proj["ps_budget_cum_usd"],
            "ps_actuals_cum_usd": proj["ps_actuals_cum_usd"],
            "ps_cmt_cum_usd": proj["ps_cmt_cum_usd"],
            "ps_pool_usd": proj["ps_pool_usd"],
            "ps_wbs_count": proj["wbs_count"],
            "tier": tier,
            "constituent_fipex": "|".join(sorted(p["constituent_fipex"])),
        })

    # Write CSV
    if rows:
        with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"  wrote {len(rows)} rows -> {OUT_CSV}")

    # Print tier summary
    print()
    print("=== TIER SUMMARY ===")
    print(f"  Tier 1 (BOTH FM+PS blocking):  {tier_counts.get(1, 0):>6}")
    print(f"  Tier 2 (FM blocking only):     {tier_counts.get(2, 0):>6}    <- INC-000005638 class")
    print(f"  Tier 3 (PS blocking only):     {tier_counts.get(3, 0):>6}")
    print(f"  Tier 4 (Neither):              {tier_counts.get(4, 0):>6}")
    print(f"  no_ps_link (FM only, no proj): {tier_counts.get('no_ps_link', 0):>6}")
    print(f"  TOTAL buckets:                 {sum(tier_counts.values()):>6}")

    # Print Tier 1 + Tier 2 leaders
    print()
    print("=== Top 20 Tier 1+2 buckets by FM deficit ===")
    blocking = [r for r in rows if r["tier"] in (1, 2)]
    blocking.sort(key=lambda r: r["fm_pool_usd"])
    for r in blocking[:20]:
        print(f"  T{r['tier']}  {r['fund']:<14}/{r['fund_center']:<10}/{r['avc_bucket']:<6}  "
              f"FM={r['fm_pool_usd']:>14,.2f}  PS={r['ps_pool_usd']:>14,.2f}  "
              f"FIPEX={r['constituent_fipex']}")

    # Highlight INC-000005638 itself
    print()
    print("=== INC-000005638 footprint ===")
    for r in rows:
        if (r["fund"] == "196EAR4042" and r["fund_center"] == "WHC"
                and r["avc_bucket"] in ("TC", "80")):
            print(f"  T{r['tier']}  {r['fund']}/{r['fund_center']}/{r['avc_bucket']}  "
                  f"FM_pool={r['fm_pool_usd']:,.2f}  PS_pool={r['ps_pool_usd']:,.2f}")

    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
