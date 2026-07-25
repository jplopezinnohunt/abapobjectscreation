"""
extract_ps_status_validation.py
================================
Extract status-validation tables to enrich Pool Health Matrix:
- PRPS broader field list (replace existing 8-field version with full status fields)
- JEST  (status records — link OBJNR to status code I0001/I0002/...)
- TJ02T (status text master — code -> "REL", "TECO", "CLSD", "LKD" etc)
- TJ30T (user-defined status text)

Driven by INC-000005638 model-gap analysis user question:
"did we validate if the PS projects are active?"

Without these tables, the Pool Health Matrix cannot distinguish active vs
closed/deleted WBSs, so the deficit count is inflated by inactive noise.
"""
import os, sys, sqlite3, time
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'mcp-backend-server-python')))
from rfc_helpers import get_connection, rfc_read_paginated

GOLD = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"
db = sqlite3.connect(GOLD)

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
LOG = os.path.join(LOG_DIR, f"ps_status_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
def log(s):
    line = f"{datetime.now().strftime('%H:%M:%S')} {s}"
    print(line, flush=True)
    with open(LOG, 'a', encoding='utf-8') as f: f.write(line + '\n')


def load(tbl, rows):
    if not rows: return 0
    fields = sorted({k for r in rows for k in r.keys()})
    cols_def = ", ".join([f'"{f}" TEXT' for f in fields])
    db.execute(f'CREATE TABLE IF NOT EXISTS {tbl.lower()} ({cols_def})')
    existing = {row[1] for row in db.execute(f'PRAGMA table_info({tbl.lower()})').fetchall()}
    for f in fields:
        if f not in existing:
            db.execute(f'ALTER TABLE {tbl.lower()} ADD COLUMN "{f}" TEXT')
    placeholders = ", ".join(["?"]*len(fields))
    cols = ", ".join([f'"{f}"' for f in fields])
    batch = [tuple(r.get(f,"") for f in fields) for r in rows]
    db.executemany(f'INSERT INTO {tbl.lower()} ({cols}) VALUES ({placeholders})', batch)
    db.commit()
    return len(batch)


# ---------- PRPS broader re-extract ----------
log("=== PRPS broader re-extract (drop + re-pull) ===")
db.execute("DROP TABLE IF EXISTS prps_full")
db.commit()
try:
    conn = get_connection("P01")
    rows = rfc_read_paginated(
        conn, "PRPS",
        ["PSPNR","POSID","POST1","OBJNR","PSPHI","PBUKR","ERDAT","ERNAM",
         "AEDAT","AENAM","LOEKZ","STUFE","PSPRI","ASTNR","STSMA",
         "PRART","PSTYP","FKSTL","FKBER","KKBER","SOBSL","KOSTL","FONDS",
         "GEBER","FISTL","FIPEX"],
        "",
        batch_size=5000, throttle=3.0
    )
    conn.close()
    n = load("prps_full", rows)
    log(f"  prps_full loaded: {n:,} rows")
except Exception as e:
    log(f"  PRPS_FULL ERROR: {type(e).__name__}: {e}")

# ---------- JEST — status records for PR* objects ----------
log("=== JEST extract (status records for PR*) ===")
try:
    conn = get_connection("P01")
    rows = rfc_read_paginated(
        conn, "JEST", [],
        "OBJNR LIKE 'PR%'",
        batch_size=5000, throttle=3.0
    )
    conn.close()
    n = load("jest", rows)
    log(f"  jest loaded: {n:,} rows")
except Exception as e:
    log(f"  JEST ERROR: {type(e).__name__}: {e}")

# ---------- TJ02T — system status text ----------
log("=== TJ02T extract (system status text) ===")
try:
    conn = get_connection("P01")
    rows = rfc_read_paginated(
        conn, "TJ02T", [],
        "SPRAS = 'E'",
        batch_size=5000, throttle=3.0
    )
    conn.close()
    n = load("tj02t", rows)
    log(f"  tj02t loaded: {n:,} rows")
except Exception as e:
    log(f"  TJ02T ERROR: {type(e).__name__}: {e}")

# ---------- TJ30T — user status text (per status profile) ----------
log("=== TJ30T extract (user status text) ===")
try:
    conn = get_connection("P01")
    rows = rfc_read_paginated(
        conn, "TJ30T", [],
        "SPRAS = 'E'",
        batch_size=5000, throttle=3.0
    )
    conn.close()
    n = load("tj30t", rows)
    log(f"  tj30t loaded: {n:,} rows")
except Exception as e:
    log(f"  TJ30T ERROR: {type(e).__name__}: {e}")

log("=== DONE ===")
db.close()
