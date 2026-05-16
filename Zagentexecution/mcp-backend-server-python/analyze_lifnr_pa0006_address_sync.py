"""Quantify the sync gap between staff vendor master (LFA1/ADRC) and HR PA0006 home address.

Question: for staff LIFNRs (those with a PERNR_CAST), is the address on the vendor master
in sync with the address on PA0006? How many drift, and on which fields?

Methodology:
- _sim_univ has 15,800 staff LIFNRs with PERNR_CAST already mapped.
- _sim_adrc has the vendor's ADRC row keyed by ADRNR (= LFA1.ADRNR).
- _sim_pa0006 has the PERNR's HR home address (STRAS, PSTLZ, ORT01, LAND1, STATE).
- Compare normalized (UPPER, trimmed) field-by-field.
- Bucket: in_sync / drift_street / drift_city / drift_postcode / drift_country / missing_one_side / both_empty.

Output: console summary + sqlite table `_sync_staff_pa0006_vs_adrc`.
"""
import sqlite3
import os

DB = "Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"
print(f"DB: {DB}  exists={os.path.exists(DB)}")
db = sqlite3.connect(DB)
cur = db.cursor()

cur.execute("DROP TABLE IF EXISTS _sync_staff_pa0006_vs_adrc")
cur.execute("""
CREATE TABLE _sync_staff_pa0006_vs_adrc AS
SELECT
  u.LIFNR,
  u.KTOKK,
  u.NAME1,
  u.ADRNR,
  u.PERNR_CAST AS PERNR,
  a.STREET     AS adrc_street,
  a.HOUSE_NUM1 AS adrc_house_num,
  a.POST_CODE1 AS adrc_post_code,
  a.CITY1      AS adrc_city,
  a.COUNTRY    AS adrc_country,
  p.STRAS      AS pa_stras,
  p.PSTLZ      AS pa_pstlz,
  p.ORT01      AS pa_ort01,
  p.LAND1      AS pa_land1,
  -- normalized comparisons (UPPER + trim spaces collapse)
  CASE WHEN a.ADDRNUMBER IS NULL THEN 'ADRC_MISSING'
       WHEN p.PERNR IS NULL OR p.PERNR = '' THEN 'PA0006_MISSING'
       WHEN (COALESCE(a.STREET,'') = '' AND COALESCE(p.STRAS,'') = '') THEN 'BOTH_STREET_EMPTY'
       WHEN UPPER(TRIM(COALESCE(a.STREET,''))) = UPPER(TRIM(COALESCE(p.STRAS,''))) THEN 'STREET_IN_SYNC'
       ELSE 'STREET_DRIFT'
  END AS street_status,
  CASE WHEN a.ADDRNUMBER IS NULL THEN 'ADRC_MISSING'
       WHEN p.PERNR IS NULL OR p.PERNR = '' THEN 'PA0006_MISSING'
       WHEN (COALESCE(a.CITY1,'') = '' AND COALESCE(p.ORT01,'') = '') THEN 'BOTH_CITY_EMPTY'
       WHEN UPPER(TRIM(COALESCE(a.CITY1,''))) = UPPER(TRIM(COALESCE(p.ORT01,''))) THEN 'CITY_IN_SYNC'
       ELSE 'CITY_DRIFT'
  END AS city_status,
  CASE WHEN a.ADDRNUMBER IS NULL THEN 'ADRC_MISSING'
       WHEN p.PERNR IS NULL OR p.PERNR = '' THEN 'PA0006_MISSING'
       WHEN (COALESCE(a.POST_CODE1,'') = '' AND COALESCE(p.PSTLZ,'') = '') THEN 'BOTH_POSTAL_EMPTY'
       WHEN UPPER(TRIM(COALESCE(a.POST_CODE1,''))) = UPPER(TRIM(COALESCE(p.PSTLZ,''))) THEN 'POSTAL_IN_SYNC'
       ELSE 'POSTAL_DRIFT'
  END AS postal_status,
  CASE WHEN a.ADDRNUMBER IS NULL THEN 'ADRC_MISSING'
       WHEN p.PERNR IS NULL OR p.PERNR = '' THEN 'PA0006_MISSING'
       WHEN (COALESCE(a.COUNTRY,'') = '' AND COALESCE(p.LAND1,'') = '') THEN 'BOTH_CTRY_EMPTY'
       WHEN UPPER(TRIM(COALESCE(a.COUNTRY,''))) = UPPER(TRIM(COALESCE(p.LAND1,''))) THEN 'CTRY_IN_SYNC'
       ELSE 'CTRY_DRIFT'
  END AS country_status
FROM _sim_univ u
LEFT JOIN _sim_adrc a   ON a.ADDRNUMBER = u.ADRNR
LEFT JOIN _sim_pa0006 p ON p.PERNR      = u.PERNR_CAST
WHERE u.PERNR_CAST IS NOT NULL AND u.PERNR_CAST != ''
""")
db.commit()

