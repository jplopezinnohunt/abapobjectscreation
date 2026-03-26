"""
bdc_schema_probe.py — Diagnostic: find where BDC transaction data lives on P01
"""
import os, sys
from datetime import datetime, timedelta
from collections import Counter
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def env(*keys, default=""):
    for k in keys:
        v = os.getenv(k)
        if v: return v
    return default

import pyrfc

params = {
    "ashost": env("SAP_P01_ASHOST", default="172.16.4.100"),
    "sysnr":  env("SAP_P01_SYSNR",  default="00"),
    "client": env("SAP_P01_CLIENT", default="350"),
}
snc_mode = env("SAP_P01_SNC_MODE")
snc_pn   = env("SAP_P01_SNC_PARTNERNAME")
if snc_mode and snc_pn:
    params["snc_mode"]        = snc_mode
    params["snc_partnername"] = snc_pn
    params["snc_qop"]         = env("SAP_P01_SNC_QOP", default="9")
elif env("SAP_P01_PASSWORD", "SAP_P01_PASSWD"):
    params["user"]   = env("SAP_P01_USER", "SAP_USER")
    params["passwd"] = env("SAP_P01_PASSWORD", "SAP_P01_PASSWD")

print(f"\nConnecting to P01 ({params['ashost']})...")
conn = pyrfc.Connection(**params)
print("Connected OK")

cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")

# ─── 1. APQI FULL SCHEMA ────────────────────────────────────────────────────
print("\n=== [1] APQI Full Schema (all fields) ===")
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="APQI", ROWCOUNT=1)
for f in r.get("FIELDS", []):
    print(f"  {f['FIELDNAME']:25} len={f['LENGTH']:4} type={f.get('TYPE','?')}")

# ─── 2. APQI sample row — all columns ───────────────────────────────────────
print("\n=== [2] APQI Sample Rows (last 90d, all columns) ===")
r2 = conn.call("RFC_READ_TABLE",
    QUERY_TABLE="APQI",
    OPTIONS=[{"TEXT": f"CREDATE >= '{cutoff}'"}],
    ROWCOUNT=5,
)
flds  = r2.get("FIELDS", [])
wids  = [int(f.get("LENGTH", 20)) for f in flds]
names = [f["FIELDNAME"] for f in flds]
print(f"  Columns: {names}")
for row in r2.get("DATA", []):
    wa = row["WA"]
    p  = 0
    vals = []
    for w in wids:
        vals.append(wa[p:p+w].strip())
        p += w + 1
    print(f"  {dict(zip(names, vals))}")

# ─── 3. APQD FULL SCHEMA ────────────────────────────────────────────────────
print("\n=== [3] APQD Full Schema (all fields) ===")
try:
    r3 = conn.call("RFC_READ_TABLE", QUERY_TABLE="APQD", ROWCOUNT=1)
    for f in r3.get("FIELDS", []):
        print(f"  {f['FIELDNAME']:25} len={f['LENGTH']:4} type={f.get('TYPE','?')}")
except Exception as ex:
    print(f"  APQD schema failed: {ex}")

# ─── 4. APQD - any rows with non-empty TCODE directly ───────────────────────
print("\n=== [4] APQD sample (unfiltered, first 10 rows) ===")
try:
    r4 = conn.call("RFC_READ_TABLE",
        QUERY_TABLE="APQD",
        FIELDS=[{"FIELDNAME": "QID"}, {"FIELDNAME": "DSATZ"},
                {"FIELDNAME": "TCODE"}, {"FIELDNAME": "DYNBEGIN"},
                {"FIELDNAME": "DYNPRO"}, {"FIELDNAME": "FNAM"}, {"FIELDNAME": "FVAL"}],
        ROWCOUNT=10,
    )
    rows = r4.get("DATA", [])
    print(f"  APQD rows returned: {len(rows)}")
    flds4  = r4.get("FIELDS", [])
    wids4  = [int(f.get("LENGTH", 20)) for f in flds4]
    names4 = [f["FIELDNAME"] for f in flds4]
    for row in rows:
        wa = row["WA"]
        p = 0; vals = []
        for w in wids4:
            vals.append(wa[p:p+w].strip()); p += w + 1
        print(f"  {dict(zip(names4, vals))}")
