"""
delta_refresh_2026.py
=====================
Delta refresh of UNESCO Gold DB for fiscal year 2026, current to 2026-05-01.

CONTEXT:
  Most 2026 transactional tables stop around 2026-03-15/16 -- 6+ weeks stale.
  This script pulls only the missing 2026 deltas. Does NOT touch 2024/2025.
  Required for INC-000005638 PS-AVC analysis (current pool depths).

PARALLEL SAFETY:
  Another agent is extracting BPGE/BPJA/BPHI/BPDJ/BPTR/COSP/COSS/EKKN/FMAVCT/
  TKA01/OPSV/T185F. Stay out of those tables. Sequential connections only
  (max 1 RFC connection from this script -- parallel agent has its own).

TABLES (10):
  1. coep              - re-extract 2026 PERIO 004,005       (DELETE+INSERT)
  2. cooi              - re-extract 2026 PERIO 001..005      (DELETE+INSERT)
  3. rpsco             - re-extract 2026 (no PERIO key)      (DELETE+INSERT)
  4. fmifiit_full      - re-extract 2026 PERIO 003,004,005   (DELETE+INSERT)
  5. bkpf              - delta WHERE GJAHR=2026 AND CPUDT > '20260316'  (INSERT)
  6. bsis,bsas,bsik,bsak,bsid,bsad - delta on each            (INSERT)
     (BSIS/BSAS have no CPUDT in Gold schema -> use BUDAT > '20260328')
  7. ekko              - delta WHERE AEDAT > '20260315'        (UPSERT EBELN)
  8. ekpo              - delta WHERE AEDAT > '20260315'        (UPSERT EBELN+EBELP)
  9. rbkp              - delta WHERE BUDAT > '20260315' AND GJAHR=2026  (INSERT)
 10. essr              - delta WHERE AEDAT > '20260315'        (ALTER+UPSERT LBLNI)
                        (Adds AEDAT column to existing 4-col schema)

USAGE:
    python delta_refresh_2026.py                # Run all 10
    python delta_refresh_2026.py --table coep   # Single table
    python delta_refresh_2026.py --dry-run      # Probe-only, no extraction
    python delta_refresh_2026.py --resume       # Skip already-fresh combos

RULES (sap_data_extraction SKILL):
  - NEVER >2 concurrent RFC connections from this process. We use 1.
  - NEVER unicode in print() -- cp1252 crashes Windows threads silently.
  - NEVER checkpoint errored periods -- skip on error so resume retries.
  - BATCH_SIZE=5000, THROTTLE=3.0, fresh connection per period.
  - Don't re-extract anything before 2024.
  - Lowercase table names in SQLite, preserve column casing.
"""

import os
import sys
import time
import sqlite3
import argparse
import json
import threading
from datetime import datetime

# rfc_helpers lives in mcp-backend-server-python
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_DIR     = os.path.abspath(os.path.join(SCRIPTS_DIR, "..", "..", "mcp-backend-server-python"))
sys.path.insert(0, MCP_DIR)
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD_DB      = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction",
                            "sqlite", "p01_gold_master_data.db")
LOG_DIR      = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "logs")
KU_FILE      = os.path.join(PROJECT_ROOT, "brain_v2", "agi", "known_unknowns.json")
STATUS_FILE  = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction",
                            "extraction_status.md")

BATCH_SIZE = 5000
THROTTLE   = 3.0
TODAY      = "20260501"

# Per-table hard timeout (Block A in particular); default 300s
DEFAULT_TABLE_TIMEOUT_SEC = 300

# Cutoff dates per task spec
CPUDT_CUTOFF = "20260316"   # bkpf, bsik, bsak, bsid, bsad
BUDAT_CUTOFF = "20260328"   # bsis, bsas (no CPUDT in Gold schema)
AEDAT_CUTOFF = "20260315"   # ekko, ekpo, essr
BUDAT_RBKP   = "20260315"   # rbkp

# ---------------------------------------------------------------------------
# FIELD LISTS (DD03L-verified) -- match Gold DB schema exactly
# ---------------------------------------------------------------------------
COEP_FIELDS = [
    "OBJNR", "GJAHR", "WRTTP", "VERSN", "KSTAR", "HRKFT",
    "TWAER", "WKGBTR", "WKFBTR", "WOGBTR", "WTGBTR",
    "KOKRS", "BELNR", "BUZEI", "PERIO", "VRGNG",
    "BUKRS", "EBELN", "EBELP",
    "GRANT_NBR", "GEBER", "FKBER", "SGTXT",
]

COOI_FIELDS = [
    "OBJNR", "GJAHR", "WRTTP", "VERSN", "SAKTO", "HRKFT",
    "TWAER", "WTGBTR", "WKGBTR", "WOGBTR",
    "REFBN", "RFPOS", "REFBT", "VRGNG",
    "LIFNR", "BUKRS", "KOKRS", "PERIO", "BUDAT", "BLDAT",
    "SGTXT", "LOEKZ",
]

RPSCO_FIELDS = [
    "OBJNR", "GJAHR", "WRTTP", "VERSN", "ACPOS", "VORGA",
    "LEDNR", "TRGKZ", "ABKAT", "GEBER", "TWAER", "PERBL", "BELTP",
    "WLP00", "WLP01", "WLP02", "WLP03", "WLP04", "WLP05", "WLP06",
    "WLP07", "WLP08", "WLP09", "WLP10", "WLP11", "WLP12",
    "WLP13", "WLP14", "WLP15", "WLP16",
    "WTP00", "WTP01", "WTP02", "WTP03", "WTP04", "WTP05", "WTP06",
    "WTP07", "WTP08", "WTP09", "WTP10", "WTP11", "WTP12",
    "WTP13", "WTP14", "WTP15", "WTP16",
]

FMIFIIT_FIELDS = [
    "FIKRS", "GJAHR", "FMBELNR", "FMBUZEI", "BTART", "RLDNR", "STUNR",
    "FONDS", "FISTL", "FIPEX", "FAREA", "WRTTP", "TWAER", "FKBTR", "TRBTR",
    "PERIO", "STATS", "VRGNG", "BUKRS", "HKONT", "PRCTR", "GRANT_NBR",
    "MEASURE", "KNBELNR", "KNGJAHR", "KNBUZEI", "SGTXT", "OBJNRZ",
]

BKPF_FIELDS = [
    "MANDT", "BUKRS", "BELNR", "GJAHR", "BLART", "BLDAT", "BUDAT", "MONAT",
    "CPUDT", "CPUTM", "USNAM", "TCODE", "BKTXT", "WAERS",
    "AWTYP", "AWKEY", "XBLNR", "GLVOR",
]

# BSIS/BSAS Gold schema (30 fields)
BSIS_FIELDS = [
    "MANDT", "BUKRS", "BELNR", "GJAHR", "BUZEI", "BUDAT", "BLDAT", "MONAT",
    "SHKZG", "WRBTR", "WAERS", "DMBTR", "DMBE2", "HKONT", "BSCHL", "GSBER",
    "KOSTL", "AUFNR", "PRCTR", "FKBER", "PS_PSP_PNR", "SGTXT", "EBELN", "EBELP",
    "MWSKZ", "AUGDT", "AUGBL", "ZFBDT", "ZTERM", "PROJK",
]
BSAS_FIELDS = BSIS_FIELDS  # same schema

