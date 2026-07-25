"""Probe SET* tables with different field lists to isolate failure."""
import os, sys
MCP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP_DIR))
from rfc_helpers import get_connection

conn = get_connection("P01")

def try_read(table, fields, where, label):
    try:
        rfc_fields = [{"FIELDNAME": f} for f in fields] if fields else []
        opts = [{"TEXT": where}] if where else []
        res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                        ROWCOUNT=3, ROWSKIPS=0, OPTIONS=opts, FIELDS=rfc_fields)
        hdrs = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
        rows = res.get("DATA", [])
        print(f"OK  {label}: headers={hdrs[:5]}... rows={len(rows)}")
        for r in rows[:1]:
            print("      ", r["WA"][:200])
    except Exception as e:
        print(f"ERR {label}: {type(e).__name__}: {str(e)[:200]}")

# Test 1: no filter, no fields (known to work)
try_read("SETLEAF", [], "", "T1 SETLEAF all-fields no-where")

# Test 2: with YBANK filter no fields
try_read("SETLEAF", [], "SETNAME LIKE 'YBANK%'", "T2 SETLEAF all-fields YBANK%")

# Test 3: MANDT variant
try_read("SETLEAF", ["MANDT","SETCLASS","SUBCLASS","SETNAME","LINEID","VALSIGN","VALOPTION","VALFROM","VALTO"],
         "SETNAME LIKE 'YBANK%'", "T3 SETLEAF MANDT-key YBANK%")

# Test 4: CLIENT variant (wrong name likely)
try_read("SETLEAF", ["CLIENT","SETCLASS","SUBCLASS","SETNAME"],
         "SETNAME LIKE 'YBANK%'", "T4 SETLEAF CLIENT-key YBANK%")

# Test 5: MANDT variant with specific SETNAME
try_read("SETLEAF", ["MANDT","SETNAME","VALFROM","VALTO"],
         "SETNAME = 'YBANK_ACCOUNTS_FO_OTH'", "T5 SETLEAF MANDT SETNAME=FO_OTH")

# DD03L check: list SETLEAF columns via DDIF_FIELDINFO_GET
try:
    res = conn.call("DDIF_FIELDINFO_GET", TABNAME="SETLEAF")
    fi = res.get("DFIES_TAB", [])
    print(f"\nDDIF_FIELDINFO_GET SETLEAF: {len(fi)} fields")
    for f in fi:
        print(f"  {f.get('FIELDNAME'):15s} {f.get('ROLLNAME','')} len={f.get('LENG','')}")
except Exception as e:
    print(f"DDIF err: {e}")
