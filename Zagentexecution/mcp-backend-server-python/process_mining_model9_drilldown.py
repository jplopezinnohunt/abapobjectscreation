"""
Model 9 drill-down: HBKID × vendor country emission matrix.

Top finding: SOG01/CIT01/CIT04 carry ~67% of all UNESCO payments.
Now drill down: from each HBKID, which vendor countries does it emit to?

This produces THE definitive test matrix:
- Every (HBKID, vendor_country) combination → 1 test case in V001 testing
- Volume gives priority
"""
import sqlite3, json, sys
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
OUT_DIR = Path('knowledge/domains/Payment/phase0')

IN_SCOPE_HBK = ['SOG01','SOG02','SOG03','SOG05','CIT01','CIT04','CIT21']


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    print('=== Model 9 drill-down: HBKID × vendor country ===\n')

    # 1. HBKID × vendor bank country (where the money goes, country-of-bank)
    print('1. HBKID × vendor bank country (LFBK.BANKS) ...')
    sql = """
    SELECT
      regu.HBKID as hbkid,
      lfbk.BANKS as vendor_bank_ctry,
      lfa1.LAND1 as vendor_address_ctry,
      COUNT(*) as cnt
    FROM REGUH regu
    LEFT JOIN LFBK lfbk ON regu.LIFNR = lfbk.LIFNR
    LEFT JOIN LFA1 lfa1 ON regu.LIFNR = lfa1.LIFNR
    WHERE regu.HBKID != ''
    GROUP BY hbkid, vendor_bank_ctry, vendor_address_ctry
    HAVING cnt > 5
    ORDER BY cnt DESC
    """
    cur.execute(sql)
    rows = cur.fetchall()
    print(f'  {len(rows)} aggregated rows')

    # Build per-hbkid drill-down
    by_hbkid = defaultdict(list)
    for hbk, vbnk, vctry, cnt in rows:
        by_hbkid[hbk].append({'bank_ctry': vbnk, 'addr_ctry': vctry, 'cnt': cnt})

    # 2. Recent year — only ZALDT >= 2024 (need to use REGUH which doesn't have ZALDT —
    #    use BKPF.BUDAT via VBLNR? Or check for REGUH_FULL availability)
    try:
        cur.execute('SELECT COUNT(*) FROM REGUH_FULL WHERE ZALDT >= "20240101"')
        recent_count = cur.fetchone()[0]
        print(f'2. Recent (2024+) payment count via REGUH_FULL: {recent_count:,}')
    except sqlite3.OperationalError:
        recent_count = None

    # 3. Top vendors per top HBKID (drill into who gets paid)
    print('3. Top 10 vendors per in-scope HBKID...')
    top_vendors_per_hbk = {}
    for hbk in IN_SCOPE_HBK:
        cur.execute(f"""
        SELECT regu.LIFNR, lfa1.NAME1, lfa1.LAND1, lfbk.BANKS, COUNT(*) cnt
        FROM REGUH regu
        LEFT JOIN LFA1 lfa1 ON regu.LIFNR = lfa1.LIFNR
        LEFT JOIN LFBK lfbk ON regu.LIFNR = lfbk.LIFNR
        WHERE regu.HBKID = ?
        GROUP BY regu.LIFNR
        ORDER BY cnt DESC LIMIT 10
        """, (hbk,))
        top_vendors_per_hbk[hbk] = cur.fetchall()

    # Output
    md = ['# PM Model 9 Drill-down — HBKID × Vendor matrix\n',
          '**Generated**: P01 Gold DB REGUH × LFBK × LFA1\n\n',
          '## Test matrix coverage (data-driven from production traffic)\n\n',
          'Goal: every test case in V001 maps to a real (HBKID, vendor country) combination '
          'that exists in production. Volume gives priority.\n\n']

    md.append('## Per HBKID — top vendor bank countries\n\n')
    for hbk in sorted(by_hbkid, key=lambda h: -sum(x['cnt'] for x in by_hbkid[h])):
        rows_hbk = sorted(by_hbkid[hbk], key=lambda x: -x['cnt'])[:15]
        total = sum(x['cnt'] for x in by_hbkid[hbk])
        in_scope = '🎯 IN SCOPE' if hbk in IN_SCOPE_HBK else '⚪ Out of scope'
        md.append(f'\n### {hbk} — {total:,} payments — {in_scope}\n\n')
        md.append('| Vendor bank country | Vendor address country | Payments |\n|---|---|---|\n')
        for r in rows_hbk:
            md.append(f"| {r['bank_ctry'] or '(empty)'} | {r['addr_ctry'] or '(empty)'} | {r['cnt']:,} |\n")

    md.append('\n## Top 10 vendors per in-scope HBKID (drill-down by recipient)\n\n')
    for hbk in IN_SCOPE_HBK:
        rows_v = top_vendors_per_hbk.get(hbk, [])
        if not rows_v:
            continue
        md.append(f'\n### {hbk} top recipients\n\n')
        md.append('| LIFNR | Name | Address country | Bank country | Payments |\n|---|---|---|---|---|\n')
        for lifnr, name, ctry, bnk, cnt in rows_v:
            md.append(f"| {lifnr} | {(name or '')[:40]} | {ctry or ''} | {bnk or ''} | {cnt:,} |\n")

    md.append('\n## Test matrix proposal — V001 unit tests\n\n')
    md.append('Tier 1 (mandatory, >1000 payments):\n\n')
    tier1 = []
    for hbk in IN_SCOPE_HBK:
        for r in by_hbkid.get(hbk, []):
            if r['cnt'] > 1000:
                tier1.append((hbk, r))
    md.append('| Test # | HBKID | Vendor bank country | Volume |\n|---|---|---|---|\n')
    for i, (hbk, r) in enumerate(sorted(tier1, key=lambda x: -x[1]['cnt'])[:30], 1):
        md.append(f"| T{i:02d} | {hbk} | {r['bank_ctry']} | {r['cnt']:,} |\n")

    out_md = OUT_DIR / 'process_mining_model9_drilldown.md'
    out_md.write_text(''.join(md), encoding='utf-8')
    out_json = OUT_DIR / 'process_mining_model9_drilldown.json'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({
            'by_hbkid': {h: v for h, v in by_hbkid.items()},
            'top_vendors_per_hbk': {h: [list(r) for r in v] for h, v in top_vendors_per_hbk.items()},
            'tier1_tests': [(h, r) for h, r in tier1],
            'recent_2024_count': recent_count,
        }, f, indent=2, ensure_ascii=False, default=str)
    print(f'\nReport: {out_md}')

    con.close()


if __name__ == '__main__':
    main()