print(f"\n=== Sync table built: _sync_staff_pa0006_vs_adrc ===")
cur.execute("SELECT COUNT(*) FROM _sync_staff_pa0006_vs_adrc")
total = cur.fetchone()[0]
print(f"Total staff LIFNRs with PERNR_CAST: {total:,}")

print(f"\n=== STREET status ===")
for r in cur.execute("SELECT street_status, COUNT(*) FROM _sync_staff_pa0006_vs_adrc GROUP BY street_status ORDER BY COUNT(*) DESC"):
    print(f"  {r[0]:30s} {r[1]:6,}  ({100*r[1]/total:5.1f}%)")

print(f"\n=== CITY status ===")
for r in cur.execute("SELECT city_status, COUNT(*) FROM _sync_staff_pa0006_vs_adrc GROUP BY city_status ORDER BY COUNT(*) DESC"):
    print(f"  {r[0]:30s} {r[1]:6,}  ({100*r[1]/total:5.1f}%)")

print(f"\n=== POSTAL status ===")
for r in cur.execute("SELECT postal_status, COUNT(*) FROM _sync_staff_pa0006_vs_adrc GROUP BY postal_status ORDER BY COUNT(*) DESC"):
    print(f"  {r[0]:30s} {r[1]:6,}  ({100*r[1]/total:5.1f}%)")

print(f"\n=== COUNTRY status ===")
for r in cur.execute("SELECT country_status, COUNT(*) FROM _sync_staff_pa0006_vs_adrc GROUP BY country_status ORDER BY COUNT(*) DESC"):
    print(f"  {r[0]:30s} {r[1]:6,}  ({100*r[1]/total:5.1f}%)")

print(f"\n=== ANY drift (street OR city OR postal OR country) by KTOKK ===")
cur.execute("""
SELECT KTOKK,
       COUNT(*) AS n,
       SUM(CASE WHEN street_status IN ('STREET_DRIFT')
                 OR city_status   IN ('CITY_DRIFT')
                 OR postal_status IN ('POSTAL_DRIFT')
                 OR country_status IN ('CTRY_DRIFT') THEN 1 ELSE 0 END) AS any_drift,
       SUM(CASE WHEN street_status = 'STREET_DRIFT' THEN 1 ELSE 0 END) AS street_drift,
       SUM(CASE WHEN city_status   = 'CITY_DRIFT'   THEN 1 ELSE 0 END) AS city_drift,
       SUM(CASE WHEN postal_status = 'POSTAL_DRIFT' THEN 1 ELSE 0 END) AS postal_drift,
       SUM(CASE WHEN country_status = 'CTRY_DRIFT'  THEN 1 ELSE 0 END) AS country_drift
FROM _sync_staff_pa0006_vs_adrc
GROUP BY KTOKK
ORDER BY any_drift DESC
""")
print(f"  {'KTOKK':6s} {'TOTAL':>7s} {'ANY':>7s}  {'STREET':>7s} {'CITY':>7s} {'POSTAL':>7s} {'CTRY':>7s}")
for r in cur.fetchall():
    print(f"  {r[0]:6s} {r[1]:7,d} {r[2]:7,d}  {r[3]:7,d} {r[4]:7,d} {r[5]:7,d} {r[6]:7,d}")

print(f"\n=== Sample 8 STREET_DRIFT rows ===")
for r in cur.execute("""
SELECT LIFNR, KTOKK, NAME1,
       SUBSTR(adrc_street,1,40) AS adrc_st,
       SUBSTR(pa_stras,1,40)    AS pa_st,
       SUBSTR(adrc_city,1,20)   AS adrc_ct,
       SUBSTR(pa_ort01,1,20)    AS pa_ct
FROM _sync_staff_pa0006_vs_adrc
WHERE street_status = 'STREET_DRIFT'
LIMIT 8
"""):
    print(f"  {r[0]} {r[1]} {r[2][:30]:30s}")
    print(f"    ADRC: {r[3]!r:42s} / {r[5]!r}")
    print(f"    PA06: {r[4]!r:42s} / {r[6]!r}")
