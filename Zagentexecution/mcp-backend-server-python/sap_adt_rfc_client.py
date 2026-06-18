"""
sap_adt_rfc_client.py — SAP ADT client via SADT_REST_RFC_ENDPOINT RFC

REPLACES sap_adt_client.py (urllib + CSRF + cookie jar).
Uses pyrfc to call SADT_REST_RFC_ENDPOINT directly — same auth as the
existing pyrfc connection, zero HTTP plumbing.

Proven on D01 (ECC EhP8): SADT_REST_RFC_ENDPOINT exists, returns 200.

Architecture (from openadt/AdtRestRfcClient.java):
  RFC INPUT:  REQUEST { REQUEST_LINE{METHOD,URI,VERSION}, HEADER_FIELDS[], MESSAGE_BODY }
  RFC OUTPUT: RESPONSE { STATUS_LINE{STATUS_CODE,REASON_PHRASE}, HEADER_FIELDS[], MESSAGE_BODY }

Supported object types and ADT URI patterns (same as sap_adt_client.py):
  CLASS   → /sap/bc/adt/oo/classes/{name}
  INTF    → /sap/bc/adt/oo/interfaces/{name}
  PROG    → /sap/bc/adt/programs/programs/{name}
  INCLUDE → /sap/bc/adt/programs/includes/{name}
  FUGR    → /sap/bc/adt/functions/groups/{name}
  FUNC    → /sap/bc/adt/functions/groups/{fg}/fmodules/{name}
  TABL    → /sap/bc/adt/ddic/tables/{name}
  DTEL    → /sap/bc/adt/ddic/dataelements/{name}
  DOMA    → /sap/bc/adt/ddic/domains/{name}
  ENHO    → /sap/bc/adt/enhancements/{name}
"""

import os
import xml.etree.ElementTree as ET
from typing import Optional
from dotenv import load_dotenv

# ── RFC function name (proven on ECC EhP8 D01) ─────────────────────────────
_RFC_FM = "SADT_REST_RFC_ENDPOINT"

# ── INCIDENT KILL-SWITCH (added 2026-06-12, INC-CLASS-LOSS) ────────────────
# This client's write/activate path CORRUPTED D01 classes (lossy CLIF_GET_SOURCE
# restore + writing to classes with missing SEOCLASS). ALL mutating operations
# are HARD-DISABLED until the read-fallback and SEOCLASS-guard bugs are fixed and
# reviewed. Reads remain fully functional. To re-enable (only after the fix):
#   set env ALLOW_D01_WRITES=1  AND  remove this block deliberately.
def _writes_blocked():
    import os as _os
    if _os.getenv("ALLOW_D01_WRITES") == "1":
        return
    raise RuntimeError(
        "D01 WRITES DISABLED (INC-CLASS-LOSS 2026-06-12). "
        "This client corrupted classes via lossy restore / missing-SEOCLASS writes. "
        "Mutating ADT ops are blocked. See "
        "knowledge/incidents/INC-CLASS-LOSS-2026-06_adt_rfc_write_corruption.md"
    )

# ── ADT URI templates ────────────────────────────────────────────────────────
_URI = {
    "CLASS":   "/sap/bc/adt/oo/classes/{name}",
    "INTF":    "/sap/bc/adt/oo/interfaces/{name}",
    "PROG":    "/sap/bc/adt/programs/programs/{name}",
    "INCLUDE": "/sap/bc/adt/programs/includes/{name}",
    "FUGR":    "/sap/bc/adt/functions/groups/{name}",
    "FUNC":    "/sap/bc/adt/functions/groups/{group}/fmodules/{name}",
    "TABL":    "/sap/bc/adt/ddic/tables/{name}",
    "DTEL":    "/sap/bc/adt/ddic/dataelements/{name}",
    "DOMA":    "/sap/bc/adt/ddic/domains/{name}",
    "ENHO":    "/sap/bc/adt/enhancements/{name}",
}


