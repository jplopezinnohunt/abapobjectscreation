"""Alt-payee analysis for /CGI_XML_CT_UNESCO and /CITI/XML/UNESCO/DC_V3_01 in P01.

Mirrors the SEPA analysis (sesión #75):
  1. LFA1.LNRZA master-level fires that routed via these formats
  2. BSEC doc-level fires for paid docs via these formats
"""
import os
from collections import Counter
from dotenv import load_dotenv
from pyrfc import Connection
import sqlite3

load_dotenv('Zagentexecution/mcp-backend-server-python/.env')
params = dict(
    ashost=os.getenv('SAP_P01_ASHOST'), sysnr=os.getenv('SAP_P01_SYSNR'),
    client=os.getenv('SAP_P01_CLIENT'), user=os.getenv('SAP_P01_USER'),
    lang='EN', snc_mode='1',
    snc_partnername=os.getenv('SAP_P01_SNC_PARTNERNAME'), snc_qop='9',
)
conn = Connection(**params)
print("Connected P01")

def rd(t, opts, fields, n=2000):
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=t,
                  OPTIONS=[{'TEXT': x} for x in opts],
                  FIELDS=[{'FIELDNAME': x} for x in fields],
                  DELIMITER='|', ROWCOUNT=n)
    cols = [f['FIELDNAME'] for f in r.get('FIELDS',[])] or fields
    return [dict(zip(cols, d['WA'].split('|'))) for d in r.get('DATA', [])]

TARGET_FORMATS = ["/CGI_XML_CT_UNESCO", "/CITI/XML/UNESCO/DC_V3_01"]

# ── PART A: LFA1.LNRZA fires against these formats (Gold DB cross-ref) ───────
print("\n" + "="*82)
print(" PART A — LFA1.LNRZA master fires that paid via /CGI or /CITI")
print("="*82)
db = sqlite3.connect('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
cur = db.cursor()
cur.execute("""
WITH src AS (
  SELECT LIFNR, NAME1, KTOKK, LNRZA FROM LFA1
  WHERE COALESCE(LNRZA,'') <> '' AND COALESCE(LOEVM,'') != 'X'
)
SELECT s.LIFNR, s.KTOKK, s.NAME1, s.LNRZA, g.FORMI, COUNT(*) AS n
FROM src s
JOIN REGUH r ON r.LIFNR = s.LIFNR AND r.XVORL = ''
JOIN DFPAYG g ON g.LAUFD=r.LAUFD AND g.LAUFI=r.LAUFI AND g.ZBUKR=r.ZBUKR
WHERE g.FORMI IN ('/CGI_XML_CT_UNESCO','/CITI/XML/UNESCO/DC_V3_01')
GROUP BY s.LIFNR, g.FORMI
ORDER BY n DESC
""")
master_hits = cur.fetchall()
if not master_hits:
    print("  (zero master-level alt-payee fires routed to /CGI or /CITI in 2-year window)")
else:
    print(f"  {len(master_hits)} master-level fires found:")
    for r in master_hits:
        print(f"  {r[0]} {r[1]} {(r[2] or '')[:25]:25s} → LNRZA={r[3]} FORMI={r[4]:30s} n={r[5]}")

# ── PART B: DFPAYG → REGUP → BSEC for doc-level alt-payee on these formats ──
print("\n" + "="*82)
print(" PART B — BSEC fires (doc-level alt-payee/CPD) on /CGI and /CITI paid docs")
print("="*82)

# Pull DFPAYG runs for these formats (since 2024)
print("\n--- DFPAYG runs since 2024 ---")
all_runs = []
for fmt in TARGET_FORMATS:
    dfpg = rd("DFPAYG",
              ["LAUFD >= '20240101'", f" AND FORMI = '{fmt}'"],
              ["LAUFD","LAUFI","ZBUKR","FORMI"], n=4000)
    print(f"  {fmt}: {len(dfpg)} runs")
    all_runs.extend(dfpg)
print(f"  Total runs: {len(all_runs)}")

# Cap at 200 runs for time control
print(f"\n--- Pulling REGUP items for first 200 runs ---")
all_items = []
runs_processed = 0
for g in all_runs[:200]:
    laufd, laufi, zb, formi = g['LAUFD'].strip(), g['LAUFI'].strip(), g['ZBUKR'].strip(), g['FORMI'].strip()
    try:
        regup = rd("REGUP",
                   [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                   ["BUKRS","BELNR","GJAHR","BUZEI","LIFNR"], n=300)
        for rp in regup:
            all_items.append((formi, rp['BUKRS'].strip(), rp['BELNR'].strip(), rp['GJAHR'].strip(), rp['BUZEI'].strip(), rp['LIFNR'].strip()))
        runs_processed += 1
    except Exception:
        pass
print(f"  {runs_processed} runs processed → {len(all_items)} REGUP items collected")

# Dedup unique docs
unique_docs = list({(it[1], it[2], it[3], it[4]): (it[0], it[5]) for it in all_items}.items())
unique_docs = [(formi_lifnr[0], formi_lifnr[1], key[0], key[1], key[2], key[3])
               for key, formi_lifnr in unique_docs]
print(f"  {len(unique_docs)} unique paid docs to test against BSEC")

# Test each against BSEC
print(f"\n--- BSEC cross-ref ---")
altpayee_hits = []
for i, (formi, lifnr, bukrs, belnr, gjahr, buzei) in enumerate(unique_docs):
    try:
        b = rd("BSEC",
               [f"BUKRS = '{bukrs}'", f" AND BELNR = '{belnr}'", f" AND GJAHR = '{gjahr}'", f" AND BUZEI = '{buzei}'"],
               ["NAME1","LAND1","STRAS","ORT01","PSTLZ"], n=1)
        if b:
            altpayee_hits.append({
                'formi': formi, 'lifnr': lifnr,
                'bukrs': bukrs, 'belnr': belnr, 'gjahr': gjahr, 'buzei': buzei,
                'name': b[0]['NAME1'].strip(),
                'land': b[0]['LAND1'].strip(),
                'stras': b[0]['STRAS'].strip(),
                'ort01': b[0]['ORT01'].strip(),
                'pstlz': b[0]['PSTLZ'].strip(),
            })
    except Exception:
        pass
    if (i+1) % 100 == 0:
        print(f"    progress: {i+1}/{len(unique_docs)}  hits so far: {len(altpayee_hits)}")

# Results
print(f"\n{'='*82}")
print(f"  RESULT")
print('='*82)
formi_dist = Counter(h['formi'] for h in altpayee_hits)
print(f"\n  Total docs sampled: {len(unique_docs)}")
print(f"  Docs with BSEC entry (alt-payee/CPD fire): {len(altpayee_hits)}")
print(f"  Format breakdown of fires: {dict(formi_dist.most_common())}")

if altpayee_hits:
    print(f"\n--- First 20 hits ---")
    for h in altpayee_hits[:20]:
        print(f"  FORMI={h['formi']:30s} LIFNR={h['lifnr']:12s} doc={h['bukrs']}/{h['belnr']}/{h['gjahr']}/{h['buzei']}")
        print(f"    BSEC NAME='{h['name'][:35]}' LAND={h['land']} STRAS='{h['stras'][:30]}' CITY='{h['ort01'][:20]}' PSTLZ={h['pstlz']}")

    # Distribution by LAND1
    land_dist = Counter(h['land'] for h in altpayee_hits)
    print(f"\n--- Country distribution of fires ---")
    for land, n in land_dist.most_common():
        print(f"  {land}: {n}")
