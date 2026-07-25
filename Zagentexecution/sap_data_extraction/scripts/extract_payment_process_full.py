"""
extract_payment_process_full.py
================================
Full-schema re-extraction of the F110/BCM payment process tables from P01.

Motivation (Session 2026-04-22): Gold DB's current REGUH is extracted with
only 8 columns (LAUFD, LAUFI, ZBUKR, LIFNR, VBLNR, XVORL, HBKID, HKTID).
This is insufficient to answer the BCM routing question — the causal flag
sits in REGUH.RZAWE (payment method) joined to T042Z/T042E config, not
in the LAUFI suffix. Without the full schema we can only observe a
correlation (LAUFI ending in B ↔ BCM batch), not prove the cause.

Scope (priority order — script runs them sequentially):
  P1: REGUH     — 37 fields, the critical one
  P2: T042      — FBZP paying co / sending co (full)
  P2: T042E     — PM per company code (full)
  P2: T042Z     — PM per country (full — has BCM flags XBKKT/XSTRA/XEINZ)
  P2: T042I     — Value date config (full)
  P2: T042B     — Other PM flags (full)
  P3: BNK_BATCH_HEADER  — re-extract with richer field list
  P3: BNK_BATCH_STATUS  — status transition log (new — not in Gold DB yet)
  P4: REGUP     — payment line items (~10x REGUH — overnight if run)
  P4: PAYR      — payment media (small top-up)

Period: 2024-01-01 -> today, monthly partitions by LAUFD (REGUH/REGUP/PAYR).
Config tables: full snapshot (no date filter).

SAP-SAFE DESIGN (matches extract_bkpf_bseg_parallel.py pattern):
  - ConnectionGuard: auto-reconnect on VPN drops
  - rfc_read_paginated: field-splitting for wide tables, 5000-row batches
  - Throttle 3.0s between RFC calls
  - Checkpoint JSON per (table, month) — safe to Ctrl+C and resume

Usage:
    python extract_payment_process_full.py               # P1+P2+P3 (no REGUP)
    python extract_payment_process_full.py --include-regup   # add REGUP
    python extract_payment_process_full.py --table REGUH     # just REGUH
    python extract_payment_process_full.py --from 202501 --to 202604
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, date

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPTS_DIR, "..", "..", ".."))

# Reuse the canonical helpers from mcp-backend-server-python
MCP_DIR = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python")
if MCP_DIR not in sys.path:
    sys.path.insert(0, MCP_DIR)

from rfc_helpers import ConnectionGuard, rfc_read_paginated  # noqa: E402

OUT_DIR = os.path.join(SCRIPTS_DIR, "..", "extracted_data", "payment_process_full")
os.makedirs(OUT_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# FIELD LISTS — canonical SAP REGUH schema fields relevant to BCM routing
# --------------------------------------------------------------------------

REGUH_FIELDS = [
    "LAUFD", "LAUFI", "XVORL", "ZBUKR", "BUKRS", "LIFNR", "KUNNR", "EMPFG",
    "VBLNR", "RZAWE", "RBETR", "RWBTR", "RWAER", "DMBTR", "WAERS",
    "HBKID", "HKTID", "UBNKL", "UBNKS", "UBKNT", "UBHKT",
    "ZBNKS", "ZBNKL", "ZBNKN", "ZBPST",
    "XECHT", "XEINB", "XAUSZ", "XSKRL", "XZLSR", "XBLZD",
    "VALUT", "LAUFK", "CHECT", "CHECF", "LFDNR", "ZNME1",
]

REGUP_FIELDS = [
    "LAUFD", "LAUFI", "XVORL", "ZBUKR", "LIFNR", "KUNNR", "EMPFG",
    "VBLNR", "BELNR", "BUZEI", "GJAHR", "BLART", "BLDAT", "BUDAT",
    "WRBTR", "WAERS", "DMBTR", "SKFBT", "SKNTO", "VALUT",
    "HBKID", "HKTID", "XAUSZ", "XZLSR", "ZUONR", "SGTXT",
]

# T042Z is the key config — the flag that distinguishes BCM-enabled PMs
# should live here or in T042E. Extracting all known fields.
T042Z_FIELDS = [
    "LAND1", "ZLSCH", "TEXT1", "XBKKT", "XSTRA", "XEINZ", "XCRED", "XDEBT",
    "XSKRL", "XINKS", "XPOIN", "XNACH", "XPORD", "XAUSZ", "XAUSF", "PRIOR",
    "ZWELS", "FORMS", "TEXT2", "HBKID", "WAERS", "XTELO", "XSTRA_2",
]

T042E_FIELDS = [
    "ZLSCH", "ZBUKR", "XAVIS", "ANZPO", "VONBT", "BISBT", "WAERS",
    "HBKID", "HKTID", "XNACH", "XOPTI", "XSKRL", "EBENE", "NCDAT",
    "XEBI2", "PYDAT", "BNKOV", "BMMAX", "LAUFS", "FPRN1", "FPRN2",
]

T042_FIELDS = [
    "BUKRS", "ZBUKR", "ULSK1", "ULSK2", "ULSD1", "ULSD2",
    "TEXT1", "XGRBL", "XINTB", "XZLOC",
]

T042I_FIELDS = [
    "ZBUKR", "ZLSCH", "TGBDT", "OPTIM", "OPTII",
]

T042B_FIELDS = [
    "ZLSCH", "ZBUKR", "BUSAB", "XPOTY",
]

BNK_BATCH_HEADER_FIELDS = [
    "BATCH_NO", "RULE_ID", "ITEM_CNT", "LAUFD", "LAUFI",
    "BATCH_SUM", "BATCH_CURR", "STATUS", "CRUSR", "CRDATE", "CRTIME",
    "CHUSR", "CHDATE", "CHTIME", "CUR_PROCESSOR", "ZBUKR", "HBKID", "CUR_STS",
]

# BNK_BATCH_STATUS — status transition log (new table for Gold DB)
BNK_BATCH_STATUS_FIELDS = [
    "BATCH_NO", "SEQ_NO", "STATUS_FROM", "STATUS_TO",
    "USR_CHG", "DATE_CHG", "TIME_CHG", "PROCESSOR",
]

PAYR_FIELDS = [
    "ZBUKR", "HBKID", "HKTID", "RZAWE", "CHECT", "LAUFD", "LAUFI",
    "LIFNR", "VBLNR", "GJAHR", "RWBTR", "WAERS", "VOIDR", "VOIDD",
    "EXTRACT_DATE", "PRNDT", "CHECF",
]


# --------------------------------------------------------------------------
# EXTRACTION LOGIC
# --------------------------------------------------------------------------

def months_in_range(from_yyyymm, to_yyyymm):
    y, m = divmod(from_yyyymm, 100)
    yt, mt = divmod(to_yyyymm, 100)
    while (y, m) <= (yt, mt):
        yield y, m
        m += 1
        if m > 12:
            y, m = y + 1, 1


def first_last_day(y, m):
    first = date(y, m, 1)
    if m == 12:
        last = date(y, 12, 31)
    else:
        last = date(y, m + 1, 1).replace(day=1)
        last = date(y, m + 1, 1)
        last = date(last.year, last.month, 1)
        from calendar import monthrange
        last = date(y, m, monthrange(y, m)[1])
    return first, last


def extract_table_partitioned(conn, table, fields, date_field, months,
                              throttle=3.0, checkpoint_dir=None):
    """Extract a table partitioned by month on date_field (e.g. LAUFD).
    Writes one JSON file per month under checkpoint_dir.
    Skips months whose checkpoint file already exists and is >0 bytes.
    Returns total rows extracted.
    """
    out = os.path.join(checkpoint_dir or OUT_DIR, table)
    os.makedirs(out, exist_ok=True)
    total = 0
    for y, m in months:
        fn = os.path.join(out, f"{table}_{y:04d}_{m:02d}.json")
        if os.path.exists(fn) and os.path.getsize(fn) > 2:
            with open(fn, "r", encoding="utf-8") as f:
                existing = json.load(f)
            print(f"  [SKIP] {table} {y}-{m:02d}: {len(existing)} rows already extracted")
            total += len(existing)
            continue
        d1, d2 = first_last_day(y, m)
        where = f"{date_field} BETWEEN '{d1:%Y%m%d}' AND '{d2:%Y%m%d}'"
        t0 = time.time()
        try:
            rows = rfc_read_paginated(conn, table, fields, where,
                                      batch_size=5000, throttle=throttle)
        except Exception as e:
            print(f"  [ERROR] {table} {y}-{m:02d}: {type(e).__name__}: {e}")
            continue
        elapsed = time.time() - t0
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False)
        print(f"  {table} {y}-{m:02d}: {len(rows):>7} rows in {elapsed:>6.1f}s  -> {fn}")
        total += len(rows)
    return total


def extract_config_full(conn, table, fields, throttle=3.0, checkpoint_dir=None):
    """Full-table extraction (no date partition) — config tables."""
    out = checkpoint_dir or OUT_DIR
    os.makedirs(out, exist_ok=True)
    fn = os.path.join(out, f"{table}_full.json")
    if os.path.exists(fn) and os.path.getsize(fn) > 2:
        with open(fn, "r", encoding="utf-8") as f:
            existing = json.load(f)
        print(f"  [SKIP] {table}: {len(existing)} rows already extracted")
        return len(existing)
    t0 = time.time()
    try:
        rows = rfc_read_paginated(conn, table, fields, "",
                                  batch_size=5000, throttle=throttle)
    except Exception as e:
        print(f"  [ERROR] {table}: {type(e).__name__}: {e}")
        return 0
    elapsed = time.time() - t0
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    print(f"  {table}: {len(rows):>7} rows in {elapsed:>6.1f}s  -> {fn}")
    return len(rows)


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm", type=int, default=202401)
    ap.add_argument("--to", type=int, default=int(datetime.now().strftime("%Y%m")))
    ap.add_argument("--table", help="Run only this table (REGUH/REGUP/T042Z/...)")
    ap.add_argument("--include-regup", action="store_true",
                    help="Also extract REGUP (heavy — ~10x REGUH volume)")
    ap.add_argument("--throttle", type=float, default=3.0)
    ap.add_argument("--system", default="P01")
    args = ap.parse_args()

    months = list(months_in_range(args.frm, args.to))
    print(f"=== Payment Process Full Extraction ===")
    print(f"System : {args.system}")
    print(f"Period : {args.frm} -> {args.to}  ({len(months)} months)")
    print(f"Output : {OUT_DIR}")
    print()

    guard = ConnectionGuard(args.system)
    guard.connect()
    print(f"[OK] Connected to {args.system}")

    plan = []
    t = args.table.upper() if args.table else None

    # P1 — REGUH (the critical one)
    if not t or t == "REGUH":
        plan.append(("REGUH", "partitioned", REGUH_FIELDS, "LAUFD"))

    # P2 — config tables
    for cfg in [
        ("T042",  T042_FIELDS),
        ("T042E", T042E_FIELDS),
        ("T042Z", T042Z_FIELDS),
        ("T042I", T042I_FIELDS),
        ("T042B", T042B_FIELDS),
    ]:
        if not t or t == cfg[0]:
            plan.append((cfg[0], "full", cfg[1], None))

    # P3 — BCM tables with richer schema
    if not t or t == "BNK_BATCH_HEADER":
        plan.append(("BNK_BATCH_HEADER", "partitioned", BNK_BATCH_HEADER_FIELDS, "CRDATE"))
    if not t or t == "BNK_BATCH_STATUS":
        plan.append(("BNK_BATCH_STATUS", "full", BNK_BATCH_STATUS_FIELDS, None))

    # P4 — PAYR top-up
    if not t or t == "PAYR":
        plan.append(("PAYR", "partitioned", PAYR_FIELDS, "LAUFD"))

    # P4 — REGUP (optional, heavy)
    if (args.include_regup and not t) or t == "REGUP":
        plan.append(("REGUP", "partitioned", REGUP_FIELDS, "LAUFD"))

    for table, mode, fields, date_field in plan:
        print(f"\n-- {table} ({mode}, {len(fields)} fields) --")
        t0 = time.time()
        if mode == "partitioned":
            n = extract_table_partitioned(guard, table, fields, date_field, months,
                                          throttle=args.throttle)
        else:
            n = extract_config_full(guard, table, fields, throttle=args.throttle)
        print(f"  TOTAL {table}: {n} rows in {time.time()-t0:.1f}s")

    guard.close()
    print("\n[DONE]")


if __name__ == "__main__":
    main()
