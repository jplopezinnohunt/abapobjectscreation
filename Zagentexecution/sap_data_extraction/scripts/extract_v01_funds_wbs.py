"""
extract_v01_funds_wbs.py
========================
Extract V01 (client 350) Funds + WBS master data for the unescrp CRP test-data
"usable data" computation. Companion to extract_v01_actor_grounding.py (which
did USR02/PA0001/PA0105 for CRP employees). READ-ONLY (RFC_READ_TABLE / SELECT).

WHY: unescrp maintains specifications/test-data/crp-usable-test-data.xlsx — the
authoritative "data usable for tests" per system (Employees / Funds / WBS). D01
is filled; V01 Funds+WBS need V01 master data to compute "usable": fund
date-validity + WBS account-assignment/released + budget. The requester only has
SSO to V01; THIS project owns the RFC/SNC service path, so we pull it here.

Tables written to v01_gold_master_data.db (same per-system DB as the actor pull):
  v01_fmfincode      — fund master (date validity DATAB/DATBIS, type, profile)
  v01_prps           — WBS element master (account-assignment BELKZ, type PRART, level)
  v01_jest           — system status per object (OBJNR LIKE 'PR%' = WBS), STAT/INACT
  v01_proj           — project definitions (PSPID, company code VBUKR)
  v01_fmavct_2024/25/26 — AVC totals table (ledger 9H): budget/consumed/available
                          per control object (fund,fundsctr,cmmtitem), HSL amounts

KEY V01 QUIRKS LEARNED (this session):
  * V01 runs a SECURED RFC_READ_TABLE that REJECTS ROWSKIPS. So every read is
    ROWSKIPS-FREE (ROWCOUNT=0, one call) and, on DATA_BUFFER_EXCEEDED, partitions
    the key space by a NUMC field's leading digit (complete over 0-9).
  * RFC_READ_TABLE here raises a misleading TABLE_WITHOUT_DATA when a requested
    FIELD does not exist (not FIELD_NOT_VALID). Field lists below are validated
    against DDIF_FIELDINFO_GET on V01. FMFINCODE has NO FIVOR; PRPS has NO PSTRT.
  * WHERE options need spaces around '=' ("RYEAR = '2026'"), else OPTION_NOT_VALID.
  * FMAVCT rows exceed the 512-byte line buffer -> field-split into chunks and
    merge by row index (same technique as rfc_helpers.rfc_read_paginated). Each
    chunk is one full ROWSKIPS-free call for the year, so index-merge is aligned;
    a per-year row-count guard aborts the year if chunks disagree.
"""
import os
import sys
import sqlite3
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
EXTRACT_DIR = os.path.abspath(os.path.join(SCRIPTS_DIR, ".."))
MCP = os.path.abspath(os.path.join(EXTRACT_DIR, "..", "mcp-backend-server-python"))
if MCP not in sys.path:
    sys.path.insert(0, MCP)

from rfc_helpers import ConnectionGuard  # noqa: E402
from pyrfc import RFCError  # noqa: E402

DB_PATH = os.path.join(EXTRACT_DIR, "sqlite", "v01_gold_master_data.db")
SYSTEM = "V01"

# Reference funds/WBS from the D01 cost-recovery test set (S-166) to verify coverage.
REF_FUNDS = ["196EAR4042", "538GLO5000", "301EGY4072", "465BRZ0002",
             "469GLO2000", "650RER0008", "633CRP9003", "633CRP9200"]
REF_WBS_HINT = "633CRP9003"  # credit-pool fund+WBS id shape

# ---- simple (narrow) tables: field, base_where, sqlite_name, numc_split_field ----
# numc_split_field: a NUMC key to partition on if a single call overflows (complete over 0-9)
FMFINCODE_FIELDS = ["FIKRS", "FINCODE", "DATAB", "DATBIS", "TYPE", "FINUSE",
                    "PROFIL", "DECKUNG", "SPONSOR", "DATE_EXP", "DATE_CAN"]
PRPS_FIELDS = ["PSPNR", "POSID", "POST1", "OBJNR", "PSPHI", "POSKI", "PBUKR",
               "PGSBR", "PKOKR", "PRCTR", "PRART", "STUFE", "PLAKZ", "BELKZ",
               "KOSTL", "LOEVM", "ERNAM", "ERDAT", "VERNR", "PRPS_STATUS"]
PROJ_FIELDS = ["PSPNR", "PSPID", "POST1", "OBJNR", "VBUKR", "VERNR",
               "ERNAM", "ERDAT", "INACT", "LOEVM", "PROJ_STATUS"]
