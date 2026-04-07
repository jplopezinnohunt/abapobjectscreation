"""
uba01_gl_comparison.py
======================
Deep field-by-field comparison of 4 G/L accounts between P01 and D01.
Accounts: 0001065421, 0001165421, 0001065424, 0001165424
Chart of Accounts / Company Code: UNES

Tables compared: SKA1 (CoA level), SKB1 (company code level), SKAT (texts)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from rfc_helpers import get_connection


ACCOUNTS = ["0001065421", "0001165421", "0001065424", "0001165424"]
KTOPL = "UNES"
BUKRS = "UNES"

TABLES = {
    "SKA1": {"key_filter": "KTOPL", "key_value": KTOPL, "row_key": ["KTOPL", "SAKNR"]},
    "SKB1": {"key_filter": "BUKRS", "key_value": BUKRS, "row_key": ["BUKRS", "SAKNR"]},
    "SKAT": {"key_filter": "KTOPL", "key_value": KTOPL, "row_key": ["SPRAS", "KTOPL", "SAKNR"]},
}


def discover_fields(conn, table_name):
    """Get all field names from a table by reading metadata (ROWCOUNT=0)."""
    result = conn.call(
        "RFC_READ_TABLE",
        QUERY_TABLE=table_name,
        ROWCOUNT=0,
        DELIMITER="|",
        OPTIONS=[],
        FIELDS=[],
    )
    return [f["FIELDNAME"] for f in result.get("FIELDS", [])]


def read_accounts(conn, table_name, fields, key_filter, key_value):
    """Read all 4 accounts from a table. Uses per-account calls to avoid long WHERE."""
    from rfc_helpers import rfc_read_paginated
    all_rows = []
    for acct in ACCOUNTS:
        where = f"{key_filter} = '{key_value}' AND SAKNR = '{acct}'"
        rows = rfc_read_paginated(conn, table_name, fields, where, batch_size=100, throttle=0.5)
        all_rows.extend(rows)
    return all_rows


def rows_to_dict(rows, row_key_fields):
    """Index rows by composite key (tuple of key field values)."""
    result = {}
    for row in rows:
        key = tuple(row.get(k, "").strip() for k in row_key_fields)
        result[key] = row
    return result


def compare_rows(p01_row, d01_row, all_fields):
    """Compare two row dicts field by field. Returns (matching, different, p01_only, d01_only)."""
    matching = []
    different = []
    p01_only = []
    d01_only = []

    p01_fields = set(p01_row.keys()) if p01_row else set()
    d01_fields = set(d01_row.keys()) if d01_row else set()

    for f in all_fields:
        p_val = (p01_row.get(f, "").strip() if p01_row else None)
        d_val = (d01_row.get(f, "").strip() if d01_row else None)

        if p_val is not None and d_val is None:
            p01_only.append((f, p_val))
        elif p_val is None and d_val is not None:
            d01_only.append((f, d_val))
        elif p_val == d_val:
            matching.append((f, p_val))
        else:
            different.append((f, p_val, d_val))

    return matching, different, p01_only, d01_only


def print_separator(char="=", width=100):
    print(char * width)


def print_comparison(table_name, row_key_fields, all_fields, p01_dict, d01_dict):
    """Print side-by-side comparison for a table."""
    print_separator("=")
    print(f"  TABLE: {table_name}")
    print(f"  Key fields: {', '.join(row_key_fields)}")
    print(f"  Total fields discovered: {len(all_fields)}")
    print(f"  P01 rows: {len(p01_dict)}  |  D01 rows: {len(d01_dict)}")
    print_separator("=")

    # Collect all keys from both systems
    all_keys = sorted(set(list(p01_dict.keys()) + list(d01_dict.keys())))

    if not all_keys:
        print("  No data found in either system.\n")
        return

    for key in all_keys:
        p01_row = p01_dict.get(key)
        d01_row = d01_dict.get(key)

        print_separator("-")
        print(f"  Row Key: {' | '.join(str(k) for k in key)}")

        if p01_row and not d01_row:
            print("  STATUS: EXISTS IN P01 ONLY (MISSING IN D01)")
            print(f"  Fields: {len(p01_row)}")
            for f in all_fields:
                v = p01_row.get(f, "")
                if v.strip():
                    print(f"    {f:30s} = {v}")
            continue

        if d01_row and not p01_row:
            print("  STATUS: EXISTS IN D01 ONLY (MISSING IN P01)")
            print(f"  Fields: {len(d01_row)}")
            for f in all_fields:
                v = d01_row.get(f, "")
                if v.strip():
                    print(f"    {f:30s} = {v}")
            continue

        matching, different, p01_only, d01_only = compare_rows(p01_row, d01_row, all_fields)

        if different:
            print(f"  STATUS: DIFFERENCES FOUND ({len(different)} fields differ)")
        else:
            print(f"  STATUS: IDENTICAL ({len(matching)} fields match)")

        if different:
            print(f"\n  DIFFERENT VALUES ({len(different)} fields):")
            print(f"    {'FIELD':30s} {'P01 VALUE':40s} {'D01 VALUE':40s}")
            print(f"    {'-----':30s} {'---------':40s} {'---------':40s}")
            for f, pv, dv in different:
                print(f"    {f:30s} {repr(pv):40s} {repr(dv):40s}")

        if p01_only:
            print(f"\n  P01-ONLY FIELDS ({len(p01_only)}):")
            for f, v in p01_only:
                print(f"    {f:30s} = {repr(v)}")

        if d01_only:
            print(f"\n  D01-ONLY FIELDS ({len(d01_only)}):")
            for f, v in d01_only:
                print(f"    {f:30s} = {repr(v)}")

        if matching:
            print(f"\n  MATCHING FIELDS ({len(matching)}):")
            for f, v in matching:
                val_display = repr(v) if v else "''"
                print(f"    {f:30s} = {val_display}")

    print()


def main():
    print("=" * 100)
    print("  G/L ACCOUNT DEEP COMPARISON: P01 vs D01")
    print(f"  Accounts: {', '.join(ACCOUNTS)}")
    print(f"  Chart of Accounts: {KTOPL}  |  Company Code: {BUKRS}")
    print("=" * 100)
    print()

    # Connect to both systems
    print("Connecting to P01...")
    p01 = get_connection("P01")
    print("  P01 connected.")

    print("Connecting to D01...")
    d01 = get_connection("D01")
    print("  D01 connected.")
    print()

    for table_name, cfg in TABLES.items():
        print(f"--- Processing {table_name} ---")

        # Discover ALL fields from P01 (master)
        print(f"  Discovering fields from P01...")
        p01_fields = discover_fields(p01, table_name)
        print(f"  P01 fields: {len(p01_fields)}")

        print(f"  Discovering fields from D01...")
        d01_fields = discover_fields(d01, table_name)
        print(f"  D01 fields: {len(d01_fields)}")

        # Union of all fields
        all_fields = list(dict.fromkeys(p01_fields + [f for f in d01_fields if f not in p01_fields]))
        print(f"  Union fields: {len(all_fields)}")

        # Read data — use each system's own discovered fields to avoid missing-field errors
        print(f"  Reading P01 data...")
        p01_rows = read_accounts(p01, table_name, p01_fields, cfg["key_filter"], cfg["key_value"])
        print(f"  P01: {len(p01_rows)} rows")

        print(f"  Reading D01 data...")
        d01_rows = read_accounts(d01, table_name, d01_fields, cfg["key_filter"], cfg["key_value"])
        print(f"  D01: {len(d01_rows)} rows")

        # Index by key
        row_key = cfg["row_key"]
        p01_dict = rows_to_dict(p01_rows, row_key)
        d01_dict = rows_to_dict(d01_rows, row_key)

        # Compare and print
        print_comparison(table_name, row_key, all_fields, p01_dict, d01_dict)

    # Summary
    print_separator("=")
    print("  COMPARISON COMPLETE")
    print_separator("=")

    p01.close()
    d01.close()


if __name__ == "__main__":
    main()
