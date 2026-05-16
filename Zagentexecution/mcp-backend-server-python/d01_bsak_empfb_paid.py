"""D01 BSAK (vendor cleared/paid items) with alt-payee.

User-directed field set (sesion #75):
  filter:  EMPFB <> ''  (alternative payee filled)
  fields:  BUKRS, LIFNR, EMPFB, BELNR, GJAHR, AUGDT, AUGBL, WRBTR, WAERS, ZLSCH, HBKID
"""
import os
from collections import Counter, defaultdict
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

# Try the wide field list as user requested — may hit buffer limit on BSAK
print("\n=== TEST 1: BSAK EMPFB <> '' with full field set ===")
try:
    rows = rd("BSAK",
              ["EMPFB <> ' '"],
              ["BUKRS","LIFNR","EMPFB","BELNR","GJAHR","AUGDT","AUGBL","WRBTR","WAERS","ZLSCH","HBKID"],
              n=2000)
    print(f"  HITS: {len(rows)}")
    for r in rows[:5]:
        print(f"  {r}")
except Exception as e:
    print(f"  err: {e}")

# Fallback: split into narrower reads
print("\n=== TEST 2: split fields (narrow reads) ===")
try:
    a = rd("BSAK", ["EMPFB <> ' '"],
           ["BUKRS","BELNR","GJAHR","LIFNR","EMPFB"], n=2000)
    b = rd("BSAK", ["EMPFB <> ' '"],
           ["BUKRS","BELNR","AUGDT","AUGBL","WAERS"], n=2000)
    c = rd("BSAK", ["EMPFB <> ' '"],
           ["BUKRS","BELNR","ZLSCH","HBKID"], n=2000)
    print(f"  a={len(a)} b={len(b)} c={len(c)} rows each")
    merged = []
    for ra, rb, rc in zip(a, b, c):
        merged.append({**ra, **rb, **rc})
    print(f"  merged: {len(merged)} rows")

    # Filter non-staff vendors (KTOKK not in UNES/SCSA/HQSU)
    # Lookup KTOKK per source LIFNR
    print(f"\n  Looking up KTOKK per source LIFNR…")
    lifnrs = sorted(set(r['LIFNR'].strip() for r in merged))
    ktokk_cache = {}
    for lifnr in lifnrs:
        try:
            l = rd("LFA1", [f"LIFNR = '{lifnr}'"], ["KTOKK","NAME1","LAND1"], n=1)
            if l:
                ktokk_cache[lifnr] = (l[0]['KTOKK'].strip(), l[0]['NAME1'].strip(), l[0]['LAND1'].strip())
        except Exception:
            pass
    # Also alt-payee KTOKK + name
    alt_lifnrs = sorted(set(r['EMPFB'].strip() for r in merged))
    alt_cache = {}
    for lifnr in alt_lifnrs:
        try:
            l = rd("LFA1", [f"LIFNR = '{lifnr}'"], ["KTOKK","NAME1","LAND1"], n=1)
            if l:
                alt_cache[lifnr] = (l[0]['KTOKK'].strip(), l[0]['NAME1'].strip(), l[0]['LAND1'].strip())
        except Exception:
            pass

    print(f"\n  === Non-staff source vendors (KTOKK not UNES/SCSA/HQSU) ===")
    pairs = defaultdict(list)
    for r in merged:
        src_kt = ktokk_cache.get(r['LIFNR'].strip(), ('?','',''))[0]
        if src_kt in ('UNES','SCSA','HQSU','ICTP'):
            continue
        pairs[(r['LIFNR'].strip(), r['EMPFB'].strip())].append(r)

    print(f"  {len(pairs)} non-staff (source, alt-payee) pairs in BSAK")
    print()
    print(f"  {'SOURCE':12s} {'KT':5s} {'NAME':27s} → {'ALT':12s} {'KT':5s} {'NAME':27s} | {'WAERS':>5s} {'ZLSCH':>5s} {'HBKID':>5s} | docs")
    print('-'*160)
    for (src, alt), docs in sorted(pairs.items(), key=lambda x: -len(x[1])):
        src_info = ktokk_cache.get(src, ('?','',''))
        alt_info = alt_cache.get(alt, ('?','',''))
        waers_set = set(d['WAERS'].strip() for d in docs)
        zlsch_set = set(d['ZLSCH'].strip() for d in docs)
        hbkid_set = set(d['HBKID'].strip() for d in docs)
        print(f"  {src:12s} {src_info[0]:5s} {src_info[1][:27]:27s} → {alt:12s} {alt_info[0]:5s} {alt_info[1][:27]:27s} | {','.join(waers_set):>5s} {','.join(zlsch_set):>5s} {','.join(hbkid_set):>5s} | {len(docs)}")

    # Best candidates per format guess
    print(f"\n  === Sample docs for top 3 non-staff pairs ===")
    for (src, alt), docs in sorted(pairs.items(), key=lambda x: -len(x[1]))[:5]:
        print(f"\n  {src} → {alt}  ({len(docs)} docs)")
        for d in docs[:3]:
            print(f"    {d['BUKRS']}/{d['BELNR']}/{d['GJAHR']} AUGDT={d['AUGDT']} AUGBL={d['AUGBL']} WAERS={d['WAERS']} ZLSCH='{d['ZLSCH'].strip()}' HBKID={d['HBKID']}")
except Exception as e:
    print(f"  err: {e}")
