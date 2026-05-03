"""
project_risk_classifier.py
==========================
Apply the 3-lens project classification (user proposal Session #69):

  Lens 1: Does the FUND have an AVC derivation rule? (fmafmap013500109)
  Lens 2: Is the relationship 1:1 Fund<->Project? (single fund per project)
  Lens 3: Is the 10-digit hard-link enforced? (TYPE 101-112 per ZXFMYU22)

Output classes:
  Class A — Locked controlled  (AVC ON + 1:1 + 10-digit enforced)  -> INC-005638 type, biennium-end trap
  Class B — Locked partial    (mixed AVC coverage on the project)
  Class C — Process-dependent (multi-fund, partial enforcement)
  Class D — Uncontrolled       (no AVC + multi-fund + no validation)

Output CSV: Zagentexecution/quality_checks/project_risk_classifier.csv
"""
import sqlite3
import csv
from datetime import datetime

GOLD = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"
OUT = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\quality_checks\project_risk_classifier.csv"

EARMARKED_TYPES = {'101','102','103','104','105','106','107','108','109','110','111','112'}

def main():
    con = sqlite3.connect(GOLD, timeout=10)
    cur = con.cursor()

    print(f"{datetime.now().strftime('%H:%M:%S')} === Project risk classifier ===")

    # 0. Build active-WBS set (JEST status REL, exclude CLSD/TECO/DLFL)
    print("Step 0: build active-WBS set (JEST filter)")
    cur.execute("DROP TABLE IF EXISTS _active_wbs")
    cur.execute("""
        CREATE TEMP TABLE _active_wbs AS
        SELECT DISTINCT j.OBJNR
        FROM jest j
        WHERE j.STAT='I0002' AND j.INACT=''
          AND j.OBJNR LIKE 'PR%'
          AND j.OBJNR NOT IN (
              SELECT OBJNR FROM jest
              WHERE STAT IN ('I0045','I0046','I0076') AND INACT=''
          )
    """)
    n_active = cur.execute("SELECT COUNT(*) FROM _active_wbs").fetchone()[0]
    print(f"  Active WBSs (REL, not CLSD/TECO/DLFL): {n_active:,}")

    # 1. For each project hierarchy (PSPHI), aggregate fund usage from coep — ACTIVE WBSs only
    print("Step 1: aggregate fund usage per project hierarchy (active filter)")
    cur.execute("DROP TABLE IF EXISTS _proj_funds")
    cur.execute("""
        CREATE TEMP TABLE _proj_funds AS
        SELECT
          p.PSPHI as proj_id,
          c.GEBER as fund,
          COUNT(*) as posting_count,
          MIN(SUBSTR(p.POSID,1,10)=c.GEBER) as posid_match_min,
          MAX(SUBSTR(p.POSID,1,10)=c.GEBER) as posid_match_max
        FROM coep c
        JOIN prps_full p ON c.OBJNR = p.OBJNR
        INNER JOIN _active_wbs aw ON c.OBJNR = aw.OBJNR
        WHERE c.GEBER != '' AND c.OBJNR LIKE 'PR%'
          AND c.GJAHR IN ('2024','2025','2026')
        GROUP BY p.PSPHI, c.GEBER
    """)
    n = cur.execute("SELECT COUNT(*) FROM _proj_funds").fetchone()[0]
    print(f"  {n:,} (project, fund) pairs with active postings")

    # 2. Enrich each pair with AVC rule presence + fund TYPE
    print("Step 2: add AVC rule presence + fund TYPE")
    cur.execute("DROP TABLE IF EXISTS _proj_funds_enriched")
    cur.execute(f"""
        CREATE TEMP TABLE _proj_funds_enriched AS
        SELECT
          pf.proj_id,
          pf.fund,
          pf.posting_count,
          pf.posid_match_min,
          pf.posid_match_max,
          f.TYPE as fund_type,
          CASE WHEN EXISTS(
            SELECT 1 FROM fmafmap013500109 m
             WHERE m.SOUR1_FROM='UNES'
               AND m.SOUR2_FROM <= pf.fund
               AND m.SOUR2_TO >= pf.fund
          ) THEN 1 ELSE 0 END as has_avc_rule,
          CASE WHEN f.TYPE IN ('{",".join(sorted(EARMARKED_TYPES))}') THEN 1 ELSE 0 END as is_earmarked
        FROM _proj_funds pf
        LEFT JOIN funds f ON pf.fund = f.FINCODE AND f.FIKRS='UNES'
    """)
    # Note: cannot use SQL IN with placeholder list easily here; using direct interpolation
    cur.execute("DROP TABLE IF EXISTS _proj_funds_enriched")
    cur.execute(f"""
        CREATE TEMP TABLE _proj_funds_enriched AS
        SELECT
          pf.proj_id, pf.fund, pf.posting_count,
          pf.posid_match_min, pf.posid_match_max,
          f.TYPE as fund_type,
          CASE WHEN EXISTS(SELECT 1 FROM fmafmap013500109 m
             WHERE m.SOUR1_FROM='UNES' AND m.SOUR2_FROM<=pf.fund AND m.SOUR2_TO>=pf.fund
          ) THEN 1 ELSE 0 END as has_avc_rule,
          CASE WHEN f.TYPE IN ('101','102','103','104','105','106','107','108','109','110','111','112')
               THEN 1 ELSE 0 END as is_earmarked
        FROM _proj_funds pf
        LEFT JOIN funds f ON pf.fund = f.FINCODE AND f.FIKRS='UNES'
    """)

    # 3. Aggregate at project level
    print("Step 3: aggregate at project level + classify")
    cur.execute("DROP TABLE IF EXISTS _proj_class")
    cur.execute("""
        CREATE TEMP TABLE _proj_class AS
        SELECT
          proj_id,
          COUNT(DISTINCT fund) as n_funds,
          SUM(posting_count) as total_postings,
          SUM(has_avc_rule) as funds_with_avc,
          SUM(is_earmarked) as funds_earmarked,
          SUM(CASE WHEN posid_match_min=1 THEN 1 ELSE 0 END) as funds_full_10digit_match,
          GROUP_CONCAT(DISTINCT fund_type) as fund_types,
          GROUP_CONCAT(DISTINCT fund) as fund_list
        FROM _proj_funds_enriched
        GROUP BY proj_id
    """)

    # 4. Apply class logic
    print("Step 4: assign Class A/B/C/D")
    cur.execute("DROP TABLE IF EXISTS _proj_classified")
    cur.execute("""
        CREATE TEMP TABLE _proj_classified AS
        SELECT
          pc.proj_id,
          pr.POST1 as project_name,
          pc.n_funds,
          pc.total_postings,
          pc.funds_with_avc,
          pc.funds_earmarked,
          pc.funds_full_10digit_match,
          pc.fund_types,
          pc.fund_list,
          CASE
            -- Class A: 1:1 single fund + has AVC + earmarked + 10-digit match
            WHEN pc.n_funds = 1 AND pc.funds_with_avc = 1
                 AND pc.funds_earmarked = 1 AND pc.funds_full_10digit_match = 1
              THEN 'A'
            -- Class B: 1:1 + earmarked + 10-digit match BUT no AVC rule
            WHEN pc.n_funds = 1 AND pc.funds_earmarked = 1 AND pc.funds_full_10digit_match = 1
              THEN 'B'
            -- Class C: multi-fund OR partial earmarked AND has at least 1 AVC rule
            WHEN pc.funds_with_avc >= 1
              THEN 'C'
            -- Class D: no AVC rule + (multi-fund OR non-earmarked) + no enforcement
            ELSE 'D'
          END as risk_class
        FROM _proj_class pc
        LEFT JOIN proj pr ON pr.PSPNR = pc.proj_id
    """)
    n = cur.execute("SELECT COUNT(*) FROM _proj_classified").fetchone()[0]
    print(f"  {n:,} projects classified")

    # 5. Class distribution
    print()
    print("=== Class distribution ===")
    for r in cur.execute("""
        SELECT risk_class, COUNT(*) as n_projects, SUM(total_postings) as total_postings,
               SUM(n_funds) as total_fund_pairs
        FROM _proj_classified
        GROUP BY risk_class ORDER BY risk_class
    """).fetchall():
        print(f"  Class {r[0]}: {r[1]:>5,} projects, {r[2]:>10,} postings, {r[3]:>8,} (proj,fund) pairs")

    # 6. Examples per class
    print()
    print("=== Sample projects per class ===")
    for cls in ['A','B','C','D']:
        print(f"\n  Class {cls} samples:")
        for r in cur.execute("""
            SELECT proj_id, project_name, n_funds, funds_with_avc, fund_types, total_postings
            FROM _proj_classified WHERE risk_class=?
            ORDER BY total_postings DESC LIMIT 5
        """, (cls,)).fetchall():
            types_short = (r[4] or '')[:20]
            print(f"    proj={r[0]} {(r[1] or '')[:35]:35s} n_funds={r[2]} avc={r[3]} types={types_short} postings={r[5]:,}")

    # 7. Export CSV
    print()
    print("Step 5: export CSV")
    cur.execute("""
        SELECT proj_id, project_name, risk_class, n_funds, total_postings,
               funds_with_avc, funds_earmarked, funds_full_10digit_match,
               fund_types, fund_list
        FROM _proj_classified
        ORDER BY risk_class, total_postings DESC
    """)
    rows = cur.fetchall()
    headers = [d[0] for d in cur.description]
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"  Wrote {len(rows):,} rows to {OUT}")

    # 8. Verify INC-005638 case
    print()
    print("=== Verify INC-005638 case (PSPHI=00013092 = project 196EAR4042) ===")
    for r in cur.execute("""
        SELECT proj_id, project_name, risk_class, n_funds, total_postings,
               funds_with_avc, funds_earmarked, fund_types
        FROM _proj_classified WHERE proj_id IN ('00013092','00050949')
    """).fetchall():
        print(f"  {r}")

    con.close()


if __name__ == "__main__":
    main()
