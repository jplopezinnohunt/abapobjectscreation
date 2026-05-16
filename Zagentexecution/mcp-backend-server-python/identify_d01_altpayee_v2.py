"""v2 — read REGUH carefully and isolate LIFNR + EMPFG before lookups."""
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

def rd(t, opts, fields, n=2000):
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=t,
                  OPTIONS=[{'TEXT': x} for x in opts],
                  FIELDS=[{'FIELDNAME': x} for x in fields],
                  DELIMITER='|', ROWCOUNT=n)
    cols = [f['FIELDNAME'] for f in r.get('FIELDS',[])] or fields
    return [dict(zip(cols, d['WA'].split('|'))) for d in r.get('DATA', [])]

RUNS = [
    ("20210316", "TST",     "UNES", "/SEPA_CT_UNES"),
    ("20230623", "00001R",  "UNES", "/CGI_XML_CT_UNESCO"),
    ("20250307", "00001R",  "UNES", "/CGI_XML_CT_UNESCO_1"),
    ("20220613", "00001R",  "UNES", "/CITI/XML/UNESCO/DC_V3_01"),
]

for laufd, laufi, zb, formi in RUNS:
    print(f"\n{'='*82}")
    print(f"  {formi}  |  run {laufd}/{laufi}/{zb}")
    print('='*82)

    # Pass 1: just LIFNR + XVORL + EMPFG (minimal fields)
    try:
        reguh = rd("REGUH",
                   [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                   ["LIFNR","XVORL","EMPFG"], n=200)
        print(f"  Total REGUH rows: {len(reguh)}")
        for h in reguh:
            mark = '★' if h['EMPFG'].strip() else ' '
            print(f"  {mark} LIFNR='{h['LIFNR'].strip()}' XVORL='{h['XVORL'].strip()}' EMPFG='{h['EMPFG'].strip()}'")
    except Exception as e:
        print(f"  REGUH read err: {e}")
