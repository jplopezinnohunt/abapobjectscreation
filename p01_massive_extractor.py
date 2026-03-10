import os
import sys
import json
import time
import sqlite3
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

# Configuration
PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
DOTENV_PATH = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python", ".env")
DB_PATH = os.path.join(PROJECT_ROOT, "knowledge", "domains", "PSM", "p01_gold_master_data.db")
ANCHOR_FILE = os.path.join(PROJECT_ROOT, "knowledge", "domains", "PSM", "sap_p01_volume_anchors.json")

# Strategy Constants
MAX_PARALLEL_WORKERS = 3
BATCH_SIZE = 10000 
# Target analytical fields to avoid memory overload (we don't need 300 fields, just the cores)
FMIFIIT_FIELDS = ["FIKRS", "GJAHR", "BELNR", "BUZEI", "FONDS", "FISTL", "FIPEX", "FIPOS", "BTART", "VALTYPE", "TWAER", "HSL", "KSL", "LOGSYS", "STATS"]

db_queue = queue.Queue()

def get_p01_conn():
    load_dotenv(DOTENV_PATH)
    params = {
        "ashost": os.getenv("SAP_P01_ASHOST"),
        "sysnr": os.getenv("SAP_P01_SYSNR"),
        "client": os.getenv("SAP_P01_CLIENT"),
        "user": os.getenv("SAP_P01_USER"),
        "lang": os.getenv("SAP_P01_LANG", "EN"),
        "snc_mode": os.getenv("SAP_SNC_MODE"),
        "snc_partnername": os.getenv("SAP_P01_SNC_PARTNERNAME"),
        "snc_qop": os.getenv("SAP_P01_SNC_QOP")
    }
    return Connection(**params)

def writer_thread_func():
    """Background thread that pulls from the queue and strictly writes to SQLite to avoid DB locks."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the full extraction table
    cols = ", ".join([f"{f} TEXT" for f in FMIFIIT_FIELDS])
    cursor.execute(f"CREATE TABLE IF NOT EXISTS fmifiit_full ({cols}, PRIMARY KEY (FIKRS, GJAHR, BELNR, BUZEI, LOGSYS))")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_fmifiit_fonds_fistl ON fmifiit_full (FONDS, FISTL)")
    conn.commit()

    write_count = 0
    while True:
        task = db_queue.get()
        if task is None: # Sentinel to stop
            break
            
        rows = task
        if rows:
            placeholders = ",".join(["?"] * len(FMIFIIT_FIELDS))
            # INSERT OR IGNORE to allow safe restarts
            cursor.executemany(f"INSERT OR IGNORE INTO fmifiit_full ({','.join(FMIFIIT_FIELDS)}) VALUES ({placeholders})", rows)
            conn.commit()
            write_count += len(rows)
            print(f"  [DB WRITER] Secured {len(rows)} rows to SQLite. (Total DB Inserted: {write_count})")
            
        db_queue.task_done()
        
    conn.close()
    print(f"[DB WRITER] Completely finished. Total written: {write_count}")


def extract_batch(rfc, table, table_fields, area_field, area, year_field, year, skip, limit):
    """Extracts exactly one block of rows from SAP."""
    opt = f"{area_field} = '{area}' AND {year_field} = '{year}'"
    
    try:
        res = rfc.call("RFC_READ_TABLE",
                      QUERY_TABLE=table,
                      FIELDS=[{'FIELDNAME': f} for f in table_fields],
                      OPTIONS=[{'TEXT': opt}],
                      ROWCOUNT=limit,
                      ROWSKIPS=skip)
                      
        data = res.get("DATA", [])
        meta = res.get("FIELDS", [])
        
        parsed_rows = []
        for row in data:
            wa = row.get("WA", "")
            vals = []
            for f in meta:
                off = int(f.get('OFFSET', 0))
                l = int(f.get('LENGTH', 0))
                vals.append(wa[off:off+l].strip())
            parsed_rows.append(tuple(vals))
            
        return parsed_rows
    except Exception as e:
        print(f"    [FETCH ERROR] Failed {area}/{year} offset {skip}: {e}")
        return None

def worker_task(area, year, skip, limit):
    """A single logical task for the ThreadPool."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            rfc = get_p01_conn()
            result = extract_batch(rfc, "FMIFIIT", FMIFIIT_FIELDS, "FIKRS", area, "GJAHR", year, skip, limit)
            rfc.close()
            
            if result is not None:
                # Send to separate DB writer to avoid locking
                db_queue.put(result)
                print(f"[WORKER DONE] Extracted {len(result)} rows for {area}/{year} at offset {skip}.")
                return True
                
        except Exception as e:
            print(f"  [WORKER CRASH] Attempt {attempt+1}/{max_retries} for {area}/{year} offset {skip}: {e}")
            time.sleep(5)
            
    print(f"!!! [FATAL WORKER FAIL] Could not retrieve {area}/{year} offset {skip} after {max_retries} attempts.")
    return False

def main():
    if not os.path.exists(ANCHOR_FILE):
        print("Anchor file missing. Run anchor counts first.")
        return
        
    with open(ANCHOR_FILE, 'r') as f:
        anchors = json.load(f)
        
    fmifiit_anchors = anchors.get("FMIFIIT", {})
    
    # Calculate all specific batch coordinates
    task_coordinates = []
    
    for year, areas in fmifiit_anchors.items():
        for area, total_rows in areas.items():
            if total_rows > 0:
                current_skip = 0
                while current_skip < total_rows:
                    task_coordinates.append((area, year, current_skip, BATCH_SIZE))
                    current_skip += BATCH_SIZE
                    
    print(f"*** MASSIVE EXTRACTION PLAN: FMIFIIT ***")
    print(f"Total Batches to execute: {len(task_coordinates)} (Batch Size: {BATCH_SIZE})")
    print(f"Parallel Worker Threads: {MAX_PARALLEL_WORKERS}")
    
    # Start the DB writer thread
    writer_thread = threading.Thread(target=writer_thread_func)
    writer_thread.start()
    
    # Execute batch fetches in parallel
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
        futures = []
        for coord in task_coordinates:
            area, year, skip, limit = coord
            futures.append(executor.submit(worker_task, area, year, skip, limit))
            time.sleep(0.5) # Slight stagger to avoid hitting the SAP gateway all at the exact same millisecond
            
        for _ in futures:
            pass # Wait for completion

    # Signal writer thread to stop
    db_queue.put(None)
    writer_thread.join()
    
    print("\n[COMPLETE] Massive Bulk Extraction Process Finished.")

if __name__ == "__main__":
    main()
