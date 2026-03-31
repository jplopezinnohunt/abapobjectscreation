"""Payment & BCM E2E Deep Analysis — 2024-2026"""
import sys, io, sqlite3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"
db = sqlite3.connect(DB)

def p(label, rows, fmt="  {0}"):
    print(f"\n{'='*60}\n{label}\n{'='*60}")
    for r in rows: print(fmt.format(*r))

# 11. UNES_AP_10 same-user
p("11. UNES_AP_10 SAME-USER (biggest SoD gap)", db.execute('''
    SELECT CRUSR, COUNT(*) cnt, ROUND(SUM(CAST(BATCH_SUM AS REAL)),2) amt,
           MIN(CRDATE) first_d, MAX(CRDATE) last_d
    FROM BNK_BATCH_HEADER
    WHERE CRDATE >= '20240101' AND RULE_ID = 'UNES_AP_10' AND CRUSR = CHUSR
      AND CUR_STS IN ('IBC15','IBC11')
    GROUP BY CRUSR ORDER BY cnt DESC
''').fetchall(), "  {0:>15}: {1:>5} batches | amt={2:>15,.2f} | {3}-{4}")

# 12. UNES_AP_EX same-user
p("12. UNES_AP_EX SAME-USER (exception countries)", db.execute('''
    SELECT CRUSR, COUNT(*) cnt, ROUND(SUM(CAST(BATCH_SUM AS REAL)),2) amt,
           MIN(CRDATE) first_d, MAX(CRDATE) last_d
    FROM BNK_BATCH_HEADER
    WHERE CRDATE >= '20240101' AND RULE_ID = 'UNES_AP_EX' AND CRUSR = CHUSR
      AND CUR_STS IN ('IBC15','IBC11','IBC05')
    GROUP BY CRUSR ORDER BY cnt DESC
''').fetchall(), "  {0:>15}: {1:>5} batches | amt={2:>15,.2f} | {3}-{4}")

# 13. F110 daily frequency
print(f"\n{'='*60}\n13. F110 DAILY RUN FREQUENCY\n{'='*60}")
rows = db.execute('''
    SELECT LAUFD, COUNT(DISTINCT LAUFI) runs, COUNT(*) items
    FROM REGUH WHERE LAUFD >= '20240101' AND XVORL != 'X'
    GROUP BY LAUFD ORDER BY runs DESC LIMIT 10
''').fetchall()
print("  Top 10 busiest days:")
for r in rows:
    print(f"    {r[0]}: {r[1]:>3} runs, {r[2]:>5} items")
avg = db.execute('''
    SELECT AVG(run_cnt) FROM (
        SELECT LAUFD, COUNT(DISTINCT LAUFI) run_cnt
        FROM REGUH WHERE LAUFD >= '20240101' AND XVORL != 'X' GROUP BY LAUFD)
''').fetchone()[0]
print(f"  Average: {avg:.1f} runs/day")

# 14. IIEP approval delays
print(f"\n{'='*60}\n14. IIEP_AP_ST APPROVAL DELAYS\n{'='*60}")
rows = db.execute('''
    SELECT CRUSR, CHUSR, COUNT(*) cnt
    FROM BNK_BATCH_HEADER
    WHERE CRDATE >= '20240101' AND RULE_ID = 'IIEP_AP_ST' AND CRUSR != CHUSR
      AND CUR_STS IN ('IBC15','IBC11')
    GROUP BY CRUSR, CHUSR ORDER BY cnt DESC LIMIT 10
''').fetchall()
for r in rows:
    print(f"  {r[0]:>15} -> {r[1]:>15}: {r[2]:>4} batches")
# Longest delays
rows = db.execute('''
    SELECT CRDATE, CHDATE, BATCH_NO, BATCH_SUM, CRUSR, CHUSR
    FROM BNK_BATCH_HEADER
    WHERE CRDATE >= '20240101' AND RULE_ID = 'IIEP_AP_ST' AND CRUSR != CHUSR
      AND CUR_STS = 'IBC15'
    ORDER BY CAST(CHDATE AS INT) - CAST(CRDATE AS INT) DESC LIMIT 5
''').fetchall()
print("  Longest delays:")
for r in rows:
    diff = int(r[1]) - int(r[0])
    print(f"    Created {r[0]}, Approved {r[1]} ({diff} diff), Batch {r[2]}, amt={float(r[3]):,.2f}, {r[4]}->{r[5]}")

