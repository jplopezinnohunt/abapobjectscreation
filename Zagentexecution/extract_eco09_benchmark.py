"""
Extract COMPLETE ECO09 house bank configuration from P01 as benchmark.
ECO09 = Ecobank Maputo, 2 accounts: USD01 (G/L 1094421), MZN01 (G/L 1094424)
"""
import sys, json
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection, rfc_read_paginated

def get_all_fields(conn, table):
    """Get all field names from a table via DDIF_FIELDINFO_GET or RFC_READ_TABLE with empty fields."""
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                           ROWCOUNT=0, ROWSKIPS=0, OPTIONS=[], FIELDS=[])
        return [f["FIELDNAME"] for f in result.get("FIELDS", [])]
    except Exception as e:
        print(f"  ERROR getting fields for {table}: {e}")
        return []

def safe_extract(conn, table, where, label=""):
    """Extract all fields from table with where clause. Returns rows or empty list."""
    print(f"\n{'='*70}")
    print(f"TABLE: {table} {f'({label})' if label else ''}")
    print(f"WHERE: {where}")
    print(f"{'='*70}")

    fields = get_all_fields(conn, table)
    if not fields:
        print(f"  TABLE NOT AVAILABLE or no fields")
        return []

    print(f"  Fields ({len(fields)}): {', '.join(fields)}")

    try:
        rows = rfc_read_paginated(conn, table, fields, where, batch_size=500, throttle=1.0)
        print(f"  ROWS: {len(rows)}")
        for i, row in enumerate(rows):
            print(f"\n  --- Row {i+1} ---")
            for k, v in row.items():
                if v.strip():  # Only show non-empty fields
                    print(f"    {k:30s} = {v}")
        return rows
    except Exception as e:
        err = str(e)
        if "TABLE_NOT_AVAILABLE" in err or "NOT_AUTHORIZED" in err:
            print(f"  TABLE NOT AVAILABLE or NOT AUTHORIZED: {e}")
        elif "TABLE_WITHOUT_DATA" in err:
            print(f"  NO DATA (TABLE_WITHOUT_DATA)")
        else:
            print(f"  ERROR: {e}")
        return []

