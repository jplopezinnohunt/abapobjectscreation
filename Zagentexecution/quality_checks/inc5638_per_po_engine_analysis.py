"""
inc5638_per_po_engine_analysis.py
==================================
INC-000005638 — per-PO FM-AVC vs PS-AVC engine analysis.

For each of the 3 incident POs (and the WBS they target), compute:
  - FM-AVC pool depth (from fmavct_*)
  - PS-AVC pool depth (current budget BPJA WRTTP=41 minus consumption COSP WRTTP=04+22)
  - Which engine is exhausted (FM | PS | BOTH | NEITHER)

Reads only — pure SQLite query against the Gold DB.
"""

from __future__ import annotations
import sqlite3
import os
import sys
import json

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD_DB = os.path.join(
    PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
    "p01_gold_master_data.db",
)

INCIDENT = {
    "incident": "INC-000005638",
    "company_code": "UNES",
    "fund": "196EAR4042",
    "fund_center": "WHC",
    "control_object_type": "TC",  # per fmafmap013500109 derivation
    "biennium": "2024-2025",
    "pos": ["4500543365", "4500540022", "4500540024"],
    "wbs_internal": "00050949",  # confirmed by EKKN extract — all 13 lines
    "wbs_external": "196EAR4042.23.2.10.1",
    "wbs_descr": "Decentralization Yaounde",
}


def signed_amount(s: str) -> float:
    """Convert SAP RFC export amount to float. SAP encodes negatives as 'NNN-'."""
    s = (s or "").strip()
    if not s:
        return 0.0
    if s.endswith("-"):
        return -float(s[:-1].replace(" ", ""))
    return float(s.replace(" ", ""))


