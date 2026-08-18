"""
adt_via_sso_cookie.py

Use the existing Chrome SSO session to get a MYSAPSSO2 cookie,
then make ADT REST API calls with that cookie.

The Chrome browser at localhost:9222 already has an authenticated SAP session.
We extract the cookie via CDP (Chrome DevTools Protocol) and use it with httpx for ADT.
"""
import os, sys, json, asyncio
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import httpx
from dotenv import load_dotenv
load_dotenv()

CDP_URL  = "http://localhost:9222"
SAP_HOST = "https://hq-sap-d01.hq.int.unesco.org"
CLIENT   = "350"
TRANSPORT = "D01K9B0EWT"

# ───────────────────────────────────────────────────────────
# 1. Extract SAP SSO cookie from running Chrome session
# ───────────────────────────────────────────────────────────

def get_sap_cookies_from_chrome() -> dict:
    """
    Use CDP JSON API to find all tabs that have the SAP domain,
    then use the Network.getCookies CDP command via WebSocket to extract cookies.
    Falls back to checking each open page for MYSAPSSO2 cookie.
    """
    # Get list of browser targets
    resp = urllib.request.urlopen(f"{CDP_URL}/json", timeout=5)
    tabs = json.loads(resp.read())
    print(f"  Found {len(tabs)} Chrome tabs")

    sap_tabs = [t for t in tabs if 'unesco.org' in t.get('url', '') or 'hq-sap' in t.get('url', '')]
    if not sap_tabs:
        print("  No SAP tabs found - checking all tabs...")
        sap_tabs = tabs[:3]

    for tab in sap_tabs:
        ws_url = tab.get('webSocketDebuggerUrl', '')
        print(f"  Tab: {tab.get('url', 'unknown')[:80]}")
        if ws_url:
            cookies = _get_cookies_via_ws(ws_url)
            sap_cookies = {c['name']: c['value'] for c in cookies
                           if 'MYSAPSSO2' in c.get('name', '') or 'SAP_' in c.get('name', '')}
            if sap_cookies:
                print(f"  Found SAP cookies: {list(sap_cookies.keys())}")
                return sap_cookies

    print("  No MYSAPSSO2 cookie found in Chrome session")
    return {}


def _get_cookies_via_ws(ws_debugger_url: str) -> list:
    """Get cookies from a Chrome tab via WebSocket CDP."""
    import websocket, threading

    result = []
    done = threading.Event()

    def on_message(ws, message):
        data = json.loads(message)
        if data.get('id') == 1:
            result.extend(data.get('result', {}).get('cookies', []))
            done.set()
            ws.close()

    def on_open(ws):
        ws.send(json.dumps({"id": 1, "method": "Network.getAllCookies"}))

    try:
        ws = websocket.WebSocketApp(ws_debugger_url, on_message=on_message, on_open=on_open)
        t = threading.Thread(target=ws.run_forever)
        t.daemon = True
        t.start()
        done.wait(timeout=5)
    except Exception as e:
        print(f"  WS error: {e}")

    return result


# ───────────────────────────────────────────────────────────
# 2. ADT API calls with SSO cookie
# ───────────────────────────────────────────────────────────

def get_adt_client(cookies: dict) -> httpx.Client:
    """Create httpx client with SAP SSO cookies."""
    return httpx.Client(
        base_url=SAP_HOST,
        cookies=cookies,
        verify=False,
        timeout=60,
        follow_redirects=True,
    )


def fetch_csrf(client: httpx.Client) -> str:
    """Fetch CSRF token from ADT discovery."""
    r = client.get(
        f"/sap/bc/adt/discovery?sap-client={CLIENT}",
        headers={"X-CSRF-Token": "Fetch", "Accept": "application/xml"}
    )
    print(f"  [CSRF] HTTP {r.status_code}")
    token = r.headers.get("X-CSRF-Token", "")
    print(f"  [CSRF] Token: {str(token)[:30]}")
    return token


