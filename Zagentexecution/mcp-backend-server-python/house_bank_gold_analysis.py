"""
house_bank_gold_analysis.py
============================
Analyze ALL house bank configurations from Gold DB.
Discover patterns across 200+ banks for the 13-step process.
"""
import sqlite3, os, sys, io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB = os.path.join(os.path.dirname(__file__), "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")

def q(conn, sql, params=None):
    try:
        return conn.execute(sql, params or []).fetchall()
    except Exception as e:
        return f"ERROR: {e}"

def cols(conn, table):
    r = q(conn, f"PRAGMA table_info({table})")
    if isinstance(r, str):
        return r
    return [row[1] for row in r]

conn = sqlite3.connect(DB)

# ── Step 0: What tables do we have? ──
print("="*70)
print("  GOLD DB — House Bank Related Tables")
print("="*70)

tables_to_check = [
    "T012", "T012K", "T012T", "BNKA", "TIBAN",
    "T030H", "T035D", "T028B", "T018V", "T042I",
    "SKA1", "SKB1", "SKAT",
    "FCLM_BSM_CUST", "FDSB",
    "T038", "T035",
    "SETLEAF",
]

# Also check _2024_2026 variants
all_tables = [r[0] for r in q(conn, "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]

for t in tables_to_check:
    found = [x for x in all_tables if x.upper().startswith(t.upper())]
    if found:
        for f in found:
            count = q(conn, f"SELECT COUNT(*) FROM [{f}]")
            c = count[0][0] if not isinstance(count, str) else "?"
            columns = cols(conn, f)
            col_list = columns if not isinstance(columns, str) else "?"
            print(f"  {f:30s} {c:>8} rows   cols: {col_list[:8]}...")
    else:
        print(f"  {t:30s} NOT IN GOLD DB")

print()

# ── Step 1: T012 — All house banks ──
print("="*70)
print("  STEP 2: T012 — All House Banks")
print("="*70)

t012_cols = cols(conn, "T012")
print(f"  Columns: {t012_cols}")

banks = q(conn, "SELECT * FROM T012 ORDER BY HBKID")
if not isinstance(banks, str):
    print(f"  Total house banks: {len(banks)}")
    # Get column indices
    ci = {c: i for i, c in enumerate(t012_cols)}
    for b in banks[:5]:
        print(f"    {b}")
    print(f"    ... showing first 5 of {len(banks)}")

    # Count by country
    if "BANKS" in ci:
        countries = q(conn, "SELECT BANKS, COUNT(*) as cnt FROM T012 GROUP BY BANKS ORDER BY cnt DESC")
        print(f"\n  Banks by country ({len(countries)} countries):")
        for c in countries[:20]:
            print(f"    {c[0]:5s}: {c[1]}")

# ── Step 2: T012K — All bank accounts ──
print(f"\n{'='*70}")
print("  STEP 2: T012K — All Bank Accounts")
print("="*70)

t012k_cols = cols(conn, "T012K")
print(f"  Columns: {t012k_cols}")

accounts = q(conn, "SELECT COUNT(*) FROM T012K")
print(f"  Total accounts: {accounts[0][0] if not isinstance(accounts, str) else '?'}")

# Accounts per bank
accts_per_bank = q(conn, """
    SELECT HBKID, COUNT(*) as cnt, GROUP_CONCAT(DISTINCT WAERS) as currencies
    FROM T012K WHERE BUKRS='UNES'
    GROUP BY HBKID ORDER BY cnt DESC
""")
if not isinstance(accts_per_bank, str):
    print(f"  Accounts per house bank (UNES):")
    for r in accts_per_bank[:20]:
        print(f"    {r[0]:10s}: {r[1]} accounts, currencies: {r[2]}")
    print(f"    ... {len(accts_per_bank)} banks total")

# Currency distribution
curr_dist = q(conn, """
    SELECT WAERS, COUNT(*) as cnt FROM T012K WHERE BUKRS='UNES'
    GROUP BY WAERS ORDER BY cnt DESC
""")
if not isinstance(curr_dist, str):
    print(f"\n  Currency distribution:")
    for r in curr_dist:
        print(f"    {r[0]:5s}: {r[1]} accounts")

# ── Step 3: SKB1 — G/L field patterns ──
print(f"\n{'='*70}")
print("  STEP 1/6: SKB1 — G/L Account Patterns")
print("="*70)

skb1_cols = cols(conn, "SKB1")
print(f"  Columns: {skb1_cols}")

# Check which fields we have
needed = ["SAKNR","FDLEV","ZUAWA","XKRES","XGKON","FIPOS","FSTAG","XOPVW","HBKID","HKTID","WAERS","XINTB"]
available = [f for f in needed if f in skb1_cols]
missing = [f for f in needed if f not in skb1_cols]
print(f"  Available fields: {available}")
print(f"  Missing fields: {missing}")

# Bank G/Ls: accounts where HBKID is set
if "HBKID" in skb1_cols:
    bank_gls = q(conn, """
        SELECT COUNT(*) FROM SKB1 WHERE BUKRS='UNES' AND HBKID IS NOT NULL AND HBKID != ''
    """)
    print(f"\n  G/L accounts with HBKID assigned: {bank_gls[0][0] if not isinstance(bank_gls, str) else '?'}")

    # FDLEV patterns
    if "FDLEV" in skb1_cols:
        fdlev = q(conn, """
            SELECT FDLEV, COUNT(*) FROM SKB1
            WHERE BUKRS='UNES' AND HBKID IS NOT NULL AND HBKID != ''
            GROUP BY FDLEV ORDER BY COUNT(*) DESC
        """)
        if not isinstance(fdlev, str):
            print(f"\n  FDLEV distribution (bank G/Ls):")
            for r in fdlev:
                print(f"    {r[0] or '(empty)':10s}: {r[1]}")

    # ZUAWA patterns
    if "ZUAWA" in skb1_cols:
        zuawa = q(conn, """
            SELECT ZUAWA, COUNT(*) FROM SKB1
            WHERE BUKRS='UNES' AND HBKID IS NOT NULL AND HBKID != ''
            GROUP BY ZUAWA ORDER BY COUNT(*) DESC
        """)
        if not isinstance(zuawa, str):
            print(f"\n  ZUAWA distribution:")
            for r in zuawa:
                print(f"    {r[0] or '(empty)':10s}: {r[1]}")

    # XOPVW patterns (should be X on sub-bank 11*, empty on bank 10*)
    if "XOPVW" in skb1_cols:
        xopvw = q(conn, """
            SELECT
                CASE WHEN SUBSTR(REPLACE(SAKNR,'0',''),1,2) = '10' THEN 'bank_10*'
                     WHEN SUBSTR(REPLACE(SAKNR,'0',''),1,2) = '11' THEN 'clearing_11*'
                     ELSE 'other' END as gl_type,
                XOPVW, COUNT(*)
            FROM SKB1 WHERE BUKRS='UNES' AND HBKID IS NOT NULL AND HBKID != ''
            GROUP BY gl_type, XOPVW ORDER BY gl_type, XOPVW
        """)
        if not isinstance(xopvw, str):
            print(f"\n  XOPVW by G/L type (Open Item Management):")
            for r in xopvw:
                print(f"    {r[0]:15s} XOPVW={r[1] or '(empty)':8s}: {r[2]}")

    # XINTB patterns
    if "XINTB" in skb1_cols:
        xintb = q(conn, """
            SELECT XINTB, COUNT(*) FROM SKB1
            WHERE BUKRS='UNES' AND HBKID IS NOT NULL AND HBKID != ''
            GROUP BY XINTB ORDER BY COUNT(*) DESC
        """)
        if not isinstance(xintb, str):
            print(f"\n  XINTB distribution (Post Automatically Only):")
            for r in xintb:
                print(f"    {r[0] or '(empty)':10s}: {r[1]}")

    # FSTAG patterns
    if "FSTAG" in skb1_cols:
        fstag = q(conn, """
            SELECT FSTAG, COUNT(*) FROM SKB1
            WHERE BUKRS='UNES' AND HBKID IS NOT NULL AND HBKID != ''
            GROUP BY FSTAG ORDER BY COUNT(*) DESC
        """)
        if not isinstance(fstag, str):
            print(f"\n  FSTAG distribution (Field Status Group):")
            for r in fstag:
                print(f"    {r[0] or '(empty)':10s}: {r[1]}")

    # KTOKS from SKA1
    if "SKA1" in all_tables:
        ska1_cols = cols(conn, "SKA1")
        if "KTOKS" in ska1_cols:
            ktoks = q(conn, """
                SELECT a.KTOKS, COUNT(*)
                FROM SKA1 a JOIN SKB1 b ON a.SAKNR = b.SAKNR
                WHERE b.BUKRS='UNES' AND b.HBKID IS NOT NULL AND b.HBKID != ''
                AND a.KTOPL='UNES'
                GROUP BY a.KTOKS ORDER BY COUNT(*) DESC
            """)
            if not isinstance(ktoks, str):
                print(f"\n  KTOKS distribution (Account Group):")
                for r in ktoks:
                    print(f"    {r[0] or '(empty)':10s}: {r[1]}")

# ── Step 4: T030H — OBA1 patterns ──
print(f"\n{'='*70}")
print("  STEP 4: T030H — OBA1 Exchange Rate Config")
print("="*70)

if "T030H" in all_tables:
    t030h_cols = cols(conn, "T030H")
    print(f"  Columns: {t030h_cols}")
    t030h_cnt = q(conn, "SELECT COUNT(*) FROM T030H")
    print(f"  Total entries: {t030h_cnt[0][0] if not isinstance(t030h_cnt, str) else '?'}")

    # Which fields are filled
    if all(f in t030h_cols for f in ["LKORR","LSREA","LHREA","LSBEW","LHBEW"]):
        completeness = q(conn, """
            SELECT
                CASE WHEN LKORR IS NOT NULL AND LKORR != '' AND LKORR != '0000000000' THEN 'Y' ELSE 'N' END as has_LKORR,
                CASE WHEN LSBEW IS NOT NULL AND LSBEW != '' AND LSBEW != '0000000000' THEN 'Y' ELSE 'N' END as has_LSBEW,
                CASE WHEN LHBEW IS NOT NULL AND LHBEW != '' AND LHBEW != '0000000000' THEN 'Y' ELSE 'N' END as has_LHBEW,
                COUNT(*)
            FROM T030H WHERE KTOPL='UNES'
            GROUP BY has_LKORR, has_LSBEW, has_LHBEW
            ORDER BY COUNT(*) DESC
        """)
        if not isinstance(completeness, str):
            print(f"\n  Field completeness (LKORR/LSBEW/LHBEW):")
            for r in completeness:
                print(f"    LKORR={r[0]} LSBEW={r[1]} LHBEW={r[2]}: {r[3]} entries")

        # LSREA/LHREA values
        loss_gain = q(conn, """
            SELECT LSREA, LHREA, COUNT(*) FROM T030H WHERE KTOPL='UNES'
            GROUP BY LSREA, LHREA ORDER BY COUNT(*) DESC LIMIT 10
        """)
        if not isinstance(loss_gain, str):
            print(f"\n  Loss/Gain account patterns:")
            for r in loss_gain:
                print(f"    Loss={r[0]} Gain={r[1]}: {r[2]} entries")
else:
    print("  T030H NOT IN GOLD DB")

# ── Step 5: T035D — EBS Config ──
print(f"\n{'='*70}")
print("  STEP 6: T035D — Electronic Bank Statement")
print("="*70)

if "T035D" in all_tables:
    t035d_cols = cols(conn, "T035D")
    print(f"  Columns: {t035d_cols}")
    cnt = q(conn, "SELECT COUNT(*) FROM T035D WHERE BUKRS='UNES'")
    print(f"  Entries (UNES): {cnt[0][0] if not isinstance(cnt, str) else '?'}")

    # DISKB naming patterns
    diskb = q(conn, "SELECT DISKB, BNKKO FROM T035D WHERE BUKRS='UNES' ORDER BY DISKB")
    if not isinstance(diskb, str):
        print(f"\n  DISKB patterns (first 20):")
        for r in diskb[:20]:
            print(f"    {r[0]:20s} -> GL {r[1]}")
        print(f"    ... {len(diskb)} total")
else:
    print("  T035D NOT IN GOLD DB")

# ── Step 6: T028B — Bank Statement Posting Rules ──
print(f"\n{'='*70}")
print("  STEP 6b: T028B — Bank Accts to Transaction Types")
print("="*70)

if "T028B" in all_tables:
    t028b_cols = cols(conn, "T028B")
    print(f"  Columns: {t028b_cols}")
    cnt = q(conn, "SELECT COUNT(*) FROM T028B")
    print(f"  Total entries: {cnt[0][0] if not isinstance(cnt, str) else '?'}")

    # Transaction type distribution
    if "VGTYP" in t028b_cols:
        vgtyp = q(conn, "SELECT VGTYP, COUNT(*) FROM T028B GROUP BY VGTYP ORDER BY COUNT(*) DESC")
        if not isinstance(vgtyp, str):
            print(f"\n  Transaction type distribution:")
            for r in vgtyp:
                print(f"    {r[0] or '(empty)':10s}: {r[1]}")
else:
    print("  T028B NOT IN GOLD DB")

# ── Step 7: T018V — Receiving Accounts ──
print(f"\n{'='*70}")
print("  STEP 8: T018V — Receiving Bank Clearing")
print("="*70)

if "T018V" in all_tables:
    t018v_cols = cols(conn, "T018V")
    print(f"  Columns: {t018v_cols}")
    cnt = q(conn, "SELECT COUNT(*) FROM T018V WHERE BUKRS='UNES'")
    print(f"  Entries (UNES): {cnt[0][0] if not isinstance(cnt, str) else '?'}")

    # Payment method distribution
    if "ZLSCH" in t018v_cols:
        zlsch = q(conn, "SELECT ZLSCH, COUNT(*) FROM T018V WHERE BUKRS='UNES' GROUP BY ZLSCH ORDER BY COUNT(*) DESC")
        if not isinstance(zlsch, str):
            print(f"\n  Payment method distribution:")
            for r in zlsch:
                print(f"    {r[0] or '(empty)':5s}: {r[1]}")

    # Banks with T018V
    if "HBKID" in t018v_cols:
        hbkids = q(conn, """
            SELECT HBKID, COUNT(*), GROUP_CONCAT(DISTINCT ZLSCH) as methods
            FROM T018V WHERE BUKRS='UNES'
            GROUP BY HBKID ORDER BY COUNT(*) DESC
        """)
        if not isinstance(hbkids, str):
            print(f"\n  Banks with receiving account config ({len(hbkids)}):")
            for r in hbkids[:20]:
                print(f"    {r[0]:10s}: {r[1]} entries, methods: {r[2]}")
else:
    print("  T018V NOT IN GOLD DB")

# ── Step 8: T042I — Payment Bank Determination ──
print(f"\n{'='*70}")
print("  STEP 9.1: T042I — Payment Bank Determination")
print("="*70)

if "T042I" in all_tables:
    t042i_cols = cols(conn, "T042I")
    print(f"  Columns: {t042i_cols}")
    cnt = q(conn, "SELECT COUNT(*) FROM T042I WHERE ZBUKR='UNES'")
    print(f"  Entries (UNES): {cnt[0][0] if not isinstance(cnt, str) else '?'}")

    # Banks with payment determination
    if "HBKID" in t042i_cols:
        paying = q(conn, """
            SELECT HBKID, COUNT(*), GROUP_CONCAT(DISTINCT ZLSCH) as methods,
                   GROUP_CONCAT(DISTINCT WAERS) as currencies
            FROM T042I WHERE ZBUKR='UNES'
            GROUP BY HBKID ORDER BY HBKID
        """)
        if not isinstance(paying, str):
            print(f"\n  Paying banks ({len(paying)}):")
            for r in paying:
                print(f"    {r[0]:10s}: {r[1]} entries, methods={r[2]}, currencies={r[3]}")
else:
    print("  T042I NOT IN GOLD DB")

# ── Step 9: TIBAN ──
print(f"\n{'='*70}")
print("  STEP 13: TIBAN — IBAN")
print("="*70)

if "TIBAN" in all_tables:
    tiban_cols = cols(conn, "TIBAN")
    cnt = q(conn, "SELECT COUNT(*) FROM TIBAN WHERE BUKRS='UNES'")
    print(f"  Entries (UNES): {cnt[0][0] if not isinstance(cnt, str) else '?'}")

    # Banks WITH vs WITHOUT IBAN
    with_iban = q(conn, """
        SELECT k.HBKID,
               COUNT(DISTINCT k.HKTID) as accts,
               COUNT(DISTINCT i.HKTID) as with_iban
        FROM T012K k LEFT JOIN TIBAN i ON k.BUKRS=i.BUKRS AND k.HBKID=i.HBKID AND k.HKTID=i.HKTID
        WHERE k.BUKRS='UNES'
        GROUP BY k.HBKID
        HAVING with_iban < accts
        ORDER BY k.HBKID
    """)
    if not isinstance(with_iban, str):
        print(f"\n  Banks with MISSING IBANs ({len(with_iban)}):")
        for r in with_iban[:30]:
            print(f"    {r[0]:10s}: {r[1]} accounts, {r[2]} with IBAN")
else:
    print("  TIBAN NOT IN GOLD DB")

# ── Summary: Which banks have COMPLETE config? ──
print(f"\n{'='*70}")
print("  CONFIGURATION COMPLETENESS MATRIX")
print("="*70)

# Get all UNES house banks from T012K
all_banks = q(conn, """
    SELECT DISTINCT HBKID FROM T012K WHERE BUKRS='UNES' ORDER BY HBKID
""")
if isinstance(all_banks, str):
    print(f"  ERROR: {all_banks}")
else:
    bank_list = [r[0] for r in all_banks]
    print(f"  Total house banks: {len(bank_list)}")

    # For each bank, check which config tables have entries
    print(f"\n  {'HBKID':8s} {'T012K':6s} {'T030H':6s} {'T035D':6s} {'T028B':6s} {'T018V':6s} {'T042I':6s} {'TIBAN':6s} {'SETS':6s}")
    print(f"  {'-'*8} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6}")

    complete = 0
    partial = 0
    for hbkid in bank_list:
        # T012K accounts
        t012k_c = q(conn, f"SELECT COUNT(*) FROM T012K WHERE BUKRS='UNES' AND HBKID='{hbkid}'")[0][0]

        # T030H (need to find GL accounts first)
        gls = q(conn, f"SELECT HKONT FROM T012K WHERE BUKRS='UNES' AND HBKID='{hbkid}'")
        gl_list = [r[0] for r in gls] if not isinstance(gls, str) else []
        t030h_c = 0
        if "T030H" in all_tables and gl_list:
            for gl in gl_list:
                # Derive clearing GL
                sig = gl.lstrip('0')
                if sig.startswith('10'):
                    clearing = ('11' + sig[2:]).zfill(len(gl))
                    r = q(conn, f"SELECT COUNT(*) FROM T030H WHERE KTOPL='UNES' AND HKONT='{clearing}'")
                    if not isinstance(r, str):
                        t030h_c += r[0][0]

        # T035D
        t035d_c = 0
        if "T035D" in all_tables:
            r = q(conn, f"SELECT COUNT(*) FROM T035D WHERE BUKRS='UNES' AND DISKB LIKE '{hbkid}%'")
            if not isinstance(r, str):
                t035d_c = r[0][0]

        # T028B (need bank key from T012)
        t028b_c = 0
        if "T028B" in all_tables and "T012" in all_tables:
            bk = q(conn, f"SELECT BANKL FROM T012 WHERE BUKRS='UNES' AND HBKID='{hbkid}'")
            if not isinstance(bk, str) and bk:
                bankl = bk[0][0]
                r = q(conn, f"SELECT COUNT(*) FROM T028B WHERE BANKL='{bankl}'")
                if not isinstance(r, str):
                    t028b_c = r[0][0]

        # T018V
        t018v_c = 0
        if "T018V" in all_tables:
            r = q(conn, f"SELECT COUNT(*) FROM T018V WHERE BUKRS='UNES' AND HBKID='{hbkid}'")
            if not isinstance(r, str):
                t018v_c = r[0][0]

        # T042I
        t042i_c = 0
        if "T042I" in all_tables:
            r = q(conn, f"SELECT COUNT(*) FROM T042I WHERE ZBUKR='UNES' AND HBKID='{hbkid}'")
            if not isinstance(r, str):
                t042i_c = r[0][0]

        # TIBAN
        tiban_c = 0
        if "TIBAN" in all_tables:
            r = q(conn, f"SELECT COUNT(*) FROM TIBAN WHERE BUKRS='UNES' AND HBKID='{hbkid}'")
            if not isinstance(r, str):
                tiban_c = r[0][0]

        # SETLEAF — check if any GL in any YBANK set
        sets_c = 0

        has_all = all([t012k_c, t035d_c, t018v_c])
        if has_all:
            complete += 1
        else:
            partial += 1

        print(f"  {hbkid:8s} {t012k_c:6d} {t030h_c:6d} {t035d_c:6d} {t028b_c:6d} {t018v_c:6d} {t042i_c:6d} {tiban_c:6d}")

    print(f"\n  Complete (T012K+T035D+T018V): {complete}")
    print(f"  Partial: {partial}")

conn.close()
print("\nDone.")
