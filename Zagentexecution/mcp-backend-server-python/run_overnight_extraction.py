"""
run_overnight_extraction.py
============================
Master overnight orchestrator for UNESCO P01 data extraction.

PIPELINES:
  FI  -> BKPF + BSEG        (FI Document Headers + Line Items, 2024-2026)
  MM  -> EKKO + EKPO + EKBE + ESSR + ESLL  (Purchasing + Entry Sheets, 2024-2026)

SAP SAFETY -- GUARANTEED MAX 2 CONCURRENT RFC CONNECTIONS:
  A single threading.Semaphore(2) is shared by ALL 7 table threads.
  No matter how many tables are queued, only 2 can be actively talking
  to SAP at any given moment. The others wait their turn automatically.

  Visual queue example:
    Slot 1: [BKPF ###################### extracting...]
    Slot 2: [BSEG ###################### extracting...]
    Queue:  [EKKO waiting...] [EKPO waiting...] [EKBE waiting...] ...
    (when BKPF finishes -> EKKO takes slot 1, and so on)

CHECKPOINTING:
  Each table+period saves a separate JSON checkpoint.
  Re-running this script skips anything already done -- safe to restart
  at any point after an interruption.

MONITORING (from another terminal while running):
    python run_overnight_extraction.py --status

Usage:
    python run_overnight_extraction.py                  # Full run (both pipelines)
    python run_overnight_extraction.py --only fi        # FI only
    python run_overnight_extraction.py --only mm        # MM only
    python run_overnight_extraction.py --year 2024      # Single year
    python run_overnight_extraction.py --throttle 2.0   # Gentler on SAP
    python run_overnight_extraction.py --merge-only     # Just merge checkpoints
    python run_overnight_extraction.py --status         # Progress report
"""

import os
import sys
import json
import time
import threading
import argparse
import traceback
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "extracted_data")
LOG_FILE = os.path.join(DATA_DIR, "extraction_log.txt")

# -----------------------------------------------------------------------------
# GLOBAL SAP SEMAPHORE -- the single source of truth for connection limits
# -----------------------------------------------------------------------------
SAP_SEMAPHORE = threading.Semaphore(2)   # <- ONLY 2 concurrent RFC connections


# -----------------------------------------------------------------------------
# THREAD-SAFE LOGGER
# -----------------------------------------------------------------------------
_log_lock = threading.Lock()

def log(msg, tag="MASTER"):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts}  [{tag:<12s}]  {msg}"
    with _log_lock:
        print(line, flush=True)
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


# -----------------------------------------------------------------------------
# STATUS REPORT
# -----------------------------------------------------------------------------

