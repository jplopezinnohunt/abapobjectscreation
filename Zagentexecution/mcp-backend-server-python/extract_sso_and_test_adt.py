"""
extract_sso_and_test_adt.py

1. Connects to Chrome CDP at localhost:9222
2. Extracts the MYSAPSSO2 cookie from the SAP session
3. Tests ADT discovery endpoint with that cookie
4. If successful, writes both CCIMP includes cleanly via ADT API
"""
import sys, ssl, json, base64, urllib.request, time
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
SAP_HOST = "hq-sap-d01.hq.int.unesco.org"
SAP_CLIENT = "350"

ctx_ssl = ssl.create_default_context()
ctx_ssl.check_hostname = False
ctx_ssl.verify_mode = ssl.CERT_NONE


# ── Step 1: Get MYSAPSSO2 Cookie from Chrome CDP ─────────────────────────────

def get_sso_cookie():
    """Extract MYSAPSSO2 cookie from running Chrome via CDP HTTP REST API."""
    print("[CDP] Looking for SAP tabs...")
    try:
        with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
            tabs = json.loads(r.read())
    except Exception as e:
        raise RuntimeError(f"Chrome CDP not reachable at {CDP_URL}: {e}\nRun: node launch_chrome_sap.js")

    sap_tabs = [t for t in tabs if SAP_HOST in t.get("url", "")]
    if not sap_tabs:
        # Try to get cookies from any tab via CDP WebSocket
        print(f"  No SAP tab found yet (total tabs: {len(tabs)})")
        print(f"  Tabs: {[t.get('url','')[:60] for t in tabs[:3]]}")
        return None

    print(f"  Found SAP tab: {sap_tabs[0].get('url','')[:80]}")

    # Use CDP Network.getCookies via WebSocket
    ws_url = sap_tabs[0].get("webSocketDebuggerUrl")
    if not ws_url:
        print("  No WebSocket URL - trying all cookies via /json/version")
        return None

    try:
        import websocket
        ws = websocket.create_connection(ws_url, timeout=10)
        ws.send(json.dumps({"id": 1, "method": "Network.getCookies", "params": {"urls": [f"https://{SAP_HOST}"]}}))
        resp = json.loads(ws.recv())
        ws.close()

        cookies = resp.get("result", {}).get("cookies", [])
        sso = next((c["value"] for c in cookies if c["name"] == "MYSAPSSO2"), None)
        if sso:
            print(f"  MYSAPSSO2 cookie found (length={len(sso)})")
            return sso
        else:
            names = [c["name"] for c in cookies]
            print(f"  Cookies found: {names} — MYSAPSSO2 not among them")
            return None
    except ImportError:
        print("  websocket-client not installed: pip install websocket-client")
        return None
    except Exception as e:
        print(f"  WebSocket error: {e}")
        return None


# ── Step 2: ADT Session with proper cookie/CSRF handling ─────────────────────

import http.cookiejar, urllib.parse