# 15. Stream distribution by month
print(f"\n{'='*60}\n15. CLEARING STREAMS BY MONTH\n{'='*60}")
rows = db.execute('''
    SELECT SUBSTR(a.AUGDT,1,6) ym,
           SUM(CASE WHEN b.BLART = 'ZP' THEN 1 ELSE 0 END) zp,
           SUM(CASE WHEN b.BLART = 'OP' AND a.HKONT LIKE '00020210%' THEN 1 ELSE 0 END) op_field,
           SUM(CASE WHEN b.BLART = 'AB' THEN 1 ELSE 0 END) ab,
           SUM(CASE WHEN b.BLART = 'OP' AND a.HKONT NOT LIKE '00020210%' THEN 1 ELSE 0 END) op_other,
           SUM(CASE WHEN b.BLART NOT IN ('ZP','OP','AB') THEN 1 ELSE 0 END) others
    FROM bsak a
    JOIN bkpf b ON a.BUKRS = b.BUKRS AND a.AUGBL = b.BELNR AND a.GJAHR = b.GJAHR
    WHERE a.AUGDT >= '20240101' AND a.AUGDT < '20270101'
    GROUP BY SUBSTR(a.AUGDT,1,6) ORDER BY ym
''').fetchall()
print(f"  {'Month':>8} {'ZP(BCM)':>8} {'OP(Field)':>10} {'AB(Net)':>8} {'OP(Oth)':>8} {'Others':>8}")
for r in rows:
    print(f"  {r[0]:>8} {r[1]:>8,} {r[2]:>10,} {r[3]:>8,} {r[4]:>8,} {r[5]:>8,}")

# 16. BCM batch size distribution
print(f"\n{'='*60}\n16. BCM BATCH SIZE DISTRIBUTION (2024-2026)\n{'='*60}")
rows = db.execute('''
    SELECT
        CASE
            WHEN CAST(ITEM_CNT AS INT) = 1 THEN '1 item'
            WHEN CAST(ITEM_CNT AS INT) <= 5 THEN '2-5 items'
            WHEN CAST(ITEM_CNT AS INT) <= 20 THEN '6-20 items'
            WHEN CAST(ITEM_CNT AS INT) <= 100 THEN '21-100 items'
            WHEN CAST(ITEM_CNT AS INT) <= 500 THEN '101-500 items'
            ELSE '500+ items'
        END bucket,
        COUNT(*) cnt,
        ROUND(SUM(CAST(BATCH_SUM AS REAL)),2) amt
    FROM BNK_BATCH_HEADER
    WHERE CRDATE >= '20240101' AND CUR_STS IN ('IBC15','IBC11')
    GROUP BY bucket ORDER BY MIN(CAST(ITEM_CNT AS INT))
''').fetchall()
for r in rows:
    print(f"  {r[0]:>15}: {r[1]:>5} batches | amt={r[2]:>15,.2f}")

# 17. Payment to clearing same-day rate
print(f"\n{'='*60}\n17. SAME-DAY PAYMENT->CLEARING RATE\n{'='*60}")
rows = db.execute('''
    SELECT
        CASE WHEN a.AUGDT = b.BUDAT THEN 'Same day'
             WHEN CAST(a.AUGDT AS INT) - CAST(b.BUDAT AS INT) <= 1 THEN 'Next day'
             WHEN CAST(a.AUGDT AS INT) - CAST(b.BUDAT AS INT) <= 7 THEN '2-7 days'
             ELSE '7+ days' END bucket,
        COUNT(*) cnt
    FROM bsak a
    JOIN bkpf b ON a.BUKRS = b.BUKRS AND a.AUGBL = b.BELNR AND a.GJAHR = b.GJAHR
    WHERE a.BUDAT >= '20240101' AND b.BLART = 'ZP'
    GROUP BY bucket
''').fetchall()
for r in rows:
    print(f"  {r[0]:>15}: {r[1]:>8,}")

db.close()
print("\n  Analysis complete.")
