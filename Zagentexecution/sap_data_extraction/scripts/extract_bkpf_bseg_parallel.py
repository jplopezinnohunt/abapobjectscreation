"""
extract_bkpf_bseg_parallel.py
==============================
Parallel extractor for BKPF (FI Document Headers) and BSEG (FI Line Items).
Covers fiscal years 2024-2026 from P01 (Production).

SAP-SAFE DESIGN:
  - Uses a GLOBAL SEMAPHORE imported from sap_connection_guard.py
  - Max 2 concurrent RFC connections across ALL extraction scripts
  - BKPF and BSEG each use 1 connection â€” they run simultaneously (= 2 concurrent)
  - Within each table: periods extracted sequentially, month by month
  - Throttle: 1s sleep between RFC pages to protect SAP work processes
  - Checkpoint per month â€” safe to resume at any time

Output:
  extracted_data/BKPF/BKPF_YYYY_MM.json
  extracted_data/BSEG/BSEG_YYYY_MM.json
  extracted_data/BKPF_BSEG_merged.json

Usage:
    python extract_bkpf_bseg_parallel.py
    python extract_bkpf_bseg_parallel.py --year 2025
    python extract_bkpf_bseg_parallel.py --bkpf-only
    python extract_bkpf_bseg_parallel.py --merge-only
    python extract_bkpf_bseg_parallel.py --throttle 2.0
"""

import os
import json
import time
import argparse
import threading
from datetime import datetime
from dotenv import load_dotenv

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CONFIG
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(SCRIPTS_DIR)   # sap_data_extraction/
DATA_DIR    = os.path.join(BASE_DIR, "extracted_data")
BKPF_DIR   = os.path.join(DATA_DIR, "BKPF")
BSEG_DIR   = os.path.join(DATA_DIR, "BSEG")
MERGED_OUT = os.path.join(DATA_DIR, "BKPF_BSEG_merged.json")
YEARS      = [2024, 2025, 2026]

# BKPF: FI Document Header (key fields â€” avoid very wide rows)
BKPF_FIELDS = [
    "MANDT", "BUKRS", "BELNR", "GJAHR", "BLART", "BLDAT", "BUDAT", "MONAT",
    "CPUDT", "CPUTM", "USNAM", "TCODE", "BKTXT", "WAERS",
    "AWTYP", "AWKEY", "XBLNR", "GLVOR",
]

# BSEG: FI Line Items (keep field count low â€” BSEG rows are very wide)
BSEG_FIELDS = [
    "MANDT", "BUKRS", "BELNR", "GJAHR", "BUZEI", "BUDAT", "BLART", "MONAT",
    "SHKZG", "WRBTR", "WAERS", "DMBTR", "MWSKZ", "KOSTL", "AUFNR",
    "HKONT", "PRCTR", "FKBER", "GSBER", "EBELN", "EBELP", "BSCHL", "KOART",
]


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# RFC HELPERS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_connection(system_id="P01"):
    from pyrfc import Connection
    load_dotenv(os.path.join(SCRIPTS_DIR, ".env"))
    prefix = f"SAP_{system_id}_"
    def env(k, d=None): return os.getenv(prefix + k) or os.getenv("SAP_" + k) or d
    params = {
        "ashost": env("ASHOST"), "sysnr": env("SYSNR"),
        "client": env("CLIENT"), "user":  env("USER"), "lang": env("LANG", "EN"),
    }
    passwd = env("PASSWD") or env("PASSWORD")
    if passwd: params["passwd"] = passwd
    if env("SNC_MODE") == "1":
        params["snc_mode"] = "1"
        params["snc_partnername"] = env("SNC_PARTNERNAME")
        params["snc_qop"] = env("SNC_QOP", "9")
    return Connection(**params)


