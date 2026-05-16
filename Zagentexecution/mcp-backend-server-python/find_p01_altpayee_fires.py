"""Diagnostic: confirm whether BSAK has EMPFG values at all in P01."""
import os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
params = dict(
    ashost=os.getenv("SAP_P01_ASHOST"), sysnr=os.getenv("SAP_P01_SYSNR"),
    client=os.getenv("SAP_P01_CLIENT"), user=os.getenv("SAP_P01_USER"),
    lang="EN", snc_mode="1",
    snc_partnername=os.getenv("SAP_P01_SNC_PARTNERNAME"), snc_qop="9",
)
conn = Connection(**params)
print("Connected P01")

def rd(t, opts, fields, n=500):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=t,
                  OPTIONS=[{"TEXT": x} for x in opts],
                  FIELDS=[{"FIELDNAME": x} for x in fields],
                  DELIMITER="|", ROWCOUNT=n)
    cols = [f["FIELDNAME"] for f in r.get("FIELDS",[])] or fields
    return [dict(zip(cols, d["WA"].split("|"))) for d in r.get("DATA", [])]

# Test 1: read 50 BSAK rows WITHOUT filtering EMPFG. See if ANY have a non-space EMPFG.
print("\n=== Test 1: 100 BSAK rows since 2024-01-01, with EMPFG shown ===")
try:
    rows = rd("BSAK",
              ["BUDAT >= '20240101'"],
              ["BUKRS","BELNR","LIFNR","EMPFG"],
              n=100)
    print(f"  {len(rows)} rows. EMPFG populated count:")
    populated = [r for r in rows if r['EMPFG'].strip()]
    print(f"  {len(populated)} of {len(rows)} have non-space EMPFG")
    if populated:
        for r in populated[:10]:
            print(f"    {r}")
    else:
        # Show a few raw rows to confirm EMPFG IS returned (blank)
        for r in rows[:5]:
            print(f"    sample (EMPFG='{r['EMPFG']}'): {r}")
except Exception as e:
    print(f"  err: {e}")

# Test 2: try the filter syntax variants
print("\n=== Test 2: different filter syntax variants ===")
for label, opt in [
    ("EMPFG <> ' '", "EMPFG <> ' '"),
    ("EMPFG <> ''",  "EMPFG <> ''"),
    ("EMPFG > ' '",  "EMPFG > ' '"),
    ("EMPFG NE ' '", "EMPFG NE ' '"),
]:
    try:
        rows = rd("BSAK", [opt], ["BUKRS","BELNR","LIFNR","EMPFG"], n=10)
        print(f"  '{label}': {len(rows)} rows. First: {rows[0] if rows else None}")
    except Exception as e:
        print(f"  '{label}': err: {str(e)[:100]}")

# Test 3: try BSEG directly with EMPFG filter (some installs only have EMPFG in BSEG, not the indexes)
print("\n=== Test 3: BSEG with EMPFG filter ===")
try:
    rows = rd("BSEG",
              ["EMPFG <> ' '"],
              ["BUKRS","BELNR","GJAHR","BUZEI","LIFNR","EMPFG"],
              n=50)
    print(f"  BSEG hits: {len(rows)}")
    for r in rows[:20]:
        print(f"    {r}")
except Exception as e:
    print(f"  BSEG err: {e}")

# Test 4: BSEC (one-time vendor / alt-payee header) — small targeted table
print("\n=== Test 4: BSEC since 2024 (one-time + alt-payee documents) ===")
try:
    rows = rd("BSEC",
              ["GJAHR >= '2024'"],
              ["BUKRS","BELNR","GJAHR","BUZEI","NAME1"],
              n=200)
    print(f"  BSEC rows: {len(rows)}")
    for r in rows[:20]:
        print(f"    {r['BUKRS']}/{r['BELNR']}/{r['GJAHR']}/{r['BUZEI']} NAME1='{r['NAME1'].strip()[:30]}'")
    if len(rows) > 20:
        print(f"  ... and {len(rows)-20} more")
except Exception as e:
    print(f"  BSEC err: {e}")