class AdtRfcError(Exception):
    """Raised when ADT returns a non-2xx status."""
    def __init__(self, status: int, reason: str, body: str):
        self.status = status
        self.reason = reason
        self.body = body
        super().__init__(f"ADT {status} {reason}: {body[:200]}")


class SapAdtRfcClient:
    """
    SAP ADT client backed by SADT_REST_RFC_ENDPOINT.

    Usage:
        from pyrfc import Connection
        conn = Connection(ashost=..., sysnr=..., client=..., user=..., passwd=...)
        adt = SapAdtRfcClient(conn)

        src = adt.read_source("PROG", "SAPF100")
        adt.write_source("CLASS", "ZMY_CLASS", new_source, package="ZLOCAL")
    """

    def __init__(self, conn):
        """
        conn: open pyrfc.Connection instance.
        The connection must already be authenticated — no extra auth needed.
        """
        self._conn = conn

    # ── Low-level RFC call ───────────────────────────────────────────────────

    def _call(self, method: str, uri: str,
              headers: Optional[dict] = None,
              body: bytes = b"") -> tuple[int, str, dict, bytes]:
        """
        Execute one ADT HTTP request via SADT_REST_RFC_ENDPOINT.
        Returns (status_code, reason, response_headers, body_bytes).
        """
        hdr_list = []
        if headers:
            for name, value in headers.items():
                hdr_list.append({"NAME": name, "VALUE": str(value)})

        result = self._conn.call(
            _RFC_FM,
            REQUEST={
                "REQUEST_LINE": {
                    "METHOD": method,
                    "URI": uri,
                    "VERSION": "HTTP/1.1",
                },
                "HEADER_FIELDS": hdr_list,
                "MESSAGE_BODY": body,
            }
        )

        resp = result["RESPONSE"]
        status = int(resp["STATUS_LINE"]["STATUS_CODE"])
        reason = resp["STATUS_LINE"]["REASON_PHRASE"]
        body_out = bytes(resp["MESSAGE_BODY"]) if resp["MESSAGE_BODY"] else b""

        resp_headers = {}
        for row in resp.get("HEADER_FIELDS", []):
            resp_headers[row["NAME"].lower()] = row["VALUE"]

        return status, reason, resp_headers, body_out

    def _require_ok(self, status: int, reason: str,
                    body_bytes: bytes, context: str = ""):
        if status >= 400:
            raise AdtRfcError(status, reason,
                              body_bytes.decode("utf-8", errors="replace"))

    # ── URI helpers ──────────────────────────────────────────────────────────

    def _uri(self, obj_type: str, name: str,
             suffix: str = "", group: str = "") -> str:
        """Build object URI; obj_type must be a key of _URI.
        ECC EhP8: ADT URIs require lowercase object names (proven D01).
        """
        obj_type = obj_type.upper()
        if obj_type not in _URI:
            raise ValueError(f"Unknown object type: {obj_type}. "
                             f"Supported: {list(_URI)}")
        template = _URI[obj_type]
        name_lc  = name.lower()
        group_lc = group.lower()
        if obj_type == "FUNC":
            return template.format(group=group_lc, name=name_lc) + suffix
        return template.format(name=name_lc) + suffix

    # ── Session warmup ───────────────────────────────────────────────────────

    def _warmup(self) -> None:
        """
        Warm up the ADT HTTP session inside SADT_REST_RFC_ENDPOINT.
        REQUIRED as first call on ECC EhP8 D01: without it, subsequent
        resource reads return 404 even for existing objects.
        A GET to /sap/bc/adt/discovery initializes the ADT HTTP context.
        """
        self._call("GET", "/sap/bc/adt/discovery",
                   headers={"Accept": "application/xml"})

    # ── Discovery ────────────────────────────────────────────────────────────

    def discovery(self) -> str:
        """Fetch ADT discovery document (XML). Useful for capability check."""
        status, reason, _, body = self._call(
            "GET", "/sap/bc/adt/discovery",
            headers={"Accept": "application/xml"}
        )
        self._require_ok(status, reason, body, "discovery")
        return body.decode("utf-8", errors="replace")

    # ── Read source ──────────────────────────────────────────────────────────

    def _read_source_rfc_fallback(self, obj_type: str, name: str) -> str:
        """
        RFC fallback for reading source when ADT returns 404.
        Covers $TMP objects (not indexed by ADT) and any other non-discoverable object.

        CLASS/INTF  → CLIF_GET_SOURCE via RFC_ABAP_INSTALL_AND_RUN
                       Reads from SEO* tables — works for $TMP and proper packages.
        PROG/INCLUDE → SIW_RFC_READ_REPORT (direct RFC, proven on D01)

        Raises AdtRfcError(404) if object is not found via RFC either.
        """
        ot = obj_type.upper()
        nm = name.upper()

        if ot in ("CLASS", "CLAS", "INTF"):
            # CLIF_GET_SOURCE reads from SEO* class repository — works for $TMP and proper packages.
            # Called via RFC_ABAP_INSTALL_AND_RUN because CLIF_GET_SOURCE itself is not RFC-enabled.
            #
            # Proven D01 call format:
            #   INPUT:  PROGRAM = [{"LINE": "abap line"}, ...], MODE = "F"
            #   OUTPUT: WRITES  = [{"ZEILE": "output line"}, ...]
            abap_lines = [
                {"LINE": "REPORT ZREAD_SRC NO STANDARD PAGE HEADING."},
                {"LINE": "DATA: lt TYPE STANDARD TABLE OF seop_source_file,"},
                {"LINE": "      ls LIKE LINE OF lt, lv TYPE c LENGTH 255."},
                {"LINE": f"CALL FUNCTION 'CLIF_GET_SOURCE'"},
                {"LINE": f"  EXPORTING clskey = '{nm}'"},
                {"LINE":  "  TABLES source_lines = lt."},
                {"LINE": "LOOP AT lt INTO ls. lv = ls-line. WRITE: / lv. ENDLOOP."},
            ]
            result = self._conn.call(
                "RFC_ABAP_INSTALL_AND_RUN",
                PROGRAM=abap_lines,
                MODE="F",
            )
            writes = result.get("WRITES", [])
            if not writes:
                raise AdtRfcError(
                    404, "NotFound",
                    f"{ot}/{name} — not found via ADT or CLIF_GET_SOURCE fallback"
                )
            return "\n".join(w.get("ZEILE", "").rstrip() for w in writes)

        elif ot in ("PROG", "INCLUDE", "FUGR"):
            result = self._conn.call("SIW_RFC_READ_REPORT", I_NAME=nm)
            lines = result.get("E_TAB_CODE", [])
            if not lines:
                raise AdtRfcError(404, "NotFound", f"{ot}/{name} not found")
            return "\n".join(ln.get("LINE", "") for ln in lines)

        else:
            raise AdtRfcError(
                404, "NotFound",
                f"No RFC fallback implemented for {ot} — object must be in a proper package for ADT"
            )

    def read_source(self, obj_type: str, name: str,
                    include: str = "", group: str = "") -> str:
        """
        Download ABAP source code for an object.

        obj_type: CLASS, PROG, INCLUDE, FUGR, FUNC, INTF, TABL, DTEL, DOMA, ENHO
        name:     object name (uppercase)
        include:  CLASS include suffix e.g. 'source/main', 'includes/definitions'
                  (defaults to 'source/main')
        group:    function group name (only for FUNC)

        Returns: source code as string.

        Strategy (D01):
          1. ADT via SADT_REST_RFC_ENDPOINT  — indexed objects (proper packages)
          2. RFC fallback (_read_source_rfc_fallback) — $TMP + any 404 from ADT
        """
        suffix = f"/{include}" if include else "/source/main"
        uri = self._uri(obj_type, name.upper(), suffix=suffix, group=group)
        status, reason, _, body = self._call(
            "GET", uri, headers={"Accept": "text/plain"}
        )
        if status == 404:
            # Object not in ADT index — common for $TMP (local package).
            # Fall back to RFC-based reading.
            return self._read_source_rfc_fallback(obj_type, name)
        self._require_ok(status, reason, body, f"read_source {obj_type}/{name}")
        return body.decode("utf-8", errors="replace")

    # ── Check object in TADIR ────────────────────────────────────────────────

    def check_tadir(self, obj_type: str, name: str) -> dict:
        """
        Look up an object in TADIR. Returns package, author, creation date.
        Useful for debugging 404s (is object in $TMP? does it exist at all?).

        obj_type: CLAS, PROG, INTF, FUGR, TABL, DTEL, DOMA, ENHO (TADIR notation)
        """
        tadir_map = {
            "CLASS": "CLAS", "CLAS": "CLAS", "INTF": "INTF",
            "PROG": "PROG",  "INCLUDE": "PROG",
            "FUGR": "FUGR",  "FUNC": "FUGR",
            "TABL": "TABL",  "DTEL": "DTEL",
            "DOMA": "DOMA",  "ENHO": "ENHO",
        }
        tadir_type = tadir_map.get(obj_type.upper(), obj_type.upper())
        result = self._conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="TADIR",
            DELIMITER="|",
            FIELDS=[
                {"FIELDNAME": "OBJ_NAME"},
                {"FIELDNAME": "DEVCLASS"},
                {"FIELDNAME": "AUTHOR"},
                {"FIELDNAME": "CREATED_ON"},
                {"FIELDNAME": "SRCSYSTEM"},
            ],
            OPTIONS=[{
                "TEXT": f"OBJECT = '{tadir_type}' AND OBJ_NAME = '{name.upper()}'"
            }],
            ROWCOUNT=1,
        )
        data = result.get("DATA", [])
        if not data:
            return {"found": False, "name": name, "tadir_type": tadir_type}
        parts = data[0]["WA"].split("|")
        return {
            "found":     True,
            "name":      parts[0].strip() if len(parts) > 0 else name,
            "package":   parts[1].strip() if len(parts) > 1 else "?",
            "author":    parts[2].strip() if len(parts) > 2 else "?",
            "created":   parts[3].strip() if len(parts) > 3 else "?",
            "system":    parts[4].strip() if len(parts) > 4 else "?",
            "is_tmp":    (parts[1].strip() if len(parts) > 1 else "") == "$TMP",
        }

    # ── Lock / Unlock ────────────────────────────────────────────────────────

    def lock(self, obj_type: str, name: str, group: str = "") -> str:
        """
        Lock an object for editing.
        Returns: lock handle string (needed for write and unlock).
        """
        uri = self._uri(obj_type, name.upper(), group=group)
        status, reason, resp_headers, body = self._call(
            "POST", uri + "?_action=LOCK&accessMode=MODIFY",
            headers={
                "X-SAP-ADT-SessionType": "stateful",
                "Accept": "application/xml",
            }
        )
        self._require_ok(status, reason, body, f"lock {obj_type}/{name}")

        # Lock handle XML on ECC EhP8 (proven D01):
        # <asx:abap><asx:values><DATA><LOCK_HANDLE>xxxxx</LOCK_HANDLE></DATA></asx:values></asx:abap>
        # Also handle Eclipse ADT format: <adtcore:lockHandle>xxxxx</adtcore:lockHandle>
        body_str = body.decode("utf-8", errors="replace")
        try:
            root = ET.fromstring(body_str)
            # ECC format: LOCK_HANDLE element anywhere in tree
            for el in root.iter():
                if el.tag.endswith("LOCK_HANDLE") or el.tag.endswith("lockHandle"):
                    if el.text and el.text.strip():
                        return el.text.strip()
            # Fallback: check response header
            if "lock-handle" in resp_headers:
                return resp_headers["lock-handle"]
        except ET.ParseError:
            pass

        raise AdtRfcError(status, reason,
                          f"Could not parse lock handle from: {body_str[:300]}")

    def unlock(self, obj_type: str, name: str, lock_handle: str,
               group: str = "") -> None:
        """Release a lock."""
        import urllib.parse
        encoded = urllib.parse.quote(lock_handle, safe="")
        uri = self._uri(obj_type, name.upper(), group=group)
        status, reason, _, body = self._call(
            "DELETE", f"{uri}?lockHandle={encoded}",
            headers={"X-SAP-ADT-SessionType": "stateful"}
        )
        self._require_ok(status, reason, body, f"unlock {obj_type}/{name}")

    # ── Write source ─────────────────────────────────────────────────────────

    def write_source(self, obj_type: str, name: str, source: str,
                     lock_handle: str, include: str = "",
                     group: str = "") -> None:
        """
        Write ABAP source to a locked object.
        Call lock() first to get lock_handle.
        """
        _writes_blocked()
        import urllib.parse
        suffix = f"/{include}" if include else "/source/main"
        uri = self._uri(obj_type, name.upper(), suffix=suffix, group=group)
        encoded_lock = urllib.parse.quote(lock_handle, safe="")

        body_bytes = source.encode("utf-8")
        status, reason, _, body = self._call(
            "PUT", f"{uri}?lockHandle={encoded_lock}",
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "X-SAP-ADT-SessionType": "stateful",
            },
            body=body_bytes
        )
        self._require_ok(status, reason, body, f"write_source {obj_type}/{name}")

    # ── Syntax check ─────────────────────────────────────────────────────────

    def syntax_check(self, obj_type: str, name: str,
                     group: str = "") -> list[dict]:
        """
        Run ADT syntax check. Returns list of findings (empty = clean).
        Each finding: {severity, message, line, uri}
        No CSRF token needed — RFC call handles auth.
        """
        obj_uri = self._uri(obj_type, name.upper(), group=group)
        # ADT type IDs: CLAS→CLAS/OC, PROG→PROG/P, FUGR→FUGR/FF, INTF→INTF/OI
        type_id_map = {
            "CLASS": "CLAS/OC", "INTF": "INTF/OI",
            "PROG": "PROG/P",   "INCLUDE": "PROG/I",
            "FUGR": "FUGR/FF",  "TABL": "TABL/DT",
        }
        type_id = type_id_map.get(obj_type.upper(), obj_type.upper())

        # ECC EhP8 namespace: http://www.sap.com/adt/checkrun (proven from error msg)
        payload = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<checkRun:checkObjectList '
            'xmlns:checkRun="http://www.sap.com/adt/checkrun" '
            'xmlns:adtcore="http://www.sap.com/adt/core">'
            f'<checkRun:checkObject checkRun:object="programInclude" '
            f'adtcore:objectTypeId="{type_id}" adtcore:uri="{obj_uri}"/>'
            '</checkRun:checkObjectList>'
        )
        status, reason, _, body = self._call(
            "POST", "/sap/bc/adt/checkruns",
            headers={
                "Content-Type": "application/vnd.sap.adt.checkobjects+xml",
                "Accept": "application/xml",
            },
            body=payload.encode("utf-8")
        )
        self._require_ok(status, reason, body, f"syntax_check {obj_type}/{name}")

        findings = []
        body_str = body.decode("utf-8", errors="replace")
        try:
            root = ET.fromstring(body_str)
            for msg in root.iter():
                if msg.tag.endswith("checkMessage"):
                    findings.append({
                        "severity": msg.get("severity", ""),
                        "message":  msg.get("shortText", ""),
                        "line":     msg.get("line", ""),
                        "uri":      msg.get("uri", ""),
                    })
        except ET.ParseError:
            pass
        return findings

    # ── Activate ─────────────────────────────────────────────────────────────

    def activate(self, obj_type: str, name: str, group: str = "") -> bool:
        """
        Activate an ABAP object.
        Returns True if activation succeeded.
        Raises AdtRfcError on activation failure.
        """
        _writes_blocked()
        obj_uri = self._uri(obj_type, name.upper(), group=group)
        type_id_map = {
            "CLASS": "CLAS/OC", "INTF": "INTF/OI",
            "PROG": "PROG/P",   "INCLUDE": "PROG/I",
            "FUGR": "FUGR/FF",  "TABL": "TABL/DT",
            "DTEL": "DTEL/DE",  "DOMA": "DOMA/DO",
        }
        type_id = type_id_map.get(obj_type.upper(), obj_type.upper())

        # Activation XML — ECC EhP8 proven format (from error: expected objectReferences):
        payload = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<adtcore:objectReferences '
            'xmlns:adtcore="http://www.sap.com/adt/core">'
            f'<adtcore:objectReference adtcore:uri="{obj_uri}" '
            f'adtcore:name="{name.upper()}" adtcore:type="{type_id}"/>'
            '</adtcore:objectReferences>'
        )
        # ECC EhP8: requires ?method=activate query param (proven D01)
        status, reason, _, body = self._call(
            "POST", "/sap/bc/adt/activation?method=activate",
            headers={
                "Content-Type": "application/vnd.sap.adt.activation.request+xml",
                "Accept": "application/xml,"
                          "application/vnd.sap.adt.activationresults+xml",
            },
            body=payload.encode("utf-8")
        )
        if status in (200, 204):
            return True
        self._require_ok(status, reason, body, f"activate {obj_type}/{name}")
        return True

    # ── High-level: full deploy cycle ────────────────────────────────────────

    def deploy(self, obj_type: str, name: str, source: str,
               include: str = "", group: str = "",
               skip_syntax_check: bool = False) -> dict:
        """
        Full deploy: SEOCLASS-check → lock → write → syntax_check → UNLOCK → activate.

        CRITICAL (proven D01 ECC EhP8):
        - Activate must be called AFTER unlock (403 "currently editing" if lock held).
        - SEOCLASS is pre-checked to ensure class is registered before writing.
          Writing to a class with missing SEOCLASS leaves it in unrecoverable state.

        Example:
            result = adt.deploy("CLASS", "ZCL_CRP_CERT_READER", new_source)
        """
        result = {
            "object":    f"{obj_type}/{name}",
            "locked":    False,
            "written":   False,
            "syntax_ok": None,
            "activated": False,
            "findings":  [],
        }

        # Pre-flight: for CLASS objects, verify SEOCLASS registration exists.
        # Writing to a class without SEOCLASS corrupts it (learned D01 2026-06-07).
        if obj_type.upper() in ("CLASS", "CLAS"):
            info = self.check_tadir(obj_type, name)
            if not info.get("found"):
                raise AdtRfcError(
                    404, "NotFound",
                    f"CLASS/{name} not found in TADIR — create it first in SE24"
                )
            seo = self._conn.call(
                "RFC_READ_TABLE",
                QUERY_TABLE="SEOCLASS",
                OPTIONS=[{"TEXT": f"CLSNAME = '{name.upper()}'"}],
                ROWCOUNT=1,
            )
            if not seo.get("DATA"):
                raise AdtRfcError(
                    412, "PreconditionFailed",
                    f"CLASS/{name} has no SEOCLASS entry — class metadata missing. "
                    f"Open SE24 → {name.upper()} → check state before deploying."
                )

        lock_handle = None
        try:
            lock_handle = self.lock(obj_type, name, group=group)
            result["locked"] = True

            self.write_source(obj_type, name, source,
                              lock_handle, include=include, group=group)
            result["written"] = True

            if not skip_syntax_check:
                findings = self.syntax_check(obj_type, name, group=group)
                result["findings"] = findings
                errors = [f for f in findings if f.get("severity") in ("E", "A")]
                result["syntax_ok"] = len(errors) == 0
                if errors:
                    # Unlock before raising so the object is not left locked
                    self.unlock(obj_type, name, lock_handle, group=group)
                    lock_handle = None
                    raise AdtRfcError(0, "SyntaxError", str(errors))

            # UNLOCK before activate — required on ECC EhP8.
            # Activate with lock held → 403 "User X is currently editing Y".
            self.unlock(obj_type, name, lock_handle, group=group)
            lock_handle = None  # cleared — finally block will skip unlock

            self.activate(obj_type, name, group=group)
            result["activated"] = True

        finally:
            # Only runs if lock_handle is still set (i.e. unlock was not reached)
            if lock_handle:
                try:
                    self.unlock(obj_type, name, lock_handle, group=group)
                except Exception:
                    pass

        return result

    # ── Search / existence check ─────────────────────────────────────────────

    def object_exists(self, obj_type: str, name: str,
                      group: str = "") -> bool:
        """Check if an ABAP object exists (HEAD request)."""
        uri = self._uri(obj_type, name.upper(), group=group)
        status, _, _, _ = self._call("GET", uri,
                                     headers={"Accept": "application/xml"})
        return status < 400

    def search(self, query: str, obj_type: str = "",
               max_results: int = 10) -> list[dict]:
        """
        Search ADT repository objects.
        Returns list of {name, type, description, uri}.
        """
        import urllib.parse
        # ECC EhP8 quicksearch format (proven D01):
        # operation=quickSearch&query=<name*>&maxResults=N
        params = (f"operation=quickSearch"
                  f"&query={urllib.parse.quote(query)}"
                  f"&maxResults={max_results}")
        if obj_type:
            params += f"&objectType={urllib.parse.quote(obj_type)}"
        uri = f"/sap/bc/adt/repository/informationsystem/search?{params}"
        status, reason, _, body = self._call(
            "GET", uri, headers={"Accept": "application/xml"}
        )
        self._require_ok(status, reason, body, f"search {query}")

        results = []
        body_str = body.decode("utf-8", errors="replace")
        try:
            root = ET.fromstring(body_str)
            # ECC EhP8: xmlns:adtcore="http://www.sap.com/adt/core"
            NS = "http://www.sap.com/adt/core"
            for obj in root.iter(f"{{{NS}}}objectReference"):
                name_attr = obj.get(f"{{{NS}}}name", "")
                type_attr = obj.get(f"{{{NS}}}type", "")
                desc_attr = obj.get(f"{{{NS}}}description", "")
                uri_attr  = obj.get(f"{{{NS}}}uri", "")
                pkg_attr  = obj.get(f"{{{NS}}}packageName", "")
                if name_attr:
                    results.append({
                        "name":        name_attr,
                        "type":        type_attr,
                        "description": desc_attr,
                        "uri":         uri_attr,
                        "package":     pkg_attr,
                    })
        except ET.ParseError:
            pass
        return results


