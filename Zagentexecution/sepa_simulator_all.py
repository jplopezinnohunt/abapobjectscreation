"""All-SEPA v6 simulator — replays v6 logic across every SEPA format × cocode pair
that fired in P01 over the last 2 years."""
import sqlite3, sys, json, time, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp-backend-server-python'))
sys.stdout.reconfigure(encoding='utf-8')
from rfc_helpers import get_connection

db = sqlite3.connect('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')

# 1. Identify all SEPA (format, cocode) tuples with traffic
sepa_pairs = list(db.execute("""
    SELECT DISTINCT FORMI, ZBUKR, COUNT(DISTINCT LAUFD||LAUFI) AS runs
    FROM DFPAYG WHERE FORMI LIKE '/SEPA%'
    GROUP BY FORMI, ZBUKR ORDER BY runs DESC
"""))
print("SEPA pairs (last 2y):")
for f, z, n in sepa_pairs:
    print(f"  {f:<35} {z:<6} {n:>5} runs")

# 2. Build universe = all distinct LIFNRs paid via any SEPA format
db.execute("DROP TABLE IF EXISTS _sepa_universe_all")
db.execute("""CREATE TABLE _sepa_universe_all AS
              SELECT DISTINCT g.FORMI, g.ZBUKR, h.LIFNR
              FROM DFPAYG g
              JOIN REGUH h INDEXED BY idx_reguh_run
                ON h.LAUFD=g.LAUFD AND h.LAUFI=g.LAUFI AND h.ZBUKR=g.ZBUKR
              WHERE g.FORMI LIKE '/SEPA%' AND h.VBLNR<>''""")
db.commit()
db.execute("CREATE INDEX _ix_sepa_uall ON _sepa_universe_all(LIFNR)")
n = db.execute("SELECT COUNT(*) FROM _sepa_universe_all").fetchone()[0]
distinct_lifnrs = db.execute("SELECT COUNT(DISTINCT LIFNR) FROM _sepa_universe_all").fetchone()[0]
print(f"\n_sepa_universe_all: {n:,} (FORMI,ZBUKR,LIFNR) tuples, {distinct_lifnrs:,} distinct LIFNRs")

# 3. Top up master data: extract any new ADRNR not already in _sim_adrc
new_lifnrs = [r[0] for r in db.execute("""
    SELECT DISTINCT LIFNR FROM _sepa_universe_all
    WHERE LIFNR NOT IN (SELECT LIFNR FROM _sim_univ)
""")]
print(f"\nNew LIFNRs not yet in master cache: {len(new_lifnrs):,}")

if new_lifnrs:
    # Bring their LFA1 master into _sim_univ
    ph = ','.join('?'*len(new_lifnrs))
    rows = list(db.execute(f"SELECT LIFNR,KTOKK,NAME1,ADRNR FROM LFA1 WHERE LIFNR IN ({ph})", new_lifnrs))
    extra = [(r[0], r[1], r[2], r[3], r[0][-8:] if r[0] and r[0].isdigit() else None) for r in rows]
    db.executemany("INSERT INTO _sim_univ VALUES (?,?,?,?,?)", extra)
    db.commit()
    print(f"  +{len(extra)} into _sim_univ")

    # Need ADRC for new ADRNRs not yet cached
    new_adrnrs = sorted({a for a in (r[3] for r in rows) if a and a != '0000000000'} -
                       {r[0] for r in db.execute("SELECT ADDRNUMBER FROM _sim_adrc")})
    print(f"  new ADRNR to fetch from P01: {len(new_adrnrs)}")
    if new_adrnrs:
        c = get_connection("P01")
        def chunked(seq, n):
            for i in range(0, len(seq), n): yield seq[i:i+n]
        added = 0
        for batch_adr in chunked(new_adrnrs, 500):
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
            wanted = set(batch_adr)
            recs = [[p.strip() for p in row['WA'].split('|')] for row in r['DATA']]
            recs = [x for x in recs if x[0] in wanted]
            db.executemany(f"INSERT INTO _sim_adrc VALUES ({','.join('?'*8)})", recs)
            added += len(recs)
        db.commit()
        print(f"  +{added} into _sim_adrc")

