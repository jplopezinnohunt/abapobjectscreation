"""Quick TADIR probe to test RFC_READ_TABLE access."""
import os, sys
from dotenv import load_dotenv
load_dotenv()
import pyrfc

def env(*keys, default=''):
    for k in keys:
        v = os.getenv(k)
        if v: return v
    return default

params = {
    'ashost': env('SAP_D01_ASHOST','SAP_HOST', default='HQ-SAP-D01.HQ.INT.UNESCO.ORG'),
    'sysnr':  env('SAP_D01_SYSNR','SAP_SYSNR', default='00'),
    'client': env('SAP_D01_CLIENT','SAP_CLIENT', default='350'),
}
snc_mode = env('SAP_D01_SNC_MODE','SAP_SNC_MODE')
snc_pn   = env('SAP_D01_SNC_PARTNERNAME','SAP_SNC_PARTNERNAME')
if snc_mode and snc_pn:
    params['snc_mode'] = snc_mode
    params['snc_partnername'] = snc_pn
    params['snc_qop'] = env('SAP_SNC_QOP', default='9')
    print('Using SNC')
else:
    params['user']   = env('SAP_D01_USER','SAP_USER')
    params['passwd'] = env('SAP_D01_PASSWORD','SAP_PASSWORD')
    print('Using Basic Auth')

print('Connecting...')
conn = pyrfc.Connection(**params)
print('Connected!')

# Test 1: TADIR with OBJECT filter, Z-custom packages only
print('\n--- Test 1: OBJECT=PROG, Z packages ---')
try:
    r = conn.call('RFC_READ_TABLE',
        QUERY_TABLE='TADIR',
        DELIMITER='|',
        FIELDS=[{'FIELDNAME':'OBJECT'},{'FIELDNAME':'OBJ_NAME'},{'FIELDNAME':'DEVCLASS'},{'FIELDNAME':'DLVUNIT'}],
        OPTIONS=[{'TEXT':"OBJECT = 'PROG'"}, {'TEXT':"AND DEVCLASS LIKE 'Z%'"}],
        ROWCOUNT=5
    )
    print('  Fields:', [f['FIELDNAME'] for f in r['FIELDS']])
    print(f'  Rows returned: {len(r["DATA"])}')
    for row in r['DATA'][:5]:
        print(f'  {row["WA"]}')
except Exception as e:
    print(f'  ERROR: {e}')

# Test 2: Known object
print('\n--- Test 2: Lookup specific object ---')
try:
    r = conn.call('RFC_READ_TABLE',
        QUERY_TABLE='TADIR',
        DELIMITER='|',
        FIELDS=[{'FIELDNAME':'DEVCLASS'},{'FIELDNAME':'DLVUNIT'}],
        OPTIONS=[{'TEXT':"PGMID = 'R3TR'"},{'TEXT':"AND OBJECT = 'CLAS'"},
                 {'TEXT':"AND OBJ_NAME = 'CL_HRPADUN_DP'"}],
        ROWCOUNT=1
    )
    print(f'  Rows: {len(r["DATA"])}')
    for row in r['DATA']: print(f'  {row["WA"]}')
except Exception as e:
    print(f'  ERROR: {e}')

# Test 3: No filter at all  
print('\n--- Test 3: First 5 rows of TADIR (no filter) ---')
try:
    r = conn.call('RFC_READ_TABLE',
        QUERY_TABLE='TADIR',
        DELIMITER='|',
        FIELDS=[{'FIELDNAME':'PGMID'},{'FIELDNAME':'OBJECT'},{'FIELDNAME':'OBJ_NAME'},{'FIELDNAME':'DEVCLASS'}],
        OPTIONS=[],
        ROWCOUNT=5
    )
    print(f'  Rows: {len(r["DATA"])}')
    for row in r['DATA']: print(f'  {row["WA"]}')
except Exception as e:
    print(f'  ERROR: {e}')

conn.close()
print('\nDone.')
