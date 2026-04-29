"""
Process mining model #3: Address DQ for ACTIVE-payment vendors only.

Goal: Phase 0 Finding A reported 5 vendors missing CITY1+COUNTRY of 111K active.
But that's all active vendors. The relevant question for V001 is:
*Of the vendors that ACTUALLY received payments via our 4 target trees, how many
have full structured address?*

Active payment vendor = appeared in REGUH at least once.
"""
import sqlite3, json, sys
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
OUT_DIR = Path('knowledge/domains/Payment/phase0')


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    print('=== Process mining: address DQ for active payment vendors ===\n')

    # Distinct vendors that received at least one payment
    cur.execute("""
        SELECT DISTINCT regu.LIFNR, lfa1.LAND1, adrc.STREET, adrc.HOUSE_NUM1,
                        adrc.POST_CODE1, adrc.CITY1, adrc.COUNTRY,
                        COUNT(*) OVER (PARTITION BY regu.LIFNR) as payment_count
        FROM REGUH regu
        LEFT JOIN LFA1 lfa1 ON regu.LIFNR = lfa1.LIFNR
        LEFT JOIN ADRC adrc ON lfa1.ADRNR = adrc.ADDRNUMBER
    """)
    rows = cur.fetchall()
    print(f'Distinct active payment vendors: {len(set(r[0] for r in rows))}')

    # Aggregate DQ per vendor
    vendor_dq = {}
    for lifnr, land1, street, house, postcode, city, country, cnt in rows:
        if lifnr not in vendor_dq:
            vendor_dq[lifnr] = {
                'land1': land1, 'street': street, 'house': house,
                'postcode': postcode, 'city': city, 'country': country,
                'payment_count': cnt,
            }

    total_active = len(vendor_dq)
    missing_country = sum(1 for v in vendor_dq.values() if not v['country'])
    missing_city = sum(1 for v in vendor_dq.values() if not v['city'])
    missing_postcode = sum(1 for v in vendor_dq.values() if not v['postcode'])
    missing_street = sum(1 for v in vendor_dq.values() if not v['street'])
    missing_house = sum(1 for v in vendor_dq.values() if not v['house'])
    missing_mandatory = sum(1 for v in vendor_dq.values()
                            if not v['city'] or not v['country'])

    md = ['# Process Mining: Address DQ for Active Payment Vendors\n',
          '**Generated**: from P01 Gold DB REGUH+LFA1+ADRC\n\n',
          '## Scope refinement\n\n',
          'Phase 0 Finding A reported 5/111K vendors missing CITY1+COUNTRY. '
          'But that included all active vendors. Real V001 risk is among vendors '
          'that **actually received payments via our 4 target trees** in production.\n\n',
          f'**Active payment vendor count**: {total_active:,}\n\n',
          '## Address DQ per CBPR+ tag (CBPR+ Hybrid minimum = TwnNm + Ctry)\n\n',
          '| Tag | Missing | % missing | Severity |\n',
          '|---|---|---|---|\n']
    md.append(f'| `<Ctry>` | {missing_country:,} | {100*missing_country/total_active:.2f}% | **CRITICAL** if >0 |\n')
    md.append(f'| `<TwnNm>` | {missing_city:,} | {100*missing_city/total_active:.2f}% | **CRITICAL** if >0 |\n')
    md.append(f'| `<PstCd>` | {missing_postcode:,} | {100*missing_postcode/total_active:.2f}% | OPTIONAL but preferred |\n')
    md.append(f'| `<StrtNm>` | {missing_street:,} | {100*missing_street/total_active:.2f}% | OPTIONAL |\n')
    md.append(f'| `<BldgNb>` | {missing_house:,} | {100*missing_house/total_active:.2f}% | OPTIONAL |\n')
    md.append(f'\n**CBPR+ blockers** (missing TwnNm OR Ctry): **{missing_mandatory:,} vendors '
              f'({100*missing_mandatory/total_active:.3f}% of active payment base)**\n\n')

    md.append('## Country distribution of active payment vendors (top 30)\n\n')
    by_ctry = Counter(v['land1'] or '(empty)' for v in vendor_dq.values())
    md.append('| Vendor LAND1 | Active vendors | % of total |\n|---|---|---|\n')
    for ctry, cnt in by_ctry.most_common(30):
        md.append(f'| {ctry} | {cnt:,} | {100*cnt/total_active:.2f}% |\n')

    # Find blocker vendors
    blockers = [(lifnr, v) for lifnr, v in vendor_dq.items()
                if (not v['city'] or not v['country']) and v['payment_count'] > 0]
    md.append(f'\n## Blocker vendor list ({len(blockers)} vendors)\n\n')
    md.append('| LIFNR | LAND1 | Missing | Recent payments |\n|---|---|---|---|\n')
    for lifnr, v in sorted(blockers, key=lambda x: -x[1]['payment_count'])[:20]:
        missing = []
        if not v['city']: missing.append('CITY1')
        if not v['country']: missing.append('COUNTRY')
        md.append(f"| {lifnr} | {v['land1'] or ''} | {', '.join(missing)} | {v['payment_count']} |\n")

    md.append('\n## Conclusions\n\n')
    if missing_mandatory == 0:
        md.append('🎉 **ZERO active-payment vendors have CBPR+ blocker fields missing**. '
                  'The 5 originally flagged in Finding A had zero recent payment activity '
                  '— they would not have been hit by V001 cutover. Risk reassessed downward.\n')
    else:
        md.append(f'⚠️ **{missing_mandatory} active-payment vendors are CBPR+ blockers**. '
                  'Master Data team must fix these BEFORE V001 cutover or those payments '
                  'will fail bank validation.\n')

    out_md = OUT_DIR / 'process_mining_address_dq_active.md'
    out_md.write_text(''.join(md), encoding='utf-8')
    out_json = OUT_DIR / 'process_mining_address_dq_active.json'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({
            'total_active': total_active,
            'missing_country': missing_country,
            'missing_city': missing_city,
            'missing_postcode': missing_postcode,
            'missing_street': missing_street,
            'missing_house': missing_house,
            'missing_mandatory': missing_mandatory,
            'by_country_top30': by_ctry.most_common(30),
            'blocker_vendors': [(l, v) for l, v in blockers[:50]],
        }, f, indent=2, ensure_ascii=False, default=str)

    print(f'\nReport: {out_md}')
    con.close()


if __name__ == '__main__':
    main()