def search_object(client: httpx.Client, name: str, obj_type: str = "CLAS") -> list:
    """Search for ABAP object by name."""
    r = client.get(
        f"/sap/bc/adt/repository/informationsystem/search",
        params={"sap-client": CLIENT, "query": name, "maxResults": "5", "objectType": obj_type}
    )
    print(f"  [SEARCH] HTTP {r.status_code}")
    import re
    text = r.text
    results = []
    for m in re.finditer(r'adtcore:uri="([^"]+)"[^/]*/>', text):
        results.append(m.group(1))
    return results


def lock_object(client: httpx.Client, uri: str, csrf: str) -> str:
    """Lock object for editing, return lockHandle."""
    r = client.post(
        f"{uri}?sap-client={CLIENT}&_action=LOCK&accessMode=MODIFY",
        headers={
            "X-CSRF-Token": csrf,
            "Accept": "application/vnd.sap.as+xml,application/xml"
        }
    )
    print(f"  [LOCK] HTTP {r.status_code}")
    import re
    m = re.search(r'<[^>]*:lockHandle[^>]*>([^<]+)<|lockHandle[">]*([A-Za-z0-9+/=]{20,})', r.text)
    if m:
        return (m.group(1) or m.group(2)).strip()
    if r.status_code >= 400:
        print(f"  [LOCK] Error: {r.text[:300]}")
    return r.text[:200]


def write_source(client: httpx.Client, uri: str, source: str,
                 lock_handle: str, csrf: str) -> int:
    """Write ABAP source to object."""
    r = client.put(
        f"{uri}/source/main?sap-client={CLIENT}&corrNr={TRANSPORT}",
        content=source.encode("utf-8"),
        headers={
            "X-CSRF-Token": csrf,
            "X-adtcore-locktoken": lock_handle,
            "Content-Type": "text/plain; charset=utf-8",
            "Accept": "*/*"
        }
    )
    print(f"  [WRITE] HTTP {r.status_code}")
    if r.status_code >= 300:
        print(f"  [WRITE] Response: {r.text[:300]}")
    return r.status_code


def activate_object(client: httpx.Client, uri: str, name: str,
                    type_id: str, csrf: str) -> bool:
    """Activate an ABAP object."""
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<adtcore:objects xmlns:adtcore="http://www.sap.com/adt/core"
                 xmlns:atom="http://www.w3.org/2005/Atom">
  <atom:link href="{uri}" rel="http://www.sap.com/adt/relations/activation"
    adtcore:name="{name}" adtcore:type="{type_id}" />
</adtcore:objects>"""
    r = client.post(
        f"/sap/bc/adt/activation?sap-client={CLIENT}",
        content=xml.encode("utf-8"),
        headers={
            "X-CSRF-Token": csrf,
            "Content-Type": "application/vnd.sap.adt.activation.request+xml",
            "Accept": "application/xml,application/vnd.sap.adt.activationresults+xml"
        }
    )
    print(f"  [ACT]  HTTP {r.status_code}")
    if r.status_code >= 400:
        print(f"  [ACT]  Error: {r.text[:300]}")
    return r.status_code < 400


def unlock_object(client: httpx.Client, uri: str, lock_handle: str, csrf: str):
    """Release object lock."""
    r = client.delete(
        f"{uri}?sap-client={CLIENT}&lockHandle={lock_handle}",
        headers={"X-CSRF-Token": csrf}
    )
    print(f"  [UNLOCK] HTTP {r.status_code}")


# ───────────────────────────────────────────────────────────
# Source code to deploy
# ───────────────────────────────────────────────────────────

CRP_PROCESS_REQ_IMPL = """CLASS zcl_crp_process_req IMPLEMENTATION.

  METHOD resolve_staff_from_user.
    SELECT SINGLE pernr INTO rv_staff_id
      FROM pa0001
      WHERE usrid = iv_uname
        AND endda >= sy-datum
        AND begda <= sy-datum.
    IF sy-subrc <> 0.
      rv_staff_id = space.
    ENDIF.
  ENDMETHOD.

  METHOD determine_gl_account.
    rv_gl_account = '0001004010'.
  ENDMETHOD.

  METHOD save_data.
    MODIFY zcrp_cert FROM is_cert.
    IF sy-subrc <> 0.
      INSERT zcrp_cert FROM is_cert.
    ENDIF.
    COMMIT WORK AND WAIT.
    ev_success = abap_true.
  ENDMETHOD.