def rfc_read_paginated(conn, table, fields, where, batch_size=200, throttle=1.0):
    """Read a SAP table in pages via RFC_READ_TABLE. Throttles between pages."""
    from pyrfc import RFCError
    rfc_fields  = [{"FIELDNAME": f} for f in fields]
    rfc_options = [{"TEXT": where}] if where else []
    all_rows, offset = [], 0

    while True:
        try:
            result = conn.call(
                "RFC_READ_TABLE",
                QUERY_TABLE=table, DELIMITER="|",
                ROWCOUNT=batch_size, ROWSKIPS=offset,
                OPTIONS=rfc_options, FIELDS=rfc_fields,
            )
        except RFCError as e:
            if "DATA_BUFFER_EXCEEDED" in str(e):
                result = conn.call(
                    "RFC_READ_TABLE",
                    QUERY_TABLE=table, DELIMITER="|",
                    ROWCOUNT=batch_size, ROWSKIPS=offset,
                    OPTIONS=rfc_options, FIELDS=[],
                )
            else:
                raise

        raw  = result.get("DATA", [])
        hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
        for row in raw:
            parts = row["WA"].split("|")
            all_rows.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)})

        returned = len(raw)
        offset  += returned
        if returned < batch_size:
            break
        if throttle > 0:
            time.sleep(throttle)

    return all_rows


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# TABLE THREAD (one connection, sequential periods)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def extract_table_thread(table_name, fields, date_field, out_dir,
                          years, batch_size, throttle, sap_semaphore):
    """
    Runs as a single thread. Acquires the global SAP semaphore once,
    holds it for the full duration, then releases it when done.

    This means: when BKPF and BSEG run together, they hold 2 slots = max load.
    """
    label = f"[{table_name}]"

    with sap_semaphore:   # â† Acquire 1 slot from the global semaphore
        print(f"  {label} Semaphore acquired. Connecting to P01...")
        os.makedirs(out_dir, exist_ok=True)

        try:
            conn = get_connection("P01")
        except Exception as e:
            print(f"  {label} Connection FAILED: {e}")
            return

        print(f"  {label} Connected. Extracting {len(years)*12} periods sequentially...")
        total_rows = 0
        t_start    = time.time()

        for year in years:
            for month in range(1, 13):
                monat      = f"{month:02d}"
                checkpoint = os.path.join(out_dir, f"{table_name}_{year}_{monat}.json")

                if os.path.exists(checkpoint):
                    with open(checkpoint, encoding="utf-8") as f:
                        d = json.load(f)
                    cnt = d.get("meta", {}).get("row_count", 0)
                    print(f"  {label} SKIP {year}/{monat}  [{cnt} rows â€” already done]")
                    total_rows += cnt
                    continue

                # WHERE clause
                date_from = f"{year}{monat}01"
                if month < 12:
                    date_to_next = f"{year}{(month+1):02d}01"
                    where = f"{date_field} >= '{date_from}' AND {date_field} < '{date_to_next}'"
                else:
                    where = f"{date_field} >= '{date_from}' AND {date_field} <= '{year}1231'"

                print(f"  {label} {year}/{monat}  where: {where}")
                t0 = time.time()
                try:
                    rows = rfc_read_paginated(conn, table_name, fields, where, batch_size, throttle)
                except Exception as e:
                    print(f"  {label} ERROR {year}/{monat}: {e}")
                    rows = []

                elapsed = time.time() - t0
                data = {
                    "meta": {
                        "table": table_name, "year": year, "month": month,
                        "monat_str": monat, "row_count": len(rows),
                        "extracted_at": datetime.now().isoformat(),
                        "elapsed_sec": round(elapsed, 1),
                    },
                    "rows": rows,
                }
                with open(checkpoint, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, default=str)

                total_rows += len(rows)
                print(f"  {label}   â†’ {len(rows):,} rows  ({elapsed:.0f}s)  running total: {total_rows:,}")

                if throttle > 0:
                    time.sleep(throttle)   # Inter-period cooldown

        try:
            conn.close()
        except Exception:
            pass

        elapsed_total = (time.time() - t_start) / 60
        print(f"\n  {label} COMPLETE. {total_rows:,} rows in {elapsed_total:.1f} min. Semaphore released.")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# MERGE
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def merge_all():
    all_bkpf, all_bseg = [], []
    for year in YEARS:
        for month in range(1, 13):
            monat = f"{month:02d}"
            for lst, tbl, d in [(all_bkpf, "BKPF", BKPF_DIR), (all_bseg, "BSEG", BSEG_DIR)]:
                fp = os.path.join(d, f"{tbl}_{year}_{monat}.json")
                if os.path.exists(fp):
                    with open(fp, encoding="utf-8") as f:
                        lst.append(json.load(f))

    total_bkpf = sum(d["meta"]["row_count"] for d in all_bkpf)
    total_bseg = sum(d["meta"]["row_count"] for d in all_bseg)

    merged = {
        "meta": {
            "extraction_type": "BKPF+BSEG (2024-2026)", "merged_at": datetime.now().isoformat(),
            "source_system": "P01", "years": YEARS,
            "bkpf_periods": len(all_bkpf), "bseg_periods": len(all_bseg),
            "total_bkpf_rows": total_bkpf, "total_bseg_rows": total_bseg,
        },
        "bkpf_summary": sorted(
            [{"year": d["meta"]["year"], "month": d["meta"]["month"], "rows": d["meta"]["row_count"]} for d in all_bkpf],
            key=lambda x: (x["year"], x["month"])
        ),
        "bseg_summary": sorted(
            [{"year": d["meta"]["year"], "month": d["meta"]["month"], "rows": d["meta"]["row_count"]} for d in all_bseg],
            key=lambda x: (x["year"], x["month"])
        ),
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MERGED_OUT, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  [Merge] BKPF: {total_bkpf:,}  BSEG: {total_bseg:,}  â†’ {MERGED_OUT}")
    return merged


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# MAIN
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main(sap_semaphore=None):
    """
    Can be called standalone OR from run_overnight_extraction.py
    which passes in the shared global semaphore.
    """
    parser = argparse.ArgumentParser(description="BKPF+BSEG Extractor â€” max 2 SAP connections")
    parser.add_argument("--year",       type=int,   default=None)
    parser.add_argument("--batch-size", type=int,   default=200)
    parser.add_argument("--throttle",   type=float, default=1.0)
    parser.add_argument("--bkpf-only",  action="store_true")
    parser.add_argument("--bseg-only",  action="store_true")
    parser.add_argument("--merge-only", action="store_true")
    args = parser.parse_args()

    years      = [args.year] if args.year else YEARS
    batch_size = args.batch_size
    throttle   = args.throttle

    # If called standalone, create own semaphore(2) â€” both BKPF+BSEG can run together
    if sap_semaphore is None:
        sap_semaphore = threading.Semaphore(2)

    t_start = datetime.now()
    print(f"\n{'='*70}")
    print(f"  BKPF + BSEG  |  P01  |  {t_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Years={years}  Batch={batch_size}  Throttle={throttle}s")
    print(f"{'='*70}\n")

    if not args.merge_only:
        threads = []
        if not args.bseg_only:
            t = threading.Thread(
                target=extract_table_thread,
                args=("BKPF", BKPF_FIELDS, "BUDAT", BKPF_DIR, years, batch_size, throttle, sap_semaphore),
                name="BKPF", daemon=True,
            )
            threads.append(t); t.start()
            print("  [START] BKPF thread â†’ waiting for semaphore slot...")

        if not args.bkpf_only:
            time.sleep(1)
            t = threading.Thread(
                target=extract_table_thread,
                args=("BSEG", BSEG_FIELDS, "BUDAT", BSEG_DIR, years, batch_size, throttle, sap_semaphore),
                name="BSEG", daemon=True,
            )
            threads.append(t); t.start()
            print("  [START] BSEG thread â†’ waiting for semaphore slot...")

        for t in threads:
            t.join()

    merge_all()
    elapsed = (datetime.now() - t_start).total_seconds()
    print(f"\n  Finished. Total: {elapsed/60:.1f} min")


if __name__ == "__main__":
    main()
