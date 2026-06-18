"""
sap_adt_client.py — Comprehensive SAP ADT REST API Client (urllib-only, no extra deps)

Implements the same workflow used by the VSCode ABAP Extension and mcp-abap-abap-adt-api:
  1. Authenticate (Basic Auth + CSRF token fetch)
  2. Search object → get URI
  3. Read source  (GET /sap/bc/adt/.../source/main)
  4. Lock object  (POST ?_action=LOCK)
  5. Write source (PUT /sap/bc/adt/.../source/main)
  6. Syntax check (POST /sap/bc/adt/checkruns)
  7. Activate     (POST /sap/bc/adt/activation)
  8. Unlock       (DELETE /sap/bc/adt/locks/{lockHandle})

Supported ABAP object types and their URI patterns:
  CLASS      /sap/bc/adt/oo/classes/{name}
  INTF       /sap/bc/adt/oo/interfaces/{name}
  PROG       /sap/bc/adt/programs/programs/{name}
  INCLUDE    /sap/bc/adt/programs/includes/{name}
  FUGR       /sap/bc/adt/functions/groups/{name}
  FUNC       /sap/bc/adt/functions/groups/{fg}/fmodules/{name}
  BSP        /sap/bc/adt/bsp/applications/{app}/pages/{page}
  TABL       /sap/bc/adt/ddic/tables/{name}
  DTEL       /sap/bc/adt/ddic/dataelements/{name}
  DOMA       /sap/bc/adt/ddic/domains/{name}
  TTYP       /sap/bc/adt/ddic/tabletypes/{name}
  ENHO       /sap/bc/adt/enhancements/{name}
  SRVB       /sap/bc/adt/businessservices/binding/{name}         (OData service binding)
  IWSV       /sap/bc/adt/gwservices/groups/{name}                (Gateway service)
  XSLT       /sap/bc/adt/xslt/{name}
  WDYN       /sap/bc/adt/wdy/components/{name}
"""

import os
import base64
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
from typing import Optional
# NOTE: load_dotenv() is NOT called at module level to avoid Windows
# pyrfc DLL heap corruption (0xC0000374). Call it inside from_env() instead.

