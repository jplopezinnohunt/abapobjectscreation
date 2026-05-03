"""
committed_vs_available_detector.py
====================================
The "active + committed vs available funds" detector.

Answers the operational question (Session #69):
  "How do we detect what is active, and committed funds that don't align
  with available funds?"

For every ACTIVE (Fund, WBS) pair in UNESCO, computes:
  - PS commitments outstanding (cooi, GJAHR=2026, signed)
  - FM available pool (fmifiit_full, WRTTP=66 - WRTTP=54)
  - PS available pool (bpja WRTTP=41 - coep WRTTP=04 - cooi)
  - Active flag (jest STAT='I0002' Released, NOT CLSD/TECO/DLFL)

Then flags rows where: commitment > FM_available.
That's the at-risk universe that will produce INC-005638-class tickets.

Output: Zagentexecution/quality_checks/committed_vs_available_detector.csv
"""
import sqlite3
import csv
from datetime import datetime

GOLD = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"
OUT_CSV = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\quality_checks\committed_vs_available_detector.csv"
LOG = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\logs\committed_vs_available_{ts}.log".format(ts=datetime.now().strftime("%Y%m%d_%H%M%S"))


def signed(col):
    return f"CASE WHEN SUBSTR({col},-1,1)='-' THEN -CAST(REPLACE({col},'-','') AS REAL) ELSE CAST({col} AS REAL) END"


