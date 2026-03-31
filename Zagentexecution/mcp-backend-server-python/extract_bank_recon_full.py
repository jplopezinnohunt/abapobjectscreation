"""
extract_bank_recon_full.py — Session #030: Bank Statement & Reconciliation Full Extraction
===========================================================================================
7 extraction tasks in one script:
  1. FEBEP enrichment  (~20 fields added to existing 223K rows)
  2. FEBKO enrichment  (~12 fields added to existing 85K rows)
  3. FEBRE extraction   (Tag 86 note-to-payee text, fresh)
  4. BSAS AUGBL re-enrichment (bank GL items, HKONT LIKE '0001%')
  5. T012K re-extraction (with UKONT)
  6. T028A + T028E extraction (account symbol definitions)
  7. TCURR/TCURF extraction (exchange rates)

Source: P01 (production, SNC/SSO)
Output: Gold DB

Usage:
    python extract_bank_recon_full.py              # All tasks
    python extract_bank_recon_full.py --task febep  # Single task
    python extract_bank_recon_full.py --dry-run     # Show plan only
"""

import os
import sys
import time
import sqlite3
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOLD_DB = os.path.join(BASE_DIR, "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
BATCH_SIZE = 5000
THROTTLE = 3.0

sys.path.insert(0, BASE_DIR)
from rfc_helpers import get_connection

# ── Field definitions ──

# FEBEP: key = KUKEY + ESNUM (already in table)
FEBEP_KEYS = ["KUKEY", "ESNUM"]
FEBEP_ENRICH = [
    "VGEXT",   # External transaction code (from bank)
    "VGINT",   # Internal posting rule applied
    "GSBER",   # Business area determined
    "ZUONR",   # Assignment (search string target)
    "INTAG",   # Interpretation algorithm used
    "XBLNR",   # Reference document number
    "SGTXT",   # Item text
    "VGDEF",   # Default posting rule
    "KFMOD",   # Account modification key
    "KOSTL",   # Cost center
    "PRCTR",   # Profit center
    "KWAER",   # Currency key (statement)
    "FWAER",   # Currency key (foreign)
    "FWBTR",   # Amount in foreign currency
    "VGMAN",   # Manual posting flag
    "KOESSION",# Account number (clearing acct)
    "RWBTR",   # Amount in document currency
    "HESSION", # House bank ID
    "HKTID",   # Account ID at house bank
]

# FEBKO: key = KUKEY (already in table)
FEBKO_KEYS = ["KUKEY"]
FEBKO_ENRICH = [
    "BUKRS",   # Company code
    "HESSION", # House bank ID
    "HKTID",   # Account ID
    "EFART",   # Statement format (XRT940/XRT940X)
    "BANKL",   # Bank number
    "BANKN",   # Bank account number
    "WAESSION",# Currency
    "STESSION",# Statement number
    "SAESSION",# Starting balance
    "SEESSION",# Ending balance
    "SFESSION",# Final balance
]

# FEBRE: fresh extraction (all fields probed from DD03L)
# Will be probed at runtime

# BSAS: key = BUKRS + BELNR + GJAHR + BUZEI (already in table, enrich AUGBL+AUGDT)
BSAS_KEYS = ["BUKRS", "BELNR", "GJAHR", "BUZEI"]
BSAS_ENRICH = ["AUGBL", "AUGDT"]

# Config tables: fresh extraction (small)
CONFIG_TABLES = ["T012K", "T028A", "T028E", "TCURR", "TCURF"]


def probe_dd03l(conn, table):
    """Get all non-MANDT fields for a table from DD03L."""
    from pyrfc import RFCError
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD03L", DELIMITER="|",
                           ROWCOUNT=200, ROWSKIPS=0,
                           OPTIONS=[{"TEXT": f"TABNAME = '{table}' AND FIELDNAME <> '.INCLUDE'"}],
                           FIELDS=[{"FIELDNAME": "FIELDNAME"}, {"FIELDNAME": "DATATYPE"},
                                   {"FIELDNAME": "LENG"}, {"FIELDNAME": "POSITION"}])
        raw = result.get("DATA", [])
        hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
        rows = []
        for row in raw:
            parts = row["WA"].split("|")
            d = {h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)}
            rows.append(d)
        rows.sort(key=lambda r: int(r.get("POSITION", "0") or "0"))
        return [r["FIELDNAME"] for r in rows if r["FIELDNAME"] != "MANDT"]
    except Exception as e:
        print(f"    [WARN] DD03L probe failed for {table}: {e}")
        return []


