"""
fix_febep_missing_months.py — Extract FEBEP for months that failed with 27 fields.
Uses only 15 critical fields (no wide text fields) to avoid SAPSQL_DATA_LOSS.
Appends to existing FEBEP_2024_2026 table.
"""
import os, sys, time, sqlite3
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOLD_DB = os.path.join(BASE_DIR, "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
sys.path.insert(0, BASE_DIR)
from rfc_helpers import get_connection

# 15 critical fields only — drop BUTXT, VGSAP, AVKON, AVKOA, SGTXT, KFMOD (wide/text)
FIELDS = [
    "KUKEY", "ESNUM", "ESTAT", "BELNR", "GJAHR", "BUDAT", "VALUT", "KWBTR",
    "VGEXT", "VGINT", "GSBER", "ZUONR", "INTAG", "VGDEF", "VGMAN",
]

MISSING = [
    ("2024", 2), ("2024", 4), ("2024", 6), ("2024", 9), ("2024", 11),
    ("2025", 2), ("2025", 4), ("2025", 6), ("2025", 9), ("2025", 11),
    ("2026", 2),
]

BATCH = 5000
THROTTLE = 3.0

def fetch_month(conn, year, month, fields):
    """Fetch one month of FEBEP data using delimiter parsing."""
    from pyrfc import RFCError
    start = f"{year}{month:02d}01"
    end = f"{year}{month:02d}31"
    where = [{"TEXT": f"BUDAT >= '{start}' AND BUDAT <= '{end}'"}]
    rfc_fields = [{"FIELDNAME": f} for f in fields]

    all_rows = []
    offset = 0
    while True:
        try:
            result = conn.call("RFC_READ_TABLE", QUERY_TABLE="FEBEP", DELIMITER="|",
                               FIELDS=rfc_fields, OPTIONS=where,
                               ROWCOUNT=BATCH, ROWSKIPS=offset)
        except RFCError as e:
            err = str(e)
            if "TABLE_WITHOUT_DATA" in err:
                break
            if "DATA_BUFFER_EXCEEDED" in err or "SAPSQL_DATA_LOSS" in err:
                print(f" [BUFFER at {len(fields)} fields]", end="", flush=True)
                return None  # signal to try fewer fields
            raise

        if not result.get("DATA"):
            break

        hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
        for row in result["DATA"]:
            parts = row["WA"].split("|")
            all_rows.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)})

        if len(result["DATA"]) < BATCH:
            break
        offset += BATCH
        time.sleep(THROTTLE)

    return all_rows


def main():
    print("\n  Fix FEBEP Missing Months")
    print("  " + "=" * 50)

    conn = get_connection("P01")
    print("  Connected to P01.\n")

    db = sqlite3.connect(GOLD_DB)
    db.execute("PRAGMA journal_mode=WAL")

    # Get existing columns to match
    existing_cols = [r[1] for r in db.execute('PRAGMA table_info(FEBEP_2024_2026)').fetchall()]
    print(f"  Existing FEBEP cols: {len(existing_cols)}: {existing_cols[:10]}...")

    total_added = 0
    for year, month in MISSING:
        print(f"  {year}-{month:02d}: ", end="", flush=True)

        # Try with 15 fields
        rows = fetch_month(conn, year, month, FIELDS)

        if rows is None:
            # Buffer error — try with 10 fields
            reduced = FIELDS[:10]
            print(f"retrying with {len(reduced)} fields... ", end="", flush=True)
            rows = fetch_month(conn, year, month, reduced)

        if rows is None:
            # Still failing — try with 8 fields
            minimal = FIELDS[:8]
            print(f"retrying with {len(minimal)} fields... ", end="", flush=True)
            rows = fetch_month(conn, year, month, minimal)

        if rows is None or len(rows) == 0:
            print("0 rows (failed or empty)")
            continue

        # Insert into existing table — pad missing columns with empty string
        for row in rows:
            for col in existing_cols:
                if col not in row:
                    row[col] = ""

        placeholders = ", ".join(["?"] * len(existing_cols))
        cols = ", ".join(f'"{c}"' for c in existing_cols)
        db.executemany(
            f'INSERT INTO "FEBEP_2024_2026" ({cols}) VALUES ({placeholders})',
            [[r.get(c, "") for c in existing_cols] for r in rows]
        )
        db.commit()
        total_added += len(rows)
        print(f"{len(rows):,} rows added (total: {total_added:,})")
        time.sleep(1)

    conn.close()
    db.close()

    final_db = sqlite3.connect(GOLD_DB)
    total = final_db.execute("SELECT COUNT(*) FROM FEBEP_2024_2026").fetchone()[0]
    final_db.close()

    print(f"\n  Done. Added {total_added:,} rows. FEBEP total: {total:,}")


if __name__ == "__main__":
    main()
