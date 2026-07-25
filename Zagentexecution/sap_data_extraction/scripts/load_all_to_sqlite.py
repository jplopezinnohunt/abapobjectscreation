"""
load_all_to_sqlite.py
======================
Loads ALL extracted SAP data into p01_gold_master_data.db SQLite.

Tables loaded:
  tadir_enrichment   -- 29,100 ABAP objects with package + description (from tadir_enrichment_checkpoint.json)
  volume_anchors     -- FMIFIIT/FMBDT/FMAVCT row counts by year/fund area (from sap_p01_volume_anchors.json)
  cts_transports     -- All CTS transport objects across all years 2017-2026 (from cts_batch_XXXX.json)
  cts_objects        -- E071 objects within each transport

Usage:
    python load_all_to_sqlite.py              # Load all
    python load_all_to_sqlite.py --tadir      # Only TADIR enrichment
    python load_all_to_sqlite.py --cts        # Only CTS transports
    python load_all_to_sqlite.py --anchors    # Only volume anchors
    python load_all_to_sqlite.py --check      # Show current row counts only
"""

import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(SCRIPTS_DIR)    # sap_data_extraction/
ROOT_DIR    = os.path.dirname(BASE_DIR)        # Zagentexecution/

DB_PATH     = os.path.join(BASE_DIR, "sqlite", "p01_gold_master_data.db")
MCP_DIR     = os.path.join(ROOT_DIR, "mcp-backend-server-python")
REPORTS_DIR = os.path.join(BASE_DIR, "reports", "cts_data")

TADIR_ENRICHMENT_JSON = os.path.join(MCP_DIR, "tadir_enrichment_checkpoint.json")
VOLUME_ANCHORS_JSON   = os.path.join(ROOT_DIR, "..", "knowledge", "domains", "PSM", "sap_p01_volume_anchors.json")
PS_ANCHORS_JSON       = os.path.join(ROOT_DIR, "..", "knowledge", "domains", "PSM", "sap_p01_ps_anchors.json")

CTS_YEAR_FILES = [
    os.path.join(REPORTS_DIR, f"cts_batch_{y}.json")
    for y in range(2017, 2027)
]

BATCH_SIZE = 5000


def connect():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA cache_size=-32000")  # 32MB cache
    return db


def show_counts(db):
    tables = ["tadir_enrichment", "volume_anchors", "cts_transports", "cts_objects"]
    print("\n  Current row counts:")
    for t in tables:
        try:
            cnt = db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            print(f"    {t:<25} {cnt:>10,}")
        except Exception:
            print(f"    {t:<25}  (not loaded)")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# 1. TADIR ENRICHMENT
# ─────────────────────────────────────────────────────────────────────────────