except Exception as ex:
    print(f"  APQD unfiltered: {ex}")

# ─── 5. APQI QSTATE distribution ────────────────────────────────────────────
print("\n=== [5] APQI Status Distribution (last 90d) ===")
r5 = conn.call("RFC_READ_TABLE",
    QUERY_TABLE="APQI",
    FIELDS=[{"FIELDNAME": "QSTATE"}, {"FIELDNAME": "GROUPID"}],
    OPTIONS=[{"TEXT": f"CREDATE >= '{cutoff}'"}],
    ROWCOUNT=2000,
)
flds5  = r5.get("FIELDS", [])
wids5  = [int(f.get("LENGTH", 10)) for f in flds5]
state_map = {" ": "NEW", "E": "ERROR", "P": "IN_PROCESS", "F": "DONE", "Z": "BG_QUEUE"}
states = Counter()
names5 = [f["FIELDNAME"] for f in flds5]
for row in r5.get("DATA", []):
    wa = row["WA"]; p=0; vals=[]
    for w in wids5:
        vals.append(wa[p:p+w].strip()); p += w + 1
    d = dict(zip(names5, vals))
    st = state_map.get(d.get("QSTATE", ""), d.get("QSTATE", "?"))
    states[st] += 1
print(f"  Status distribution: {dict(states)}")

# ─── 6. Try BDC_OPEN_GROUP / BDC_READ  via RFC call ─────────────────────────
print("\n=== [6] Try: function APQI_WITH_STATUS_GET (SM35 helper) ===")
for fn in ["APQI_WITH_STATUS_GET", "RSBDC_GROUP_READ", "BDC_GROUP_READ", "BDC_OPEN_GROUP"]:
    try:
        r6 = conn.call(fn)
        print(f"  {fn}: OK — keys={list(r6.keys())[:5]}")
    except Exception as ex:
        print(f"  {fn}: {str(ex)[:100]}")

# ─── 7. APQR table (alternative to APQD in some SAP releases) ──────────────
print("\n=== [7] APQR table (alternative APQD?) ===")
for tbl in ["APQR", "APQQ", "BDC_TAB", "BDCP", "BDCPS"]:
    try:
        r7 = conn.call("RFC_READ_TABLE", QUERY_TABLE=tbl, ROWCOUNT=3)
        cnt = len(r7.get("DATA", []))
        fnames = [f["FIELDNAME"] for f in r7.get("FIELDS", [])]
        print(f"  {tbl}: {cnt} rows, fields={fnames[:8]}")
    except Exception as ex:
        print(f"  {tbl}: {str(ex)[:80]}")

# ─── 8. APQI with GROUPID='TRIP_MODIFY' - get QIDs ─────────────────────────
print("\n=== [8] TRIP_MODIFY QIDs (to spot pattern) ===")
r8 = conn.call("RFC_READ_TABLE",
    QUERY_TABLE="APQI",
    FIELDS=[{"FIELDNAME": "QID"}, {"FIELDNAME": "QSTATE"},
            {"FIELDNAME": "CREDATE"}, {"FIELDNAME": "CREATOR"}],
    OPTIONS=[{"TEXT": "GROUPID = 'TRIP_MODIFY'"},
             {"TEXT": f" AND CREDATE >= '{cutoff}'"}],
    ROWCOUNT=10,
)
flds8  = r8.get("FIELDS", [])
wids8  = [int(f.get("LENGTH", 20)) for f in flds8]
names8 = [f["FIELDNAME"] for f in flds8]
for row in r8.get("DATA", []):
    wa = row["WA"]; p=0; vals=[]
    for w in wids8:
        vals.append(wa[p:p+w].strip()); p += w + 1
    print(f"  {dict(zip(names8, vals))}")

conn.close()
print("\nProbe complete.")
