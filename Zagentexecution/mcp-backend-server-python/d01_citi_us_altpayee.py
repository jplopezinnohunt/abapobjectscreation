"""Find D01 CITI XML US-country test candidates with alt-payee.

Criteria:
  - BSAK with EMPFB <> '' (alt-payee fired and paid)
  - WAERS = USD (CITI Worldlink)
  - SOURCE or ALT-PAYEE country LAND1 = 'US'
  - Source non-staff (KTOKK not in UNES/SCSA/HQSU/ICTP)
"""
import os
from collections import defaultdict
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

# BSAK USD with EMPFB
print("\n=== BSAK EMPFB USD (split reads) ===")
a = rd("BSAK", ["EMPFB <> ' '"], ["BUKRS","BELNR","GJAHR","LIFNR","EMPFB"], n=2000)
b = rd("BSAK", ["EMPFB <> ' '"], ["BUKRS","BELNR","WAERS","ZLSCH","HBKID","AUGDT","AUGBL"], n=2000)

merged = []
for ra, rb in zip(a, b):
    if rb['WAERS'].strip() == 'USD':
        merged.append({**ra, **rb})
print(f"  {len(merged)} USD rows")

# Master data for LIFNRs
all_lifnrs = set(r['LIFNR'].strip() for r in merged) | set(r['EMPFB'].strip() for r in merged)
print(f"  Looking up master data for {len(all_lifnrs)} LIFNRs…")

info_cache = {}
for lifnr in sorted(all_lifnrs):
    try:
        l = rd("LFA1", [f"LIFNR = '{lifnr}'"], ["KTOKK","NAME1","LAND1","ADRNR"], n=1)
        if l:
            info_cache[lifnr] = (l[0]['KTOKK'].strip(), l[0]['NAME1'].strip(),
                                 l[0]['LAND1'].strip(), l[0]['ADRNR'].strip())
    except Exception:
        pass

# Filter: non-staff source, US country on alt-payee OR source
print(f"\n=== US-country pairs with alt-payee (non-staff source) ===")
pairs = defaultdict(list)
for r in merged:
    src = r['LIFNR'].strip()
    alt = r['EMPFB'].strip()
    src_kt = info_cache.get(src, ('?','','',''))[0]
    if src_kt in ('UNES','SCSA','HQSU','ICTP'):
        continue
    src_land = info_cache.get(src, ('?','','',''))[2]
    alt_land = info_cache.get(alt, ('?','','',''))[2]
    if src_land != 'US' and alt_land != 'US':
        continue
    pairs[(src, alt)].append(r)

print(f"  {len(pairs)} pairs with US country on source or alt-payee")
print(f"\n  {'SOURCE':12s} {'KT':5s} {'NAME':25s} {'LAND':4s} → {'ALT':12s} {'KT':5s} {'NAME':25s} {'LAND':4s} | ZLSCH HBKID | docs")
print('-'*150)
for (src, alt), docs in sorted(pairs.items(), key=lambda x: -len(x[1])):
    src_info = info_cache.get(src, ('?','','',''))
    alt_info = info_cache.get(alt, ('?','','',''))
    zlsch_set = sorted(set(d['ZLSCH'].strip() for d in docs))
    hbkid_set = sorted(set(d['HBKID'].strip() for d in docs if d['HBKID'].strip()))
    print(f"  {src:12s} {src_info[0]:5s} {src_info[1][:25]:25s} {src_info[2]:4s} → {alt:12s} {alt_info[0]:5s} {alt_info[1][:25]:25s} {alt_info[2]:4s} | {','.join(zlsch_set):>5s} {','.join(hbkid_set):>5s} | {len(docs)}")

# Sample docs for top pairs
print(f"\n=== Sample docs for top 5 US pairs ===")
for (src, alt), docs in sorted(pairs.items(), key=lambda x: -len(x[1]))[:5]:
    src_info = info_cache.get(src, ('?','','',''))
    alt_info = info_cache.get(alt, ('?','','',''))
    print(f"\n  {src} {src_info[1]} ({src_info[2]}) → {alt} {alt_info[1]} ({alt_info[2]})  [{len(docs)} docs]")
    for d in docs[:3]:
        print(f"    {d['BUKRS']}/{d['BELNR']}/{d['GJAHR']} AUGDT={d['AUGDT']} AUGBL={d['AUGBL']} WAERS={d['WAERS']} ZLSCH='{d['ZLSCH'].strip()}' HBKID={d['HBKID']}")
    # ADRC for alt-payee
    alt_adrnr = info_cache.get(alt, ('','','',''))[3]
    if alt_adrnr:
        adrc = rd("ADRC", [f"ADDRNUMBER = '{alt_adrnr}'"],
                  ["STREET","HOUSE_NUM1","POST_CODE1","CITY1","COUNTRY","REGION"], n=1)
        if adrc:
            ar = adrc[0]
            print(f"    ALT-PAYEE ADRC: STREET='{ar['STREET'].strip()}' HOUSE='{ar['HOUSE_NUM1'].strip()}' POST={ar['POST_CODE1'].strip()} CITY='{ar['CITY1'].strip()}' COUNTRY={ar['COUNTRY']} REGION={ar['REGION']}")
    # IBAN
    try:
        t = rd("TIBAN", [f"TABKEY LIKE '%{alt}%'"], ["IBAN"], n=2)
        for tr in t:
            print(f"    ALT-PAYEE IBAN: {tr['IBAN'].strip()}")
    except Exception:
        pass