# 4. Re-run simulation across all SEPA (format, cocode) pairs
print("\n[Running simulation across all SEPA pairs]", flush=True)
db.execute("DROP TABLE IF EXISTS sim_sepa_all")
db.execute("""
CREATE TABLE sim_sepa_all AS
SELECT
  ua.FORMI, ua.ZBUKR, u.LIFNR, u.KTOKK, u.NAME1, u.PERNR_CAST, u.ADRNR,
  a.STREET     AS v0_StrtNm,
  a.POST_CODE1 AS v0_PstCd,
  a.CITY1      AS v0_TwnNm,
  a.COUNTRY    AS v0_Ctry,
  CASE WHEN p.PERNR IS NOT NULL THEN p.STRAS ELSE a.STREET     END AS v6_StrtNm,
  CASE WHEN p.PERNR IS NOT NULL THEN p.PSTLZ ELSE a.POST_CODE1 END AS v6_PstCd,
  CASE WHEN p.PERNR IS NOT NULL THEN p.ORT01 ELSE a.CITY1      END AS v6_TwnNm,
  CASE WHEN p.PERNR IS NOT NULL THEN p.LAND1 ELSE a.COUNTRY    END AS v6_Ctry,
  CASE WHEN p.PERNR IS NOT NULL THEN 1 ELSE 0 END AS pa0006_hit,
  CASE WHEN COALESCE((CASE WHEN p.PERNR IS NOT NULL THEN p.STRAS ELSE a.STREET END),'')
         <> COALESCE(a.STREET,'') THEN 1 ELSE 0 END AS drift
FROM _sepa_universe_all ua
LEFT JOIN _sim_univ u   ON u.LIFNR = ua.LIFNR
LEFT JOIN _sim_pa0006 p ON p.PERNR = u.PERNR_CAST
LEFT JOIN _sim_adrc   a ON a.ADDRNUMBER = u.ADRNR
""")
db.commit()

# Report
print("\n" + "="*120)
print("v6 SIMULATION — All SEPA formats × cocodes (last 2 years, P01)")
print("="*120)

print(f"\n{'FORMI':<35} {'COCODE':<6} {'KTOKK':<10} {'vendors':>8} {'PA0006 hit':>11} {'drift':>7} {'drift %':>9}")
print(f"{'-'*35} {'-'*6} {'-'*10} {'-'*8} {'-'*11} {'-'*7} {'-'*9}")
prev = (None, None)
for r in db.execute("""SELECT FORMI, ZBUKR, KTOKK,
                              COUNT(*) v, SUM(pa0006_hit) h, SUM(drift) d
                       FROM sim_sepa_all
                       GROUP BY FORMI, ZBUKR, KTOKK
                       ORDER BY FORMI, ZBUKR, v DESC"""):
    f, z, k, v, h, d = r
    rate = (d or 0)/v*100 if v else 0
    if (f, z) != prev:
        print(f"{'─'*35} {'─'*6} {'─'*10} {'─'*8} {'─'*11} {'─'*7} {'─'*9}")
        prev = (f, z)
    print(f"{f:<35} {z:<6} {(k or '(no LFA1)'):<10} {v:>8,} {h or 0:>11,} {d or 0:>7,} {rate:>8.1f}%")

# Theory holders / violators
print("\n[Theory check across all SEPA]")
total = db.execute("SELECT COUNT(*) FROM sim_sepa_all").fetchone()[0]
hits = db.execute("SELECT SUM(pa0006_hit) FROM sim_sepa_all").fetchone()[0] or 0
drift = db.execute("SELECT SUM(drift) FROM sim_sepa_all").fetchone()[0] or 0
violators = db.execute("SELECT COUNT(*) FROM sim_sepa_all WHERE drift=1 AND pa0006_hit=0").fetchone()[0]
print(f"  Total tuples       : {total:,}")
print(f"  PA0006 hits        : {hits:,}")
print(f"  Drift (v6 != V0)   : {drift:,}")
print(f"  Theory violators   : {violators}  ← drift WITHOUT PA0006 hit")