def load_tadir_enrichment(db):
    print("\n  [TADIR] Loading tadir_enrichment_checkpoint.json...")
    if not os.path.exists(TADIR_ENRICHMENT_JSON):
        print(f"  [TADIR] File not found: {TADIR_ENRICHMENT_JSON}")
        return

    with open(TADIR_ENRICHMENT_JSON, encoding="utf-8") as f:
        data = json.load(f)

    enrichment = data.get("enrichment", {})
    completed_types = data.get("completed_types", [])

    print(f"  [TADIR] {len(enrichment):,} objects, {len(completed_types)} completed types")

    db.execute("DROP TABLE IF EXISTS tadir_enrichment")
    db.execute("""
        CREATE TABLE tadir_enrichment (
            obj_type   TEXT,
            obj_name   TEXT,
            devclass   TEXT,
            ddtext     TEXT,
            PRIMARY KEY (obj_type, obj_name)
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_tadir_devclass ON tadir_enrichment (devclass)")
    db.commit()

    rows = []
    for key, val in enrichment.items():
        # key format: "TYPE:NAME" or just the obj_name (older format)
        if ":" in key:
            obj_type, obj_name = key.split(":", 1)
        else:
            obj_type = ""
            obj_name = key

        if isinstance(val, dict):
            devclass = val.get("devclass", "")
            ddtext   = val.get("ddtext", "") or val.get("description", "")
        elif isinstance(val, str):
            devclass = val
            ddtext   = ""
        else:
            devclass = ""
            ddtext   = ""

        rows.append((obj_type, obj_name, devclass, ddtext))

        if len(rows) >= BATCH_SIZE:
            db.executemany("INSERT OR REPLACE INTO tadir_enrichment VALUES (?,?,?,?)", rows)
            db.commit()
            rows = []

    if rows:
        db.executemany("INSERT OR REPLACE INTO tadir_enrichment VALUES (?,?,?,?)", rows)
        db.commit()

    cnt = db.execute("SELECT COUNT(*) FROM tadir_enrichment").fetchone()[0]
    print(f"  [TADIR] Done. {cnt:,} rows loaded.")


# ─────────────────────────────────────────────────────────────────────────────
# 2. VOLUME ANCHORS
# ─────────────────────────────────────────────────────────────────────────────

def load_volume_anchors(db):
    print("\n  [ANCHORS] Loading volume anchors (FMIFIIT/FMBDT/FMAVCT by year/fund_area)...")

    db.execute("DROP TABLE IF EXISTS volume_anchors")
    db.execute("""
        CREATE TABLE volume_anchors (
            table_name TEXT,
            year       TEXT,
            fund_area  TEXT,
            row_count  INTEGER,
            PRIMARY KEY (table_name, year, fund_area)
        )
    """)
    db.commit()

    rows = []
    for json_path in [VOLUME_ANCHORS_JSON, PS_ANCHORS_JSON]:
        json_path = os.path.normpath(json_path)
        if not os.path.exists(json_path):
            print(f"  [ANCHORS] Not found: {json_path}")
            continue

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        src_name = os.path.basename(json_path)
        file_rows = 0
        for table_name, year_data in data.items():
            if isinstance(year_data, dict):
                # Nested format: {table: {year: {fund_area: count}}}
                for year, area_data in year_data.items():
                    if isinstance(area_data, dict):
                        for fund_area, count in area_data.items():
                            rows.append((table_name, str(year), fund_area, int(count)))
                            file_rows += 1
                    else:
                        rows.append((table_name, str(year), "_total", int(area_data)))
                        file_rows += 1
            else:
                # Flat format: {table: total_count}
                rows.append((table_name, "ALL", "_total", int(year_data)))
                file_rows += 1

        print(f"  [ANCHORS] {src_name}: {file_rows} entries")

    db.executemany("INSERT OR REPLACE INTO volume_anchors VALUES (?,?,?,?)", rows)
    db.commit()
    cnt = db.execute("SELECT COUNT(*) FROM volume_anchors").fetchone()[0]
    print(f"  [ANCHORS] Done. {cnt:,} rows loaded.")


# ─────────────────────────────────────────────────────────────────────────────
# 3. CTS TRANSPORTS
# ─────────────────────────────────────────────────────────────────────────────

def load_cts_transports(db):
    print("\n  [CTS] Loading CTS transport data (2017-2026)...")

    db.execute("DROP TABLE IF EXISTS cts_transports")
    db.execute("""
        CREATE TABLE cts_transports (
            trkorr       TEXT PRIMARY KEY,
            year         INTEGER,
            trstatus     TEXT,
            trfunction   TEXT,
            trtype       TEXT,
            deploy_level TEXT,
            as4user      TEXT,
            as4date      TEXT,
            as4text      TEXT,
            obj_count    INTEGER
        )
    """)
    db.execute("DROP TABLE IF EXISTS cts_objects")
    db.execute("""
        CREATE TABLE cts_objects (
            trkorr     TEXT,
            pgmid      TEXT,
            object     TEXT,
            obj_name   TEXT,
            change_cat TEXT,
            devclass   TEXT,
            FOREIGN KEY (trkorr) REFERENCES cts_transports(trkorr)
        )
    """)
    db.execute("CREATE INDEX idx_cts_objects_trkorr ON cts_objects(trkorr)")
    db.execute("CREATE INDEX idx_cts_objects_object ON cts_objects(object)")
    db.execute("CREATE INDEX idx_cts_transports_year ON cts_transports(year)")
    db.commit()

    t_rows = []
    o_rows = []
    total_t, total_o = 0, 0

    for json_path in CTS_YEAR_FILES:
        if not os.path.exists(json_path):
            continue

        year = int(os.path.basename(json_path).replace("cts_batch_", "").replace(".json", ""))

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        transports = data.get("transports", data if isinstance(data, list) else [])

        for tr in transports:
            trkorr = tr.get("trkorr", "")
            t_rows.append((
                trkorr,
                year,
                tr.get("status",       tr.get("trstatus", "")),
                tr.get("type_code",    tr.get("trfunction", "")),
                tr.get("type",         ""),
                tr.get("deploy_level", ""),
                tr.get("owner",        tr.get("as4user", "")),
                tr.get("date",         tr.get("as4date", "")),
                tr.get("description",  tr.get("as4text", "")),
                len(tr.get("objects", []))
            ))

            for obj in tr.get("objects", []):
                o_rows.append((
                    trkorr,
                    obj.get("pgmid", ""),
                    obj.get("obj_type", obj.get("object", "")),
                    obj.get("obj_name", ""),
                    obj.get("change_cat", ""),
                    obj.get("devclass", "")
                ))

        if len(t_rows) >= BATCH_SIZE:
            db.executemany("INSERT OR REPLACE INTO cts_transports VALUES (?,?,?,?,?,?,?,?,?,?)", t_rows)
            db.executemany("INSERT INTO cts_objects VALUES (?,?,?,?,?,?)", o_rows)
            db.commit()
            total_t += len(t_rows); total_o += len(o_rows)
            print(f"  [CTS] Year {year}: +{len(t_rows):,} transports, +{len(o_rows):,} objects (running: {total_t:,}/{total_o:,})")
            t_rows = []; o_rows = []
        else:
            print(f"  [CTS] Year {year}: {len(t_rows):,} transports queued")

    if t_rows:
        db.executemany("INSERT OR REPLACE INTO cts_transports VALUES (?,?,?,?,?,?,?,?,?,?)", t_rows)
        db.executemany("INSERT INTO cts_objects VALUES (?,?,?,?,?,?)", o_rows)
        db.commit()
        total_t += len(t_rows); total_o += len(o_rows)

    cnt_t = db.execute("SELECT COUNT(*) FROM cts_transports").fetchone()[0]
    cnt_o = db.execute("SELECT COUNT(*) FROM cts_objects").fetchone()[0]
    print(f"  [CTS] Done. {cnt_t:,} transports, {cnt_o:,} objects loaded.")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Load all extracted SAP data into SQLite")
    parser.add_argument("--tadir",   action="store_true", help="Load TADIR enrichment only")
    parser.add_argument("--cts",     action="store_true", help="Load CTS transports only")
    parser.add_argument("--anchors", action="store_true", help="Load volume anchors only")
    parser.add_argument("--check",   action="store_true", help="Show row counts only")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found: {DB_PATH}")
        sys.exit(1)

    db = connect()

    print(f"\n{'='*70}")
    print(f"  LOAD ALL DATA INTO SQLITE")
    print(f"  DB: {DB_PATH}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    show_counts(db)

    if args.check:
        db.close()
        return

    run_all = not (args.tadir or args.cts or args.anchors)

    if args.tadir or run_all:
        load_tadir_enrichment(db)

    if args.anchors or run_all:
        load_volume_anchors(db)

    if args.cts or run_all:
        load_cts_transports(db)

    print(f"\n{'='*70}")
    print("  FINAL COUNTS:")
    show_counts(db)
    print(f"  DONE at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    db.close()


if __name__ == "__main__":
    main()