class SAPADTClient:
    """
    SAP ADT REST API client.
    Uses Basic Auth. CSRF token is fetched on first write operation.
    Session is kept stateful via a cookie jar.
    """

    def __init__(self, host: str, client: str, user: str, password: str,
                 verify_ssl: bool = False, port: int = 443, https: bool = True):
        scheme = "https" if https else "http"
        self.base_url = f"{scheme}://{host}:{port}"
        self.client = client
        self.user = user
        self.password = password
        self._csrf_token: Optional[str] = None
        self._session_cookies: dict = {}

        # SSL context
        if not verify_ssl:
            self._ssl_ctx = ssl.create_default_context()
            self._ssl_ctx.check_hostname = False
            self._ssl_ctx.verify_mode = ssl.CERT_NONE
        else:
            self._ssl_ctx = None

        # Authorization header
        creds = base64.b64encode(f"{user}:{password}".encode()).decode()
        self._auth_header = f"Basic {creds}"

    def _build_url(self, path: str, params: dict = None) -> str:
        url = f"{self.base_url}{path}?sap-client={self.client}"
        if params:
            url += "&" + urllib.parse.urlencode(params)
        return url

    def _get_headers(self, extra: dict = None) -> dict:
        h = {
            "Authorization": self._auth_header,
            "Accept": "application/xml,application/json;q=0.9,*/*;q=0.8",
            "X-CSRF-Token": self._csrf_token or "Fetch",
        }
        if self._session_cookies:
            cookie_str = "; ".join(f"{k}={v}" for k, v in self._session_cookies.items())
            h["Cookie"] = cookie_str
        if extra:
            h.update(extra)
        return h

    def _parse_set_cookie(self, response):
        cookies = response.getheader("Set-Cookie") or ""
        for part in cookies.split(","):
            part = part.strip()
            kv = part.split(";")[0]
            if "=" in kv:
                k, v = kv.split("=", 1)
                self._session_cookies[k.strip()] = v.strip()

    def _request(self, method: str, path: str, body: bytes = None,
                 params: dict = None, extra_headers: dict = None,
                 content_type: str = None, raise_on_error: bool = True) -> tuple[int, bytes, dict]:
        """
        Execute an HTTP request.
        Returns (status_code, response_body, response_headers_dict).
        """
        url = self._build_url(path, params)
        headers = self._get_headers(extra_headers)
        if content_type:
            headers["Content-Type"] = content_type

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=60) as resp:
                status = resp.status
                body_data = resp.read()
                # Capture CSRF token from response
                new_csrf = resp.getheader("X-CSRF-Token")
                if new_csrf:
                    self._csrf_token = new_csrf
                self._parse_set_cookie(resp)
                resp_headers = dict(resp.headers)
                return status, body_data, resp_headers
        except urllib.error.HTTPError as e:
            body_data = e.read()
            # NOTE: Do NOT store X-CSRF-Token from error responses. SAP echoes a
            # token even on 401, which previously poisoned self._csrf_token and
            # made fetch_csrf() appear to succeed (silent-401 bug, session #75
            # retro). Only success responses (handled above) update the token.
            if raise_on_error:
                if e.code in (401, 403):
                    raise PermissionError(
                        f"SAP ADT Authentication/Authorization failed (HTTP {e.code}) for user '{self.user}'. "
                        f"Please check your credentials in .env or SAP ICF service settings. "
                        f"Details: {body_data.decode('utf-8', errors='replace')[:200]}"
                    )
                else:
                    raise urllib.error.HTTPError(
                        e.url, e.code,
                        f"SAP ADT request failed (HTTP {e.code}): {body_data.decode('utf-8', errors='replace')[:200]}",
                        e.headers, e.fp
                    )
            return e.code, body_data, dict(e.headers)

    def fetch_csrf(self) -> str:
        """Fetch CSRF token via HEAD request to discovery endpoint.

        Raises RuntimeError if the discovery call did not authenticate
        (e.g., HTTP 401 from SICF/SU01 misconfiguration). Previously this
        method returned an empty token silently because SAP echoes a CSRF
        token in 401 responses too — see session #75 retro.
        """
        print("  [ADT] Fetching CSRF token...")
        self._csrf_token = None  # clear any prior value before probing
        status, body, headers = self._request(
            "GET", "/sap/bc/adt/discovery",
            extra_headers={"X-CSRF-Token": "Fetch"},
        )
        if status != 200 or not self._csrf_token:
            preview = (body or b"").decode("utf-8", errors="replace")[:200]
            raise RuntimeError(
                f"ADT CSRF fetch did not return a usable token "
                f"(HTTP {status}, csrf_present={bool(self._csrf_token)}). "
                f"Body preview: {preview!r}. "
                f"This is the documented silent-401 condition — verify SICF "
                f"/sap/bc/adt and SU01 user type for {self.user}. "
                f"See knowledge/session_retros/session_075_retro.md."
            )
        print(f"  [ADT] CSRF token obtained: {self._csrf_token[:20]}...")
        return self._csrf_token

    # ── OBJECT SEARCH ──────────────────────────────────────────────────────────

    def search_object(self, query: str, obj_type: str = None,
                      max_results: int = 10) -> list[dict]:
        """
        Search for ABAP objects by name.
        obj_type: CLASS, INTF, PROG, FUGR, FUNC, TABL, DTEL, DOMA, TTYP, IWSV, SRVB, BSP
        Returns list of {name, type, packageName, uri}
        """
        params = {"operation": "quickSearch", "query": query, "maxResults": max_results}
        if obj_type:
            params["objectType"] = obj_type
        status, body, _ = self._request(
            "GET", "/sap/bc/adt/repository/informationsystem/search", params=params,
            extra_headers={"Accept": "application/xml"}
        )
        # Parse XML for URIs
        objects = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(body)
            for elem in root.iter():
                if elem.tag.endswith('objectReference'):
                    attribs = {k.split('}')[-1]: v for k, v in elem.attrib.items()}
                    if "uri" in attribs and "name" in attribs:
                        objects.append({
                            "uri": attribs.get("uri"),
                            "name": attribs.get("name"),
                            "type": attribs.get("type", "")
                        })
        except Exception:
            import re
            text = body.decode("utf-8", errors="replace")
            for m in re.finditer(r'adtcore:uri="([^"]+)"', text):
                uri = m.group(1)
                # Quick extract name/type from surrounding tag if XML parser fails
                name_match = re.search(r'adtcore:name="([^"]+)"', m.group(0))
                type_match = re.search(r'adtcore:type="([^"]+)"', m.group(0))
                objects.append({
                    "uri": uri,
                    "name": name_match.group(1) if name_match else "",
                    "type": type_match.group(1) if type_match else ""
                })
        return objects

    # ── SOURCE READ ────────────────────────────────────────────────────────────

    def get_source(self, object_uri: str) -> str:
        """Read ABAP source code from object URI (appends /source/main)."""
        source_url = f"{object_uri}/source/main"
        status, body, _ = self._request(
            "GET", source_url,
            extra_headers={"Accept": "text/plain"}
        )
        return body.decode("utf-8", errors="replace")

    # ── LOCK / UNLOCK ──────────────────────────────────────────────────────────

    def lock(self, object_uri: str) -> str:
        """Lock object for editing. Returns lockHandle."""
        if not self._csrf_token:
            self.fetch_csrf()
        status, body, headers = self._request(
            "POST", object_uri,
            params={"_action": "LOCK", "accessMode": "MODIFY"},
            extra_headers={"Accept": "application/vnd.sap.as+xml, application/xml"}
        )
        # Extract lockHandle from response
        text = body.decode("utf-8", errors="replace")
        import re
        m = re.search(r'<[^>]*:lockHandle[^>]*>([^<]+)<', text)
        if not m:
            m = re.search(r'lockHandle[">:]*([A-Za-z0-9+/=]{20,})', text)
        if m:
            lh = m.group(1).strip()
            print(f"  [ADT] Lock obtained: {lh[:30]}...")
            return lh
        # Try JSON
        try:
            data = json.loads(text)
            return data.get("lockHandle", data.get("LOCKHANDLE", ""))
        except:
            pass
        raise RuntimeError(f"Lock failed (HTTP {status}): {text[:200]}")

    def unlock(self, object_uri: str, lock_handle: str):
        """Release object lock."""
        encoded_handle = urllib.parse.quote(lock_handle, safe="")
        status, body, _ = self._request(
            "DELETE", f"/sap/bc/adt/locks/{encoded_handle}",
            extra_headers={"X-adtcore-locktoken": lock_handle}
        )
        print(f"  [ADT] Unlock status: {status}")

    # ── SOURCE WRITE ───────────────────────────────────────────────────────────

    def set_source(self, object_uri: str, source: str, lock_handle: str,
                   transport: str = "") -> int:
        """Write ABAP source to object. Returns HTTP status."""
        import os as _os
        if _os.getenv("ALLOW_D01_WRITES") != "1":
            raise RuntimeError(
                "D01 WRITES DISABLED (INC-CLASS-LOSS 2026-06-12). ADT source "
                "writes are blocked after class-corruption incident. See "
                "knowledge/incidents/INC-CLASS-LOSS-2026-06_adt_rfc_write_corruption.md")
        if not self._csrf_token:
            self.fetch_csrf()
        source_url = f"{object_uri}/source/main"
        params = {}
        if transport:
            params["corrNr"] = transport
        status, body, _ = self._request(
            "PUT", source_url,
            body=source.encode("utf-8"),
            params=params,
            extra_headers={
                "X-adtcore-locktoken": lock_handle,
                "Content-Type": "text/plain; charset=utf-8",
            }
        )
        print(f"  [ADT] Set source status: {status}")
        if status >= 400:
            print(f"  [ADT] Error: {body.decode('utf-8', errors='replace')[:300]}")
        return status

    # ── SYNTAX CHECK ───────────────────────────────────────────────────────────

    def syntax_check(self, source: str, object_uri: str = "",
                     main_program: str = "") -> list[dict]:
        """Run syntax check on ABAP source. Returns list of issues."""
        if not self._csrf_token:
            self.fetch_csrf()
        xml_body = f"""<?xml version="1.0" encoding="utf-8"?>
<checkObject:checkObjectList xmlns:checkObject="http://www.sap.com/adt/checkobject">
  <checkObject:checkObject checkObject:object="programInclude"
    adtcore:objectTypeId="CLAS/OC" adtcore:uri="{object_uri}">
    <checkObject:source>{source.replace('<','&lt;').replace('>','&gt;')}</checkObject:source>
  </checkObject:checkObject>
</checkObject:checkObjectList>"""
        status, body, _ = self._request(
            "POST", "/sap/bc/adt/checkruns",
            body=xml_body.encode("utf-8"),
            extra_headers={"Accept": "application/xml",
                           "Content-Type": "application/vnd.sap.adt.checkobjects+xml"}
        )
        text = body.decode("utf-8", errors="replace")
        import re
        issues = []
        for m in re.finditer(r'<[^>]*message[^>]*>([^<]+)<', text, re.IGNORECASE):
            issues.append({"message": m.group(1)})
        return issues

    # ── ACTIVATION ─────────────────────────────────────────────────────────────

    def activate(self, object_uri: str, object_name: str, obj_type_id: str = "CLAS/OC") -> bool:
        """
        Activate ABAP object via ADT activation API.
        obj_type_id examples: CLAS/OC (class), PROG/P (program), FUGR/FF (func group)
        """
        if not self._csrf_token:
            self.fetch_csrf()
        xml_body = f"""<?xml version="1.0" encoding="utf-8"?>
<adtcore:objects xmlns:adtcore="http://www.sap.com/adt/core" xmlns:atom="http://www.w3.org/2005/Atom">
  <atom:link href="{object_uri}" rel="http://www.sap.com/adt/relations/activation"
    adtcore:name="{object_name}" adtcore:type="{obj_type_id}" />
</adtcore:objects>"""
        status, body, _ = self._request(
            "POST", "/sap/bc/adt/activation",
            body=xml_body.encode("utf-8"),
            extra_headers={"Accept": "application/xml,application/vnd.sap.adt.activationresults+xml",
                           "Content-Type": "application/vnd.sap.adt.activation.request+xml"}
        )
        text = body.decode("utf-8", errors="replace")
        print(f"  [ADT] Activate status: {status}")
        if status >= 400 or "error" in text.lower():
            print(f"  [ADT] Activate response: {text[:500]}")
            return False
        return True

    # ── TRANSPORT INFO ─────────────────────────────────────────────────────────

    def transport_info(self, object_uri: str) -> dict:
        """Get transport (workbench request) info for an object."""
        status, body, _ = self._request(
            "GET", f"{object_uri}",
            params={"_action": "TRANSPORTINFO"},
            extra_headers={"Accept": "application/vnd.sap.adt.transportinfo+xml"}
        )
        text = body.decode("utf-8", errors="replace")
        import re
        m = re.search(r'TRKORR="([^"]+)"', text)
        trkorr = m.group(1) if m else ""
        return {"raw": text[:300], "trkorr": trkorr}

    # ── HIGH-LEVEL OBJECT HELPERS ──────────────────────────────────────────────

    def write_class_source(self, class_name: str, source: str,
                           transport: str = "") -> bool:
        """Full workflow: lock → write → activate → unlock for an ABAP class."""
        uri = f"/sap/bc/adt/oo/classes/{class_name.lower()}"
        print(f"\n[ADT] Writing class {class_name}...")
        try:
            lock_handle = self.lock(uri)
            self.set_source(uri, source, lock_handle, transport)
            issues = self.syntax_check(source, uri)
            if issues:
                print(f"  [ADT] Syntax issues: {issues[:3]}")
            self.activate(uri, class_name, "CLAS/OC")
            self.unlock(uri, lock_handle)
            return True
        except Exception as e:
            print(f"  [ADT] FAILED: {e}")
            return False

    def write_program_source(self, prog_name: str, source: str,
                             transport: str = "") -> bool:
        """Write and activate an ABAP program."""
        uri = f"/sap/bc/adt/programs/programs/{prog_name.lower()}"
        print(f"\n[ADT] Writing program {prog_name}...")
        try:
            lock_handle = self.lock(uri)
            self.set_source(uri, source, lock_handle, transport)
            self.activate(uri, prog_name, "PROG/P")
            self.unlock(uri, lock_handle)
            return True
        except Exception as e:
            print(f"  [ADT] FAILED: {e}")
            return False

    def write_include_source(self, include_name: str, source: str,
                             transport: str = "") -> bool:
        """Write and activate an ABAP include."""
        uri = f"/sap/bc/adt/programs/includes/{include_name.lower()}"
        print(f"\n[ADT] Writing include {include_name}...")
        try:
            lock_handle = self.lock(uri)
            self.set_source(uri, source, lock_handle, transport)
            self.activate(uri, include_name, "PROG/I")
            self.unlock(uri, lock_handle)
            return True
        except Exception as e:
            print(f"  [ADT] FAILED: {e}")
            return False

    def write_function_source(self, func_group: str, func_name: str,
                              source: str, transport: str = "") -> bool:
        """Write and activate a function module source."""
        uri = f"/sap/bc/adt/functions/groups/{func_group.lower()}/fmodules/{func_name.lower()}"
        print(f"\n[ADT] Writing function {func_name} in {func_group}...")
        try:
            lock_handle = self.lock(uri)
            self.set_source(uri, source, lock_handle, transport)
            self.activate(uri, func_name, "FUGR/FF")
            self.unlock(uri, lock_handle)
            return True
        except Exception as e:
            print(f"  [ADT] FAILED: {e}")
            return False

    # ── DATA PREVIEW (OSQL QUERY) ───────────────────────────────────────────────

    def data_preview(self, sql_query: str, max_rows: int = 100) -> list[dict]:
        """
        Run an Open SQL / OSQL query against SAP tables via ADT Data Preview.
        Example: SELECT * FROM TADIR WHERE OBJECT = 'CLAS' UP TO 10 ROWS
        Returns list of row dicts.
        """
        import urllib.parse
        url = f"/sap/bc/adt/datapreview/freestyle"
        params = {"rowNumber": str(max_rows), "dataPreviewParameters": "undefined"}
        status, body, _ = self._request(
            "POST", url,
            body=sql_query.encode("utf-8"),
            params=params,
            extra_headers={
                "Content-Type": "text/plain;charset=UTF-8",
                "Accept": "application/xml",
            }
        )
        import re
        text = body.decode("utf-8", errors="replace")
        # Parse <dataPreview:row> blocks → return list of column→value dicts
        rows = []
        for row_block in re.findall(r'<dataPreview:row[^>]*>(.*?)</dataPreview:row>', text, re.DOTALL):
            row = {}
            for col_m in re.finditer(r'<dataPreview:column[^>]*keyAttribute="([^"]*)"[^>]*isKey="[^"]*"[^>]*>([^<]*)</dataPreview:column>', row_block):
                pass
            for col_m in re.finditer(r'<[^>]*:column[^>]*name="([^"]+)"[^>]*>([^<]*)<', row_block):
                row[col_m.group(1)] = col_m.group(2).strip()
            if row:
                rows.append(row)
        print(f"  [ADT] Data preview: HTTP {status}, {len(rows)} rows, SQL: {sql_query[:80]}")
        if not rows and status == 200:
            print(f"  [ADT] Raw preview (first 500): {text[:500]}")
        return rows

    # ── PACKAGE TREE BROWSER ────────────────────────────────────────────────────

    def get_package_tree(self, package: str = None) -> list[dict]:
        """
        Browse the SAP object repository tree.
        package=None → top level. package='ZHRBENEFITS_FIORI' → contents of that package.
        Returns list of {name, type, description, uri}
        """
        import re
        params = {}
        if package:
            params["parent"] = f"/sap/bc/adt/packages/{package}"
        else:
            params["parent"] = "/sap/bc/adt/repository/root"
        status, body, _ = self._request(
            "GET", "/sap/bc/adt/repository/nodestructure",
            params=params,
            extra_headers={"Accept": "application/vnd.sap.as+xml"}
        )
        text = body.decode("utf-8", errors="replace")
        items = []
        for m in re.finditer(r'<[^>]*:node[^>]*name="([^"]+)"[^>]*type="([^"]+)"[^>]*objectUri="([^"]+)"', text):
            items.append({"name": m.group(1), "type": m.group(2), "uri": m.group(3)})
        print(f"  [ADT] Package tree '{package or 'root'}': {len(items)} items (HTTP {status})")
        return items

    # ── TRANSPORT MANAGEMENT (CTS) ──────────────────────────────────────────────

    def get_transports(self, user: str = None) -> list[dict]:
        """List open CTS transport requests for user (or current user)."""
        import re
        params = {}
        if user:
            params["user"] = user
        params["category"] = "Workbench"
        params["status"] = "D"   # D = Modifiable (open)
        status, body, _ = self._request(
            "GET", "/sap/bc/adt/cts/transportrequests",
            params=params,
            extra_headers={"Accept": "application/xml"}
        )
        text = body.decode("utf-8", errors="replace")
        transports = []
        for m in re.finditer(r'<[^>]*:transportRequest[^>]*trkorr="([^"]+)"[^>]*description="([^"]*)"', text):
            transports.append({"trkorr": m.group(1), "description": m.group(2)})
        print(f"  [ADT] Transports: {len(transports)} open requests (HTTP {status})")
        return transports

    # ── BSP / UI5 FILE UPLOAD (DEPLOY) ─────────────────────────────────────────

    def upload_bsp_file(self, app_name: str, file_path: str,
                        content: str, transport: str = "") -> int:
        """
        Upload/update a single file inside a BSP/UI5 app via ADT file store.

        app_name  : e.g. 'ZHROFFBOARDING'
        file_path : relative path e.g. 'manifest.json' or 'controller/Main.controller.js'
        content   : file text content
        transport : CTS transport request number (optional)

        Workflow: LOCK → PUT content → ACTIVATE → UNLOCK
        Returns HTTP status of the PUT.
        """
        import urllib.parse
        # Build the filestore URI for lock/unlock
        encoded = urllib.parse.quote(f"{app_name}/{file_path}", safe="")
        obj_uri = f"/sap/bc/adt/filestore/ui5-bsp/objects/{encoded}"
        content_uri = f"{obj_uri}/content"

        print(f"  [ADT] Uploading {app_name}/{file_path}...")
        if not self._csrf_token:
            self.fetch_csrf()

        # Lock
        params = {"_action": "LOCK", "accessMode": "MODIFY"}
        if transport:
            params["corrNr"] = transport
        lk_status, lk_body, _ = self._request("POST", obj_uri, params=params,
            extra_headers={"Accept": "application/vnd.sap.as+xml,application/xml"})
        lk_text = lk_body.decode("utf-8", errors="replace")
        import re
        m = re.search(r'<[^>]*:lockHandle[^>]*>([^<]+)<', lk_text)
        if not m:
            m = re.search(r'lockHandle[">:]*([A-Za-z0-9+/=]{20,})', lk_text)
        if not m:
            print(f"  [ADT] Lock failed (HTTP {lk_status}): {lk_text[:200]}")
            return lk_status
        lock_handle = m.group(1).strip()
        print(f"  [ADT] Lock: {lock_handle[:30]}...")

        # PUT content
        put_params = {}
        if transport:
            put_params["corrNr"] = transport
        status, body, _ = self._request(
            "PUT", content_uri,
            body=content.encode("utf-8"),
            params=put_params,
            extra_headers={
                "X-adtcore-locktoken": lock_handle,
                "Content-Type": "application/octet-stream",
            }
        )
        print(f"  [ADT] PUT status: {status}")

        # Activate
        act_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<adtcore:objects xmlns:adtcore="http://www.sap.com/adt/core" xmlns:atom="http://www.w3.org/2005/Atom">
  <atom:link href="{obj_uri}" rel="http://www.sap.com/adt/relations/activation"
    adtcore:name="{app_name}/{file_path}" adtcore:type="WAPA" />
