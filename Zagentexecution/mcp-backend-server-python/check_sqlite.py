"""check_sqlite.py - Check what's in the existing SQLite databases"""
import sqlite3, os

dbs = [
    r'C:\Users\jp_lopez\projects\abapobjectscreation\knowledge\domains\PSM\p01_gold_master_data.db',
    r'C:\Users\jp_lopez\projects\abapobjectscreation\knowledge\domains\PSM\p01_master_data_v2.db',
]

for db_path in dbs:
    if not os.path.exists(db_path): continue
    print(f'\n=== {os.path.basename(db_path)} ({os.path.getsize(db_path)//1024}KB) ===')
    conn = sqlite3.connect(db_path)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for (tname,) in tables:
        cnt = conn.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
        cols = [c[1] for c in conn.execute(f'PRAGMA table_info("{tname}")').fetchall()]
        print(f'  {tname}: {cnt:,} rows | cols: {cols}')
        # Check for TADIR-like columns
        col_lower = [c.lower() for c in cols]
        if any(k in col_lower for k in ['devclass','obj_name','object','package']):
            print(f'    ** Has TADIR-like columns!')
            row = conn.execute(f'SELECT * FROM "{tname}" LIMIT 3').fetchall()
            for r in row: print(f'    sample: {r}')
    conn.close()
