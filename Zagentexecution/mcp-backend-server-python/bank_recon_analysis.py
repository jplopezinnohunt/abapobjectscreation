"""Bank Statement & Reconciliation Deep Analysis — 2024-2026"""
import sys, io, sqlite3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"
db = sqlite3.connect(DB)

print("=" * 70)
print("BANK STATEMENT & RECONCILIATION ANALYSIS - UNESCO SAP (2024-2026)")
print("=" * 70)

# 1. Bank account landscape
print("\n1. BANK ACCOUNT LANDSCAPE")
banks = db.execute("SELECT COUNT(DISTINCT HBKID) FROM T012K WHERE BUKRS='UNES'").fetchone()[0]
accounts = db.execute("SELECT COUNT(*) FROM T012K WHERE BUKRS='UNES'").fetchone()[0]
currencies = db.execute("SELECT COUNT(DISTINCT WAERS) FROM T012K WHERE BUKRS='UNES'").fetchone()[0]
print(f"   UNES: {banks} house banks, {accounts} accounts, {currencies} currencies")

all_banks = db.execute("SELECT COUNT(DISTINCT BUKRS||HBKID) FROM T012K").fetchone()[0]
all_accts = db.execute("SELECT COUNT(*) FROM T012K").fetchone()[0]
print(f"   All co codes: {all_banks} bank+co combos, {all_accts} total accounts")

# Top banks by account count
print("\n   Top house banks (UNES) by account count:")
rows = db.execute("""
    SELECT k.HBKID, COUNT(*) accts, GROUP_CONCAT(DISTINCT k.WAERS) ccys, t.NAME1
    FROM T012K k LEFT JOIN T012 t ON k.BUKRS=t.BUKRS AND k.HBKID=t.HBKID
    WHERE k.BUKRS='UNES' GROUP BY k.HBKID ORDER BY accts DESC LIMIT 15
""").fetchall()
for r in rows:
    print(f"   {r[0]:>6}: {r[1]:>3} accounts | {r[2][:40]:40} | {(r[3] or '')[:30]}")

# 2. Bank statement document types
print("\n2. BANK STATEMENT DOCUMENT TYPES (2024-2026)")
z_types = {
    'Z1': 'Bank statement posting (GL reconciliation)',
    'Z2': 'Bank statement - memo/adjustment',
    'Z3': 'Bank statement - reference document',
    'Z5': 'Cash journal entries (FBCJ)',
    'Z6': 'Bank statement reversal',
    'Z7': 'Bank statement clearing (FB05)',
}
for blart, desc in z_types.items():
    cnt = db.execute(f"SELECT COUNT(*) FROM bkpf WHERE BLART='{blart}' AND BUDAT >= '20240101'").fetchone()[0]
    if cnt > 0:
        print(f"   BLART={blart}: {cnt:>8,} | {desc}")
total_bs = sum(db.execute(f"SELECT COUNT(*) FROM bkpf WHERE BLART='{b}' AND BUDAT >= '20240101'").fetchone()[0] for b in z_types)
print(f"   TOTAL: {total_bs:>8,} bank statement documents")

# 3. Bank GL open items (unreconciled)
print("\n3. BANK GL OPEN ITEMS (BSIS - unreconciled)")
rows = db.execute("""
    SELECT SUBSTR(s.HKONT,5,7) gl, COUNT(*) cnt, ROUND(SUM(CAST(s.DMBTR AS REAL)),2) amt,
           s.WAERS, k.HBKID, k.HKTID
    FROM bsis s
    LEFT JOIN T012K k ON s.BUKRS=k.BUKRS AND s.HKONT=k.HKONT
    WHERE s.HKONT LIKE '0001%' AND s.BUKRS='UNES'
    GROUP BY s.HKONT ORDER BY cnt DESC LIMIT 20
""").fetchall()
print(f"   {'GL':>10} {'Bank':>6} {'AcctID':>6} {'Open Items':>10} {'Amount':>18} {'CCY':>4}")
for r in rows:
    print(f"   {r[0]:>10} {(r[4] or ''):>6} {(r[5] or ''):>6} {r[1]:>10,} {r[2]:>18,.2f} {r[3] or '':>4}")