def print_status_report():
    print(f"\n{'='*70}")
    print(f"  SAP EXTRACTION STATUS REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    print(f"  {'Table':<8}  {'Done':>6}  {'Expected':>8}  {'Total Rows':>14}  {'Status'}")
    print(f"  {'-'*60}")

    table_dirs = {
        "BKPF": os.path.join(DATA_DIR, "BKPF"),
        "BSEG": os.path.join(DATA_DIR, "BSEG"),
        "EKKO": os.path.join(DATA_DIR, "EKKO"),
        "EKPO": os.path.join(DATA_DIR, "EKPO"),
        "EKBE": os.path.join(DATA_DIR, "EKBE"),
        "ESSR": os.path.join(DATA_DIR, "ESSR"),
        "ESLL": os.path.join(DATA_DIR, "ESLL"),
    }

    overall_rows = 0
    for tbl, d in table_dirs.items():
        if not os.path.exists(d):
            print(f"  {tbl:<8}  {'0':>6}  {'36':>8}  {'0':>14}  NOT STARTED")
            continue

        files = [f for f in os.listdir(d) if f.endswith(".json")]
        total = 0
        for fname in files:
            try:
                with open(os.path.join(d, fname), encoding="utf-8") as f:
                    data = json.load(f)
                total += data.get("meta", {}).get("row_count", 0)
            except Exception:
                pass

        expected = 1 if tbl == "ESLL" else 36
        pct      = int(len(files) / expected * 100)
        status   = "OK COMPLETE" if len(files) >= expected else f"{pct}% done"
        overall_rows += total
        print(f"  {tbl:<8}  {len(files):>6}  {expected:>8}  {total:>14,}  {status}")

    print(f"  {'-'*60}")
    print(f"  {'TOTAL':<8}  {'':>6}  {'':>8}  {overall_rows:>14,}")
    print(f"{'='*70}\n")


# -----------------------------------------------------------------------------
# PIPELINE RUNNERS
# -----------------------------------------------------------------------------

def run_fi_pipeline(years, batch_size, throttle):
    log("Starting FI pipeline (BKPF + BSEG replacements: BSIK/BSAK/BSID/BSAD/BSIS/BSAS)", "FI")
    t0 = time.time()
    try:
        sys.path.insert(0, BASE_DIR)
        import extract_bkpf_bseg_parallel as fi

        # Override module-level config
        fi.YEARS      = years
        fi.BATCH_SIZE = batch_size

        # BKPF first (date-based)
        log("Starting BKPF extraction (by BUDAT)...", "FI")
        t = threading.Thread(
            target=fi.extract_table_thread,
            args=("BKPF", fi.BKPF_FIELDS, "BUDAT", fi.BKPF_DIR,
                  years, batch_size, throttle, SAP_SEMAPHORE),
            name="BKPF", daemon=True,
        )
        t.start()
        t.join()

        # BSEG replacement tables (all transparent, date-based via CPUDT)
        # Semaphore limits to 2 concurrent -- rest queue automatically
        threads = []
        for tbl_name, date_f, koart, desc in fi.BSEG_TABLES:
            fields, date_field, out_dir = fi.TABLE_DEFS[tbl_name]
            t = threading.Thread(
                target=fi.extract_table_thread,
                args=(tbl_name, fields, date_field, out_dir,
                      years, batch_size, throttle, SAP_SEMAPHORE),
                name=tbl_name, daemon=True,
            )
            threads.append(t)
            t.start()
            log(f"{tbl_name} thread queued ({desc}, KOART={koart})", "FI")
            time.sleep(0.5)

        for t in threads:
            t.join()

        fi.merge_all()
        log(f"FI pipeline COMPLETE in {(time.time()-t0)/60:.1f} min", "FI")

    except Exception as e:
        log(f"FI pipeline FATAL ERROR: {e}\n{traceback.format_exc()}", "FI")


def run_mm_pipeline(years, batch_size, throttle, skip_esll=False):
    log("Starting MM pipeline (EKKO + EKPO + EKBE + ESSR + ESLL)", "MM")
    t0 = time.time()
    try:
        sys.path.insert(0, BASE_DIR)
        import extract_ekko_ekpo_parallel as mm

        mm.YEARS      = years
        mm.BATCH_SIZE = batch_size

        # Launch ALL 4 table threads -- semaphore will queue them to max 2 concurrent
        threads = []
        for tbl, (fields, date_f, out_d) in mm.TABLE_DEFS.items():
            t = threading.Thread(
                target=mm.extract_table_thread,
                args=(tbl, fields, date_f, out_d, years, batch_size, throttle, SAP_SEMAPHORE),
                name=tbl, daemon=True,
            )
            threads.append(t)
            t.start()
            log(f"{tbl} thread queued (waiting for semaphore slot)", "MM")
            time.sleep(0.5)

        for t in threads:
            t.join()

        if not skip_esll:
            log("Starting ESLL extraction (entry sheet lines)...", "MM")
            mm.extract_esll(years, batch_size, throttle, SAP_SEMAPHORE)

        mm.merge_all()
        log(f"MM pipeline COMPLETE in {(time.time()-t0)/60:.1f} min", "MM")

    except Exception as e:
        log(f"MM pipeline FATAL ERROR: {e}\n{traceback.format_exc()}", "MM")


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Overnight SAP Extraction -- max 2 RFC connections at all times")
    parser.add_argument("--only",       choices=["fi", "mm"], default=None,
                        help="Run only FI or only MM pipeline")
    parser.add_argument("--year",       type=int,   default=None,  help="Extract only this year (e.g. 2024)")
    parser.add_argument("--batch-size", type=int,   default=5000,  help="Rows per RFC call (default: 5000, proven with 2M FMIFIIT)")
    parser.add_argument("--throttle",   type=float, default=3.0,   help="Seconds between RFC pages (default: 3.0, proven safe)")
    parser.add_argument("--skip-esll",  action="store_true",       help="Skip ESLL entry sheet lines")
    parser.add_argument("--merge-only", action="store_true",       help="Only merge checkpoints, no extraction")
    parser.add_argument("--status",     action="store_true",       help="Show extraction progress and exit")
    args = parser.parse_args()

    years      = [args.year] if args.year else [2024, 2025, 2026]
    batch_size = args.batch_size
    throttle   = args.throttle

    os.makedirs(DATA_DIR, exist_ok=True)

    if args.status:
        print_status_report()
        return

    t_start = datetime.now()
    log(f"{'='*55}")
    log(f"UNESCO SAP OVERNIGHT EXTRACTION  --  STARTED")
    log(f"Years:       {years}")
    log(f"Batch size:  {batch_size} rows/call")
    log(f"Throttle:    {throttle}s between pages")
    log(f"Max SAP connections: 2  (global semaphore enforced)")
    log(f"Pipeline:    {args.only or 'BOTH (FI + MM)  -- all 7 tables queued'}")
    log(f"Log file:    {LOG_FILE}")
    log(f"{'='*55}")

    if args.merge_only:
        sys.path.insert(0, BASE_DIR)
        if not args.only or args.only == "fi":
            import extract_bkpf_bseg_parallel as fi; fi.merge_all()
        if not args.only or args.only == "mm":
            import extract_ekko_ekpo_parallel as mm; mm.merge_all()
        print_status_report()
        return

    # Launch pipeline threads (NOT table threads -- those are internal)
    # Each pipeline thread internally launches its table threads with shared semaphore
    pipeline_threads = []

    if not args.only or args.only == "fi":
        t = threading.Thread(
            target=run_fi_pipeline,
            args=(years, batch_size, throttle),
            name="FI-PIPELINE", daemon=True,
        )
        pipeline_threads.append(("FI", t))
        t.start()
        log("FI pipeline launched (BKPF + BSEG)")

    if not args.only or args.only == "mm":
        time.sleep(1)
        t = threading.Thread(
            target=run_mm_pipeline,
            args=(years, batch_size, throttle, args.skip_esll),
            name="MM-PIPELINE", daemon=True,
        )
        pipeline_threads.append(("MM", t))
        t.start()
        log("MM pipeline launched (EKKO + EKPO + EKBE + ESSR + ESLL)")

    log(f"All pipelines running. {len(pipeline_threads)} pipelines × N tables = ALWAYS max 2 SAP connections.")
    log("Monitor progress: python run_overnight_extraction.py --status")

    for name, t in pipeline_threads:
        t.join()
        log(f"Pipeline '{name}' finished.")

    elapsed_h = (datetime.now() - t_start).total_seconds() / 3600
    log(f"ALL COMPLETE. Total elapsed: {elapsed_h:.2f} hours")
    print_status_report()


if __name__ == "__main__":
    main()
