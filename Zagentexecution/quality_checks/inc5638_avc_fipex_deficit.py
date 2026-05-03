"""
INC-000005638 class detector — find all (Fund, FundCenter) combinations
where revenue (WRTTP=66) is concentrated on FIPEX='REVENUE' placeholder
but consumption sits on operational FIPEX, creating per-FIPEX AVC deficit
even though the fund-level pool has surplus.

This is the "FIPEX revenue/consumption mismatch" class.
"""
import sqlite3
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB = r'c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db'
con = sqlite3.connect(DB)
cur = con.cursor()

con.executescript("""
DROP TABLE IF EXISTS tmp_consume;
DROP TABLE IF EXISTS tmp_commit;
DROP TABLE IF EXISTS tmp_rev;

CREATE TEMP TABLE tmp_consume AS
SELECT BUKRS, FONDS, FISTL, FIPEX, SUM(FKBTR) AS used
FROM fmifiit_full WHERE WRTTP IN ('54','57') AND FONDS IS NOT NULL
GROUP BY BUKRS, FONDS, FISTL, FIPEX;

CREATE TEMP TABLE tmp_commit AS
SELECT BUKRS, FONDS, FISTL, FIPEX, SUM(FKBTR) AS comm
FROM fmioi WHERE WRTTP IN ('51','52','65','81','82') AND FONDS IS NOT NULL
GROUP BY BUKRS, FONDS, FISTL, FIPEX;

CREATE TEMP TABLE tmp_rev AS
SELECT BUKRS, FONDS, FISTL, FIPEX, SUM(FKBTR) AS rev
FROM fmifiit_full WHERE WRTTP='66' AND FONDS IS NOT NULL
GROUP BY BUKRS, FONDS, FISTL, FIPEX;

CREATE INDEX tmp_consume_idx ON tmp_consume(BUKRS, FONDS, FISTL, FIPEX);
CREATE INDEX tmp_commit_idx  ON tmp_commit(BUKRS, FONDS, FISTL, FIPEX);
CREATE INDEX tmp_rev_idx     ON tmp_rev(BUKRS, FONDS, FISTL, FIPEX);
""")

print("=== INC-000005638 class detector: AVC FIPEX-level deficit signature ===")
print()

sql_top = """
WITH all_b AS (
  SELECT BUKRS, FONDS, FISTL, FIPEX FROM tmp_consume
  UNION
  SELECT BUKRS, FONDS, FISTL, FIPEX FROM tmp_commit
  UNION
  SELECT BUKRS, FONDS, FISTL, FIPEX FROM tmp_rev
),
joined AS (
  SELECT a.BUKRS, a.FONDS, a.FISTL, a.FIPEX,
         COALESCE(c.used,0) AS used,
         COALESCE(co.comm,0) AS comm,
         COALESCE(r.rev,0)   AS rev
  FROM all_b a
  LEFT JOIN tmp_consume c
    ON c.BUKRS=a.BUKRS AND c.FONDS=a.FONDS AND c.FISTL=a.FISTL AND c.FIPEX=a.FIPEX
  LEFT JOIN tmp_commit co
    ON co.BUKRS=a.BUKRS AND co.FONDS=a.FONDS AND co.FISTL=a.FISTL AND co.FIPEX=a.FIPEX
  LEFT JOIN tmp_rev r
    ON r.BUKRS=a.BUKRS AND r.FONDS=a.FONDS AND r.FISTL=a.FISTL AND r.FIPEX=a.FIPEX
)
SELECT FONDS, FISTL,
       SUM(CASE WHEN FIPEX != 'REVENUE' AND (used+comm) > rev + 1000
                THEN 1 ELSE 0 END) AS deficit_fipex,
       SUM(CASE WHEN FIPEX = 'REVENUE' THEN rev ELSE 0 END) AS rev_in_placeholder,
       SUM(CASE WHEN FIPEX != 'REVENUE' THEN (used+comm-rev) ELSE 0 END) AS sum_op_deficit_usd
FROM joined
GROUP BY FONDS, FISTL
HAVING deficit_fipex >= 2 AND rev_in_placeholder > 1000
ORDER BY sum_op_deficit_usd DESC
LIMIT 30
"""
cur.execute(sql_top)
print(f'{"FUND":<14} {"FUNDSCTR":<10} {"#deficit_FIPEX":>15} {"REV_pool_USD":>16} {"Op_Deficit_USD":>18}')
print('-'*80)
n=0
for r in cur.fetchall():
    n+=1
    print(f'{r[0]:<14} {r[1]:<10} {r[2]:>15} {r[3]:>16,.2f} {r[4]:>18,.2f}')
print(f'\n(Top {n} shown)')

# Summary count
sql_count = """
WITH all_b AS (
  SELECT BUKRS, FONDS, FISTL, FIPEX FROM tmp_consume
  UNION
  SELECT BUKRS, FONDS, FISTL, FIPEX FROM tmp_commit
  UNION
  SELECT BUKRS, FONDS, FISTL, FIPEX FROM tmp_rev
),
joined AS (
  SELECT a.BUKRS, a.FONDS, a.FISTL, a.FIPEX,
         COALESCE(c.used,0) AS used,
         COALESCE(co.comm,0) AS comm,
         COALESCE(r.rev,0)   AS rev
  FROM all_b a
  LEFT JOIN tmp_consume c
    ON c.BUKRS=a.BUKRS AND c.FONDS=a.FONDS AND c.FISTL=a.FISTL AND c.FIPEX=a.FIPEX
  LEFT JOIN tmp_commit co
    ON co.BUKRS=a.BUKRS AND co.FONDS=a.FONDS AND co.FISTL=a.FISTL AND co.FIPEX=a.FIPEX
  LEFT JOIN tmp_rev r
    ON r.BUKRS=a.BUKRS AND r.FONDS=a.FONDS AND r.FISTL=a.FISTL AND r.FIPEX=a.FIPEX
),
flag AS (
  SELECT FONDS, FISTL,
         SUM(CASE WHEN FIPEX != 'REVENUE' AND (used+comm) > rev + 1000
                  THEN 1 ELSE 0 END) AS deficit_fipex,
         SUM(CASE WHEN FIPEX = 'REVENUE' THEN rev ELSE 0 END) AS rev_in_placeholder,
         SUM(CASE WHEN FIPEX != 'REVENUE' THEN (used+comm-rev) ELSE 0 END) AS sum_op_deficit
  FROM joined
  GROUP BY FONDS, FISTL
)
SELECT
  COUNT(*) AS total_buckets,
  SUM(CASE WHEN deficit_fipex >= 2 AND rev_in_placeholder > 1000 THEN 1 ELSE 0 END) AS at_risk_buckets,
  SUM(CASE WHEN deficit_fipex >= 2 AND rev_in_placeholder > 1000 THEN sum_op_deficit ELSE 0 END) AS total_deficit_usd
FROM flag
"""
cur.execute(sql_count)
r = cur.fetchone()
print(f'\nTotal (FUND, FISTL) buckets in P01:    {r[0]:,}')
print(f'AT-RISK buckets (deficit class match): {r[1]:,}')
print(f'Aggregate operational deficit (USD):   {r[2]:,.2f}')
