"""
ECO09 extraction part 2: remaining tables that didn't complete in part 1.
"""
import sys, json
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection, rfc_read_paginated

def get_all_fields(conn, table):
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                           ROWCOUNT=0, ROWSKIPS=0, OPTIONS=[], FIELDS=[])
        return [f["FIELDNAME"] for f in result.get("FIELDS", [])]
    except Exception as e:
        print(f"  ERROR getting fields for {table}: {e}")
        return []

def safe_extract(conn, table, where, label=""):
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
                if v.strip():
                    print(f"    {k:30s} = {v}")
        return rows
    except Exception as e:
        err = str(e)
        if "TABLE_NOT_AVAILABLE" in err or "NOT_AUTHORIZED" in err:
            print(f"  TABLE NOT AVAILABLE or NOT AUTHORIZED")
        elif "TABLE_WITHOUT_DATA" in err:
            print(f"  NO DATA")
        else:
            print(f"  ERROR: {e}")
        return []

def main():
    conn = get_connection("P01")
    print("Connected to P01")

    # 1. T018V — Clearing Accounts (re-run to get full output)
    safe_extract(conn, "T018V", "BUKRS = 'UNES' AND HBKID = 'ECO09'", "Clearing Accounts")

    # 2. T042I — Payment Bank Determination
    safe_extract(conn, "T042I", "ZBUKR = 'UNES' AND HBKID = 'ECO09'", "Payment Bank Determination")

    # 3. T042IY — Available Amounts
    safe_extract(conn, "T042IY", "ZBUKR = 'UNES' AND HBKID = 'ECO09'", "Available Amounts")

    # 4. TIBAN — try with BANKS/BANKL instead
    safe_extract(conn, "TIBAN", "BANKS = 'MZ' AND BANKL = 'XX001877'", "IBAN data")

    # 5. T035D — try BUKRS
    safe_extract(conn, "T035D", "BUKRS = 'UNES'", "Electronic Bank Statement - UNES")

    # 6. SKA1 — Chart of Accounts
    for acct in ["0001094421", "0001194421", "0001094424", "0001194424"]:
        safe_extract(conn, "SKA1", f"KTOPL = 'UNES' AND SAKNR = '{acct}'", f"CoA {acct}")

    # 7. SKAT — G/L Account Texts
    for acct in ["0001094421", "0001194421", "0001094424", "0001194424"]:
        safe_extract(conn, "SKAT", f"KTOPL = 'UNES' AND SAKNR = '{acct}' AND SPRAS = 'E'", f"Text {acct}")

    # 8. T012T — House Bank Text
    safe_extract(conn, "T012T", "BUKRS = 'UNES' AND HBKID = 'ECO09'", "House Bank Text")

    # 9. T030H — OBA1 data filtered for our specific accounts
    for acct in ["0001094421", "0001194421", "0001094424", "0001194424"]:
        safe_extract(conn, "T030H", f"KTOPL = 'UNES' AND HKONT = '{acct}'", f"OBA1 for {acct}")

    # 10. FDSB — Cash Management
    safe_extract(conn, "FDSB", "BUKRS = 'UNES' AND HBKID = 'ECO09'", "Cash Mgmt ECO09")

    # 11. SETLEAF — account sets (narrow search)
    for acct in ["0001094421", "0001094424"]:
        safe_extract(conn, "SETLEAF", f"VATEFROM = '{acct}' OR VATETO = '{acct}'", f"SETLEAF {acct}")

    # 12. T042E — Payment methods per company code (ECO09-related)
    safe_extract(conn, "T042E", "BUKRS = 'UNES'", "Payment Methods")

    # 13. FEBKO — Electronic Bank Statement headers (check for ECO09)
    safe_extract(conn, "FEBKO", "BUKRS = 'UNES' AND HBKID = 'ECO09'", "EBS Headers")

    # 14. T028B — Bank Posting Rules
    safe_extract(conn, "T028B", "BUKRS = 'UNES'", "Bank Posting Rules")

    conn.close()
    print("\nDone.")

if __name__ == "__main__":
    main()