ENDCLASS."""

DPC_EXT_IMPL = """CLASS zcl_z_crp_srv_dpc_ext IMPLEMENTATION.

  METHOD crpcertificateset_get_entityset.
    DATA: lt_certs TYPE TABLE OF zcrp_cert.
    DATA: ls_cert  TYPE zcrp_cert.
    DATA: ls_entity TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.

    SELECT * FROM zcrp_cert INTO TABLE lt_certs.

    LOOP AT lt_certs INTO ls_cert.
      CLEAR ls_entity.
      ls_entity-company_code    = ls_cert-bukrs.
      ls_entity-fiscal_year     = ls_cert-gjahr.
      ls_entity-certificate_id  = ls_cert-certificate_id.
      ls_entity-status          = ls_cert-status.
      ls_entity-calculated_amount = ls_cert-calc_amount.
      ls_entity-currency        = ls_cert-currency.
      APPEND ls_entity TO et_entityset.
    ENDLOOP.
  ENDMETHOD.

  METHOD crpcertificateset_create_entity.
    DATA: ls_cert   TYPE zcrp_cert.
    DATA: ls_entity TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.

    io_data_provider->read_entry_data(
      IMPORTING es_entry_data = ls_entity ).

    ls_cert-bukrs          = ls_entity-company_code.
    ls_cert-gjahr          = ls_entity-fiscal_year.
    ls_cert-certificate_id = ls_entity-certificate_id.
    ls_cert-status         = '01'.
    ls_cert-calc_amount    = ls_entity-calculated_amount.
    ls_cert-currency       = ls_entity-currency.
    ls_cert-created_by     = sy-uname.
    ls_cert-bldat          = sy-datum.

    INSERT zcrp_cert FROM ls_cert.
    IF sy-subrc <> 0.
      /iwbep/cx_mgw_busi_exception=>raise( 'Create failed' ).
    ENDIF.
    COMMIT WORK AND WAIT.
    er_entity = ls_entity.
    er_entity-status = '01'.
  ENDMETHOD.

ENDCLASS."""


def deploy_class(client: httpx.Client, csrf: str,
                 class_name: str, source: str) -> bool:
    """Full deploy: lock → write → activate → unlock."""
    uri = f"/sap/bc/adt/oo/classes/{class_name.lower()}"
    print(f"\n=== Deploying {class_name} ===")

    lock_handle = lock_object(client, uri, csrf)
    if not lock_handle or len(lock_handle) < 10:
        print(f"  Lock failed or no valid handle")
        return False

    status = write_source(client, uri, source, lock_handle, csrf)
    if status >= 400:
        unlock_object(client, uri, lock_handle, csrf)
        return False

    ok = activate_object(client, uri, class_name.upper(), "CLAS/OC", csrf)
    unlock_object(client, uri, lock_handle, csrf)
    return ok


if __name__ == "__main__":
    print("=== SAP ADT Deployment via SSO Cookie ===\n")

    # Step 1: Get SSO cookies from Chrome
    print("1. Extracting SSO cookie from Chrome browser...")
    try:
        cookies = get_sap_cookies_from_chrome()
    except Exception as e:
        print(f"  Chrome extraction failed: {e}")
        print("  Trying without cookies (may use Windows SSPI automatically)...")
        cookies = {}

    # Step 2: Create httpx client
    print("\n2. Building ADT client...")
    client = get_adt_client(cookies)

    # Step 3: Fetch CSRF token
    print("\n3. Fetching CSRF token...")
    try:
        csrf = fetch_csrf(client)
    except Exception as e:
        print(f"  FAILED: {e}")
        sys.exit(1)

    if not csrf or csrf in ("Fetch", "Required"):
        print("  No CSRF token - auth may have failed. Check cookie extraction.")
        sys.exit(1)

    # Step 4: Deploy classes
    print("\n4. Deploying ABAP classes...")
    deploy_class(client, csrf, "ZCL_CRP_PROCESS_REQ", CRP_PROCESS_REQ_IMPL)
    deploy_class(client, csrf, "ZCL_Z_CRP_SRV_DPC_EXT", DPC_EXT_IMPL)

    print("\n=== Done ===")