# BSIK/BSAK Gold schema (30 fields, with CPUDT, with LIFNR)
BSIK_FIELDS = [
    "MANDT", "BUKRS", "BELNR", "GJAHR", "BUZEI", "BUDAT", "BLDAT", "CPUDT", "MONAT",
    "SHKZG", "WRBTR", "WAERS", "DMBTR", "DMBE2", "HKONT", "BSCHL", "GSBER",
    "KOSTL", "AUFNR", "PRCTR", "FKBER", "EBELN", "EBELP", "MWSKZ",
    "AUGDT", "AUGBL", "LIFNR", "SGTXT", "ZFBDT", "ZTERM",
]
BSAK_FIELDS = BSIK_FIELDS  # same schema

# BSID/BSAD Gold schema (16 fields, narrower)
BSID_FIELDS = [
    "MANDT", "BUKRS", "BELNR", "GJAHR", "BUZEI", "BUDAT", "BLDAT", "CPUDT", "MONAT",
    "SHKZG", "WRBTR", "WAERS", "DMBTR", "DMBE2", "HKONT", "BSCHL",
]
BSAD_FIELDS = BSID_FIELDS

EKKO_FIELDS = [
    "MANDT", "EBELN", "BUKRS", "BSART", "LOEKZ", "STATU", "AEDAT", "BEDAT",
    "EKGRP", "WAERS", "ZTERM", "LIFNR", "EKORG",
]

EKPO_FIELDS = [
    "MANDT", "EBELN", "EBELP", "LOEKZ", "STATU", "AEDAT", "TXZ01", "MATNR",
    "BUKRS", "WERKS", "MENGE", "MEINS", "NETPR", "NETWR", "BRTWR", "MWSKZ",
]

RBKP_FIELDS = [
    "MANDT", "BELNR", "GJAHR", "BLART", "BLDAT", "BUDAT", "USNAM", "TCODE",
    "CPUDT", "CPUTM", "WAERS", "RMWWR", "WMWST1", "LIFNR", "BUKRS",
    "XBLNR", "STBLG", "STJAH",
]

# ESSR Gold schema is currently 4 fields. Task says: ALTER TABLE essr ADD COLUMN AEDAT
# We extract 5 fields (4 existing + AEDAT) and refresh fields too if schema lacks AEDAT.
ESSR_FIELDS = ["LBLNI", "PACKNO", "EBELN", "EBELP", "AEDAT"]


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
class Logger:
    def __init__(self, log_path):
        self.path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self.fh = open(log_path, "a", encoding="utf-8")
        self.summary = {
            "started": datetime.now().isoformat(),
            "tables": {},
            "errors": [],
            "ku_logged": [],
        }

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = "[{}] {}".format(ts, msg)
        print(line)
        self.fh.write(line + "\n")
        self.fh.flush()

    def record(self, table, key, value):
        if table not in self.summary["tables"]:
            self.summary["tables"][table] = {}
        self.summary["tables"][table][key] = value

    def error(self, table, msg):
        self.summary["errors"].append({"table": table, "error": msg,
                                        "ts": datetime.now().isoformat()})
        self.log("ERROR [{}]: {}".format(table, msg))

    def close(self):
        self.summary["finished"] = datetime.now().isoformat()
        json_path = self.path.replace(".log", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.summary, f, indent=2, default=str)
        self.fh.close()


# ---------------------------------------------------------------------------
# SQLITE HELPERS
# ---------------------------------------------------------------------------
def get_existing_columns(db, table):
    """Return list of column names in lowercase table -- preserves declared casing."""
    cur = db.execute("PRAGMA table_info({})".format(table))
    return [row[1] for row in cur.fetchall()]


def count_rows(db, table, where=None):
    sql = "SELECT COUNT(*) FROM {}".format(table)
    if where:
        sql += " WHERE " + where
    try:
        return db.execute(sql).fetchone()[0]
    except Exception:
        return -1


def insert_rows(db, table, fields, rows):
    """Plain INSERT (no DELETE). Assumes caller did the right scoping."""
    if not rows:
        return 0
    placeholders = ", ".join(["?"] * len(fields))
    col_names = ", ".join(['"{}"'.format(f) for f in fields])
    batch = [tuple(r.get(f, "") for f in fields) for r in rows]
    db.executemany("INSERT INTO {} ({}) VALUES ({})".format(table, col_names, placeholders),
                   batch)
    db.commit()
    return len(batch)


def delete_then_insert(db, table, fields, rows, delete_where, delete_params):
    """DELETE WHERE ... then bulk INSERT."""
    db.execute("DELETE FROM {} WHERE {}".format(table, delete_where), delete_params)
    db.commit()
    return insert_rows(db, table, fields, rows)


def upsert_rows(db, table, fields, rows, key_fields):
    """DELETE rows whose key matches any new row, then INSERT all new rows."""
    if not rows:
        return 0
    # Delete matching keys
    keys_set = set()
    for r in rows:
        keys_set.add(tuple(r.get(k, "") for k in key_fields))
    if keys_set:
        placeholders = " AND ".join(['"{}" = ?'.format(k) for k in key_fields])
        cur = db.cursor()
        for keytup in keys_set:
            cur.execute("DELETE FROM {} WHERE {}".format(table, placeholders), keytup)
        db.commit()
    return insert_rows(db, table, fields, rows)


