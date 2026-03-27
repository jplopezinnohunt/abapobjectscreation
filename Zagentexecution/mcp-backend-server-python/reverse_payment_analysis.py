"""
reverse_payment_analysis.py - v2
Proper cross-company payment reverse engineering.
BELNR is NOT unique across BUKRS — must anchor joins to paying company.
"""
import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB = 'Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db'
db = sqlite3.connect(DB)

# ── 1. T042 configuration: who is configured to pay for whom?
print('=== 1. T042 CONFIG: BUKRS vs ZBUKR (cross-company config) ===')
rows = db.execute('SELECT BUKRS, ZBUKR FROM T042 ORDER BY BUKRS').fetchall()
for r in rows:
    cross = ' *** PAYS VIA ANOTHER ***' if r[0] != r[1] else ' (self-pay)'
    print(f'  {r[0]} -> paying company: {r[1]}{cross}')

# ── 2. Who runs F110 for whom (REGUH)?
# ZBUKR = who runs the F110 run (the paying entity)
# LIFNR = vendor being paid — but we need to find which BUKRS the invoice is in
print('\n=== 2. REGUH: F110 runs by paying company ===')
for r in db.execute("""
    SELECT ZBUKR, COUNT(DISTINCT LAUFD||LAUFI) as runs, COUNT(*) as items,
           SUM(CASE WHEN XVORL='X' THEN 1 ELSE 0 END) as prop,
           COUNT(DISTINCT HBKID) as banks, COUNT(DISTINCT LIFNR) as vendors
    FROM REGUH GROUP BY ZBUKR ORDER BY items DESC
""").fetchall():
    print(f"  {r[0]}: {r[1]} runs | {r[2]:,} items (prop={r[3]:,}) | {r[4]} banks | {r[5]:,} vendors")

# ── 3. Proper cross-company: anchor on ZP docs per paying company
# For each paying company, find which invoice companies they cleared
print('\n=== 3. CROSS-COMPANY REALITY: ZP doc (pay_BUKRS) clears invoice in (inv_BUKRS) ===')
print('   Anchoring on paying company ZP docs to avoid BELNR collision...')

# Get all ZP payment docs per paying company
pay_companies = ['UNES', 'UBO', 'ICTP', 'IIEP', 'UIL', 'UIS']

total_cross = 0
total_self = 0
matrix = {}  # (pay_bukrs, inv_bukrs) -> count

for pay_co in pay_companies:
    # BSAK where the clearing doc (AUGBL) is a ZP/KZ in THIS specific company
    # Join: BSAK.AUGBL = BKPF.BELNR AND BKPF.BUKRS = pay_co (anchored!) AND BKPF.BLART IN ZP/KZ
    q = """
    SELECT s.BUKRS as inv_bukrs, COUNT(*) as cnt,
           ROUND(SUM(CAST(s.WRBTR AS REAL)),0) as total_amt
    FROM bsak s
    JOIN bkpf p ON p.BELNR = s.AUGBL
                AND p.GJAHR = s.GJAHR
                AND p.BUKRS = ?
                AND p.BLART IN ('ZP','KZ','KG','ZV')
    GROUP BY s.BUKRS
    ORDER BY cnt DESC
    """
    results = db.execute(q, (pay_co,)).fetchall()
    if results:
        print(f"\n  {pay_co} pays for:")
        for r in results:
            inv_co = r[0]
            cnt = r[1]
            amt = r[2]
            cross = '*** CROSS ***' if inv_co != pay_co else '(self)'
            print(f"    -> Invoice in {inv_co}: {cnt:,} cleared items | amt={amt:,.0f}  {cross}")
            matrix[(pay_co, inv_co)] = cnt
            if inv_co != pay_co:
                total_cross += cnt
            else:
                total_self += cnt

print(f'\n  TOTAL self-pay cleared: {total_self:,}')
print(f'  TOTAL cross-company cleared: {total_cross:,}')

# ── 4. Payment Matrix Summary
print('\n=== 4. PAYMENT MATRIX (rows=payer, cols=invoice company) ===')
all_cos = sorted(set([k[0] for k in matrix] + [k[1] for k in matrix]))
header = f"{'PAYER':6} | " + " | ".join(f"{c:6}" for c in all_cos)
print(f"  {header}")
print("  " + "-" * len(header))
for pay in pay_companies:
    row = f"  {pay:6} | "
    for inv in all_cos:
        val = matrix.get((pay, inv), 0)
        if val == 0:
            row += f"{'—':6} | "
        elif pay == inv:
            row += f"{'S':>4}{val//1000:>2}K | "
        else:
            row += f"{'X':>4}{val//1000:>2}K | "
    print(row)

print("  S = self-pay, X = cross-company")

# ── 5. IBE, MGIE, ICBA: their invoices — who clears them?
print('\n=== 5. IBE/MGIE/ICBA: They cant run F110 — who clears their invoices? ===')
for no_f110 in ['IBE', 'MGIE', 'ICBA']:
    q = """
    SELECT p.BUKRS as cleared_by, p.BLART, COUNT(*) as cnt
    FROM bsak s
    JOIN bkpf p ON p.BELNR = s.AUGBL AND p.GJAHR = s.GJAHR
    WHERE s.BUKRS = ?
    GROUP BY p.BUKRS, p.BLART ORDER BY cnt DESC
    """
    results = db.execute(q, (no_f110,)).fetchall()
    if results:
        print(f"\n  {no_f110} invoices cleared by:")
        for r in results:
            print(f"    {r[1]} in {r[0]}: {r[2]:,} docs")
    else:
        print(f"\n  {no_f110}: no clearing found in BSAK")

# ── 6. How many invoices are OPEN (never cleared) per company?
print('\n=== 6. OPEN INVOICES (BSIK = never cleared) ===')
for r in db.execute("""
    SELECT BUKRS, COUNT(*) as open_items, COUNT(DISTINCT LIFNR) as vendors
    FROM bsik GROUP BY BUKRS ORDER BY open_items DESC
""").fetchall():
    print(f"  {r[0]}: {r[1]:,} open items | {r[2]:,} vendors")

# ── 7. BCM vs direct payment: does BCM only cover some payments?
print('\n=== 7. BCM COVERAGE: BCM items vs ZP docs per company ===')
bcm = {r[0]: r[1] for r in db.execute(
    "SELECT ZBUKR, SUM(CAST(ITEM_CNT AS INT)) FROM BNK_BATCH_HEADER GROUP BY ZBUKR"
).fetchall()}
zp = {r[0]: r[1] for r in db.execute(
    "SELECT BUKRS, COUNT(*) FROM bkpf WHERE BLART IN ('ZP','KZ') GROUP BY BUKRS"
).fetchall()}

for co in sorted(set(list(bcm.keys()) + list(zp.keys()))):
    b = bcm.get(co, 0)
    z = zp.get(co, 0)
    pct = (b/z*100) if z > 0 else 0
    print(f"  {co}: BCM={b:,} items | ZP docs={z:,} | coverage={pct:.0f}%")

db.close()