</adtcore:objects>"""
        self._request("POST", "/sap/bc/adt/activation",
            body=act_xml.encode("utf-8"),
            extra_headers={"X-adtcore-locktoken": lock_handle,
                           "Content-Type": "application/vnd.sap.adt.activation.request+xml"})

        # Unlock
        encoded_lh = urllib.parse.quote(lock_handle, safe="")
        self._request("DELETE", f"/sap/bc/adt/locks/{encoded_lh}",
            extra_headers={"X-adtcore-locktoken": lock_handle})

        return status

    # ── MONITORING: ABAP RUNTIME DUMPS (ST22) ──────────────────────────────────

    def get_runtime_dumps(self, max_rows: int = 20) -> list[dict]:
        """
        List recent ABAP runtime short dumps (ST22).
        Returns list of {date, time, user, error, program}
        """
        import re
        status, body, _ = self._request(
            "GET", "/sap/bc/adt/runtime/dumps",
            params={"maxEntries": str(max_rows)},
            extra_headers={"Accept": "application/xml"}
        )
        text = body.decode("utf-8", errors="replace")
        dumps = []
        for m in re.finditer(r'<[^>]*:dump[^>]*date="([^"]+)"[^>]*time="([^"]*)"[^>]*user="([^"]*)"[^>]*error="([^"]*)"', text):
            dumps.append({"date": m.group(1), "time": m.group(2),
                          "user": m.group(3), "error": m.group(4)})
        # Fallback: try attribute-only elements
        if not dumps:
            for m in re.finditer(r'date="([^"]+)"[^/]*time="([^"]*)"[^/]*user="([^"]*)"[^/]*', text):
                dumps.append({"date": m.group(1), "time": m.group(2), "user": m.group(3)})
        print(f"  [ADT] Runtime dumps: {len(dumps)} entries (HTTP {status})")
        return dumps

    # ── MONITORING: ABAP RUNTIME TRACES ────────────────────────────────────────

    def get_runtime_traces(self, max_rows: int = 20) -> list[dict]:
        """
        List ABAP runtime performance traces.
        Returns list of trace entries.
        """
        import re
        status, body, _ = self._request(
            "GET", "/sap/bc/adt/runtime/traces/abaptraces",
            params={"maxEntries": str(max_rows)},
            extra_headers={"Accept": "application/xml"}
        )
        text = body.decode("utf-8", errors="replace")
        traces = []
        for m in re.finditer(r'<[^>]*:trace[^>]*/>', text):
            traces.append({"raw": m.group(0)[:150]})
        print(f"  [ADT] Runtime traces: {len(traces)} entries (HTTP {status})")
        if not traces:
            print(f"  [ADT] Trace response preview: {text[:300]}")
        return traces

    # ── MONITORING: ABAP UNIT TEST RUNNER ──────────────────────────────────────

    def run_unit_tests(self, object_uri: str) -> dict:
        """
        Run ABAP Unit tests for a class or program.
        Returns dict with {passed, failed, errors, raw}
        """
        import re
        xml_body = f"""<?xml version="1.0" encoding="utf-8"?>
<aunit:run xmlns:aunit="http://www.sap.com/adt/aunit">
  <aunit:options>
    <aunit:measurements type="coverage"/>
    <aunit:scope ownTests="true" foreignTests="false"/>
  </aunit:options>
  <osl:objectSet xmlns:osl="http://www.sap.com/adt/osl">
    <osl:softwareComponents/>
    <osl:adtobjects>
      <adtcore:adtobject xmlns:adtcore="http://www.sap.com/adt/core"
        adtcore:uri="{object_uri}" adtcore:type="CLAS/OC"/>
    </osl:adtobjects>
  </osl:objectSet>