JEST_FIELDS = ["OBJNR", "STAT", "INACT"]

# FMAVCT field chunks (each < 512-byte line). Merged by row index per year.
FMAVCT_CHUNKS = [
    ["RFIKRS", "RFUND", "RFUNDSCTR", "RCMMTITEM", "RFUNCAREA", "RGRANT_NBR", "RYEAR", "RCVRGRP_9"],
    ["DRCRK", "RRCTY", "RVERS", "RMEASURE", "BUDGET_PD_9", "WFSTATE_9", "ALLOCTYPE_9", "RTCUR"],
    ["ROBJNR", "HSLVT", "HSL01", "HSL02", "HSL03", "HSL04", "HSL05", "HSL06"],
    ["HSL07", "HSL08", "HSL09", "HSL10", "HSL11", "HSL12", "HSL13", "HSL14"],
    ["HSL15", "HSL16"],
]
FMAVCT_FIELDS = [f for c in FMAVCT_CHUNKS for f in c]
FMAVCT_YEARS = ["2024", "2025", "2026"]


def _read(conn, table, fields, where):
    """One ROWSKIPS-free RFC_READ_TABLE call. Returns list of dicts.
    Raises RFCError so caller can partition on DATA_BUFFER_EXCEEDED."""
    opts = [{"TEXT": where}] if where else []
    rfc_fields = [{"FIELDNAME": f} for f in fields]
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                    ROWCOUNT=0, FIELDS=rfc_fields, OPTIONS=opts)
    hdrs = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
    out = []
    for row in res.get("DATA", []):
        parts = row["WA"].split("|")
        out.append({h: (parts[i].strip() if i < len(parts) else "")
                    for i, h in enumerate(hdrs)})
    return out


def read_simple(conn, table, fields, base_where="", numc_field=None):
    """Read a narrow table ROWSKIPS-free; partition by NUMC leading digit on overflow."""
    try:
        return _read(conn, table, fields, base_where)
    except RFCError as e:
        msg = str(e)
        if "TABLE_WITHOUT_DATA" in msg:
            return []
        if "DATA_BUFFER_EXCEEDED" not in msg or not numc_field:
            raise
    rows = []
    for d in "0123456789":
        w = f"{numc_field} LIKE '{d}%'"
        if base_where:
            w = f"{base_where} AND {w}"
        try:
            rows += _read(conn, table, fields, w)
        except RFCError as e:
            if "TABLE_WITHOUT_DATA" not in str(e):
                raise
        time.sleep(0.3)
    return rows


def read_jest_wbs(conn):
    """JEST filtered to WBS objects (OBJNR LIKE 'PR%'); partition by trailing digit on overflow."""
    base = "OBJNR LIKE 'PR%'"
    try:
        return _read(conn, "JEST", JEST_FIELDS, base)
    except RFCError as e:
        if "TABLE_WITHOUT_DATA" in str(e):
            return []
        if "DATA_BUFFER_EXCEEDED" not in str(e):
            raise
    rows = []
    for d in "0123456789":
        w = f"OBJNR LIKE 'PR{d}%'"
        try:
            rows += _read(conn, "JEST", JEST_FIELDS, w)
        except RFCError as e:
            if "TABLE_WITHOUT_DATA" not in str(e):
                raise
        time.sleep(0.3)
    return rows


def read_fmavct_year(conn, year):
    """Read FMAVCT for one year via field-split chunks, merged by row index.
    Returns (rows, note). note != '' means the year was skipped/degraded."""
    where = f"RYEAR = '{year}'"
    chunk_results = []
    for ch in FMAVCT_CHUNKS:
        try:
            chunk_results.append(_read(conn, "FMAVCT", ch, where))
        except RFCError as e:
            if "TABLE_WITHOUT_DATA" in str(e):
                chunk_results.append([])
            else:
                return [], f"RFCError on chunk {ch[:2]}: {str(e).splitlines()[0][:80]}"
        time.sleep(0.3)
    counts = [len(c) for c in chunk_results]
    if len(set(counts)) > 1:
        return [], f"chunk row-count mismatch {counts} -> index-merge unsafe, year skipped"
    n = counts[0] if counts else 0
    rows = []
    for i in range(n):
        merged = {}
        for c in chunk_results:
            merged.update(c[i])
        rows.append(merged)
    return rows, ""


