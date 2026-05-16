"""Step 3: replay v6 logic across all 17,826 LIFNRs paid in /SEPA_CT_UNES UNES.
Compare v6 (PA0006-first) vs V0 (ADRC blind) per KTOKK."""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

db = sqlite3.connect('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')

# rebuild _univ from _sepa_uns_lifnrs file (since temp tables don't persist)
import json
univ = json.load(open('Zagentexecution/_sepa_universe.json'))

db.execute("DROP TABLE IF EXISTS _sim_univ")
db.execute("CREATE TABLE _sim_univ (LIFNR TEXT, KTOKK TEXT, NAME1 TEXT, ADRNR TEXT, PERNR_CAST TEXT)")
ph = ','.join('?'*len(univ['lifnrs']))
rows = list(db.execute(f"SELECT LIFNR,KTOKK,NAME1,ADRNR FROM LFA1 WHERE LIFNR IN ({ph})", univ['lifnrs']))
batch = [(r[0], r[1], r[2], r[3], r[0][-8:] if r[0] and r[0].isdigit() else None) for r in rows]
db.executemany("INSERT INTO _sim_univ VALUES (?,?,?,?,?)", batch)
db.commit()
db.execute("CREATE INDEX _ix_simu ON _sim_univ(LIFNR)")
db.execute("CREATE INDEX _ix_simu_pernr ON _sim_univ(PERNR_CAST)")
db.execute("CREATE INDEX _ix_simu_adrnr ON _sim_univ(ADRNR)")
print(f"_sim_univ: {len(batch):,} rows", flush=True)

# Apply v6 logic in pure SQL
print("\nRunning v6 simulation…", flush=True)
db.execute("DROP TABLE IF EXISTS sim_v6_results")
db.execute("""
CREATE TABLE sim_v6_results AS
SELECT
  u.LIFNR,
  u.KTOKK,
  u.NAME1,
  u.PERNR_CAST,
  u.ADRNR,
  -- V0 legacy: always reads ADRC
  a.STREET     AS v0_StrtNm,
  a.HOUSE_NUM1 AS v0_BldgNb,
  a.POST_CODE1 AS v0_PstCd,
  a.CITY1      AS v0_TwnNm,
  a.COUNTRY    AS v0_Ctry,
  a.REGION     AS v0_CtrySubDvsn,
  -- v6: PA0006 if hit, else ADRC
  CASE WHEN p.PERNR IS NOT NULL THEN p.STRAS ELSE a.STREET     END AS v6_StrtNm,
  CASE WHEN p.PERNR IS NOT NULL THEN ''      ELSE a.HOUSE_NUM1 END AS v6_BldgNb,
  CASE WHEN p.PERNR IS NOT NULL THEN p.PSTLZ ELSE a.POST_CODE1 END AS v6_PstCd,
  CASE WHEN p.PERNR IS NOT NULL THEN p.ORT01 ELSE a.CITY1      END AS v6_TwnNm,
  CASE WHEN p.PERNR IS NOT NULL THEN p.LAND1 ELSE a.COUNTRY    END AS v6_Ctry,
  CASE WHEN p.PERNR IS NOT NULL THEN p.STATE ELSE a.REGION     END AS v6_CtrySubDvsn,
  CASE WHEN p.PERNR IS NOT NULL THEN 'PA0006' ELSE 'ADRC'      END AS v6_path,
  CASE WHEN p.PERNR IS NOT NULL THEN 1 ELSE 0 END AS pa0006_hit
FROM _sim_univ u
LEFT JOIN _sim_pa0006 p ON p.PERNR = u.PERNR_CAST
LEFT JOIN _sim_adrc   a ON a.ADDRNUMBER = u.ADRNR
""")
db.commit()

# Add drift flag
db.execute("ALTER TABLE sim_v6_results ADD COLUMN drift INTEGER DEFAULT 0")
db.execute("""
UPDATE sim_v6_results
SET drift = CASE
  WHEN COALESCE(v6_StrtNm,'') <> COALESCE(v0_StrtNm,'')
    OR COALESCE(v6_PstCd,'')  <> COALESCE(v0_PstCd,'')
    OR COALESCE(v6_TwnNm,'')  <> COALESCE(v0_TwnNm,'')
    OR COALESCE(v6_Ctry,'')   <> COALESCE(v0_Ctry,'')
  THEN 1 ELSE 0 END
""")
db.commit()

