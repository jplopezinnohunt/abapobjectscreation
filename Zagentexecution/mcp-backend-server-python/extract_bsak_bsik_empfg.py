"""Re-extract BSAK + BSIK from P01 with EMPFG/EMPFB added.

The existing bsak/bsik tables in Gold DB have 30 cols but lack EMPFG (alt-payee
LIFNR override on the document item). Without that field, alt-payee-fire analysis
is impossible against AR/AP cleared/open items.

This script extracts the same fields as extract_bkpf_bseg_parallel.py PLUS EMPFG
and EMPFB, filters to BUDAT >= 20240101, and replaces the existing bsak/bsik
tables in Gold DB (backing up the originals as bsak_pre_empfg / bsik_pre_empfg).
"""
import sys, sqlite3, time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')

# Mirror the BSEG_REPLACEMENT_FIELDS list from extract_bkpf_bseg_parallel.py
# PLUS EMPFG + EMPFB for alt-payee forensics.
COLS = [
    'MANDT', 'BUKRS', 'BELNR', 'GJAHR', 'BUZEI',
    'BUDAT', 'BLDAT', 'CPUDT', 'MONAT',
    'SHKZG', 'WRBTR', 'WAERS', 'DMBTR', 'DMBE2',
    'HKONT', 'BSCHL', 'GSBER', 'KOSTL',
    'AUFNR', 'PRCTR', 'FKBER',
    'EBELN', 'EBELP', 'MWSKZ',
    'AUGDT', 'AUGBL',
    'LIFNR', 'SGTXT', 'ZFBDT', 'ZTERM',
    # ★ alt-payee fields (the gap)
    'EMPFG', 'EMPFB',
]

TABLES = [
    ('BSAK', 'bsak', 'Vendor cleared items (paid)'),
    ('BSIK', 'bsik', 'Vendor open items'),
]


def extract_one(conn, sap_table, gold_table, desc):
    print(f'\n=== Extract {sap_table} ({desc}) — BUDAT >= 20240101 ===')
    t0 = time.time()
    rows = rfc_read_paginated(conn, sap_table, COLS,
                              where="BUDAT >= '20240101'",
                              batch_size=5000, throttle=1.0)
    print(f'  Extracted {len(rows):,} rows in {time.time()-t0:.0f}s')

    sqlcon = sqlite3.connect(DB)
    cur = sqlcon.cursor()

    # Backup existing table
    cur.execute(f'DROP TABLE IF EXISTS {gold_table}_pre_empfg')
    try:
        cur.execute(f'CREATE TABLE {gold_table}_pre_empfg AS SELECT * FROM {gold_table}')
        print(f'  Backed up existing {gold_table} → {gold_table}_pre_empfg')
    except Exception as e:
        print(f'  (no existing {gold_table} to back up: {e})')
    sqlcon.commit()

    # Drop + recreate with new schema
    cur.execute(f'DROP TABLE IF EXISTS {gold_table}')
    cols_def = ', '.join(f'"{c}" TEXT' for c in COLS)
    cur.execute(f'CREATE TABLE {gold_table} ({cols_def})')
    sqlcon.commit()

    placeholders = ', '.join('?' * len(COLS))
    batch = []
    for r in rows:
        batch.append([r.get(c, '') for c in COLS])
        if len(batch) >= 5000:
            cur.executemany(f'INSERT INTO {gold_table} VALUES ({placeholders})', batch)
            batch = []
    if batch:
        cur.executemany(f'INSERT INTO {gold_table} VALUES ({placeholders})', batch)
    sqlcon.commit()

    # Indexes
    for s in [
        f'CREATE INDEX idx_{gold_table}_lifnr ON {gold_table}(LIFNR)',
        f'CREATE INDEX idx_{gold_table}_doc ON {gold_table}(BUKRS, BELNR, GJAHR, BUZEI)',
        f'CREATE INDEX idx_{gold_table}_empfg ON {gold_table}(EMPFG)',
        f'CREATE INDEX idx_{gold_table}_budat ON {gold_table}(BUDAT)',
    ]:
        try:
            cur.execute(s)
        except Exception as e:
            print(f'    index err: {e}')
    sqlcon.commit()

    cur.execute(f'SELECT COUNT(*) FROM {gold_table}')
    print(f'  {gold_table} row count: {cur.fetchone()[0]:,}')
    cur.execute(f"SELECT COUNT(*) FROM {gold_table} WHERE EMPFG != '' AND EMPFG IS NOT NULL")
    print(f'  EMPFG populated rows: {cur.fetchone()[0]:,}')
    cur.execute(f"SELECT COUNT(*) FROM {gold_table} WHERE EMPFB != '' AND EMPFB IS NOT NULL")
    print(f'  EMPFB populated rows: {cur.fetchone()[0]:,}')
    sqlcon.close()


def main():
    t0 = time.time()
    conn = get_connection('P01')
    for sap_t, gold_t, desc in TABLES:
        extract_one(conn, sap_t, gold_t, desc)
    conn.close()
    print(f'\n=== DONE in {time.time()-t0:.0f}s total ===')


if __name__ == '__main__':
    main()
