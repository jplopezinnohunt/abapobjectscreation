"""
extract_travel_tables.py
========================
Extract travel-related tables to Gold DB for INC-000006073 analysis preservation.

Tables extracted:
  - PA0001: HR master (org assignment) — filter IIEP/UNES/UBO/MGIE/ICBA/UIL/UIS
  - PA0027: Cost distribution — all subtypes
  - LFA1: Vendor master (general) — personnel vendors
  - LFB1: Vendor master (company code) — AKONT, KTOKK
  - PTRV_SCOS: Trip cost assignment — 2024-2026
  - PTRV_SHDR: Trip header summary — 2024-2026
  - GB922: GGB1 substitution results (complements GB901 conditions)

Usage:
    python extract_travel_tables.py [--table TABLE_NAME]
"""

import sys
import os
import sqlite3
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python"))
from rfc_helpers import get_connection, rfc_read_paginated

GOLD_DB = os.path.join(os.path.dirname(__file__), "..", "sqlite", "p01_gold_master_data.db")

# Company codes for travel analysis
COMPANY_CODES = "('IIEP','UNES','UBO','MGIE','ICBA','UIL','UIS','IBE','ICTP')"


def extract_table(guard, db, table_name, fields, where_clause, table_label=None):
    """Generic extraction: RFC_READ_TABLE → SQLite."""
    label = table_label or table_name
    print(f"\n{'='*60}")
    print(f"Extracting {label}...")
    print(f"  Table: {table_name}")
    print(f"  Fields: {len(fields)}")
    print(f"  WHERE: {where_clause[:80]}...")

    try:
        rows = rfc_read_paginated(
            guard, table=table_name, fields=fields,
            where=where_clause, batch_size=5000, throttle=2.0
        )
    except Exception as e:
        print(f"  ERROR extracting {table_name}: {e}")
        return 0

    if not rows:
        print(f"  No rows returned for {table_name}")
        return 0

    # Create table
    cols = list(rows[0].keys())
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    db.execute(f'DROP TABLE IF EXISTS "{label}"')
    db.execute(f'CREATE TABLE "{label}" ({col_defs})')

    # Insert rows
    placeholders = ", ".join("?" for _ in cols)
    col_names = ", ".join(f'"{c}"' for c in cols)
    for row in rows:
        vals = [str(row.get(c, "")).strip() for c in cols]
        db.execute(f'INSERT INTO "{label}" ({col_names}) VALUES ({placeholders})', vals)

    db.commit()
    print(f"  Loaded {len(rows)} rows into {label}")
    return len(rows)


def extract_pa0001(guard, db):
    """PA0001 — HR Organizational Assignment. Key fields for travel analysis."""
    fields = [
        "PERNR", "SUBTY", "OBJPS", "SPRPS", "ENDDA", "BEGDA",
        "BUKRS", "WERKS", "BTRTL", "PERSG", "PERSK",
        "ORGEH", "STELL", "PLANS", "KOSTL", "ABKRS",
        "PTEXT", "GSBER", "FISTL", "GESSION", "GEBER"
    ]
    # Get all current + recent records for travel-relevant company codes
    where = f"BUKRS IN {COMPANY_CODES} AND ENDDA >= '20240101'"
    return extract_table(guard, db, "PA0001", fields, where)


def extract_pa0027(guard, db):
    """PA0027 — Cost Distribution. Critical for BAdI EX_ZWEP_ACCOUNT2 analysis."""
    fields = [
        "PERNR", "SUBTY", "OBJPS", "SPRPS", "ENDDA", "BEGDA",
        "ANESSION", "BUKRS",
        "KPR01", "KBU01", "KGB01", "KST01", "KOR01",
        "FCT01", "FCD01", "PSP01",
        "KPR02", "KBU02", "KGB02", "KST02", "KOR02",
        "FCT02", "FCD02", "PSP02"
    ]
    # All records — small table, no date filter needed
    where = "SUBTY IN ('01','02')"
    return extract_table(guard, db, "PA0027", fields, where)


