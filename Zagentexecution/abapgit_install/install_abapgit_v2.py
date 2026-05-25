"""
install_abapgit_v2.py — Bypass the buggy wrapper. Direct urllib calls with the
exact XML payload from marcellourbani/abap-adt-api (MIT) for PROG/P creation.

Why v2: v1 hit HTTP 400 on POST /programs/programs because sap_adt_client.create_object
builds xmlns:program="http://www.sap.com/adt/programs" but SAP expects
xmlns:program="http://www.sap.com/adt/programs/programs" (full path). v2 inlines
the correct XML and uses a 300s timeout for the 4.86 MB source PUT.
"""
import os, sys, time, base64, ssl
import urllib.request, urllib.parse, urllib.error
from dotenv import load_dotenv

# Load .env from sibling mcp-backend-server-python folder
DOTENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "mcp-backend-server-python", ".env")
load_dotenv(DOTENV_PATH)

HOST     = os.getenv("SAP_D01_HOST") or os.getenv("SAP_HOST") or "HQ-SAP-D01.HQ.INT.UNESCO.ORG"
CLIENT   = os.getenv("SAP_D01_CLIENT") or os.getenv("SAP_CLIENT") or "350"
USER     = os.getenv("SAP_D01_USER")   or os.getenv("SAP_USER")
PASSWORD = os.getenv("SAP_D01_PASSWD") or os.getenv("SAP_PASSWD") or os.getenv("SAP_PASSWORD")
PORT     = int(os.getenv("SAP_D01_ADT_PORT") or os.getenv("SAP_ADT_PORT") or "80")
HTTPS    = (os.getenv("SAP_D01_ADT_HTTPS") or os.getenv("SAP_ADT_HTTPS") or "false").lower() in ("1", "true", "yes")
SCHEME   = "https" if HTTPS else "http"
BASE     = f"{SCHEME}://{HOST}:{PORT}"

SOURCE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "zabapgit_standalone_2026-05-25.abap")
PROG_NAME = "ZABAPGIT_STANDALONE"
PROG_DESC = "abapGit standalone - official build"
PACKAGE   = "$TMP"

# ── HTTP helpers (no wrapper) ──────────────────────────────────────────────────
auth = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
ctx  = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
COOKIES = {}
CSRF    = None

def call(method, path, body=None, params=None, extra_headers=None, content_type=None,
         timeout=60, accept="application/xml"):
    global CSRF
    qs = {"sap-client": CLIENT}
    if params: qs.update(params)
    url = f"{BASE}{path}?{urllib.parse.urlencode(qs)}"
    headers = {
        "Authorization": f"Basic {auth}",
        "Accept": accept,
        "X-CSRF-Token": CSRF or "Fetch",
    }
    if COOKIES:
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in COOKIES.items())
    if content_type:
        headers["Content-Type"] = content_type
    if extra_headers:
        headers.update(extra_headers)
    if isinstance(body, str):
        body = body.encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            status = resp.status
            data = resp.read()
            new_csrf = resp.getheader("X-CSRF-Token")
            if new_csrf and new_csrf != "Required":
                CSRF = new_csrf
            sc = resp.getheader("Set-Cookie") or ""
            for part in sc.split(","):
                kv = part.strip().split(";")[0]
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    COOKIES[k.strip()] = v.strip()
            return status, data, dict(resp.headers)
    except urllib.error.HTTPError as e:
        data = e.read() if e.fp else b""
        return e.code, data, dict(e.headers) if e.headers else {}

# ── 1. CSRF ────────────────────────────────────────────────────────────────────
print(f"[ADT] {BASE}  client={CLIENT}  user={USER}")
print(f"[1/6] Fetching CSRF token")
status, body, _ = call("GET", "/sap/bc/adt/discovery", extra_headers={"X-CSRF-Token": "Fetch"})
if status != 200 or not CSRF:
    print(f"      FAILED: HTTP {status}  csrf={CSRF!r}")
    print(f"      body: {body[:300]}")
    sys.exit(1)
print(f"      CSRF ok: {CSRF[:20]}...")

# ── 2. Create PROG ─────────────────────────────────────────────────────────────
print(f"\n[2/6] Creating PROG/P {PROG_NAME} in {PACKAGE}")
xml_create = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<program:abapProgram '
    'xmlns:program="http://www.sap.com/adt/programs/programs" '
    'xmlns:adtcore="http://www.sap.com/adt/core" '
    f'adtcore:description="{PROG_DESC}" '
    f'adtcore:name="{PROG_NAME}" '
    'adtcore:type="PROG/P" '
    'adtcore:language="EN" '
    'adtcore:masterLanguage="EN" '
    f'adtcore:responsible="{USER.upper()}">'
    f'<adtcore:packageRef adtcore:name="{PACKAGE}"/>'
    '</program:abapProgram>'
)
status, body, _ = call("POST", "/sap/bc/adt/programs/programs",
                       body=xml_create, content_type="application/vnd.sap.adt.programs.programs.v2+xml")