def write_table(cur, sqlite_name, fields, rows):
    cols = ", ".join(f'"{f}" TEXT' for f in fields)
    cur.execute(f'DROP TABLE IF EXISTS "{sqlite_name}"')
    cur.execute(f'CREATE TABLE "{sqlite_name}" ({cols})')
    ph = ", ".join("?" for _ in fields)
    cur.executemany(f'INSERT INTO "{sqlite_name}" VALUES ({ph})',
                    [tuple(r.get(f, "") for f in fields) for r in rows])


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    print(f"[connect] {SYSTEM} (SNC/SSO)...", flush=True)
    t0 = time.time()
    g = ConnectionGuard(SYSTEM)
    g.connect()
    print(f"[connect] OK in {time.time()-t0:.1f}s -> {DB_PATH}", flush=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    summary = []
    notes = []

    # --- narrow tables ---
    plan = [
        ("FMFINCODE", FMFINCODE_FIELDS, "", "v01_fmfincode", None),
        ("PRPS", PRPS_FIELDS, "", "v01_prps", "PSPNR"),
        ("PROJ", PROJ_FIELDS, "", "v01_proj", "PSPNR"),
    ]
    for table, fields, where, name, numc in plan:
        print(f"[{table}] reading {len(fields)} fields ...", flush=True)
        t0 = time.time()
        rows = read_simple(g, table, fields, where, numc)
        write_table(cur, name, fields, rows)
        conn.commit()
        print(f"[{table}] {len(rows):,} rows -> {name} ({time.time()-t0:.1f}s)", flush=True)
        summary.append((table, name, len(rows)))

    # --- JEST (WBS status) ---
    print("[JEST] reading OBJNR LIKE 'PR%' ...", flush=True)
    t0 = time.time()
    jest = read_jest_wbs(g)
    write_table(cur, "v01_jest", JEST_FIELDS, jest)
    conn.commit()
    print(f"[JEST] {len(jest):,} rows -> v01_jest ({time.time()-t0:.1f}s)", flush=True)
    summary.append(("JEST", "v01_jest", len(jest)))

    # --- FMAVCT (AVC totals, per year, field-split) ---
    for year in FMAVCT_YEARS:
        name = f"v01_fmavct_{year}"
        print(f"[FMAVCT] year {year} (field-split, {len(FMAVCT_CHUNKS)} chunks) ...", flush=True)
        t0 = time.time()
        rows, note = read_fmavct_year(g, year)
        write_table(cur, name, FMAVCT_FIELDS, rows)
        conn.commit()
        tag = f"  NOTE: {note}" if note else ""
        print(f"[FMAVCT] {year}: {len(rows):,} rows -> {name} ({time.time()-t0:.1f}s){tag}", flush=True)
        summary.append((f"FMAVCT/{year}", name, len(rows)))
        if note:
            notes.append(f"FMAVCT {year}: {note}")

    # --- reference-fund coverage check ---
    present = []
    for fnd in REF_FUNDS:
        r = cur.execute("SELECT FIKRS, FINCODE, DATAB, DATBIS FROM v01_fmfincode WHERE FINCODE = ?",
                        (fnd,)).fetchall()
        present.append((fnd, len(r), r[0] if r else None))
    print("\n[REF FUNDS on V01]")
    for fnd, n, row in present:
        print(f"  {fnd:12s} {'PRESENT '+str(row) if n else 'ABSENT'}")

    # --- provenance ---
    cur.execute('DROP TABLE IF EXISTS _funds_wbs_meta')
    cur.execute('CREATE TABLE _funds_wbs_meta (k TEXT, v TEXT)')
    cur.executemany('INSERT INTO _funds_wbs_meta VALUES (?,?)', [
        ("system", "V01"),
        ("host", "hq-sap-v01.hq.int.unesco.org"),
        ("client", "350"),
        ("channel", "RFC_READ_TABLE over SNC/SSO (abapobjectscreation service path)"),
        ("purpose", "unescrp CRP usable-test-data: Funds + WBS (crp-usable-test-data.xlsx)"),
        ("tables", ", ".join(s[1] for s in summary)),
        ("ref_funds_present", ", ".join(f for f, n, _ in present if n)),
        ("ref_funds_absent", ", ".join(f for f, n, _ in present if not n)),
        ("notes", " | ".join(notes) if notes else "none"),
        ("fmavct_ledger", "9H (AVC), amounts = HSLVT + HSL01..HSL16 (FM-area currency)"),
    ])
    conn.commit()
    conn.close()
    g.close()

    print("\n=== DONE ===")
    for table, name, n in summary:
        print(f"  {table:14s} -> {name:18s} {n:>9,} rows")
    print(f"  DB: {DB_PATH}")
    if notes:
        print("  NOTES:")
        for nt in notes:
            print(f"    - {nt}")


if __name__ == "__main__":
    main()