def main():
    conn = get_connection("P01")
    print("Connected to P01")

    all_results = {}

    # 1. T012 — House Bank Master
    rows = safe_extract(conn, "T012", "BUKRS = 'UNES' AND HBKID = 'ECO09'", "House Bank Master")
    all_results["T012"] = rows

    # 2. T012K — Bank Accounts
    rows = safe_extract(conn, "T012K", "BUKRS = 'UNES' AND HBKID = 'ECO09'", "Bank Accounts")
    all_results["T012K"] = rows

    # 3. BNKA — Bank Directory
    rows = safe_extract(conn, "BNKA", "BANKS = 'MZ' AND BANKL = 'XX001877'", "Bank Directory")
    all_results["BNKA"] = rows

    # 4. SKB1 — Company Code G/L details (4 accounts)
    gl_accounts = ["0001094421", "0001194421", "0001094424", "0001194424"]
    skb1_all = []
    for acct in gl_accounts:
        rows = safe_extract(conn, "SKB1", f"BUKRS = 'UNES' AND SAKNR = '{acct}'", f"G/L {acct}")
        skb1_all.extend(rows)
    all_results["SKB1"] = skb1_all

    # 5. OBA1 — Exchange Rate Differences
    # Try multiple tables
    for tbl in ["T030HB", "T030R", "T030H", "T030B", "T030", "FAGL_011FC"]:
        rows = safe_extract(conn, tbl, "KTOPL = 'UNES'", f"OBA1 candidate")
        if rows:
            # Filter for our accounts
            relevant = [r for r in rows if any(acct in str(r.values()) for acct in ["1094421", "1194421", "1094424", "1194424"])]
            if relevant:
                print(f"\n  >>> FOUND {len(relevant)} relevant rows in {tbl} <<<")
                for i, row in enumerate(relevant):
                    print(f"\n  --- Relevant Row {i+1} ---")
                    for k, v in row.items():
                        if v.strip():
                            print(f"    {k:30s} = {v}")
            all_results[tbl] = rows

    # 6. TIBAN — IBAN data
    rows = safe_extract(conn, "TIBAN", "BUKRS = 'UNES' AND HBKID = 'ECO09'", "IBAN data")
    all_results["TIBAN"] = rows

    # 7. T035D — Electronic Bank Statement (try BANKL filter)
    for where_clause in [
        "BANKL = 'XX001877'",
        "BANKS = 'MZ'",
    ]:
        rows = safe_extract(conn, "T035D", where_clause, "Electronic Bank Statement")
        if rows:
            all_results["T035D"] = rows
            break

    # 8. T018 / T018V — Clearing Accounts
    for tbl in ["T018", "T018V"]:
        rows = safe_extract(conn, tbl, "BUKRS = 'UNES' AND HBKID = 'ECO09'", "Clearing Accounts")
        if rows:
            all_results[tbl] = rows

    # 9. T042I — Payment Bank Determination
    rows = safe_extract(conn, "T042I", "ZBUKR = 'UNES' AND HBKID = 'ECO09'", "Payment Bank Determination")
    all_results["T042I"] = rows

    # 10. T042IY — Available Amounts
    rows = safe_extract(conn, "T042IY", "ZBUKR = 'UNES' AND HBKID = 'ECO09'", "Available Amounts")
    all_results["T042IY"] = rows

    # 11. Cash Management — try FDSB, T037
    for tbl in ["FDSB"]:
        rows = safe_extract(conn, tbl, "BUKRS = 'UNES'", "Cash Management")
        if rows:
            relevant = [r for r in rows if any(acct in str(r.values()) for acct in ["1094421", "1094424", "ECO09"])]
            if relevant:
                print(f"\n  >>> FOUND {len(relevant)} ECO09-relevant rows in {tbl} <<<")
                for i, row in enumerate(relevant):
                    print(f"\n  --- Relevant Row {i+1} ---")
                    for k, v in row.items():
                        if v.strip():
                            print(f"    {k:30s} = {v}")
            all_results[tbl] = rows

    # 12. SETLEAF — GS02 Account Sets
    for pattern in ["YBANK%"]:
        rows = safe_extract(conn, "SETLEAF", f"SETNAME LIKE '{pattern}'", "Account Sets")
        if rows:
            relevant = [r for r in rows if any(acct in str(r.values()) for acct in ["1094421", "1094424", "1194421", "1194424"])]
            if relevant:
                print(f"\n  >>> FOUND {len(relevant)} relevant SETLEAF rows <<<")
                for i, row in enumerate(relevant):
                    print(f"\n  --- Relevant Row {i+1} ---")
                    for k, v in row.items():
                        if v.strip():
                            print(f"    {k:30s} = {v}")
            all_results["SETLEAF"] = rows

    # 13. FCLM_BSM / Bank Statement Monitor
    for tbl in ["FCLM_BSM_CUST", "FTE_BSM_CUST"]:
        rows = safe_extract(conn, tbl, "BUKRS = 'UNES'", "Bank Statement Monitor")
        if rows:
            all_results[tbl] = rows

    # 14. SKA1 — Chart of Accounts data for our G/L accounts
    ska1_all = []
    for acct in gl_accounts:
        rows = safe_extract(conn, "SKA1", f"KTOPL = 'UNES' AND SAKNR = '{acct}'", f"CoA {acct}")
        ska1_all.extend(rows)
    all_results["SKA1"] = ska1_all

    # 15. SKAT — G/L Account Texts
    skat_all = []
    for acct in gl_accounts:
        rows = safe_extract(conn, "SKAT", f"KTOPL = 'UNES' AND SAKNR = '{acct}' AND SPRAS = 'E'", f"Text {acct}")
        skat_all.extend(rows)
    all_results["SKAT"] = skat_all

    # 16. T012T — House Bank Text
    rows = safe_extract(conn, "T012T", "BUKRS = 'UNES' AND HBKID = 'ECO09'", "House Bank Text")
    all_results["T012T"] = rows

    # Save JSON
    output_path = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\eco09_benchmark.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n\nSaved to {output_path}")

    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
