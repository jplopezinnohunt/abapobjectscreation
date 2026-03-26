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
                 content_type: str = None) -> tuple[int, bytes, dict]:
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
            new_csrf = e.headers.get("X-CSRF-Token")
            if new_csrf:
                self._csrf_token = new_csrf
            return e.code, body_data, dict(e.headers)

    def fetch_csrf(self) -> str:
        """Fetch CSRF token via HEAD request to discovery endpoint."""
        print("  [ADT] Fetching CSRF token...")
        status, body, headers = self._request("GET", "/sap/bc/adt/discovery",
                                                extra_headers={"X-CSRF-Token": "Fetch"})
        if self._csrf_token:
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
        params = {"query": query, "maxResults": max_results}
        if obj_type:
            params["objectType"] = obj_type
        status, body, _ = self._request(
            "GET", "/sap/bc/adt/repository/informationsystem/search", params=params,
            extra_headers={"Accept": "application/xml"}
        )
        # Parse simple XML for URIs
        import re
        objects = []
        text = body.decode("utf-8", errors="replace")
        for m in re.finditer(r'adtcore:uri="([^"]+)"[^>]*adtcore:name="([^"]+)"[^>]*adtcore:type="([^"]+)"', text):
            objects.append({"uri": m.group(1), "name": m.group(2), "type": m.group(3)})
        if not objects:
            # Second pattern
            for m in re.finditer(r'name="([^"]+)".*?type="([^"]+)".*?uri="([^"]+)"', text):
                objects.append({"name": m.group(1), "type": m.group(2), "uri": m.group(3)})
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
