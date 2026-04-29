"""
Definitive HBKID × Tree mapping — config-derived, NOT inferred.

JOIN chain (anchored on P01 customizing):
  REGUH_FULL.RZAWE (actual payment method per F110 run)
  + T001.LAND1 (paying co code's country)
  → T042Z lookup → FORMI = the REAL DMEE tree used

Plus per-year breakdown using REGUH_FULL.LAUFD (or ZALDT).
"""
import sqlite3, json, sys
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
OUT_DIR = Path('knowledge/domains/Payment/phase0')


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # Verify REGUH_FULL is ready
    try:
        cur.execute('SELECT COUNT(*) FROM REGUH_FULL')
        cnt = cur.fetchone()[0]
        print(f'REGUH_FULL has {cnt:,} rows')
    except sqlite3.OperationalError:
        print('REGUH_FULL not yet ready — abort.')
        return

    print('\n=== Definitive HBKID × Tree mapping (CONFIG-DERIVED) ===\n')

    # 1. The real JOIN — per F110 row, real tree from config
    sql = """
    SELECT
      regu.HBKID,
      regu.ZBUKR,
      t001.LAND1 as co_country,
      regu.RZAWE,
      COALESCE(t042z.FORMI, 'NO_T042Z_MATCH') as actual_tree,
      COALESCE(t042z.XBKKT, '') as xbkkt,
      COALESCE(t042z.XSTRA, '') as xstra,
      COALESCE(t042z.TEXT1, '') as t042z_text,
      COUNT(*) as cnt,
      SUM(CAST(NULLIF(regu.RWBTR,'') AS REAL)) as total_amt
    FROM REGUH_FULL regu
    JOIN T001 t001 ON regu.ZBUKR = t001.BUKRS
    LEFT JOIN T042Z t042z ON t042z.LAND1 = t001.LAND1 AND t042z.ZLSCH = regu.RZAWE
    GROUP BY regu.HBKID, regu.ZBUKR, regu.RZAWE
    ORDER BY cnt DESC
    """
    cur.execute(sql)
    rows = cur.fetchall()
    print(f'  Got {len(rows)} (HBKID,ZBUKR,RZAWE) combinations')

    # 2. Tree totals via real config
    tree_totals = defaultdict(lambda: {'cnt': 0, 'amt': 0})
    hbkid_tree = defaultdict(lambda: defaultdict(int))
    for hbk, co, ctry, rz, tree, xb, xs, txt, cnt, amt in rows:
        tree_totals[tree]['cnt'] += cnt
        tree_totals[tree]['amt'] += amt or 0
        hbkid_tree[hbk][tree] += cnt

    # 3. Per-year breakdown via LAUFD
    cur.execute("""
    SELECT
      regu.HBKID,
      SUBSTR(regu.LAUFD,1,4) as year,
      COALESCE(t042z.FORMI, 'NO_T042Z_MATCH') as tree,
      COUNT(*) as cnt
    FROM REGUH_FULL regu
    JOIN T001 t001 ON regu.ZBUKR = t001.BUKRS
    LEFT JOIN T042Z t042z ON t042z.LAND1 = t001.LAND1 AND t042z.ZLSCH = regu.RZAWE
    WHERE regu.LAUFD != ''
    GROUP BY regu.HBKID, year, tree
    """)
    yearly_rows = cur.fetchall()

    # Output
    md = ['# Definitive HBKID × Tree mapping — CONFIG-derived (no inference)\n',
          '**Generated**: from P01 Gold DB JOIN REGUH_FULL × T001 × T042Z\n\n',
          '## Method\n\n',
          'For each F110 payment in REGUH_FULL:\n',
          '1. Lookup paying co code country: `T001.BUKRS = REGUH.ZBUKR → T001.LAND1`\n',
          '2. Lookup actual payment method: `REGUH.RZAWE`\n',
          '3. Config lookup: `T042Z WHERE LAND1=co_country AND ZLSCH=RZAWE → FORMI`\n',
          '4. FORMI = the actual DMEE tree used at runtime\n\n']

    md.append('## Tree usage (REAL config-derived)\n\n')
    md.append('| Tree (FORMI) | Payments | Total amount | In scope? |\n|---|---|---|---|\n')
    target = ('/SEPA_CT_UNES','/CITI/XML/UNESCO/DC_V3_01',
              '/CGI_XML_CT_UNESCO','/CGI_XML_CT_UNESCO_1','/CGI_XML_CT_UNESCO_BK')
    for tree, info in sorted(tree_totals.items(), key=lambda x: -x[1]['cnt']):
        is_target = tree in target
        marker = '🎯 IN SCOPE' if is_target else ('⚪ Out of scope' if tree != 'NO_T042Z_MATCH' else '❓ unmapped')
        md.append(f"| `{tree}` | {info['cnt']:,} | {info['amt']:,.0f} | {marker} |\n")

    md.append('\n## HBKID × Tree (CONFIG-derived) — top 15 HBKIDs\n\n')
    md.append('| HBKID | Tree | Payments |\n|---|---|---|\n')
    for hbk in sorted(hbkid_tree, key=lambda h: -sum(hbkid_tree[h].values()))[:15]:
        for tree, cnt in sorted(hbkid_tree[hbk].items(), key=lambda x: -x[1]):
            in_scope = '🎯' if tree in target else ''
            md.append(f"| {hbk} | `{tree}` {in_scope} | {cnt:,} |\n")

    md.append('\n## Per-year breakdown (HBKID × Tree × Year)\n\n')
    by_year = defaultdict(lambda: defaultdict(int))
    by_year_tree = defaultdict(lambda: defaultdict(int))
    for hbk, year, tree, cnt in yearly_rows:
        if year:
            by_year[hbk][year] += cnt
            by_year_tree[(hbk, tree)][year] += cnt
    years_seen = sorted({y for hbk_data in by_year.values() for y in hbk_data})
    md.append('### Total payments per HBKID per year\n\n')
    md.append('| HBKID | ' + ' | '.join(years_seen) + ' |\n')
    md.append('|---' * (len(years_seen) + 1) + '|\n')
    for hbk in sorted(by_year, key=lambda h: -sum(by_year[h].values()))[:15]:
        cells = [f"{by_year[hbk].get(y, 0):,}" for y in years_seen]
        md.append(f"| {hbk} | " + ' | '.join(cells) + " |\n")

    md.append('\n### Top (HBKID, Tree) × Year (in-scope only)\n\n')
    md.append('| HBKID | Tree | ' + ' | '.join(years_seen) + ' | Total |\n')
    md.append('|---' * (len(years_seen) + 3) + '|\n')
    target_combos = [k for k in by_year_tree if k[1] in target]
    target_combos.sort(key=lambda k: -sum(by_year_tree[k].values()))
    for hbk, tree in target_combos[:25]:
        cells = [f"{by_year_tree[(hbk,tree)].get(y, 0):,}" for y in years_seen]
        total = sum(by_year_tree[(hbk,tree)].values())
        md.append(f"| {hbk} | `{tree}` | " + ' | '.join(cells) + f" | **{total:,}** |\n")

    md.append('\n## Test matrix (CONFIG-derived priorities)\n\n')
    md.append('Tier 1 (mandatory: combinations >1000 payments routing to in-scope trees):\n\n')
    md.append('| # | HBKID | Tree | Volume |\n|---|---|---|---|\n')
    for i, ((hbk, tree), years) in enumerate(target_combos[:15], 1):
        total = sum(years.values())
        if total > 1000:
            md.append(f"| T{i:02d} | {hbk} | `{tree}` | {total:,} |\n")

    out_md = OUT_DIR / 'process_mining_real_tree_per_payment.md'
    out_md.write_text(''.join(md), encoding='utf-8')
    out_json = OUT_DIR / 'process_mining_real_tree_per_payment.json'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({
            'tree_totals': {k: dict(v) for k, v in tree_totals.items()},
            'hbkid_tree': {h: dict(t) for h, t in hbkid_tree.items()},
            'years': years_seen,
            'by_year_top15': {h: dict(by_year[h]) for h in
                              sorted(by_year, key=lambda h: -sum(by_year[h].values()))[:15]},
        }, f, indent=2, ensure_ascii=False, default=str)
    print(f'\nReport: {out_md}')
    con.close()


if __name__ == '__main__':
    main()
