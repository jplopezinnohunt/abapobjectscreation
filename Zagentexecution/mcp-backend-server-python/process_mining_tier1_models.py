"""
Process mining Tier 1 — three highest-value models for V001 scope.

Model 6: Void/reverse payment patterns (REGUH.VOIDS, VOIDR if extracted)
Model 8: BCM batch lifecycle (BNK_BATCH_HEADER + BNK_BATCH_ITEM)
Model 9: Per-house-bank emission distribution (REGUH.HBKID + T012)
Model 10: Worldlink currencies on CITI tree (REGUH.WAERS exotic + house bank=CIT*)

All anchored on P01 production data.
"""
import sqlite3, json, sys
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
OUT_DIR = Path('knowledge/domains/Payment/phase0')


def model_8_bcm_lifecycle(cur):
    """BCM batch lifecycle from BNK_BATCH_HEADER + BNK_BATCH_ITEM."""
    out = {'name': 'Model 8 — BCM Batch Lifecycle'}

    cur.execute('PRAGMA table_info(BNK_BATCH_HEADER)')
    bbh_cols = [r[1] for r in cur.fetchall()]
    cur.execute('PRAGMA table_info(BNK_BATCH_ITEM)')
    bbi_cols = [r[1] for r in cur.fetchall()]
    out['bbh_cols'] = bbh_cols
    out['bbi_cols'] = bbi_cols

    cur.execute('SELECT COUNT(*) FROM BNK_BATCH_HEADER')
    out['bbh_count'] = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM BNK_BATCH_ITEM')
    out['bbi_count'] = cur.fetchone()[0]

    # Status distribution if STATUS column exists
    if 'STATUS' in bbh_cols:
        cur.execute('SELECT STATUS, COUNT(*) FROM BNK_BATCH_HEADER GROUP BY STATUS ORDER BY 2 DESC')
        out['status_distribution'] = cur.fetchall()
    elif 'BATCH_STATUS' in bbh_cols:
        cur.execute('SELECT BATCH_STATUS, COUNT(*) FROM BNK_BATCH_HEADER GROUP BY BATCH_STATUS ORDER BY 2 DESC')
        out['status_distribution'] = cur.fetchall()

    # Per house bank
    if 'HBKID' in bbh_cols:
        cur.execute('SELECT HBKID, COUNT(*) FROM BNK_BATCH_HEADER GROUP BY HBKID ORDER BY 2 DESC LIMIT 30')
        out['per_house_bank'] = cur.fetchall()

    # Sample row
    cur.execute('SELECT * FROM BNK_BATCH_HEADER LIMIT 1')
    sample = cur.fetchone()
    if sample:
        out['sample_row'] = dict(zip(bbh_cols, sample))

    return out


def model_9_house_bank_emission(cur):
    """REGUH_FULL.HBKID + T012 — emission distribution per house bank."""
    out = {'name': 'Model 9 — Per House Bank Emission'}
    # Use REGUH (8-col) since REGUH_FULL may not be ready yet — HBKID is in both
    cur.execute('SELECT HBKID, COUNT(*) FROM REGUH WHERE HBKID != "" GROUP BY HBKID ORDER BY 2 DESC LIMIT 30')
    hbk_dist = cur.fetchall()
    out['per_hbkid'] = hbk_dist

    # JOIN with T012 to get bank info
    cur.execute("""
        SELECT regu.HBKID, t012.BANKS, t012.BANKL, COUNT(*)
        FROM REGUH regu
        LEFT JOIN T012 t012 ON regu.HBKID = t012.HBKID AND regu.ZBUKR = t012.BUKRS
        WHERE regu.HBKID != ""
        GROUP BY regu.HBKID, t012.BANKS, t012.BANKL
        ORDER BY 4 DESC LIMIT 30
    """)
    out['hbkid_with_bank'] = cur.fetchall()

    # Per HBKID + ZBUKR (paying co)
    cur.execute("""
        SELECT regu.ZBUKR, regu.HBKID, COUNT(*)
        FROM REGUH regu WHERE regu.HBKID != ""
        GROUP BY regu.ZBUKR, regu.HBKID ORDER BY 3 DESC LIMIT 30
    """)
    out['per_co_hbkid'] = cur.fetchall()

    return out


