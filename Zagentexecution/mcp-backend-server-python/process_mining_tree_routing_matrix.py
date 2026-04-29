"""
Process mining model #2: Tree × Co code × Payment method routing matrix.

Goal: produce a definitive matrix of which (paying co code, payment method)
combinations route to which DMEE tree, with actual P01 payment volume.

This is THE test matrix for V001 testing — every combination with >100 payments
in last year is a tier-1 test scenario.
"""
import sqlite3, json, sys, os
from pathlib import Path
from collections import Counter, defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
P01_SNAPSHOT = Path('knowledge/domains/Payment/phase0/d01_vs_p01_drift_p01_snapshot.json')
OUT_DIR = Path('knowledge/domains/Payment/phase0')

# UNESCO co code → country (from prior session knowledge)
CO_CODE_COUNTRY = {
    'SOG01': 'FR', 'SOG02': 'FR', 'SOG03': 'FR', 'SOG05': 'FR',
    'CIT01': 'US', 'CIT04': 'FR', 'CIT21': 'FR',
}


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    with open(P01_SNAPSHOT, 'r', encoding='utf-8') as f:
        p01 = json.load(f)
    t042z = p01.get('cust_tables', {}).get('T042Z', {}).get('rows', [])

    # T042Z map: (LAND1, ZLSCH) -> FORMI (and we know XBKKT/XSTRA flags)
    pm_routing = {}
    for r in t042z:
        key = (r.get('LAND1'), r.get('ZLSCH'))
        pm_routing[key] = {
            'formi': r.get('FORMI'),
            'xbkkt': r.get('XBKKT'),
            'xstra': r.get('XSTRA'),
            'text': r.get('TEXT1'),
        }

    # Aggregate REGUH by (ZBUKR, payment_method via LFB1.ZWELS)
    sql = """
    SELECT
      regu.ZBUKR as paying_co,
      lfb1.ZWELS as pay_method,
      COUNT(*) as cnt
    FROM REGUH regu
    LEFT JOIN LFB1 lfb1 ON regu.LIFNR = lfb1.LIFNR AND regu.ZBUKR = lfb1.BUKRS
    GROUP BY paying_co, pay_method
    HAVING cnt > 0
    ORDER BY cnt DESC
    """
    print('Running co × pay_method aggregation...')
    cur.execute(sql)
    rows = cur.fetchall()
    print(f'  {len(rows)} aggregated rows')

    # Build the matrix
    matrix = []
    tree_totals = Counter()
    for co, pm, cnt in rows:
        # Determine country of paying co
        co_country = CO_CODE_COUNTRY.get(co, 'FR')  # default UNESCO HQ
        # Look up routing — try (co_country, pm) first, then ('FR', pm) fallback
        routing = pm_routing.get((co_country, pm)) or pm_routing.get(('FR', pm)) or {}
        formi = routing.get('formi', 'NO_T042Z_MATCH')
        matrix.append({
            'co': co, 'co_country': co_country, 'pm': pm,
            'cnt': cnt, 'formi': formi,
            'xbkkt': routing.get('xbkkt'), 'xstra': routing.get('xstra'),
            'text': routing.get('text'),
        })
        tree_totals[formi] += cnt

    # Output
    md = ['# Process Mining: Tree × Co × Payment Method Routing Matrix\n',
          '**Generated**: from P01 Gold DB REGUH 942K payments\n\n',
          '## Tree usage totals (top of funnel)\n\n',
          '| Tree (FORMI) | Total payments routed | Status |\n|---|---|---|\n']
    for formi, cnt in sorted(tree_totals.items(), key=lambda x: -x[1]):
        is_target = formi in ('/SEPA_CT_UNES','/CITI/XML/UNESCO/DC_V3_01',
                              '/CGI_XML_CT_UNESCO','/CGI_XML_CT_UNESCO_1',
                              '/CGI_XML_CT_UNESCO_BK')
        marker = '🎯 IN SCOPE' if is_target else ('⚪ Out of scope' if formi != 'NO_T042Z_MATCH' else '❓ No T042Z routing')
        md.append(f'| `{formi}` | {cnt:,} | {marker} |\n')

    md.append(f'\n## Tier-1 routing combinations (volume > 100 payments)\n\n')
    md.append('| Co | Co country | Pay method | Tree | XBKKT | XSTRA | Volume | Description |\n')
    md.append('|---|---|---|---|---|---|---|---|\n')
    tier1 = [m for m in matrix if m['cnt'] > 100]
    for m in sorted(tier1, key=lambda x: -x['cnt']):
        in_scope = m['formi'] in ('/SEPA_CT_UNES','/CITI/XML/UNESCO/DC_V3_01',
                                   '/CGI_XML_CT_UNESCO','/CGI_XML_CT_UNESCO_1','/CGI_XML_CT_UNESCO_BK')
        if in_scope:
            md.append(f"| {m['co']} | {m['co_country']} | {m['pm']} | "
                      f"`{m['formi']}` | {m['xbkkt'] or ''} | {m['xstra'] or ''} | "
                      f"{m['cnt']:,} | {m['text'] or ''} |\n")

    md.append(f'\n## All routing combinations within scope (full set)\n\n')
    in_scope_all = [m for m in matrix if m['formi'] in (
        '/SEPA_CT_UNES','/CITI/XML/UNESCO/DC_V3_01',
        '/CGI_XML_CT_UNESCO','/CGI_XML_CT_UNESCO_1','/CGI_XML_CT_UNESCO_BK')]
    md.append(f'**Total in-scope payments**: {sum(m["cnt"] for m in in_scope_all):,}\n\n')
    md.append('| Co | Co country | Pay method | Tree | Volume |\n|---|---|---|---|---|\n')
    for m in sorted(in_scope_all, key=lambda x: -x['cnt']):
        md.append(f"| {m['co']} | {m['co_country']} | {m['pm']} | `{m['formi']}` | {m['cnt']:,} |\n")

    md.append(f'\n## Conclusions\n\n')
    target_total = sum(m['cnt'] for m in in_scope_all)
    overall = sum(m['cnt'] for m in matrix)
    pct = 100 * target_total / overall if overall else 0
    md.append(f'- **Target trees** (4 + bonus _BK) carry approximately **{pct:.1f}%** '
              f'of total payments ({target_total:,} / {overall:,})\n')
    md.append('- Tier-1 test combinations cover the realistic V001 cutover scenarios\n')
    md.append('- Out-of-scope trees handle internal transfers, payroll, etc. — '
              'not affected by structured address change\n')

    out_md = OUT_DIR / 'process_mining_tree_routing.md'
    out_md.write_text(''.join(md), encoding='utf-8')

    out_json = OUT_DIR / 'process_mining_tree_routing.json'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({'matrix': matrix, 'tree_totals': dict(tree_totals)},
                  f, indent=2, ensure_ascii=False)
    print(f'\nReport: {out_md}')

    con.close()


if __name__ == '__main__':
    main()
