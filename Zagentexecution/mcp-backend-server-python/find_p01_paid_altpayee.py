"""PAID alt-payee fires in P01 — inverse approach: DFPAYG → REGUP → BSEC.

For each paid run in DFPAYG (any FORMI, last 2 years):
  get all REGUP item docs → for each (BUKRS,BELNR,GJAHR,BUZEI) check BSEC.

If BSEC has the row → that document was paid with alt-payee/CPD address.
That's a real production fire.
"""
import os
from collections import Counter, defaultdict
from dotenv import load_dotenv
from pyrfc import Connection

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

# Step 1: pull DFPAYG runs since 2024 for SEPA family only (focus on user question)
print("\n=== DFPAYG SEPA-family runs since 2024 ===")
dfpg = rd("DFPAYG",
          ["LAUFD >= '20240101'", " AND FORMI LIKE '/SEPA%'"],
          ["LAUFD","LAUFI","ZBUKR","FORMI"], n=2000)
print(f"  {len(dfpg)} SEPA-family runs")
print(f"  Formats: {Counter(r['FORMI'].strip() for r in dfpg).most_common()}")
print(f"  Cocodes: {Counter(r['ZBUKR'].strip() for r in dfpg).most_common()}")

# Step 2: for each run, pull REGUP items
print(f"\n=== Pulling REGUP items for these runs (cap at 100 runs to keep time bounded) ===")
all_items = []  # list of (LAUFD, LAUFI, ZBUKR, FORMI, BUKRS, BELNR, GJAHR, BUZEI, LIFNR)
runs_processed = 0
for g in dfpg[:100]:
    laufd, laufi, zb, formi = g['LAUFD'].strip(), g['LAUFI'].strip(), g['ZBUKR'].strip(), g['FORMI'].strip()
    try:
        regup = rd("REGUP",
                   [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                   ["BUKRS","BELNR","GJAHR","BUZEI","LIFNR"], n=200)
        for rp in regup:
            all_items.append((laufd, laufi, zb, formi, rp['BUKRS'].strip(), rp['BELNR'].strip(), rp['GJAHR'].strip(), rp['BUZEI'].strip(), rp['LIFNR'].strip()))
        runs_processed += 1
    except Exception:
        pass
print(f"  {runs_processed} runs processed → {len(all_items)} REGUP items collected")

# Step 3: for each unique (BUKRS,BELNR,GJAHR,BUZEI), check whether BSEC exists
print(f"\n=== Checking which paid REGUP items have a BSEC entry (= alt-payee/CPD fire) ===")
seen_docs = set()
unique_docs = []
for it in all_items:
    key = (it[4], it[5], it[6], it[7])
    if key not in seen_docs:
        seen_docs.add(key)
        unique_docs.append((it[3], it[8], *key))  # (formi, lifnr, bukrs, belnr, gjahr, buzei)

print(f"  {len(unique_docs)} unique paid docs to test against BSEC")

altpayee_hits = []
for i, (formi, lifnr, bukrs, belnr, gjahr, buzei) in enumerate(unique_docs):
    try:
        b = rd("BSEC",
               [f"BUKRS = '{bukrs}'", f" AND BELNR = '{belnr}'", f" AND GJAHR = '{gjahr}'", f" AND BUZEI = '{buzei}'"],
               ["NAME1","LAND1","STRAS","ORT01"], n=1)
        if b:
            altpayee_hits.append({
                'formi': formi, 'lifnr': lifnr, 'bukrs': bukrs, 'belnr': belnr, 'gjahr': gjahr, 'buzei': buzei,
                'bsec_name': b[0]['NAME1'].strip(),
                'bsec_land': b[0]['LAND1'].strip(),
                'bsec_stras': b[0]['STRAS'].strip(),
                'bsec_ort01': b[0]['ORT01'].strip(),
            })
    except Exception:
        pass
    if (i+1) % 50 == 0:
        print(f"    progress: {i+1}/{len(unique_docs)}  hits so far: {len(altpayee_hits)}")

print(f"\n=== RESULT: {len(altpayee_hits)} paid SEPA-family docs have BSEC (alt-payee/CPD fire) ===")
formi_dist = Counter(h['formi'] for h in altpayee_hits)
print(f"  Format breakdown: {dict(formi_dist.most_common())}")

print(f"\n=== First 15 hits ===")
for h in altpayee_hits[:15]:
    print(f"  FORMI={h['formi']:30s} LIFNR={h['lifnr']:12s} doc={h['bukrs']}/{h['belnr']}/{h['gjahr']}/{h['buzei']}")
    print(f"    BSEC NAME={h['bsec_name'][:35]:35s} LAND={h['bsec_land']} STRAS={h['bsec_stras'][:30]} ORT={h['bsec_ort01'][:20]}")
