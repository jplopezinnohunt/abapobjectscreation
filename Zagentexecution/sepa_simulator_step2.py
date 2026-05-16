"""Step 2: bulk extract PA0006 SUBTY=1 (active) + ADRC from P01 for the universe."""
import sqlite3, sys, json, time, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp-backend-server-python'))
sys.stdout.reconfigure(encoding='utf-8')
from rfc_helpers import get_connection

c = get_connection("P01")
db = sqlite3.connect('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')

univ = json.load(open('Zagentexecution/_sepa_universe.json'))
adrnrs = univ['adrnrs']
pernrs = univ['pernrs']

# ─── PA0006 SUBTY=1 active (small set, ~2K rows total at UNESCO) ────────────
db.execute("DROP TABLE IF EXISTS _sim_pa0006")
db.execute("""CREATE TABLE _sim_pa0006 (
    PERNR TEXT, STRAS TEXT, PSTLZ TEXT, ORT01 TEXT, LAND1 TEXT, STATE TEXT
)""")
print("[PA0006] extracting all active SUBTY=1 from P01…", flush=True)
t0 = time.time()
SKIP, PAGE, total = 0, 30000, 0
while True:
    r = c.call("RFC_READ_TABLE", QUERY_TABLE='PA0006',
               DELIMITER='|',
               FIELDS=[{'FIELDNAME':'PERNR'},{'FIELDNAME':'STRAS'},
                       {'FIELDNAME':'PSTLZ'},{'FIELDNAME':'ORT01'},
                       {'FIELDNAME':'LAND1'},{'FIELDNAME':'STATE'}],
               OPTIONS=[{'TEXT':"SUBTY = '1' AND ENDDA >= '20260509'"},
                        {'TEXT':" AND BEGDA <= '20260509'"}],
               ROWCOUNT=PAGE, ROWSKIPS=SKIP)
    rows = r['DATA']
    if not rows: break
    batch = [[p.strip() for p in row['WA'].split('|')][:6] for row in rows]
    db.executemany(f"INSERT INTO _sim_pa0006 VALUES ({','.join('?'*6)})", batch)
    db.commit()
    total += len(batch)
    if len(rows) < PAGE: break
    SKIP += PAGE
db.execute("CREATE INDEX _ix_sim_pa ON _sim_pa0006(PERNR)")
print(f"  PA0006 active: {total:,} rows ({time.time()-t0:.0f}s)", flush=True)

# ─── ADRC for distinct ADRNR set, chunked ────────────────────────────────────
db.execute("DROP TABLE IF EXISTS _sim_adrc")
db.execute("""CREATE TABLE _sim_adrc (
    ADDRNUMBER TEXT, NAME1 TEXT, STREET TEXT, HOUSE_NUM1 TEXT,
    POST_CODE1 TEXT, CITY1 TEXT, COUNTRY TEXT, REGION TEXT
)""")

# Chunk ADRNRs into batches that fit OPTIONS text limit (~72 chars per row)
def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

print(f"[ADRC] extracting {len(adrnrs):,} ADRNRs from P01 (chunked)…", flush=True)
t0 = time.time()
total = 0
# Approach: build OPTIONS as multiple rows joined with OR, each row a partial IN clause
# Use ADDRNUMBER >= 'x' AND <= 'y' range chunks instead — much more efficient
# Sort ADRNRs and chunk by 500 (range bracket) → 30 chunks
chunks = list(chunked(sorted(adrnrs), 500))
for i, batch_adr in enumerate(chunks):
    lo, hi = batch_adr[0], batch_adr[-1]
    r = c.call("RFC_READ_TABLE", QUERY_TABLE='ADRC',
               DELIMITER='|',
               FIELDS=[{'FIELDNAME':'ADDRNUMBER'},{'FIELDNAME':'NAME1'},
                       {'FIELDNAME':'STREET'},{'FIELDNAME':'HOUSE_NUM1'},
                       {'FIELDNAME':'POST_CODE1'},{'FIELDNAME':'CITY1'},
                       {'FIELDNAME':'COUNTRY'},{'FIELDNAME':'REGION'}],
               OPTIONS=[{'TEXT':f"ADDRNUMBER >= '{lo}'"},
                        {'TEXT':f" AND ADDRNUMBER <= '{hi}'"},
                        {'TEXT':f" AND DATE_FROM <= '20260509'"},
                        {'TEXT':f" AND DATE_TO   >= '20260509'"}],
               ROWCOUNT=20000)
    rows = r['DATA']
    rec = [[p.strip() for p in row['WA'].split('|')] for row in rows]
    # Filter to only requested ADRNRs (range may include unwanted)
    wanted = set(batch_adr)
    rec = [x for x in rec if x[0] in wanted]
    db.executemany(f"INSERT INTO _sim_adrc VALUES ({','.join('?'*8)})", rec)
    db.commit()
    total += len(rec)
    print(f"  chunk {i+1}/{len(chunks)} [{lo}..{hi}]: +{len(rec)} (cumulative {total:,})", flush=True)

db.execute("CREATE INDEX _ix_sim_adrc ON _sim_adrc(ADDRNUMBER)")
print(f"\n  ADRC date-valid: {total:,} rows in {time.time()-t0:.0f}s", flush=True)

# Verify coverage
m_pa = db.execute("SELECT COUNT(*) FROM _sim_pa0006").fetchone()[0]
m_ad = db.execute("SELECT COUNT(DISTINCT ADDRNUMBER) FROM _sim_adrc").fetchone()[0]
print(f"\nFinal: PA0006 active={m_pa}, ADRC distinct ADRNR={m_ad} of {len(adrnrs):,} requested")
