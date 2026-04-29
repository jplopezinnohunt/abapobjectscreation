"""
Process mining model #1: Country dispatcher usage frequency.

Goal: validate active vs dead inventory of CL_IDFI_CGI_CALL05_<country> classes
with REAL P01 production traffic. The dispatcher fires per-payment based on
vendor's bank country (LFBK.BANKS), so counting payments by bank country
quantifies which country dispatchers are actually exercised.

Data sources (Gold DB P01):
- REGUH: 942K payment headers (ZBUKR + LIFNR per F110 run)
- LFBK: 202K vendor bank entries (LIFNR → BANKS = bank country)
- LFA1: 316K vendor master (LIFNR → LAND1 = vendor country)
- LFB1: 327K vendor co code data (LIFNR + BUKRS → ZWELS = payment method)
- T042Z: in P01 snapshot — maps (LAND1, ZLSCH, BUKRS) → FORMI (DMEE tree)

Outputs:
- knowledge/domains/Payment/phase0/process_mining_dispatcher_usage.md
- knowledge/domains/Payment/phase0/process_mining_dispatcher_usage.json
"""
import sqlite3, json, sys, os
from pathlib import Path
from collections import Counter, defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
P01_SNAPSHOT = Path('knowledge/domains/Payment/phase0/d01_vs_p01_drift_p01_snapshot.json')
OUT_DIR = Path('knowledge/domains/Payment/phase0')


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # Load T042Z mapping from P01 snapshot
    with open(P01_SNAPSHOT, 'r', encoding='utf-8') as f:
        p01 = json.load(f)
    t042z = p01.get('cust_tables', {}).get('T042Z', {}).get('rows', [])
    # Build (LAND1, ZLSCH) -> FORMI map
    pm_to_tree = {}
    for r in t042z:
        key = (r.get('LAND1', ''), r.get('ZLSCH', ''))
        pm_to_tree[key] = r.get('FORMI', '')

    print('=== Process mining: country dispatcher usage frequency ===\n')

    # 1. REGUH joined with LFBK (vendor bank country) and LFB1 (payment method)
    sql = """
    SELECT
      lfbk.BANKS as bank_country,
      lfb1.ZWELS as pay_method,
      lfa1.LAND1 as vendor_country,
      regu.ZBUKR as paying_co,
      COUNT(*) as payment_count
    FROM REGUH regu
    LEFT JOIN LFB1 lfb1 ON regu.LIFNR = lfb1.LIFNR AND regu.ZBUKR = lfb1.BUKRS
    LEFT JOIN LFBK lfbk ON regu.LIFNR = lfbk.LIFNR
    LEFT JOIN LFA1 lfa1 ON regu.LIFNR = lfa1.LIFNR
    GROUP BY bank_country, pay_method, vendor_country, paying_co
    ORDER BY payment_count DESC
    LIMIT 200
    """
    print('Running aggregation query (this may take a moment)...')
    cur.execute(sql)
    raw = cur.fetchall()
    print(f'  {len(raw)} aggregated rows')

    # 2. Aggregate by bank_country (= which country dispatcher fires)
    by_bank_country = Counter()
    by_vendor_country = Counter()
    by_co_pm = Counter()
    by_combo = []
    for bank, pm, vendor, co, cnt in raw:
        by_bank_country[bank or '(empty)'] += cnt
        by_vendor_country[vendor or '(empty)'] += cnt
        by_co_pm[(co, pm)] += cnt
        by_combo.append({'bank_country': bank, 'pay_method': pm, 'vendor_country': vendor,
                          'paying_co': co, 'count': cnt})

    # 3. Map dispatcher class to traffic
    sap_dispatchers = ['AT','AU','BE','BG','CA','CH','CN','CZ','DE','DK','EE','ES','FALLBACK',
                       'FR','GB','HK','HR','IE','IT','LT','LU','MX','PL','PT','RO','SE','SK',
                       'TW','US','GENERIC','USAGE']
    dispatcher_traffic = {}
    for ctry in sap_dispatchers:
        if ctry in ('FALLBACK', 'GENERIC', 'USAGE'):
            continue  # not country-specific
        cnt = by_bank_country.get(ctry, 0)
        dispatcher_traffic[f'CL_IDFI_CGI_CALL05_{ctry}'] = cnt

    # 4. Tree usage frequency via T042Z lookup
    tree_usage = Counter()
    for c in by_combo:
        co = c['paying_co']; pm = c['pay_method']; vendor_ctry = c['vendor_country']
        # T042Z key is (co_country, payment_method) — need co_country from BUKRS
        # Skip — would need to JOIN T001 to get BUKRS->LAND1. For now use proxy:
        # if (vendor_ctry, pm) in pm_to_tree, attribute traffic to tree
        formi = pm_to_tree.get((vendor_ctry, pm), '')
        if not formi:
            formi = pm_to_tree.get(('FR', pm), '')  # UNESCO HQ fallback
        if formi:
            tree_usage[formi] += c['count']

    # Output report
    md = ['# Process Mining: Country Dispatcher Usage Frequency\n',
          '**Generated**: from P01 Gold DB REGUH 942K payments\n\n',
          '## Goal\n\n',
          'Validate active vs dead inventory of `CL_IDFI_CGI_CALL05_<country>` SAP-std '
          'dispatcher classes with REAL production traffic. A dispatcher fires when a '
          'vendor\'s bank is in the matching country. Zero traffic = zero dispatcher exercise.\n\n']

    md.append('## Top 20 vendor bank countries by payment volume\n\n')
    md.append('| Rank | Bank country | Payments | Dispatcher exercised | Status |\n')
    md.append('|---|---|---|---|---|\n')
    top20 = by_bank_country.most_common(20)
    for i, (ctry, cnt) in enumerate(top20, 1):
        if not ctry or ctry == '(empty)':
            disp = '-'
            status = 'Empty (no LFBK record — likely one-time vendor or domestic SEPA)'
        else:
            cls = f'CL_IDFI_CGI_CALL05_{ctry}'
            extracted = ctry in sap_dispatchers
            disp = cls if extracted else f'(no SAP-std class for {ctry} — falls through to GENERIC)'
            status = 'EXTRACTED' if extracted else 'GENERIC fallback'
        md.append(f'| {i} | {ctry} | {cnt:,} | `{disp}` | {status} |\n')

    md.append(f'\n## Country dispatchers — extracted vs traffic\n\n')
    md.append('| Class | Country | Payments to vendors with bank in this country | Verdict |\n')
    md.append('|---|---|---|---|\n')
    for cls, cnt in sorted(dispatcher_traffic.items(), key=lambda x: -x[1]):
        ctry = cls.replace('CL_IDFI_CGI_CALL05_', '')
        if cnt > 1000:
            v = '🔥 HIGH usage'
        elif cnt > 100:
            v = '✅ Active'
        elif cnt > 0:
            v = '⚠️ Low traffic (probably extracted as scaffolding, rarely exercised)'
        else:
            v = '💀 ZERO traffic (extracted but never exercised — DEAD)'
        md.append(f'| `{cls}` | {ctry} | {cnt:,} | {v} |\n')

    md.append(f'\n## Tree usage frequency (proxy — vendor LAND1 + payment method)\n\n')
    md.append('| Tree | Estimated payment volume |\n|---|---|\n')
    for tree, cnt in sorted(tree_usage.items(), key=lambda x: -x[1]):
        md.append(f'| `{tree}` | {cnt:,} |\n')

    md.append(f'\n## Top 30 (paying_co × payment_method) combinations\n\n')
    md.append('| Co code | Pay method | Payments |\n|---|---|---|\n')
    for (co, pm), cnt in by_co_pm.most_common(30):
        md.append(f'| {co} | {pm} | {cnt:,} |\n')

    md.append(f'\n## Top 30 vendor countries by payment volume\n\n')
    md.append('| Rank | Vendor LAND1 | Payments |\n|---|---|---|\n')
    for i, (vctry, cnt) in enumerate(by_vendor_country.most_common(30), 1):
        md.append(f'| {i} | {vctry} | {cnt:,} |\n')

    md.append(f'\n## Conclusions\n\n')
    md.append('- **DE/IT class retrofit value**: quantified by counting payments where '
              'vendor bank country = DE / IT (above)\n')
    md.append('- **Dead country dispatcher candidates**: classes with 0 traffic — extracted '
              'but never exercised in P01\n')
    md.append('- **Test matrix priority**: top 80% of (co × pay_method × vendor_country) '
              'combinations cover the realistic scenarios for V001 testing\n')

    out_md = OUT_DIR / 'process_mining_dispatcher_usage.md'
    out_md.write_text(''.join(md), encoding='utf-8')

    out_json = OUT_DIR / 'process_mining_dispatcher_usage.json'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({
            'top20_bank_country': top20,
            'dispatcher_traffic': dispatcher_traffic,
            'tree_usage': dict(tree_usage),
            'top30_co_pm': [(f'{co}|{pm}', cnt) for (co,pm), cnt in by_co_pm.most_common(30)],
            'top30_vendor_country': by_vendor_country.most_common(30),
        }, f, indent=2, ensure_ascii=False)

    print(f'\nReport: {out_md}')
    print(f'Raw:    {out_json}')

    con.close()


if __name__ == '__main__':
    main()
