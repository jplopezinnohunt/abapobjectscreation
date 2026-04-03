"""
extract_master_data_3cc.py
Extract master data counts for ICTP, MGIE, ICBA from P01
"""
import sys, io, json
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, __import__('os').path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

conn = get_connection('P01')
results = {}

for bukrs in ['ICTP', 'MGIE', 'ICBA']:
    print(f'\n{"="*60}')
    print(f'{bukrs}')
    print(f'{"="*60}')
    data = {}

    # 1. GL Accounts (SKB1)
    print(f'  [SKB1] GL Accounts...')
    try:
        rows = rfc_read_paginated(conn, 'SKB1', ['BUKRS','SAKNR'], f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        data['gl_accounts'] = len(rows)
        print(f'    {len(rows)}')
    except Exception as e:
        print(f'    Error: {e}')
        data['gl_accounts'] = 'ERROR'

    # 2. Cost Centers (CSKS)
    print(f'  [CSKS] Cost Centers...')
    try:
        rows = rfc_read_paginated(conn, 'CSKS', ['KOKRS','KOSTL','DATAB','DATBI','BUKRS'], f"KOKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        if not rows:
            rows = rfc_read_paginated(conn, 'CSKS', ['KOKRS','KOSTL','DATAB','DATBI','BUKRS'], f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        data['cost_centers'] = len(rows)
        print(f'    {len(rows)}')
        if rows:
            dates = sorted(r.get('DATAB','') for r in rows if r.get('DATAB',''))
            if dates: print(f'    First: {dates[0]}')
    except Exception as e:
        print(f'    Error: {e}')
        data['cost_centers'] = 'ERROR'

    # 3. Cost Elements (CSKA)
    print(f'  [CSKA] Cost Elements...')
    try:
        rows = rfc_read_paginated(conn, 'CSKA', ['KSTAR','KOKRS','DATAB','DATBI','KATYP'], f"KOKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        data['cost_elements'] = len(rows)
        print(f'    {len(rows)}')
        if rows:
            types = Counter(r.get('KATYP','') for r in rows)
            for t, c in types.most_common():
                print(f'      Type {t}: {c}')
    except Exception as e:
        print(f'    Error: {e}')
        data['cost_elements'] = 'ERROR'

    # 4. Internal Orders (AUFK)
    print(f'  [AUFK] Internal Orders...')
    try:
        rows = rfc_read_paginated(conn, 'AUFK', ['AUFNR','AUART','BUKRS','ERDAT'], f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        data['internal_orders'] = len(rows)
        print(f'    {len(rows)}')
        if rows:
            types = Counter(r.get('AUART','') for r in rows)
            for t, c in types.most_common(5):
                print(f'      Type {t}: {c}')
            dates = sorted(r.get('ERDAT','') for r in rows if r.get('ERDAT',''))
            if dates: print(f'      First: {dates[0]}, Last: {dates[-1]}')
    except Exception as e:
        print(f'    Error: {e}')
        data['internal_orders'] = 'ERROR'

    # 5. Fixed Assets (ANLA)
    print(f'  [ANLA] Fixed Assets...')
    try:
        rows = rfc_read_paginated(conn, 'ANLA', ['BUKRS','ANLN1','ANLKL','ERDAT','AKTIV','DEAKT'], f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        data['fixed_assets'] = len(rows)
        active = sum(1 for r in rows if not r.get('DEAKT','').strip())
        data['assets_active'] = active
        print(f'    {len(rows)} total, {active} active')
        if rows:
            classes = Counter(r.get('ANLKL','') for r in rows)
            for t, c in classes.most_common(5):
                print(f'      Class {t}: {c}')
    except Exception as e:
        print(f'    Error: {e}')
        data['fixed_assets'] = 'ERROR'

    # 6. Customers (KNB1)
    print(f'  [KNB1] Customers...')
    try:
        rows = rfc_read_paginated(conn, 'KNB1', ['KUNNR','BUKRS','AKONT','ERDAT'], f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        data['customers'] = len(rows)
        print(f'    {len(rows)}')
    except Exception as e:
        print(f'    Error: {e}')
        data['customers'] = 'ERROR'

    # 7. Vendors (LFB1)
    print(f'  [LFB1] Vendors...')
    try:
        rows = rfc_read_paginated(conn, 'LFB1', ['LIFNR','BUKRS','AKONT','ERDAT'], f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        data['vendors'] = len(rows)
        print(f'    {len(rows)}')
    except Exception as e:
        print(f'    Error: {e}')
        data['vendors'] = 'ERROR'

    # 8. Funds (FMFINT)
    print(f'  [FMFINT] Funds...')
    try:
        rows = rfc_read_paginated(conn, 'FMFINT', ['FINCODE','FIKRS','DATAB','DATBI'], f"FIKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        data['funds'] = len(rows)
        print(f'    {len(rows)}')
    except Exception as e:
        print(f'    FMFINT error: {e}, trying FMFINCODE...')
        try:
            rows = rfc_read_paginated(conn, 'FMFINCODE', ['FINCODE','FIKRS','DATAB','DATBI'], f"FIKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
            data['funds'] = len(rows)
            print(f'    FMFINCODE: {len(rows)}')
        except Exception as e2:
            print(f'    Error: {e2}')
            data['funds'] = 'ERROR'

    # 9. Fund Centers (FMFCTR)
    print(f'  [FMFCTR] Fund Centers...')
    try:
        rows = rfc_read_paginated(conn, 'FMFCTR', ['FICTR','FIKRS','DATAB','DATBI'], f"FIKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        data['fund_centers'] = len(rows)
        print(f'    {len(rows)}')
    except Exception as e:
        print(f'    Error: {e}')
        data['fund_centers'] = 'ERROR'

    # 10. Commitment Items (FMCI)
    print(f'  [FMCI] Commitment Items...')
    try:
        rows = rfc_read_paginated(conn, 'FMCI', ['FIPEX','FIKRS','DATAB','DATBI'], f"FIKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        data['commitment_items'] = len(rows)
        print(f'    {len(rows)}')
    except Exception as e:
        print(f'    Error: {e}')
        data['commitment_items'] = 'ERROR'

    # 11. Profit Centers (CEPC)
    print(f'  [CEPC] Profit Centers...')
    try:
        rows = rfc_read_paginated(conn, 'CEPC', ['PRCTR','KOKRS','DATAB','DATBI'], f"KOKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        data['profit_centers'] = len(rows)
        print(f'    {len(rows)}')
    except Exception as e:
        print(f'    Error: {e}')
        data['profit_centers'] = 'ERROR'

    results[bukrs] = data

conn.close()

# Summary table
print(f'\n{"="*80}')
print(f'COMPARATIVE SUMMARY')
print(f'{"="*80}')
print(f'{"Aspect":30s} | {"ICTP":>8s} | {"MGIE":>8s} | {"ICBA":>8s} | {"STEM":>8s}')
print(f'{"-"*30}-+-{"-"*8}-+-{"-"*8}-+-{"-"*8}-+-{"-"*8}')

fields = [
    ('GL Accounts (SKB1)', 'gl_accounts'),
    ('Cost Centers (CSKS)', 'cost_centers'),
    ('Cost Elements (CSKA)', 'cost_elements'),
    ('Internal Orders (AUFK)', 'internal_orders'),
    ('Fixed Assets (ANLA)', 'fixed_assets'),
    ('Assets Active', 'assets_active'),
    ('Customers (KNB1)', 'customers'),
    ('Vendors (LFB1)', 'vendors'),
    ('Funds (FMFINT)', 'funds'),
    ('Fund Centers (FMFCTR)', 'fund_centers'),
    ('Commitment Items (FMCI)', 'commitment_items'),
    ('Profit Centers (CEPC)', 'profit_centers'),
]

for label, key in fields:
    ictp = results.get('ICTP', {}).get(key, '?')
    mgie = results.get('MGIE', {}).get(key, '?')
    icba = results.get('ICBA', {}).get(key, '?')
    print(f'{label:30s} | {str(ictp):>8s} | {str(mgie):>8s} | {str(icba):>8s} | {"0":>8s}')

# Save
with open('blueprint_output/master_data_comparison.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f'\nSaved to blueprint_output/master_data_comparison.json')
