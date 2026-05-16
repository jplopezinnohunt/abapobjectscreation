"""Theoretical v6-equivalent drift across ALL formats — CGI, CITI, SEPA — to estimate
the structured-address bug surface across UNESCO's full payment landscape."""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

db = sqlite3.connect('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')

# 1. Build universe = all distinct (FORMI, ZBUKR, LIFNR) tuples from DFPAYG ↔ REGUH
db.execute("DROP TABLE IF EXISTS _univ_all")
db.execute("""CREATE TABLE _univ_all AS
              SELECT DISTINCT g.FORMI, g.ZBUKR, h.LIFNR
              FROM DFPAYG g
              JOIN REGUH h INDEXED BY idx_reguh_run
                ON h.LAUFD=g.LAUFD AND h.LAUFI=g.LAUFI AND h.ZBUKR=g.ZBUKR
              WHERE h.VBLNR<>''""")
db.commit()
db.execute("CREATE INDEX _ix_univ_all ON _univ_all(LIFNR)")
n = db.execute("SELECT COUNT(*) FROM _univ_all").fetchone()[0]
print(f"Universe (all formats × cocodes × LIFNRs): {n:,}")

# 2. Coverage check: how many LIFNRs already have master data cached
covered = db.execute("""SELECT COUNT(DISTINCT u.LIFNR) FROM _univ_all u
                        INNER JOIN _sim_univ s ON s.LIFNR=u.LIFNR""").fetchone()[0]
total = db.execute("SELECT COUNT(DISTINCT LIFNR) FROM _univ_all").fetchone()[0]
print(f"Master data cached: {covered:,}/{total:,} ({covered/total*100:.1f}%)")
print(f"Uncovered (need P01 fetch later): {total-covered:,}")

# 3. Run simulation on the COVERED subset
print("\n[Simulating drift across all formats — covered subset only]")
db.execute("DROP TABLE IF EXISTS sim_all_formats")
db.execute("""
CREATE TABLE sim_all_formats AS
SELECT
  ua.FORMI, ua.ZBUKR, ua.LIFNR, u.KTOKK, u.NAME1, u.PERNR_CAST,
  a.STREET     AS v0_StrtNm,
  a.POST_CODE1 AS v0_PstCd,
  a.CITY1      AS v0_TwnNm,
  CASE WHEN p.PERNR IS NOT NULL THEN p.STRAS ELSE a.STREET END AS v6_StrtNm,
  CASE WHEN p.PERNR IS NOT NULL THEN p.PSTLZ ELSE a.POST_CODE1 END AS v6_PstCd,
  CASE WHEN p.PERNR IS NOT NULL THEN p.ORT01 ELSE a.CITY1 END AS v6_TwnNm,
  CASE WHEN p.PERNR IS NOT NULL THEN 1 ELSE 0 END AS pa0006_hit,
  CASE WHEN COALESCE((CASE WHEN p.PERNR IS NOT NULL THEN p.STRAS ELSE a.STREET END),'')
         <> COALESCE(a.STREET,'') THEN 1 ELSE 0 END AS drift
FROM _univ_all ua
LEFT JOIN _sim_univ u   ON u.LIFNR = ua.LIFNR
LEFT JOIN _sim_pa0006 p ON p.PERNR = u.PERNR_CAST
LEFT JOIN _sim_adrc   a ON a.ADDRNUMBER = u.ADRNR
""")
db.commit()

# 4. Report per FORMI: drift would-be count
print("\n" + "="*120)
print("DRIFT FORECAST — if v6 PA0006-first detection were applied to each format")
print("="*120)
print(f"\n{'FORMI':<35} {'COCODE':<6} {'vendors':>9} {'PA0006 hit':>11} {'drift forecast':>15} {'drift %':>9}")
print(f"{'─'*35} {'─'*6} {'─'*9} {'─'*11} {'─'*15} {'─'*9}")
for r in db.execute("""SELECT FORMI, ZBUKR,
                              COUNT(*) v, SUM(pa0006_hit) h, SUM(drift) d
                       FROM sim_all_formats
                       GROUP BY FORMI, ZBUKR
                       ORDER BY d DESC, v DESC"""):
    f, z, v, h, d = r
    rate = (d or 0)/v*100 if v else 0
    print(f"{f:<35} {z:<6} {v:>9,} {h or 0:>11,} {d or 0:>15,} {rate:>8.1f}%")

# 5. Aggregate by format only (collapse cocodes)
print("\n[Aggregate by FORMI — collapse cocodes]")
print(f"{'FORMI':<35} {'cocodes':>8} {'vendors':>9} {'drift':>9} {'drift %':>9}")
print(f"{'─'*35} {'─'*8} {'─'*9} {'─'*9} {'─'*9}")
for r in db.execute("""SELECT FORMI, COUNT(DISTINCT ZBUKR) cc,
                              COUNT(*) v, SUM(drift) d
                       FROM sim_all_formats
                       GROUP BY FORMI ORDER BY d DESC"""):
    f, cc, v, d = r
    rate = (d or 0)/v*100 if v else 0
    print(f"{f:<35} {cc:>8} {v:>9,} {d or 0:>9,} {rate:>8.1f}%")

# 6. Total impact estimate
total = db.execute("SELECT COUNT(*) FROM sim_all_formats").fetchone()[0]
hits = db.execute("SELECT SUM(pa0006_hit) FROM sim_all_formats").fetchone()[0] or 0
drift = db.execute("SELECT SUM(drift) FROM sim_all_formats").fetchone()[0] or 0
violators = db.execute("SELECT COUNT(*) FROM sim_all_formats WHERE drift=1 AND pa0006_hit=0").fetchone()[0]
print(f"\nTotals (covered subset):")
print(f"  Tuples           : {total:,}")
print(f"  PA0006 hits      : {hits:,}")
print(f"  Drift forecast   : {drift:,}  ← staff cases that would be corrected")
print(f"  Theory violators : {violators}")
