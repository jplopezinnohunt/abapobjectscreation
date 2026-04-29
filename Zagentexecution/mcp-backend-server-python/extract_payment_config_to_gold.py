"""
Extract payment config tables fully into Gold DB.

Currently incomplete:
- TFPM042FB: NOT in Gold DB (OBPM4 Event 05 registrations) — extract full
- T042Z: only 6 cols in Gold DB but actual table has 31 cols — replace with full

Plus other related config tables for full coverage:
- T042: Country/payment config
- T042B: PMW format header
- T042D: Paying co code config
- T042E: Country-currency → format
- T042I: IBAN config
- T012, T012K, T012T (already 8/9 cols — extend if needed)
"""
import sys, sqlite3, time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')

TABLES = [
    'TFPM042FB',
    'T042Z',
    'T042',
    'T042B',
    'T042D',
    'T042E',
    'T042I',
    'T012T',  # bank texts
]


def get_full_schema(conn, tab):
    r = conn.call('DDIF_FIELDINFO_GET', TABNAME=tab)
    return [f['FIELDNAME'] for f in r.get('DFIES_TAB', [])]


def main():
    print('=== Extract payment config to Gold DB ===')
    t0 = time.time()
    conn = get_connection('P01')
    sqlcon = sqlite3.connect(DB)
    cur = sqlcon.cursor()

    for tab in TABLES:
        try:
            cols = get_full_schema(conn, tab)
            print(f'\n  {tab}: {len(cols)} fields')
            rows = rfc_read_paginated(conn, tab, cols, where='', batch_size=5000, throttle=0.5)
            print(f'    {len(rows):,} rows')
            cur.execute(f'DROP TABLE IF EXISTS "{tab}"')
            col_def = ', '.join(f'"{c}" TEXT' for c in cols)
            cur.execute(f'CREATE TABLE "{tab}" ({col_def})')
            placeholders = ', '.join('?' * len(cols))
            batch = [[r.get(c, '') for c in cols] for r in rows]
            for i in range(0, len(batch), 1000):
                cur.executemany(f'INSERT INTO "{tab}" VALUES ({placeholders})',
                                batch[i:i+1000])
            sqlcon.commit()
            print(f'    written to Gold DB')
        except Exception as e:
            print(f'    ERROR: {e}')

    sqlcon.close()
    conn.close()
    print(f'\nDONE in {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
