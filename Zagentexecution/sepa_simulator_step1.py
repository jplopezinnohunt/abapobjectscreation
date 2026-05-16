"""Step 1: identify universe of LIFNRs paid in /SEPA_CT_UNES UNES (last 2y)."""
import sqlite3, sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp-backend-server-python'))
sys.stdout.reconfigure(encoding='utf-8')

DB = 'Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db'
db = sqlite3.connect(DB)
print("step a: SEPA UNES runs from DFPAYG", flush=True)
runs = list(db.execute("SELECT DISTINCT LAUFD,LAUFI FROM DFPAYG WHERE FORMI='/SEPA_CT_UNES' AND ZBUKR='UNES'"))
print(f"  {len(runs)} runs", flush=True)

# Materialize runs as a real table (avoid CTE perf hit)
db.execute("DROP TABLE IF EXISTS _runs")
db.execute("CREATE TABLE _runs (LAUFD TEXT, LAUFI TEXT)")
db.executemany("INSERT INTO _runs VALUES (?,?)", runs)
db.commit()
db.execute("CREATE INDEX _ix_runs ON _runs(LAUFD, LAUFI)")

print("step b: distinct LIFNR via JOIN", flush=True)
sql = """SELECT DISTINCT h.LIFNR FROM _runs r
         INNER JOIN REGUH h INDEXED BY idx_reguh_run
           ON h.LAUFD=r.LAUFD AND h.LAUFI=r.LAUFI AND h.ZBUKR='UNES'
         WHERE h.VBLNR<>''"""
lifnrs = [r[0] for r in db.execute(sql)]
print(f"Universe: {len(lifnrs):,} LIFNRs", flush=True)

# enrich with KTOKK + ADRNR via Gold DB LFA1
db.execute("DROP TABLE IF EXISTS _univ")
db.execute("""CREATE TABLE _univ (LIFNR TEXT, KTOKK TEXT, NAME1 TEXT, ADRNR TEXT)""")
ph = ','.join('?' * len(lifnrs))
rows = list(db.execute(f"""SELECT LIFNR,KTOKK,NAME1,ADRNR FROM LFA1 WHERE LIFNR IN ({ph})""", lifnrs))
db.executemany("INSERT INTO _univ VALUES (?,?,?,?)", rows)
db.commit()
db.execute("CREATE INDEX _ix_univ ON _univ(LIFNR)")
print(f"LFA1 enriched: {len(rows):,} rows")

print("\nBy KTOKK (paid in /SEPA_CT_UNES UNES):")
for r in db.execute("SELECT KTOKK, COUNT(*) FROM _univ GROUP BY KTOKK ORDER BY 2 DESC"):
    print(f"  {r[0] or '(no LFA1)':<10}  {r[1]:>6}")

# distinct sets
adrnrs = sorted({r[0] for r in db.execute("SELECT ADRNR FROM _univ WHERE ADRNR<>'' AND ADRNR<>'0000000000' AND ADRNR IS NOT NULL")})
pernrs = sorted({r[0][-8:] for r in db.execute("SELECT LIFNR FROM _univ") if r[0] and r[0].isdigit()})
print(f"\nDistinct ADRNR: {len(adrnrs):,}")
print(f"Distinct PERNR cast (numeric LIFNRs only): {len(pernrs):,}")

with open('Zagentexecution/_sepa_universe.json', 'w') as f:
    json.dump({'lifnrs': lifnrs, 'adrnrs': adrnrs, 'pernrs': pernrs}, f)
print("\nSaved → Zagentexecution/_sepa_universe.json")
