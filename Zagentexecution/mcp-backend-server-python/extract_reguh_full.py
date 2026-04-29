"""
Extract REGUH with all critical columns from P01 (split-field mode for wide table).

Replaces our current 8-column REGUH with a 27-column version that includes:
- RZAWE (ACTUAL payment method per payment — KEY for tree routing)
- WAERS, RWBTR, ZALDT (currency, amount, date)
- UBNKS, UBNKL (vendor bank country + bank key actually used at payment time)
- LAND1, ORT01, PSTLZ, REGIO (address snapshot at payment time)
- HBKID, HKTID (house bank + account)
- VBLNR (payment doc number)
- ANRED + NAME1+NAME2 (recipient name snapshot)
- BVTYP (vendor bank type used)
- VOIDS, XAVIS, XEINZ (status flags)

Writes to Gold DB (replaces existing REGUH table).
"""
import sys, os, sqlite3, time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')

CRITICAL_COLS = [
    'LAUFD', 'LAUFI', 'ZBUKR', 'LIFNR', 'VBLNR',
    'RZAWE', 'HBKID', 'HKTID', 'UBHKT', 'BVTYP',
    'UBNKS', 'UBNKL', 'UBKNT',
    'WAERS', 'RWBTR', 'ZALDT', 'XAVIS',
    'EMPFG', 'ANRED', 'NAME1', 'NAME2',
    'STRAS', 'PSTLZ', 'ORT01', 'LAND1', 'REGIO',
    'PERNR'
]


def main():
    print(f'=== Extract REGUH with {len(CRITICAL_COLS)} critical cols ===')
    t0 = time.time()
    conn = get_connection('P01')

    rows = rfc_read_paginated(
        conn, 'REGUH', CRITICAL_COLS, where='', batch_size=5000, throttle=1.0)
    print(f'\nExtracted {len(rows):,} rows in {time.time()-t0:.0f}s')

    conn.close()

    # Write to Gold DB — replace existing REGUH table
    sqlcon = sqlite3.connect(DB)
    cur = sqlcon.cursor()
    cur.execute('DROP TABLE IF EXISTS REGUH_FULL')
    cols_def = ', '.join(f'"{c}" TEXT' for c in CRITICAL_COLS)
    cur.execute(f'CREATE TABLE REGUH_FULL ({cols_def})')
    sqlcon.commit()

    placeholders = ', '.join('?' * len(CRITICAL_COLS))
    print(f'Writing to Gold DB...')
    batch = []
    for r in rows:
        batch.append([r.get(c, '') for c in CRITICAL_COLS])
        if len(batch) >= 5000:
            cur.executemany(f'INSERT INTO REGUH_FULL VALUES ({placeholders})', batch)
            batch = []
    if batch:
        cur.executemany(f'INSERT INTO REGUH_FULL VALUES ({placeholders})', batch)
    sqlcon.commit()

    # Add indexes
    print('Creating indexes...')
    for s in [
        'CREATE INDEX idx_rfull_lifnr ON REGUH_FULL(LIFNR)',
        'CREATE INDEX idx_rfull_zbukr_rzawe ON REGUH_FULL(ZBUKR, RZAWE)',
        'CREATE INDEX idx_rfull_zaldt ON REGUH_FULL(ZALDT)',
        'CREATE INDEX idx_rfull_ubnks ON REGUH_FULL(UBNKS)',
    ]:
        cur.execute(s)
    sqlcon.commit()

    # Verify
    cur.execute('SELECT COUNT(*) FROM REGUH_FULL')
    print(f'REGUH_FULL row count: {cur.fetchone()[0]:,}')
    cur.execute('SELECT COUNT(DISTINCT RZAWE) FROM REGUH_FULL')
    print(f'Distinct RZAWE values: {cur.fetchone()[0]}')
    cur.execute('SELECT COUNT(DISTINCT UBNKS) FROM REGUH_FULL WHERE UBNKS != ""')
    print(f'Distinct UBNKS values: {cur.fetchone()[0]}')

    sqlcon.close()
    print(f'\nDONE in {time.time()-t0:.0f}s total')


if __name__ == '__main__':
    main()
