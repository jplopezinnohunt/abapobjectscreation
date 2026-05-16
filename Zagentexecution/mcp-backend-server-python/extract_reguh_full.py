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
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
# Force line-buffered stdout for background-task visibility
try:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1, encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa

DB = Path(__file__).resolve().parents[2] / 'Zagentexecution' / 'sap_data_extraction' / 'sqlite' / 'p01_gold_master_data.db'
print(f'DB path: {DB}  exists={DB.exists()}', flush=True)

CRITICAL_COLS = [
    'LAUFD', 'LAUFI', 'ZBUKR', 'LIFNR', 'VBLNR',
    'RZAWE', 'HBKID', 'HKTID', 'UBHKT', 'BVTYP',
    'UBNKS', 'UBNKL', 'UBKNT',
    'WAERS', 'RWBTR', 'ZALDT', 'XAVIS',
    'EMPFG', 'ANRED', 'NAME1', 'NAME2',
    'STRAS', 'PSTLZ', 'ORT01', 'LAND1', 'REGIO',
    'PERNR'
]


def _prepare_target_table(sqlcon):
    """Backup the existing narrow REGUH and recreate with full schema. Idempotent."""
    cur = sqlcon.cursor()
    # Backup only if not already backed up
    exists = cur.execute("SELECT 1 FROM sqlite_master WHERE name='REGUH_8COL_BACKUP'").fetchone()
    if not exists:
        print('Backing up existing narrow REGUH → REGUH_8COL_BACKUP', flush=True)
        cur.execute('CREATE TABLE REGUH_8COL_BACKUP AS SELECT * FROM REGUH')
    # Re-create REGUH with full schema (only if it doesn't already have CRITICAL_COLS)
    cur.execute('PRAGMA table_info(REGUH)')
    existing_cols = [r[1] for r in cur.fetchall()]
    if set(existing_cols) != set(CRITICAL_COLS):
        cur.execute('DROP TABLE IF EXISTS REGUH')
        cols_def = ', '.join(f'"{c}" TEXT' for c in CRITICAL_COLS)
        cur.execute(f'CREATE TABLE REGUH ({cols_def})')
        print(f'Recreated REGUH with {len(CRITICAL_COLS)} cols', flush=True)
    sqlcon.commit()


def _flush_chunk(sqlcon, chunk):
    placeholders = ', '.join('?' * len(CRITICAL_COLS))
    batch = [[r.get(c, '') for c in CRITICAL_COLS] for r in chunk]
    sqlcon.executemany(f'INSERT INTO REGUH VALUES ({placeholders})', batch)
    sqlcon.commit()


def main():
    print(f'=== Extract REGUH with {len(CRITICAL_COLS)} critical cols (chunked + incremental write) ===', flush=True)
    t0 = time.time()

    # Open Gold DB once, validate path BEFORE doing any SAP work
    if not DB.exists():
        raise SystemExit(f'Gold DB not found at {DB}')
    sqlcon = sqlite3.connect(DB)
    _prepare_target_table(sqlcon)

    conn = get_connection('P01')
    total = 0
    # Smaller year chunks for the older window (pre-2017 dumps if too wide)
    year_ranges = [
        ("20260101", "20261231"),
        ("20250101", "20251231"),
        ("20240101", "20241231"),
        ("20230101", "20231231"),
        ("20220101", "20221231"),
        ("20210101", "20211231"),
        ("20200101", "20201231"),
        ("20190101", "20191231"),
        ("20180101", "20181231"),
        ("20170101", "20171231"),
        ("20160101", "20161231"),
        ("20150101", "20151231"),
        ("20140101", "20141231"),
        ("20130101", "20131231"),
        ("20120101", "20121231"),
        ("20110101", "20111231"),
        ("20100101", "20101231"),
        ("19000101", "20091231"),
    ]
    for date_from, date_to in year_ranges:
        chunk_t0 = time.time()
        print(f'\n--- chunk {date_from} .. {date_to} ---', flush=True)
        try:
            chunk = rfc_read_paginated(
                conn, 'REGUH', CRITICAL_COLS,
                where=f"LAUFD >= '{date_from}' AND LAUFD <= '{date_to}'",
                batch_size=5000, throttle=1.0)
            elapsed = time.time() - chunk_t0
            # IMMEDIATELY write to Gold DB so we don't lose anything
            _flush_chunk(sqlcon, chunk)
            total += len(chunk)
            print(f'   chunk rows: {len(chunk):,}  cumulative: {total:,}  time: {elapsed:.0f}s  → written', flush=True)
        except Exception as e:
            print(f'   chunk err: {e}', flush=True)
    print(f'\nExtracted {total:,} rows total in {time.time()-t0:.0f}s', flush=True)

    conn.close()

    # Indexes + verify (data already written incrementally per chunk)
    print('\nCreating indexes...', flush=True)
    cur = sqlcon.cursor()
    for s in [
        'CREATE INDEX IF NOT EXISTS idx_reguh_lifnr ON REGUH(LIFNR)',
        'CREATE INDEX IF NOT EXISTS idx_reguh_zbukr_lifnr ON REGUH(ZBUKR, LIFNR)',
        'CREATE INDEX IF NOT EXISTS idx_reguh_run ON REGUH(LAUFD, LAUFI, ZBUKR)',
        'CREATE INDEX IF NOT EXISTS idx_reguh_empfg ON REGUH(EMPFG)',
        'CREATE INDEX IF NOT EXISTS idx_reguh_rzawe ON REGUH(ZBUKR, RZAWE)',
        'CREATE INDEX IF NOT EXISTS idx_reguh_zaldt ON REGUH(ZALDT)',
        'CREATE INDEX IF NOT EXISTS idx_reguh_ubnks ON REGUH(UBNKS)',
    ]:
        cur.execute(s)
    sqlcon.commit()

    cur.execute('SELECT COUNT(*) FROM REGUH')
    print(f'REGUH row count: {cur.fetchone()[0]:,}', flush=True)
    cur.execute("SELECT COUNT(*) FROM REGUH WHERE EMPFG != '' AND EMPFG IS NOT NULL")
    print(f'EMPFG populated rows: {cur.fetchone()[0]:,}', flush=True)
    cur.execute('SELECT COUNT(DISTINCT RZAWE) FROM REGUH')
    print(f'Distinct RZAWE values: {cur.fetchone()[0]}', flush=True)
    cur.execute("SELECT COUNT(DISTINCT UBNKS) FROM REGUH WHERE UBNKS != ''")
    print(f'Distinct UBNKS values: {cur.fetchone()[0]}', flush=True)

    sqlcon.close()
    print(f'\nDONE in {time.time()-t0:.0f}s total', flush=True)


if __name__ == '__main__':
    main()
