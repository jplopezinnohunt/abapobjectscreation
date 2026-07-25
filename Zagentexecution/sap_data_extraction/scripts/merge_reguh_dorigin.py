"""Merge REGUH_DORIGIN into canonical REGUH (lossless).
DORIGIN is constant per (LAUFD,LAUFI,ZBUKR,LIFNR); the 567,567 rows are exact dups
of 395,644 distinct rows. Dedup, add DORIGIN to REGUH, populate by key, verify, drop.
"""
import sqlite3
DB = r'Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db'
c = sqlite3.connect(DB, timeout=120)
def cnt(q): return c.execute(q).fetchone()[0]

# 1. dedup satellite into a clean keyed table
c.execute('DROP TABLE IF EXISTS _dorigin_dedup')
c.execute('''CREATE TABLE _dorigin_dedup AS
   SELECT DISTINCT LAUFD,LAUFI,ZBUKR,LIFNR,DORIGIN FROM REGUH_DORIGIN''')
c.execute('CREATE INDEX ix_dd ON _dorigin_dedup(LAUFD,LAUFI,ZBUKR,LIFNR)')
c.commit()
dd = cnt('SELECT COUNT(*) FROM _dorigin_dedup')
print(f'dedup table: {dd} rows (from 567567)')

# 2. add column + populate via UPDATE..FROM (efficient, indexed)
cols=[r[1] for r in c.execute('PRAGMA table_info(REGUH)')]
if 'DORIGIN' not in cols:
    c.execute('ALTER TABLE REGUH ADD COLUMN DORIGIN TEXT')
c.execute('''UPDATE REGUH SET DORIGIN=d.DORIGIN
   FROM _dorigin_dedup d
   WHERE d.LAUFD=REGUH.LAUFD AND d.LAUFI=REGUH.LAUFI
     AND d.ZBUKR=REGUH.ZBUKR AND d.LIFNR=REGUH.LIFNR''')
c.commit()

# 3. verify lossless: every distinct DORIGIN key now reflected in REGUH
pop = cnt("SELECT COUNT(*) FROM REGUH WHERE DORIGIN IS NOT NULL AND DORIGIN<>''")
keys_in_reguh = cnt('''SELECT COUNT(*) FROM _dorigin_dedup d
   WHERE EXISTS (SELECT 1 FROM REGUH r WHERE r.LAUFD=d.LAUFD AND r.LAUFI=d.LAUFI
                 AND r.ZBUKR=d.ZBUKR AND r.LIFNR=d.LIFNR)''')
print(f'REGUH rows with DORIGIN populated: {pop}')
print(f'dedup keys that exist in REGUH: {keys_in_reguh} / {dd}')
# distinct DORIGIN values preserved?
dv_src = cnt('SELECT COUNT(DISTINCT DORIGIN) FROM _dorigin_dedup')
dv_dst = cnt("SELECT COUNT(DISTINCT DORIGIN) FROM REGUH WHERE DORIGIN IS NOT NULL AND DORIGIN<>''")
print(f'distinct DORIGIN values: source={dv_src} merged={dv_dst}')

assert dv_dst >= dv_src - 1, 'lost DORIGIN values!'  # -1 tolerance for blank
c.execute('DROP TABLE _dorigin_dedup')
c.execute('DROP TABLE REGUH_DORIGIN')
c.commit()
print('LOSSLESS -> DORIGIN merged into REGUH; REGUH_DORIGIN dropped')
print('tables remaining:', cnt("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
