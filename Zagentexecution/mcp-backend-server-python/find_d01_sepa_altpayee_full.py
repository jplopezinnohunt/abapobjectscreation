"""Find ALL D01 /SEPA_CT_UNES runs with EMPFG populated + extract full test payload.

Goal: give the user a ready-to-replay ZSAPFPAYM_REPLAY variant for SEPA + alt-payee.
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

# Step 1: ALL D01 DFPAYG /SEPA_CT_UNES runs (no date filter — D01 has limited data)
print("\n=== ALL D01 DFPAYG /SEPA_CT_UNES runs ===")
dfpg = rd("DFPAYG", ["FORMI = '/SEPA_CT_UNES'"],
          ["LAUFD","LAUFI","ZBUKR","GRPNO","HBKID","HKTID","ANZ_ERZ","ANZ_ERL"], n=200)
print(f"  {len(dfpg)} DFPAYG rows total in D01 for /SEPA_CT_UNES")
for g in dfpg:
    print(f"    {g['LAUFD']}/{g['LAUFI'].strip()}/{g['ZBUKR']}  GRPNO={g['GRPNO'].strip()} HBKID={g['HBKID']} ANZ_ERZ={g['ANZ_ERZ'].strip()} ANZ_ERL={g['ANZ_ERL'].strip()}")

# Step 2: for each SEPA run, check REGUH for EMPFG
print(f"\n=== Per-run REGUH.EMPFG check ===")
runs_with_empfg = []
for g in dfpg:
    laufd, laufi, zb = g['LAUFD'].strip(), g['LAUFI'].strip(), g['ZBUKR'].strip()
    try:
        reguh = rd("REGUH",
                   [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                   ["LIFNR","EMPFG","XVORL","VBLNR","HBKID","HKTID"], n=200)
        hits = [r for r in reguh if r['EMPFG'].strip()]
        if hits:
            print(f"\n  ★ {laufd}/{laufi}/{zb}  total REGUH={len(reguh)}  with EMPFG={len(hits)}")
            for h in hits:
                print(f"    LIFNR={h['LIFNR']} EMPFG={h['EMPFG']} XVORL='{h['XVORL']}' VBLNR={h['VBLNR']} HBKID={h['HBKID']}")
            runs_with_empfg.append((laufd, laufi, zb, hits))
    except Exception as e:
        print(f"  {laufd}/{laufi}/{zb}: ERR {e}")

# Step 3: master data for the source + alt-payee LIFNRs in each run
print(f"\n=== Master data for each alt-payee pair ===")
seen_lifnrs = set()
for _, _, _, hits in runs_with_empfg:
    for h in hits:
        src = h['LIFNR'].strip()
        empfg_raw = h['EMPFG'].strip()
        # parse alt-payee LIFNR from EMPFG (>NNNNNNNNNN>Z format)
        if empfg_raw.startswith('>') and '>Z' in empfg_raw:
            alt = empfg_raw[1:].split('>')[0]
        else:
            alt = empfg_raw  # may be a Y1 batch sequence — keep raw
        seen_lifnrs.add((src, alt, empfg_raw))

for src, alt, empfg_raw in seen_lifnrs:
    print(f"\n  --- Pair SOURCE={src}  ALT_PARSED={alt}  (raw EMPFG={empfg_raw}) ---")
    for role, lifnr in (("SOURCE", src), ("ALT-PAYEE", alt)):
        try:
            l = rd("LFA1", [f"LIFNR = '{lifnr}'"],
                   ["LIFNR","NAME1","KTOKK","STRAS","ORT01","PSTLZ","LAND1","ADRNR","LNRZA"], n=1)
            if l:
                d = l[0]
                print(f"    [{role}] {d['LIFNR']} {d['NAME1'].strip()[:35]:35s} KTOKK={d['KTOKK']} LAND={d['LAND1']}  ADRNR={d['ADRNR']} LNRZA={d['LNRZA'].strip()}")
                adrnr = d['ADRNR'].strip()
                if adrnr:
                    a = rd("ADRC", [f"ADDRNUMBER = '{adrnr}'"],
                           ["STREET","HOUSE_NUM1","POST_CODE1","CITY1","COUNTRY"], n=1)
                    if a:
                        ar = a[0]
                        print(f"        ADRC STREET='{ar['STREET'].strip()}' HOUSE='{ar['HOUSE_NUM1'].strip()}' POST={ar['POST_CODE1'].strip()} CITY='{ar['CITY1'].strip()}' COUNTRY={ar['COUNTRY']}")
            else:
                print(f"    [{role}] {lifnr}: NOT in D01 LFA1")
        except Exception as e:
            print(f"    [{role}] {lifnr}: ERR {e}")

# Step 4: extract REGUP items for the chosen test run
print(f"\n=== REGUP item details for runs with EMPFG ===")
for laufd, laufi, zb, hits in runs_with_empfg:
    print(f"\n  {laufd}/{laufi}/{zb}:")
    try:
        regup = rd("REGUP",
                   [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                   ["LIFNR","BUKRS","BELNR","GJAHR","BUZEI","BLART","BLDAT"], n=30)
        for p in regup:
            print(f"    REGUP: LIFNR={p['LIFNR']} doc={p['BUKRS']}/{p['BELNR']}/{p['GJAHR']}/{p['BUZEI']} BLART={p['BLART']} BLDAT={p['BLDAT']}")
    except Exception as e:
        print(f"    REGUP err: {e}")

print(f"\n=== SUMMARY: {len(runs_with_empfg)} D01 /SEPA_CT_UNES runs with EMPFG ===")