total_open = db.execute("SELECT COUNT(*), ROUND(SUM(CAST(DMBTR AS REAL)),2) FROM bsis WHERE HKONT LIKE '0001%' AND BUKRS='UNES'").fetchone()
print(f"   {'TOTAL':>10} {'':>6} {'':>6} {total_open[0]:>10,} {total_open[1]:>18,.2f}")

# 4. Bank GL cleared items volume
print("\n4. BANK GL CLEARED ITEMS (BSAS - reconciled)")
cleared = db.execute("SELECT COUNT(*), ROUND(SUM(CAST(DMBTR AS REAL)),2) FROM bsas WHERE HKONT LIKE '0001%' AND BUKRS='UNES'").fetchone()
print(f"   Total cleared: {cleared[0]:,} items, amt={cleared[1]:,.2f}")

# 5. Monthly bank statement volume
print("\n5. MONTHLY BANK STATEMENT VOLUME")
rows = db.execute("""
    SELECT SUBSTR(BUDAT,1,6) ym,
           SUM(CASE WHEN BLART='Z1' THEN 1 ELSE 0 END) z1,
           SUM(CASE WHEN BLART='Z5' THEN 1 ELSE 0 END) z5,
           SUM(CASE WHEN BLART='Z7' THEN 1 ELSE 0 END) z7,
           SUM(CASE WHEN BLART IN ('Z2','Z3','Z6') THEN 1 ELSE 0 END) other_z,
           COUNT(*) total
    FROM bkpf WHERE BLART IN ('Z1','Z2','Z3','Z5','Z6','Z7') AND BUDAT >= '20240101'
    GROUP BY SUBSTR(BUDAT,1,6) ORDER BY ym
""").fetchall()
print(f"   {'Month':>8} {'Z1(Post)':>9} {'Z5(Cash)':>9} {'Z7(Clear)':>9} {'Z2/3/6':>8} {'Total':>8}")
for r in rows:
    print(f"   {r[0]:>8} {r[1]:>9,} {r[2]:>9,} {r[3]:>9,} {r[4]:>8,} {r[5]:>8,}")

# 6. Clearing methods on bank GLs
print("\n6. CLEARING METHODS ON BANK GL ACCOUNTS")
rows = db.execute("""
    SELECT BLART, TCODE, COUNT(*) cnt
    FROM bkpf WHERE TCODE IN ('FB05','FEBAN','FF67','FF_5','F-04','F-28','F-53','FEB_BSPROC','FB01','FB08','FBCJ','FBR2')
      AND BUDAT >= '20240101'
    GROUP BY BLART, TCODE ORDER BY cnt DESC LIMIT 20
""").fetchall()
print(f"   {'DocType':>8} {'TCode':>12} {'Count':>8}")
for r in rows:
    print(f"   {r[0]:>8} {r[1]:>12} {r[2]:>8,}")

# 7. Open items aging
print("\n7. OPEN BANK ITEMS AGING (all co codes)")
rows = db.execute("""
    SELECT
        CASE
            WHEN BUDAT >= '20260301' THEN '0-30 days'
            WHEN BUDAT >= '20260101' THEN '1-3 months'
            WHEN BUDAT >= '20250701' THEN '3-9 months'
            WHEN BUDAT >= '20250101' THEN '9-15 months'
            ELSE '15+ months'
        END bucket,
        COUNT(*) cnt, ROUND(SUM(CAST(DMBTR AS REAL)),2) amt
    FROM bsis WHERE HKONT LIKE '0001%'
    GROUP BY bucket ORDER BY MIN(BUDAT) DESC
""").fetchall()
for r in rows:
    print(f"   {r[0]:>15}: {r[1]:>8,} items | amt={r[2]:>18,.2f}")

