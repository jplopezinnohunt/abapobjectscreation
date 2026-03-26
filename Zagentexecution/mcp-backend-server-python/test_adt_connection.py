"""
test_adt_connection.py — Test ADT connectivity and discover the right port
"""
import os, sys, base64, ssl
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
from dotenv import load_dotenv
load_dotenv()

host = '172.16.4.66'
client = '350'
user = os.getenv('SAP_USER', '')
# ADT uses HTTP Basic Auth, not SNC. Need plain password.
password = (os.getenv('SAP_PASSWORD') or os.getenv('SAP_ADT_PASSWORD') or
            os.getenv('SAP_PASS') or '')

print(f'User: {user}')
print(f'Password set: {bool(password)}')

if not password:
    print("ERROR: No password found in env.")
    print("Set SAP_PASSWORD=<your_password> or SAP_ADT_PASSWORD=<your_password> in .env")
    print("ADT uses HTTP Basic Auth, not SNC. The SNC-based RFC connection does not apply.")
    sys.exit(1)


creds = base64.b64encode(f'{user}:{password}'.encode()).decode()
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for port, scheme in [(8000, 'http'), (443, 'https'), (8443, 'https'), (44300, 'https')]:
    url = f'{scheme}://{host}:{port}/sap/bc/adt/discovery?sap-client={client}'
    req = urllib.request.Request(url, headers={
        'Authorization': f'Basic {creds}',
        'X-CSRF-Token': 'Fetch',
        'Accept': 'application/xml'
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
            csrf = r.getheader('X-CSRF-Token', 'none')
            print(f'[{scheme}:{port}] OK! CSRF: {str(csrf)[:30]}')
            break
    except Exception as e:
        print(f'[{scheme}:{port}] FAIL: {type(e).__name__}: {str(e)[:80]}')
