"""
UBA01 Config Check v5 — Fix field names, get GL account texts, clearing accounts
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mcp-backend-server-python"))
from rfc_helpers import get_connection

results = {}

def get_fields(conn, table):
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, ROWCOUNT=0, DELIMITER="|", OPTIONS=[], FIELDS=[])
        return [f["FIELDNAME"] for f in result.get("FIELDS", [])]
    except Exception as e:
        return f"ERROR: {str(e)[:150]}"

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
        print(f"  [{label}] ERROR: {err[:200]}")
        return f"ERROR: {err[:200]}"


def run(system_id):
    print(f"\n{'='*60}\n  {system_id}\n{'='*60}")
    conn = get_connection(system_id)
    sr = {}

    # 1. Discover SKA1 and SKAT field names
    print("\n--- SKA1/SKAT field discovery ---")
    for t in ["SKA1","SKAT","SKB1"]:
        flds = get_fields(conn, t)
        print(f"  {t} fields: {flds[:12] if isinstance(flds, list) else flds}")
        sr[f"{t}_fields"] = flds[:12] if isinstance(flds, list) else flds

    # 2. Read GL account texts with correct field name (SAKNR not SAESSION)
    print("\n--- SKA1 G/L Accounts ---")
    for acct in ["0001065421","0001165421","0001065424","0001165424","0001094421","0001194421","0001094424","0001194424"]:
        r = read_table(conn, "SKA1",
            ["KTOPL","SAKNR","KTOKS","XBILK"],
            [f"KTOPL = 'UNES' AND SAKNR = '{acct}'"], f"SKA1-{acct}")
        sr[f"SKA1_{acct}"] = r

    print("\n--- SKAT G/L Account Texts ---")
    for acct in ["0001065421","0001165421","0001065424","0001165424","0001094421","0001194421","0001094424","0001194424"]:
        r = read_table(conn, "SKAT",
            ["SPRAS","KTOPL","SAKNR","TXT20","TXT50"],
            [f"SPRAS = 'E' AND KTOPL = 'UNES' AND SAKNR = '{acct}'"], f"SKAT-{acct}")
        sr[f"SKAT_{acct}"] = r

    # 3. T012K full clearing account info
    print("\n--- T012K with all clearing/FX fields ---")
    for hb in ["UBA01","ECO09"]:
        r = read_table(conn, "T012K",
            ["HBKID","HKTID","WAERS","HKONT","WEKON","WKKON","WIKON","FDGRP"],
            [f"BUKRS = 'UNES' AND HBKID = '{hb}'"], f"T012K-{hb}")
        sr[f"T012K_{hb}"] = r

    # 4. BNKA bank names
    print("\n--- BNKA Bank Names ---")
    for bankl in ["SP0000001YCB","XX001877"]:
        r = read_table(conn, "BNKA",
            ["BANKS","BANKL","BANKA","STRAS","ORT01","SWIFT"],
            [f"BANKS = 'MZ' AND BANKL = '{bankl}'"], f"BNKA-{bankl}")
        sr[f"BNKA_{bankl}"] = r

    # 5. T030 — KDR, KDW, KDM, SKE entries (found earlier)
    print("\n--- T030 Exchange Rate entries ---")
    for ktosl in ["KDR","KDW","KDM","SKE"]:
        r = read_table(conn, "T030",
            ["KTOPL","KTOSL","BWMOD","KOMOK","BKLAS","KONTS","KONTH"],
            [f"KTOPL = 'UNES' AND KTOSL = '{ktosl}'"], f"T030-{ktosl}")
        sr[f"T030_{ktosl}"] = r

    # 6. T042I — ECO09 full entry (to see clearing acct = UKONT)
    print("\n--- T042I ECO09 Payment Bank Selection ---")
    r = read_table(conn, "T042I",
        ["ZBUKR","HBKID","ZLSCH","WAERS","HKTID","UKONT","VKONT","GEBKZ","GSBER"],
        ["ZBUKR = 'UNES'"], f"T042I-all")
    sr["T042I_all"] = r

    # 7. SKB1 — Company code level GL account (check if accounts are created at co code level)
    print("\n--- SKB1 G/L Account Company Code ---")
    for acct in ["0001065421","0001165421","0001065424","0001165424","0001094421","0001194421","0001094424","0001194424"]:
        r = read_table(conn, "SKB1",
            ["BUKRS","SAKNR","MWSKZ","WAESSION","FDLEV","XOPVW"],
            [f"BUKRS = 'UNES' AND SAKNR = '{acct}'"], f"SKB1-{acct}")
        if isinstance(r, str) and "ERROR" in r:
            r = read_table(conn, "SKB1",
                ["BUKRS","SAKNR","MWSKZ","FDLEV","XOPVW"],
                [f"BUKRS = 'UNES' AND SAKNR = '{acct}'"], f"SKB1-{acct}-retry")
        sr[f"SKB1_{acct}"] = r

    # 8. SETLEAF — Check ranges more carefully, filter for SETNAME containing BANK
    print("\n--- SETLEAF YBANK sets ---")
    # Get the actual YBANK set entries
    r = read_table(conn, "SETLEAF",
        ["SETCLASS","SUBCLASS","SETNAME","VALSIGN","VALOPTION","VALFROM","VALTO"],
        ["SETNAME LIKE '%YBANK%'"], f"SETLEAF-YBANK", max_rows=500)
    sr["SETLEAF_YBANK"] = r

    # 9. T035D — EBS entries for UBA01 and ECO09 (use DISKB field which contains house bank ID)
    print("\n--- T035D EBS (UBA01/ECO09) ---")
    for hb in ["UBA01","ECO09"]:
        r = read_table(conn, "T035D",
            ["BUKRS","DISKB","BNKKO","XPSSK","XHBZA"],
            [f"BUKRS = 'UNES' AND DISKB LIKE '{hb}%'"], f"T035D-{hb}")
        sr[f"T035D_{hb}"] = r

    conn.close()
    return sr


print("UBA01 Config Check v5 — Fix field names")
results["D01"] = run("D01")
results["P01"] = run("P01")

out = os.path.join(os.path.dirname(__file__), "uba01_config_check_v5_results.json")
with open(out, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved to {out}")