# 8. Bank statement users
print("\n8. BANK STATEMENT POSTING USERS (top 15)")
rows = db.execute("""
    SELECT USNAM, COUNT(*) cnt, GROUP_CONCAT(DISTINCT BLART) types
    FROM bkpf WHERE BLART IN ('Z1','Z2','Z3','Z5','Z6','Z7') AND BUDAT >= '20240101'
    GROUP BY USNAM ORDER BY cnt DESC LIMIT 15
""").fetchall()
for r in rows:
    print(f"   {r[0]:>15}: {r[1]:>8,} docs | types: {r[2]}")

# 9. Cash journal (Z5/FBCJ) analysis
print("\n9. CASH JOURNAL (Z5/FBCJ) BY COMPANY CODE")
rows = db.execute("""
    SELECT p.BUKRS, COUNT(*) cnt, ROUND(SUM(CAST(b.DMBTR AS REAL)),2) amt
    FROM bkpf p JOIN bsis b ON p.BUKRS=b.BUKRS AND p.BELNR=b.BELNR AND p.GJAHR=b.GJAHR
    WHERE p.BLART='Z5' AND p.BUDAT >= '20240101'
    GROUP BY p.BUKRS ORDER BY cnt DESC
""").fetchall()
for r in rows:
    print(f"   {r[0]}: {r[1]:>6,} entries | amt={r[2]:>15,.2f}")

# 10. Reconciliation efficiency: cleared vs open ratio by bank
print("\n10. RECONCILIATION RATE BY HOUSE BANK (top 15)")
rows = db.execute("""
    SELECT k.HBKID,
           SUM(CASE WHEN s.source='bsis' THEN 1 ELSE 0 END) open_cnt,
           SUM(CASE WHEN s.source='bsas' THEN 1 ELSE 0 END) cleared_cnt
    FROM (
        SELECT BUKRS, HKONT, 'bsis' as source FROM bsis WHERE HKONT LIKE '0001%' AND BUKRS='UNES'
        UNION ALL
        SELECT BUKRS, HKONT, 'bsas' as source FROM bsas WHERE HKONT LIKE '0001%' AND BUKRS='UNES'
    ) s
    JOIN T012K k ON s.BUKRS=k.BUKRS AND s.HKONT=k.HKONT
    GROUP BY k.HBKID
    HAVING (open_cnt + cleared_cnt) > 100
    ORDER BY open_cnt DESC LIMIT 15
""").fetchall()
print(f"   {'Bank':>6} {'Open':>8} {'Cleared':>8} {'Recon%':>8}")
for r in rows:
    total = r[1] + r[2]
    pct = 100 * r[2] / total if total > 0 else 0
    print(f"   {r[0]:>6} {r[1]:>8,} {r[2]:>8,} {pct:>7.1f}%")

# ═══════════════════════════════════════════════════════════════════════
# PROCESS DISCOVERY — Bank Statement Lifecycle from System Logs
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PROCESS DISCOVERY: BANK STATEMENT LIFECYCLE")
print("=" * 70)

# 11. Discover the REAL bank statement process from BKPF TCODE sequences
print("\n11. BANK STATEMENT PROCESS — TCODE ACTIVITY FLOW")
print("    (What transactions are used and in what order?)")

# Z1 = main bank statement posting. What TCODE creates them?
rows = db.execute("""
    SELECT TCODE, USNAM, COUNT(*) cnt, MIN(BUDAT) first_d, MAX(BUDAT) last_d
    FROM bkpf WHERE BLART='Z1' AND BUDAT >= '20240101'
    GROUP BY TCODE, USNAM ORDER BY cnt DESC LIMIT 15
""").fetchall()
print("\n    Z1 (Bank Statement) creation by TCODE + User:")
for r in rows:
    print(f"      {r[0] or '(blank)':>12} | {r[1]:>15} | {r[2]:>8,} docs | {r[3]}-{r[4]}")