# ─── REPORT ──────────────────────────────────────────────────────────────────
print("\n" + "="*120)
print("v6 SIMULATION RESULTS — /SEPA_CT_UNES UNES (17,826 LIFNRs over last 2 years)")
print("="*120)

print("\n[A] Drift summary by KTOKK (does v6 differ from V0?)\n")
print(f"  {'KTOKK':<10} {'total':>8} {'PA0006 hits':>13} {'drifted':>10} {'drift %':>9}  classification")
print(f"  {'─'*10} {'─'*8} {'─'*13} {'─'*10} {'─'*9}  {'─'*30}")
for r in db.execute("""SELECT KTOKK,
                              COUNT(*) total,
                              SUM(pa0006_hit) hits,
                              SUM(drift) drift
                       FROM sim_v6_results
                       GROUP BY KTOKK ORDER BY total DESC"""):
    k, tot, hits, drift = r
    rate = (drift or 0)/tot*100 if tot else 0
    cls = 'STAFF (drift expected)' if hits else 'NON-STAFF (no drift expected)'
    print(f"  {k or '(no LFA1)':<10} {tot:>8,} {hits or 0:>13,} {drift or 0:>10,} {rate:>8.1f}%  {cls}")

print("\n[B] Theory check — only employees should drift:")
total_drift = db.execute("SELECT SUM(drift) FROM sim_v6_results").fetchone()[0] or 0
total_hits  = db.execute("SELECT SUM(pa0006_hit) FROM sim_v6_results").fetchone()[0] or 0
violators   = db.execute("SELECT COUNT(*) FROM sim_v6_results WHERE drift=1 AND pa0006_hit=0").fetchone()[0]
no_drift_when_hit = db.execute("SELECT COUNT(*) FROM sim_v6_results WHERE drift=0 AND pa0006_hit=1").fetchone()[0]
print(f"  Total LIFNRs simulated   : {len(batch):,}")
print(f"  Total PA0006 hits        : {total_hits:,}")
print(f"  Total drifted (v6≠V0)    : {total_drift:,}")
print(f"  Drift WITHOUT PA0006 hit : {violators}  ← should be 0 if theory holds")
print(f"  PA0006 hit but no drift  : {no_drift_when_hit}  (means PA0006 == ADRC, edge case)")

print("\n[C] Sample drift rows — KTOKK=UNES staff (BERTOLDINI-like):")
for r in db.execute("""SELECT LIFNR,NAME1,v0_StrtNm,v6_StrtNm,v0_TwnNm,v6_TwnNm
                       FROM sim_v6_results
                       WHERE drift=1 AND KTOKK='UNES' AND pa0006_hit=1
                       LIMIT 6"""):
    print(f"  {r[0]} {r[1][:30]:<30}")
    print(f"    V0: {r[2][:40]:<40} | {r[4]}")
    print(f"    v6: {r[3][:40]:<40} | {r[5]}")

print("\n[D] Sample drift rows — KTOKK=SCSA staff:")
for r in db.execute("""SELECT LIFNR,NAME1,v0_StrtNm,v6_StrtNm
                       FROM sim_v6_results
                       WHERE drift=1 AND KTOKK='SCSA' AND pa0006_hit=1
                       LIMIT 6"""):
    print(f"  {r[0]} {r[1][:30]:<30}")
    print(f"    V0: {(r[2] or '(empty)')[:50]:<50}")
    print(f"    v6: {(r[3] or '(empty)')[:50]:<50}")

if violators > 0:
    print("\n[E] ⚠ Theory violators — drift WITHOUT PA0006 hit (would falsify the simulator):")
    for r in db.execute("""SELECT LIFNR,KTOKK,NAME1,v0_StrtNm,v6_StrtNm
                           FROM sim_v6_results WHERE drift=1 AND pa0006_hit=0 LIMIT 10"""):
        print(f"  {r[0]} ({r[1]}) {r[2][:30]}: V0={r[3][:30]} v6={r[4][:30]}")

print("\nResults persisted in Gold DB → table `sim_v6_results`")