def main() -> int:
    db = sqlite3.connect(GOLD_DB)
    db.row_factory = sqlite3.Row

    out: dict = {"incident": INCIDENT, "analysis": {}}

    # ----------------------------------------------------------------
    # 1. WBS context for the 3 POs
    # ----------------------------------------------------------------
    wbs = db.execute(
        "SELECT PSPNR, OBJNR, POSID, POST1 FROM prps WHERE PSPNR=?",
        (INCIDENT["wbs_internal"],),
    ).fetchone()
    out["analysis"]["wbs"] = dict(wbs) if wbs else None
    print("=== WBS context ===")
    print(f"  PSPNR={wbs['PSPNR']}  OBJNR={wbs['OBJNR']}  POSID={wbs['POSID']}  POST1={wbs['POST1']}")

    target_objnr = wbs["OBJNR"]  # e.g. PR00050949

    # ----------------------------------------------------------------
    # 2. PS-AVC pool: current budget vs consumption — per WBS
    # ----------------------------------------------------------------
    print()
    print("=== PS-AVC pool for WBS PR00050949 ===")
    ps_pool = compute_ps_pool(db, target_objnr)
    out["analysis"]["ps_pool_target_wbs"] = ps_pool
    for k, v in ps_pool.items():
        print(f"  {k}: {v}")

    # ----------------------------------------------------------------
    # 3. PS-AVC pool: roll-up from project node down to target WBS
    #    (the PS-AVC engine in cumulative mode aggregates UP the
    #     project hierarchy — child WBS budget is consumed by parent).
    # ----------------------------------------------------------------
    print()
    print("=== PS-AVC pool: parent + sibling rollup ===")
    # Parent path: 196EAR4042.23.2.10.1 ascends through 23.2.10, 23.2, 23, root
    parents = [
        "196EAR4042.23.2.10.1",  # self
        "196EAR4042.23.2.10",
        "196EAR4042.23.2",
        "196EAR4042.23",
        "196EAR4042",
    ]
    rollup_objnrs = []
    for posid in parents:
        r = db.execute("SELECT OBJNR, PSPNR, POST1 FROM prps WHERE POSID=?", (posid,)).fetchone()
        if r:
            rollup_objnrs.append((posid, r["OBJNR"], r["POST1"]))
            print(f"  {posid:<30}  {r['OBJNR']}  {r['POST1']}")
    out["analysis"]["rollup_path"] = rollup_objnrs

    # PS pool for full project (sum all 139 WBS)
    print()
    print("=== PS-AVC pool: full project 196EAR4042 (all 139 WBS) ===")
    project_pool = compute_ps_pool_project(db, "196EAR4042")
    out["analysis"]["ps_pool_full_project"] = project_pool
    for k, v in project_pool.items():
        print(f"  {k}: {v}")

    # ----------------------------------------------------------------
    # 4. FM-AVC pool: read fmavct_2026 for UNES/196EAR4042 control objects
    # ----------------------------------------------------------------
    print()
    print("=== FM-AVC pool for 196EAR4042 / WHC (2026) ===")
    fm_pool = compute_fm_pool(db, "196EAR4042", "WHC")
    out["analysis"]["fm_pool"] = fm_pool
    for k, v in fm_pool.items():
        print(f"  {k}: {v}")

    # ----------------------------------------------------------------
    # 5. Verdict per PO line
    # ----------------------------------------------------------------
    print()
    print("=== VERDICT — which engine is exhausted ===")
    verdicts = []

    # The FM-AVC engine enforces at AVC-DERIVED bucket level, NOT fund level.
    # For 196EAR4042/WHC the AVC bucket = TC (covering FIPEX 10'..50).
    # The reporter's POs target FIPEX=20 (services) and FIPEX=11 (consultants),
    # both of which roll into the TC bucket.
    fm_avail_TC = fm_pool["fm_avc_available_2026_TC_bucket"]
    fm_avail_80 = fm_pool["fm_avc_available_2026_80_bucket"]
    fm_avail_fund_level = fm_pool["fm_avc_available_2026_fund_level"]
    ps_avail = project_pool["ps_pool_available"]

    fm_TC_exhausted = fm_avail_TC <= 0
    fm_80_exhausted = fm_avail_80 <= 0
    fm_fund_exhausted = fm_avail_fund_level <= 0
    ps_exhausted = ps_avail <= 0

    # The actual engine that fires for this incident's POs (FIPEX 11/20)
    # is the FM-AVC TC bucket. THAT's the relevant test.
    fm_exhausted_for_incident = fm_TC_exhausted

    if fm_exhausted_for_incident and ps_exhausted:
        engine = "BOTH"
    elif fm_exhausted_for_incident:
        engine = "FM"
    elif ps_exhausted:
        engine = "PS"
    else:
        engine = "NEITHER"

    print(f"  FM-AVC fund-level avail (2026):  ${fm_avail_fund_level:>16,.2f}  -> exhausted={fm_fund_exhausted}")
    print(f"  FM-AVC TC bucket avail (2026):   ${fm_avail_TC:>16,.2f}  -> exhausted={fm_TC_exhausted}  <- this is what blocks FIPEX=11,20")
    print(f"  FM-AVC 80 bucket avail (2026):   ${fm_avail_80:>16,.2f}  -> exhausted={fm_80_exhausted}")
    print(f"  PS-AVC available (cum):          ${ps_avail:>16,.2f}  -> exhausted={ps_exhausted}")
    print(f"  >>> ENGINE FIRING for incident POs (FIPEX 11/20 -> TC bucket): {engine}")

    for po in INCIDENT["pos"]:
        verdicts.append({"po": po, "engine_exhausted": engine,
                         "fm_avail_2026_TC_bucket_usd": round(fm_avail_TC, 2),
                         "fm_avail_2026_fund_level_usd": round(fm_avail_fund_level, 2),
                         "ps_avail_usd": round(ps_avail, 2),
                         "wbs": INCIDENT["wbs_external"]})
    out["analysis"]["verdict_engine"] = engine
    out["analysis"]["verdict_per_po"] = verdicts

    # ----------------------------------------------------------------
    # 6. Persist analysis
    # ----------------------------------------------------------------
    json_path = os.path.join(
        PROJECT_ROOT, "Zagentexecution", "quality_checks",
        "inc5638_per_po_engine_analysis.json",
    )
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print()
    print(f"=== JSON saved -> {json_path} ===")

    db.close()
    return 0