def fetch_page_offset(conn, table, fields, where_opts, batch_size, offset):
    """Fetch one page using offset-based field parsing (more reliable)."""
    from pyrfc import RFCError
    rfc_fields = [{"FIELDNAME": f} for f in fields]
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table,
                           FIELDS=rfc_fields, OPTIONS=where_opts,
                           ROWCOUNT=batch_size, ROWSKIPS=offset)
    except RFCError as e:
        err = str(e)
        if "TABLE_WITHOUT_DATA" in err:
            return None
        if "DATA_BUFFER_EXCEEDED" in err or "SAPSQL_DATA_LOSS" in err:
            return "BUFFER_EXCEEDED"
        raise

    if not result.get("DATA"):
        return None

    finfo = {f["FIELDNAME"]: (int(f["OFFSET"]), int(f["LENGTH"])) for f in result["FIELDS"]}
    rows = []
    for row in result["DATA"]:
        wa = row["WA"]
        vals = {}
        for f in fields:
            if f in finfo:
                o, l = finfo[f]
                vals[f] = wa[o:o+l].strip()
            else:
                vals[f] = ""
        rows.append(vals)
    return rows


def fetch_page_delim(conn, table, fields, where_opts, batch_size, offset):
    """Fetch one page using delimiter-based parsing."""
    from pyrfc import RFCError
    rfc_fields = [{"FIELDNAME": f} for f in fields]
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                           FIELDS=rfc_fields, OPTIONS=where_opts,
                           ROWCOUNT=batch_size, ROWSKIPS=offset)
    except RFCError as e:
        err = str(e)
        if "TABLE_WITHOUT_DATA" in err:
            return None
        if "DATA_BUFFER_EXCEEDED" in err or "SAPSQL_DATA_LOSS" in err:
            return "BUFFER_EXCEEDED"
        if "NOT_AUTHORIZED" in err:
            return "NOT_AUTHORIZED"
        raise

    if not result.get("DATA"):
        return None

    hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
    rows = []
    for row in result["DATA"]:
        parts = row["WA"].split("|")
        rows.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)})
    return rows


