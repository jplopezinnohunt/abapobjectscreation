"""
load_payment_process_full.py
=============================
Load the JSON checkpoints produced by extract_payment_process_full.py into
the Gold DB as *new* tables (suffix _FULL) so the legacy sparse REGUH is
not overwritten until validation passes.

Tables written:
  REGUH_FULL               — replaces sparse REGUH (8 cols -> 37 cols)
  T042_FULL, T042E_FULL, T042Z_FULL, T042I_FULL, T042B_FULL
  BNK_BATCH_HEADER_FULL    — richer schema than current BNK_BATCH_HEADER
  BNK_BATCH_STATUS         — new table (not in Gold DB before)
  PAYR_FULL
  REGUP_FULL               — if extracted

After loading, run validate_bcm_routing.py to test the causal hypothesis:
  REGUH.RZAWE -> T042Z flags -> BCM batch existence

Usage:
    python load_payment_process_full.py
    python load_payment_process_full.py --table REGUH
    python load_payment_process_full.py --replace-legacy  # atomic swap
"""

import os
import sys
import json
import sqlite3
import glob
import argparse

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPTS_DIR, "..", "extracted_data", "payment_process_full")
DB_PATH = os.path.join(SCRIPTS_DIR, "..", "sqlite", "p01_gold_master_data.db")


def load_json_files(pattern):
    rows = []
    for fn in sorted(glob.glob(pattern)):
        with open(fn, "r", encoding="utf-8") as f:
            rows.extend(json.load(f))
    return rows


def create_table_from_rows(conn, table, rows):
    if not rows:
        print(f"  [SKIP] {table}: no rows")
        return 0
    cols = sorted(set().union(*(r.keys() for r in rows)))
    conn.execute(f"DROP TABLE IF EXISTS {table}")
    ddl = ", ".join(f'"{c}" TEXT' for c in cols)
    conn.execute(f"CREATE TABLE {table} ({ddl})")
    placeholders = ", ".join("?" * len(cols))
    col_list = ", ".join(f'"{c}"' for c in cols)
    insert_sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    batch = []
    for r in rows:
        batch.append(tuple(r.get(c, "") for c in cols))
        if len(batch) >= 5000:
            conn.executemany(insert_sql, batch)
            batch = []
    if batch:
        conn.executemany(insert_sql, batch)
    conn.commit()
    return len(rows)


def load_partitioned(conn, table, target_name):
    """Load monthly JSON files from DATA_DIR/<table>/*.json"""
    pattern = os.path.join(DATA_DIR, table, f"{table}_*.json")
    rows = load_json_files(pattern)
    n = create_table_from_rows(conn, target_name, rows)
    print(f"  {target_name}: {n} rows")
    return n


def load_full(conn, table, target_name):
    """Load single config snapshot from DATA_DIR/<table>_full.json"""
    fn = os.path.join(DATA_DIR, f"{table}_full.json")
    if not os.path.exists(fn):
        print(f"  [SKIP] {target_name}: {fn} not found")
        return 0
    with open(fn, "r", encoding="utf-8") as f:
        rows = json.load(f)
    n = create_table_from_rows(conn, target_name, rows)
    print(f"  {target_name}: {n} rows")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", help="Only load this table")
    ap.add_argument("--replace-legacy", action="store_true",
                    help="After load, DROP legacy REGUH/BNK_BATCH_HEADER and rename _FULL to canonical name")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    tgt = args.table.upper() if args.table else None

    plan = [
        # (src_table, mode, target_name)
        ("REGUH",            "partitioned", "REGUH_FULL"),
        ("T042",             "full",        "T042_FULL"),
        ("T042E",            "full",        "T042E_FULL"),
        ("T042Z",            "full",        "T042Z_FULL"),
        ("T042I",            "full",        "T042I_FULL"),
        ("T042B",            "full",        "T042B_FULL"),
        ("BNK_BATCH_HEADER", "partitioned", "BNK_BATCH_HEADER_FULL"),
        ("BNK_BATCH_STATUS", "full",        "BNK_BATCH_STATUS"),
        ("PAYR",             "partitioned", "PAYR_FULL"),
        ("REGUP",            "partitioned", "REGUP_FULL"),
    ]

    for src, mode, target in plan:
        if tgt and tgt not in (src, target):
            continue
        print(f"\n-- {target} (source: {src}, mode: {mode}) --")
        if mode == "partitioned":
            load_partitioned(conn, src, target)
        else:
            load_full(conn, src, target)

    if args.replace_legacy:
        print("\n-- Atomic replace of legacy tables --")
        for legacy, fresh in [
            ("REGUH", "REGUH_FULL"),
            ("BNK_BATCH_HEADER", "BNK_BATCH_HEADER_FULL"),
            ("T042Z", "T042Z_FULL"),
            ("T042E", "T042E_FULL"),
            ("T042", "T042_FULL"),
        ]:
            # Check fresh has rows first
            n = conn.execute(f"SELECT COUNT(*) FROM {fresh}").fetchone()[0]
            if n == 0:
                print(f"  [ABORT] {fresh} is empty, not replacing {legacy}")
                continue
            conn.execute(f"DROP TABLE IF EXISTS {legacy}_OLD")
            conn.execute(f"ALTER TABLE {legacy} RENAME TO {legacy}_OLD")
            conn.execute(f"ALTER TABLE {fresh} RENAME TO {legacy}")
            print(f"  {legacy} replaced ({fresh} -> {legacy}, old kept as {legacy}_OLD)")
        conn.commit()

    conn.close()
    print("\n[DONE]")


if __name__ == "__main__":
    main()
