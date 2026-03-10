import os
import sqlite3
import threading
import time
import queue
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
DOTENV_PATH = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python", ".env")
DB_PATH = os.path.join(PROJECT_ROOT, "knowledge", "domains", "PSM", "p01_gold_master_data.db")

# Lowered workers to prevent SNC gateway saturation
MAX_WORKERS = 2
BATCH_SIZE = 5000

TABLE_CONFIGS = {
    "RPSCO": {
        "fields":  ["OBJNR", "GJAHR", "WRTTP", "PERIO", "STAGR", "WTGBTR"],
        "key":     "OBJNR",
        "pk":      "OBJNR, GJAHR, WRTTP, PERIO",
        "filter":  "OBJNR = '{objnr}'"
    },
    "COOI": {
        "fields":  ["OBJNR", "GJAHR", "BELNR", "BUZEI", "BTART", "WRTTP", "TWAERS", "WTGBTR", "BLDAT"],
        "key":     "OBJNR",
        "pk":      "OBJNR, GJAHR, BELNR, BUZEI",
        "filter":  "OBJNR = '{objnr}' AND GJAHR IN ('2024','2025','2026')"
    },
    "COEP": {
        "fields":  ["OBJNR", "GJAHR", "BELNR", "BUZEI", "WRTTP", "KOART", "TWAERS", "WKGBTR", "BLDAT", "USNAM"],
        "key":     "OBJNR",
        "pk":      "OBJNR, GJAHR, BELNR, BUZEI",
        "filter":  "OBJNR = '{objnr}' AND GJAHR IN ('2024','2025','2026')"
    },
    "JEST": {
        "fields":  ["OBJNR", "STAT", "INACT"],
        "key":     "OBJNR",
        "pk":      "OBJNR, STAT",
        "filter":  "OBJNR = '{objnr}'"
    }
}

db_queues = {t: queue.Queue() for t in TABLE_CONFIGS}

def get_p01_conn():
    load_dotenv(DOTENV_PATH)
    params = {
        "ashost": os.getenv("SAP_P01_ASHOST"),
        "sysnr": os.getenv("SAP_P01_SYSNR"),
        "client": os.getenv("SAP_P01_CLIENT"),
        "user": os.getenv("SAP_P01_USER"),
        "lang": "EN",
        "snc_mode": "1",
        "snc_partnername": f"{os.getenv('SAP_P01_SNC_PARTNERNAME')}",
        "snc_qop": "9"
    }
    # Add small delay before connection to avoid flood
    time.sleep(0.1)
    return Connection(**params)

def db_writer(table_name, config):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cols_def = ", ".join([f"{f} TEXT" for f in config["fields"]])
    pk = config["pk"]
    tbl = table_name.lower()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {tbl} ({cols_def}, PRIMARY KEY ({pk}))")
    conn.commit()
    
    total_written = 0
    q = db_queues[table_name]
    while True:
        rows = q.get()
        if rows is None: break
        if rows:
            ph = ",".join(["?"] * len(config["fields"]))
            f_str = ",".join(config["fields"])
            try:
                cursor.executemany(f"INSERT OR IGNORE INTO {tbl} ({f_str}) VALUES ({ph})", rows)
                conn.commit()
                total_written += len(rows)
            except Exception as e:
                print(f"[DB ERR] {table_name}: {e}")
        q.task_done()
    conn.close()
    print(f"[#] {table_name} DONE. Total: {total_written}")

def extract_for_objnr_robust(table_name, config, objnr):
    retries = 3
    for attempt in range(retries):
        try:
            rfc = get_p01_conn()
            skip = 0
            all_rows = []
            opt = config["filter"].format(objnr=objnr)
            fields = config["fields"]
            
            while True:
                res = rfc.call("RFC_READ_TABLE",
                               QUERY_TABLE=table_name,
                               FIELDS=[{"FIELDNAME": f} for f in fields],
                               OPTIONS=[{"TEXT": opt}],
                               ROWCOUNT=BATCH_SIZE,
                               ROWSKIPS=skip)
                data = res.get("DATA", [])
                meta = res.get("FIELDS", [])
                
                if not data: break
                
                for row in data:
                    wa = row.get("WA", "")
                    vals = []
                    for f in meta:
                        off, l = int(f.get("OFFSET", 0)), int(f.get("LENGTH", 0))
                        vals.append(wa[off:off+l].strip())
                    all_rows.append(tuple(vals))
                
                if len(data) < BATCH_SIZE: break
                skip += BATCH_SIZE
            
            rfc.close()
            if all_rows:
                db_queues[table_name].put(all_rows)
            return objnr, len(all_rows)
            
        except Exception as e:
            time.sleep(1.0 * (attempt + 1))
            if attempt == retries - 1:
                print(f" [X] FATAL {table_name}/{objnr}: {e}")
                return objnr, 0
    return objnr, 0

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT OBJNR FROM prps WHERE OBJNR LIKE 'PR%' ORDER BY OBJNR")
    objnrs = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print(f"--- PS REALITY SYNC START ({datetime.now().strftime('%H:%M:%S')}) ---")
    print(f"Targeting {len(objnrs)} WBS OBJNRs | Workers: {MAX_WORKERS}")
    
    writers = {}
    for table_name, config in TABLE_CONFIGS.items():
        t = threading.Thread(target=db_writer, args=(table_name, config), daemon=True)
        t.start()
        writers[table_name] = t
    
    for table_name, config in TABLE_CONFIGS.items():
        print(f"\n> Syncing Table: {table_name}")
        completed = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(extract_for_objnr_robust, table_name, config, obj): obj for obj in objnrs}
            for fut in futures:
                fut.result()
                completed += 1
                if completed % 1000 == 0:
                    print(f"  - Progress: {completed}/{len(objnrs)}")
        
        db_queues[table_name].put(None)
        writers[table_name].join()
    
    print(f"\n--- PS REALITY SYNC COMPLETE ({datetime.now().strftime('%H:%M:%S')}) ---")

if __name__ == "__main__":
    main()
