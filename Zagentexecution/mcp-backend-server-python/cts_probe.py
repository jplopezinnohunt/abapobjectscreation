"""
cts_probe.py — Diagnostic probe for CTS table accessibility from D01
=====================================================================
Helps determine the correct way to read E070/E071 transport tables.
Tests multiple approaches:
  1. RFC_READ_TABLE with simple WHERE
  2. RFC_READ_TABLE with IN clause (TRSTATUS)
  3. BAPI_TRANSPORT_READ (if available)
  4. SE01_REQUESTS_OVERVIEW (standard FM)
  5. TMS_CI_GET_REQUESTS (TMS FC)

Run: python cts_probe.py
"""

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

import pyrfc

def env(*keys, default=""):
    for k in keys:
        v = os.getenv(k)
        if v: return v
    return default

def rfc_connect():
    params = {
        "ashost": env("SAP_D01_ASHOST", "SAP_HOST", default="HQ-SAP-D01.HQ.INT.UNESCO.ORG"),
        "sysnr":  env("SAP_D01_SYSNR",  "SAP_SYSNR",  default="00"),
        "client": env("SAP_D01_CLIENT", "SAP_CLIENT", default="350"),
    }
    snc_mode = env("SAP_D01_SNC_MODE", "SAP_SNC_MODE")
    snc_pn   = env("SAP_D01_SNC_PARTNERNAME", "SAP_SNC_PARTNERNAME")
    if snc_mode and snc_pn:
        params["snc_mode"] = snc_mode
        params["snc_partnername"] = snc_pn
        params["snc_qop"] = env("SAP_D01_SNC_QOP", "SAP_SNC_QOP", default="9")
    else:
        params["user"]   = env("SAP_D01_USER", "SAP_USER")
        params["passwd"] = env("SAP_D01_PASSWORD", "SAP_PASSWORD")
    return pyrfc.Connection(**params)

def test(label, fn):
    try:
        result = fn()
        print(f"  [OK]  {label}")
        return result
    except Exception as e:
        print(f"  [FAIL] {label}: {str(e)[:120]}")
        return None

conn = rfc_connect()
print("[OK] Connected to D01\n")

# ── Test 1: E070 simple status filter (no IN) ─────────────────────────────────
print("=== Testing E070 access approaches ===")

def t1():
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="E070",
        FIELDS=[{"FIELDNAME": "TRKORR"}, {"FIELDNAME": "AS4USER"}, {"FIELDNAME": "AS4DATE"},
                {"FIELDNAME": "TRFUNCTION"}, {"FIELDNAME": "TRSTATUS"}],
        OPTIONS=[{"TEXT": "TRSTATUS = 'R'"}],
        ROWCOUNT=10, ROWSKIPS=0)
    rows = r.get("DATA", [])
    for row in rows[:3]:
        print(f"     {row['WA']}")
    return rows
result1 = test("E070 RFC_READ_TABLE TRSTATUS='R'", t1)

# ── Test 2: E070 with date filter ─────────────────────────────────────────────
def t2():
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="E070",
        FIELDS=[{"FIELDNAME": "TRKORR"}, {"FIELDNAME": "AS4USER"}, {"FIELDNAME": "AS4DATE"}],
        OPTIONS=[{"TEXT": "AS4DATE >= '20250101'"}],
        ROWCOUNT=5, ROWSKIPS=0)
    rows = r.get("DATA", [])
    for row in rows[:3]:
        print(f"     {row['WA']}")
    return rows
test("E070 RFC_READ_TABLE date filter", t2)

# ── Test 3: E070 no filter ────────────────────────────────────────────────────
def t3():
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="E070",
        FIELDS=[{"FIELDNAME": "TRKORR"}, {"FIELDNAME": "AS4USER"}],
        OPTIONS=[], ROWCOUNT=5, ROWSKIPS=0)
    rows = r.get("DATA", [])
    for row in rows[:3]:
        print(f"     {row['WA']}")
    return rows
test("E070 RFC_READ_TABLE no filter (raw first 5)", t3)

# ── Test 4: E071 ──────────────────────────────────────────────────────────────
print("\n=== Testing E071 access ===")
def t4():
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="E071",
        FIELDS=[{"FIELDNAME": "TRKORR"}, {"FIELDNAME": "OBJECT"}, {"FIELDNAME": "OBJ_NAME"}],
        OPTIONS=[], ROWCOUNT=5, ROWSKIPS=0)
    rows = r.get("DATA", [])
    for row in rows[:3]:
        print(f"     {row['WA']}")
    return rows
test("E071 RFC_READ_TABLE no filter", t4)

# ── Test 5: E070L ─────────────────────────────────────────────────────────────
print("\n=== Testing E070L access ===")
def t5():
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="E070L",
        FIELDS=[{"FIELDNAME": "TRKORR"}, {"FIELDNAME": "SYSTM"}, {"FIELDNAME": "TPSTAT"}],
        OPTIONS=[], ROWCOUNT=5, ROWSKIPS=0)
    rows = r.get("DATA", [])
    for row in rows[:3]:
        print(f"     {row['WA']}")
    return rows
test("E070L RFC_READ_TABLE no filter", t5)

# ── Test 6: Function module TMS_MGR_DISPLAY_IMPORT_PROT ───────────────────────
print("\n=== Testing standard CTS Function Modules ===")
def t6():
    r = conn.call("TR_READ_OBJECTS_OF_REQUEST",
        IV_TRKORR="D01K900001")  # dummy TRKORR — just test if FM is callable
    return r
test("TR_READ_OBJECTS_OF_REQUEST (TR_* FM)", t6)

def t7():
    r = conn.call("TRINT_READ_TRANSPORT_REQUEST",
        IV_TRKORR="D01K900001")
    return r
test("TRINT_READ_TRANSPORT_REQUEST", t7)

def t8():
    r = conn.call("SE01_REQUESTS_OVERVIEW",
        TRSTATUS="R",
        TRFUNCTIONS=["K", "W"],
        FROM_DATE="20250101",
        MAX_RESULTS=20)
    results = r.get("REQUESTS") or r.get("ET_REQUESTS") or []
    for row in results[:3]:
        print(f"     {row}")
    return results
test("SE01_REQUESTS_OVERVIEW", t8)

def t9():
    r = conn.call("BAPI_TRANSPORT_READ",
        TRKORR="D01K900001")
    return r
test("BAPI_TRANSPORT_READ", t9)

# ── Test 7: Check E070 table attributes ───────────────────────────────────────
print("\n=== Checking E070 table metadata ===")
def t10():
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD02L",
        FIELDS=[{"FIELDNAME": "TABNAME"}, {"FIELDNAME": "TABCLASS"}, {"FIELDNAME": "CONTFLAG"}],
        OPTIONS=[{"TEXT": "TABNAME = 'E070'"}],
        ROWCOUNT=1)
    rows = r.get("DATA", [])
    for row in rows:
        print(f"     {row['WA']}")
    return rows
test("E070 table metadata (DD02L)", t10)

print("\n=== Done. Review results above for working approach ===")
conn.close()
