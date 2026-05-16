"""Profile D01 BSIK open items with EMPFB for V001 F110 proposal candidacy.

Goal: filter to those that would be picked by F110 with /SEPA_CT_UNES.
Key info per candidate:
  - Source LIFNR (LFA1: name, KTOKK, country, ZWELS allowed methods)
  - Alt-payee LIFNR (LFA1 + ADRC + IBAN — alt-payee's bank receives)
  - Open doc's payment method (BSIK.ZLSCH if visible, fallback to source vendor's ZWELS)
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

# Step 1: all BSIK with EMPFB
print("\n=== BSIK with EMPFB (UNES cocode focus) ===")
items_a = rd("BSIK", ["EMPFB <> ' '"],
             ["BUKRS","BELNR","GJAHR","BUZEI","LIFNR","EMPFB"], n=500)
items_b = rd("BSIK", ["EMPFB <> ' '"],
             ["BUKRS","BELNR","GJAHR","BUZEI","ZLSCH","SHKZG"], n=500)
print(f"  {len(items_a)} rows pulled")

# Join the two narrow reads positionally
items = []
for a, b in zip(items_a, items_b):
    items.append({**a, **b})

# Group by (source LIFNR, alt-payee)
pairs = defaultdict(list)
for it in items:
    src = it['LIFNR'].strip()
    alt = it['EMPFB'].strip()
    pairs[(src, alt)].append(it)

print(f"\n  {len(pairs)} unique (source, alt-payee) pairs in BSIK")

# Step 2: master data for each LIFNR involved
all_lifnrs = set()
for src, alt in pairs.keys():
    all_lifnrs.add(src)
    all_lifnrs.add(alt)

def vendor_info(lifnr):
    info = {"name":None,"ktokk":None,"land":None,"zwels":None,"adrnr":None,
            "street":None,"city":None,"post":None,"country":None,"iban":None}
    if not lifnr: return info
    try:
        l = rd("LFA1", [f"LIFNR = '{lifnr}'"],
               ["NAME1","KTOKK","LAND1","ADRNR"], n=1)
        if l:
            info["name"] = l[0]["NAME1"].strip()
            info["ktokk"] = l[0]["KTOKK"].strip()
            info["land"] = l[0]["LAND1"].strip()
            info["adrnr"] = l[0]["ADRNR"].strip()
    except Exception: pass
    try:
        b = rd("LFB1", [f"LIFNR = '{lifnr}'", " AND BUKRS = 'UNES'"],
               ["ZWELS"], n=1)
        if b:
            info["zwels"] = b[0]["ZWELS"].strip()
    except Exception: pass
    if info["adrnr"]:
        try:
            a = rd("ADRC", [f"ADDRNUMBER = '{info['adrnr']}'"],
                   ["STREET","HOUSE_NUM1","POST_CODE1","CITY1","COUNTRY"], n=1)
            if a:
                info["street"] = a[0]["STREET"].strip()
                info["city"] = a[0]["CITY1"].strip()
                info["post"] = a[0]["POST_CODE1"].strip()
                info["country"] = a[0]["COUNTRY"].strip()
        except Exception: pass
    try:
        t = rd("TIBAN", [f"TABKEY LIKE '%{lifnr}%'"], ["IBAN"], n=1)
        if t:
            info["iban"] = t[0]["IBAN"].strip()
    except Exception: pass
    return info

print(f"\n=== Master data for {len(all_lifnrs)} LIFNRs ===")
info_cache = {}
for lifnr in sorted(all_lifnrs):
    info_cache[lifnr] = vendor_info(lifnr)

# Step 3: classify each pair by SEPA-eligibility
print(f"\n=== Pairs classified by SEPA-eligibility ===")
sepa_eligible = []
non_sepa = []
SEPA_COUNTRIES = {'FR','DE','IT','ES','NL','BE','AT','PT','LU','IE','FI','GR','SI','SK','EE','LV','LT','CY','MT','HR','PL','CZ','HU','SE','DK','RO','BG','IS','LI','NO','CH','MC','SM','VA','AD','GB'}
for (src, alt), docs in sorted(pairs.items(), key=lambda x: -len(x[1])):
    src_i = info_cache.get(src, {})
    alt_i = info_cache.get(alt, {})
    alt_iban = alt_i.get("iban") or ""
    alt_land = alt_i.get("country") or alt_i.get("land") or ""
    is_sepa = alt_iban.startswith(tuple(SEPA_COUNTRIES)) or alt_land in SEPA_COUNTRIES
    classification = "SEPA-ELIGIBLE" if is_sepa else "NON-SEPA"
    line = (f"  {classification}: SOURCE={src} {(src_i.get('name') or '')[:25]:25s} → "
            f"ALT={alt} {(alt_i.get('name') or '')[:25]:25s} "
            f"[ALT-LAND={alt_land} ALT-IBAN={alt_iban[:25] if alt_iban else 'NONE'}] "
            f"docs={len(docs)} ZLSCH={set(d['ZLSCH'].strip() for d in docs)}")
    if is_sepa:
        sepa_eligible.append((src, alt, src_i, alt_i, docs))
        print(line)
    else:
        non_sepa.append((src, alt, src_i, alt_i, docs))

print(f"\n=== Non-SEPA pairs (for reference) ===")
for src, alt, src_i, alt_i, docs in non_sepa[:10]:
    print(f"  SOURCE={src} {(src_i.get('name') or '')[:25]:25s} → ALT={alt} {(alt_i.get('name') or '')[:25]:25s} [LAND={alt_i.get('country','')}/{alt_i.get('land','')}] docs={len(docs)}")

print(f"\n=== SEPA-eligible candidates with open docs ready for F110 proposal ===")
for src, alt, src_i, alt_i, docs in sepa_eligible[:10]:
    print(f"\n  SOURCE: {src} {src_i.get('name')} (KTOKK={src_i.get('ktokk')}, LAND={src_i.get('land')})")
    print(f"          IBAN={src_i.get('iban','NONE')}  ZWELS_UNES={src_i.get('zwels','?')}")
    print(f"  ALT-PAYEE: {alt} {alt_i.get('name')} (KTOKK={alt_i.get('ktokk')}, LAND={alt_i.get('land')})")
    print(f"          ADDR: {alt_i.get('street','')}, {alt_i.get('post','')} {alt_i.get('city','')}, {alt_i.get('country','')}")
    print(f"          IBAN={alt_i.get('iban','NONE')}")
    print(f"  OPEN docs ({len(docs)}):")
    for d in docs[:5]:
        print(f"    {d['BUKRS']}/{d['BELNR']}/{d['GJAHR']}/{d['BUZEI']} SHKZG={d['SHKZG']} ZLSCH='{d['ZLSCH'].strip()}'")
