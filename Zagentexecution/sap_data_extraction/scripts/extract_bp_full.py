"""
extract_bp_full.py — Complete Business Partner / Vendor / Customer extraction to Gold DB.
Extracts ALL fields from each table (auto field-splitting for wide tables).
22 tables: vendor + customer + BP + address + config + GB922.
"""
import sys, os, sqlite3, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python"))
from rfc_helpers import get_connection, rfc_read_paginated

GOLD_DB = os.path.join(os.path.dirname(__file__), "..", "sqlite", "p01_gold_master_data.db")
Q = chr(39)  # single quote for RFC WHERE clauses
BUKRS_WHERE = f"BUKRS IN ({Q}IIEP{Q},{Q}UNES{Q},{Q}UBO{Q},{Q}MGIE{Q},{Q}ICBA{Q},{Q}UIL{Q},{Q}UIS{Q},{Q}IBE{Q},{Q}ICTP{Q})"
ALL_VENDORS = f"LIFNR >= {Q}0000000001{Q}"
ALL_BP = f"PARTNER >= {Q}0000000001{Q}"
ALL_CUST = f"KUNNR >= {Q}0000000001{Q}"


def get_all_fields(guard, table):
    """Get complete field list via DDIF_FIELDINFO_GET (avoids DATA_BUFFER_EXCEEDED on wide tables)."""
    result = guard.call("DDIF_FIELDINFO_GET", TABNAME=table, FIELDNAME="", LANGU="E")
    fields = [f["FIELDNAME"] for f in result["DFIES_TAB"] if f["FIELDNAME"] != ".INCLUDE"]
    print(f"  {table}: {len(fields)} fields detected", flush=True)
    return fields


def save(db, name, rows):
    if not rows:
        print(f"  {name}: 0 rows", flush=True)
        return 0
    cols = [c.replace("/", "_").replace(".", "_") for c in rows[0].keys()]
    db.execute(f'DROP TABLE IF EXISTS "{name}"')
    db.execute(f'CREATE TABLE "{name}" ({",".join(chr(34)+c+chr(34)+" TEXT" for c in cols)})')
    ph = ",".join("?" for _ in cols)
    for r in rows:
        db.execute(f'INSERT INTO "{name}" VALUES ({ph})', [str(r.get(c, "")).strip() for c in cols])
    db.commit()
    print(f"  {name}: {len(rows)} rows SAVED", flush=True)
    return len(rows)


def extract_all_fields(guard, table, where):
    """Extract ALL fields from a table with auto field-splitting."""
    print(f"--- {table} ---", flush=True)
    try:
        fields = get_all_fields(guard, table)
        rows = rfc_read_paginated(guard, table=table, fields=fields, where=where, batch_size=5000, throttle=2.0)
        print(f"  {len(rows)} rows extracted", flush=True)
        return rows
    except Exception as e:
        print(f"  ERROR: {str(e)[:150]}", flush=True)
        return []


def main():
    # Allow single table extraction via CLI
    target = sys.argv[1].upper() if len(sys.argv) > 1 else None

    guard = get_connection("P01")
    # get_connection already calls connect()
    db = sqlite3.connect(GOLD_DB)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    print("Connected to P01 + Gold DB", flush=True)

    # Table definitions: name → WHERE clause
    TABLES = {
        # Vendor Master
        "LFA1":  ALL_VENDORS,
        "LFB1":  BUKRS_WHERE,
        "LFBK":  ALL_VENDORS,
        "LFB5":  BUKRS_WHERE,
        "LFAS":  ALL_VENDORS,
        "LFC1":  BUKRS_WHERE + f" AND GJAHR >= {Q}2024{Q}",
        # Customer Master
        "KNA1":  ALL_CUST,
        "KNB1":  BUKRS_WHERE,
        "KNVV":  ALL_CUST,
        # Business Partner
        "BUT000": ALL_BP,
        "BUT0BK": ALL_BP,
        "BUT100": ALL_BP,
        "BP001":  ALL_BP,
        "CVI_VEND_LINK": f"VENDOR >= {Q}0000000001{Q}",
        "CVI_CUST_LINK": f"CUSTOMER >= {Q}0000000001{Q}",
        # Address
        "ADRC": f"ADDRNUMBER >= {Q}0000000001{Q}",
        "ADR6": f"ADDRNUMBER >= {Q}0000000001{Q}",
        "ADR2": f"ADDRNUMBER >= {Q}0000000001{Q}",
        # Config
        "TIBAN": f"BANKS >= {Q}A{Q}",
        "T077K": f"KTOKK >= {Q} {Q}",
        # GGB1 results
        "GB922": f"SUBSTID LIKE {Q}%IIEP%{Q} OR SUBSTID LIKE {Q}%UNES%{Q} OR SUBSTID LIKE {Q}%UNESCO%{Q} OR SUBSTID LIKE {Q}%UBO%{Q}",
    }

    total = 0
    for name, where in TABLES.items():
        if target and name != target:
            continue
        try:
            rows = extract_all_fields(guard, name, where)
            total += save(db, name, rows)
            time.sleep(3)
        except Exception as e:
            print(f"  FAILED {name}: {str(e)[:150]}", flush=True)

    # Indexes
    print("Creating indexes...", flush=True)
    indexes = [
        ("LFA1", "LIFNR"), ("LFA1", "KTOKK"),
        ("LFB1", "LIFNR"), ("LFB1", "BUKRS"), ("LFB1", "AKONT"),
        ("LFBK", "LIFNR"), ("LFB5", "LIFNR"),
        ("KNA1", "KUNNR"), ("KNB1", "KUNNR"), ("KNB1", "BUKRS"),
        ("KNVV", "KUNNR"),
        ("BUT000", "PARTNER"), ("BUT0BK", "PARTNER"), ("BUT100", "PARTNER"),
        ("BP001", "PARTNER"),
        ("CVI_VEND_LINK", "VENDOR"), ("CVI_CUST_LINK", "CUSTOMER"),
        ("ADRC", "ADDRNUMBER"), ("ADR6", "ADDRNUMBER"),
        ("TIBAN", "IBAN"),
    ]
    for tbl, col in indexes:
        try:
            db.execute(f'CREATE INDEX IF NOT EXISTS idx_{tbl}_{col} ON "{tbl}" ("{col}")')
        except:
            pass
    db.commit()

    guard.close()
    db.close()
    print(f"\n{'='*60}\nDONE. Total: {total} rows across all tables", flush=True)


if __name__ == "__main__":
    main()