</aunit:run>"""
        if not self._csrf_token:
            self.fetch_csrf()
        status, body, _ = self._request(
            "POST", "/sap/bc/adt/abapunit/testruns",
            body=xml_body.encode("utf-8"),
            extra_headers={
                "Content-Type": "application/vnd.sap.adt.abapunit.testruns+xml",
                "Accept": "application/vnd.sap.adt.abapunit.testruns.result+xml",
            }
        )
        text = body.decode("utf-8", errors="replace")
        result = {
            "status": status,
            "passed": len(re.findall(r'result="passed"', text, re.IGNORECASE)),
            "failed": len(re.findall(r'result="failed"', text, re.IGNORECASE)),
            "errors": len(re.findall(r'<[^>]*:error', text, re.IGNORECASE)),
            "raw": text[:600]
        }
        print(f"  [ADT] Unit tests: HTTP {status} | Passed: {result['passed']} | Failed: {result['failed']}")
        return result

    # ── ABAPGIT REPOS ───────────────────────────────────────────────────────────

    def get_abapgit_repos(self) -> list[dict]:
        """List abapGit repositories linked in this SAP system."""
        import re
        status, body, _ = self._request(
            "GET", "/sap/bc/adt/abapgit/repos",
            extra_headers={"Accept": "application/json, application/xml"}
        )
        text = body.decode("utf-8", errors="replace")
        repos = []
        # Try JSON
        try:
            import json
            data = json.loads(text)
            for r in (data if isinstance(data, list) else data.get("repositories", [])):
                repos.append({"url": r.get("url",""), "package": r.get("sapPackage",""), "branch": r.get("branch","")})
        except:
            for m in re.finditer(r'url="([^"]+)"[^>]*package="([^"]+)"', text):
                repos.append({"url": m.group(1), "package": m.group(2)})
        print(f"  [ADT] abapGit repos: {len(repos)} (HTTP {status})")
        return repos

    # ── OBJECT TYPE REGISTRY ────────────────────────────────────────────────────

    def get_object_types(self) -> list[dict]:
        """List all known ABAP object types in this system (full type ID registry)."""
        import re
        status, body, _ = self._request(
            "GET", "/sap/bc/adt/repository/informationsystem/objecttypes",
            params={"maxItemCount": "999", "name": "*", "data": "usedByProvider"},
            extra_headers={"Accept": "application/xml"}
        )
        text = body.decode("utf-8", errors="replace")
        types = []
        for m in re.finditer(r'<[^>]*:objectType[^>]*id="([^"]+)"[^>]*category="([^"]*)"', text):
            types.append({"id": m.group(1), "category": m.group(2)})
        print(f"  [ADT] Object types: {len(types)} registered (HTTP {status})")
        return types

    # ══════════════════════════════════════════════════════════════════════════
    # ADT EXPANSION (session #076, 2026-05-24) — strictly additive.
    # No existing public method semantics changed. New methods cover:
    #   - adt_discovery()                : capability self-introspection
    #   - create_object() + DDIC helpers : TABL, DTEL, DOMA, structure, INTF,
    #                                      MSAG, FUGR/F, package, interface
    #   - class_include_uri / set_class_include_source / create_test_include
    #                                    : proper CCIMP/CCDEF/CCMAC/CCAU URI
    #                                      scheme (closes 7 write_ccimp_*.py
    #                                      historical workarounds)
    #   - create_transport / transport_release
    #   - debugger_*                     : set_breakpoint, listen, attach,
    #                                      step, stack, variables, set_variable
    #   - atc_run / atc_worklist         : code inspector quality gate
    # NOT covered (ADT has no public REST endpoint) — use Playwright SAPGUI:
    #   - BOR / Business Object Repository (SWO1)
    #   - SWDD Workflow Builder, SWE2/SWEC event linkages
    # ══════════════════════════════════════════════════════════════════════════

    # ── CAPABILITY DISCOVERY ───────────────────────────────────────────────────
    def adt_discovery(self) -> list[dict]:
        """List ADT collections (endpoints) this server actually exposes.

        Returns one entry per Atom collection from /sap/bc/adt/discovery.
        Call once at startup to learn which features are reachable on the
        specific NW kernel — e.g., RAP generator only on S/4 HANA, debugger
        listener requires BC-DWB-AIE 7.40+.
        """
        import re
        status, body, _ = self._request(
            "GET", "/sap/bc/adt/discovery",
            extra_headers={"Accept": "application/atomsvc+xml,application/xml"},
            raise_on_error=False,
        )
        text = body.decode("utf-8", errors="replace")
        collections = []
        for m in re.finditer(
            r'<[^>]*collection[^>]*href="([^"]+)"[^>]*>.*?<[^>]*title[^>]*>([^<]+)<',
            text, re.DOTALL,
        ):
            collections.append({"href": m.group(1), "title": m.group(2).strip()})
        print(f"  [ADT] Discovery: {len(collections)} collections (HTTP {status})")
        return collections

    # ── GENERIC OBJECT CREATION ────────────────────────────────────────────────
    # Source: marcellourbani/abap-adt-api/src/api/objectcreator.ts (MIT), verified
    # against ADT REST surface 2026-05-24.
    _CREATABLE_TYPES = {
        "PROG/P":  {"path": "programs/programs",            "ns": "program",  "root": "program:abapProgram",               "max": 30},
        "CLAS/OC": {"path": "oo/classes",                   "ns": "class",    "root": "class:abapClass",                   "max": 30},
        "INTF/OI": {"path": "oo/interfaces",                "ns": "intf",     "root": "intf:abapInterface",                "max": 30},
        "PROG/I":  {"path": "programs/includes",            "ns": "include",  "root": "include:abapInclude",               "max": 30},
        "FUGR/F":  {"path": "functions/groups",             "ns": "group",    "root": "group:abapFunctionGroup",           "max": 26},
        "FUGR/FF": {"path": "functions/groups/%s/fmodules", "ns": "fmodule",  "root": "fmodule:abapFunctionModule",        "max": 30},
        "FUGR/I":  {"path": "functions/groups/%s/includes", "ns": "finclude", "root": "finclude:abapFunctionGroupInclude", "max":  3},
        "DEVC/K":  {"path": "packages",                     "ns": "pak",      "root": "pak:package",                       "max": 30},
        "TABL/DT": {"path": "ddic/tables",                  "ns": "tabl",     "root": "blue:wbobject",                     "max": 16},
        "TABL/DS": {"path": "ddic/structures",              "ns": "tabl",     "root": "blue:wbobject",                     "max": 16},
        "DTEL/DE": {"path": "ddic/dataelements",            "ns": "dtel",     "root": "blue:wbobject",                     "max": 30},
        "DOMA/DD": {"path": "ddic/domains",                 "ns": "doma",     "root": "blue:wbobject",                     "max": 30},
        "MSAG/N":  {"path": "messageclass",                 "ns": "msag",     "root": "blue:wbobject",                     "max": 20},
        "TTYP/T":  {"path": "ddic/tabletypes",              "ns": "ttyp",     "root": "blue:wbobject",                     "max": 30},
    }

    def create_object(self, type_id: str, name: str, description: str,
                      package: str, transport: str = "",
                      parent: str = "") -> int:
        """Create an empty ABAP object (skeleton). Write source separately.

        type_id    : one of self._CREATABLE_TYPES (e.g. 'TABL/DT', 'CLAS/OC')
        name       : object name (uppercased automatically)
        description: short description (<=50 chars)
        package    : SAP package ('$TMP' for local-only)
        transport  : workbench request (required outside $TMP)
        parent     : for FUGR/FF and FUGR/I, the function group name
        Returns HTTP status (200 = created, 400 = already exists / invalid).
        """
        if type_id not in self._CREATABLE_TYPES:
            raise ValueError(
                f"Unsupported creatable type: {type_id}. "
                f"Known: {sorted(self._CREATABLE_TYPES)}"
            )
        meta = self._CREATABLE_TYPES[type_id]
        if not self._csrf_token:
            self.fetch_csrf()
        path_template = meta["path"]
        if "%s" in path_template:
            if not parent:
                raise ValueError(
                    f"type_id={type_id} requires parent= (function group name)"
                )
            path = f"/sap/bc/adt/{path_template % parent.lower()}"
        else:
            path = f"/sap/bc/adt/{path_template}"
        desc_safe = description.replace('"', '&quot;').replace('<', '&lt;')
        root_short = meta["root"].split(":")[0]
        domain_root = meta["path"].split("/")[0]
        xml_body = (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<{meta["root"]} xmlns:{meta["ns"]}="http://www.sap.com/adt/{domain_root}" '
            f'xmlns:adtcore="http://www.sap.com/adt/core" '
            f'adtcore:type="{type_id}" '
            f'adtcore:name="{name.upper()}" '
            f'adtcore:description="{desc_safe}" '
            f'adtcore:responsible="{self.user.upper()}">'
            f'<adtcore:packageRef adtcore:name="{package.upper()}"/>'
            f'</{meta["root"]}>'
        )
        params = {}
        if transport:
            params["corrNr"] = transport
        status, body, _ = self._request(
            "POST", path,
            body=xml_body.encode("utf-8"),
            params=params,
            content_type=f"application/vnd.sap.adt.{meta['ns']}+xml",
            raise_on_error=False,
        )
        print(f"  [ADT] create_object {type_id} {name}: HTTP {status}")
        if status >= 400:
            print(f"  [ADT] Response: {body.decode('utf-8', errors='replace')[:300]}")
        return status

    # DDIC + foundational convenience wrappers
    def create_table(self, name: str, description: str, package: str, transport: str = "") -> int:
        return self.create_object("TABL/DT", name, description, package, transport)

    def create_structure(self, name: str, description: str, package: str, transport: str = "") -> int:
        return self.create_object("TABL/DS", name, description, package, transport)

    def create_data_element(self, name: str, description: str, package: str, transport: str = "") -> int:
        return self.create_object("DTEL/DE", name, description, package, transport)

    def create_domain(self, name: str, description: str, package: str, transport: str = "") -> int:
        return self.create_object("DOMA/DD", name, description, package, transport)

    def create_interface(self, name: str, description: str, package: str, transport: str = "") -> int:
        return self.create_object("INTF/OI", name, description, package, transport)

    def create_message_class(self, name: str, description: str, package: str, transport: str = "") -> int:
        return self.create_object("MSAG/N", name, description, package, transport)

    def create_function_group(self, name: str, description: str, package: str, transport: str = "") -> int:
        return self.create_object("FUGR/F", name, description, package, transport)

    def create_package(self, name: str, description: str, transport: str = "") -> int:
        """Create a SAP package (DEVC/K). Description is also used as software-component label."""
        return self.create_object("DEVC/K", name, description, name, transport)

    # ── DDIC TABLE HANDLER (atomic create + fields + activate) ────────────────
    # ⚠️ KERNEL REQUIREMENT: NW 7.50+ / S/4HANA. NOT USABLE ON ECC 6.0 EhP8
    # (NW 7.40). Empirically confirmed 2026-05-24 against D01 — POST to
    # /sap/bc/adt/ddic/tables returns HTTP 404; the endpoint is absent from
    # discovery. The methods below are preserved as forward-compatible
    # scaffolding for the S/4HANA migration path.
    #
    # For TABL + secondary INDEX work on EhP8 today, use the
    # `DDIF_*_PUT via RFC_ABAP_INSTALL_AND_RUN` pattern with mandatory
    # pre-flight (single-equality RFC_READ_TABLE, no IN-lists) and structured
    # SY-SUBRC → named-exception mapping. See
    # .agents/skills/sap_adt_api/SKILL.md §0 (ADT-FIRST qualifier).

    def build_table_source_xml(self, name: str, description: str,
                                fields: list, delivery_class: str = "A",
                                tab_class: str = "TRANSP") -> str:
        """Build the asx:abap TABL source XML for set_source().

        fields: list of dicts with keys:
          - name          : field name (uppercased)             [required]
          - key           : True if part of primary key
          - data_element  : DTEL name (e.g. 'CHAR7', 'MANDT')   [required]
          - position      : 1-based ordinal (auto-assigned if missing)
        delivery_class: A=application, C=customizing, L=temporary
        tab_class    : TRANSP (default), CLUSTER, POOL
        """
        dd03p_xml = ""
        for i, f in enumerate(fields, start=1):
            pos = f.get("position", i)
            keyflag = "X" if f.get("key") else ""
            notnull = "X" if f.get("key") else ""
            dd03p_xml += (
                '<DD03P>'
                f'<FIELDNAME>{f["name"].upper()}</FIELDNAME>'
                f'<POSITION>{int(pos):04d}</POSITION>'
                f'<KEYFLAG>{keyflag}</KEYFLAG>'
                f'<ROLLNAME>{f["data_element"].upper()}</ROLLNAME>'
                f'<NOTNULL>{notnull}</NOTNULL>'
                '</DD03P>'
            )
        desc_safe = description.replace('&', '&amp;').replace('<', '&lt;')
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">'
            '<asx:values>'
            '<DD02V>'
            f'<TABNAME>{name.upper()}</TABNAME>'
            '<DDLANGUAGE>E</DDLANGUAGE>'
            f'<TABCLASS>{tab_class}</TABCLASS>'
            f'<DDTEXT>{desc_safe}</DDTEXT>'
            f'<CONTFLAG>{delivery_class}</CONTFLAG>'
            '</DD02V>'
            '<DD09L>'
            f'<TABNAME>{name.upper()}</TABNAME>'
            '<AS4LOCAL>A</AS4LOCAL>'
            '<TABKAT>0</TABKAT>'
            '<TABART>APPL0</TABART>'
            '<SCHFELDANZ>0</SCHFELDANZ>'
            '</DD09L>'
            f'<DD03P_TABLE>{dd03p_xml}</DD03P_TABLE>'
            '</asx:values>'
            '</asx:abap>'
        )

    def define_table(self, name: str, description: str, package: str,
                      fields: list, transport: str = "",
                      delivery_class: str = "A") -> dict:
        """Atomic table creation: skeleton + fields + activate.

        Returns a structured dict (no opaque RC). Phases: create, lock,
        set_source, activate. Each phase reports HTTP status or "OK"/"FAILED".
        """
        name_upper = name.upper()
        uri = f"/sap/bc/adt/ddic/tables/{name.lower()}"
        result = {"table": name_upper, "phases": {}}
        create_status = self.create_table(name_upper, description, package, transport)
        result["phases"]["create"] = create_status
        try:
            lock_handle = self.lock(uri)
            result["phases"]["lock"] = "OK"
        except Exception as ex:
            result["phases"]["lock"] = f"FAILED: {ex}"
            return result
        try:
            source_xml = self.build_table_source_xml(
                name_upper, description, fields, delivery_class
            )
            set_status = self.set_source(uri, source_xml, lock_handle, transport)
            result["phases"]["set_source"] = set_status
            activated = self.activate(uri, name_upper, "TABL/DT")
            result["phases"]["activate"] = "OK" if activated else "FAILED"
        finally:
            self.unlock(uri, lock_handle)
        return result

    def add_table_field(self, name: str, field: dict, transport: str = "") -> dict:
        """Append a single field to an existing table (read-modify-write)."""
        uri = f"/sap/bc/adt/ddic/tables/{name.lower()}"
        current_source = self.get_source(uri)
        if "position" not in field:
            field["position"] = current_source.count("<DD03P>") + 1
        scratch_xml = self.build_table_source_xml(name.upper(), "", [field])
        import re
        m = re.search(r'<DD03P>.*?</DD03P>', scratch_xml, re.DOTALL)
        if not m:
            raise RuntimeError("Could not synthesize new <DD03P> entry")
        new_dd03p = m.group(0)
        updated_source = current_source.replace(
            "</DD03P_TABLE>", f"{new_dd03p}</DD03P_TABLE>", 1
        )
        lock_handle = self.lock(uri)
        try:
            set_status = self.set_source(uri, updated_source, lock_handle, transport)
            activated = self.activate(uri, name.upper(), "TABL/DT")
        finally:
            self.unlock(uri, lock_handle)
        return {"field": field["name"], "set_source": set_status,
                "activate": "OK" if activated else "FAILED"}

    # ── DDIC SECONDARY INDEXES ─────────────────────────────────────────────────
    def build_index_source_xml(self, table: str, index_id: str,
                                 description: str, fields: list,
                                 unique: bool = False) -> str:
        """Build asx:abap source XML for a secondary index (DD12V + DD17V)."""
        unique_flag = "X" if unique else ""
        dd17v_xml = ""
        for i, fname in enumerate(fields, start=1):
            dd17v_xml += (
                '<DD17V>'
                f'<SQLTAB>{table.upper()}</SQLTAB>'
                f'<INDEXNAME>{index_id.upper()}</INDEXNAME>'
                f'<POSITION>{i:04d}</POSITION>'
                f'<FIELDNAME>{fname.upper()}</FIELDNAME>'
                '</DD17V>'
            )
        desc_safe = description.replace('&', '&amp;').replace('<', '&lt;')
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">'
            '<asx:values>'
            '<DD12V>'
            f'<SQLTAB>{table.upper()}</SQLTAB>'
            f'<INDEXNAME>{index_id.upper()}</INDEXNAME>'
            '<DDLANGUAGE>E</DDLANGUAGE>'
            f'<DDTEXT>{desc_safe}</DDTEXT>'
            f'<UNIQUEFLAG>{unique_flag}</UNIQUEFLAG>'
            f'<DBINDEX>{unique_flag}</DBINDEX>'
            '</DD12V>'
            f'<DD17V_TABLE>{dd17v_xml}</DD17V_TABLE>'
            '</asx:values>'
            '</asx:abap>'
        )

    # ── DDIC TABLE UPDATE / READ STRUCTURE ────────────────────────────────────
    # Closes the "update" side of the lifecycle. Covers: introspect current
    # structure, full field-list replacement, surgical add/remove/modify field,
    # metadata-only updates, database conversion trigger (SE14 equivalent) when
    # a non-additive change requires DB restructuring.

    def get_table_structure(self, name: str) -> dict:
        """Read a table's current structure. Returns parsed Python dict.

        Returns: {
          'name': str, 'description': str, 'delivery_class': str,
          'tab_class': str, 'fields': [
              {'name', 'position', 'key', 'data_element', 'notnull'}, ...
          ]
        }
        """
        import re
        uri = f"/sap/bc/adt/ddic/tables/{name.lower()}"
        source = self.get_source(uri)
        out = {"name": name.upper(), "fields": []}
        m = re.search(r'<DDTEXT>([^<]*)</DDTEXT>', source)
        out["description"] = m.group(1) if m else ""
        m = re.search(r'<CONTFLAG>([^<]*)</CONTFLAG>', source)
        out["delivery_class"] = m.group(1) if m else ""
        m = re.search(r'<TABCLASS>([^<]*)</TABCLASS>', source)
        out["tab_class"] = m.group(1) if m else ""
        for block in re.findall(r'<DD03P>(.*?)</DD03P>', source, re.DOTALL):
            f = {}
            for tag in ("FIELDNAME", "POSITION", "KEYFLAG", "ROLLNAME", "NOTNULL"):
                fm = re.search(rf'<{tag}>([^<]*)</{tag}>', block)
                if fm:
                    f[tag.lower()] = fm.group(1)
            out["fields"].append({
                "name":         f.get("fieldname", ""),
                "position":     int(f.get("position", "0") or 0),
                "key":          f.get("keyflag", "") == "X",
                "data_element": f.get("rollname", ""),
                "notnull":      f.get("notnull", "") == "X",
            })
        out["fields"].sort(key=lambda x: x["position"])
        return out

    def update_table_fields(self, name: str, fields: list,
                              transport: str = "",
                              auto_convert: bool = False) -> dict:
        """Replace the entire field list of an existing table. Atomic.

        fields: same shape as define_table() — {name, key, data_element,
                position?, description?}
        auto_convert: if True, automatically trigger DB conversion (SE14
                      equivalent) when activation fails due to incompatible
                      DB structure change. Default False — destructive
                      changes require explicit opt-in.

        Returns structured dict with phases. If activation fails and
        auto_convert is False, the result includes 'conversion_required': True
        so the caller can decide.
        """
        uri = f"/sap/bc/adt/ddic/tables/{name.lower()}"
        result = {"table": name.upper(), "phases": {}}
        # Preserve current description if not provided in any field dict
        try:
            current = self.get_table_structure(name)
            description = current["description"]
            delivery_class = current["delivery_class"] or "A"
        except Exception as ex:
            result["phases"]["read_current"] = f"FAILED: {ex}"
            return result
        result["phases"]["read_current"] = "OK"
        try:
            lock_handle = self.lock(uri)
            result["phases"]["lock"] = "OK"
        except Exception as ex:
            result["phases"]["lock"] = f"FAILED: {ex}"
            return result
        try:
            new_source = self.build_table_source_xml(
                name.upper(), description, fields, delivery_class
            )
            set_status = self.set_source(uri, new_source, lock_handle, transport)
            result["phases"]["set_source"] = set_status
            activated = self.activate(uri, name.upper(), "TABL/DT")
            result["phases"]["activate"] = "OK" if activated else "FAILED"
            if not activated:
                # Likely a non-additive change requiring DB conversion
                result["conversion_required"] = True
                if auto_convert:
                    conv = self.convert_table(name, transport)
                    result["phases"]["convert"] = conv
                    if conv.get("status", 500) < 400:
                        # Retry activation
                        retry = self.activate(uri, name.upper(), "TABL/DT")
                        result["phases"]["activate_retry"] = "OK" if retry else "FAILED"
        finally:
            self.unlock(uri, lock_handle)
        return result

    def remove_table_field(self, name: str, field_name: str,
                             transport: str = "",
                             auto_convert: bool = False) -> dict:
        """Surgically remove ONE field. DESTRUCTIVE — drops the column at DB level.

        Requires auto_convert=True to actually drop the column in DB, otherwise
        activation will fail and the structural diff stays inactive.
        """
        current = self.get_table_structure(name)
        new_fields = [
            {"name": f["name"], "key": f["key"], "data_element": f["data_element"]}
            for f in current["fields"]
            if f["name"].upper() != field_name.upper()
        ]
        if len(new_fields) == len(current["fields"]):
            return {"table": name.upper(), "field": field_name,
                    "error": "field not found in current structure"}
        # Renumber positions
        for i, f in enumerate(new_fields, start=1):
            f["position"] = i
        result = self.update_table_fields(
            name, new_fields, transport=transport, auto_convert=auto_convert
        )
        result["removed_field"] = field_name.upper()
        return result

    def modify_table_field(self, name: str, field_name: str,
                             new_data_element: str = None,
                             new_position: int = None,
                             new_key_flag: bool = None,
                             transport: str = "",
                             auto_convert: bool = False) -> dict:
        """Change a single field's DE / position / key flag.

        Changing data_element or key flag may require DB conversion if the
        new type/length differs or the primary key changes. Set auto_convert=
        True to allow ADT to trigger the conversion.
        """
        current = self.get_table_structure(name)
        modified = False
        new_fields = []
        for f in current["fields"]:
            entry = {"name": f["name"], "key": f["key"],
                     "data_element": f["data_element"],
                     "position": f["position"]}
            if f["name"].upper() == field_name.upper():
                if new_data_element is not None:
                    entry["data_element"] = new_data_element.upper()
                if new_key_flag is not None:
                    entry["key"] = bool(new_key_flag)
                if new_position is not None:
                    entry["position"] = int(new_position)
                modified = True
            new_fields.append(entry)
        if not modified:
            return {"table": name.upper(), "field": field_name,
                    "error": "field not found in current structure"}
        # Re-sort and renumber if a position was forced
        if new_position is not None:
            new_fields.sort(key=lambda x: x["position"])
            for i, f in enumerate(new_fields, start=1):
                f["position"] = i
        result = self.update_table_fields(
            name, new_fields, transport=transport, auto_convert=auto_convert
        )
        result["modified_field"] = field_name.upper()
        return result

    def update_table_metadata(self, name: str, description: str = None,
                                delivery_class: str = None,
                                transport: str = "") -> dict:
        """Change description / delivery class only. Field list preserved.

        Non-destructive — does NOT touch the DB structure, only DDIC text.
        """
        current = self.get_table_structure(name)
        if description is None:
            description = current["description"]
        if delivery_class is None:
            delivery_class = current["delivery_class"] or "A"
        # Re-emit current fields with new metadata
        fields = [
            {"name": f["name"], "key": f["key"], "data_element": f["data_element"]}
            for f in current["fields"]
        ]
        uri = f"/sap/bc/adt/ddic/tables/{name.lower()}"
        result = {"table": name.upper(), "phases": {}}
        try:
            lock_handle = self.lock(uri)
            result["phases"]["lock"] = "OK"
        except Exception as ex:
            result["phases"]["lock"] = f"FAILED: {ex}"
            return result
        try:
            new_source = self.build_table_source_xml(
                name.upper(), description, fields, delivery_class
            )
            set_status = self.set_source(uri, new_source, lock_handle, transport)
            result["phases"]["set_source"] = set_status
            activated = self.activate(uri, name.upper(), "TABL/DT")
            result["phases"]["activate"] = "OK" if activated else "FAILED"
        finally:
            self.unlock(uri, lock_handle)
        return result

    def convert_table(self, name: str, transport: str = "") -> dict:
        """Trigger DB conversion for a table whose active+inactive structures diverge.

        Equivalent to SE14 "Activate and adjust database". Required after
        destructive changes (drop field, change type, change keys). MAY LOSE
        DATA if columns are dropped — caller responsibility to back up.

        Returns {status, raw}.
        """
        if not self._csrf_token:
            self.fetch_csrf()
        uri = f"/sap/bc/adt/ddic/tables/{name.lower()}/database-conversions"
        params = {}
        if transport:
            params["corrNr"] = transport
        status, body, _ = self._request(
            "POST", uri,
            params=params,
            content_type="application/vnd.sap.adt.ddic.conversion+xml",
            raise_on_error=False,
        )
        text = body.decode("utf-8", errors="replace")
        print(f"  [ADT] convert_table {name}: HTTP {status}")
        return {"status": status, "raw": text[:500]}

    def drop_index(self, table: str, index_id: str, transport: str = "") -> dict:
        """Delete a secondary index. DESTRUCTIVE on DB level."""
        if not self._csrf_token:
            self.fetch_csrf()
        uri = f"/sap/bc/adt/ddic/tables/{table.lower()}/indexes/{index_id.lower()}"
        try:
            lock_handle = self.lock(uri)
        except Exception as ex:
            return {"table": table.upper(), "index": index_id.upper(),
                    "phase": "lock", "error": str(ex)}
        params = {}
        if transport:
            params["corrNr"] = transport
        status, body, _ = self._request(
            "DELETE", uri,
            params=params,
            extra_headers={"X-adtcore-locktoken": lock_handle},
            raise_on_error=False,
        )
        # ADT releases the lock on successful DELETE; explicit unlock is best-effort
        try:
            self.unlock(uri, lock_handle)
        except Exception:
            pass
        print(f"  [ADT] drop_index {table}/{index_id}: HTTP {status}")
        return {"table": table.upper(), "index": index_id.upper(),
                "status": status, "raw": body.decode("utf-8", errors="replace")[:300]}

    def create_index(self, table: str, index_id: str, description: str,
                      fields: list, unique: bool = False,
                      transport: str = "") -> dict:
        """Create + activate a secondary index. Atomic, structured result."""
        if not self._csrf_token:
            self.fetch_csrf()
        uri = f"/sap/bc/adt/ddic/tables/{table.lower()}/indexes/{index_id.lower()}"
        result = {"table": table.upper(), "index": index_id.upper(), "phases": {}}
        desc_safe = description.replace('"', '&quot;').replace('<', '&lt;')
        create_xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<index:secondaryIndex '
            'xmlns:index="http://www.sap.com/adt/ddic/tables/indexes" '
            'xmlns:adtcore="http://www.sap.com/adt/core" '
            'adtcore:type="INDX/DT" '
            f'adtcore:name="{index_id.upper()}" '
            f'adtcore:description="{desc_safe}"/>'
        )
        params = {"corrNr": transport} if transport else {}
        c_status, _c_body, _ = self._request(
            "POST",
            f"/sap/bc/adt/ddic/tables/{table.lower()}/indexes",
            body=create_xml.encode("utf-8"),
            params=params,
            content_type="application/vnd.sap.adt.index+xml",
            raise_on_error=False,
        )
        result["phases"]["create"] = c_status
        try:
            lock_handle = self.lock(uri)
            result["phases"]["lock"] = "OK"
        except Exception as ex:
            result["phases"]["lock"] = f"FAILED: {ex}"
            return result
        try:
            source_xml = self.build_index_source_xml(
                table, index_id, description, fields, unique
            )
            set_status = self.set_source(uri, source_xml, lock_handle, transport)
            result["phases"]["set_source"] = set_status
            activated = self.activate(
                uri, f"{table.upper()}-{index_id.upper()}", "INDX/DT"
            )
            result["phases"]["activate"] = "OK" if activated else "FAILED"
        finally:
            self.unlock(uri, lock_handle)
        return result

    # ── CLASS INCLUDES (proper CCIMP / DEFINITIONS / TESTCLASSES URI scheme) ───
    # Closes the historical pain of 7 write_ccimp_*.py attempts that all tried
    # to write CCIMP via /source/main. Correct pattern: per-include sub-URIs.
    CLASS_INCLUDE_TYPES = {
        "definitions":     "definitions",      # local class TYPES / public section
        "implementations": "implementations",  # METHOD implementations (CCIMP)
        "macros":          "macros",           # DEFINE macros (CCMAC)
        "testclasses":     "testclasses",      # ABAP Unit tests (CCAU)
        "main":            "main",             # main include (default)
    }

    def class_include_uri(self, class_name: str, include_type: str = "definitions") -> str:
        """Return the ADT URI for a class sub-include.

        include_type: definitions | implementations | macros | testclasses | main
        For local-class implementations (CCIMP), use 'implementations'.
        """
        if include_type not in self.CLASS_INCLUDE_TYPES:
            raise ValueError(
                f"include_type must be one of {list(self.CLASS_INCLUDE_TYPES)}"
            )
        suffix = self.CLASS_INCLUDE_TYPES[include_type]
        return f"/sap/bc/adt/oo/classes/{class_name.lower()}/includes/{suffix}"

    def set_class_include_source(self, class_name: str, include_type: str,
                                  source: str, transport: str = "") -> bool:
        """Write source to a specific class include (CCIMP/CCDEF/CCMAC/CCAU).

        Replaces the 7 write_ccimp_*.py historical workarounds.
        """
        uri = self.class_include_uri(class_name, include_type)
        print(f"\n[ADT] Writing class {class_name} include={include_type}...")
        try:
            lock_handle = self.lock(uri)
            self.set_source(uri, source, lock_handle, transport)
            self.activate(uri, class_name, "CLAS/OC")
            self.unlock(uri, lock_handle)
            return True
        except Exception as ex:
            print(f"  [ADT] FAILED: {ex}")
            return False

    def create_test_include(self, class_name: str, transport: str = "") -> bool:
        """Create the testclasses include skeleton (if it doesn't exist)."""
        uri = self.class_include_uri(class_name, "testclasses")
        if not self._csrf_token:
            self.fetch_csrf()
        params = {}
        if transport:
            params["corrNr"] = transport
        status, _body, _ = self._request(
            "POST", uri,
            params=params,
            extra_headers={"Accept": "application/xml"},
            raise_on_error=False,
        )
        print(f"  [ADT] create_test_include {class_name}: HTTP {status}")
        return status < 400

    # ── TRANSPORT CREATE / RELEASE ─────────────────────────────────────────────
    def create_transport(self, description: str, transport_type: str = "K",
                          target_system: str = "") -> str:
        """Create a workbench transport request. Returns the new TRKORR (or '')."""
        if not self._csrf_token:
            self.fetch_csrf()
        body_xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<tm:root xmlns:tm="http://www.sap.com/cts/adt/tm" '
            f'tm:useraction="newrequest" tm:targetsystem="{target_system}">'
            f'<tm:request tm:type="{transport_type}" tm:desc="{description}"/>'
            '</tm:root>'
        )
        status, body, _ = self._request(
            "POST", "/sap/bc/adt/cts/transportrequests",
            body=body_xml.encode("utf-8"),
            params={"_action": "NEWREQUEST"},
            content_type="application/vnd.sap.adt.transportorganizer.v1+xml",
            raise_on_error=False,
        )
        import re
        text = body.decode("utf-8", errors="replace")
        m = (re.search(r'tm:number="([A-Z0-9]+)"', text)
             or re.search(r'trkorr="([A-Z0-9]+)"', text))
        trkorr = m.group(1) if m else ""
        print(f"  [ADT] create_transport: HTTP {status}, TRKORR={trkorr or 'NOT-PARSED'}")
        return trkorr

    def transport_release(self, trkorr: str) -> int:
        """Release a transport. Returns HTTP status (200 = released)."""
        if not self._csrf_token:
            self.fetch_csrf()
        status, body, _ = self._request(
            "POST", f"/sap/bc/adt/cts/transportrequests/{trkorr}/newreleasejobs",
            extra_headers={"Accept": "application/vnd.sap.adt.transportorganizer.v1+xml"},
            raise_on_error=False,
        )
        print(f"  [ADT] transport_release {trkorr}: HTTP {status}")
        if status >= 400:
            print(f"  [ADT] Response: {body.decode('utf-8', errors='replace')[:300]}")
        return status

    # ── ABAP DEBUGGER (external breakpoint workflow) ───────────────────────────
    # Flow: set_breakpoint → listen (long-poll) → attach → stack → variables →
    #       step → ... → terminate
    def debugger_set_breakpoint(self, object_uri: str, line: int,
                                  username: str = None) -> dict:
        """Set an external breakpoint visible to the given user."""
        if not self._csrf_token:
            self.fetch_csrf()
        username = (username or self.user).upper()
        body_xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<dbg:debugger xmlns:dbg="http://www.sap.com/adt/debugger">'
            f'<dbg:breakpoints><dbg:breakpoint dbg:kind="line" '
            f'dbg:clientId="adt-py" dbg:uri="{object_uri}#start={line}"/>'
            '</dbg:breakpoints></dbg:debugger>'
        )
        status, body, _ = self._request(
            "POST", "/sap/bc/adt/debugger/breakpoints",
            body=body_xml.encode("utf-8"),
            params={"requestUser": username, "terminalId": "adt-py-terminal",
                    "ideId": "adt-py-ide"},
            content_type="application/vnd.sap.adt.debugger.breakpoints.v1+xml",
            raise_on_error=False,
        )
        print(f"  [ADT] debugger_set_breakpoint {object_uri}:{line}: HTTP {status}")
        return {"status": status, "raw": body.decode("utf-8", errors="replace")[:500]}

    def debugger_listen(self, username: str = None) -> dict:
        """Long-poll until a breakpoint is hit. Blocks server-side until event."""
        if not self._csrf_token:
            self.fetch_csrf()
        username = (username or self.user).upper()
        status, body, _ = self._request(
            "POST", "/sap/bc/adt/debugger/listeners",
            params={"requestUser": username, "terminalId": "adt-py-terminal",
                    "ideId": "adt-py-ide", "checkConflict": "true"},
            content_type="application/vnd.sap.adt.debugger.v1+xml",
            raise_on_error=False,
        )
        print(f"  [ADT] debugger_listen: HTTP {status}")
        return {"status": status, "raw": body.decode("utf-8", errors="replace")[:1000]}

    def debugger_attach(self, debuggee_id: str, username: str = None) -> dict:
        """Attach to a debuggee that already hit a breakpoint."""
        if not self._csrf_token:
            self.fetch_csrf()
        username = (username or self.user).upper()
        status, body, _ = self._request(
            "POST", "/sap/bc/adt/debugger",
            params={"method": "attach", "debuggeeId": debuggee_id,
                    "requestUser": username, "dynproDebugging": "true"},
            content_type="application/vnd.sap.adt.debugger.v1+xml",
            raise_on_error=False,
        )
        print(f"  [ADT] debugger_attach {debuggee_id}: HTTP {status}")
        return {"status": status, "raw": body.decode("utf-8", errors="replace")[:500]}

    def debugger_step(self, step_type: str = "stepInto") -> dict:
        """Step. step_type: stepInto | stepOver | stepReturn | stepContinue
        | stepRunToLine | terminateDebuggee.
        """
        valid = {"stepInto", "stepOver", "stepReturn", "stepContinue",
                 "stepRunToLine", "terminateDebuggee"}
        if step_type not in valid:
            raise ValueError(f"step_type must be one of {valid}")
        status, body, _ = self._request(
            "POST", "/sap/bc/adt/debugger/steps",
            params={"action": step_type},
            content_type="application/vnd.sap.adt.debugger.v1+xml",
            raise_on_error=False,
        )
        return {"status": status, "raw": body.decode("utf-8", errors="replace")[:500]}

    def debugger_stack(self) -> dict:
        """Get the current ABAP call stack."""
        status, body, _ = self._request(
            "GET", "/sap/bc/adt/debugger/stack",
            extra_headers={"Accept": "application/vnd.sap.adt.debugger.v1+xml"},
            raise_on_error=False,
        )
        return {"status": status, "raw": body.decode("utf-8", errors="replace")[:2000]}

    def debugger_variables(self, parents: list = None) -> dict:
        """Inspect variables. parents=['@ROOT', '@DATAAGING'] = top-level scope."""
        parents = parents or ["@ROOT", "@DATAAGING"]
        body_xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<dbg:variables xmlns:dbg="http://www.sap.com/adt/debugger">'
            + "".join(f'<dbg:parent>{p}</dbg:parent>' for p in parents)
            + '</dbg:variables>'
        )
        status, body, _ = self._request(
            "POST", "/sap/bc/adt/debugger/variables",
            body=body_xml.encode("utf-8"),
            content_type="application/vnd.sap.adt.debugger.v1+xml",
            raise_on_error=False,
        )
        return {"status": status, "raw": body.decode("utf-8", errors="replace")[:2000]}

    def debugger_set_variable(self, variable_name: str, value: str) -> dict:
        """Change a variable's value mid-execution. Destructive — use sparingly."""
        body_xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<dbg:variable xmlns:dbg="http://www.sap.com/adt/debugger" '
            f'dbg:name="{variable_name}" dbg:value="{value}"/>'
        )
        status, body, _ = self._request(
            "PUT", f"/sap/bc/adt/debugger/variables/{variable_name}",
            body=body_xml.encode("utf-8"),
            content_type="application/vnd.sap.adt.debugger.v1+xml",
            raise_on_error=False,
        )
        return {"status": status, "raw": body.decode("utf-8", errors="replace")[:500]}

    # ══════════════════════════════════════════════════════════════════════════
    # DDIF WRITER (RFC + DDIF_*_PUT) — for ECC 6.0 EhP8 / NW 7.40
    # ══════════════════════════════════════════════════════════════════════════
    # Drop-in alternative for define_table / create_data_element / create_domain
    # / create_index on systems where the ADT DDIC creation endpoints return
    # 404 (NW <7.50). Same structured-dict return shape — when UNESCO upgrades
    # to S/4HANA, callers can switch to the ADT-REST methods without changing
    # call sites.
    #
    # Mitigation pattern (per feedback_adt_first_no_abap_program_generators):
    #   1. Pre-flight each DE/Domain with single-equality RFC_READ_TABLE
    #      (NEVER IN-list — 72-char OPTIONS bug breaks them on EhP8).
    #   2. Synthesize ABAP that calls DDIF_*_PUT with explicit EXCEPTIONS.
    #   3. Parse WRITES output → map SY-SUBRC → named exception.
    #   4. Activate in chain order Domain → DE → Table → Index.
    #
    # pyrfc is lazy-imported only when these methods are called, so the
    # urllib-only ADT path keeps working without pyrfc installed.

    # DDIF_TABL_PUT exception map (SY-SUBRC → human cause)
    _DDIF_TABL_PUT_RC = {
        0: ("OK", "Object written successfully (still inactive — needs activate)"),
        1: ("not_executed", "TBL_NAME malformed — check charset/length"),
        2: ("name_inconsistent", "Name conflicts with existing TADIR OR referenced DE/DOMA missing — re-run preflight"),
        3: ("tabl_inconsistent", "Structure invalid (PK not first / NOTNULL gap / CHAR with missing DTEL)"),
        4: ("put_failure", "DB-level error — transport blocked or lock held"),
        5: ("put_refused", "No DEVCLASS, no authorization (S_DEVELOP, S_TRANSPRT)"),
    }
    _DDIF_TABL_ACT_RC = {
        0: ("OK", "Active version written; structure available in DB"),
        1: ("not_found", "Inactive version does not exist — PUT first"),
        2: ("put_failure", "DB conversion failed — incompatible structural change requires SE14 conversion"),
    }
    _DDIF_DTEL_PUT_RC = {
        0: ("OK", "DE written (inactive)"),
        1: ("dtel_not_found", "DE name malformed"),
        2: ("name_inconsistent", "Conflict with existing TADIR OR referenced domain missing"),
        3: ("dtel_inconsistent", "DDIC inconsistency"),
        4: ("put_failure", "DB error"),
        5: ("put_refused", "No DEVCLASS / no auth"),
    }
    _DDIF_DOMA_PUT_RC = {
        0: ("OK", "Domain written (inactive)"),
        1: ("doma_not_found", "Domain name malformed"),
        2: ("name_inconsistent", "Name conflicts with existing TADIR"),
        3: ("doma_inconsistent", "DDIC inconsistency"),
        4: ("put_failure", "DB error"),
        5: ("put_refused", "No DEVCLASS / no auth"),
    }

    def _get_rfc_connection(self, system_id: str = "D01"):
        """Lazy-create a pyrfc Connection using same .env vars as from_env().

        Prefers HOST (hostname) over ASHOST (often stale IP). Cached on self
        for reuse within a single SAPADTClient lifetime.
        """
        if getattr(self, "_rfc_conn", None) is not None:
            return self._rfc_conn
        try:
            from pyrfc import Connection
        except ImportError as ex:
            raise RuntimeError(
                "pyrfc not available — required for *_via_ddif() methods. "
                "Install pyrfc and ensure SAP NWRFC SDK is in PATH."
            ) from ex
        from dotenv import load_dotenv
        dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
        load_dotenv(dotenv_path)
        prefix = f"SAP_{system_id}_"
        def e(k, d=None):
            return os.getenv(prefix + k) or os.getenv("SAP_" + k) or d
        # Prefer hostname (HOST) over IP (ASHOST). The IP may be stale; the
        # hostname is what BASIS keeps stable across infra moves.
        host = e("HOST") or e("ASHOST")
        self._rfc_conn = Connection(
            ashost=host,
            sysnr=e("SYSNR", "00"),
            client=e("CLIENT", "350"),
            user=e("USER"),
            passwd=e("PASSWD") or e("PASSWORD"),
        )
        return self._rfc_conn

    def verify_tadir(self, name: str, obj_class: str) -> dict:
        """Read TADIR row for an object. Used as post-DDIF sanity check.

        Returns {exists, devclass, author, pgmid, srcsystem, edtflag}.
        TADIR row missing OR DEVCLASS empty == 'functional-but-orphan' bug
        (object exists in DD0xx but has no proper transport organizer record).
        """
        conn = self._get_rfc_connection()
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="TADIR",
            DELIMITER="|",
            OPTIONS=[
                {"TEXT": f"PGMID EQ 'R3TR' AND OBJECT EQ '{obj_class}' AND OBJ_NAME EQ '{name.upper()}'"},
            ],
            FIELDS=[
                {"FIELDNAME": "PGMID"},
                {"FIELDNAME": "OBJECT"},
                {"FIELDNAME": "OBJ_NAME"},
                {"FIELDNAME": "DEVCLASS"},
                {"FIELDNAME": "AUTHOR"},
                {"FIELDNAME": "SRCSYSTEM"},
                {"FIELDNAME": "EDTFLAG"},
            ],
        )
        rows = result.get("DATA", [])
        if not rows:
            return {"exists": False, "name": name.upper(), "object_class": obj_class}
        parts = rows[0]["WA"].split("|")
        # Pad in case some columns are blank
        parts += [""] * (7 - len(parts))
        return {
            "exists": True,
            "pgmid":     parts[0].strip(),
            "object":    parts[1].strip(),
            "name":      parts[2].strip(),
            "devclass":  parts[3].strip(),
            "author":    parts[4].strip(),
            "srcsystem": parts[5].strip(),
            "edtflag":   parts[6].strip(),
            "orphan": not parts[3].strip(),  # blank DEVCLASS = TADIR orphan
        }

    def _run_abap_program(self, source_lines: list,
                            program_name: str = "Z_ADTPY_DDIF") -> dict:
        """Execute synthesized ABAP via RFC_ABAP_INSTALL_AND_RUN.

        Returns {writes: [str], error_message: str, raw: dict}.
        WRITES table is parsed line-by-line — the synthesized ABAP must emit
        machine-parseable markers like 'PUT_RC=2', 'ACT_RC=0'.
        """
        conn = self._get_rfc_connection()
        # PROGRAM table is TABLE OF C72 (one line per dict, key 'LINE')
        program_tab = [{"LINE": line[:72]} for line in source_lines]
        result = conn.call(
            "RFC_ABAP_INSTALL_AND_RUN",
            PROGRAMNAME=program_name,
            PROGRAM=program_tab,
        )
        writes_raw = result.get("WRITES", []) or []
        # WRITES table on EhP8 returns rows with field 'ZEILE' (German for line).
        # Fallback to TAB/MESSAGE for kernel-version variance + take any non-empty
        # string value if the field name surprises us.
        def _row_text(w: dict) -> str:
            for k in ("ZEILE", "TAB", "MESSAGE"):
                v = w.get(k)
                if v:
                    return str(v).strip()
            for v in w.values():
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return ""
        writes = [_row_text(w) for w in writes_raw]
        err = result.get("ERRORMESSAGE", "") or ""
        return {"writes": writes, "error_message": err, "raw": result}

    @staticmethod
    def _parse_rc_marker(writes: list, marker: str) -> Optional[int]:
        """Find 'MARKER=<int>' in WRITES output; return the int or None."""
        for line in writes:
            if line.startswith(f"{marker}="):
                try:
                    return int(line.split("=", 1)[1].strip())
                except ValueError:
                    return None
        return None

    @staticmethod
    def _abap_quote(s: str) -> str:
        """Escape a string for embedding inside ABAP single-quoted literal."""
        return s.replace("'", "''")

    # ── PRE-FLIGHT ─────────────────────────────────────────────────────────────
    def preflight_data_element(self, name: str) -> dict:
        """Check if DD04L has an active DTEL with this name.

        Uses single-equality RFC_READ_TABLE (avoids the EhP8 IN-list parser bug).
        Returns {exists: bool, active: bool, domain: str}.
        """
        conn = self._get_rfc_connection()
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="DD04L",
            DELIMITER="|",
            OPTIONS=[{"TEXT": f"ROLLNAME EQ '{name.upper()}'"}],
            FIELDS=[
                {"FIELDNAME": "ROLLNAME"},
                {"FIELDNAME": "AS4LOCAL"},
                {"FIELDNAME": "DOMNAME"},
            ],
        )
        rows = result.get("DATA", [])
        if not rows:
            return {"exists": False, "active": False, "domain": "", "name": name.upper()}
        # Pick the active row if present, else first
        parsed = [r["WA"].split("|") for r in rows]
        active_row = next((p for p in parsed if len(p) >= 2 and p[1].strip() == "A"), parsed[0])
        return {
            "exists": True,
            "active": (active_row[1].strip() == "A") if len(active_row) >= 2 else False,
            "domain": active_row[2].strip() if len(active_row) >= 3 else "",
            "name": name.upper(),
        }

    def preflight_domain(self, name: str) -> dict:
        """Check if DD01L has an active Domain with this name."""
        conn = self._get_rfc_connection()
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="DD01L",
            DELIMITER="|",
            OPTIONS=[{"TEXT": f"DOMNAME EQ '{name.upper()}'"}],
            FIELDS=[
                {"FIELDNAME": "DOMNAME"},
                {"FIELDNAME": "AS4LOCAL"},
                {"FIELDNAME": "DATATYPE"},
                {"FIELDNAME": "LENG"},
            ],
        )
        rows = result.get("DATA", [])
        if not rows:
            return {"exists": False, "active": False, "name": name.upper()}
        parsed = [r["WA"].split("|") for r in rows]
        active_row = next((p for p in parsed if len(p) >= 2 and p[1].strip() == "A"), parsed[0])
        return {
            "exists": True,
            "active": (active_row[1].strip() == "A") if len(active_row) >= 2 else False,
            "datatype": active_row[2].strip() if len(active_row) >= 3 else "",
            "leng": active_row[3].strip() if len(active_row) >= 4 else "",
            "name": name.upper(),
        }

    def preflight_table_chain(self, fields: list) -> dict:
        """For a list of field dicts (with 'data_element'), verify every DE exists
        and is active. Returns {ready: bool, missing_des: [...], inactive_des: [...]}.
        """
        missing, inactive = [], []
        seen = set()
        for f in fields:
            de = f.get("data_element", "").upper()
            if not de or de in seen:
                continue
            seen.add(de)
            pf = self.preflight_data_element(de)
            if not pf["exists"]:
                missing.append(de)
            elif not pf["active"]:
                inactive.append(de)
        return {
            "ready": not (missing or inactive),
            "missing_des": missing,
            "inactive_des": inactive,
            "checked_count": len(seen),
        }

    # ── DDIF DOMAIN ────────────────────────────────────────────────────────────
    def define_domain_via_ddif(self, name: str, description: str,
                                 datatype: str, leng: int,
                                 package: str, transport: str = "",
                                 decimals: int = 0) -> dict:
        """Create + activate a DOMA on EhP8 via DDIF_DOMA_PUT / DDIF_DOMA_ACTIVATE.

        datatype: 'CHAR', 'NUMC', 'DEC', 'DATS', 'TIMS', 'INT4', etc.
        Returns structured phases dict.
        """
        name = name.upper()
        package = package.upper()
        d_safe = self._abap_quote(description)
        src = [
            "REPORT z_adtpy_doma.",
            "DATA: ls_dd01v TYPE dd01v, lv_rc TYPE i.",
            f"ls_dd01v-domname    = '{name}'.",
            f"ls_dd01v-ddlanguage = 'E'.",
            f"ls_dd01v-datatype   = '{datatype}'.",
            f"ls_dd01v-leng       = {int(leng)}.",
            f"ls_dd01v-decimals   = {int(decimals)}.",
            "ls_dd01v-outputlen   = ls_dd01v-leng.",
            f"ls_dd01v-ddtext     = '{d_safe}'.",
            "* TADIR-first (avoids functional-but-orphan bug where DDIF_*_PUT",
            "* writes the active version but TADIR has no row → object can't",
            "* be transported and shows up wrong in SE03/SE10).",
            "CALL FUNCTION 'TR_TADIR_INTERFACE'",
            "  EXPORTING",
            "    wi_test_modus        = ' '",
            "    wi_tadir_pgmid       = 'R3TR'",
            "    wi_tadir_object      = 'DOMA'",
            f"    wi_tadir_obj_name    = '{name}'",
            "    wi_tadir_author      = sy-uname",
            f"    wi_tadir_devclass    = '{package}'",
            "    wi_tadir_masterlang  = 'E'",
            "    iv_set_edtflag       = ' '",  # ' ' = SE11-editable; 'X' = locked (TK035 trap, session #76)
            "    iv_delflag           = ' '",
            "  EXCEPTIONS",
            "    OTHERS               = 99.",
            "WRITE: / 'TADIR_RC=', sy-subrc.",
            "CALL FUNCTION 'DDIF_DOMA_PUT'",
            "  EXPORTING",
            f"    name              = '{name}'",
            "    dd01v_wa          = ls_dd01v",
            "  EXCEPTIONS",
            "    doma_not_found    = 1",
            "    name_inconsistent = 2",
            "    doma_inconsistent = 3",
            "    put_failure       = 4",
            "    put_refused       = 5",
            "    OTHERS            = 6.",
            "WRITE: / 'PUT_RC=', sy-subrc.",
            "IF sy-subrc = 0.",
            "  CALL FUNCTION 'RS_CORR_INSERT'",
            "    EXPORTING",
            f"      object              = '{name}'",
            "      object_class        = 'DOMA'",
            f"      devclass            = '{package}'",
            "      master_language     = 'E'",
            "      global_lock         = 'X'",
            "      suppress_dialog     = 'X'",
            f"      korrnum             = '{transport}'",
            "    EXCEPTIONS",
            "      cancelled           = 1",
            "      permission_failure  = 2",
            "      unknown_objectclass = 3",
            "      OTHERS              = 4.",
            "  WRITE: / 'CORR_RC=', sy-subrc.",
            "  CALL FUNCTION 'DDIF_DOMA_ACTIVATE'",
            "    EXPORTING",
            f"      name        = '{name}'",
            "    EXCEPTIONS",
            "      not_found   = 1",
            "      put_failure = 2",
            "      OTHERS      = 3.",
            "  WRITE: / 'ACT_RC=', sy-subrc.",
            "ENDIF.",
        ]
        return self._execute_ddif(src, name, "DOMA",
                                    self._DDIF_DOMA_PUT_RC)

    # ── DDIF DATA ELEMENT ──────────────────────────────────────────────────────
    def define_data_element_via_ddif(self, name: str, description: str,
                                       domain: str, package: str,
                                       transport: str = "",
                                       text_short: str = None) -> dict:
        """Create + activate a DTEL on EhP8 via DDIF_DTEL_PUT / DDIF_DTEL_ACTIVATE.

        domain: name of DOMA that backs this DE (must exist + be active).
        """
        name = name.upper()
        domain = domain.upper()
        package = package.upper()
        d_safe = self._abap_quote(description)
        s_safe = self._abap_quote(text_short or description[:20])
        src = [
            "REPORT z_adtpy_dtel.",
            "DATA: ls_dd04v TYPE dd04v.",
            f"ls_dd04v-rollname   = '{name}'.",
            f"ls_dd04v-ddlanguage = 'E'.",
            f"ls_dd04v-domname    = '{domain}'.",
            "ls_dd04v-headlen    = 55.",
            "ls_dd04v-scrlen1    = 10.",
            "ls_dd04v-scrlen2    = 20.",
            "ls_dd04v-scrlen3    = 40.",
            f"ls_dd04v-ddtext     = '{d_safe}'.",
            f"ls_dd04v-reptext    = '{s_safe}'.",
            f"ls_dd04v-scrtext_s  = '{s_safe}'.",
            f"ls_dd04v-scrtext_m  = '{d_safe[:20]}'.",
            f"ls_dd04v-scrtext_l  = '{d_safe[:40]}'.",
            "* TADIR-first — prevents the functional-but-orphan bug observed",
            "* in legacy DDIF_DTEL_PUT runs (DE active in DD04L but no TADIR).",
            "CALL FUNCTION 'TR_TADIR_INTERFACE'",
            "  EXPORTING",
            "    wi_test_modus        = ' '",
            "    wi_tadir_pgmid       = 'R3TR'",
            "    wi_tadir_object      = 'DTEL'",
            f"    wi_tadir_obj_name    = '{name}'",
            "    wi_tadir_author      = sy-uname",
            f"    wi_tadir_devclass    = '{package}'",
            "    wi_tadir_masterlang  = 'E'",
            "    iv_set_edtflag       = ' '",  # ' ' = SE11-editable; 'X' = locked (TK035 trap, session #76)
            "    iv_delflag           = ' '",
            "  EXCEPTIONS",
            "    OTHERS               = 99.",
            "WRITE: / 'TADIR_RC=', sy-subrc.",
            "CALL FUNCTION 'DDIF_DTEL_PUT'",
            "  EXPORTING",
            f"    name              = '{name}'",
            "    dd04v_wa          = ls_dd04v",
            "  EXCEPTIONS",
            "    dtel_not_found    = 1",
            "    name_inconsistent = 2",
            "    dtel_inconsistent = 3",
            "    put_failure       = 4",
            "    put_refused       = 5",
            "    OTHERS            = 6.",
            "WRITE: / 'PUT_RC=', sy-subrc.",
            "IF sy-subrc = 0.",
            "  CALL FUNCTION 'RS_CORR_INSERT'",
            "    EXPORTING",
            f"      object              = '{name}'",
            "      object_class        = 'DTEL'",
            f"      devclass            = '{package}'",
            "      master_language     = 'E'",
            "      global_lock         = 'X'",
            "      suppress_dialog     = 'X'",
            f"      korrnum             = '{transport}'",
            "    EXCEPTIONS OTHERS    = 4.",
            "  WRITE: / 'CORR_RC=', sy-subrc.",
            "  CALL FUNCTION 'DDIF_DTEL_ACTIVATE'",
            "    EXPORTING",
            f"      name        = '{name}'",
            "    EXCEPTIONS",
            "      not_found   = 1",
            "      put_failure = 2",
            "      OTHERS      = 3.",
            "  WRITE: / 'ACT_RC=', sy-subrc.",
            "ENDIF.",
        ]
        return self._execute_ddif(src, name, "DTEL",
                                    self._DDIF_DTEL_PUT_RC)

    # ── DDIF TABLE ─────────────────────────────────────────────────────────────
    def define_table_via_ddif(self, name: str, description: str,
                                package: str, fields: list,
                                transport: str = "",
                                delivery_class: str = "A",
                                skip_preflight: bool = False) -> dict:
        """Create + activate a TABL on EhP8 via DDIF_TABL_PUT / DDIF_TABL_ACTIVATE.

        Same API shape as ADT-based define_table(). Pre-flights all referenced
        data elements (skip with skip_preflight=True). Returns structured dict
        with phases — never opaque RC=2.
        """
        name = name.upper()
        package = package.upper()
        result = {"table": name, "phases": {}, "transport": transport}
        # 1) Preflight DE chain
        if not skip_preflight:
            pf = self.preflight_table_chain(fields)
            result["phases"]["preflight"] = pf
            if not pf["ready"]:
                result["error"] = (
                    f"Preflight failed — missing DEs: {pf['missing_des']}, "
                    f"inactive DEs: {pf['inactive_des']}. "
                    f"Create them first via define_data_element_via_ddif() / "
                    f"define_domain_via_ddif()."
                )
                return result
        # 2) Synthesize the ABAP
        d_safe = self._abap_quote(description)
        src = [
            "REPORT z_adtpy_tabl.",
            "DATA: ls_dd02v TYPE dd02v, ls_dd09l TYPE dd09l,",
            "      lt_dd03p TYPE TABLE OF dd03p, ls_dd03p TYPE dd03p.",
            f"ls_dd02v-tabname    = '{name}'.",
            "ls_dd02v-ddlanguage = 'E'.",
            "ls_dd02v-tabclass   = 'TRANSP'.",
            f"ls_dd02v-ddtext     = '{d_safe}'.",
            f"ls_dd02v-contflag   = '{delivery_class}'.",
            "ls_dd02v-mainflag   = 'X'.",
            f"ls_dd09l-tabname    = '{name}'.",
            "ls_dd09l-as4local   = 'A'.",
            "ls_dd09l-tabkat     = '0'.",
            "ls_dd09l-tabart     = 'APPL0'.",
            "ls_dd09l-bufallow   = 'N'.",
        ]
        for i, f in enumerate(fields, start=1):
            fn = f["name"].upper()
            de = f["data_element"].upper()
            key = "X" if f.get("key") else ""
            notnull = "X" if f.get("key") else ""
            pos = f.get("position", i)
            reftable = (f.get("reftable") or "").upper()
            reffield = (f.get("reffield") or "").upper()
            src += [
                "CLEAR ls_dd03p.",
                f"ls_dd03p-tabname   = '{name}'.",
                f"ls_dd03p-fieldname = '{fn}'.",
                f"ls_dd03p-position  = '{int(pos):04d}'.",
                f"ls_dd03p-keyflag   = '{key}'.",
                f"ls_dd03p-rollname  = '{de}'.",
                f"ls_dd03p-notnull   = '{notnull}'.",
            ]
            # CURR / QUAN reference table+field (e.g. amount -> currency, qty -> uom)
            # SE14 rejects CURR/QUAN fields without reftable+reffield.
            if reftable:
                src.append(f"ls_dd03p-reftable  = '{reftable}'.")
            if reffield:
                src.append(f"ls_dd03p-reffield  = '{reffield}'.")
            src.append("APPEND ls_dd03p TO lt_dd03p.")
        src += [
            "* TADIR-first — prevents functional-but-orphan tables. Without this,",
            "* DDIF_TABL_PUT can succeed and the DB structure can be built, but",
            "* the TADIR row stays blank/missing → table can't be transported.",
            "CALL FUNCTION 'TR_TADIR_INTERFACE'",
            "  EXPORTING",
            "    wi_test_modus        = ' '",
            "    wi_tadir_pgmid       = 'R3TR'",
            "    wi_tadir_object      = 'TABL'",
            f"    wi_tadir_obj_name    = '{name}'",
            "    wi_tadir_author      = sy-uname",
            f"    wi_tadir_devclass    = '{package}'",
            "    wi_tadir_masterlang  = 'E'",
            "    iv_set_edtflag       = ' '",  # ' ' = SE11-editable; 'X' = locked (TK035 trap, session #76)
            "    iv_delflag           = ' '",
            "  EXCEPTIONS",
            "    OTHERS               = 99.",
            "WRITE: / 'TADIR_RC=', sy-subrc.",
            "CALL FUNCTION 'DDIF_TABL_PUT'",
            "  EXPORTING",
            f"    name              = '{name}'",
            "    dd02v_wa          = ls_dd02v",
            "    dd09l_wa          = ls_dd09l",
            "  TABLES",
            "    dd03p_tab         = lt_dd03p",
            "  EXCEPTIONS",
            "    tabl_not_found    = 1",
            "    name_inconsistent = 2",
            "    tabl_inconsistent = 3",
            "    put_failure       = 4",
            "    put_refused       = 5",
            "    OTHERS            = 6.",
            "WRITE: / 'PUT_RC=', sy-subrc.",
            "IF sy-subrc = 0.",
            "  CALL FUNCTION 'RS_CORR_INSERT'",
            "    EXPORTING",
            f"      object              = '{name}'",
            "      object_class        = 'TABL'",
            f"      devclass            = '{package}'",
            "      master_language     = 'E'",
            "      global_lock         = 'X'",
            "      suppress_dialog     = 'X'",
            f"      korrnum             = '{transport}'",
            "    EXCEPTIONS OTHERS    = 4.",
            "  WRITE: / 'CORR_RC=', sy-subrc.",
            "  CALL FUNCTION 'DDIF_TABL_ACTIVATE'",
            "    EXPORTING",
            f"      name        = '{name}'",
            "    EXCEPTIONS",
            "      not_found   = 1",
            "      put_failure = 2",
            "      OTHERS      = 3.",
            "  WRITE: / 'ACT_RC=', sy-subrc.",
            "* SE11-EDITOR FIX: re-issue DDIF_TABL_PUT to recreate the inactive (N)",
            "* copy. ACTIVATE consumes+deletes N; SE11 needs N to load into the editor",
            "* when user opens the table. Without this re-PUT, opening in SE11 raises",
            "* TK035 'You cannot edit object TABL X with the standard editor'.",
            "  IF sy-subrc = 0.",
            "    CALL FUNCTION 'DDIF_TABL_PUT'",
            "      EXPORTING",
            f"        name              = '{name}'",
            "        dd02v_wa          = ls_dd02v",
            "        dd09l_wa          = ls_dd09l",
            "      TABLES",
            "        dd03p_tab         = lt_dd03p",
            "      EXCEPTIONS OTHERS   = 1.",
            "    WRITE: / 'EDITBUF_RC=', sy-subrc.",
            "  ENDIF.",
            "ENDIF.",
        ]
        return self._execute_ddif(src, name, "TABL",
                                    self._DDIF_TABL_PUT_RC,
                                    base_result=result)

    # ── DDIF EXECUTION HELPER ──────────────────────────────────────────────────
    def _execute_ddif(self, src_lines: list, name: str, obj_class: str,
                       put_rc_map: dict,
                       base_result: dict = None) -> dict:
        """Run a synthesized DDIF program and parse the canonical PUT_RC /
        CORR_RC / ACT_RC markers into a structured result.
        """
        result = base_result or {"name": name, "object_class": obj_class, "phases": {}}
        try:
            run = self._run_abap_program(src_lines,
                                            program_name=f"Z_ADTPY_{obj_class}")
        except Exception as ex:
            result["phases"]["rfc_call"] = f"FAILED: {ex}"
            return result
        result["phases"]["rfc_call"] = "OK"
        if run.get("error_message"):
            result["phases"]["abap_compile"] = f"ERROR: {run['error_message']}"
            result["writes"] = run.get("writes", [])
            return result
        result["phases"]["abap_compile"] = "OK"
        writes = run.get("writes", [])
        tadir_rc = self._parse_rc_marker(writes, "TADIR_RC")
        put_rc = self._parse_rc_marker(writes, "PUT_RC")
        corr_rc = self._parse_rc_marker(writes, "CORR_RC")
        act_rc = self._parse_rc_marker(writes, "ACT_RC")
        # TADIR registration (must be done BEFORE put for clean orphan-free state)
        if tadir_rc is not None:
            result["phases"]["tadir_interface"] = {
                "rc": tadir_rc,
                "status": "OK" if tadir_rc == 0 else f"FAILED rc={tadir_rc}",
            }
        # PUT
        if put_rc is None:
            result["phases"]["put"] = "UNKNOWN — no PUT_RC marker in WRITES"
        else:
            label, expl = put_rc_map.get(put_rc, ("unknown_rc", f"SY-SUBRC={put_rc}"))
            result["phases"]["put"] = {"rc": put_rc, "exception": label, "explanation": expl}
        # CORR (transport assignment)
        if corr_rc is not None:
            result["phases"]["corr_insert"] = {"rc": corr_rc, "status": "OK" if corr_rc == 0 else "FAILED"}
        # ACTIVATE
        if act_rc is not None:
            label = "OK" if act_rc == 0 else f"FAILED rc={act_rc}"
            result["phases"]["activate"] = label
        # POST-VERIFY TADIR (sanity check — catches the functional-but-orphan bug)
        if act_rc == 0:
            try:
                tadir = self.verify_tadir(name, obj_class)
                result["phases"]["verify_tadir"] = tadir
                if tadir.get("orphan"):
                    result["phases"]["verify_tadir"]["warning"] = (
                        "Object active but TADIR row has blank DEVCLASS — "
                        "this is the historical orphan bug. Manual fix needed via "
                        "SE03 'Change Object Directory Entries'."
                    )
            except Exception as ex:
                result["phases"]["verify_tadir"] = f"VERIFY FAILED: {ex}"
        result["writes"] = writes
        return result

    # ── ATC (CODE INSPECTOR) ───────────────────────────────────────────────────
    def atc_run(self, object_uri: str, check_variant: str = "DEFAULT") -> dict:
        """Run ATC on an object. Returns {worklist_id} for use with atc_worklist()."""
        if not self._csrf_token:
            self.fetch_csrf()
        body_xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<atc:run xmlns:atc="http://www.sap.com/adt/atc">'
            '<atc:objectSets><atc:objectSet>'
            f'<atc:adtObject xmlns:adtcore="http://www.sap.com/adt/core" '
            f'adtcore:uri="{object_uri}"/>'
            '</atc:objectSet></atc:objectSets>'
            f'<atc:checkVariant>{check_variant}</atc:checkVariant>'
            '</atc:run>'
        )
        status, body, _ = self._request(
            "POST", "/sap/bc/adt/atc/runs",
            body=body_xml.encode("utf-8"),
            content_type="application/vnd.sap.atc.run.v1+xml",
            raise_on_error=False,
        )
        import re
        text = body.decode("utf-8", errors="replace")
        m = (re.search(r'<[^>]*:worklistId[^>]*>([^<]+)<', text)
             or re.search(r'worklistId="([^"]+)"', text))
        worklist_id = m.group(1) if m else ""
        print(f"  [ADT] atc_run: HTTP {status}, worklist={worklist_id}")
        return {"status": status, "worklist_id": worklist_id, "raw": text[:500]}

    def atc_worklist(self, worklist_id: str) -> list[dict]:
        """Fetch ATC findings (priority, message, location) for a worklist."""
        status, body, _ = self._request(
            "GET", f"/sap/bc/adt/atc/worklists/{worklist_id}",
            extra_headers={"Accept": "application/vnd.sap.atc.worklist.v1+xml"},
            raise_on_error=False,
        )
        import re
        text = body.decode("utf-8", errors="replace")
        findings = []
        for m in re.finditer(
            r'<[^>]*:finding[^>]*priority="([^"]*)"[^>]*>(.*?)</[^>]*:finding>',
            text, re.DOTALL,
        ):
            f = {"priority": m.group(1)}
            msg_m = re.search(r'<[^>]*:messageTitle[^>]*>([^<]+)<', m.group(2))
            if msg_m:
                f["message"] = msg_m.group(1)
            findings.append(f)
        print(f"  [ADT] atc_worklist {worklist_id}: {len(findings)} findings (HTTP {status})")
        return findings


