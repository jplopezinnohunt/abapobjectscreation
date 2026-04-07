"""
UBA01 House Bank E2E Configuration Check
=========================================
Checks OBA1, V_T018V, Payment Bank Determination, EBS, Sets, Cash Mgmt
for house bank UBA01 vs reference ECO09 in D01 and P01.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mcp-backend-server-python"))
from rfc_helpers import get_connection, rfc_read_paginated

results = {}

def safe_read(conn, table, fields, where, label, batch_size=5000, throttle=0.5):
    """Read table, return rows or error string."""
    try:
        rows = rfc_read_paginated(conn, table, fields, where, batch_size=batch_size, throttle=throttle)
        print(f"  [{label}] {table}: {len(rows)} rows")
        return rows
    except Exception as e:
        err = str(e)
        if "NOT_AUTHORIZED" in err:
            print(f"  [{label}] {table}: NOT AUTHORIZED")
            return f"NOT_AUTHORIZED"
        if "TABLE_NOT_AVAILABLE" in err or "NOT_FOUND" in err:
            print(f"  [{label}] {table}: TABLE NOT FOUND")
            return f"TABLE_NOT_FOUND"
        print(f"  [{label}] {table}: ERROR - {err[:200]}")
        return f"ERROR: {err[:200]}"

def run_checks(system_id):
    print(f"\n{'='*60}")
    print(f"  SYSTEM: {system_id}")
    print(f"{'='*60}")
    conn = get_connection(system_id)
    sys_results = {}

    # =============================================
    # 1. T030 — Exchange Rate Differences (OBA1)
    # =============================================
    print("\n--- 1. T030 / T030R (OBA1 - Exchange Rate Differences) ---")
    # T030R
    r = safe_read(conn, "T030R", ["KTOPL","KTOSL","KONTS","KTOSW"], "KTOPL = 'UNES'", f"{system_id}-T030R")
    sys_results["T030R"] = r

    # T030 with KTOPL = UNES
    r = safe_read(conn, "T030", ["KTOPL","KTOSL","KTOSL_VOR","KONTS","KONTS2"], "KTOPL = 'UNES'", f"{system_id}-T030")
    sys_results["T030"] = r

    # =============================================
    # 2. T012 + T012K — House Bank Master Data
    # =============================================
    print("\n--- 2. T012 / T012K (House Bank Master) ---")
    r = safe_read(conn, "T012", ["BUKRS","HBKID","BANKS","BANKL","BANKN","BRNCH","HKTID","TEXT1"],
                  "BUKRS = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-T012")
    sys_results["T012"] = r

    r = safe_read(conn, "T012K", ["BUKRS","HBKID","HKTID","BANKN","BKONT","BANKL","HKONT","ZLSCH","WAESSION","UBKNT","DTAAI"],
                  "BUKRS = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-T012K")
    if isinstance(r, str) and "ERROR" in r:
        # Try without WAESSION which may not exist
        r = safe_read(conn, "T012K", ["BUKRS","HBKID","HKTID","BANKN","BKONT","BANKL","HKONT","ZLSCH","UBKNT"],
                      "BUKRS = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-T012K-retry")
    sys_results["T012K"] = r

    # =============================================
    # 3. T018 — Clearing Accounts (V_T018V)
    # =============================================
    print("\n--- 3. T018 / T018V (Clearing Accounts for Receiving Bank) ---")
    # Try all fields first
    r = safe_read(conn, "T018", ["MANDT","BUKRS","HBKID","HKTID","WAESSION","KONTO"],
                  "BUKRS = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-T018")
    if isinstance(r, str):
        # Try without WAESSION
        r = safe_read(conn, "T018", ["MANDT","BUKRS","HBKID","HKTID","KONTO"],
                      "BUKRS = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-T018-retry")
    sys_results["T018"] = r

    # Also try with WAESSION as WAESSION
    r2 = safe_read(conn, "T018V", ["BUKRS","HBKID","HKTID","WAERS","KONTO"],
                   "BUKRS = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-T018V")
    sys_results["T018V"] = r2

    # =============================================
    # 4. T042I — Payment Bank Selection
    # =============================================
    print("\n--- 4. T042I / T042IY (Payment Bank Determination) ---")
    r = safe_read(conn, "T042I", ["ZBUKR","ZLSCH","WAESSION","HBKID","HKTID","UBKNT","UZAESSION"],
                  "ZBUKR = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-T042I")
    if isinstance(r, str) and "ERROR" in r:
        r = safe_read(conn, "T042I", ["ZBUKR","ZLSCH","HBKID","HKTID","UBKNT"],
                      "ZBUKR = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-T042I-retry")
    sys_results["T042I"] = r

    r = safe_read(conn, "T042IY", ["ZBUKR","ZLSCH","HBKID","HKTID"],
                  "ZBUKR = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-T042IY")
    sys_results["T042IY"] = r

    # =============================================
    # 5. T037 / T037T — Cash Management Planning
    # =============================================
    print("\n--- 5. T037 / T037T (Cash Management) ---")
    r = safe_read(conn, "T037", ["BUKRS","FDLEV","FDGRP"], "BUKRS = 'UNES'", f"{system_id}-T037")
    sys_results["T037"] = r

    r = safe_read(conn, "T037T", ["BUKRS","FDLEV","FDGRP","TEXT1"], "BUKRS = 'UNES'", f"{system_id}-T037T")
    if isinstance(r, str) and "ERROR" in r:
        r = safe_read(conn, "T037T", ["FDLEV","FDGRP","TEXT1"], "", f"{system_id}-T037T-all")
    sys_results["T037T"] = r

    # =============================================
    # 6. T035D — Electronic Bank Statement Config
    # =============================================
    print("\n--- 6. T035D (Electronic Bank Statement) ---")
    r = safe_read(conn, "T035D", ["BUKRS","HBKID","HKTID","GSESSION","CSESSION","TEXT1"],
                  "BUKRS = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-T035D")
    if isinstance(r, str) and "ERROR" in r:
        r = safe_read(conn, "T035D", ["BUKRS","HBKID","HKTID"],
                      "BUKRS = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-T035D-retry")
    sys_results["T035D"] = r

    # =============================================
    # 7. SETLEAF / SETHEADER — GL Account Sets
    # =============================================
    print("\n--- 7. SETHEADER + SETLEAF (GL Account Sets with bank accounts) ---")
    # Get all sets for GL accounts
    r = safe_read(conn, "SETHEADER", ["SETCLASS","SUBCLASS","SETNAME","DTEFROM","DTETO","DTEFLD"],
                  "SETCLASS = '0000' AND SETNAME LIKE '%BANK%'", f"{system_id}-SETHEADER-BANK")
    sys_results["SETHEADER_BANK"] = r

    r = safe_read(conn, "SETHEADER", ["SETCLASS","SUBCLASS","SETNAME","DTEFROM","DTETO"],
                  "SETCLASS = '0000' AND SETNAME LIKE '%YBANK%'", f"{system_id}-SETHEADER-YBANK")
    sys_results["SETHEADER_YBANK"] = r

    # Check SETLEAF for specific bank G/L accounts
    for acct in ["1065421", "1165421", "1065424", "1165424", "1094421", "1194421", "1094424", "1194424"]:
        r = safe_read(conn, "SETLEAF", ["SETCLASS","SUBCLASS","SETNAME","VALSIGN","VALOPTION","VAESSION_LOW","VAESSION_HIGH"],
                      f"SETCLASS = '0000' AND VAESSION_LOW = '{acct}'", f"{system_id}-SETLEAF-{acct}")
        if isinstance(r, str) and "ERROR" in r:
            r = safe_read(conn, "SETLEAF", ["SETCLASS","SUBCLASS","SETNAME","VALSIGN","VALOPTION","VAESSION_LOW"],
                          f"SETCLASS = '0000' AND VAESSION_LOW = '{acct}'", f"{system_id}-SETLEAF-{acct}-retry")
        sys_results[f"SETLEAF_{acct}"] = r

    # Also check ranges that might INCLUDE these accounts
    for acct in ["1065421", "1165421", "1065424", "1165424"]:
        r = safe_read(conn, "SETLEAF", ["SETCLASS","SUBCLASS","SETNAME","VALSIGN","VALOPTION","VAESSION_LOW","VAESSION_HIGH"],
                      f"SETCLASS = '0000' AND VALOPTION = 'BT' AND VAESSION_LOW <= '{acct}' AND VAESSION_HIGH >= '{acct}'",
                      f"{system_id}-SETLEAF-range-{acct}")
        if isinstance(r, str):
            pass  # skip range check if error
        else:
            sys_results[f"SETLEAF_range_{acct}"] = r

    # =============================================
    # 8. T038 — Cash Management Grouping
    # =============================================
    print("\n--- 8. T038 (Cash Management Grouping) ---")
    r = safe_read(conn, "T038", ["BUKRS","HKONT","FDLEV","FDGRP"],
                  "BUKRS = 'UNES'", f"{system_id}-T038")
    sys_results["T038"] = r

    # =============================================
    # 9. T012T — House Bank Text
    # =============================================
    print("\n--- 9. T012T (House Bank Texts) ---")
    r = safe_read(conn, "T012T", ["BUKRS","HBKID","TEXT1","SPRAS"],
                  "BUKRS = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-T012T")
    sys_results["T012T"] = r

    # =============================================
    # 10. FCLM_BSM_CUST — Bank Statement Monitor
    # =============================================
    print("\n--- 10. FCLM_BSM_CUST / Bank Statement Monitor ---")
    for tbl in ["FCLM_BSM_CUST", "FTE_BSM_CUST", "FEBKO"]:
        r = safe_read(conn, tbl, [], "", f"{system_id}-{tbl}-probe", batch_size=1)
        if isinstance(r, str) and "NOT_FOUND" in r:
            sys_results[tbl] = "TABLE_NOT_FOUND"
            continue
        # If table exists, try to read UBA01/ECO09 entries
        # Get field list first
        try:
            result = conn.call("RFC_READ_TABLE", QUERY_TABLE=tbl, ROWCOUNT=0, DELIMITER="|", OPTIONS=[], FIELDS=[])
            field_names = [f["FIELDNAME"] for f in result.get("FIELDS", [])[:10]]
            print(f"    {tbl} fields: {field_names}")
            sys_results[f"{tbl}_FIELDS"] = field_names
        except Exception as e2:
            print(f"    {tbl} field discovery error: {str(e2)[:100]}")

    # FEBKO — bank statement header (known table)
    r = safe_read(conn, "FEBKO", ["BUKRS","HBKID","HKTID","AZESSION","AESSION","WAESSION","KUESSION"],
                  "BUKRS = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-FEBKO")
    if isinstance(r, str) and "ERROR" in r:
        r = safe_read(conn, "FEBKO", ["BUKRS","HBKID","HKTID","AZESSION","AESSION"],
                      "BUKRS = 'UNES' AND ( HBKID = 'UBA01' OR HBKID = 'ECO09' )", f"{system_id}-FEBKO-retry")
    sys_results["FEBKO"] = r

    conn.close()
    return sys_results


# ========== MAIN ==========
print("UBA01 House Bank E2E Configuration Check")
print("="*60)

# D01 checks
d01 = run_checks("D01")
results["D01"] = d01

# P01 checks
p01 = run_checks("P01")
results["P01"] = p01

# ========== SAVE JSON ==========
out_path = os.path.join(os.path.dirname(__file__), "uba01_config_check_results.json")
# Convert to serializable
def make_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    return obj

with open(out_path, "w") as f:
    json.dump(make_serializable(results), f, indent=2, default=str)

print(f"\n\nResults saved to {out_path}")
print("DONE")