# 12. Process discovery: what happens AFTER a bank statement is posted?
# Trace Z1 docs -> their clearing docs (AUGBL) -> what type are those?
print("\n12. BANK STATEMENT CLEARING CHAIN")
print("    (Z1 posted -> What clears it?)")
rows = db.execute("""
    SELECT p2.BLART clearing_type, p2.TCODE clearing_tcode, COUNT(*) cnt
    FROM bsas s
    JOIN bkpf p1 ON s.BUKRS=p1.BUKRS AND s.BELNR=p1.BELNR AND s.GJAHR=p1.GJAHR
    JOIN bkpf p2 ON s.BUKRS=p2.BUKRS AND s.AUGBL=p2.BELNR AND s.GJAHR=p2.GJAHR
    WHERE p1.BLART='Z1' AND s.HKONT LIKE '0001%' AND s.BUDAT >= '20240101'
    GROUP BY p2.BLART, p2.TCODE ORDER BY cnt DESC LIMIT 15
""").fetchall()
print(f"    {'Clearing Type':>15} {'TCode':>12} {'Count':>8}")
for r in rows:
    print(f"    {r[0]:>15} {r[1] or '(blank)':>12} {r[2]:>8,}")

# 13. Automated vs Manual bank statement processing
print("\n13. AUTOMATION LEVEL")
auto = db.execute("SELECT COUNT(*) FROM bkpf WHERE BLART='Z1' AND USNAM='JOBBATCH' AND BUDAT >= '20240101'").fetchone()[0]
manual = db.execute("SELECT COUNT(*) FROM bkpf WHERE BLART='Z1' AND USNAM != 'JOBBATCH' AND BUDAT >= '20240101'").fetchone()[0]
total_z1 = auto + manual
print(f"    Automated (JOBBATCH): {auto:>8,} ({100*auto/total_z1:.1f}%)")
print(f"    Manual (named users):  {manual:>8,} ({100*manual/total_z1:.1f}%)")

# 14. Bank statement -> Payment matching (the reconciliation)
# How many Z1 items match to ZP payments?
print("\n14. BANK STATEMENT -> PAYMENT MATCHING")
print("    (How well do bank statements link to payment documents?)")

# Z1 items in BSAS that clear to ZP docs
z1_clears_zp = db.execute("""
    SELECT COUNT(*)
    FROM bsas s
    JOIN bkpf p1 ON s.BUKRS=p1.BUKRS AND s.BELNR=p1.BELNR AND s.GJAHR=p1.GJAHR
    JOIN bkpf p2 ON s.BUKRS=p2.BUKRS AND s.AUGBL=p2.BELNR AND s.GJAHR=p2.GJAHR
    WHERE p1.BLART='Z1' AND p2.BLART='ZP' AND s.HKONT LIKE '0001%' AND s.BUDAT >= '20240101'
""").fetchone()[0]

z1_clears_ab = db.execute("""
    SELECT COUNT(*)
    FROM bsas s
    JOIN bkpf p1 ON s.BUKRS=p1.BUKRS AND s.BELNR=p1.BELNR AND s.GJAHR=p1.GJAHR
    JOIN bkpf p2 ON s.BUKRS=p2.BUKRS AND s.AUGBL=p2.BELNR AND s.GJAHR=p2.GJAHR
    WHERE p1.BLART='Z1' AND p2.BLART='AB' AND s.HKONT LIKE '0001%' AND s.BUDAT >= '20240101'
""").fetchone()[0]

