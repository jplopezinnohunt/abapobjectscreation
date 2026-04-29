"""H52 — P01 live probe: MuleSoft IDoc reality + DBCON + SM58. One-shot, no CLI args."""
import os
from dotenv import load_dotenv
from pyrfc import Connection
from collections import Counter

load_dotenv()
cp = {
    'ashost': os.getenv('SAP_P01_ASHOST'),
    'sysnr': os.getenv('SAP_P01_SYSNR'),
    'client': os.getenv('SAP_P01_CLIENT'),
    'user': os.getenv('SAP_P01_USER'),
    'lang': 'EN',
    'snc_mode': '1',
    'snc_partnername': os.getenv('SAP_P01_SNC_PARTNERNAME'),
    'snc_qop': '9',
}
conn = Connection(**cp)
print('P01 connected:', conn.call('STFC_CONNECTION', REQUTEXT='ping')['RESPTEXT'][:80])

# 1. EDIDC — IDoc traffic to any MULE partner
r = conn.call('RFC_READ_TABLE', QUERY_TABLE='EDIDC', DELIMITER='|',
              OPTIONS=[{'TEXT': "RCVPRN LIKE 'MULE%'"}],
              FIELDS=[{'FIELDNAME': 'MESTYP'}, {'FIELDNAME': 'RCVPRN'}],
              ROWCOUNT=20000)
cnt = Counter([tuple(row['WA'].split('|')[:2]) for row in r['DATA']])
print('\nP01 EDIDC to MULE% total rows:', len(r['DATA']))
for k, n in sorted(cnt.items(), key=lambda x: -x[1]):
    print(' ', k[0].strip(), 'to', k[1].strip(), '=', n)

# 2. EDP13 — outbound partner profile MULE_PROD
r = conn.call('RFC_READ_TABLE', QUERY_TABLE='EDP13', DELIMITER='|',
              OPTIONS=[{'TEXT': "RCVPRN = 'MULE_PROD'"}], ROWCOUNT=50)
f = [x['FIELDNAME'] for x in r['FIELDS']]
iM, iT = f.index('MESTYP'), f.index('IDOCTYP')
print('\nP01 EDP13 MULE_PROD outbound rows:', len(r['DATA']))
for row in r['DATA']:
    p = row['WA'].split('|')
    print(' ', p[iM].strip(), '->', p[iT].strip())

# 3. EDP21 — inbound partner profile from MULE_PROD
r = conn.call('RFC_READ_TABLE', QUERY_TABLE='EDP21', DELIMITER='|',
              OPTIONS=[{'TEXT': "SNDPRN = 'MULE_PROD'"}], ROWCOUNT=50)
f = [x['FIELDNAME'] for x in r['FIELDS']]
iM = f.index('MESTYP')
print('\nP01 EDP21 MULE_PROD inbound rows:', len(r['DATA']))
for row in r['DATA']:
    p = row['WA'].split('|')
    print(' ', p[iM].strip())

# 4. DBCON — external DB connections
r = conn.call('RFC_READ_TABLE', QUERY_TABLE='DBCON', DELIMITER='|',
              FIELDS=[{'FIELDNAME': 'CON_NAME'}, {'FIELDNAME': 'DBMS'},
                      {'FIELDNAME': 'USER_NAME'}], ROWCOUNT=50)
print('\nP01 DBCON rows:', len(r['DATA']))
for row in r['DATA']:
    print(' ', row['WA'])

# 5. ARFCSSTATE — SM58 (pending/failed tRFC)
r = conn.call('RFC_READ_TABLE', QUERY_TABLE='ARFCSSTATE', DELIMITER='|',
              FIELDS=[{'FIELDNAME': 'ARFCDEST'}, {'FIELDNAME': 'ARFCSTATE'}],
              ROWCOUNT=200)
dc = Counter([row['WA'].strip() for row in r['DATA']])
print('\nP01 SM58 (ARFCSSTATE) total rows:', len(r['DATA']))
for k, n in dc.most_common(15):
    print(' ', k, '=', n)