def enrich_table(conn_sap, db, sqlite_table, sap_table, key_fields, enrich_fields,
                 where_clause="", pass_label="", batch_size=BATCH_SIZE):
    """Enrich existing SQLite table with new fields from SAP.
    Uses ALTER TABLE + UPDATE by key. Splits enrich fields into passes if buffer exceeded.
    """
    # Step 1: Ensure columns exist
    existing_cols = {r[1] for r in db.execute(f'PRAGMA table_info("{sqlite_table}")').fetchall()}
    added = 0
    for col in enrich_fields:
        if col not in existing_cols:
            db.execute(f'ALTER TABLE "{sqlite_table}" ADD COLUMN "{col}" TEXT DEFAULT \'\'')
            added += 1
    if added:
        db.commit()
        print(f"    Added {added} columns to {sqlite_table}")

    # Step 2: Check how many already enriched
    total = db.execute(f'SELECT COUNT(*) FROM "{sqlite_table}"').fetchone()[0]
    if total == 0:
        print(f"    {pass_label}: 0 rows in SQLite, nothing to enrich")
        return 0

    check_field = enrich_fields[0]
    already = db.execute(
        f'SELECT COUNT(*) FROM "{sqlite_table}" WHERE "{check_field}" != \'\' AND "{check_field}" IS NOT NULL',
    ).fetchone()[0]
    if already > total * 0.9:
        print(f"    {pass_label}: {already}/{total} already enriched, skip")
        return already

    # Step 3: Determine field passes (buffer limit)
    # Try all enrich fields first, fall back to splitting
    all_fetch = key_fields + enrich_fields
    where_opts = [{"TEXT": where_clause}] if where_clause else []

    test = fetch_page_offset(conn_sap, sap_table, all_fetch, where_opts, 1, 0)
    if test == "BUFFER_EXCEEDED":
        # Split enrich fields into passes of 4
        passes = []
        for i in range(0, len(enrich_fields), 4):
            passes.append(enrich_fields[i:i+4])
        print(f"    {pass_label}: Buffer exceeded, splitting into {len(passes)} passes")
    elif test is None:
        print(f"    {pass_label}: No data in SAP for this WHERE clause")
        return 0
    else:
        passes = [enrich_fields]  # All fields fit in one pass

    # Step 4: Run each pass
    total_updated = 0
    for pi, pass_fields in enumerate(passes):
        fetch_fields = key_fields + pass_fields
        pname = f"{pass_label} P{pi+1}/{len(passes)}" if len(passes) > 1 else pass_label

        # Check if this pass already done
        pcheck = pass_fields[0]
        palready = db.execute(
            f'SELECT COUNT(*) FROM "{sqlite_table}" WHERE "{pcheck}" != \'\' AND "{pcheck}" IS NOT NULL',
        ).fetchone()[0]
        if palready > total * 0.9:
            print(f"    {pname}: {palready}/{total} already done, skip")
            continue

        print(f"    {pname}: enriching {len(pass_fields)} fields ({', '.join(pass_fields)})", end="", flush=True)
        t0 = time.time()
        offset = 0
        pass_updated = 0
        batch_num = 0

        while True:
            rows = fetch_page_offset(conn_sap, sap_table, fetch_fields, where_opts, batch_size, offset)
            if rows is None or rows == "BUFFER_EXCEEDED":
                if rows == "BUFFER_EXCEEDED":
                    print(f" [BUFFER ERROR at {len(fetch_fields)} fields]")
                break

            for row in rows:
                set_clause = ", ".join(f'"{f}" = ?' for f in pass_fields)
                where_keys = " AND ".join(f'"{f}" = ?' for f in key_fields)
                params = [row.get(f, "") for f in pass_fields] + [row.get(f, "") for f in key_fields]
                db.execute(f'UPDATE "{sqlite_table}" SET {set_clause} WHERE {where_keys}', params)

            pass_updated += len(rows)
            batch_num += 1

            if batch_num % 10 == 0:
                db.commit()
                print(f" [{pass_updated}]", end="", flush=True)

            if len(rows) < batch_size:
                break
            offset += batch_size
            time.sleep(THROTTLE)

        db.commit()
        elapsed = time.time() - t0
        print(f" -> {pass_updated} rows ({elapsed:.1f}s)")
        total_updated += pass_updated

    return total_updated


def extract_fresh(conn_sap, db, sap_table, sqlite_table, fields, where_clause="",
                  max_rows=500000, label=""):
    """Fresh extraction of a table (drop and recreate). Auto field-split on buffer exceeded."""
    where_opts = [{"TEXT": where_clause}] if where_clause else []
    print(f"    {label}: extracting {len(fields)} fields...", end="", flush=True)
    t0 = time.time()

    # Try full field list
    all_rows = []
    offset = 0

    while True:
        rows = fetch_page_delim(conn_sap, sap_table, fields, where_opts, BATCH_SIZE, offset)

        if rows == "BUFFER_EXCEEDED":
            # Need to split fields
            print(f" [SPLIT needed]")
            all_rows = _extract_split(conn_sap, sap_table, fields, where_opts, max_rows, label)
            break
        elif rows == "NOT_AUTHORIZED":
            print(f" [NOT AUTHORIZED]")
            return 0
        elif rows is None:
            break
        else:
            all_rows.extend(rows)
            if len(rows) < BATCH_SIZE:
                break
            offset += BATCH_SIZE
            if offset % 20000 == 0:
                print(f" [{offset}]", end="", flush=True)
            time.sleep(THROTTLE)

    if not all_rows:
        print(f" -> 0 rows")
        return 0

    # Load to SQLite
    actual_fields = list(all_rows[0].keys())
    cols_def = ", ".join(f'"{f}" TEXT' for f in actual_fields)
    db.execute(f'DROP TABLE IF EXISTS "{sqlite_table}"')
    db.execute(f'CREATE TABLE "{sqlite_table}" ({cols_def})')
    placeholders = ", ".join(["?"] * len(actual_fields))
    cols = ", ".join(f'"{f}"' for f in actual_fields)
    db.executemany(
        f'INSERT INTO "{sqlite_table}" ({cols}) VALUES ({placeholders})',
        [[r.get(f, "") for f in actual_fields] for r in all_rows]
    )
    db.commit()

    elapsed = time.time() - t0
    print(f" -> {len(all_rows):,} rows, {len(actual_fields)} fields ({elapsed:.1f}s)")
    return len(all_rows)