def model_10_worldlink_currencies(cur):
    """REGUH_FULL.WAERS + HBKID — Worldlink CITI traffic (exotic currencies)."""
    out = {'name': 'Model 10 — Worldlink Currencies via CITI'}
    # Need REGUH_FULL for WAERS column
    try:
        cur.execute('SELECT WAERS, COUNT(*), SUM(CAST(RWBTR AS REAL)) FROM REGUH_FULL WHERE WAERS != "" GROUP BY WAERS ORDER BY 2 DESC LIMIT 30')
        out['currency_distribution'] = cur.fetchall()
    except sqlite3.OperationalError:
        out['error'] = 'REGUH_FULL not yet available (extraction in progress)'
        return out

    # Worldlink-specific (BRL, MGA, TND, ARS, ZAR, CDF, KES, NGN, MXN, INR, CNY)
    worldlink_cur = ('BRL','MGA','TND','ARS','ZAR','CDF','KES','NGN','MXN','INR','CNY','THB','MYR','IDR')
    placeholders = ','.join('?' * len(worldlink_cur))
    cur.execute(f"""
        SELECT WAERS, COUNT(*) FROM REGUH_FULL
        WHERE WAERS IN ({placeholders})
        GROUP BY WAERS ORDER BY 2 DESC
    """, worldlink_cur)
    out['worldlink_per_currency'] = cur.fetchall()

    # WAERS × HBKID for Worldlink
    cur.execute(f"""
        SELECT WAERS, HBKID, COUNT(*) FROM REGUH_FULL
        WHERE WAERS IN ({placeholders})
        GROUP BY WAERS, HBKID ORDER BY 3 DESC LIMIT 30
    """, worldlink_cur)
    out['worldlink_per_currency_hbkid'] = cur.fetchall()

    return out


