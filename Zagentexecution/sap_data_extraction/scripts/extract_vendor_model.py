"""
extract_vendor_model.py
=======================
Extract complete vendor/BP model to Gold DB.
Also extracts GB922 (GGB1 substitution results) which failed in previous run.

Tables:
  Tier 1: LFA1, LFB1, LFBK, LFBW (vendor master)
  Tier 2: KNA1, KNB1 (customer master — intercompany mirror)
  Config: T077K (vendor account groups), BNKA (bank master), TIBAN
  GGB:    GB922 (substitution results)

Usage:
    python extract_vendor_model.py                  # all tables
    python extract_vendor_model.py --table LFA1     # single table
    python extract_vendor_model.py --tier 1         # tier 1 only
"""

import sys, os, sqlite3, time, argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python"))
from rfc_helpers import get_connection, rfc_read_paginated

GOLD_DB = os.path.join(os.path.dirname(__file__), "..", "sqlite", "p01_gold_master_data.db")
BUKRS_FILTER = "BUKRS IN ('IIEP','UNES','UBO','MGIE','ICBA','UIL','UIS','IBE','ICTP')"


def save_to_db(db, table_name, rows):
    """Save rows to SQLite Gold DB."""
    if not rows:
        print(f"  {table_name}: 0 rows — skipped")
        return 0
    cols = list(rows[0].keys())
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    db.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    db.execute(f'CREATE TABLE "{table_name}" ({col_defs})')
    ph = ", ".join("?" for _ in cols)
    cn = ", ".join(f'"{c}"' for c in cols)
    for r in rows:
        vals = [str(r.get(c, "")).strip() for c in cols]
        db.execute(f'INSERT INTO "{table_name}" ({cn}) VALUES ({ph})', vals)
    db.commit()
    print(f"  {table_name}: {len(rows)} rows saved", flush=True)
    return len(rows)


def extract_split(guard, table, fields_groups, where, label=None):
    """Extract with manual field splitting and merge by key fields."""
    label = label or table
    print(f"Extracting {label} ({len(fields_groups)} field groups)...", flush=True)

    all_data = {}
    key_fields = fields_groups[0][:2]  # first 2 fields = key

    for i, fields in enumerate(fields_groups):
        try:
            rows = rfc_read_paginated(guard, table=table, fields=fields,
                                       where=where, batch_size=5000, throttle=2.0)
            print(f"  Group {i+1}: {len(rows)} rows, fields: {fields}", flush=True)
            for r in rows:
                key = "|".join(str(r.get(k, "")).strip() for k in key_fields)
                if key not in all_data:
                    all_data[key] = {}
                all_data[key].update(r)
        except Exception as e:
            print(f"  Group {i+1} ERROR: {str(e)[:120]}", flush=True)

    return list(all_data.values())


# ── TABLE DEFINITIONS ──────────────────────────────────────────────────

TABLES = {
    # Tier 1: Vendor Master
    "LFA1": {
        "tier": 1,
        "groups": [
            ["LIFNR", "LAND1", "NAME1", "NAME2", "KTOKK", "STCD1"],
            ["LIFNR", "ERDAT", "ERNAM", "SPERR", "LOEVM", "SPERM"],
        ],
        "where": "LIFNR >= '0000000001'",
    },
    "LFB1": {
        "tier": 1,
        "groups": [
            ["LIFNR", "BUKRS", "AKONT", "FDGRV", "ZTERM", "ZWELS", "ZAHLS"],
            ["LIFNR", "BUKRS", "LNRZE", "LNRZB", "SPERR", "LOEVM", "ERDAT", "ERNAM"],
        ],
        "where": BUKRS_FILTER,
    },
    "LFBK": {
        "tier": 1,
        "groups": [
            ["LIFNR", "BANKS", "BANKL", "BANKN", "KOINH", "BVTYP"],
            ["LIFNR", "BANKS", "BANKL", "BANKN", "IBAN", "BKREF"],
        ],
        "where": "LIFNR >= '0000000001'",
    },
    "LFBW": {
        "tier": 1,
        "groups": [
            ["LIFNR", "BUKRS", "WITHT", "WT_WITHCD", "WT_AGENT", "WT_SUBJCT"],
        ],
        "where": BUKRS_FILTER,
    },

    # Tier 2: Customer Master (intercompany)
    "KNA1": {
        "tier": 2,
        "groups": [
            ["KUNNR", "LAND1", "NAME1", "NAME2", "KTOKD", "STCD1"],
            ["KUNNR", "ERDAT", "ERNAM", "SPERR", "LOEVM"],
        ],
        "where": "KUNNR >= '0000000001'",
    },
    "KNB1": {
        "tier": 2,
        "groups": [
            ["KUNNR", "BUKRS", "AKONT", "FDGRV", "ZTERM", "ZWELS"],
            ["KUNNR", "BUKRS", "SPERR", "LOEVM", "ERDAT", "ERNAM"],
        ],
        "where": BUKRS_FILTER,
    },

    # Config
    "T077K": {
        "tier": 3,
        "groups": [
            ["MANDT", "KTOKK", "TXT30"],
        ],
        "where": "MANDT = '350'",
    },
    "BNKA": {
        "tier": 3,
        "groups": [
            ["BANKS", "BANKL", "BANKA", "PROVZ", "STRAS", "ORT01", "SWIFT"],
        ],
        "where": "BANKS IN ('FR','US','GB','CH','DE','JP','BE')",
    },

    # GB922 — GGB1 substitution results (fix MANDT syntax from previous failure)
    "GB922": {
        "tier": 3,
        "groups": [
            ["SUBSTID", "SUBSEQNR", "CONSEQNR", "SUBSTAB", "SUBSFIELD", "SUBSVAL"],
            ["SUBSTID", "SUBSEQNR", "MANIPEXP", "EXITSUBST", "TABSUBST", "FILEDSUB"],
        ],
        "where": "SUBSTID LIKE '%IIEP%' OR SUBSTID LIKE '%UNES%' OR SUBSTID LIKE '%UNESCO%' OR SUBSTID LIKE '%UBO%'",
    },
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", help="Extract single table")
    parser.add_argument("--tier", type=int, help="Extract tier (1, 2, or 3)")
    args = parser.parse_args()

    print(f"Gold DB: {GOLD_DB}", flush=True)
    guard = get_connection("P01")
    guard.connect()
    print("Connected to P01", flush=True)

    db = sqlite3.connect(GOLD_DB)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")

    total = 0
    for name, cfg in TABLES.items():
        if args.table and name != args.table.upper():
            continue
        if args.tier and cfg["tier"] != args.tier:
            continue

        try:
            rows = extract_split(guard, name, cfg["groups"], cfg["where"])
            total += save_to_db(db, name, rows)
            time.sleep(3)
        except Exception as e:
            print(f"  FAILED {name}: {str(e)[:150]}", flush=True)

    # Create indexes
    print("Creating indexes...", flush=True)
    indexes = [
        ("LFA1", "LIFNR"), ("LFA1", "KTOKK"),
        ("LFB1", "LIFNR"), ("LFB1", "BUKRS"), ("LFB1", "AKONT"),
        ("LFBK", "LIFNR"),
        ("KNA1", "KUNNR"), ("KNB1", "KUNNR"), ("KNB1", "BUKRS"),
    ]
    for tbl, col in indexes:
        try:
            db.execute(f'CREATE INDEX IF NOT EXISTS "idx_{tbl}_{col}" ON "{tbl}" ("{col}")')
        except:
            pass
    db.commit()

    guard.close()
    db.close()
    print(f"\nDONE. Total: {total} rows", flush=True)


if __name__ == "__main__":
    main()