class ADTSession:
    """
    Maintains an ADT session using MYSAPSSO2 cookie.
    CSRF token is fetched once and reused within the same opener (session).
    """
    def __init__(self, sso_cookie: str, host: str, client: str):
        self.host   = host
        self.client = client
        self.base   = f"https://{host}"
        self.csrf   = None

        # Build opener with cookie jar
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ctx_ssl),
            urllib.request.HTTPCookieProcessor(self.jar)
        )
        # Pre-seed the MYSAPSSO2 cookie into the jar
        self._seed_cookie(sso_cookie)

    def _seed_cookie(self, value: str):
        import http.cookiejar as cj, time
        cookie = cj.Cookie(
            version=0, name="MYSAPSSO2", value=value,
            port=None, port_specified=False,
            domain=self.host, domain_specified=True, domain_initial_dot=False,
            path="/", path_specified=True, secure=True, expires=None,
            discard=False, comment=None, comment_url=None, rest={}
        )
        self.jar.set_cookie(cookie)

    def fetch_csrf(self) -> bool:
        url = f"{self.base}/sap/bc/adt/discovery?sap-client={self.client}"
        req = urllib.request.Request(url, headers={
            "X-CSRF-Token": "Fetch",
            "Accept": "application/xml",
        })
        try:
            with self.opener.open(req, timeout=10) as r:
                self.csrf = r.getheader("X-CSRF-Token", "")
                print(f"[ADT] CSRF fetched: {self.csrf[:30]}")
                return bool(self.csrf)
        except Exception as e:
            print(f"[ADT] CSRF fetch failed: {e}")
            return False

    def get(self, path: str, accept="text/plain") -> str | None:
        url = f"{self.base}{path}?sap-client={self.client}"
        req = urllib.request.Request(url, headers={"Accept": accept})
        try:
            with self.opener.open(req, timeout=10) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            print(f"  GET {path} → HTTP {e.code}")
            return None

    def post(self, path: str, data: bytes = b"", content_type="", accept="application/xml",
             extra_headers: dict = None) -> tuple[int, str]:
        url = f"{self.base}{path}?sap-client={self.client}"
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "X-CSRF-Token": self.csrf,
            "Accept": accept,
        })
        if content_type:
            req.add_header("Content-Type", content_type)
        if extra_headers:
            for k, v in extra_headers.items():
                req.add_header(k, v)
        try:
            with self.opener.open(req, timeout=30) as r:
                return r.status, r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode(errors="replace")

    def put(self, path: str, data: bytes, content_type: str, lock_handle: str) -> tuple[int, str]:
        url = f"{self.base}{path}?sap-client={self.client}"
        req = urllib.request.Request(url, data=data, method="PUT", headers={
            "X-CSRF-Token": self.csrf,
            "X-adtcore-locktoken": lock_handle,
            "Content-Type": content_type,
        })
        try:
            with self.opener.open(req, timeout=30) as r:
                return r.status, r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode(errors="replace")

    def delete(self, path: str) -> int:
        url = f"{self.base}{path}?sap-client={self.client}"
        req = urllib.request.Request(url, method="DELETE", headers={
            "X-CSRF-Token": self.csrf,
        })
        try:
            with self.opener.open(req, timeout=10) as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code

    def lock(self, class_name: str) -> tuple[str, str] | tuple[None, None]:
        # Lock the specific resource we're writing to: /source/main
        path = f"/sap/bc/adt/oo/classes/{class_name.lower()}/source/main"
        url = f"{self.base}{path}?_action=LOCK&accessMode=MODIFY&sap-client={self.client}"
        req = urllib.request.Request(url, data=b"", method="POST", headers={
            "X-CSRF-Token": self.csrf,
            "Accept": "application/xml, application/vnd.sap.as+xml",
            "Content-Length": "0",
        })
        try:
            with self.opener.open(req, timeout=10) as r:
                body = r.read().decode("utf-8", errors="replace")
                import re
                m_h = re.search(r'<LOCK_HANDLE>([^<]+)</LOCK_HANDLE>', body)
                m_c = re.search(r'<CORRNR>([^<]+)</CORRNR>', body)
                if not m_h:
                    m_h = re.search(r'lockHandle[^>]*>([^<]+)<', body, re.IGNORECASE)
                if m_h:
                    handle = m_h.group(1)
                    corrnr = m_c.group(1) if m_c else ""
                    print(f"  Locked handle: {handle[:30]}, transport: {corrnr}")
                    return handle, corrnr
                print(f"  Lock body: {body[:300]}")
                return None, None
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            print(f"  Lock HTTP {e.code}: {body[:300]}")
            return None, None


    def write_source(self, class_name: str, source: str, handle: str, corrnr: str = "") -> bool:
        path = f"/sap/bc/adt/oo/classes/{class_name.lower()}/source/main"
        data = source.encode("utf-8")
        import urllib.parse
        params = f"sap-client={self.client}&lockHandle={urllib.parse.quote(handle, safe='')}"
        if corrnr:
            params += f"&corrNr={urllib.parse.quote(corrnr, safe='')}"
        url = f"{self.base}{path}?{params}"
        req = urllib.request.Request(url, data=data, method="PUT", headers={
            "X-CSRF-Token": self.csrf,
            "X-adtcore-locktoken": handle,
            "Content-Type": "text/plain; charset=utf-8",
        })
        try:
            with self.opener.open(req, timeout=30) as r:
                body = r.read().decode("utf-8", errors="replace")
                print(f"  Write → HTTP {r.status}" + (f": {body[:80]}" if body.strip() else ""))
                return True
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            print(f"  Write → HTTP {e.code}: {body[:300]}")
            return False


    def unlock(self, class_name: str, handle: str):
        url = f"{self.base}/sap/bc/adt/oo/classes/{class_name.lower()}?_action=UNLOCK&lockHandle={handle}&sap-client={self.client}"
        req = urllib.request.Request(url, method="DELETE", headers={
            "X-CSRF-Token": self.csrf,
        })
        try:
            with self.opener.open(req, timeout=10) as r:
                print(f"  Unlocked: HTTP {r.status}")
        except urllib.error.HTTPError as e:
            print(f"  Unlock HTTP {e.code}")

    def activate(self, class_name: str) -> bool:
        body = f'''<?xml version="1.0" encoding="utf-8"?>
<adtcore:objects xmlns:adtcore="http://www.sap.com/adt/core"
                 xmlns:atom="http://www.w3.org/2005/Atom">
  <atom:link href="/sap/bc/adt/oo/classes/{class_name.lower()}"
    rel="http://www.sap.com/adt/relations/activation"
    adtcore:name="{class_name.upper()}"
    adtcore:type="CLAS/OC" />
</adtcore:objects>'''
        status, resp = self.post(
            "/sap/bc/adt/activation?method=activate",
            data=body.encode("utf-8"),
            content_type="application/vnd.sap.adt.activation.request+xml; charset=utf-8",
        )
        print(f"  Activate → HTTP {status}" + (f": {resp[:200]}" if resp.strip() else ""))
        return status in (200, 204)

    def deploy_class(self, class_name: str, source: str) -> bool:
        print(f"\n--- {class_name} ---")
        old = self.get(f"/sap/bc/adt/oo/classes/{class_name.lower()}/source/main")
        if old:
            print(f"  Current: {len(old.splitlines())} lines")

        handle, corrnr = self.lock(class_name)
        if not handle:
            return False

        ok = self.write_source(class_name, source, handle, corrnr)
        self.unlock(class_name, handle)
        if ok:
            self.activate(class_name)
        return ok



