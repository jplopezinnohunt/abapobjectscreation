"""
UBA01 Config Check v4 — Final targeted checks
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
        print(f"  [{label}] ERROR: {err[:200]}")
        return f"ERROR: {err[:200]}"


def run(system_id):
    print(f"\n{'='*60}\n  {system_id}\n{'='*60}")
    conn = get_connection(system_id)
    sr = {}

    # 1. SETLEAF — check ECO09 MZN account (0001094424) and all 10-digit variants
    print("\n--- SETLEAF (all bank accounts, 10-digit padded) ---")
    for acct in ["0001094424","0001194424","0001065421","0001165421","0001065424","0001165424"]:
        r = read_table(conn, "SETLEAF",
            ["SETCLASS","SUBCLASS","SETNAME","VALSIGN","VALOPTION","VALFROM","VALTO"],
            [f"VALFROM = '{acct}'"], f"SET-{acct}")
        if isinstance(r, list) and r:
            sr[f"SETLEAF_{acct}"] = r

    # Also check ranges (BT = between) covering our accounts
    for acct in ["0001065421","0001065424","0001094421","0001094424"]:
        r = read_table(conn, "SETLEAF",
            ["SETCLASS","SUBCLASS","SETNAME","VALSIGN","VALOPTION","VALFROM","VALTO"],
            [f"VALOPTION = 'BT' AND VALFROM <= '{acct}'", f"AND VALTO >= '{acct}'"],
            f"SET-range-{acct}")
        if isinstance(r, list) and r:
            sr[f"SETLEAF_range_{acct}"] = r

    # 2. T042IY — Read ALL UNES entries to check ECO09 pattern
    print("\n--- T042IY (ALL UNES entries) ---")
    r = read_table(conn, "T042IY",
        ["ZBUKR","HBKID","ZLSCH","WAERS","HKTID","UKONT","VKONT"],
        ["ZBUKR = 'UNES'"], f"T042IY-all")
    sr["T042IY_all"] = r

    # Filter for ECO09 and UBA01
    if isinstance(r, list):
        eco09 = [x for x in r if x.get("HBKID") == "ECO09"]
        uba01 = [x for x in r if x.get("HBKID") == "UBA01"]
        print(f"  ECO09 entries: {len(eco09)}")
        print(f"  UBA01 entries: {len(uba01)}")
        sr["T042IY_ECO09"] = eco09
        sr["T042IY_UBA01"] = uba01

    # 3. T030 — Read MORE entries (was capped at 5000)
    # Check transaction keys related to bank clearing: KDB, KDF, AUM, etc.
    print("\n--- T030 Exchange Rate Diff transaction keys ---")
    # Get unique KTOSL values
    r = read_table(conn, "T030R",
        ["KTOPL","KTOSL","XKOMO","XBWMO","XBKLA"],
        ["KTOPL = 'UNES'"], f"T030R-UNES")
    sr["T030R_UNES"] = r

    # Read T030 for specific transaction keys related to FX
    for ktosl in ["KDB","KDF","AUM","KDR","KDV","KDW","KDI","KDM","KDG","SKE","SKA","KDG","UMB"]:
        r2 = read_table(conn, "T030",
            ["KTOPL","KTOSL","BWMOD","KOMOK","BKLAS","KONTS","KONTH"],
            [f"KTOPL = 'UNES' AND KTOSL = '{ktosl}'"], f"T030-{ktosl}")
        if isinstance(r2, list) and r2:
            sr[f"T030_{ktosl}"] = r2

    # 4. Check T012K WEKON/WKKON/WIKON — these are the clearing accounts
    print("\n--- T012K Clearing/Diff accounts ---")
    # WEKON = Exch rate diff account, WKKON = Short-term clearing, WIKON = interest clearing
    for hb in ["UBA01","ECO09"]:
        r = read_table(conn, "T012K",
            ["HBKID","HKTID","HKONT","WEKON","WKKON","WIKON"],
            [f"BUKRS = 'UNES' AND HBKID = '{hb}'"], f"T012K-clr-{hb}")
        sr[f"T012K_clearing_{hb}"] = r

    # 5. BNKA — Bank master data (get bank name for both bank keys)
    print("\n--- BNKA Bank Master ---")
    for bankl in ["SP0000001YCB","XX001877"]:
        r = read_table(conn, "BNKA",
            ["BANKS","BANKL","BANKA","STRAS","ORT01","SWIFT","PROVZ"],
            [f"BANKS = 'MZ' AND BANKL = '{bankl}'"], f"BNKA-{bankl}")
        sr[f"BNKA_{bankl}"] = r

    # 6. T042E — Payment methods per company code
    print("\n--- T042E Payment Methods per Company Code ---")
    r = read_table(conn, "T042E",
        ["ZBUKR","ZLSCH","TEXT1"],
        ["ZBUKR = 'UNES'"], f"T042E-UNES")
    sr["T042E"] = r

    # 7. T042Z — Payment method supplements
    print("\n--- T042Z Payment Method Supplements ---")
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE="T042Z", ROWCOUNT=0, DELIMITER="|", OPTIONS=[], FIELDS=[])
        flds = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
        print(f"  T042Z fields: {flds}")
        sr["T042Z_fields"] = flds
    except:
        pass

    # 8. SKA1/SKAT — Check if G/L accounts exist
    print("\n--- SKA1/SKAT G/L Account Master ---")
    for acct in ["0001065421","0001165421","0001065424","0001165424","0001094421","0001194421","0001094424","0001194424"]:
        r = read_table(conn, "SKA1",
            ["KTOPL","SAESSION","KTOKS","XBILK"],
            [f"KTOPL = 'UNES' AND SAESSION = '{acct}'"], f"SKA1-{acct}")
        if isinstance(r, str) and "ERROR" in r:
            r = read_table(conn, "SKA1",
                ["KTOPL","SAESSION","KTOKS"],
                [f"KTOPL = 'UNES' AND SAESSION = '{acct}'"], f"SKA1-{acct}-retry")
        sr[f"SKA1_{acct}"] = r

    for acct in ["0001065421","0001165421","0001065424","0001165424","0001094421","0001194421","0001094424","0001194424"]:
        r = read_table(conn, "SKAT",
            ["SPRAS","KTOPL","SAESSION","TXT20","TXT50"],
            [f"SPRAS = 'E' AND KTOPL = 'UNES' AND SAESSION = '{acct}'"], f"SKAT-{acct}")
        if isinstance(r, str) and "ERROR" in r:
            r = read_table(conn, "SKAT",
                ["SPRAS","KTOPL","SAESSION","TXT20"],
                [f"SPRAS = 'E' AND KTOPL = 'UNES' AND SAESSION = '{acct}'"], f"SKAT-{acct}-retry")
        sr[f"SKAT_{acct}"] = r

    conn.close()
    return sr


print("UBA01 Config Check v4 — Final targeted")
results["D01"] = run("D01")
results["P01"] = run("P01")

out = os.path.join(os.path.dirname(__file__), "uba01_config_check_v4_results.json")
with open(out, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved to {out}")
