"""
fix_febko_reextract.py — Re-extract FEBKO with correct DD03L field names.
Probes DD03L first, then extracts all non-MANDT fields year by year.
"""
import os, sys, time, sqlite3
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOLD_DB = os.path.join(BASE_DIR, "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
sys.path.insert(0, BASE_DIR)
from rfc_helpers import get_connection

BATCH = 5000
THROTTLE = 3.0

def probe_dd03l(conn, table):
    result = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD03L", DELIMITER="|",
                       ROWCOUNT=200, ROWSKIPS=0,
                       OPTIONS=[{"TEXT": f"TABNAME = '{table}' AND FIELDNAME <> '.INCLUDE'"}],
                       FIELDS=[{"FIELDNAME": "FIELDNAME"}, {"FIELDNAME": "DATATYPE"},
                               {"FIELDNAME": "LENG"}, {"FIELDNAME": "POSITION"}])
    hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
    rows = []
    for row in result["DATA"]:
        parts = row["WA"].split("|")
        d = {h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)}
        rows.append(d)
    rows.sort(key=lambda r: int(r.get("POSITION", "0") or "0"))
    return [(r["FIELDNAME"], r["DATATYPE"], r["LENG"]) for r in rows if r["FIELDNAME"] != "MANDT"]


def fetch_page(conn, table, fields, where, batch, offset):
    from pyrfc import RFCError
    rfc_fields = [{"FIELDNAME": f} for f in fields]
    rfc_opts = [{"TEXT": where}] if where else []
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                           FIELDS=rfc_fields, OPTIONS=rfc_opts,
                           ROWCOUNT=batch, ROWSKIPS=offset)
    except RFCError as e:
        err = str(e)
        if "TABLE_WITHOUT_DATA" in err:
            return None
        if "DATA_BUFFER_EXCEEDED" in err or "SAPSQL_DATA_LOSS" in err:
            return "BUFFER"
        raise
    if not result.get("DATA"):
        return None
    hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
    rows = []
    for row in result["DATA"]:
        parts = row["WA"].split("|")
        rows.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)})
    return rows


def extract_with_split(conn, table, fields, where, label):
    """Extract with auto field-splitting."""
    all_rows = []
    offset = 0

    # Test full field list
    test = fetch_page(conn, table, fields, where, 1, 0)
    if test == "BUFFER":
        # Find working chunk size
        chunk = 6
        while chunk >= 2:
            t = fetch_page(conn, table, fields[:chunk], where, 1, 0)
            if t not in ("BUFFER", None):
                break
            chunk -= 1
        if chunk < 2:
            return []

        print(f"  [{label}] Splitting into chunks of {chunk}")
        chunks = [fields[i:i+chunk] for i in range(0, len(fields), chunk)]

        while True:
            page = fetch_page(conn, table, chunks[0], where, BATCH, offset)
            if page is None or page == "BUFFER":
                break
            for ci in range(1, len(chunks)):
                extra = fetch_page(conn, table, chunks[ci], where, BATCH, offset)
                if extra and extra != "BUFFER":
                    for i, row in enumerate(extra):
                        if i < len(page):
                            page[i].update(row)
            all_rows.extend(page)
            if len(page) < BATCH:
                break
            offset += BATCH
            time.sleep(THROTTLE)
    elif test is None:
        return []
    else:
        # Full field list works
        all_rows = list(test) if isinstance(test, list) else []
        # But we only got 1 row from test, re-fetch properly
        all_rows = []
        while True:
            rows = fetch_page(conn, table, fields, where, BATCH, offset)
            if rows is None or rows == "BUFFER":
                break
            all_rows.extend(rows)
            if len(rows) < BATCH:
                break
            offset += BATCH
            time.sleep(THROTTLE)

    return all_rows


def main():
    print("\n  Fix FEBKO Re-extraction with DD03L field names")
    print("  " + "=" * 50)

    conn = get_connection("P01")
    print("  Connected to P01.\n")

    # Step 1: Probe DD03L
    dd_fields = probe_dd03l(conn, "FEBKO")
    print(f"  DD03L FEBKO: {len(dd_fields)} fields:")
    for f, dt, ln in dd_fields:
        print(f"    {f:20s} {dt:6s} len={ln}")

    # Step 2: Select fields — prioritize key fields + important enrichment
    # Keep all fields but if too many, split into chunks
    all_field_names = [f[0] for f in dd_fields]
    print(f"\n  Will extract {len(all_field_names)} fields")

    # Step 3: Extract year by year
    db = sqlite3.connect(GOLD_DB)
    db.execute("PRAGMA journal_mode=WAL")

    all_rows = []
    for year in ["2024", "2025", "2026"]:
        # AZIDT is 9 chars: YYYYMMDD + statement-number-within-day
        where = f"AZIDT >= '{year}0101' AND AZIDT <= '{year}1231'"
        print(f"\n  Year {year}:", end=" ", flush=True)
        rows = extract_with_split(conn, "FEBKO", all_field_names, where, f"FEBKO-{year}")
        if rows:
            all_rows.extend(rows)
            print(f"{len(rows):,} rows")
        else:
            print("0 rows")
        time.sleep(1)

    conn.close()

    if not all_rows:
        print("  No data!")
        db.close()
        return

    # Load to SQLite
    actual = list(all_rows[0].keys())
    cols_def = ", ".join(f'"{f}" TEXT' for f in actual)
    db.execute('DROP TABLE IF EXISTS "FEBKO_2024_2026"')
    db.execute(f'CREATE TABLE "FEBKO_2024_2026" ({cols_def})')
    placeholders = ", ".join(["?"] * len(actual))
    cols = ", ".join(f'"{f}"' for f in actual)
    db.executemany(
        f'INSERT INTO "FEBKO_2024_2026" ({cols}) VALUES ({placeholders})',
        [[r.get(f, "") for f in actual] for r in all_rows]
    )
    db.commit()
    db.close()

    print(f"\n  Done. FEBKO: {len(all_rows):,} rows, {len(actual)} fields")
    print(f"  Fields: {actual}")


if __name__ == "__main__":
    main()
