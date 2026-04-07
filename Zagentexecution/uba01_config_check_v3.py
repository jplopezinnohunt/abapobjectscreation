"""
UBA01 Config Check v3 — Focused extraction of UBA01 vs ECO09
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mcp-backend-server-python"))
from rfc_helpers import get_connection

results = {}

def read_table(conn, table, fields, where_list, label, max_rows=500):
    rfc_fields = [{"FIELDNAME": f} for f in fields]
    rfc_options = [{"TEXT": w} for w in where_list] if where_list else []
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                           ROWCOUNT=max_rows, ROWSKIPS=0,
                           OPTIONS=rfc_options, FIELDS=rfc_fields)
        raw = result.get("DATA", [])
        hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
        rows = []
        for row in raw:
            parts = row["WA"].split("|")
            rows.append({h: parts[i].strip() if i < len(parts) else "" for i, h in enumerate(hdrs)})
        print(f"  [{label}] {len(rows)} rows")
        return rows
    except Exception as e:
        err = str(e)
        if "TABLE_WITHOUT_DATA" in err:
            print(f"  [{label}] 0 rows")
            return []
        if "DATA_BUFFER_EXCEEDED" in err:
            print(f"  [{label}] BUFFER EXCEEDED")
            return "BUFFER_EXCEEDED"
        print(f"  [{label}] ERROR: {err[:200]}")
        return f"ERROR: {err[:200]}"


def run(system_id):
    print(f"\n{'='*60}\n  {system_id}\n{'='*60}")
    conn = get_connection(system_id)
    sr = {}

    # T012 — House Bank Master
    print("\n--- T012 House Bank Master ---")
    for hb in ["UBA01", "ECO09"]:
        sr[f"T012_{hb}"] = read_table(conn, "T012",
            ["BUKRS","HBKID","BANKS","BANKL","TELF1","NAME1","BUPLA"],
            [f"BUKRS = 'UNES' AND HBKID = '{hb}'"], f"T012-{hb}")

    # T012K — House Bank Accounts (split into 2 calls for wide fields)
    print("\n--- T012K House Bank Accounts ---")
    for hb in ["UBA01", "ECO09"]:
        where = [f"BUKRS = 'UNES' AND HBKID = '{hb}'"]
        r1 = read_table(conn, "T012K",
            ["BUKRS","HBKID","HKTID","BANKN","BKONT","WAERS","HKONT","FDGRP"],
            where, f"T012K-{hb}-1")
        r2 = read_table(conn, "T012K",
            ["BUKRS","HBKID","HKTID","WEKON","WKKON","WIKON","BNKN2","ABWAE"],
            where, f"T012K-{hb}-2")
        # Merge
        if isinstance(r1, list) and isinstance(r2, list):
            for i in range(min(len(r1), len(r2))):
                r1[i].update(r2[i])
        sr[f"T012K_{hb}"] = r1

    # T030 — OBA1: Look for our specific G/L accounts in KONTS/KONTH
    print("\n--- T030 OBA1 (checking if bank accounts appear) ---")
    # Read ALL T030 entries for UNES chart (max 500 to start)
    t030_all = read_table(conn, "T030",
        ["KTOPL","KTOSL","BWMOD","KOMOK","BKLAS","KONTS","KONTH"],
        ["KTOPL = 'UNES'"], f"T030-UNES", max_rows=5000)
    sr["T030_UNES_count"] = len(t030_all) if isinstance(t030_all, list) else t030_all

    if isinstance(t030_all, list):
        # Filter for rows containing our bank accounts
        target_accts = {"1065421","1165421","1065424","1165424","1094421","1194421","1094424","1194424"}
        matches = [r for r in t030_all if r.get("KONTS","").strip() in target_accts or r.get("KONTH","").strip() in target_accts]
        sr["T030_bank_acct_matches"] = matches
        print(f"  T030 matches for bank accounts: {len(matches)}")

        # Also show KDB/KDF transaction keys (exchange rate differences)
        kdb_kdf = [r for r in t030_all if r.get("KTOSL","").strip() in ("KDB","KDF","KDR","KDV","KDW","KDI","KDM","KDO","KDG","AUM")]
        sr["T030_exchange_rate_keys"] = kdb_kdf
        print(f"  T030 exchange rate keys (KDB/KDF/etc): {len(kdb_kdf)}")

    # T042I — Payment Bank Selection
    print("\n--- T042I Payment Bank Selection ---")
    for hb in ["UBA01", "ECO09"]:
        sr[f"T042I_{hb}"] = read_table(conn, "T042I",
            ["ZBUKR","HBKID","ZLSCH","WAERS","HKTID","UKONT","VKONT"],
            [f"ZBUKR = 'UNES' AND HBKID = '{hb}'"], f"T042I-{hb}")

    # Also read ALL T042I for UNES to see all banks
    sr["T042I_all"] = read_table(conn, "T042I",
        ["ZBUKR","HBKID","ZLSCH","WAERS","HKTID","UKONT","VKONT"],
        ["ZBUKR = 'UNES'"], f"T042I-all")

    # T042IY — Payment Bank Ranking
    print("\n--- T042IY Payment Bank Ranking ---")
    for hb in ["UBA01", "ECO09"]:
        sr[f"T042IY_{hb}"] = read_table(conn, "T042IY",
            ["ZBUKR","HBKID","ZLSCH","WAERS","HKTID","UKONT","VKONT"],
            [f"ZBUKR = 'UNES' AND HBKID = '{hb}'"], f"T042IY-{hb}")

    # T035D — EBS Config (no HBKID — uses DISKB/BNKKO)
    print("\n--- T035D EBS Config ---")
    # T035D doesn't have HBKID — it has DISKB (planning level) and BNKKO (bank account)
    # Read all UNES entries
    t035d = read_table(conn, "T035D",
        ["BUKRS","DISKB","BNKKO","XPSSK","XHBZA"],
        ["BUKRS = 'UNES'"], f"T035D-UNES")
    sr["T035D"] = t035d

    # Filter for our accounts
    if isinstance(t035d, list):
        our_accts = [r for r in t035d if any(a in str(r) for a in ["1065","1165","1094","1194"])]
        sr["T035D_bank_matches"] = our_accts
        print(f"  T035D matches for bank accounts: {len(our_accts)}")

    # T038 — Cash Management grouping
    print("\n--- T038 Cash Management ---")
    # T038 uses GLIED (structure element), SELEK (selection), not BUKRS directly
    t038 = read_table(conn, "T038",
        ["GLIED","ZEILT","SELEK","BUKRS","KTOPL","EXCLUDE","TEXTV","CKONT"],
        ["KTOPL = 'UNES'"], f"T038-UNES")
    sr["T038"] = t038
    if not t038 or (isinstance(t038, list) and len(t038) == 0):
        # Try without filter
        t038 = read_table(conn, "T038",
            ["GLIED","ZEILT","SELEK","BUKRS","KTOPL","EXCLUDE","TEXTV","CKONT"],
            [], f"T038-all", max_rows=100)
        sr["T038_all"] = t038

    # FEBKO — Bank Statement Headers
    print("\n--- FEBKO Bank Statement Headers ---")
    # FEBKO is very wide (512+ bytes), try minimal fields
    febko = read_table(conn, "FEBKO",
        ["BUKRS","HBKID","HKTID","AZESSION","AESSION"],
        ["BUKRS = 'UNES'"], f"FEBKO-UNES")
    if febko == "BUFFER_EXCEEDED":
        febko = read_table(conn, "FEBKO",
            ["BUKRS","HBKID","HKTID"],
            ["BUKRS = 'UNES'"], f"FEBKO-slim")
    sr["FEBKO"] = febko

    # SETLEAF — check with VALFROM field (discovered correct name)
    print("\n--- SETLEAF GL Account Sets ---")
    for acct in ["1065421","1165421","1065424","1165424","1094421","1194421","1094424","1194424"]:
        r = read_table(conn, "SETLEAF",
            ["SETCLASS","SUBCLASS","SETNAME","VALSIGN","VALOPTION","VALFROM","VALTO"],
            [f"SETCLASS = '0000' AND VALFROM = '{acct}'"], f"SET-{acct}")
        if isinstance(r, list) and r:
            sr[f"SETLEAF_{acct}"] = r

    # Also check SETLEAF with 10-digit padded format
    for acct in ["0001065421","0001165421","0001065424","0001165424","0001094421","0001194421","0001094424","0001194424"]:
        r = read_table(conn, "SETLEAF",
            ["SETCLASS","SUBCLASS","SETNAME","VALSIGN","VALOPTION","VALFROM","VALTO"],
            [f"SETCLASS = '0000' AND VALFROM = '{acct}'"], f"SET-{acct}")
        if isinstance(r, list) and r:
            sr[f"SETLEAF_{acct}"] = r
            print(f"  ** FOUND SET ENTRY for {acct}: {r}")

    # FEBEP — Bank statement line items (check for existing postings)
    print("\n--- FEBEP Bank Statement Items ---")
    # Check FEBEP field structure
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE="FEBEP", ROWCOUNT=0, DELIMITER="|", OPTIONS=[], FIELDS=[])
        febep_fields = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
        print(f"  FEBEP fields (first 15): {febep_fields[:15]}")
        sr["FEBEP_fields"] = febep_fields[:15]
    except Exception as e:
        print(f"  FEBEP field discovery: {str(e)[:100]}")

    conn.close()
    return sr


# ========== MAIN ==========
print("UBA01 Config Check v3 — Focused")
results["D01"] = run("D01")
results["P01"] = run("P01")

out = os.path.join(os.path.dirname(__file__), "uba01_config_check_v3_results.json")
with open(out, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved to {out}")