def model_6_void_patterns(cur):
    """Void / reverse payment patterns (XVORL flag in REGUH 8-col version)."""
    out = {'name': 'Model 6 — Reverse/Void Payment Patterns'}
    cur.execute('PRAGMA table_info(REGUH)')
    cols = [r[1] for r in cur.fetchall()]
    out['available_cols'] = cols

    # XVORL column = test/proposal flag (X = test proposal)
    if 'XVORL' in cols:
        cur.execute('SELECT XVORL, COUNT(*) FROM REGUH GROUP BY XVORL')
        out['xvorl_distribution'] = cur.fetchall()

    # If REGUH_FULL has VOIDS/VOIDR/XAVIS/XEINZ
    try:
        cur.execute('PRAGMA table_info(REGUH_FULL)')
        full_cols = [r[1] for r in cur.fetchall()]
        if 'VOIDS' in full_cols or 'XAVIS' in full_cols:
            cur.execute('SELECT XAVIS, COUNT(*) FROM REGUH_FULL GROUP BY XAVIS')
            out['xavis_distribution_full'] = cur.fetchall()
    except sqlite3.OperationalError:
        out['note'] = 'REGUH_FULL not yet available — using REGUH 8-col only'

    return out


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    print('=== Process Mining Tier 1 Models ===\n')

    print('Model 8 — BCM Batch Lifecycle...')
    m8 = model_8_bcm_lifecycle(cur)

    print('Model 9 — Per House Bank Emission...')
    m9 = model_9_house_bank_emission(cur)

    print('Model 10 — Worldlink Currencies (needs REGUH_FULL)...')
    m10 = model_10_worldlink_currencies(cur)

    print('Model 6 — Reverse/Void Patterns...')
    m6 = model_6_void_patterns(cur)

    # Output
    md = ['# Process Mining Tier 1 Models — V001 scope insights\n',
          f'**Generated**: from P01 Gold DB\n\n']

    md.append('## Model 8 — BCM Batch Lifecycle (BNK_BATCH_HEADER + BNK_BATCH_ITEM)\n\n')
    md.append(f'**BBH rows**: {m8.get("bbh_count","?"):,}  |  **BBI rows**: {m8.get("bbi_count","?"):,}\n\n')
    md.append(f'**BBH columns**: {", ".join(m8.get("bbh_cols",[]))}\n\n')
    if 'status_distribution' in m8:
        md.append('### Status distribution\n\n| Status | Count |\n|---|---|\n')
        for s, c in m8['status_distribution']:
            md.append(f'| {s or "(empty)"} | {c:,} |\n')
    if 'per_house_bank' in m8:
        md.append('\n### Top 15 house banks by batch count\n\n| HBKID | Batches |\n|---|---|\n')
        for h, c in m8['per_house_bank'][:15]:
            md.append(f'| {h or "(empty)"} | {c:,} |\n')

    md.append('\n## Model 9 — Per House Bank Emission Distribution\n\n')
    md.append('### Top 30 HBKID by F110 payment runs\n\n| HBKID | Payments |\n|---|---|\n')
    for h, c in m9.get('per_hbkid', [])[:30]:
        md.append(f'| {h or "(empty)"} | {c:,} |\n')

    md.append('\n### HBKID × Bank country (T012 join)\n\n')
    md.append('| HBKID | Bank country | Bank key | Payments |\n|---|---|---|---|\n')
    for h, bc, bk, c in m9.get('hbkid_with_bank', [])[:30]:
        md.append(f'| {h or "(empty)"} | {bc or "?"} | {bk or "?"} | {c:,} |\n')

    md.append('\n### Top (Co code, HBKID) combinations\n\n')
    md.append('| Co | HBKID | Payments |\n|---|---|---|\n')
    for co, h, c in m9.get('per_co_hbkid', [])[:30]:
        md.append(f'| {co} | {h or "(empty)"} | {c:,} |\n')

    md.append('\n## Model 10 — Worldlink Currencies via CITI\n\n')
    if 'error' in m10:
        md.append(f'⏳ {m10["error"]}\n')
    else:
        md.append('### Total currency distribution (top 20)\n\n')
        md.append('| Currency | Payments | Total amount |\n|---|---|---|\n')
        for cur_, c, amt in m10.get('currency_distribution', [])[:20]:
            md.append(f'| {cur_} | {c:,} | {amt:,.0f} |\n')

        md.append('\n### Worldlink-pattern currencies (BRL/MGA/TND/...)\n\n')
        md.append('| Currency | Payments |\n|---|---|\n')
        for cur_, c in m10.get('worldlink_per_currency', []):
            md.append(f'| {cur_} | {c:,} |\n')

        md.append('\n### Worldlink Currency × HBKID\n\n')
        md.append('| Currency | HBKID | Payments |\n|---|---|---|\n')
        for cur_, h, c in m10.get('worldlink_per_currency_hbkid', [])[:30]:
            md.append(f'| {cur_} | {h or "(empty)"} | {c:,} |\n')

    md.append('\n## Model 6 — Reverse/Void Payment Patterns\n\n')
    md.append(f'**REGUH columns available**: {", ".join(m6.get("available_cols",[]))}\n\n')
    if 'xvorl_distribution' in m6:
        md.append('### XVORL flag (X=test proposal, ""=real run)\n\n')
        md.append('| XVORL | Count |\n|---|---|\n')
        for x, c in m6['xvorl_distribution']:
            md.append(f'| {x or "(real run)"} | {c:,} |\n')

    md.append('\n## Conclusions\n\n')
    md.append('- BCM lifecycle stats above identify chokepoints in V000 today; '
              'V001 cutover should not increase rejection rates beyond baseline\n')
    md.append('- HBKID distribution informs test matrix house-bank coverage requirements\n')
    md.append('- Worldlink currency mix validates UltmtCdtr Q3 deferral or escalation\n')
    md.append('- Void/reverse patterns identify what TYPE of failures we should test\n')

    out_md = OUT_DIR / 'process_mining_tier1_models.md'
    out_md.write_text(''.join(md), encoding='utf-8')
    out_json = OUT_DIR / 'process_mining_tier1_models.json'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({'m6': m6, 'm8': m8, 'm9': m9, 'm10': m10}, f,
                  indent=2, ensure_ascii=False, default=str)

    print(f'\nReport: {out_md}')
    con.close()


if __name__ == '__main__':
    main()