def _extract_split(conn_sap, sap_table, fields, where_opts, max_rows, label):
    """Extract with field splitting for wide tables."""
    # Find working chunk size
    chunk_size = 6
    while chunk_size >= 2:
        test = fetch_page_delim(conn_sap, sap_table, fields[:chunk_size], where_opts, 1, 0)
        if test not in ("BUFFER_EXCEEDED", "NOT_AUTHORIZED", None):
            break
        chunk_size -= 1

    if chunk_size < 2:
        print(f"    {label}: even 2 fields fail, giving up")
        return []

    print(f"    {label}: splitting into chunks of {chunk_size}")
    chunks = [fields[i:i+chunk_size] for i in range(0, len(fields), chunk_size)]

    all_rows = []
    offset = 0

    while True:
        # Read first chunk to get row count
        page_rows = fetch_page_delim(conn_sap, sap_table, chunks[0], where_opts, BATCH_SIZE, offset)
        if page_rows is None or isinstance(page_rows, str):
            break

        # Read remaining chunks at same offset
        for ci in range(1, len(chunks)):
            chunk_rows = fetch_page_delim(conn_sap, sap_table, chunks[ci], where_opts, BATCH_SIZE, offset)
            if chunk_rows and not isinstance(chunk_rows, str):
                for i, row in enumerate(chunk_rows):
                    if i < len(page_rows):
                        page_rows[i].update(row)

        all_rows.extend(page_rows)

        if len(page_rows) < BATCH_SIZE:
            break
        offset += BATCH_SIZE
        if offset % 20000 == 0:
            print(f"    [{offset}]", end="", flush=True)
        time.sleep(THROTTLE)

    return all_rows


# ── Task functions ──

def task_febep(conn_sap, db, dry_run=False):
    """H22: Re-extract FEBEP with all key fields (drop+recreate approach).
    The enrichment approach is too slow because FEBEP has no efficient WHERE clause
    for matching pre-existing rows. Fresh extraction with year filter is faster.
    """
    print("\n  === TASK 1: FEBEP Full Fields Re-extraction ===")

    # Validate fields exist in DD03L
    dd_fields = probe_dd03l(conn_sap, "FEBEP")
    if not dd_fields:
        print("    DD03L probe failed")
        return

    # Keep existing 8 fields + add enrichment fields
    existing = ["KUKEY", "ESNUM", "ESTAT", "BELNR", "GJAHR", "BUDAT", "VALUT", "KWBTR"]
    enrich = [f for f in FEBEP_ENRICH if f in dd_fields]
    # Add a few critical bonus fields only
    bonus = ["BUTXT", "VGSAP", "AVKON", "AVKOA"]
    bonus_valid = [f for f in bonus if f in dd_fields and f not in existing and f not in enrich]

    all_fields = existing + enrich + bonus_valid
    # Remove duplicates preserving order
    seen = set()
    all_fields = [f for f in all_fields if not (f in seen or seen.add(f))]

    invalid = [f for f in FEBEP_ENRICH if f not in dd_fields]
    if invalid:
        print(f"    [WARN] Fields not in DD03L: {', '.join(invalid)}")
    print(f"    Will extract: {len(all_fields)} fields ({len(existing)} base + {len(enrich)} enrich + {len(bonus_valid)} bonus)")

    if dry_run:
        print(f"    DRY RUN: would extract {len(all_fields)} fields")
        return

    # Extract month by month (avg 8K/month, manageable)
    all_rows = []
    for year in ["2024", "2025", "2026"]:
        for month in range(1, 13):
            budat_start = f"{year}{month:02d}01"
            budat_end = f"{year}{month:02d}31"
            where = f"BUDAT >= '{budat_start}' AND BUDAT <= '{budat_end}'"

            rows = _extract_with_split(conn_sap, "FEBEP", all_fields, where, f"FEBEP {year}-{month:02d}")
            if rows:
                all_rows.extend(rows)
                print(f"    {year}-{month:02d}: {len(rows):,} rows (total: {len(all_rows):,})")
            time.sleep(1)

            # Stop if we're in future months
            if year == "2026" and month >= 4:
                break

    if not all_rows:
        print("    No data extracted!")
        return

    # Load to SQLite (replace existing table)
    actual_fields = list(all_rows[0].keys())
    cols_def = ", ".join(f'"{f}" TEXT' for f in actual_fields)
    db.execute('DROP TABLE IF EXISTS "FEBEP_2024_2026"')
    db.execute(f'CREATE TABLE "FEBEP_2024_2026" ({cols_def})')
    placeholders = ", ".join(["?"] * len(actual_fields))
    cols = ", ".join(f'"{f}"' for f in actual_fields)
    db.executemany(
        f'INSERT INTO "FEBEP_2024_2026" ({cols}) VALUES ({placeholders})',
        [[r.get(f, "") for f in actual_fields] for r in all_rows]
    )
    db.commit()
    print(f"  FEBEP done: {len(all_rows):,} rows, {len(actual_fields)} fields loaded")


