"""
Read actual Bank + Payment config values for company code STEM from D01.
Focus: what GL accounts, what bank details, what payment methods.
"""
import os, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def env(*keys, default=""):
    for k in keys:
        v = os.getenv(k)
        if v: return v
    return default

def rfc_connect():
    import pyrfc
    params = {
        "ashost": env("SAP_D01_ASHOST", "SAP_ASHOST", default="172.16.4.66"),
        "sysnr": env("SAP_D01_SYSNR", "SAP_SYSNR", default="00"),
        "client": env("SAP_D01_CLIENT", "SAP_CLIENT", default="350"),
    }
    # Use hostname instead of IP (matches working pattern from cts_extract.py)
    params["ashost"] = env("SAP_HOST", default="HQ-SAP-D01.HQ.INT.UNESCO.ORG")
    snc_mode = env("SAP_D01_SNC_MODE", "SAP_SNC_MODE")
    snc_pn = env("SAP_D01_SNC_PARTNERNAME", "SAP_SNC_PARTNERNAME")
    if snc_mode and snc_pn:
        params["snc_mode"] = snc_mode
        params["snc_partnername"] = snc_pn
        params["snc_qop"] = env("SAP_D01_SNC_QOP", "SAP_SNC_QOP", default="9")
    else:
        params["user"] = env("SAP_D01_USER", "SAP_USER")
        params["passwd"] = env("SAP_D01_PASSWORD", "SAP_PASSWORD")
    print(f"[RFC] Connecting to {params['ashost']}...")
    return pyrfc.Connection(**params)

def read_table(conn, table, fields, where, max_rows=100):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=table,
        FIELDS=[{"FIELDNAME": f} for f in fields],
        OPTIONS=[{"TEXT": t} for t in where],
        ROWCOUNT=max_rows, ROWSKIPS=0, DELIMITER="|")
    rows = []
    for row in r.get("DATA", []):
        parts = row.get("WA", "").split("|")
        if len(parts) == len(fields):
            rows.append({fields[i]: parts[i].strip() for i in range(len(fields))})
    return rows

conn = rfc_connect()

# 1. T012 - House Bank definition
print("=== T012 (House Bank) ===")
rows = read_table(conn, "T012", ["BUKRS", "HBKID", "BANKS", "BANKL", "BANKN", "BRNCH", "STRAS", "ORT01", "SWIFT"], ["BUKRS = 'STEM'"])
for r in rows: print(f"  {r}")

# 2. T012K - House Bank Accounts (GL reconciliation!)
print("\n=== T012K (Bank Accounts — GL reconciliation) ===")
rows = read_table(conn, "T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "WAESSION", "HKONT", "UKONT", "EESSION"], ["BUKRS = 'STEM'"])
for r in rows: print(f"  {r}")

# Retry with corrected fields if WAESSION fails
try:
    print("\n=== T012K (retry with standard fields) ===")
    rows = read_table(conn, "T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "WAESSION", "HKONT"], ["BUKRS = 'STEM'"])
    for r in rows: print(f"  {r}")
except:
    pass

# 3. T042 - Paying company codes
print("\n=== T042 (Paying Company Codes) ===")
rows = read_table(conn, "T042", ["BUKRS", "ZBUKR", "ZLSCH", "HBKID", "HKTID"], ["BUKRS = 'STEM'"])
for r in rows: print(f"  {r}")

# 4. T042B - Payment methods per company code
print("\n=== T042B (Payment Methods per CoCode) ===")
rows = read_table(conn, "T042B", ["BUKRS", "ZLSCH", "XBLNR", "ZNME1"], ["BUKRS = 'STEM'"])
for r in rows: print(f"  {r}")

# 5. T042E - Payment methods per country
print("\n=== T042E (Payment Methods per Country) ===")
rows = read_table(conn, "T042E", ["BUKRS", "LAND1", "ZLSCH", "TEXT1", "XBLNR"], ["BUKRS = 'STEM'"])
for r in rows: print(f"  {r}")

# 6. Check what the SOURCE company code looks like - let's check if there's a similar one
# Look for other company codes with CBE01 house bank
print("\n=== Other CoCode with house bank CBE01 (potential source of copy) ===")
rows = read_table(conn, "T012", ["BUKRS", "HBKID", "BANKS", "BANKL", "SWIFT"], ["HBKID = 'CBE01'"])
for r in rows: print(f"  {r}")

# 7. T012K for those other company codes - to compare GL accounts
print("\n=== T012K for ALL CoCodes with CBE01 (GL comparison) ===")
rows = read_table(conn, "T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "HKONT"], ["HBKID = 'CBE01'"])
for r in rows: print(f"  {r}")
