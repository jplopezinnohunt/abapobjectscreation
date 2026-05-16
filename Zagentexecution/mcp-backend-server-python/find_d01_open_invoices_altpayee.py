"""Find D01 open vendor invoices (BSIK) with alt-payee (EMPFB) already set —
candidates to include in a fresh F110 proposal for V001 testing.
"""
import os
from collections import Counter
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv('Zagentexecution/mcp-backend-server-python/.env')
params = dict(
    ashost=os.getenv('SAP_ASHOST'), sysnr=os.getenv('SAP_SYSNR'),
    client=os.getenv('SAP_CLIENT'), user=os.getenv('SAP_USER'),
    lang='EN', snc_mode='1',
    snc_partnername=os.getenv('SAP_SNC_PARTNERNAME'), snc_qop='9',
)
conn = Connection(**params)
print("Connected D01")

def rd(t, opts, fields, n=2000):
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=t,
                  OPTIONS=[{'TEXT': x} for x in opts],
                  FIELDS=[{'FIELDNAME': x} for x in fields],
                  DELIMITER='|', ROWCOUNT=n)
    cols = [f['FIELDNAME'] for f in r.get('FIELDS',[])] or fields
    return [dict(zip(cols, d['WA'].split('|'))) for d in r.get('DATA', [])]

# ── Try 1: BSIK with EMPFB filter directly ──
print("\n=== TEST 1: BSIK with EMPFB <> ' ' (D01) ===")
try:
    rows = rd("BSIK",
              ["EMPFB <> ' '"],
              ["BUKRS","BELNR","GJAHR","BUZEI","LIFNR","EMPFB"],
              n=500)
    print(f"  HITS: {len(rows)}")
    for r in rows[:30]:
        print(f"  {r['BUKRS']}/{r['BELNR']}/{r['GJAHR']}/{r['BUZEI']} LIFNR={r['LIFNR']} EMPFB={r['EMPFB']}")
except Exception as e:
    print(f"  err: {e}")

# ── Try 2: BSIK sample to see if EMPFB column is visible ──
print("\n=== TEST 2: read 50 BSIK rows + EMPFB ===")
try:
    rows = rd("BSIK", ["BUKRS = 'UNES'"], ["BUKRS","BELNR","LIFNR","EMPFB"], n=50)
    pop = [r for r in rows if r['EMPFB'].strip()]
    print(f"  50 rows read, {len(pop)} have non-blank EMPFB")
    for r in pop[:10]:
        print(f"    {r}")
except Exception as e:
    print(f"  err: {e}")

# ── Try 3: D01 BSEC since 2024 (one-time vendor + alt-payee header) ──
print("\n=== TEST 3: D01 BSEC since 2024 ===")
try:
    rows = rd("BSEC",
              ["GJAHR >= '2024'"],
              ["BUKRS","BELNR","GJAHR","BUZEI","NAME1","LAND1"],
              n=500)
    print(f"  BSEC rows since 2024: {len(rows)}")
    bk = Counter(r['BUKRS'].strip() for r in rows)
    print(f"  By BUKRS: {dict(bk.most_common())}")
    for r in rows[:15]:
        print(f"  {r['BUKRS']}/{r['BELNR']}/{r['GJAHR']}/{r['BUZEI']} NAME='{r['NAME1'].strip()[:30]}' LAND={r['LAND1']}")
except Exception as e:
    print(f"  err: {e}")

# ── Try 4: BKPF docs since 2024 with BLART = KR (vendor invoice) + check if any has BSEC ──
# Simpler approach: scan BSIK (open vendor items) for UNES cocode, sample with EMPFB column
print("\n=== TEST 4: UNES open vendor items (BSIK) — sample then check EMPFB ===")
try:
    bsik = rd("BSIK",
              ["BUKRS = 'UNES'", " AND BUDAT >= '20240101'"],
              ["BUKRS","BELNR","GJAHR","BUZEI","LIFNR","BUDAT"],
              n=200)
    print(f"  UNES open vendor items since 2024: {len(bsik)}")
    # For each, check if BSEC exists (indicator of alt-payee/CPD)
    print("  Cross-ref with BSEC for first 30...")
    hits = []
    for r in bsik[:30]:
        try:
            b = rd("BSEC",
                   [f"BUKRS = '{r['BUKRS']}'", f" AND BELNR = '{r['BELNR']}'", f" AND GJAHR = '{r['GJAHR']}'"],
                   ["NAME1","LAND1","STRAS","ORT01","PSTLZ"], n=1)
            if b:
                hits.append((r, b[0]))
                print(f"    ★ OPEN {r['BUKRS']}/{r['BELNR']}/{r['GJAHR']} LIFNR={r['LIFNR']} BUDAT={r['BUDAT']}")
                print(f"        BSEC NAME='{b[0]['NAME1'].strip()[:30]}' LAND={b[0]['LAND1']} STRAS='{b[0]['STRAS'].strip()[:25]}'")
        except Exception:
            pass
    print(f"  → {len(hits)} of 30 open items have BSEC")
except Exception as e:
    print(f"  err: {e}")
