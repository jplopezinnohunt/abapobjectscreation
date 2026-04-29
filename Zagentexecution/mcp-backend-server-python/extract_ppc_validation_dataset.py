"""
Extract focused dataset for PPC validation:
- Vendors with bank in PPC-9-countries (LFBK.BANKS in AE/BH/CN/ID/IN/JO/MA/MY/PH)
- Their REGUH payments 2025+ (with DORIGIN)
- Matching REGUP rows (with LZBKZ)
"""
import sys, sqlite3, time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
PPC_COUNTRIES = ('AE', 'BH', 'CN', 'ID', 'IN', 'JO', 'MA', 'MY', 'PH')


def main():
    print('=== Extract PPC validation dataset ===')
    t0 = time.time()
    sqlcon = sqlite3.connect(DB)
    cur = sqlcon.cursor()

    print('1. Identifying PPC vendors...')
    placeholders = ','.join('?' * len(PPC_COUNTRIES))
    cur.execute(
        f'SELECT DISTINCT LIFNR FROM LFBK WHERE BANKS IN ({placeholders})',
        PPC_COUNTRIES,
    )
    ppc_lifnrs = [r[0] for r in cur.fetchall()]
    print(f'   {len(ppc_lifnrs):,} distinct vendors')

    conn = get_connection('P01')
    chunk_size = 50

    print('2. Extracting REGUH for PPC vendors with DORIGIN...')
    reguh_cols = ['LAUFD', 'LAUFI', 'ZBUKR', 'LIFNR', 'VBLNR', 'RZAWE',
                  'HBKID', 'HKTID', 'UBNKS', 'UBNKL', 'WAERS', 'RWBTR',
                  'ZALDT', 'DORIGIN', 'EMPFG', 'NAME1', 'LAND1']
    all_reguh = []
    for i in range(0, len(ppc_lifnrs), chunk_size):
        chunk = ppc_lifnrs[i:i + chunk_size]
        in_clause = ','.join("'" + l + "'" for l in chunk)
        where = f"LIFNR IN ({in_clause}) AND LAUFD >= '20250101'"
        rows = rfc_read_paginated(conn, 'REGUH', reguh_cols, where=where,
                                   batch_size=2000, throttle=0.3)
        all_reguh.extend(rows)
        if i % 200 == 0:
            print(f'   chunk {i}/{len(ppc_lifnrs)}: total {len(all_reguh):,}')
    print(f'   REGUH rows: {len(all_reguh):,} in {time.time()-t0:.0f}s')

    print('3. Extracting REGUP with LZBKZ...')
    regup_cols = ['LAUFD', 'LAUFI', 'ZBUKR', 'LIFNR', 'BELNR', 'GJAHR',
                  'BUZEI', 'LZBKZ', 'XBLNR', 'BLDAT', 'SGTXT', 'WRBTR',
                  'WAERS']
    all_regup = []
    for i in range(0, len(ppc_lifnrs), chunk_size):
        chunk = ppc_lifnrs[i:i + chunk_size]
        in_clause = ','.join("'" + l + "'" for l in chunk)
        where = f"LIFNR IN ({in_clause}) AND LAUFD >= '20250101'"
        rows = rfc_read_paginated(conn, 'REGUP', regup_cols, where=where,
                                   batch_size=2000, throttle=0.3)
        all_regup.extend(rows)
        if i % 200 == 0:
            print(f'   chunk {i}/{len(ppc_lifnrs)}: total {len(all_regup):,}')
    print(f'   REGUP rows: {len(all_regup):,} in {time.time()-t0:.0f}s')
    conn.close()

    cur.execute('DROP TABLE IF EXISTS REGUH_PPC')
    cur.execute('CREATE TABLE REGUH_PPC (' +
                ', '.join('"' + c + '" TEXT' for c in reguh_cols) + ')')
    p1 = ', '.join('?' * len(reguh_cols))
    cur.executemany(f'INSERT INTO REGUH_PPC VALUES ({p1})',
                     [[r.get(c, '') for c in reguh_cols] for r in all_reguh])

    cur.execute('DROP TABLE IF EXISTS REGUP_PPC')
    cur.execute('CREATE TABLE REGUP_PPC (' +
                ', '.join('"' + c + '" TEXT' for c in regup_cols) + ')')
    p2 = ', '.join('?' * len(regup_cols))
    cur.executemany(f'INSERT INTO REGUP_PPC VALUES ({p2})',
                     [[r.get(c, '') for c in regup_cols] for r in all_regup])
    sqlcon.commit()
    cur.execute('SELECT COUNT(*) FROM REGUH_PPC')
    print(f'REGUH_PPC: {cur.fetchone()[0]} rows')
    cur.execute('SELECT COUNT(*) FROM REGUP_PPC')
    print(f'REGUP_PPC: {cur.fetchone()[0]} rows')
    sqlcon.close()
    print(f'\nDONE in {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