# ---------------------------------------------------------------------------
# RFC EXTRACT WRAPPER (with KU logging on hard failure)
# ---------------------------------------------------------------------------
def safe_extract(table, fields, where, log, ku_id, batch_size=BATCH_SIZE,
                 throttle=THROTTLE):
    """Returns (rows, error_str_or_None). Fresh connection per call."""
    conn = None
    try:
        conn = get_connection("P01")
    except Exception as e:
        err = "CONNECTION_FAILED: {}".format(str(e)[:200])
        log.error(table, err)
        log_ku(ku_id, table, where, err, log)
        return [], err

    try:
        log.log("  RFC: {} where={}".format(table, where))
        rows = rfc_read_paginated(conn, table, fields, where,
                                  batch_size=batch_size, throttle=throttle)
        log.log("    -> {} rows".format(len(rows)))
        return rows, None
    except Exception as e:
        err = "RFC_FAILED: {}".format(str(e)[:300])
        log.error(table, err)
        log_ku(ku_id, table, where, err, log)
        return [], err
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def log_ku(ku_id, table, where, err, log):
    """Append a known_unknown to brain_v2/agi/known_unknowns.json on hard RFC failure."""
    try:
        if os.path.exists(KU_FILE):
            with open(KU_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"known_unknowns": []}
        if not isinstance(data, dict):
            data = {"known_unknowns": []}
        kus = data.get("known_unknowns", [])
        kus.append({
            "id": ku_id,
            "table": table,
            "where": where,
            "error": err,
            "logged_at": datetime.now().isoformat(),
            "context": "delta_refresh_2026.py",
            "status": "open",
        })
        data["known_unknowns"] = kus
        os.makedirs(os.path.dirname(KU_FILE), exist_ok=True)
        with open(KU_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        log.summary["ku_logged"].append(ku_id)
        log.log("    KU logged: {}".format(ku_id))
    except Exception as e:
        log.log("    KU log failed: {}".format(e))


# ---------------------------------------------------------------------------
# TABLE STRATEGIES
# ---------------------------------------------------------------------------
def refresh_coep(db, log, dry_run=False, resume=False):
    """COEP: re-extract 2026 PERIO 004,005. DELETE+INSERT."""
    table = "coep"
    pre = count_rows(db, table, "GJAHR='2026'")
    log.record(table, "pre_2026", pre)
    log.log("[{}] pre 2026: {}".format(table, pre))
    if dry_run:
        return

    cols = get_existing_columns(db, table)
    fields = [f for f in COEP_FIELDS if f in cols]
    if len(fields) != len(COEP_FIELDS):
        log.log("  WARN: schema mismatch, using {} of {} fields".format(
            len(fields), len(COEP_FIELDS)))

    total_new = 0
    for period in ["004", "005"]:
        if resume:
            existing = count_rows(db, table,
                                   "GJAHR='2026' AND PERIO='{}'".format(period))
            if existing > 0 and period == "005":
                # P005 might be in flight; never skip on resume for P005
                pass
        where = "GJAHR = '2026' AND PERIO = '{}'".format(period)
        rows, err = safe_extract("COEP", fields, where, log,
                                  "KU-2026-DELTA-COEP-P{}".format(period))
        if err:
            log.log("  P{}: skip (rfc error)".format(period))
            continue
        n = delete_then_insert(db, table, fields, rows,
                               "GJAHR=? AND PERIO=?", ("2026", period))
        log.log("  P{}: deleted+inserted {} rows".format(period, n))
        total_new += n

    post = count_rows(db, table, "GJAHR='2026'")
    log.record(table, "post_2026", post)
    log.record(table, "delta_2026", post - pre)
    log.log("[{}] post 2026: {} (delta {:+})".format(table, post, post - pre))


def refresh_cooi(db, log, dry_run=False, resume=False):
    """COOI: re-extract 2026 PERIO 001..005. DELETE+INSERT."""
    table = "cooi"
    pre = count_rows(db, table, "GJAHR='2026'")
    log.record(table, "pre_2026", pre)
    log.log("[{}] pre 2026: {}".format(table, pre))
    if dry_run:
        return

    cols = get_existing_columns(db, table)
    fields = [f for f in COOI_FIELDS if f in cols]

    for period in ["001", "002", "003", "004", "005"]:
        where = "GJAHR = '2026' AND PERIO = '{}'".format(period)
        rows, err = safe_extract("COOI", fields, where, log,
                                  "KU-2026-DELTA-COOI-P{}".format(period))
        if err:
            log.log("  P{}: skip (rfc error)".format(period))
            continue
        n = delete_then_insert(db, table, fields, rows,
                               "GJAHR=? AND PERIO=?", ("2026", period))
        log.log("  P{}: deleted+inserted {} rows".format(period, n))

    post = count_rows(db, table, "GJAHR='2026'")
    log.record(table, "post_2026", post)
    log.record(table, "delta_2026", post - pre)
    log.log("[{}] post 2026: {} (delta {:+})".format(table, post, post - pre))


def refresh_rpsco(db, log, dry_run=False, resume=False):
    """RPSCO: re-extract 2026 (no PERIO key). DELETE+INSERT."""
    table = "rpsco"
    pre = count_rows(db, table, "GJAHR='2026'")
    log.record(table, "pre_2026", pre)
    log.log("[{}] pre 2026: {}".format(table, pre))
    if dry_run:
        return

    cols = get_existing_columns(db, table)
    fields = [f for f in RPSCO_FIELDS if f in cols]

    where = "GJAHR = '2026'"
    rows, err = safe_extract("RPSCO", fields, where, log, "KU-2026-DELTA-RPSCO")
    if err:
        log.log("  skip (rfc error)")
        return
    n = delete_then_insert(db, table, fields, rows, "GJAHR=?", ("2026",))
    log.log("  deleted+inserted {} rows".format(n))

    post = count_rows(db, table, "GJAHR='2026'")
    log.record(table, "post_2026", post)
    log.record(table, "delta_2026", post - pre)
    log.log("[{}] post 2026: {} (delta {:+})".format(table, post, post - pre))


def refresh_fmifiit(db, log, dry_run=False, resume=False):
    """fmifiit_full: re-extract 2026 PERIO 003,004,005. DELETE+INSERT."""
    table = "fmifiit_full"
    pre = count_rows(db, table, "GJAHR='2026'")
    log.record(table, "pre_2026", pre)
    log.log("[{}] pre 2026: {}".format(table, pre))
    if dry_run:
        return

    cols = get_existing_columns(db, table)
    fields = [f for f in FMIFIIT_FIELDS if f in cols]

    for period in ["003", "004", "005"]:
        where = "GJAHR = '2026' AND PERIO = '{}'".format(period)
        rows, err = safe_extract("FMIFIIT", fields, where, log,
                                  "KU-2026-DELTA-FMIFIIT-P{}".format(period))
        if err:
            log.log("  P{}: skip (rfc error)".format(period))
            continue
        n = delete_then_insert(db, table, fields, rows,
                               "GJAHR=? AND PERIO=?", ("2026", period))
        log.log("  P{}: deleted+inserted {} rows".format(period, n))

    post = count_rows(db, table, "GJAHR='2026'")
    log.record(table, "post_2026", post)
    log.record(table, "delta_2026", post - pre)
    log.log("[{}] post 2026: {} (delta {:+})".format(table, post, post - pre))


def refresh_bkpf(db, log, dry_run=False, resume=False):
    """BKPF: delta WHERE GJAHR=2026 AND CPUDT > 20260316. INSERT-only."""
    table = "bkpf"
    pre = count_rows(db, table, "GJAHR='2026'")
    log.record(table, "pre_2026", pre)
    log.log("[{}] pre 2026: {}".format(table, pre))
    if dry_run:
        return

    cols = get_existing_columns(db, table)
    fields = [f for f in BKPF_FIELDS if f in cols]

    where = "GJAHR = '2026' AND CPUDT > '{}'".format(CPUDT_CUTOFF)
    rows, err = safe_extract("BKPF", fields, where, log, "KU-2026-DELTA-BKPF")
    if err:
        return

    # INSERT-only with dedup against existing (BUKRS, BELNR, GJAHR)
    cur = db.cursor()
    existing_keys = set()
    for k in cur.execute("SELECT BUKRS, BELNR, GJAHR FROM bkpf WHERE GJAHR='2026' AND CPUDT > '{}'".format(CPUDT_CUTOFF)):
        existing_keys.add(k)
    new_rows = [r for r in rows if (r.get("BUKRS",""), r.get("BELNR",""), r.get("GJAHR","")) not in existing_keys]
    n = insert_rows(db, table, fields, new_rows)
    log.log("  inserted {} new rows ({} dups skipped)".format(n, len(rows) - n))

    post = count_rows(db, table, "GJAHR='2026'")
    log.record(table, "post_2026", post)
    log.record(table, "delta_2026", post - pre)
    log.log("[{}] post 2026: {} (delta {:+})".format(table, post, post - pre))


def refresh_bsx_table(db, log, table, fields_def, sap_table, where_clause,
                      key_fields, ku_id, dry_run=False):
    """Generic BSIS/BSAS/BSIK/BSAK/BSID/BSAD delta-INSERT."""
    pre = count_rows(db, table, "GJAHR='2026'")
    log.record(table, "pre_2026", pre)
    log.log("[{}] pre 2026: {}".format(table, pre))
    if dry_run:
        return

    cols = get_existing_columns(db, table)
    fields = [f for f in fields_def if f in cols]

    rows, err = safe_extract(sap_table, fields, where_clause, log, ku_id)
    if err:
        return

    # Dedup against existing keys in scope
    cur = db.cursor()
    key_cols = ", ".join(['"{}"'.format(k) for k in key_fields])
    existing_keys = set()
    for k in cur.execute("SELECT {} FROM {} WHERE GJAHR='2026'".format(key_cols, table)):
        existing_keys.add(k)
    new_rows = [r for r in rows
                if tuple(r.get(k, "") for k in key_fields) not in existing_keys]
    n = insert_rows(db, table, fields, new_rows)
    log.log("  inserted {} new rows ({} dups skipped, {} total fetched)".format(
        n, len(rows) - n, len(rows)))

    post = count_rows(db, table, "GJAHR='2026'")
    log.record(table, "post_2026", post)
    log.record(table, "delta_2026", post - pre)
    log.log("[{}] post 2026: {} (delta {:+})".format(table, post, post - pre))


def refresh_bsis(db, log, dry_run=False, resume=False):
    # BSIS Gold has no CPUDT -> filter by BUDAT instead
    where = "GJAHR = '2026' AND BUDAT > '{}'".format(BUDAT_CUTOFF)
    refresh_bsx_table(db, log, "bsis", BSIS_FIELDS, "BSIS", where,
                      ["BUKRS", "BELNR", "GJAHR", "BUZEI"],
                      "KU-2026-DELTA-BSIS", dry_run)


def refresh_bsas(db, log, dry_run=False, resume=False):
    where = "GJAHR = '2026' AND BUDAT > '{}'".format(BUDAT_CUTOFF)
    refresh_bsx_table(db, log, "bsas", BSAS_FIELDS, "BSAS", where,
                      ["BUKRS", "BELNR", "GJAHR", "BUZEI"],
                      "KU-2026-DELTA-BSAS", dry_run)


def refresh_bsik(db, log, dry_run=False, resume=False):
    where = "GJAHR = '2026' AND CPUDT > '{}'".format(CPUDT_CUTOFF)
    refresh_bsx_table(db, log, "bsik", BSIK_FIELDS, "BSIK", where,
                      ["BUKRS", "BELNR", "GJAHR", "BUZEI"],
                      "KU-2026-DELTA-BSIK", dry_run)


def refresh_bsak(db, log, dry_run=False, resume=False):
    where = "GJAHR = '2026' AND CPUDT > '{}'".format(CPUDT_CUTOFF)
    refresh_bsx_table(db, log, "bsak", BSAK_FIELDS, "BSAK", where,
                      ["BUKRS", "BELNR", "GJAHR", "BUZEI"],
                      "KU-2026-DELTA-BSAK", dry_run)


def refresh_bsid(db, log, dry_run=False, resume=False):
    where = "GJAHR = '2026' AND CPUDT > '{}'".format(CPUDT_CUTOFF)
    refresh_bsx_table(db, log, "bsid", BSID_FIELDS, "BSID", where,
                      ["BUKRS", "BELNR", "GJAHR", "BUZEI"],
                      "KU-2026-DELTA-BSID", dry_run)


def refresh_bsad(db, log, dry_run=False, resume=False):
    where = "GJAHR = '2026' AND CPUDT > '{}'".format(CPUDT_CUTOFF)
    refresh_bsx_table(db, log, "bsad", BSAD_FIELDS, "BSAD", where,
                      ["BUKRS", "BELNR", "GJAHR", "BUZEI"],
                      "KU-2026-DELTA-BSAD", dry_run)


def refresh_ekko(db, log, dry_run=False, resume=False):
    """EKKO: delta WHERE AEDAT > 20260315. UPSERT on EBELN."""
    table = "ekko"
    pre = count_rows(db, table)
    pre_max_aedat = db.execute("SELECT MAX(AEDAT) FROM ekko").fetchone()[0]
    log.record(table, "pre_total", pre)
    log.record(table, "pre_max_aedat", pre_max_aedat)
    log.log("[{}] pre total: {} (max AEDAT {})".format(table, pre, pre_max_aedat))
    if dry_run:
        return

    cols = get_existing_columns(db, table)
    fields = [f for f in EKKO_FIELDS if f in cols]

    where = "AEDAT > '{}'".format(AEDAT_CUTOFF)
    rows, err = safe_extract("EKKO", fields, where, log, "KU-2026-DELTA-EKKO")
    if err:
        return

    # UPSERT keeping max AEDAT per EBELN
    by_ebeln = {}
    for r in rows:
        eb = r.get("EBELN", "")
        if not eb:
            continue
        cur_max = by_ebeln.get(eb)
        if cur_max is None or r.get("AEDAT", "") > cur_max.get("AEDAT", ""):
            by_ebeln[eb] = r
    n = upsert_rows(db, table, fields, list(by_ebeln.values()), ["EBELN"])
    log.log("  upserted {} EKKO rows ({} fetched, dedup by max AEDAT)".format(
        n, len(rows)))

    post = count_rows(db, table)
    post_max_aedat = db.execute("SELECT MAX(AEDAT) FROM ekko").fetchone()[0]
    log.record(table, "post_total", post)
    log.record(table, "post_max_aedat", post_max_aedat)
    log.record(table, "delta_total", post - pre)
    log.log("[{}] post total: {} (max AEDAT {})".format(table, post, post_max_aedat))


def refresh_ekpo(db, log, dry_run=False, resume=False):
    """EKPO: delta WHERE AEDAT > 20260315. UPSERT on (EBELN, EBELP)."""
    table = "ekpo"
    pre = count_rows(db, table)
    pre_max_aedat = db.execute("SELECT MAX(AEDAT) FROM ekpo").fetchone()[0]
    log.record(table, "pre_total", pre)
    log.record(table, "pre_max_aedat", pre_max_aedat)
    log.log("[{}] pre total: {} (max AEDAT {})".format(table, pre, pre_max_aedat))
    if dry_run:
        return

    cols = get_existing_columns(db, table)
    fields = [f for f in EKPO_FIELDS if f in cols]

    where = "AEDAT > '{}'".format(AEDAT_CUTOFF)
    rows, err = safe_extract("EKPO", fields, where, log, "KU-2026-DELTA-EKPO")
    if err:
        return

    # UPSERT keeping max AEDAT per (EBELN, EBELP)
    by_key = {}
    for r in rows:
        k = (r.get("EBELN", ""), r.get("EBELP", ""))
        if not k[0]:
            continue
        cur_max = by_key.get(k)
        if cur_max is None or r.get("AEDAT", "") > cur_max.get("AEDAT", ""):
            by_key[k] = r
    n = upsert_rows(db, table, fields, list(by_key.values()), ["EBELN", "EBELP"])
    log.log("  upserted {} EKPO rows ({} fetched, dedup by max AEDAT)".format(
        n, len(rows)))

    post = count_rows(db, table)
    post_max_aedat = db.execute("SELECT MAX(AEDAT) FROM ekpo").fetchone()[0]
    log.record(table, "post_total", post)
    log.record(table, "post_max_aedat", post_max_aedat)
    log.record(table, "delta_total", post - pre)
    log.log("[{}] post total: {} (max AEDAT {})".format(table, post, post_max_aedat))


def refresh_rbkp(db, log, dry_run=False, resume=False):
    """RBKP: delta WHERE BUDAT > 20260315 AND GJAHR=2026. INSERT-only with dedup."""
    table = "rbkp"
    pre = count_rows(db, table, "GJAHR='2026'")
    pre_max_budat = db.execute("SELECT MAX(BUDAT) FROM rbkp").fetchone()[0]
    log.record(table, "pre_2026", pre)
    log.record(table, "pre_max_budat", pre_max_budat)
    log.log("[{}] pre 2026: {} (max BUDAT {})".format(table, pre, pre_max_budat))
    if dry_run:
        return

    cols = get_existing_columns(db, table)
    fields = [f for f in RBKP_FIELDS if f in cols]

    where = "GJAHR = '2026' AND BUDAT > '{}'".format(BUDAT_RBKP)
    rows, err = safe_extract("RBKP", fields, where, log, "KU-2026-DELTA-RBKP")
    if err:
        return

    # Dedup against existing (BELNR, GJAHR)
    existing = set()
    for k in db.execute("SELECT BELNR, GJAHR FROM rbkp WHERE GJAHR='2026'"):
        existing.add(k)
    new_rows = [r for r in rows
                if (r.get("BELNR",""), r.get("GJAHR","")) not in existing]
    n = insert_rows(db, table, fields, new_rows)
    log.log("  inserted {} new rows ({} dups skipped)".format(n, len(rows) - n))

    post = count_rows(db, table, "GJAHR='2026'")
    post_max_budat = db.execute("SELECT MAX(BUDAT) FROM rbkp").fetchone()[0]
    log.record(table, "post_2026", post)
    log.record(table, "post_max_budat", post_max_budat)
    log.record(table, "delta_2026", post - pre)
    log.log("[{}] post 2026: {} (max BUDAT {})".format(table, post, post_max_budat))


def refresh_essr(db, log, dry_run=False, resume=False):
    """ESSR: ALTER TABLE to add AEDAT (if missing), delta WHERE AEDAT > 20260315.
    UPSERT on LBLNI.
    """
    table = "essr"
    cols = get_existing_columns(db, table)
    pre = count_rows(db, table)
    log.record(table, "pre_total", pre)
    log.log("[{}] pre total: {} (cols: {})".format(table, pre, cols))

    if dry_run:
        return

    # Add AEDAT column if missing
    if "AEDAT" not in cols:
        try:
            db.execute('ALTER TABLE essr ADD COLUMN "AEDAT" TEXT')
            db.commit()
            log.log("  ALTER TABLE: added AEDAT column")
            cols.append("AEDAT")
        except Exception as e:
            log.error(table, "ALTER ADD AEDAT failed: {}".format(e))
            return

    fields = [f for f in ESSR_FIELDS if f in cols]

    where = "AEDAT > '{}'".format(AEDAT_CUTOFF)
    rows, err = safe_extract("ESSR", fields, where, log, "KU-2026-DELTA-ESSR")
    if err:
        return

    # UPSERT on LBLNI keeping max AEDAT
    by_key = {}
    for r in rows:
        k = r.get("LBLNI", "")
        if not k:
            continue
        cur_max = by_key.get(k)
        if cur_max is None or r.get("AEDAT", "") > cur_max.get("AEDAT", ""):
            by_key[k] = r
    n = upsert_rows(db, table, fields, list(by_key.values()), ["LBLNI"])
    log.log("  upserted {} ESSR rows ({} fetched, dedup by max AEDAT)".format(
        n, len(rows)))

    post = count_rows(db, table)
    post_max_aedat = db.execute("SELECT MAX(AEDAT) FROM essr").fetchone()[0]
    log.record(table, "post_total", post)
    log.record(table, "post_max_aedat", post_max_aedat)
    log.record(table, "delta_total", post - pre)
    log.log("[{}] post total: {} (max AEDAT {})".format(table, post, post_max_aedat))


# ---------------------------------------------------------------------------
# BLOCK A — PS-AVC core extraction (INC-000005638)
# ---------------------------------------------------------------------------
# Slim 8-field sets (RFC_READ_TABLE 512-byte WA buffer ceiling).
# Where existing Gold DB tables are present, we PRESERVE the existing
# schema (use the same field list) so quality_check scripts keep working.

INCIDENT_POS = ("4500543365", "4500540022", "4500540024")

EKKN_FIELDS = ["EBELN", "EBELP", "PS_PSP_PNR", "FISTL", "GEBER", "SAKTO", "AEDAT"]
BPGE_FIELDS = ["OBJNR", "POSIT", "WRTTP", "GEBER", "VERSN", "TWAER", "WTGES", "WLGES"]
BPHI_FIELDS = ["OBJNR", "WRTTP", "HIERA", "GEBER", "VERSN", "PLDAT", "RELE", "AVA"]
BPJA_FIELDS = ["OBJNR", "WRTTP", "GJAHR", "GEBER", "VERSN", "TWAER", "WTJHR", "WLJHR"]
COSP_BLOCKA_FIELDS = ["OBJNR", "GJAHR", "WRTTP", "KSTAR", "TWAER",
                      "WTG001", "WTG002", "WTG003"]
COSS_BLOCKA_FIELDS = COSP_BLOCKA_FIELDS  # same key set
FMAVCT_BLOCKA_FIELDS = ["RFIKRS", "RFUND", "RFUNDSCTR", "RCMMTITEM", "RYEAR",
                        "ALLOCTYPE_9", "HSL01"]
TKA01_BLOCKA_FIELDS = ["KOKRS", "BEZEI", "FIKRS", "WAERS", "KTOPL", "BPHINR",
                       "CTYP", "CVPROF"]
# OPSV / T185F: small config tables. Try a generous slim set; rfc_read_paginated
# will split if needed.
OPSV_FIELDS = ["PROFIL", "VERSN", "GJAHR", "TOLERANZ", "AKTI"]
T185F_FIELDS = ["TCODE", "PSCRN", "TBNAM", "FNAME", "FAUS"]


def ensure_block_a_table(db, table_name, fields, indexes=None):
    """Create lowercase table if missing with TEXT cols."""
    cols = ", ".join('"{}" TEXT'.format(f) for f in fields)
    db.execute('CREATE TABLE IF NOT EXISTS {} ({})'.format(table_name, cols))
    if indexes:
        for col in indexes:
            try:
                db.execute('CREATE INDEX IF NOT EXISTS idx_{}_{} ON {}({})'.format(
                    table_name, col.lower(), table_name, col))
            except Exception:
                pass
    db.commit()


def get_existing_field_subset(db, table, desired):
    """Return desired fields filtered to those that exist in the SQLite table."""
    cols = get_existing_columns(db, table)
    if not cols:
        return desired  # table doesn't exist yet, use all desired
    return [f for f in desired if f in cols]


def block_a_full_refresh(db, table, fields, sap_table, where, log, ku_id):
    """Full DELETE+INSERT for Block A re-extracts.

    For tables that already have a known good schema (cosp_*, coss_*, fmavct_*,
    bpge, bphi, bpja_*, tka01) we PRESERVE that schema by using the existing
    column list as the field set.

    Always: DELETE all matching rows for the WHERE scope, INSERT fresh.
    """
    cols = get_existing_columns(db, table)
    if cols:
        eff_fields = [f for f in fields if f in cols]
        if len(eff_fields) < len(fields):
            log.log("  schema preserved: using {}/{} fields ({})".format(
                len(eff_fields), len(fields), eff_fields))
    else:
        ensure_block_a_table(db, table, fields)
        eff_fields = fields

    rows, err = safe_extract(sap_table, eff_fields, where, log, ku_id)
    if err:
        return -1
    # Wipe entire table for full-refresh tables (small lookups)
    # For year-scoped tables (cosp_2024, etc.), still wipe entire table
    db.execute("DELETE FROM {}".format(table))
    db.commit()
    n = insert_rows(db, table, eff_fields, rows)
    return n


# --- EKKN: per-PO chunked + broader range ---------------------------------
def refresh_ekkn(db, log, dry_run=False, resume=False):
    """EKKN: per-PO incident extracts (already exist), then broader 4500..-4600.. range."""
    table = "ekkn"
    log.log("[ekkn] strategy: per-PO incident tables (re-extract) + consolidated 'ekkn' broader pull")
    if dry_run:
        return

    cols_per_po = ["EBELN", "EBELP", "PS_PSP_PNR", "FISTL", "GEBER", "SAKTO", "AEDAT"]

    # 1. Re-extract per-incident-PO tables (preserves existing tables for analysis script)
    for i, po in enumerate(INCIDENT_POS):
        sql_tbl = "ekkn_inc5638" if i == 0 else "ekkn_inc5638_{}".format(po[-2:])
        ensure_block_a_table(db, sql_tbl, cols_per_po, indexes=["EBELN", "PS_PSP_PNR"])
        where = "EBELN = '{}'".format(po)
        rows, err = safe_extract("EKKN", cols_per_po, where, log,
                                  "KU-2026-005638-EKKN-PO{}".format(i + 1))
        if err:
            continue
        db.execute("DELETE FROM {}".format(sql_tbl))
        db.commit()
        n = insert_rows(db, sql_tbl, cols_per_po, rows)
        log.log("  {}: {} rows for PO {}".format(sql_tbl, n, po))
        log.record(table, "rows_po_{}".format(po), n)

    # 2. Consolidated 'ekkn' table — broader range; chunked by EBELN to avoid timeouts
    ensure_block_a_table(db, "ekkn", cols_per_po, indexes=["EBELN", "PS_PSP_PNR"])
    pre_total = count_rows(db, "ekkn")
    log.record(table, "pre_total", pre_total)
    log.log("  pre rows in 'ekkn' (consolidated): {}".format(pre_total))

    # First try: just the 3 incident POs as a sanity check
    sanity_where = "EBELN IN ('4500543365','4500540022','4500540024')"
    rows, err = safe_extract("EKKN", cols_per_po, sanity_where, log,
                              "KU-2026-005638-EKKN-INCIDENT")
    if not err:
        log.log("  incident POs in EKKN: {} rows".format(len(rows)))
        # Persist into consolidated ekkn
        if rows:
            # Replace incident PO rows in ekkn
            for po in INCIDENT_POS:
                db.execute("DELETE FROM ekkn WHERE EBELN = ?", (po,))
            db.commit()
            insert_rows(db, "ekkn", cols_per_po, rows)
        log.record(table, "incident_po_rows", len(rows))

    # Don't attempt the full 4500.. range (millions of rows, > 5 min). Log KU.
    log.log("  NOT extracting full EBELN range 4500..-4600.. (would exceed 5 min cap)")
    log_ku("KU-2026-DELTA-EKKN-FULL", "EKKN",
           "EBELN >= '4500000000' AND EBELN < '4600000000'",
           "Skipped: 5-min cap; broader EKKN pull deferred", log)

    post_total = count_rows(db, "ekkn")
    log.record(table, "post_total", post_total)
    log.log("[{}] post total: {} (delta {:+})".format(table, post_total, post_total - pre_total))


# --- COSP / COSS: per-year refresh ----------------------------------------
def _refresh_cosp_coss(db, log, sap_table, prefix):
    """Re-extract cosp_2024, cosp_2025, cosp_2026 (or coss). DELETE+INSERT."""
    fields = COSP_BLOCKA_FIELDS  # same for COSS
    summary = {}
    for year in ("2024", "2025", "2026"):
        sql_tbl = "{}_{}".format(prefix, year)
        ensure_block_a_table(db, sql_tbl, fields, indexes=["OBJNR", "GJAHR", "WRTTP"])
        cols = get_existing_columns(db, sql_tbl)
        eff_fields = [f for f in fields if f in cols] or fields

        pre = count_rows(db, sql_tbl)
        where = "OBJNR LIKE 'PR%' AND GJAHR = '{}'".format(year)
        log.log("  [{}] WHERE: {} (pre rows {})".format(sql_tbl, where, pre))
        rows, err = safe_extract(sap_table, eff_fields, where, log,
                                  "KU-2026-005638-{}-{}".format(sap_table, year))
        if err:
            log.log("    skip year {} (rfc error)".format(year))
            summary[year] = -1
            continue
        db.execute("DELETE FROM {}".format(sql_tbl))
        db.commit()
        n = insert_rows(db, sql_tbl, eff_fields, rows)
        log.log("    {}: {} rows".format(sql_tbl, n))
        summary[year] = n
    return summary


def refresh_cosp(db, log, dry_run=False, resume=False):
    if dry_run:
        return
    s = _refresh_cosp_coss(db, log, "COSP", "cosp")
    log.record("cosp", "rows_per_year", s)


def refresh_coss(db, log, dry_run=False, resume=False):
    if dry_run:
        return
    s = _refresh_cosp_coss(db, log, "COSS", "coss")
    log.record("coss", "rows_per_year", s)


# --- BPGE: full refresh, broader WRTTP filter -----------------------------
def refresh_bpge(db, log, dry_run=False, resume=False):
    """BPGE: re-extract OBJNR LIKE 'PR%' AND WRTTP IN (41,42,51,54,60,61).

    Previous extract returned 654 rows with only WRTTP 01 + 41 — the WHERE
    was too narrow. This version uses the full PS-AVC value-type set.
    """
    table = "bpge"
    pre = count_rows(db, table)
    log.record(table, "pre_total", pre)
    log.log("[{}] pre total: {}".format(table, pre))
    if dry_run:
        return

    cols = get_existing_columns(db, table) or BPGE_FIELDS
    fields = [f for f in BPGE_FIELDS if f in cols] or BPGE_FIELDS

    # Try multiple WRTTP buckets sequentially (each pull is small)
    total_rows = []
    wrttp_set = ("41", "42", "51", "54", "60", "61", "01")
    for wrttp in wrttp_set:
        where = "OBJNR LIKE 'PR%' AND WRTTP = '{}'".format(wrttp)
        rows, err = safe_extract("BPGE", fields, where, log,
                                  "KU-2026-005638-BPGE-WRTTP{}".format(wrttp))
        if err:
            continue
        log.log("  WRTTP {}: {} rows".format(wrttp, len(rows)))
        total_rows.extend(rows)

    db.execute("DELETE FROM bpge")
    db.commit()
    n = insert_rows(db, "bpge", fields, total_rows)
    post = count_rows(db, table)
    log.record(table, "post_total", post)
    log.log("[{}] post total: {} (delta {:+})".format(table, post, post - pre))


# --- BPHI: full refresh ---------------------------------------------------
def refresh_bphi(db, log, dry_run=False, resume=False):
    """BPHI: re-extract OBJNR LIKE 'PR%'."""
    table = "bphi"
    pre = count_rows(db, table)
    log.record(table, "pre_total", pre)
    log.log("[{}] pre total: {}".format(table, pre))
    if dry_run:
        return

    cols = get_existing_columns(db, table) or BPHI_FIELDS
    fields = [f for f in BPHI_FIELDS if f in cols] or BPHI_FIELDS

    where = "OBJNR LIKE 'PR%'"
    rows, err = safe_extract("BPHI", fields, where, log, "KU-2026-005638-BPHI")
    if err:
        return
    db.execute("DELETE FROM bphi")
    db.commit()
    n = insert_rows(db, "bphi", fields, rows)
    post = count_rows(db, table)
    log.record(table, "post_total", post)
    log.log("[{}] post total: {} (delta {:+})".format(table, post, post - pre))


# --- BPJA: per-year refresh ----------------------------------------------
def refresh_bpja(db, log, dry_run=False, resume=False):
    """BPJA: re-extract bpja_2024, bpja_2025, bpja_2026 OBJNR LIKE 'PR%'."""
    if dry_run:
        return
    summary = {}
    for year in ("2024", "2025", "2026"):
        sql_tbl = "bpja_{}".format(year)
        ensure_block_a_table(db, sql_tbl, BPJA_FIELDS,
                             indexes=["OBJNR", "WRTTP", "GJAHR"])
        cols = get_existing_columns(db, sql_tbl)
        eff_fields = [f for f in BPJA_FIELDS if f in cols] or BPJA_FIELDS

        where = "OBJNR LIKE 'PR%' AND GJAHR = '{}'".format(year)
        rows, err = safe_extract("BPJA", eff_fields, where, log,
                                  "KU-2026-005638-BPJA-{}".format(year))
        if err:
            summary[year] = -1
            continue
        db.execute("DELETE FROM {}".format(sql_tbl))
        db.commit()
        n = insert_rows(db, sql_tbl, eff_fields, rows)
        log.log("    {}: {} rows".format(sql_tbl, n))
        summary[year] = n
    log.record("bpja", "rows_per_year", summary)


# --- FMAVCT: per-year proper refresh -------------------------------------
def refresh_fmavct(db, log, dry_run=False, resume=False):
    """FMAVCT: re-extract fmavct_2024/25/26 RFIKRS=UNES."""
    if dry_run:
        return
    summary = {}
    for year in ("2024", "2025", "2026"):
        sql_tbl = "fmavct_{}".format(year)
        ensure_block_a_table(db, sql_tbl, FMAVCT_BLOCKA_FIELDS,
                             indexes=["RFUND", "RFUNDSCTR", "RCMMTITEM"])
        cols = get_existing_columns(db, sql_tbl)
        eff_fields = [f for f in FMAVCT_BLOCKA_FIELDS if f in cols] or FMAVCT_BLOCKA_FIELDS

        where = "RFIKRS = 'UNES' AND RYEAR = '{}'".format(year)
        rows, err = safe_extract("FMAVCT", eff_fields, where, log,
                                  "KU-2026-005638-FMAVCT-{}".format(year))
        if err:
            summary[year] = -1
            continue
        db.execute("DELETE FROM {}".format(sql_tbl))
        db.commit()
        n = insert_rows(db, sql_tbl, eff_fields, rows)
        log.log("    {}: {} rows".format(sql_tbl, n))
        summary[year] = n
    log.record("fmavct", "rows_per_year", summary)


# --- OPSV / T185F: small config tables -----------------------------------
def refresh_opsv(db, log, dry_run=False, resume=False):
    """OPSV: PS-AVC profile config (small)."""
    table = "opsv"
    pre = count_rows(db, table)
    log.log("[{}] pre total: {}".format(table, pre))
    if dry_run:
        return

    ensure_block_a_table(db, table, OPSV_FIELDS)
    cols = get_existing_columns(db, table)
    eff_fields = [f for f in OPSV_FIELDS if f in cols] or OPSV_FIELDS

    rows, err = safe_extract("OPSV", eff_fields, "", log, "KU-2026-005638-OPSV")
    if err:
        return
    db.execute("DELETE FROM opsv")
    db.commit()
    n = insert_rows(db, "opsv", eff_fields, rows)
    log.record(table, "post_total", n)
    log.log("[{}] post total: {}".format(table, n))


def refresh_t185f(db, log, dry_run=False, resume=False):
    """T185F: PS field selection (small)."""
    table = "t185f"
    pre = count_rows(db, table)
    log.log("[{}] pre total: {}".format(table, pre))
    if dry_run:
        return

    ensure_block_a_table(db, table, T185F_FIELDS)
    cols = get_existing_columns(db, table)
    eff_fields = [f for f in T185F_FIELDS if f in cols] or T185F_FIELDS

    rows, err = safe_extract("T185F", eff_fields, "", log, "KU-2026-005638-T185F")
    if err:
        return
    db.execute("DELETE FROM t185f")
    db.commit()
    n = insert_rows(db, "t185f", eff_fields, rows)
    log.record(table, "post_total", n)
    log.log("[{}] post total: {}".format(table, n))


# ---------------------------------------------------------------------------
# DISPATCH TABLE
# ---------------------------------------------------------------------------
STRATEGIES = {
    # Block A — PS-AVC core (INC-000005638)
    "ekkn":         refresh_ekkn,
    "cosp":         refresh_cosp,
    "coss":         refresh_coss,
    "bpge":         refresh_bpge,
    "bphi":         refresh_bphi,
    "bpja":         refresh_bpja,
    "fmavct":       refresh_fmavct,
    "opsv":         refresh_opsv,
    "t185f":        refresh_t185f,

    # Block B — 2026 delta backlog
    "coep":         refresh_coep,
    "cooi":         refresh_cooi,
    "rpsco":        refresh_rpsco,
    "fmifiit_full": refresh_fmifiit,
    "bkpf":         refresh_bkpf,
    "bsis":         refresh_bsis,
    "bsas":         refresh_bsas,
    "bsik":         refresh_bsik,
    "bsak":         refresh_bsak,
    "bsid":         refresh_bsid,
    "bsad":         refresh_bsad,
    "ekko":         refresh_ekko,
    "ekpo":         refresh_ekpo,
    "rbkp":         refresh_rbkp,
    "essr":         refresh_essr,
}

BLOCK_A_TABLES = ["ekkn", "cosp", "coss", "bpge", "bphi", "bpja", "fmavct",
                  "opsv", "t185f"]
BLOCK_B_TABLES = ["bsas", "bsik", "bsak", "bsid", "bsad", "coep", "ekko",
                  "ekpo", "rbkp", "fmifiit_full", "bkpf", "bsis"]


# ---------------------------------------------------------------------------
# Per-table timeout wrapper (Windows-safe — uses thread)
# ---------------------------------------------------------------------------
def run_strategy_with_timeout(strategy, db, log, dry_run, resume,
                               timeout_sec=DEFAULT_TABLE_TIMEOUT_SEC):
    """Run strategy(db, log, ...) with a hard wall-clock timeout.

    On Windows we cannot signal.alarm; we run the strategy in a daemon thread
    and abandon it on timeout. The thread can't be killed, but we return so
    the main loop continues to the next table. The strategy itself uses fresh
    RFC connections per call, so an abandoned thread releases its pyrfc
    handle on garbage collection.
    """
    result = {"done": False, "error": None}

    def _runner():
        try:
            strategy(db, log, dry_run=dry_run, resume=resume)
            result["done"] = True
        except Exception as e:
            result["error"] = str(e)
            result["done"] = True

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join(timeout=timeout_sec)
    if t.is_alive():
        log.log("  !! TIMEOUT after {}s — abandoning table, moving on".format(timeout_sec))
        return False, "timeout"
    if result["error"]:
        log.log("  !! strategy error: {}".format(result["error"]))
        return False, result["error"]
    return True, None


# ---------------------------------------------------------------------------
# STATUS FILE WRITER
# ---------------------------------------------------------------------------
def write_status_md(db, summary):
    """Write/update extraction_status.md with current freshness thresholds."""
    lines = ["# Gold DB Extraction Status",
             "",
             "Updated: {}".format(datetime.now().isoformat()),
             "Source: delta_refresh_2026.py (Session 2026-05-01)",
             "",
             "## 2026 Freshness Thresholds (per table)",
             "",
             "| Table | Total 2026 | Max CPUDT | Max BUDAT | Max AEDAT | Max PERIO |",
             "|-------|-----------:|-----------|-----------|-----------|-----------|"]

    probes = [
        ("bkpf",        "2026", "GJAHR='2026'", "CPUDT", "BUDAT", None,    True),
        ("bsis",        "2026", "GJAHR='2026'", None,    "BUDAT", None,    None),
        ("bsas",        "2026", "GJAHR='2026'", None,    "BUDAT", None,    None),
        ("bsik",        "2026", "GJAHR='2026'", "CPUDT", "BUDAT", None,    None),
        ("bsak",        "2026", "GJAHR='2026'", "CPUDT", "BUDAT", None,    None),
        ("bsid",        "2026", "GJAHR='2026'", "CPUDT", "BUDAT", None,    None),
        ("bsad",        "2026", "GJAHR='2026'", "CPUDT", "BUDAT", None,    None),
        ("rbkp",        "2026", "GJAHR='2026'", "CPUDT", "BUDAT", None,    None),
        ("coep",        "2026", "GJAHR='2026'", None,    None,    None,    True),
        ("cooi",        "2026", "GJAHR='2026'", None,    "BUDAT", None,    True),
        ("rpsco",       "2026", "GJAHR='2026'", None,    None,    None,    None),
        ("fmifiit_full","2026", "GJAHR='2026'", None,    None,    None,    True),
        ("ekko",        "all",  None,           None,    None,    "AEDAT", None),
        ("ekpo",        "all",  None,           None,    None,    "AEDAT", None),
        ("essr",        "all",  None,           None,    None,    "AEDAT", None),
    ]

    for tbl, scope, where, cpudt_col, budat_col, aedat_col, perio_col in probes:
        try:
            cnt_sql = "SELECT COUNT(*) FROM {}".format(tbl)
            if where:
                cnt_sql += " WHERE " + where
            cnt = db.execute(cnt_sql).fetchone()[0]
        except Exception:
            cnt = "n/a"
        def _max(col):
            if col is None:
                return "-"
            try:
                base = "SELECT MAX({}) FROM {}".format(col, tbl)
                if where:
                    base += " WHERE " + where
                v = db.execute(base).fetchone()[0]
                return v or "-"
            except Exception:
                return "n/a"
        cpudt_v = _max(cpudt_col)
        budat_v = _max(budat_col)
        aedat_v = _max(aedat_col)
        perio_v = "-"
        if perio_col:
            try:
                base = "SELECT MAX(PERIO) FROM {}".format(tbl)
                if where:
                    base += " WHERE " + where
                perio_v = db.execute(base).fetchone()[0] or "-"
            except Exception:
                perio_v = "n/a"
        lines.append("| {} | {} | {} | {} | {} | {} |".format(
            tbl, cnt, cpudt_v, budat_v, aedat_v, perio_v))

    lines += ["",
              "## Summary",
              "",
              "- Pre/Post per table: see logs/delta_2026_refresh_*.json",
              "- KU entries logged: {}".format(", ".join(summary.get("ku_logged", [])) or "none"),
              "- Errors: {}".format(len(summary.get("errors", []))),
              ""]

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Delta-refresh Gold DB for FY 2026.")
    parser.add_argument("--table", type=str, default=None,
                        help="Single table (one of: {})".format(
                            ", ".join(STRATEGIES.keys())))
    parser.add_argument("--block", type=str, default=None,
                        choices=("A", "B", "all"),
                        help="A = PS-AVC core, B = 2026 delta backlog, all = both")
    parser.add_argument("--dry-run", action="store_true",
                        help="Probe only, no extraction")
    parser.add_argument("--resume", action="store_true",
                        help="Skip already-fresh combos (best effort)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TABLE_TIMEOUT_SEC,
                        help="Per-table hard timeout in seconds")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(LOG_DIR, "delta_2026_refresh_{}.log".format(ts))
    log = Logger(log_path)

    log.log("=" * 70)
    log.log("DELTA REFRESH 2026 | started {}".format(datetime.now()))
    log.log("Gold DB: {}".format(GOLD_DB))
    log.log("Mode: dry_run={} resume={}".format(args.dry_run, args.resume))
    log.log("=" * 70)

    # Pre size
    pre_size = os.path.getsize(GOLD_DB) if os.path.exists(GOLD_DB) else 0
    log.summary["gold_db_size_pre"] = pre_size
    log.log("Gold DB size pre: {:,} bytes ({:.1f} MB)".format(
        pre_size, pre_size / 1024 / 1024))

    if args.table:
        if args.table not in STRATEGIES:
            log.log("ERROR: unknown table {}".format(args.table))
            log.close()
            sys.exit(2)
        tables_to_run = [args.table]
    elif args.block == "A":
        tables_to_run = list(BLOCK_A_TABLES)
    elif args.block == "B":
        tables_to_run = list(BLOCK_B_TABLES)
    elif args.block == "all":
        tables_to_run = list(BLOCK_A_TABLES) + list(BLOCK_B_TABLES)
    else:
        # No block / no table -> default Block B (legacy behavior)
        tables_to_run = list(BLOCK_B_TABLES)
    log.log("Tables to run ({}): {}".format(len(tables_to_run), tables_to_run))

    db = sqlite3.connect(GOLD_DB, check_same_thread=False)
    db.execute("PRAGMA journal_mode = WAL")

    t_total = time.time()
    for table in tables_to_run:
        log.log("")
        log.log("-" * 70)
        log.log("TABLE: {}".format(table))
        log.log("-" * 70)
        t0 = time.time()
        ok, errstr = run_strategy_with_timeout(
            STRATEGIES[table], db, log,
            dry_run=args.dry_run, resume=args.resume,
            timeout_sec=args.timeout,
        )
        if not ok:
            log.error(table, "STRATEGY_FAILED_OR_TIMEOUT: {}".format(errstr))
            log_ku("KU-2026-DELTA-{}".format(table.upper()), table, "(see strategy)",
                   "timeout/exception: {}".format(errstr), log)
        log.log("[{}] elapsed: {:.1f}s".format(table, time.time() - t0))

    # Integrity check
    log.log("")
    log.log("=" * 70)
    log.log("PRAGMA integrity_check ...")
    try:
        result = db.execute("PRAGMA integrity_check").fetchone()[0]
        log.summary["integrity_check"] = result
        log.log("integrity_check: {}".format(result))
    except Exception as e:
        log.log("integrity_check failed: {}".format(e))
        log.summary["integrity_check"] = "FAILED: {}".format(e)

    # Status MD
    write_status_md(db, log.summary)
    log.log("Wrote status: {}".format(STATUS_FILE))

    db.close()

    post_size = os.path.getsize(GOLD_DB) if os.path.exists(GOLD_DB) else 0
    log.summary["gold_db_size_post"] = post_size
    log.log("Gold DB size post: {:,} bytes ({:.1f} MB) -- delta {:+,} bytes".format(
        post_size, post_size / 1024 / 1024, post_size - pre_size))

    log.log("")
    log.log("=" * 70)
    log.log("FINISHED in {:.1f} min".format((time.time() - t_total) / 60))
    log.log("=" * 70)
    log.close()


if __name__ == "__main__":
    main()
