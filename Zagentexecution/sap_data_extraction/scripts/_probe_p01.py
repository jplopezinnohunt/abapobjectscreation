"""
_probe_p01.py — minimal connection + one-RFC smoke test. ~5 sec.

Runs:
  1. ConnectionGuard.connect() to P01
  2. One RFC_READ_TABLE call: T042Z, 1 row, 3 fields
  3. Print result, close, exit

If this fails or hangs, the full extractor can't work either.
"""
import sys, os, time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
MCP = os.path.abspath(os.path.join(SCRIPTS_DIR, "..", "..", "mcp-backend-server-python"))
if MCP not in sys.path: sys.path.insert(0, MCP)

from rfc_helpers import ConnectionGuard

print("[1/4] Building connection params...", flush=True)
t0 = time.time()
g = ConnectionGuard("P01")
print(f"      params built in {time.time()-t0:.2f}s", flush=True)

print("[2/4] Connecting to P01 (SNC)...", flush=True)
t0 = time.time()
try:
    g.connect()
except Exception as e:
    print(f"      FAILED in {time.time()-t0:.2f}s: {type(e).__name__}: {e}", flush=True)
    sys.exit(1)
print(f"      CONNECTED in {time.time()-t0:.2f}s", flush=True)

print("[3/4] RFC_READ_TABLE T042Z 1 row...", flush=True)
t0 = time.time()
try:
    r = g.call("RFC_READ_TABLE", QUERY_TABLE="T042Z", ROWCOUNT=1, DELIMITER="|",
               FIELDS=[{"FIELDNAME":"LAND1"},{"FIELDNAME":"ZLSCH"},{"FIELDNAME":"XBKKT"}])
except Exception as e:
    print(f"      FAILED in {time.time()-t0:.2f}s: {type(e).__name__}: {e}", flush=True)
    sys.exit(1)
print(f"      OK in {time.time()-t0:.2f}s: {len(r.get('DATA', []))} rows", flush=True)
if r.get("DATA"):
    print(f"      sample: {r['DATA'][0]['WA']!r}", flush=True)

print("[4/4] Closing...", flush=True)
g.close()
print("DONE", flush=True)