def log(s):
    line = f"{datetime.now().strftime('%H:%M:%S')} {s}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    log("=== Committed-vs-Available detector starting ===")
    con = sqlite3.connect(GOLD, timeout=10)
    cur = con.cursor()

    # 1. Active WBSs only (STAT=I0002 REL, no CLSD/TECO/DLFL)
    log("Step 1: Build active WBS set from JEST")
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
    log(f"  Active WBSs (REL, not CLSD/TECO/DLFL): {n_active:,}")

    # 2. PS commitments outstanding 2026 per WBS
    # COOI has no GEBER. Derive fund via:
    #   (a) HARD-link: POSID(10) = fund (only valid for Earmarked TYPE 101-112)
    #   (b) DERIVED:  most-recent GEBER seen in COEP for the same OBJNR
    log("Step 2: Aggregate PS commitments 2026 from cooi (fund derived via POSID prefix or coep history)")
    cur.execute("DROP TABLE IF EXISTS _wbs_fund_map")
    cur.execute(f"""
        CREATE TEMP TABLE _wbs_fund_map AS
        SELECT
          c.OBJNR,
          COALESCE(
            -- HARD-link first (POSID(10) for fund-named WBSs)
            (SELECT f.FINCODE FROM funds f WHERE f.FINCODE = SUBSTR(p.POSID, 1, 10) AND f.FIKRS='UNES'),
            -- otherwise: most-frequent GEBER for the WBS in 2024-2026 COEP
            (SELECT GEBER FROM coep e WHERE e.OBJNR=c.OBJNR AND GEBER!='' GROUP BY GEBER ORDER BY COUNT(*) DESC LIMIT 1)
          ) as fund_derived,
          CASE WHEN EXISTS (SELECT 1 FROM funds f WHERE f.FINCODE = SUBSTR(p.POSID, 1, 10) AND f.FIKRS='UNES') THEN 'HARD' ELSE 'DERIVED' END as link_type
        FROM (SELECT DISTINCT OBJNR FROM cooi WHERE GJAHR='2026' AND OBJNR IN (SELECT OBJNR FROM _active_wbs)) c
        LEFT JOIN prps_full p ON c.OBJNR = p.OBJNR
    """)
    cur.execute(f"""
        CREATE TEMP TABLE _ps_commit AS
        SELECT c.OBJNR, m.fund_derived as GEBER, m.link_type,
               COUNT(*) as n_commit_lines, SUM({signed('WKGBTR')}) as ps_commit_2026
        FROM cooi c
        JOIN _wbs_fund_map m ON c.OBJNR = m.OBJNR
        WHERE c.GJAHR='2026' AND m.fund_derived IS NOT NULL
        GROUP BY c.OBJNR, m.fund_derived, m.link_type
    """)
    n_ps_commit = cur.execute("SELECT COUNT(*) FROM _ps_commit").fetchone()[0]
    log(f"  Active (WBS, Fund) pairs with 2026 commitments: {n_ps_commit:,}")
    # link type breakdown
    for r in cur.execute("SELECT link_type, COUNT(*) FROM _ps_commit GROUP BY link_type").fetchall():
        log(f"    {r[0]}: {r[1]:,} pairs")

    # 3. PS budget pool 2026 per WBS
    log("Step 3: Aggregate PS budget pool 2026 from bpja")
    cur.execute("DROP TABLE IF EXISTS _ps_budget")
    cur.execute(f"""
        CREATE TEMP TABLE _ps_budget AS
        SELECT OBJNR, SUM({signed('WTJHR')}) as ps_budget_2026
        FROM bpja
        WHERE GJAHR='2026' AND WRTTP='41' AND OBJNR IN (SELECT OBJNR FROM _active_wbs)
        GROUP BY OBJNR
    """)
    log(f"  Active WBSs with 2026 budget rows: {cur.execute('SELECT COUNT(*) FROM _ps_budget').fetchone()[0]:,}")

    # 4. PS actuals 2026 per WBS
    log("Step 4: Aggregate PS actuals 2026 from coep")
    cur.execute("DROP TABLE IF EXISTS _ps_actual")
    cur.execute(f"""
        CREATE TEMP TABLE _ps_actual AS
        SELECT OBJNR, SUM({signed('WKGBTR')}) as ps_actual_2026
        FROM coep
        WHERE GJAHR='2026' AND WRTTP='04' AND OBJNR IN (SELECT OBJNR FROM _active_wbs)
        GROUP BY OBJNR
    """)
    log(f"  Active WBSs with 2026 actuals rows: {cur.execute('SELECT COUNT(*) FROM _ps_actual').fetchone()[0]:,}")

    # 5. FM pool 2026 per FOND
    log("Step 5: Aggregate FM revenue/consumption 2026 from fmifiit_full per fund")
    cur.execute("DROP TABLE IF EXISTS _fm_pool")
    cur.execute(f"""
        CREATE TEMP TABLE _fm_pool AS
        SELECT FONDS,
            SUM(CASE WHEN WRTTP='66' THEN {signed('FKBTR')} ELSE 0 END) as fm_revenue_2026,
            SUM(CASE WHEN WRTTP='54' THEN {signed('FKBTR')} ELSE 0 END) as fm_consumed_2026
        FROM fmifiit_full
        WHERE GJAHR='2026' AND FONDS!=''
        GROUP BY FONDS
    """)
    n_fm = cur.execute("SELECT COUNT(*) FROM _fm_pool").fetchone()[0]
    log(f"  Funds with 2026 FM activity: {n_fm:,}")

    # 6. ISBD-flagged WBSs (SAP itself flags as deficit)
    log("Step 6: Build ISBD-flag lookup from JEST")
    cur.execute("DROP TABLE IF EXISTS _isbd_wbs")
    cur.execute("""
        CREATE TEMP TABLE _isbd_wbs AS
        SELECT DISTINCT OBJNR FROM jest WHERE STAT='I0093' AND INACT=''
    """)
    log(f"  ISBD-flagged WBSs: {cur.execute('SELECT COUNT(*) FROM _isbd_wbs').fetchone()[0]:,}")

    # 7. Final assembly: ACTIVE pairs with commitments + budgets + FM pool + status
    log("Step 7: Build final committed-vs-available matrix")
    cur.execute(f"""
        CREATE TEMP TABLE _matrix AS
        SELECT
          c.OBJNR as wbs_objnr,
          p.POSID as wbs_posid,
          p.POST1 as wbs_post1,
          c.GEBER as fund,
          f.TYPE as fund_type,
          c.link_type,
          c.n_commit_lines,
          c.ps_commit_2026 as ps_commit_open_2026,
          COALESCE(b.ps_budget_2026, 0) as ps_budget_2026,
          COALESCE(a.ps_actual_2026, 0) as ps_actual_2026,
          COALESCE(b.ps_budget_2026, 0) - COALESCE(a.ps_actual_2026, 0) - c.ps_commit_2026 as ps_pool_remaining,
          COALESCE(fm.fm_revenue_2026, 0) as fm_revenue_2026,
          COALESCE(fm.fm_consumed_2026, 0) as fm_consumed_2026,
          COALESCE(fm.fm_revenue_2026, 0) + COALESCE(fm.fm_consumed_2026, 0) as fm_pool_remaining,
          CASE WHEN i.OBJNR IS NOT NULL THEN 'YES' ELSE 'NO' END as isbd_flag
        FROM _ps_commit c
        LEFT JOIN prps_full p ON c.OBJNR = p.OBJNR
        LEFT JOIN funds f ON c.GEBER = f.FINCODE AND f.FIKRS='UNES'
        LEFT JOIN _ps_budget b ON c.OBJNR = b.OBJNR
        LEFT JOIN _ps_actual a ON c.OBJNR = a.OBJNR
        LEFT JOIN _fm_pool fm ON c.GEBER = fm.FONDS
        LEFT JOIN _isbd_wbs i ON c.OBJNR = i.OBJNR
    """)
    n_matrix = cur.execute("SELECT COUNT(*) FROM _matrix").fetchone()[0]
    log(f"  Final matrix rows: {n_matrix:,}")

    # 8. Classify each row
    log("Step 8: Classify each pair")
    classify_stats = cur.execute("""
        SELECT
          COUNT(*) as total,
          SUM(CASE WHEN ps_pool_remaining < 0 AND fm_pool_remaining < 0 THEN 1 ELSE 0 END) as both_exh,
          SUM(CASE WHEN ps_pool_remaining >= 0 AND fm_pool_remaining < 0 THEN 1 ELSE 0 END) as fm_only_exh,
          SUM(CASE WHEN ps_pool_remaining < 0 AND fm_pool_remaining >= 0 THEN 1 ELSE 0 END) as ps_only_exh,
          SUM(CASE WHEN ps_pool_remaining >= 0 AND fm_pool_remaining >= 0 THEN 1 ELSE 0 END) as aligned,
          SUM(CASE WHEN isbd_flag='YES' THEN 1 ELSE 0 END) as isbd_count,
          SUM(CASE WHEN ps_commit_open_2026 > fm_pool_remaining AND fm_pool_remaining > 0 THEN 1 ELSE 0 END) as commit_exceeds_fm_avail
        FROM _matrix
    """).fetchone()

    log(f"  Total pairs:            {classify_stats[0]:,}")
    log(f"  BOTH-EXHAUSTED:         {classify_stats[1]:,}")
    log(f"  FM-only-EXHAUSTED:      {classify_stats[2]:,}  <- INC-005638 class")
    log(f"  PS-only-EXHAUSTED:      {classify_stats[3]:,}")
    log(f"  ALIGNED:                {classify_stats[4]:,}")
    log(f"  ISBD-flagged (any):     {classify_stats[5]:,}")
    log(f"  Commit > FM available:  {classify_stats[6]:,}  <- pre-flight HARD-BLOCK candidates")

    # 9. Export CSV
    log(f"Step 9: Export CSV to {OUT_CSV}")
    cur.execute("""
        SELECT
          fund, fund_type, link_type, wbs_objnr, wbs_posid, wbs_post1,
          n_commit_lines, ps_commit_open_2026,
          ps_budget_2026, ps_actual_2026, ps_pool_remaining,
          fm_revenue_2026, fm_consumed_2026, fm_pool_remaining,
          isbd_flag,
          CASE
            WHEN ps_pool_remaining < 0 AND fm_pool_remaining < 0 THEN 'BOTH_EXHAUSTED'
            WHEN ps_pool_remaining >= 0 AND fm_pool_remaining < 0 THEN 'FM_ONLY_EXHAUSTED'
            WHEN ps_pool_remaining < 0 AND fm_pool_remaining >= 0 THEN 'PS_ONLY_EXHAUSTED'
            ELSE 'ALIGNED'
          END as state,
          CASE WHEN ps_commit_open_2026 > fm_pool_remaining AND fm_pool_remaining > 0
               THEN 'YES' ELSE 'NO' END as commit_exceeds_fm,
          CASE
            WHEN ps_commit_open_2026 > 0 AND fm_pool_remaining < 0 THEN 'PRE_FLIGHT_BLOCK_HARD'
            WHEN ps_commit_open_2026 > 0 AND fm_pool_remaining < ps_commit_open_2026 THEN 'PRE_FLIGHT_BLOCK_PARTIAL'
            ELSE 'PASS'
          END as pre_flight_verdict
        FROM _matrix
        ORDER BY fm_pool_remaining ASC, ps_commit_open_2026 DESC
    """)
    rows = cur.fetchall()
    headers = [d[0] for d in cur.description]
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow([f"{x:.2f}" if isinstance(x, float) else (x or "") for x in r])
    log(f"  Wrote {len(rows):,} rows")

    # 10. Top 20 worst (highest pre-flight risk)
    log("Step 10: Top 20 worst pairs (highest commit-vs-available gap)")
    log("Format: fund | wbs | post1 | n_commit | ps_commit | fm_pool_remaining | verdict")
    log("-" * 120)
    for r in cur.execute("""
        SELECT fund, wbs_objnr, wbs_post1, n_commit_lines,
               ps_commit_open_2026, fm_pool_remaining,
               CASE
                 WHEN ps_commit_open_2026 > 0 AND fm_pool_remaining < 0 THEN 'BLOCK_HARD'
                 WHEN ps_commit_open_2026 > 0 AND fm_pool_remaining < ps_commit_open_2026 THEN 'BLOCK_PARTIAL'
                 ELSE 'PASS'
               END as verdict
        FROM _matrix
        WHERE ps_commit_open_2026 > 1000
        ORDER BY (ps_commit_open_2026 - fm_pool_remaining) DESC
        LIMIT 20
    """).fetchall():
        log(f"  {str(r[0])[:12]:12s} {str(r[1])[:12]:12s} {(str(r[2]) or '')[:30]:30s} n={r[3]:>4} commit=${r[4]:>15,.2f} fm_pool=${r[5]:>15,.2f} {r[6]}")

    log("=== DONE ===")
    con.close()


if __name__ == "__main__":
    main()