def compute_ps_pool(db, objnr: str) -> dict:
    """PS-AVC pool for a SINGLE WBS object (BPJA budget vs COSP consumption)."""
    res: dict = {"objnr": objnr}
    # Cumulative budget 2026 (current = WRTTP=41)
    rows = db.execute(
        "SELECT WTJHR FROM bpja_2026 WHERE OBJNR=? AND WRTTP='41'", (objnr,)
    ).fetchall()
    res["ps_budget_2026_current_usd"] = round(sum(signed_amount(r["WTJHR"]) for r in rows), 2)

    # Cumulative budget 2025 (previous year — relevant for biennium)
    rows = db.execute(
        "SELECT WTJHR FROM bpja_2025 WHERE OBJNR=? AND WRTTP='41'", (objnr,)
    ).fetchall()
    res["ps_budget_2025_current_usd"] = round(sum(signed_amount(r["WTJHR"]) for r in rows), 2)

    # Consumption COSP WRTTP=04 (actuals primary), summing WTG001+WTG002+WTG003
    rows = db.execute(
        "SELECT WTG001,WTG002,WTG003 FROM cosp_2026 WHERE OBJNR=? AND WRTTP='04'", (objnr,)
    ).fetchall()
    res["ps_actuals_2026_usd_3periods"] = round(
        sum(signed_amount(r["WTG001"]) + signed_amount(r["WTG002"]) + signed_amount(r["WTG003"])
            for r in rows), 2
    )

    # Commitments WRTTP=22
    rows = db.execute(
        "SELECT WTG001,WTG002,WTG003 FROM cosp_2026 WHERE OBJNR=? AND WRTTP='22'", (objnr,)
    ).fetchall()
    res["ps_commitments_2026_usd_3periods"] = round(
        sum(signed_amount(r["WTG001"]) + signed_amount(r["WTG002"]) + signed_amount(r["WTG003"])
            for r in rows), 2
    )

    res["ps_pool_available"] = round(
        res["ps_budget_2026_current_usd"]
        - res["ps_actuals_2026_usd_3periods"]
        - res["ps_commitments_2026_usd_3periods"], 2
    )
    return res


def compute_ps_pool_project(db, project_pspid: str) -> dict:
    """PS-AVC pool for the full project (all WBS)."""
    res: dict = {"project": project_pspid}
    objnrs = [r["OBJNR"] for r in db.execute(
        "SELECT OBJNR FROM prps WHERE substr(POSID,1,?)=?",
        (len(project_pspid), project_pspid),
    )]
    res["wbs_count"] = len(objnrs)
    if not objnrs:
        return res
    in_clause = "(" + ",".join(f"'{o}'" for o in objnrs) + ")"

    # PS budget cumulative
    rows = db.execute(
        f"SELECT WTJHR FROM bpja_2026 WHERE OBJNR IN {in_clause} AND WRTTP='41'"
    ).fetchall()
    res["ps_budget_2026_current_usd"] = round(sum(signed_amount(r["WTJHR"]) for r in rows), 2)

    rows = db.execute(
        f"SELECT WTJHR FROM bpja_2025 WHERE OBJNR IN {in_clause} AND WRTTP='41'"
    ).fetchall()
    res["ps_budget_2025_current_usd"] = round(sum(signed_amount(r["WTJHR"]) for r in rows), 2)

    rows = db.execute(
        f"SELECT WTJHR FROM bpja_2024 WHERE OBJNR IN {in_clause} AND WRTTP='41'"
    ).fetchall()
    res["ps_budget_2024_current_usd"] = round(sum(signed_amount(r["WTJHR"]) for r in rows), 2)

    # Actuals + commitments 2026
    rows = db.execute(
        f"SELECT WTG001,WTG002,WTG003 FROM cosp_2026 WHERE OBJNR IN {in_clause} AND WRTTP='04'"
    ).fetchall()
    res["ps_actuals_2026_usd_3periods"] = round(
        sum(signed_amount(r["WTG001"]) + signed_amount(r["WTG002"]) + signed_amount(r["WTG003"])
            for r in rows), 2
    )

    rows = db.execute(
        f"SELECT WTG001,WTG002,WTG003 FROM cosp_2026 WHERE OBJNR IN {in_clause} AND WRTTP='22'"
    ).fetchall()
    res["ps_commitments_2026_usd_3periods"] = round(
        sum(signed_amount(r["WTG001"]) + signed_amount(r["WTG002"]) + signed_amount(r["WTG003"])
            for r in rows), 2
    )

    # CUMULATIVE PS-AVC pool: sum 2024+2025+2026 budget minus 2024+2025+2026 consumption
    cum_budget = (res["ps_budget_2024_current_usd"]
                  + res["ps_budget_2025_current_usd"]
                  + res["ps_budget_2026_current_usd"])
    res["ps_budget_cumulative_2024_2026_usd"] = round(cum_budget, 2)

    # Cumulative actuals across all years (sum of WTG001+002+003 across 2024-2026)
    cum_actuals = 0.0
    cum_cmt = 0.0
    for tbl in ("cosp_2024", "cosp_2025", "cosp_2026"):
        for r in db.execute(
            f"SELECT WTG001,WTG002,WTG003 FROM {tbl} WHERE OBJNR IN {in_clause} AND WRTTP='04'"
        ):
            cum_actuals += signed_amount(r["WTG001"]) + signed_amount(r["WTG002"]) + signed_amount(r["WTG003"])
        for r in db.execute(
            f"SELECT WTG001,WTG002,WTG003 FROM {tbl} WHERE OBJNR IN {in_clause} AND WRTTP='22'"
        ):
            cum_cmt += signed_amount(r["WTG001"]) + signed_amount(r["WTG002"]) + signed_amount(r["WTG003"])
    res["ps_actuals_cumulative_2024_2026_usd"] = round(cum_actuals, 2)
    res["ps_commitments_cumulative_2024_2026_usd"] = round(cum_cmt, 2)
    res["ps_pool_available"] = round(cum_budget - cum_actuals - cum_cmt, 2)
    return res


