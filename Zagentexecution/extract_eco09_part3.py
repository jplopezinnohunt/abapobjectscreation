"""
ECO09 extraction part 3: FEBKO with specific fields, SETLEAF with correct fields,
and T042E with correct filter.
"""
import sys
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection, rfc_read_paginated

def safe_extract(conn, table, fields, where, label=""):
    print(f"\n{'='*70}")
    print(f"TABLE: {table} ({label})")
    print(f"WHERE: {where}")
    print(f"{'='*70}")
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
        print(f"  ERROR: {e}")
        return []

def main():
    conn = get_connection("P01")
    print("Connected to P01")

    # FEBKO — EBS headers for ECO09 (specific fields to avoid buffer exceeded)
    safe_extract(conn, "FEBKO",
                 ["KUESSION", "AZESSION", "AESSION", "BUKRS", "HBKID", "HKTID", "AZDAT", "ANESSION"],
                 "BUKRS = 'UNES' AND HBKID = 'ECO09'", "EBS Headers")

    # Try minimal FEBKO fields
    safe_extract(conn, "FEBKO",
                 ["KUESSION", "BUKRS", "HBKID", "HKTID", "AZDAT"],
                 "BUKRS = 'UNES' AND HBKID = 'ECO09'", "EBS Headers minimal")

    # SETLEAF — correct field names are VALFROM/VALTO
    for acct in ["0001094421", "0001094424"]:
        safe_extract(conn, "SETLEAF",
                     ["SETCLASS", "SUBCLASS", "SETNAME", "LINEID", "VALSIGN", "VALOPTION", "VALFROM", "VALTO", "SEQNR"],
                     f"VALFROM = '{acct}'", f"SETLEAF {acct}")

    # T042E — correct field is ZBUKR not BUKRS
    safe_extract(conn, "T042E",
                 ["ZBUKR", "ZLSCH", "XAVIS", "WAERS", "XEIPO", "XAUSL", "XFWAE", "ZFORN"],
                 "ZBUKR = 'UNES'", "Payment Methods per company")

    # T030H — check if 1094421 has entry with different CURTP
    for acct in ["0001094421", "0001094424"]:
        safe_extract(conn, "T030H",
                     ["KTOPL", "HKONT", "WAERS", "CURTP", "LKORR", "LSREA", "LHREA", "LSBEW", "LHBEW", "LSTRA", "LHTRA", "LSTRV", "LHTRV"],
                     f"KTOPL = 'UNES' AND HKONT = '{acct}'", f"OBA1 {acct}")

    conn.close()
    print("\nDone.")

if __name__ == "__main__":
    main()