def _extract_with_split(conn_sap, table, fields, where, label):
    """Extract with automatic field splitting. Returns list of dicts."""
    where_opts = [{"TEXT": where}] if where else []

    # Try full field list
    rows = fetch_page_delim(conn_sap, table, fields, where_opts, BATCH_SIZE, 0)
    if rows == "BUFFER_EXCEEDED":
        # Split into chunks
        chunk_size = 6
        while chunk_size >= 2:
            test = fetch_page_delim(conn_sap, table, fields[:chunk_size], where_opts, 1, 0)
            if test not in ("BUFFER_EXCEEDED", "NOT_AUTHORIZED", None):
                break
            chunk_size -= 1
        if chunk_size < 2:
            return []

        chunks = [fields[i:i+chunk_size] for i in range(0, len(fields), chunk_size)]
        all_rows = []
        offset = 0
        while True:
            page = fetch_page_delim(conn_sap, table, chunks[0], where_opts, BATCH_SIZE, offset)
            if page is None or isinstance(page, str):
                break
            for ci in range(1, len(chunks)):
                extra = fetch_page_delim(conn_sap, table, chunks[ci], where_opts, BATCH_SIZE, offset)
                if extra and not isinstance(extra, str):
                    for i, row in enumerate(extra):
                        if i < len(page):
                            page[i].update(row)
            all_rows.extend(page)
            if len(page) < BATCH_SIZE:
                break
            offset += BATCH_SIZE
            time.sleep(THROTTLE)
        return all_rows

    elif rows == "NOT_AUTHORIZED" or rows is None:
        return []
    else:
        # Full field list worked, paginate
        all_rows = list(rows)
        offset = len(rows)
        while len(rows) >= BATCH_SIZE:
            time.sleep(THROTTLE)
            rows = fetch_page_delim(conn_sap, table, fields, where_opts, BATCH_SIZE, offset)
            if rows is None or isinstance(rows, str):
                break
            all_rows.extend(rows)
            offset += len(rows)
        return all_rows


