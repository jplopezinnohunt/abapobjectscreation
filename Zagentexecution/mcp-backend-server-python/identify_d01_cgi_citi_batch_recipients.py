"""For CGI/CITI batch runs (LIFNR empty in REGUH, batch tag in EMPFG),
pull REGUP items to identify actual recipients.
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

def rd(t, opts, fields, n=2000):
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=t,
                  OPTIONS=[{'TEXT': x} for x in opts],
                  FIELDS=[{'FIELDNAME': x} for x in fields],
                  DELIMITER='|', ROWCOUNT=n)
    cols = [f['FIELDNAME'] for f in r.get('FIELDS',[])] or fields
    return [dict(zip(cols, d['WA'].split('|'))) for d in r.get('DATA', [])]

RUNS = [
    ("20230623","00001R","UNES","/CGI_XML_CT_UNESCO"),
    ("20250307","00001R","UNES","/CGI_XML_CT_UNESCO_1"),
    ("20220613","00001R","UNES","/CITI/XML/UNESCO/DC_V3_01"),
]

for laufd, laufi, zb, formi in RUNS:
    print(f"\n{'='*82}")
    print(f"  {formi}  |  {laufd}/{laufi}/{zb}")
    print('='*82)

    # REGUP items
    try:
        regup = rd("REGUP",
                   [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                   ["LIFNR","BUKRS","BELNR","GJAHR","BUZEI","BLART","BLDAT","EMPFG"], n=200)
        print(f"  REGUP items: {len(regup)}")
        lifnrs = sorted(set(r['LIFNR'].strip() for r in regup if r['LIFNR'].strip()))
        print(f"  Distinct LIFNRs in REGUP: {len(lifnrs)} → {lifnrs[:10]}{'...' if len(lifnrs)>10 else ''}")
        for r in regup[:30]:
            print(f"    LIFNR={r['LIFNR']} doc={r['BUKRS']}/{r['BELNR']}/{r['GJAHR']}/{r['BUZEI']} BLART={r['BLART']} BLDAT={r['BLDAT']} EMPFG='{r['EMPFG'].strip()}'")
        if len(regup) > 30:
            print(f"    ... and {len(regup)-30} more")
    except Exception as e:
        print(f"  REGUP err: {e}")

    # Master data for each recipient
    print(f"\n  --- Master data for first 5 distinct recipients ---")
    for lifnr in lifnrs[:5]:
        try:
            l = rd("LFA1", [f"LIFNR = '{lifnr}'"],
                   ["LIFNR","NAME1","KTOKK","LAND1","ADRNR","LNRZA"], n=1)
            if l:
                d = l[0]
                print(f"    {d['LIFNR']} {d['NAME1'].strip()[:35]:35s} KTOKK={d['KTOKK']} LAND={d['LAND1']} LNRZA={d['LNRZA'].strip()}")
                adrnr = d['ADRNR'].strip()
                if adrnr:
                    a = rd("ADRC", [f"ADDRNUMBER = '{adrnr}'"],
                           ["STREET","HOUSE_NUM1","POST_CODE1","CITY1","COUNTRY"], n=1)
                    if a:
                        ar = a[0]
                        print(f"        ADRC: STREET='{ar['STREET'].strip()}' HOUSE='{ar['HOUSE_NUM1'].strip()}' POST={ar['POST_CODE1'].strip()} CITY='{ar['CITY1'].strip()}' COUNTRY={ar['COUNTRY']}")
            else:
                print(f"    {lifnr}: NOT in LFA1")
        except Exception as e:
            print(f"    {lifnr}: ERR {e}")
