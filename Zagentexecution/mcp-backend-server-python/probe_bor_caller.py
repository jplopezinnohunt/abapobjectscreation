"""H52 — find what calls Salesforce BOR (via MULESOFT_PROD HTTP destination).
P01 RFC_READ_TABLE rejects OR/parens on TADIR — use simple = / LIKE per query."""
import os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv()
cp = {'ashost': os.getenv('SAP_P01_ASHOST'), 'sysnr': os.getenv('SAP_P01_SYSNR'),
      'client': os.getenv('SAP_P01_CLIENT'), 'user': os.getenv('SAP_P01_USER'), 'lang': 'EN',
      'snc_mode': '1', 'snc_partnername': os.getenv('SAP_P01_SNC_PARTNERNAME'), 'snc_qop': '9'}
conn = Connection(**cp)

def scan(tab, opts, fields, label, rowcount=200):
    try:
        kw = {'QUERY_TABLE': tab, 'DELIMITER': '|', 'ROWCOUNT': rowcount,
              'OPTIONS': [{'TEXT': opts}], 'FIELDS': [{'FIELDNAME': f} for f in fields]}
        r = conn.call('RFC_READ_TABLE', **kw)
        print(f'\n-- {label} ({len(r["DATA"])}) --')
        for row in r['DATA'][:30]:
            print(' ', row['WA'][:200])
        return r['DATA']
    except Exception as e:
        print(f'\n-- {label} ERR: {str(e)[:120]}')
        return []

# 1. Custom classes with BOR — Y then Z
scan('TADIR', "OBJ_NAME LIKE 'Y%BOR%' AND OBJECT = 'CLAS'", ['OBJ_NAME', 'DEVCLASS', 'AUTHOR'], 'Y* classes with BOR')
scan('TADIR', "OBJ_NAME LIKE 'Z%BOR%' AND OBJECT = 'CLAS'", ['OBJ_NAME', 'DEVCLASS', 'AUTHOR'], 'Z* classes with BOR')

# 2. Programs with BOR
scan('TADIR', "OBJ_NAME LIKE 'Y%BOR%' AND OBJECT = 'PROG'", ['OBJ_NAME', 'DEVCLASS', 'AUTHOR'], 'Y* programs with BOR')
scan('TADIR', "OBJ_NAME LIKE 'Z%BOR%' AND OBJECT = 'PROG'", ['OBJ_NAME', 'DEVCLASS', 'AUTHOR'], 'Z* programs with BOR')

# 3. Any Salesforce reference
scan('TADIR', "OBJ_NAME LIKE 'Y%SALESFORCE%'", ['OBJECT', 'OBJ_NAME', 'DEVCLASS'], 'Any Y SALESFORCE')
scan('TADIR', "OBJ_NAME LIKE 'Z%SALESFORCE%'", ['OBJECT', 'OBJ_NAME', 'DEVCLASS'], 'Any Z SALESFORCE')
scan('TADIR', "OBJ_NAME LIKE 'Y%SFDC%'", ['OBJECT', 'OBJ_NAME', 'DEVCLASS'], 'Any Y SFDC')
scan('TADIR', "OBJ_NAME LIKE 'Y%MULE%'", ['OBJECT', 'OBJ_NAME', 'DEVCLASS'], 'Any Y MULE')
scan('TADIR', "OBJ_NAME LIKE 'Z%MULE%'", ['OBJECT', 'OBJ_NAME', 'DEVCLASS'], 'Any Z MULE')

# 4. Known Core Manager prefix (PROJECT02 sender)
scan('TADIR', "OBJ_NAME LIKE 'Y%CORE%'", ['OBJECT', 'OBJ_NAME', 'DEVCLASS'], 'Any Y CORE')
scan('TADIR', "DEVCLASS = 'YWFI'", ['OBJECT', 'OBJ_NAME'], 'YWFI package objects', 200)

# 5. Custom FMs — destination might be dynamic. Try TFDIR for anything with BOR in FUNCNAME
scan('TFDIR', "FUNCNAME LIKE 'Y%BOR%'", ['FUNCNAME', 'PNAME'], 'Y FMs with BOR')
scan('TFDIR', "FUNCNAME LIKE 'Z%BOR%'", ['FUNCNAME', 'PNAME'], 'Z FMs with BOR')
scan('TFDIR', "FUNCNAME LIKE 'Y%MULE%'", ['FUNCNAME', 'PNAME'], 'Y FMs with MULE')
scan('TFDIR', "FUNCNAME LIKE 'Y%SALESFORCE%'", ['FUNCNAME', 'PNAME'], 'Y FMs with SALESFORCE')
scan('TFDIR', "FUNCNAME LIKE 'Y%SFDC%'", ['FUNCNAME', 'PNAME'], 'Y FMs with SFDC')

# 6. Proxy classes (SAP proxy generator prefixes CO_/CI_/II_ for SOAP clients)
scan('TADIR', "OBJ_NAME LIKE 'YCO_%' AND OBJECT = 'CLAS'", ['OBJ_NAME', 'DEVCLASS'], 'YCO_ proxy classes', 100)
scan('TADIR', "OBJ_NAME LIKE 'ZCO_%' AND OBJECT = 'CLAS'", ['OBJ_NAME', 'DEVCLASS'], 'ZCO_ proxy classes', 100)

# 7. WBCROSSGT for MULESOFT_PROD (may need LIKE)
scan('WBCROSSGT', "NAME LIKE 'MULESOFT%'", ['OTYPE', 'NAME', 'INCLUDE'], 'WBCROSSGT MULESOFT refs', 100)
scan('WBCROSSGT', "NAME = 'BOR'", ['OTYPE', 'NAME', 'INCLUDE'], 'WBCROSSGT BOR refs', 50)