# ── Convenience factory ──────────────────────────────────────────────────────

def from_env(system_id: str = "D01") -> "SapAdtRfcClient":
    """
    Build a SapAdtRfcClient from environment variables.
    Reads from .env in the same directory.

    system_id: "D01" or "P01"

    Note: calls discovery() on first use to warm up the ADT HTTP session
    inside SADT_REST_RFC_ENDPOINT (proven required on ECC EhP8 D01).
    """
    from pyrfc import Connection

    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)

    prefix = f"SAP_{system_id}_"

    def get(key, default=None):
        return (os.getenv(prefix + key)
                or os.getenv("SAP_" + key)
                or default)

    conn = Connection(
        ashost=get("ASHOST"),
        sysnr=get("SYSNR"),
        client=get("CLIENT"),
        user=get("USER"),
        passwd=get("PASSWD") or get("PASSWORD"),
        lang="EN",
    )
    client = SapAdtRfcClient(conn)
    client._warmup()          # initialize ADT HTTP session
    return client


# ── Quick smoke test ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    system = sys.argv[1] if len(sys.argv) > 1 else "D01"
    print(f"Smoke test — {system}")

    adt = from_env(system)

    # 1. Discovery
    disc = adt.discovery()
    print(f"  discovery: {len(disc)} chars OK")

    # 2. Read SAPF100
    src = adt.read_source("PROG", "SAPF100")
    print(f"  SAPF100 source: {len(src)} chars OK")
    print(f"  First line: {src.splitlines()[0]}")

    # 3. Existence check
    exists = adt.object_exists("PROG", "SAPF100")
    print(f"  SAPF100 exists: {exists}")

    exists_fake = adt.object_exists("PROG", "ZZNOTEXIST999")
    print(f"  ZZNOTEXIST999 exists: {exists_fake}")

    print("Smoke test passed.")
