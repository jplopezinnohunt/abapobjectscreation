"""
Discover unique payment scenarios in P01 production + extract 10 samples per scenario.

A SCENARIO = distinct combination of:
  - Tree (derived FORMI from T001+T042Z+RZAWE)
  - Co code (ZBUKR)
  - Vendor bank country (UBNKS)
  - Currency (WAERS)
  - Pay method (RZAWE)
  - Pay type (DORIGIN[0:2]: HR=P, TR=R, others=O)

For each scenario, sample 10 payments + their REGUP rows (with LZBKZ for PPC).

This is the dataset for V001 simulation: predict V000 vs V001 output per scenario,
verify nothing breaks.
"""
import sys, sqlite3, time, json
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')


def main():
    print('=== Scenario discovery + sampling ===')
    t0 = time.time()

    # Step 1: extend REGUH with DORIGIN if missing (check REGUH_DORIGIN table)
    sqlcon = sqlite3.connect(DB)
    cur = sqlcon.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='REGUH_DORIGIN'")
    has_dorigin = cur.fetchone() is not None
    if has_dorigin:
        cur.execute('SELECT COUNT(*) FROM REGUH_DORIGIN')
        if cur.fetchone()[0] > 0:
            print(f'Step 1: REGUH_DORIGIN already populated, skipping extraction')
            has_dorigin = True
        else:
            has_dorigin = False
    if not has_dorigin:
        print('Step 1: extracting DORIGIN to add to REGUH_FAST...')
        conn = get_connection('P01')
        rows = rfc_read_paginated(
            conn, 'REGUH',
            ['LAUFD', 'LAUFI', 'ZBUKR', 'LIFNR', 'DORIGIN'],
            where="LAUFD >= '20250101'",
            batch_size=10000, throttle=0.3)
        conn.close()
        print(f'   Got {len(rows):,} rows in {time.time()-t0:.0f}s')

        cur.execute('CREATE TABLE IF NOT EXISTS REGUH_DORIGIN (LAUFD TEXT, LAUFI TEXT, ZBUKR TEXT, LIFNR TEXT, DORIGIN TEXT)')
        cur.execute('DELETE FROM REGUH_DORIGIN')
        cur.executemany('INSERT INTO REGUH_DORIGIN VALUES (?,?,?,?,?)',
                        [(r.get('LAUFD',''), r.get('LAUFI',''), r.get('ZBUKR',''),
                          r.get('LIFNR',''), r.get('DORIGIN','')) for r in rows])
        cur.execute('CREATE INDEX IF NOT EXISTS idx_dorigin_key ON REGUH_DORIGIN(LAUFD,LAUFI,ZBUKR,LIFNR)')
        sqlcon.commit()
        print(f'   REGUH_DORIGIN written: {len(rows):,} rows')
    else:
        print('Step 1: DORIGIN already in REGUH_FAST, skipping')

    # Step 2: Discover unique scenarios
    print('\nStep 2: Discovering unique scenarios...')
    sql = """
    SELECT
      COALESCE(t042z.FORMI, 'NO_T042Z') as tree,
      regu.ZBUKR as co,
      regu.UBNKS as vendor_bank,
      regu.WAERS as cur,
      regu.RZAWE as pm,
      CASE
        WHEN SUBSTR(d.DORIGIN,1,2)='HR' THEN 'P'
        WHEN SUBSTR(d.DORIGIN,1,2)='TR' THEN 'R'
        ELSE 'O'
      END as pay_type,
      COUNT(*) as cnt
    FROM REGUH_FAST regu
    JOIN T001 t001 ON regu.ZBUKR = t001.BUKRS
    LEFT JOIN T042Z t042z ON t042z.LAND1 = t001.LAND1 AND t042z.ZLSCH = regu.RZAWE
    LEFT JOIN REGUH_DORIGIN d ON d.LAUFD=regu.LAUFD AND d.LAUFI=regu.LAUFI
                              AND d.ZBUKR=regu.ZBUKR AND d.LIFNR=regu.LIFNR
    GROUP BY tree, co, vendor_bank, cur, pm, pay_type
    HAVING cnt > 0
    ORDER BY cnt DESC
    """
    cur.execute(sql)
    scenarios = cur.fetchall()
    print(f'   {len(scenarios):,} unique scenarios discovered')

    # Filter to in-scope trees + tier-1 (>= 5 payments)
    target_trees = ('/SEPA_CT_UNES', '/CITI/XML/UNESCO/DC_V3_01',
                    '/CGI_XML_CT_UNESCO', '/CGI_XML_CT_UNESCO_1',
                    '/CGI_XML_CT_UNESCO_BK')
    in_scope = [s for s in scenarios if s[0] in target_trees and s[6] >= 5]
    print(f'   In-scope scenarios (>=5 payments, target trees): {len(in_scope)}')

    # Step 3: Sample 10 payments per in-scope scenario
    print('\nStep 3: Sampling 10 payments per scenario...')
    cur.execute('DROP TABLE IF EXISTS SCENARIO_SAMPLES')
    cur.execute("""
    CREATE TABLE SCENARIO_SAMPLES (
      scenario_id INTEGER,
      tree TEXT, co TEXT, vendor_bank TEXT, cur TEXT, pm TEXT, pay_type TEXT,
      total_count INTEGER,
      LAUFD TEXT, LAUFI TEXT, ZBUKR TEXT, LIFNR TEXT,
      RZAWE TEXT, HBKID TEXT, HKTID TEXT, UBNKS TEXT, WAERS TEXT,
      RWBTR TEXT, ZALDT TEXT, NAME1 TEXT, LAND1 TEXT, DORIGIN TEXT
    )
    """)
    inserted = 0
    for scenario_id, scenario in enumerate(in_scope, 1):
        tree, co, vbank, cur_, pm, ptype, cnt = scenario
        # Sample 10 random rows for this scenario; JOIN LFA1 for NAME1/LAND1
        cur.execute("""
        SELECT regu.LAUFD, regu.LAUFI, regu.ZBUKR, regu.LIFNR,
               regu.RZAWE, regu.HBKID, regu.HKTID, regu.UBNKS, regu.WAERS,
               regu.RWBTR, regu.ZALDT, lfa1.NAME1, lfa1.LAND1, d.DORIGIN
        FROM REGUH_FAST regu
        JOIN T001 t001 ON regu.ZBUKR = t001.BUKRS
        LEFT JOIN T042Z t042z ON t042z.LAND1 = t001.LAND1 AND t042z.ZLSCH = regu.RZAWE
        LEFT JOIN REGUH_DORIGIN d ON d.LAUFD=regu.LAUFD AND d.LAUFI=regu.LAUFI
                                  AND d.ZBUKR=regu.ZBUKR AND d.LIFNR=regu.LIFNR
        LEFT JOIN LFA1 lfa1 ON regu.LIFNR = lfa1.LIFNR
        WHERE COALESCE(t042z.FORMI, 'NO_T042Z') = ?
          AND regu.ZBUKR = ?
          AND regu.UBNKS = ?
          AND regu.WAERS = ?
          AND regu.RZAWE = ?
          AND CASE
                WHEN SUBSTR(COALESCE(d.DORIGIN,''),1,2)='HR' THEN 'P'
                WHEN SUBSTR(COALESCE(d.DORIGIN,''),1,2)='TR' THEN 'R'
                ELSE 'O'
              END = ?
        LIMIT 10
        """, (tree, co, vbank, cur_, pm, ptype))
        samples = cur.fetchall()
        for s in samples:
            cur.execute("""
            INSERT INTO SCENARIO_SAMPLES VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (scenario_id, tree, co, vbank, cur_, pm, ptype, cnt, *s))
            inserted += 1
    sqlcon.commit()
    print(f'   {inserted} sample rows inserted (10 per scenario, {len(in_scope)} scenarios)')

    # Step 4: Get REGUP for sampled payments — LIFNR-based (simpler WHERE)
    print('\nStep 4: Getting REGUP for sampled payments via LIFNR list...')
    cur.execute('SELECT DISTINCT LIFNR FROM SCENARIO_SAMPLES')
    lifnrs = [r[0] for r in cur.fetchall()]
    print(f'   {len(lifnrs)} distinct LIFNRs to extract REGUP from')

    conn = get_connection('P01')
    all_regup = []
    for i, lifnr in enumerate(lifnrs):
        where = f"LIFNR = '{lifnr}' AND LAUFD >= '20250101'"
        try:
            rows = rfc_read_paginated(conn, 'REGUP',
                ['LAUFD','LAUFI','ZBUKR','LIFNR','BELNR','GJAHR','BUZEI','LZBKZ','XBLNR','BLDAT','SGTXT','WRBTR','WAERS'],
                where=where, batch_size=500, throttle=0.1)
            all_regup.extend(rows)
        except Exception as e:
            print(f'   LIFNR {lifnr} ERROR: {str(e)[:80]}')
        if i % 50 == 0:
            print(f'   LIFNR {i}/{len(lifnrs)}: {len(all_regup):,} REGUP rows so far')
    print(f'   REGUP rows: {len(all_regup):,}')
    conn.close()

    cur.execute('DROP TABLE IF EXISTS REGUP_SCENARIOS')
    regup_cols = ['LAUFD','LAUFI','ZBUKR','LIFNR','BELNR','GJAHR','BUZEI','LZBKZ','XBLNR','BLDAT','SGTXT','WRBTR','WAERS']
    cur.execute('CREATE TABLE REGUP_SCENARIOS (' + ', '.join(f'"{c}" TEXT' for c in regup_cols) + ')')
    p = ', '.join('?' * len(regup_cols))
    cur.executemany(f'INSERT INTO REGUP_SCENARIOS VALUES ({p})',
                     [[r.get(c, '') for c in regup_cols] for r in all_regup])
    sqlcon.commit()

    # Step 5: Output discovery summary
    print('\nStep 5: Scenario summary')
    summary = {'total_scenarios': len(in_scope), 'total_samples': inserted,
               'regup_rows': len(all_regup), 'scenarios': [
        {'id': i+1, 'tree': s[0], 'co': s[1], 'vendor_bank': s[2],
         'cur': s[3], 'pm': s[4], 'pay_type': s[5], 'count': s[6]}
        for i, s in enumerate(in_scope)
    ]}
    out_path = Path('knowledge/domains/Payment/phase0/scenario_discovery.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f'   Summary: {out_path}')

    # Print top scenarios
    print('\nTop 30 scenarios by volume:')
    for s in in_scope[:30]:
        print(f'  T={s[0]:30s} co={s[1]:5s} bank={s[2] or "(empty)":5s} '
              f'cur={s[3]:4s} pm={s[4] or "(empty)":3s} pt={s[5]:1s} cnt={s[6]:>6,}')

    sqlcon.close()
    print(f'\nDONE in {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