def compute_fm_pool(db, fund: str, fund_center: str = "WHC") -> dict:
    """FM-AVC pool computation — UNESCO 9HZ00001 environment.

    KEY INSIGHT (INC-000005638 extension): UNESCO's FMAVCT only stores
    KBFC (consumption) entries. There is NO budget-load row in FMAVCT.
    The pool depth at the AVC-derived granularity is computed AT RUNTIME
    by the FM-AVC engine via:

        pool_depth = sum(fmifiit revenue WHERE FONDS=F AND FISTL=FC AND
                         derived_cmtitem(FIPEX) = AVC_BUCKET)
                   - sum(fmavct.HSL01 WHERE RFIKRS=UNES AND RFUND=F
                         AND RFUNDSCTR=FC AND RCMMTITEM=AVC_BUCKET
                         AND ALLOCTYPE_9='KBFC')

    Where AVC_BUCKET is from FMAFMAP013500109 derivation. For 196EAR4042:
    the rule maps (UNES, 196EAR4042, "10'..50") → TC. Any FIPEX in 10'..50
    rolls into the TC bucket. FIPEX=80 has NO derivation rule → uses
    literal '80' bucket.

    The AVC enforcement granularity at UNESCO is therefore:
      (FUND × FUND_CENTER × DERIVED_CMTITEM × YEAR)
    """
    res: dict = {"fund": fund, "fund_center": fund_center}

    def _abs_sum(query, params):
        r = db.execute(query, params).fetchone()
        return round(abs(r[0] or 0.0), 2)

    # ----- LEVEL 1: Fund-level FM pool (the original Section 5.2 view) -----
    res["fm_revenue_2026_usd"] = _abs_sum(
        "SELECT SUM(CASE WHEN substr(FKBTR,-1)='-' THEN -CAST(replace(replace(FKBTR,'-',''),' ','') AS REAL) "
        "ELSE CAST(replace(FKBTR,' ','') AS REAL) END) FROM fmifiit_full "
        "WHERE FONDS=? AND GJAHR='2026' AND WRTTP='66'",
        (fund,)
    )
    res["fm_actuals_2026_usd"] = _abs_sum(
        "SELECT SUM(CASE WHEN substr(FKBTR,-1)='-' THEN -CAST(replace(replace(FKBTR,'-',''),' ','') AS REAL) "
        "ELSE CAST(replace(FKBTR,' ','') AS REAL) END) FROM fmifiit_full "
        "WHERE FONDS=? AND GJAHR='2026' AND WRTTP='54'",
        (fund,)
    )
    res["fm_commitments_open_usd"] = _abs_sum(
        "SELECT SUM(CASE WHEN substr(FKBTR,-1)='-' THEN -CAST(replace(replace(FKBTR,'-',''),' ','') AS REAL) "
        "ELSE CAST(replace(FKBTR,' ','') AS REAL) END) FROM fmioi "
        "WHERE FONDS=? AND WRTTP='51'",
        (fund,)
    )
    res["fm_avc_available_2026_fund_level"] = round(
        res["fm_revenue_2026_usd"]
        - res["fm_actuals_2026_usd"]
        - res["fm_commitments_open_usd"], 2
    )

    # ----- LEVEL 2: AVC-derived bucket pool (the actual enforcement) -----
    # The AVC engine enforces at (Fund × FundCenter × DerivedCmtItem × Year).
    # For 196EAR4042 the derivation maps FIPEX in 10'..50 -> TC; FIPEX=80 ->
    # literal '80'. So we partition the FM revenue / consumption per
    # FIPEX bucket the AVC engine sees.

    fipex_in_TC_range = ("10'", "11", "13", "20", "30", "40", "50")
    # Use parameterized IN clause to escape "10'"
    placeholders = ",".join("?" * len(fipex_in_TC_range))

    # 2026 revenue assigned to the TC FIPEX range (almost certainly $0 due
    # to UNESCO's REVENUE-placeholder pattern)
    rev_tc = _abs_sum(
        f"SELECT SUM(CASE WHEN substr(FKBTR,-1)='-' THEN -CAST(replace(replace(FKBTR,'-',''),' ','') AS REAL) "
        f"ELSE CAST(replace(FKBTR,' ','') AS REAL) END) FROM fmifiit_full "
        f"WHERE FONDS=? AND FISTL=? AND GJAHR='2026' AND WRTTP='66' "
        f"AND FIPEX IN ({placeholders})",
        (fund, fund_center, *fipex_in_TC_range),
    )
    res["fm_revenue_2026_TC_bucket_usd"] = rev_tc

    # 2026 KBFC consumption against TC bucket per FMAVCT (proper)
    kbfc_tc_2026 = _abs_sum(
        "SELECT SUM(CASE WHEN substr(HSL01,-1)='-' THEN -CAST(replace(replace(HSL01,'-',''),' ','') AS REAL) "
        "ELSE CAST(replace(HSL01,' ','') AS REAL) END) FROM fmavct_2026 "
        "WHERE RFIKRS='UNES' AND RFUND=? AND RFUNDSCTR=? "
        "AND TRIM(RCMMTITEM)='TC' AND ALLOCTYPE_9='KBFC'",
        (fund, fund_center)
    )
    res["fm_avc_consumption_2026_TC_bucket_usd"] = kbfc_tc_2026
    # Pool depth at the TC AVC bucket
    res["fm_avc_available_2026_TC_bucket"] = round(rev_tc - kbfc_tc_2026, 2)

    # Same for 80 bucket
    rev_80 = _abs_sum(
        "SELECT SUM(CASE WHEN substr(FKBTR,-1)='-' THEN -CAST(replace(replace(FKBTR,'-',''),' ','') AS REAL) "
        "ELSE CAST(replace(FKBTR,' ','') AS REAL) END) FROM fmifiit_full "
        "WHERE FONDS=? AND FISTL=? AND GJAHR='2026' AND WRTTP='66' AND FIPEX='80'",
        (fund, fund_center)
    )
    res["fm_revenue_2026_80_bucket_usd"] = rev_80
    kbfc_80_2026 = _abs_sum(
        "SELECT SUM(CASE WHEN substr(HSL01,-1)='-' THEN -CAST(replace(replace(HSL01,'-',''),' ','') AS REAL) "
        "ELSE CAST(replace(HSL01,' ','') AS REAL) END) FROM fmavct_2026 "
        "WHERE RFIKRS='UNES' AND RFUND=? AND RFUNDSCTR=? "
        "AND TRIM(RCMMTITEM)='80' AND ALLOCTYPE_9='KBFC'",
        (fund, fund_center)
    )
    res["fm_avc_consumption_2026_80_bucket_usd"] = kbfc_80_2026
    res["fm_avc_available_2026_80_bucket"] = round(rev_80 - kbfc_80_2026, 2)

    # Counts of FMAVCT rows that COULD be the bucket — TIER_2
    n = db.execute(
        "SELECT COUNT(*) FROM fmavct_2026 WHERE RFIKRS='UNES' AND RFUND=? AND RFUNDSCTR=?",
        (fund, fund_center)
    ).fetchone()[0]
    res["fmavct_2026_rows_for_fund_center"] = n
    return res


if __name__ == "__main__":
    sys.exit(main())
