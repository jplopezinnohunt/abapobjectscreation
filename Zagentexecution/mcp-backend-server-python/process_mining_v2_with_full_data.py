"""
Process mining v2 — uses REGUH_FULL with RZAWE + UBNKS + WAERS + ZALDT.

Now that we have proper REGUH columns, run the full set of analyses:
1. Tree usage exact (RZAWE per payment + T042Z lookup)
2. Country dispatcher exact (UBNKS = bank country actually used at payment)
3. Currency distribution (WAERS) — CITI Worldlink subset
4. Temporal trends (ZALDT) — recent year focus
5. Co code × payment method × tree matrix
"""
import sqlite3, json, sys
from pathlib import Path
from collections import Counter, defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
OUT_DIR = Path('knowledge/domains/Payment/phase0')

UNESCO_CO_TO_COUNTRY = {
    'UNES': 'FR', 'IIEP': 'FR', 'UIL': 'DE', 'UBO': 'BR',
    'UIS': 'CA', 'ICTP': 'IT', 'OXX': 'GB', 'IICBA': 'NG',
}


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    print('=== Process Mining v2 (REGUH_FULL) ===\n')

    # 1. Tree usage via RZAWE → T042Z lookup
    print('1. Tree usage via RZAWE...')
    sql = """
    SELECT
      regu.ZBUKR as paying_co,
      regu.RZAWE as actual_pay_method,
      regu.UBNKS as bank_country_actual,
      regu.WAERS as currency,
      COUNT(*) as cnt,
      SUM(CAST(regu.RWBTR AS REAL)) as total_amount
    FROM REGUH_FULL regu
    GROUP BY paying_co, actual_pay_method, bank_country_actual, currency
    ORDER BY cnt DESC
    """
    cur.execute(sql)
    rows = cur.fetchall()
    print(f'  {len(rows)} aggregated combinations')

    # T042Z lookup for tree
    cur.execute('SELECT LAND1, ZLSCH, FORMI, XBKKT, XSTRA, TEXT1 FROM T042Z')
    t042z = {(l, z): {'formi': f, 'xbkkt': xb, 'xstra': xs, 'text': t}
             for l, z, f, xb, xs, t in cur.fetchall()}

    matrix = []
    tree_totals = Counter()
    for co, pm, bank_ctry, cur_, cnt, amt in rows:
        co_country = UNESCO_CO_TO_COUNTRY.get(co, 'FR')
        routing = t042z.get((co_country, pm)) or t042z.get(('FR', pm)) or {}
        formi = routing.get('formi', 'NO_T042Z_MATCH')
        matrix.append({
            'co': co, 'co_country': co_country, 'pm': pm,
            'bank_country': bank_ctry, 'currency': cur_,
            'count': cnt, 'amount': float(amt) if amt else 0,
            'formi': formi,
            'xbkkt': routing.get('xbkkt'),
            'xstra': routing.get('xstra'),
            'text': routing.get('text'),
        })
        tree_totals[formi] += cnt

    # 2. Country dispatcher actual firing (UBNKS)
    print('2. Country dispatcher firing (UBNKS)...')
    cur.execute("""
        SELECT UBNKS, COUNT(*) FROM REGUH_FULL
        WHERE UBNKS != '' AND UBNKS IS NOT NULL
        GROUP BY UBNKS ORDER BY 2 DESC LIMIT 50
    """)
    ubnks_distribution = cur.fetchall()

    # 3. Currency distribution (WAERS)
    print('3. Currency distribution...')
    cur.execute("""
        SELECT WAERS, COUNT(*), SUM(CAST(RWBTR AS REAL))
        FROM REGUH_FULL WHERE WAERS != ''
        GROUP BY WAERS ORDER BY 2 DESC LIMIT 30
    """)
    currency_dist = cur.fetchall()

    # 4. Temporal trends (last 5 years)
    print('4. Temporal trends...')
    cur.execute("""
        SELECT SUBSTR(ZALDT, 1, 4) as year, COUNT(*)
        FROM REGUH_FULL WHERE ZALDT >= '20200101'
        GROUP BY year ORDER BY year
    """)
    yearly = cur.fetchall()

    # 5. Recent traffic (last 12 months)
    print('5. Recent 12 months traffic...')
    cur.execute("""
        SELECT
          regu.ZBUKR as co,
          regu.RZAWE as pm,
          regu.UBNKS as bank_ctry,
          regu.WAERS as cur,
          COUNT(*) as cnt
        FROM REGUH_FULL regu
        WHERE regu.ZALDT >= '20240101'
        GROUP BY co, pm, bank_ctry, cur
        HAVING cnt > 50
        ORDER BY cnt DESC
        LIMIT 100
    """)
    recent_top = cur.fetchall()

    # Output
    md = ['# Process Mining v2 — REGUH_FULL data\n',
          '**Generated**: from Gold DB REGUH_FULL (27 cols), 942K payments\n\n']

    md.append('## 1. Tree usage by RZAWE (actual payment method)\n\n')
    md.append('| Tree (FORMI) | Total payments | Status |\n|---|---|---|\n')
    target = ('/SEPA_CT_UNES','/CITI/XML/UNESCO/DC_V3_01',
              '/CGI_XML_CT_UNESCO','/CGI_XML_CT_UNESCO_1','/CGI_XML_CT_UNESCO_BK')
    for formi, cnt in sorted(tree_totals.items(), key=lambda x: -x[1])[:30]:
        is_target = formi in target
        marker = '🎯 IN SCOPE' if is_target else ('⚪ Out of scope' if formi != 'NO_T042Z_MATCH' else '❓ unmapped')
        md.append(f'| `{formi}` | {cnt:,} | {marker} |\n')

    md.append('\n## 2. Country dispatcher exercised (UBNKS = bank country actually used)\n\n')
    md.append('| Bank country | Payments | Dispatcher | Verdict |\n|---|---|---|---|\n')
    sap_dispatchers = {'AT','AU','BE','BG','CA','CH','CN','CZ','DE','DK','EE','ES',
                       'FR','GB','HK','HR','IE','IT','LT','LU','MX','PL','PT',
                       'RO','SE','SK','TW','US'}
    for bnk, cnt in ubnks_distribution[:30]:
        if not bnk:
            continue
        cls = f'CL_IDFI_CGI_CALL05_{bnk}' if bnk in sap_dispatchers else f'GENERIC fallback'
        if cnt > 1000:
            verdict = '🔥 HIGH'
        elif cnt > 100:
            verdict = '✅ Active'
        else:
            verdict = '⚠️ Low'
        md.append(f'| {bnk} | {cnt:,} | `{cls}` | {verdict} |\n')

    md.append('\n## 3. Currency distribution (WAERS)\n\n')
    md.append('| Currency | Payments | Total amount |\n|---|---|---|\n')
    for cur_, cnt, amt in currency_dist[:20]:
        md.append(f'| {cur_ or "(empty)"} | {cnt:,} | {amt:,.0f} |\n')

    md.append('\n## 4. Temporal trends (ZALDT >= 2020)\n\n')
    md.append('| Year | Payments |\n|---|---|\n')
    for year, cnt in yearly:
        md.append(f'| {year} | {cnt:,} |\n')

    md.append('\n## 5. Top recent (last 12 months) traffic\n\n')
    md.append('| Co | Pay method | Bank ctry | Currency | Payments |\n|---|---|---|---|---|\n')
    for co, pm, bnk, cur_, cnt in recent_top[:30]:
        md.append(f'| {co} | {pm or "(empty)"} | {bnk or "(empty)"} | {cur_ or ""} | {cnt:,} |\n')

    # Test matrix priorities
    md.append('\n## Test matrix priority (combinations >100 payments routing to in-scope trees)\n\n')
    md.append('| Co | Pay method | Bank ctry | Currency | Tree | Volume |\n|---|---|---|---|---|---|\n')
    in_scope_combinations = [m for m in matrix
                              if m['formi'] in target and m['count'] > 100]
    for m in sorted(in_scope_combinations, key=lambda x: -x['count'])[:50]:
        md.append(f"| {m['co']} | {m['pm']} | {m['bank_country'] or ''} | "
                  f"{m['currency']} | `{m['formi']}` | {m['count']:,} |\n")

    out_md = OUT_DIR / 'process_mining_v2_full.md'
    out_md.write_text(''.join(md), encoding='utf-8')
    out_json = OUT_DIR / 'process_mining_v2_full.json'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({
            'tree_totals': dict(tree_totals),
            'ubnks_distribution': ubnks_distribution[:50],
            'currency_distribution': [(c, n, a) for c, n, a in currency_dist[:30]],
            'yearly': yearly,
            'recent_top100': [(c, p, b, w, n) for c, p, b, w, n in recent_top[:100]],
            'matrix_top100': sorted(matrix, key=lambda x: -x['count'])[:100],
        }, f, indent=2, ensure_ascii=False, default=str)

    print(f'Report: {out_md}')
    con.close()


if __name__ == '__main__':
    main()