def task_febko(conn_sap, db, dry_run=False):
    """H23: Re-extract FEBKO with all key fields (drop+recreate).
    FEBKO has AZIDT (statement date) for year filtering.
    """
    print("\n  === TASK 2: FEBKO Full Fields Re-extraction ===")

    dd_fields = probe_dd03l(conn_sap, "FEBKO")
    if not dd_fields:
        print("    DD03L probe failed")
        return

    # Keep existing + add enrichment fields
    existing = ["ANWND", "ABSND", "AZIDT", "EMKEY", "KUKEY", "ASTAT", "DSTAT", "VB1OK"]
    enrich = [f for f in FEBKO_ENRICH if f in dd_fields]
    bonus = ["ANESSION", "EESSION", "TESSION", "VESSION"]  # statement totals
    bonus_valid = [f for f in bonus if f in dd_fields and f not in existing and f not in enrich]

    all_fields = existing + enrich + bonus_valid
    seen = set()
    all_fields = [f for f in all_fields if not (f in seen or seen.add(f))]

    invalid = [f for f in FEBKO_ENRICH if f not in dd_fields]
    if invalid:
        print(f"    [WARN] Fields not in DD03L: {', '.join(invalid)}")
    print(f"    Will extract: {len(all_fields)} fields")

    if dry_run:
        print(f"    DRY RUN: would extract {len(all_fields)} fields")
        return

    # FEBKO is 85K rows — extract by year using AZIDT (statement date)
    all_rows = []
    for year in ["2024", "2025", "2026"]:
        where = f"AZIDT >= '{year}0101' AND AZIDT <= '{year}1231'"
        rows = _extract_with_split(conn_sap, "FEBKO", all_fields, where, f"FEBKO {year}")
        if rows:
            all_rows.extend(rows)
            print(f"    {year}: {len(rows):,} rows")
        time.sleep(1)

    if not all_rows:
        print("    No data extracted!")
        return

    actual_fields = list(all_rows[0].keys())
    cols_def = ", ".join(f'"{f}" TEXT' for f in actual_fields)
    db.execute('DROP TABLE IF EXISTS "FEBKO_2024_2026"')
    db.execute(f'CREATE TABLE "FEBKO_2024_2026" ({cols_def})')
    placeholders = ", ".join(["?"] * len(actual_fields))
    cols = ", ".join(f'"{f}"' for f in actual_fields)
    db.executemany(
        f'INSERT INTO "FEBKO_2024_2026" ({cols}) VALUES ({placeholders})',
        [[r.get(f, "") for f in actual_fields] for r in all_rows]
    )
    db.commit()
    print(f"  FEBKO done: {len(all_rows):,} rows, {len(actual_fields)} fields loaded")


def task_febre(conn_sap, db, dry_run=False):
    """H24: Extract FEBRE (Tag 86 note-to-payee text)."""
    print("\n  === TASK 3: FEBRE Extraction (Tag 86 Text) ===")

    dd_fields = probe_dd03l(conn_sap, "FEBRE")
    if not dd_fields:
        print("    FEBRE not found in DD03L or not authorized")
        return

    print(f"    DD03L: {len(dd_fields)} fields: {', '.join(dd_fields[:10])}...")

    if dry_run:
        print(f"    DRY RUN: would extract {len(dd_fields)} fields")
        return

    # Extract with date filter (2024-2026)
    # FEBRE may not have date field directly — linked via KUKEY to FEBKO
    # Extract all rows (should be manageable)
    extracted = extract_fresh(conn_sap, db, "FEBRE", "FEBRE", dd_fields,
                              label="FEBRE")
    print(f"  FEBRE done: {extracted} rows")