z1_clears_z1 = db.execute("""
    SELECT COUNT(*)
    FROM bsas s
    JOIN bkpf p1 ON s.BUKRS=p1.BUKRS AND s.BELNR=p1.BELNR AND s.GJAHR=p1.GJAHR
    JOIN bkpf p2 ON s.BUKRS=p2.BUKRS AND s.AUGBL=p2.BELNR AND s.GJAHR=p2.GJAHR
    WHERE p1.BLART='Z1' AND p2.BLART='Z1' AND s.HKONT LIKE '0001%' AND s.BUDAT >= '20240101'
""").fetchone()[0]

z1_total_cleared = db.execute("""
    SELECT COUNT(*) FROM bsas s
    JOIN bkpf p1 ON s.BUKRS=p1.BUKRS AND s.BELNR=p1.BELNR AND s.GJAHR=p1.GJAHR
    WHERE p1.BLART='Z1' AND s.HKONT LIKE '0001%' AND s.BUDAT >= '20240101'
""").fetchone()[0]

print(f"    Z1 cleared by ZP (payment): {z1_clears_zp:>8,}")
print(f"    Z1 cleared by AB (netting): {z1_clears_ab:>8,}")
print(f"    Z1 cleared by Z1 (self):    {z1_clears_z1:>8,}")
print(f"    Z1 total cleared:           {z1_total_cleared:>8,}")

# 15. Discovered process flow
print("\n15. DISCOVERED BANK STATEMENT E2E PROCESS")
print("""
    INBOUND FLOW (Bank -> SAP):
    +-----------+     +----------------+     +-------------+     +------------+
    | SWIFT/SIL | --> | SAP EBS Import | --> | Auto-Post   | --> | Bank GL    |
    | Bank stmt |     | (JOBBATCH)     |     | (FB01/Z1)   |     | BSIS open  |
    +-----------+     +----------------+     +-------------+     +------------+
                                                                       |
    RECONCILIATION:                                                    v
    +------------------+     +-----------+     +------------+     +----------+
    | Manual Clearing  | --> | FB05/Z7   | --> | BSAS clrd  | --> | Matched  |
    | (L_NEVES etc.)   |     | (Z1->ZP)  |     | (bank+pay) |     | Recon OK |
    +------------------+     +-----------+     +------------+     +----------+

    OUTBOUND FLOW (SAP -> Bank):
    +----------+     +----------+     +-------+     +----------+     +-------+
    | F110 run | --> | BCM batch| --> | DMEE  | --> | SFTP/SIL | --> | SWIFT |
    | (ZP doc) |     | (approve)|     | (XML) |     | (15 min) |     | Bank  |
    +----------+     +----------+     +-------+     +----------+     +-------+
""")

# 16. Configuration validation
print("16. CONFIGURATION VALIDATION")
print("    T012K accounts with matching BSIS activity:")
active = db.execute("""
    SELECT COUNT(DISTINCT k.HBKID||k.HKTID)
    FROM T012K k
    JOIN bsis s ON k.BUKRS=s.BUKRS AND k.HKONT=s.HKONT
    WHERE k.BUKRS='UNES'
""").fetchone()[0]
total_accts = db.execute("SELECT COUNT(*) FROM T012K WHERE BUKRS='UNES'").fetchone()[0]
print(f"    Active accounts (have BSIS items): {active}/{total_accts}")

dormant = db.execute("""
    SELECT k.HBKID, k.HKTID, k.WAERS, k.HKONT
    FROM T012K k WHERE k.BUKRS='UNES'
    AND NOT EXISTS (SELECT 1 FROM bsis s WHERE s.BUKRS=k.BUKRS AND s.HKONT=k.HKONT)
    AND NOT EXISTS (SELECT 1 FROM bsas s WHERE s.BUKRS=k.BUKRS AND s.HKONT=k.HKONT)
    ORDER BY k.HBKID LIMIT 20
""").fetchall()
print(f"    Dormant accounts (no activity): {total_accts - active}")
if dormant:
    print("    Sample dormant:")
    for r in dormant[:10]:
        print(f"      {r[0]}/{r[1]} ({r[2]}) GL={r[3]}")

db.close()
print("\n   Analysis complete.")
