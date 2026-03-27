"""
central_payment_analysis.py
Understand UNESCO central payment reality:
- Who really pays for whom?
- F110 run ID patterns (B* = BCM, others = direct)
- Vendor sharing across company codes
- UNES field office payments
"""
import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB = 'Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db'
db = sqlite3.connect(DB)

# ── 1. F110 run ID (LAUFI) patterns — B* = BCM routing
print('=== 1. F110 RUN ID PATTERNS (LAUFI prefix reveals payment type) ===')
for r in db.execute("""
    SELECT ZBUKR, SUBSTR(LAUFI,1,1) as prefix,
           COUNT(DISTINCT LAUFD||LAUFI) as runs,
           COUNT(*) as items,
           SUM(CASE WHEN XVORL='X' THEN 1 ELSE 0 END) as proposals
    FROM REGUH
    GROUP BY ZBUKR, SUBSTR(LAUFI,1,1)
    ORDER BY ZBUKR, runs DESC
""").fetchall():
    bcm_flag = ' [BCM]' if r[1] == 'B' else ' [PAYROLL?]' if r[1] in ('P','Y') else ' [DIRECT]'
    print(f"  {r[0]} prefix='{r[1]}'{bcm_flag}: {r[2]} runs | {r[3]:,} items | prop={r[4]:,}")

# ── 2. REGUH HBKID = '' — who are the invisible payments?
print('\n=== 2. REGUH: Items with EMPTY house bank (no bank routing) ===')
for r in db.execute("""
    SELECT ZBUKR, COUNT(*) as cnt,
           SUM(CASE WHEN XVORL='X' THEN 1 ELSE 0 END) as proposals
    FROM REGUH WHERE HBKID IS NULL OR HBKID = ''
    GROUP BY ZBUKR ORDER BY cnt DESC
""").fetchall():
    print(f"  {r[0]}: {r[1]:,} items (proposals={r[2]:,})")

# ── 3. UNES vendor analysis: unique vs shared vendors
print('\n=== 3. VENDOR SHARING: which vendors appear in MULTIPLE company codes ===')
# Vendors that appear in REGUH for MORE than one ZBUKR
for r in db.execute("""
    SELECT LIFNR, COUNT(DISTINCT ZBUKR) as cos, GROUP_CONCAT(DISTINCT ZBUKR) as codes,
           COUNT(*) as total_items
    FROM REGUH
    GROUP BY LIFNR HAVING COUNT(DISTINCT ZBUKR) > 1
    ORDER BY cos DESC, total_items DESC LIMIT 20
""").fetchall():
    print(f"  Vendor {r[0]}: {r[1]} companies ({r[2]}) | {r[3]:,} items")

# ── 4. UNES-exclusive vendors (only UNES ever pays them)
print('\n=== 4. UNES-EXCLUSIVE VENDORS (only UNES pays them) ===')
r = db.execute("""
    SELECT COUNT(DISTINCT LIFNR) FROM REGUH
    WHERE LIFNR NOT IN (SELECT LIFNR FROM REGUH WHERE ZBUKR != 'UNES')
    AND ZBUKR = 'UNES'
""").fetchone()
print(f"  UNES-exclusive vendors: {r[0]:,}")

# Also count shared vendors
r2 = db.execute("""
    SELECT COUNT(DISTINCT LIFNR) FROM REGUH
    WHERE LIFNR IN (SELECT LIFNR FROM REGUH WHERE ZBUKR != 'UNES')
    AND ZBUKR = 'UNES'
""").fetchone()
print(f"  UNES vendors also paid by other companies: {r2[0]:,}")

# ── 5. UNES house banks by country — maps to field offices
print('\n=== 5. UNES HOUSE BANKS BY COUNTRY (= field office network) ===')
for r in db.execute("""
    SELECT k.WAERS as currency, h.BANKS as country, COUNT(DISTINCT k.HBKID) as banks,
           COUNT(DISTINCT k.HKTID) as accounts
    FROM T012K k
    JOIN T012 h ON h.HBKID = k.HBKID AND h.BUKRS = k.BUKRS
    WHERE k.BUKRS = 'UNES'
    GROUP BY h.BANKS, k.WAERS
    ORDER BY accounts DESC LIMIT 25
""").fetchall():
    print(f"  {r[1]} {r[0]}: {r[2]} banks | {r[3]} accounts")

# ── 6. Which company codes share vendors with UNES field offices?
print('\n=== 6. DO OTHER INSTITUTES USE UNES BANKS? (T012 bank sharing) ===')
# House banks used by BOTH UNES and another company
for r in db.execute("""
    SELECT k1.BUKRS as other_co, COUNT(DISTINCT k1.HBKID) as shared_banks
    FROM T012K k1
    JOIN T012K k2 ON k2.HBKID = k1.HBKID AND k2.BUKRS = 'UNES'
    WHERE k1.BUKRS != 'UNES'
    GROUP BY k1.BUKRS ORDER BY shared_banks DESC
""").fetchall():
    print(f"  {r[0]} shares {r[1]} house banks with UNES")

# ── 7. BCM BATCH ITEMS: link VBLNR to find actual ZP docs
print('\n=== 7. BCM BATCH ITEM VBLNR patterns ===')
# VBLNR in BNK_BATCH_ITEM = the payment document reference
cols = [r[1] for r in db.execute('PRAGMA table_info(BNK_BATCH_ITEM)').fetchall()]
print('  BNK_BATCH_ITEM columns:', cols)

# Sample VBLNR format
for r in db.execute("""
    SELECT ZBUKR, SUBSTR(VBLNR,1,4) as prefix, COUNT(*) as cnt
    FROM BNK_BATCH_ITEM GROUP BY ZBUKR, SUBSTR(VBLNR,1,4)
    ORDER BY cnt DESC LIMIT 15
""").fetchall():
    print(f"  {r[0]} VBLNR prefix '{r[1]}': {r[2]:,}")

# ── 8. IBE/MGIE/ICBA invoice clearing doc types
print('\n=== 8. IBE/MGIE/ICBA: How are their invoices actually cleared? ===')
for co in ['IBE', 'MGIE', 'ICBA']:
    # Find AUGBL in BSAK and check what doc type it is in BKPF for SAME BUKRS
    r = db.execute(f"""
        SELECT p.BLART, p.BUKRS as pay_co, COUNT(*) as cnt
        FROM bsak s
        JOIN bkpf p ON p.BELNR = s.AUGBL AND p.GJAHR = s.GJAHR AND p.BUKRS = s.BUKRS
        WHERE s.BUKRS = '{co}'
        GROUP BY p.BLART, p.BUKRS ORDER BY cnt DESC
    """).fetchall()
    # Also check cleared by different company
    r2 = db.execute(f"""
        SELECT COUNT(*) as open FROM bsik WHERE BUKRS = '{co}'
    """).fetchone()
    print(f"\n  {co} own BKPF clearing docs: {r if r else 'NONE'}")
    print(f"  {co} still open in BSIK: {r2[0]:,}")

    # Total invoices vs cleared
    inv = db.execute(f"SELECT COUNT(*) FROM bkpf WHERE BUKRS='{co}' AND BLART IN ('KR','RE','KG')").fetchone()[0]
    clrd = db.execute(f"SELECT COUNT(*) FROM bsak WHERE BUKRS='{co}'").fetchone()[0]
    print(f"  {co}: {inv:,} invoices posted, {clrd:,} in BSAK (cleared)")

db.close()
