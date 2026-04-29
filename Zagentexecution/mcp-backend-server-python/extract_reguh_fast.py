"""
Fast alternative REGUH extraction — minimal columns, recent year filter, low throttle.

If full extraction stalls, this gives us 70% of analytical value in 4 minutes:
- 11 critical cols (LAUFD/LAUFI/ZBUKR/LIFNR/RZAWE/HBKID/HKTID/UBNKS/WAERS/RWBTR/ZALDT)
- WHERE LAUFD >= 2025-01-01 (covers 2025 + 2026 Q1 = ~535K rows = 57% of total)
- throttle 0.3s
- Single field-chunk (≤8 cols) per RFC call where possible
"""
import sys, sqlite3, time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa

DB = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')

# 8 cols → fits single RFC call (under MAX_FIELDS_PER_CALL)
COLS_PHASE1 = ['LAUFD', 'LAUFI', 'ZBUKR', 'LIFNR', 'RZAWE', 'HBKID', 'HKTID', 'UBNKS']
# 4 more cols → second RFC call same offset
COLS_PHASE2 = ['LAUFD', 'LAUFI', 'ZBUKR', 'LIFNR', 'WAERS', 'RWBTR', 'ZALDT']  # repeat key for join


def main():
    print('=== REGUH fast extraction (2025+2026, 11 cols) ===')
    t0 = time.time()
    conn = get_connection('P01')

    # WHERE LAUFD >= 2025-01-01
    where = "LAUFD >= '20250101'"

    print('Extracting Phase 1 (8 cols)...')
    rows1 = rfc_read_paginated(conn, 'REGUH', COLS_PHASE1, where=where,
                                batch_size=10000, throttle=0.3)
    print(f'  Got {len(rows1):,} rows in {time.time()-t0:.0f}s')

    print('Extracting Phase 2 (additional 3 cols)...')
    rows2 = rfc_read_paginated(conn, 'REGUH', COLS_PHASE2, where=where,
                                batch_size=10000, throttle=0.3)
    print(f'  Got {len(rows2):,} rows in {time.time()-t0:.0f}s')
    conn.close()

    # Merge by key (LAUFD+LAUFI+ZBUKR+LIFNR)
    print('Merging...')
    key_to_phase2 = {}
    for r in rows2:
        k = (r.get('LAUFD'), r.get('LAUFI'), r.get('ZBUKR'), r.get('LIFNR'))
        key_to_phase2[k] = r
    merged = []
    for r in rows1:
        k = (r.get('LAUFD'), r.get('LAUFI'), r.get('ZBUKR'), r.get('LIFNR'))
        p2 = key_to_phase2.get(k, {})
        merged.append({**r, 'WAERS': p2.get('WAERS', ''),
                       'RWBTR': p2.get('RWBTR', ''),
                       'ZALDT': p2.get('ZALDT', '')})

    # Write to Gold DB
    sqlcon = sqlite3.connect(DB)
    cur = sqlcon.cursor()
    cur.execute('DROP TABLE IF EXISTS REGUH_FAST')
    all_cols = list(merged[0].keys()) if merged else []
    cur.execute(f'CREATE TABLE REGUH_FAST ({", ".join(f"\"{c}\" TEXT" for c in all_cols)})')
    placeholders = ', '.join('?' * len(all_cols))
    print(f'Writing {len(merged):,} rows to REGUH_FAST...')
    batch = [[r.get(c, '') for c in all_cols] for r in merged]
    for i in range(0, len(batch), 5000):
        cur.executemany(f'INSERT INTO REGUH_FAST VALUES ({placeholders})', batch[i:i+5000])
    sqlcon.commit()
    for s in [
        'CREATE INDEX idx_rfast_lifnr ON REGUH_FAST(LIFNR)',
        'CREATE INDEX idx_rfast_zbukr ON REGUH_FAST(ZBUKR, RZAWE)',
        'CREATE INDEX idx_rfast_zaldt ON REGUH_FAST(ZALDT)',
        'CREATE INDEX idx_rfast_ubnks ON REGUH_FAST(UBNKS)',
    ]:
        cur.execute(s)
    sqlcon.commit()
    cur.execute('SELECT COUNT(*) FROM REGUH_FAST')
    print(f'REGUH_FAST count: {cur.fetchone()[0]:,}')
    sqlcon.close()
    print(f'DONE in {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
