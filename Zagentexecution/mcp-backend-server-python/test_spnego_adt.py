"""
test_spnego_adt.py — Test SPNEGO (Windows SSO/Kerberos) for SAP ADT HTTP access.
Uses pywin32's sspi module to get a Negotiate token from Windows SSPI.
"""
import sys, ssl, base64, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

host = 'hq-sap-d01.hq.int.unesco.org'
spn  = f'HTTP/{host}'
client = '350'

ctx_ssl = ssl.create_default_context()
ctx_ssl.check_hostname = False
ctx_ssl.verify_mode = ssl.CERT_NONE

try:
    import sspi
    print(f'sspi available: {dir(sspi)[:8]}')

    # Get SPNEGO token via Windows SSPI
    ca = sspi.ClientAuth('Negotiate', targetspn=spn)
    err, bufs = ca.authorize(None)
    print(f'SSPI authorize rc={err}')
    token = base64.b64encode(bufs[0].Buffer).decode()
    print(f'Negotiate token (first 40): {token[:40]}...')

    # Try ADT with Negotiate header
    url = f'https://{host}/sap/bc/adt/discovery?sap-client={client}'
    req = urllib.request.Request(url, headers={
        'Authorization': f'Negotiate {token}',
        'X-CSRF-Token': 'Fetch',
        'Accept': 'application/xml'
    })
    try:
        with urllib.request.urlopen(req, context=ctx_ssl, timeout=10) as r:
            csrf = r.getheader('X-CSRF-Token', '')
            print(f'SUCCESS via SPNEGO! HTTP {r.status}, CSRF={csrf[:30]}')
    except urllib.error.HTTPError as e:
        auth_hdr = e.headers.get('WWW-Authenticate', '')
        print(f'HTTP {e.code}  WWW-Authenticate: {auth_hdr[:100]}')

except ImportError as e:
    print(f'sspi import failed: {e}')
except Exception as e:
    print(f'Error: {e}')
