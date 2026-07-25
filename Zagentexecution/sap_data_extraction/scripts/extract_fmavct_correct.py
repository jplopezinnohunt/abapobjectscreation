"""Extract FMAVCT with the CORRECT key (RLDNR='9H', not RFIKRS).
Key per DD03L: RCLNT, RLDNR, RRCTY, RVERS, RYEAR, ROBJNR, COBJNR, SOBJNR, RTCUR, DRCRK, RPMAX
UNESCO ledger = '9H' per brain claims (env=9HZ00001).
"""
import os, sys, sqlite3, time
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'mcp-backend-server-python')))
from rfc_helpers import get_connection, rfc_read_paginated

GOLD = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"
db = sqlite3.connect(GOLD)

def log(s): print(f"{datetime.now().strftime('%H:%M:%S')} {s}", flush=True)

for year in ['2024','2025','2026']:
    where = f"RLDNR = '9H' AND RYEAR = '{year}'"
    log(f"FMAVCT WHERE {where}")
    t0 = time.time()
    try:
        conn = get_connection("P01")
        rows = rfc_read_paginated(conn, "FMAVCT", [], where, batch_size=5000, throttle=3.0)
        conn.close()
        log(f"  -> {len(rows):,} rows in {time.time()-t0:.0f}s")
        if rows:
            fields = sorted({k for r in rows for k in r.keys()})
            cols_def = ", ".join([f'"{f}" TEXT' for f in fields])
            db.execute(f'CREATE TABLE IF NOT EXISTS fmavct ({cols_def})')
            existing = {row[1] for row in db.execute('PRAGMA table_info(fmavct)').fetchall()}
            for f in fields:
                if f not in existing:
                    db.execute(f'ALTER TABLE fmavct ADD COLUMN "{f}" TEXT')
            placeholders = ", ".join(["?"]*len(fields))
            cols = ", ".join([f'"{f}"' for f in fields])
            batch = [tuple(r.get(f,"") for f in fields) for r in rows]
            db.executemany(f'INSERT INTO fmavct ({cols}) VALUES ({placeholders})', batch)
            db.commit()
    except Exception as e:
        log(f"  ERROR {type(e).__name__}: {e}")

log("done")
db.close()