def from_env(system_id: str = "D01") -> "SAPADTClient":
    """Create ADT client from environment variables.
    
    Confirmed working endpoint (D01):
      http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80  client=350
    Discovered by reverse-engineering the ABAP remote filesystem VS Code plugin config.
    """
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)

    prefix = f"SAP_{system_id}_"
    def e(k, d=None):
        return os.getenv(prefix + k) or os.getenv("SAP_" + k) or d

    host     = e("HOST") or e("ASHOST", "HQ-SAP-D01.HQ.INT.UNESCO.ORG")
    client   = e("CLIENT", "350")
    user     = e("USER", "jp_lopez")
    password = e("PASSWD") or e("PASSWORD", "")
    port     = int(e("ADT_PORT", "80"))          # Port 80 HTTP — confirmed from abapfs plugin
    https_str = e("ADT_HTTPS", "false").lower()
    https    = https_str not in ("false", "0", "no")
    return SAPADTClient(host=host, client=client, user=user, password=password,
                        port=port, https=https, verify_ssl=False)


if __name__ == "__main__":
    # Quick connection test
    client = from_env()
    print("Fetching CSRF token from ADT...")
    token = client.fetch_csrf()
    print(f"Token: {token}")

    print("\nSearching for ZCL_CRP_PROCESS_REQ...")
    results = client.search_object("ZCL_CRP_PROCESS_REQ", "CLASS")
    for r in results:
        print(f"  Found: {r}")