print(f"      HTTP {status}")
if status == 200 or status == 201:
    print(f"      PROG created")
elif b"already exists" in body or b"AlreadyExists" in body:
    print(f"      PROG already exists — proceeding to source upload")
else:
    print(f"      body: {body[:500].decode('utf-8', errors='replace')}")
    sys.exit(2)

# ── 3. Lock ────────────────────────────────────────────────────────────────────
# IMPORTANT (NW 7.40 EhP8): for PROG/P source writes, lock the source URL
# (.../source/main) directly, not the program shell. The shell lock returns
# IS_LOCAL=X but its handle is invalid against the source/main endpoint
# (HTTP 423 "Resource INCLUDE is not locked").
prog_uri = f"/sap/bc/adt/programs/programs/{PROG_NAME.lower()}"
source_uri = f"{prog_uri}/source/main"
print(f"\n[3/6] Locking {source_uri}")
status, body, _ = call("POST", source_uri,
                       params={"_action": "LOCK", "accessMode": "MODIFY"},
                       extra_headers={"Accept": "application/vnd.sap.as+xml, application/xml"})
print(f"      HTTP {status}")
if status >= 400:
    print(f"      body: {body[:500].decode('utf-8', errors='replace')}")
    sys.exit(3)
import re
text = body.decode("utf-8", errors="replace")
m = (re.search(r'<LOCK_HANDLE>([^<]+)</LOCK_HANDLE>', text)
     or re.search(r'<[^>]*:lockHandle[^>]*>([^<]+)<', text)
     or re.search(r'lockHandle["\':>]*([A-Za-z0-9+/=]{20,})', text))
LOCK = m.group(1).strip() if m else ""
if not LOCK:
    print(f"      Could not parse lockHandle from response: {text[:500]}")
    sys.exit(3)
print(f"      lock: {LOCK[:30]}...")

# ── 4. PUT source (4.86 MB) ────────────────────────────────────────────────────
print(f"\n[4/6] Reading {SOURCE_FILE}")
with open(SOURCE_FILE, "rb") as f:
    source = f.read()
print(f"      {len(source):,} bytes")
print(f"      Uploading to {prog_uri}/source/main with 300s timeout")
t0 = time.time()
status, body, _ = call("PUT", f"{prog_uri}/source/main", body=source,
                       params={"lockHandle": LOCK},
                       extra_headers={"X-adtcore-locktoken": LOCK},
                       content_type="text/plain; charset=utf-8",
                       timeout=300)
elapsed = time.time() - t0
print(f"      HTTP {status}  ({elapsed:.1f}s)")
if status >= 400:
    print(f"      body: {body[:1000].decode('utf-8', errors='replace')}")
    # try to unlock
    enc = urllib.parse.quote(LOCK, safe="")
    call("DELETE", f"/sap/bc/adt/locks/{enc}", extra_headers={"X-adtcore-locktoken": LOCK})
    sys.exit(4)

# ── 5. Activate ────────────────────────────────────────────────────────────────
print(f"\n[5/6] Activating {PROG_NAME}")
activate_xml = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<adtcore:objectReferences xmlns:adtcore="http://www.sap.com/adt/core">'
    f'<adtcore:objectReference adtcore:uri="{prog_uri}" adtcore:name="{PROG_NAME}"/>'
    '</adtcore:objectReferences>'
)
status, body, _ = call("POST", "/sap/bc/adt/activation",
                       params={"method": "activate", "preauditRequested": "true"},
                       body=activate_xml,
                       content_type="application/xml")
print(f"      HTTP {status}  ({len(body)} bytes response)")
if body:
    preview = body[:800].decode("utf-8", errors="replace")
    print(f"      response: {preview}")

# ── 6. Unlock ──────────────────────────────────────────────────────────────────
print(f"\n[6/6] Unlocking")
enc = urllib.parse.quote(LOCK, safe="")
status, body, _ = call("DELETE", f"/sap/bc/adt/locks/{enc}",
                       extra_headers={"X-adtcore-locktoken": LOCK})
print(f"      HTTP {status}")

print(f"\nDONE. Now run check_abapgit_installed.py to verify TADIR/TRDIR.")
