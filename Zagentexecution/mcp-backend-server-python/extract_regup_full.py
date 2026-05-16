"""Extract REGUP (payment line items) from P01 to Gold DB."""
import sys, sqlite3, time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')

CRITICAL_COLS = [
    'LAUFD', 'LAUFI', 'ZBUKR', 'LIFNR',
    'BUKRS', 'BELNR', 'GJAHR', 'BUZEI',
    'BLART', 'BLDAT', 'BUDAT',
    'WRBTR', 'WAERS', 'HKONT', 'KOART', 'BSCHL', 'SHKZG',
    'XBLNR', 'VBLNR', 'UMSKZ', 'ZUONR', 'SGTXT',
    'ZTERM', 'ZBD1T', 'ZBD2T', 'ZBD3T',
    'MWSKZ', 'MANSP', 'REBZG',
    'EMPFG',  # ← alt-payee at item level (the field that was missing)
]


def main():
    print('=== Extract REGUP (payment line items) with EMPFG, LAUFD >= 20240101 ===')
    t0 = time.time()
    conn = get_connection('P01')
    rows = rfc_read_paginated(conn, 'REGUP', CRITICAL_COLS,
                              where="LAUFD >= '20240101'",
                              batch_size=5000, throttle=1.0)
    print(f'Extracted {len(rows):,} rows in {time.time()-t0:.0f}s')
    conn.close()

    sqlcon = sqlite3.connect(DB)
    cur = sqlcon.cursor()
    cur.execute('DROP TABLE IF EXISTS REGUP')
    cols_def = ', '.join(f'"{c}" TEXT' for c in CRITICAL_COLS)
    cur.execute(f'CREATE TABLE REGUP ({cols_def})')
    placeholders = ', '.join('?' * len(CRITICAL_COLS))
    batch = [[r.get(c, '') for c in CRITICAL_COLS] for r in rows]
    print(f'Writing {len(batch):,} rows to Gold DB...')
    for i in range(0, len(batch), 5000):
        cur.executemany(f'INSERT INTO REGUP VALUES ({placeholders})', batch[i:i+5000])
    sqlcon.commit()
    for s in [
        'CREATE INDEX idx_regup_lifnr ON REGUP(LIFNR)',
        'CREATE INDEX idx_regup_doc ON REGUP(BUKRS, BELNR, GJAHR, BUZEI)',
        'CREATE INDEX idx_regup_run ON REGUP(LAUFD, LAUFI, ZBUKR)',
        'CREATE INDEX idx_regup_empfg ON REGUP(EMPFG)',
    ]:
        cur.execute(s)
    sqlcon.commit()
    cur.execute('SELECT COUNT(*) FROM REGUP')
    print(f'REGUP final count: {cur.fetchone()[0]:,}')
    cur.execute("SELECT COUNT(*) FROM REGUP WHERE EMPFG != '' AND EMPFG IS NOT NULL")
    print(f'REGUP rows with EMPFG populated: {cur.fetchone()[0]:,}')
    sqlcon.close()
    print(f'DONE in {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