# ── Source code ───────────────────────────────────────────────────────────────

CRP_SOURCE = """\
CLASS zcl_crp_process_req IMPLEMENTATION.

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

ENDCLASS.
"""

DPC_SOURCE = """\
CLASS zcl_z_crp_srv_dpc_ext IMPLEMENTATION.

  METHOD crpcertificateset_get_entityset.
    DATA: lt_certs TYPE TABLE OF zcrp_cert.
    DATA: ls_cert  TYPE zcrp_cert.
    DATA: ls_entity TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.
    SELECT * FROM zcrp_cert INTO TABLE lt_certs.
    LOOP AT lt_certs INTO ls_cert.
      CLEAR ls_entity.
      ls_entity-company_code   = ls_cert-bukrs.
      ls_entity-fiscal_year    = ls_cert-gjahr.
      ls_entity-certificate_id = ls_cert-certificate_id.
      ls_entity-status         = ls_cert-status.
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
    INSERT zcrp_cert FROM ls_cert.
    IF sy-subrc <> 0.
      /iwbep/cx_mgw_busi_exception=>raise( 'Create failed' ).
    ENDIF.
    COMMIT WORK AND WAIT.
    er_entity = ls_entity.
    er_entity-status = '01'.
  ENDMETHOD.

ENDCLASS.
"""


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== ADT via MYSAPSSO2 Cookie ===\n")

    print("Step 1: Extracting SSO cookie from Chrome...")
    time.sleep(2)
    cookie = get_sso_cookie()

    if not cookie:
        print("\nNo SSO cookie yet — is Chrome fully loaded and showing SAP WebGUI?")
        sys.exit(1)

    print("\nStep 2: Building ADT session...")
    session = ADTSession(cookie, SAP_HOST, SAP_CLIENT)
    if not session.fetch_csrf():
        print("ADT authentication failed.")
        sys.exit(1)

    print("\nStep 3: Writing CCIMP sources via ADT...")
    session.deploy_class("ZCL_CRP_PROCESS_REQ", CRP_SOURCE)
    session.deploy_class("ZCL_Z_CRP_SRV_DPC_EXT", DPC_SOURCE)

    print("\n=== Done ===")