def task_bsas_augbl(conn_sap, db, dry_run=False):
    """H20: Re-enrich BSAS AUGBL for bank GL accounts."""
    print("\n  === TASK 4: BSAS AUGBL Re-enrichment (Bank Items) ===")

    # Count bank items
    bank_total = db.execute(
        "SELECT COUNT(*) FROM BSAS WHERE HKONT LIKE '0001%'"
    ).fetchone()[0]
    print(f"    Bank items in BSAS (HKONT LIKE '0001%'): {bank_total:,}")

    # Check current AUGBL status
    augbl_filled = db.execute(
        "SELECT COUNT(*) FROM BSAS WHERE HKONT LIKE '0001%' AND AUGBL != '' AND AUGBL IS NOT NULL"
    ).fetchone()[0]
    print(f"    Already have AUGBL: {augbl_filled:,}")

    if augbl_filled > bank_total * 0.9:
        print(f"    >90% done, skip")
        return

    if dry_run:
        print(f"    DRY RUN: would re-enrich {bank_total - augbl_filled} bank items")
        return

    # Enrich year by year for bank GL accounts
    for year in ["2024", "2025", "2026"]:
        year_count = db.execute(
            "SELECT COUNT(*) FROM BSAS WHERE HKONT LIKE '0001%' AND GJAHR = ?", (year,)
        ).fetchone()[0]
        if year_count == 0:
            continue

        year_done = db.execute(
            "SELECT COUNT(*) FROM BSAS WHERE HKONT LIKE '0001%' AND GJAHR = ? AND AUGBL != '' AND AUGBL IS NOT NULL",
            (year,)
        ).fetchone()[0]
        if year_done > year_count * 0.9:
            print(f"    Year {year}: {year_done}/{year_count} done, skip")
            continue

        print(f"    Year {year}: {year_count} bank items", end="", flush=True)
        t0 = time.time()

        # Fetch from SAP: BSAS with HKONT filter + year
        where = f"GJAHR = '{year}' AND HKONT LIKE '0001%'"
        offset = 0
        updated = 0

        while True:
            rows = fetch_page_offset(conn_sap, "BSAS",
                                     BSAS_KEYS + BSAS_ENRICH,
                                     [{"TEXT": where}], BATCH_SIZE, offset)
            if rows is None or isinstance(rows, str):
                break

            for row in rows:
                db.execute(
                    'UPDATE BSAS SET AUGBL = ?, AUGDT = ? WHERE BUKRS = ? AND BELNR = ? AND GJAHR = ? AND BUZEI = ?',
                    (row.get("AUGBL", ""), row.get("AUGDT", ""),
                     row.get("BUKRS", ""), row.get("BELNR", ""), row.get("GJAHR", ""), row.get("BUZEI", ""))
                )

            updated += len(rows)
            if len(rows) < BATCH_SIZE:
                break
            offset += BATCH_SIZE
            time.sleep(THROTTLE)

        db.commit()
        elapsed = time.time() - t0
        print(f" -> {updated} rows ({elapsed:.1f}s)")

    print(f"  BSAS AUGBL done")


def task_config_tables(conn_sap, db, dry_run=False):
    """H25+H26+H27: Extract config tables (T012K, T028A, T028E, TCURR, TCURF)."""
    print("\n  === TASK 5: Config & Exchange Rate Tables ===")

    for tbl in CONFIG_TABLES:
        dd_fields = probe_dd03l(conn_sap, tbl)
        if not dd_fields:
            print(f"    {tbl}: not found in DD03L")
            continue

        print(f"    {tbl}: {len(dd_fields)} fields")

        if dry_run:
            print(f"      DRY RUN: would extract")
            continue

        # For TCURR: filter to recent rates (2024+)
        where = ""
        if tbl == "TCURR":
            where = "GDATU >= '20240101'"

        extracted = extract_fresh(conn_sap, db, tbl, tbl, dd_fields,
                                  where_clause=where, label=tbl)
        time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description="Session #030: Bank Statement Full Extraction")
    parser.add_argument("--task", choices=["febep", "febko", "febre", "bsas", "config", "all"],
                        default="all")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("\n  " + "=" * 60)
    print("  Session #030: Bank Statement & Reconciliation Full Extraction")
    print("  " + "=" * 60)

    db = sqlite3.connect(GOLD_DB)
    db.execute("PRAGMA journal_mode=WAL")

    if args.dry_run:
        print("  *** DRY RUN MODE ***\n")

    conn_sap = get_connection("P01") if not args.dry_run else None
    if conn_sap:
        print("  Connected to P01 (SNC/SSO).\n")

    t0 = time.time()

    tasks = {
        "febep": task_febep,
        "febko": task_febko,
        "febre": task_febre,
        "bsas": task_bsas_augbl,
        "config": task_config_tables,
    }

    if args.task == "all":
        for name, func in tasks.items():
            try:
                func(conn_sap, db, args.dry_run)
            except Exception as e:
                print(f"\n  [ERROR] Task {name} failed: {e}")
                import traceback
                traceback.print_exc()
    else:
        tasks[args.task](conn_sap, db, args.dry_run)

    if conn_sap:
        conn_sap.close()

    elapsed = (time.time() - t0) / 60
    print(f"\n  {'=' * 60}")
    print(f"  DONE. Total time: {elapsed:.1f} min")
    print(f"  Gold DB: {GOLD_DB}")
    print(f"  {'=' * 60}\n")

    db.close()


if __name__ == "__main__":
    main()
