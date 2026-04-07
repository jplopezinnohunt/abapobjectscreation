"""
UBA01 House Bank E2E Config Check — v2
======================================
More targeted: discover fields first, use correct WHERE clauses.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mcp-backend-server-python"))
from rfc_helpers import get_connection

results = {}

def get_fields(conn, table):
    """Get field names for a table."""
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, ROWCOUNT=0, DELIMITER="|", OPTIONS=[], FIELDS=[])
        return [f["FIELDNAME"] for f in result.get("FIELDS", [])]
    except Exception as e:
        return f"ERROR: {str(e)[:150]}"

def read_table(conn, table, fields, where_list, label, max_rows=500):
    """Read with proper OPTIONS list format."""
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
        print(f"  [{label}] {table}: {len(rows)} rows")
        return rows
    except Exception as e:
        err = str(e)
        if "TABLE_WITHOUT_DATA" in err:
            print(f"  [{label}] {table}: 0 rows (empty)")
            return []
        if "DATA_BUFFER_EXCEEDED" in err:
            # Try with fewer fields
            if len(fields) > 4:
                return read_table(conn, table, fields[:4], where_list, label + "-slim", max_rows)
            print(f"  [{label}] {table}: BUFFER EXCEEDED even with {len(fields)} fields")
            return []
        if "NOT_AUTHORIZED" in err:
            print(f"  [{label}] {table}: NOT AUTHORIZED")
            return "NOT_AUTHORIZED"
        if "NOT_FOUND" in err or "NOT_AVAILABLE" in err:
            print(f"  [{label}] {table}: NOT FOUND")
            return "NOT_FOUND"
        print(f"  [{label}] {table}: ERROR - {err[:200]}")
        return f"ERROR: {err[:200]}"


def run_system(system_id):
    print(f"\n{'='*60}")
    print(f"  SYSTEM: {system_id}")
    print(f"{'='*60}")
    conn = get_connection(system_id)
    sr = {}

    # -------------------------------------------------------
    # T012 — House Bank Master (discover fields first)
    # -------------------------------------------------------
    print("\n--- T012 (House Bank Master) ---")
    flds = get_fields(conn, "T012")
    print(f"  T012 fields: {flds}")
    sr["T012_fields"] = flds
    if isinstance(flds, list):
        # Read with minimal key fields + relevant ones
        read_flds = [f for f in ["BUKRS","HBKID","BANKS","BANKL","BANKN","BRNCH","HKTID","STRAS","ORT01","SWIFT","TEXT1","NUMSFH"] if f in flds]
        rows = read_table(conn, "T012", read_flds,
                         ["BUKRS = 'UNES' AND HBKID IN ('UBA01','ECO09')"], f"{system_id}-T012")
        sr["T012"] = rows
        if not rows:
            # Try without IN syntax
            rows = read_table(conn, "T012", read_flds,
                             ["BUKRS = 'UNES'"], f"{system_id}-T012-all")
            sr["T012"] = rows

    # -------------------------------------------------------
    # T012K — House Bank Accounts (full fields)
    # -------------------------------------------------------
    print("\n--- T012K (House Bank Accounts) ---")
    flds = get_fields(conn, "T012K")
    print(f"  T012K fields: {flds}")
    sr["T012K_fields"] = flds
    if isinstance(flds, list):
        read_flds = [f for f in ["BUKRS","HBKID","HKTID","BANKN","BKONT","BANKL","HKONT","WAESSION","ZLSCH","UBKNT","DTAAI","XEBS"] if f in flds]
        # Fix: WAESSION was a placeholder, use actual field names from discovery
        read_flds = [f for f in flds if f in ["BUKRS","HBKID","HKTID","BANKN","BKONT","BANKL","HKONT","WAESSION","ZLSCH","UBKNT","DTAAI","XEBS","WAESSION"]]
        if not read_flds:
            read_flds = flds[:8]
        rows = read_table(conn, "T012K", read_flds,
                         ["BUKRS = 'UNES'"], f"{system_id}-T012K")
        sr["T012K"] = rows

    # -------------------------------------------------------
    # T030 — Automatic Postings (OBA1 exchange rate diffs)
    # -------------------------------------------------------
    print("\n--- T030 (Automatic Postings - OBA1) ---")
    flds = get_fields(conn, "T030")
    print(f"  T030 fields: {flds}")
    sr["T030_fields"] = flds
    if isinstance(flds, list):
        # T030 uses KTOPL (chart of accounts), not BUKRS
        # Key: KTOPL + KTOSL (transaction key). KDB/KDF = exch rate diff realized
        read_flds = [f for f in ["KTOPL","KTOSL","KONTS","KONTS2"] if f in flds]
        if not read_flds:
            read_flds = flds[:6]
        # Try KTOPL = UNES (UNESCO chart of accounts)
        rows = read_table(conn, "T030", read_flds,
                         ["KTOPL = 'UNES'"], f"{system_id}-T030-UNES")
        sr["T030_UNES"] = rows

        # Also try KTOPL = UNESCO or INT
        for ktopl in ["INT", "UNESCO"]:
            rows2 = read_table(conn, "T030", read_flds,
                              [f"KTOPL = '{ktopl}'"], f"{system_id}-T030-{ktopl}")
            if rows2 and not isinstance(rows2, str):
                sr[f"T030_{ktopl}"] = rows2

        # Exchange rate diff keys: KDB (realized), KDF (unrealized)
        for ktosl in ["KDB", "KDF"]:
            rows3 = read_table(conn, "T030", read_flds,
                              [f"KTOSL = '{ktosl}'"], f"{system_id}-T030-{ktosl}")
            sr[f"T030_{ktosl}"] = rows3

    # T030R
    print("\n--- T030R (Auto Posting Rules) ---")
    flds = get_fields(conn, "T030R")
    print(f"  T030R fields: {flds}")
    sr["T030R_fields"] = flds
    if isinstance(flds, list) and flds:
        read_flds = flds[:8]
        rows = read_table(conn, "T030R", read_flds, [], f"{system_id}-T030R-all", max_rows=50)
        sr["T030R"] = rows

    # -------------------------------------------------------
    # T042 — Payment Methods
    # -------------------------------------------------------
    print("\n--- T042I (Payment Bank Selection) ---")
    flds = get_fields(conn, "T042I")
    print(f"  T042I fields: {flds}")
    sr["T042I_fields"] = flds
    if isinstance(flds, list):
        read_flds = [f for f in flds if f in ["ZBUKR","ZLSCH","WAESSION","HBKID","HKTID","UBKNT"]]
        if not read_flds:
            read_flds = flds[:6]
        rows = read_table(conn, "T042I", read_flds,
                         ["ZBUKR = 'UNES'"], f"{system_id}-T042I")
        sr["T042I"] = rows

    # T042IY
    flds = get_fields(conn, "T042IY")
    print(f"  T042IY fields: {flds}")
    sr["T042IY_fields"] = flds
    if isinstance(flds, list):
        read_flds = flds[:8]
        rows = read_table(conn, "T042IY", read_flds,
                         ["ZBUKR = 'UNES'"], f"{system_id}-T042IY")
        sr["T042IY"] = rows

    # -------------------------------------------------------
    # T035D — Electronic Bank Statement Customizing
    # -------------------------------------------------------
    print("\n--- T035D (EBS Config) ---")
    flds = get_fields(conn, "T035D")
    print(f"  T035D fields: {flds}")
    sr["T035D_fields"] = flds
    if isinstance(flds, list):
        read_flds = flds[:8]
        rows = read_table(conn, "T035D", read_flds,
                         ["BUKRS = 'UNES'"], f"{system_id}-T035D")
        sr["T035D"] = rows
        if not rows:
            # Maybe uses different company code field
            key_field = flds[0] if flds else "BUKRS"
            rows = read_table(conn, "T035D", read_flds, [], f"{system_id}-T035D-all", max_rows=20)
            sr["T035D_sample"] = rows

    # -------------------------------------------------------
    # T037 / T037T — Cash Management Planning
    # -------------------------------------------------------
    print("\n--- T037/T037T (Cash Management) ---")
    flds = get_fields(conn, "T037")
    print(f"  T037 fields: {flds}")
    sr["T037_fields"] = flds

    flds_t = get_fields(conn, "T037T")
    print(f"  T037T fields: {flds_t}")
    sr["T037T_fields"] = flds_t

    # -------------------------------------------------------
    # T038 — Cash Management Account Assignment
    # -------------------------------------------------------
    print("\n--- T038 (CM Account Assignment) ---")
    flds = get_fields(conn, "T038")
    print(f"  T038 fields: {flds}")
    sr["T038_fields"] = flds
    if isinstance(flds, list):
        read_flds = flds[:8]
        # Check if BUKRS is a field
        if "BUKRS" in flds:
            rows = read_table(conn, "T038", read_flds, ["BUKRS = 'UNES'"], f"{system_id}-T038")
        else:
            rows = read_table(conn, "T038", read_flds, [], f"{system_id}-T038-all", max_rows=50)
        sr["T038"] = rows

        # If we got data, look for UBA01/ECO09 accounts
        if isinstance(rows, list) and rows:
            # Check for bank account fields
            for acct in ["1065421","1165421","1065424","1165424","1094421","1194421","1094424","1194424"]:
                if "HKONT" in flds:
                    r2 = read_table(conn, "T038", read_flds, [f"HKONT = '{acct}'"], f"{system_id}-T038-{acct}")
                    if r2 and not isinstance(r2, str):
                        sr[f"T038_{acct}"] = r2

    # -------------------------------------------------------
    # FEBKO — Bank Statement Headers (check if any exist)
    # -------------------------------------------------------
    print("\n--- FEBKO (Bank Statement Headers) ---")
    flds = get_fields(conn, "FEBKO")
    print(f"  FEBKO fields (first 15): {flds[:15] if isinstance(flds, list) else flds}")
    sr["FEBKO_fields"] = flds[:15] if isinstance(flds, list) else flds
    if isinstance(flds, list):
        read_flds = [f for f in ["BUKRS","HBKID","HKTID","AZESSION","AESSION","WAESSION","KUESSION","BANKS","BANKL","BANKN"] if f in flds]
        if not read_flds:
            read_flds = flds[:6]
        rows = read_table(conn, "FEBKO", read_flds, ["BUKRS = 'UNES'"], f"{system_id}-FEBKO")
        sr["FEBKO"] = rows

    # -------------------------------------------------------
    # SETLEAF — Check with correct field names
    # -------------------------------------------------------
    print("\n--- SETLEAF (GL Account Sets) ---")
    flds = get_fields(conn, "SETLEAF")
    print(f"  SETLEAF fields: {flds}")
    sr["SETLEAF_fields"] = flds
    if isinstance(flds, list):
        # The value fields are probably VAESSION_LOW -> find actual names
        val_low = [f for f in flds if "LOW" in f or "FROM" in f or "VALSF" in f]
        val_high = [f for f in flds if "HIGH" in f or "TO" in f or "VALST" in f]
        print(f"  Value fields LOW: {val_low}, HIGH: {val_high}")

        # Read all with SETCLASS=0000 that have our accounts
        for acct in ["1065421","1165421","1065424","1165424","1094421","1194421"]:
            for vf in val_low[:1]:  # Use first LOW field
                read_flds_set = [f for f in ["SETCLASS","SUBCLASS","SETNAME","VALSIGN","VALOPTION"] + val_low + val_high if f in flds][:8]
                rows = read_table(conn, "SETLEAF", read_flds_set,
                                 [f"SETCLASS = '0000' AND {vf} = '{acct}'"],
                                 f"{system_id}-SETLEAF-{acct}")
                if rows and not isinstance(rows, str):
                    sr[f"SETLEAF_{acct}"] = rows

    # -------------------------------------------------------
    # V_T018V view alternative — T012K.UBKNT is the clearing account
    # -------------------------------------------------------
    print("\n--- Clearing Account Check (T012K.UBKNT) ---")
    # T012K already read above with UBKNT field if it exists
    # Re-read T012K with ALL fields to be sure
    if isinstance(sr.get("T012K_fields"), list):
        all_flds = sr["T012K_fields"]
        # Read in chunks if needed
        rows = read_table(conn, "T012K", all_flds[:8], ["BUKRS = 'UNES'"], f"{system_id}-T012K-full1")
        if rows and not isinstance(rows, str) and len(all_flds) > 8:
            rows2 = read_table(conn, "T012K", all_flds[8:16], ["BUKRS = 'UNES'"], f"{system_id}-T012K-full2")
            if rows2 and not isinstance(rows2, str):
                for i, r in enumerate(rows):
                    if i < len(rows2):
                        r.update(rows2[i])
            if len(all_flds) > 16:
                rows3 = read_table(conn, "T012K", all_flds[16:24], ["BUKRS = 'UNES'"], f"{system_id}-T012K-full3")
                if rows3 and not isinstance(rows3, str):
                    for i, r in enumerate(rows):
                        if i < len(rows3):
                            r.update(rows3[i])
        sr["T012K_full"] = rows

    # -------------------------------------------------------
    # Check REGUH (payment documents) for any UBA01 usage
    # -------------------------------------------------------
    print("\n--- REGUH (Payment History) ---")
    flds = get_fields(conn, "REGUH")
    sr["REGUH_fields"] = flds[:15] if isinstance(flds, list) else flds

    conn.close()
    return sr


# ========== MAIN ==========
print("UBA01 House Bank E2E Config Check — v2")
print("="*60)

d01 = run_system("D01")
results["D01"] = d01

p01 = run_system("P01")
results["P01"] = p01

# Save
out_path = os.path.join(os.path.dirname(__file__), "uba01_config_check_v2_results.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nResults saved to {out_path}")
print("DONE")
