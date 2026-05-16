"""Find D01 /CITI/XML/UNESCO/DC_V3_01 runs that already ran and involved a US-country
source vendor or alt-payee. These are directly replayable via ZSAPFPAYM_REPLAY without
needing a new FB60 + F110.
"""
import os
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

def rd(t, opts, fields, n=200):
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=t,
                  OPTIONS=[{'TEXT': x} for x in opts],
                  FIELDS=[{'FIELDNAME': x} for x in fields],
                  DELIMITER='|', ROWCOUNT=n)
    cols = [f['FIELDNAME'] for f in r.get('FIELDS',[])] or fields
    return [dict(zip(cols, d['WA'].split('|'))) for d in r.get('DATA', [])]

# 1. All D01 /CITI/XML/UNESCO/DC_V3_01 DFPAYG runs
print("\n=== ALL D01 DFPAYG /CITI/XML/UNESCO/DC_V3_01 runs ===")
dfpg = rd("DFPAYG", ["FORMI = '/CITI/XML/UNESCO/DC_V3_01'"],
          ["LAUFD","LAUFI","ZBUKR","GRPNO","HBKID","ANZ_ERZ","ANZ_ERL"], n=50)
print(f"  {len(dfpg)} CITI DC_V3_01 runs in D01")
for g in dfpg:
    print(f"    {g['LAUFD']}/{g['LAUFI'].strip()}/{g['ZBUKR']} GRPNO={g['GRPNO'].strip()} HBKID={g['HBKID']} ANZ_ERZ={g['ANZ_ERZ'].strip()} ANZ_ERL={g['ANZ_ERL'].strip()}")

# 2. Per run, list REGUH LIFNRs + EMPFG + look up master to find US country
print(f"\n=== Per-run vendor list + US country check ===")
for g in dfpg:
    laufd, laufi, zb = g['LAUFD'].strip(), g['LAUFI'].strip(), g['ZBUKR'].strip()
    print(f"\n  Run {laufd}/{laufi}/{zb}:")
    try:
        # Narrow read for REGUH
        a = rd("REGUH",
               [f"LAUFD = '{laufd}'", f"AND LAUFI = '{laufi}'", f"AND ZBUKR = '{zb}'"],
               ["LIFNR","EMPFG","XVORL"], n=100)
        b = rd("REGUH",
               [f"LAUFD = '{laufd}'", f"AND LAUFI = '{laufi}'", f"AND ZBUKR = '{zb}'"],
               ["LIFNR","VBLNR"], n=100)
        for ra, rb in zip(a, b):
            lifnr = ra['LIFNR'].strip()
            empfg = ra['EMPFG'].strip()
            xv = ra['XVORL'].strip()
            v = rb['VBLNR'].strip()
            # Look up LFA1 country
            land_src = '?'
            ktokk_src = '?'
            name_src = ''
            if lifnr:
                try:
                    l = rd("LFA1", [f"LIFNR = '{lifnr}'"], ["LAND1","KTOKK","NAME1"], n=1)
                    if l:
                        land_src = l[0]['LAND1'].strip()
                        ktokk_src = l[0]['KTOKK'].strip()
                        name_src = l[0]['NAME1'].strip()
                except Exception:
                    pass
            # Parse EMPFG → alt-payee LIFNR
            alt_lifnr = ''
            land_alt = '?'
            name_alt = ''
            if empfg.startswith('>') and '>Z' in empfg:
                alt_lifnr = empfg[1:].split('>')[0]
                try:
                    l = rd("LFA1", [f"LIFNR = '{alt_lifnr}'"], ["LAND1","KTOKK","NAME1"], n=1)
                    if l:
                        land_alt = l[0]['LAND1'].strip()
                        name_alt = l[0]['NAME1'].strip()
                except Exception:
                    pass
            us_flag = '★US★' if land_src == 'US' or land_alt == 'US' else '     '
            real_flag = 'REAL' if (xv == '' and v and v.startswith('0002')) else '     '
            print(f"    {us_flag} {real_flag} LIFNR={lifnr} {name_src[:20]:20s} ({ktokk_src},{land_src})  EMPFG='{empfg}'  alt={alt_lifnr} {name_alt[:20]:20s} ({land_alt})  XVORL='{xv}' VBLNR={v}")
    except Exception as e:
        print(f"    err: {e}")