def extract_lfa1(guard, db):
    """LFA1 — Vendor Master General. KTOKK determines reconciliation account."""
    fields = [
        "LIFNR", "LAND1", "NAME1", "NAME2", "ORT01",
        "KTOKK", "STCD1", "STCD2", "TELF1",
        "ERDAT", "ERNAM", "SPERR", "LOEVM"
    ]
    # Personnel vendors (10xxxxxx range typical for employees)
    where = "KTOKK IN ('UNES','SCSA','STAF','EMPL','PERS')"
    return extract_table(guard, db, "LFA1", fields, where)


def extract_lfb1(guard, db):
    """LFB1 — Vendor Master Company Code. AKONT = reconciliation GL account."""
    fields = [
        "LIFNR", "BUKRS", "AKONT", "BEGRU", "FDGRV",
        "ZTERM", "ZWELS", "ZAHLS", "LNRZE", "LNRZB",
        "SPERR", "LOEVM", "XVERR", "TOGRU",
        "ERDAT", "ERNAM"
    ]
    where = f"BUKRS IN {COMPANY_CODES}"
    return extract_table(guard, db, "LFB1", fields, where)


def extract_ptrv_scos(guard, db):
    """PTRV_SCOS — Trip Cost Assignment. The definitive evidence table."""
    fields = [
        "REINR", "SEQNR", "COMP_CODE", "BUS_AREA", "COSTCENTER",
        "FUNDS_CTR", "FUND", "FUNC_AREA", "WBS_ELEMENT",
        "CO_AREA", "GRANT_NBR", "CURRENCY", "PERCENT",
        "REC_AMOUNT", "TOTAL_AMOUNT"
    ]
    # All trips — REINR is trip number, filter by date via join later
    where = "REINR >= '0100000000'"
    return extract_table(guard, db, "PTRV_SCOS", fields, where)


def extract_ptrv_shdr(guard, db):
    """PTRV_SHDR — Trip Header Summary."""
    fields = [
        "REINR", "PESSION_PERNR", "STATUS", "REINR_ORIG",
        "DATV1", "DATB1", "UZEIT1", "UZEIT2",
        "ZESSION_ZESSION", "ZESSION_LGART", "ZESSION_MOESSION",
        "TOTAL_AMOUNT", "CURRENCY", "COUNTRY"
    ]
    where = "DATV1 >= '20240101'"
    return extract_table(guard, db, "PTRV_SHDR", fields, where)


def extract_gb922(guard, db):
    """GB922 — GGB1 Substitution Result Assignments (complements GB901 conditions)."""
    fields = [
        "MANDT", "CALLID", "SEESSION_SEQNR", "TABNAME", "FIELDNAME",
        "EXITNAME", "CONSTANT"
    ]
    where = "MANDT = '350'"
    return extract_table(guard, db, "GB922", fields, where)


def main():
    target_table = None
    if len(sys.argv) > 2 and sys.argv[1] == "--table":
        target_table = sys.argv[2].upper()

    print(f"Gold DB: {GOLD_DB}")
    print(f"Target: {target_table or 'ALL tables'}")

    guard = get_connection("P01")
    guard.connect()

    db = sqlite3.connect(GOLD_DB)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")

    total = 0
    extractors = {
        "PA0001": extract_pa0001,
        "PA0027": extract_pa0027,
        "LFA1": extract_lfa1,
        "LFB1": extract_lfb1,
        "PTRV_SCOS": extract_ptrv_scos,
        "PTRV_SHDR": extract_ptrv_shdr,
        "GB922": extract_gb922,
    }

    for name, func in extractors.items():
        if target_table and name != target_table:
            continue
        try:
            count = func(guard, db)
            total += count
            time.sleep(2)  # throttle between tables
        except Exception as e:
            print(f"  FAILED {name}: {e}")

    guard.close()
    db.close()

    print(f"\n{'='*60}")
    print(f"DONE. Total rows loaded: {total}")


if __name__ == "__main__":
    main()
