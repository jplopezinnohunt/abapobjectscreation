import os
import sqlite3
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
DOTENV_PATH = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python", ".env")
DB_PATH = os.path.join(PROJECT_ROOT, "knowledge", "domains", "PSM", "p01_gold_master_data.db")

MAX_WORKERS = 4
BATCH_SIZE = 10000

# We pull the rich set of exact raw fields
RAW_FIELDS = ["FIKRS", "GJAHR", "BELNR", "BUZEI", "FONDS", "FISTL", "FIPEX", "FIPOS", "BTART", "VALTYPE", "TWAER", "HSL", "KSL", "LOGSYS", "STATS", "POPER", "BUDAT", "BLDAT", "USNAM", "AWTYP", "AWKEY"]

db_queue = queue.Queue()

def get_p01_conn():
    load_dotenv(DOTENV_PATH)
    params = {
        "ashost": os.getenv("SAP_P01_ASHOST"),
        "sysnr": os.getenv("SAP_P01_SYSNR"),
        "client": os.getenv("SAP_P01_CLIENT"),
        "user": os.getenv("SAP_P01_USER"),
        "lang": "EN",
        "snc_mode": "1",
        "snc_partnername": os.getenv("SAP_P01_SNC_PARTNERNAME"),
        "snc_qop": "9"
    }
    return Connection(**params)

def db_writer_thread():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cols = ", ".join([f"{f} TEXT" for f in RAW_FIELDS])
    cursor.execute(f"CREATE TABLE IF NOT EXISTS fmifiit_raw_data ({cols}, PRIMARY KEY (FIKRS, GJAHR, BELNR, BUZEI, LOGSYS))")
    conn.commit()

    total_inserted = 0
    while True:
        rows = db_queue.get()
        if rows is None:
            break
            
        if rows:
            placeholders = ",".join(["?"] * len(RAW_FIELDS))
            try:
                cursor.executemany(f"INSERT OR IGNORE INTO fmifiit_raw_data ({','.join(RAW_FIELDS)}) VALUES ({placeholders})", rows)
                conn.commit()
                total_inserted += len(rows)
            except Exception as e:
                print(f"DB Write Error: {e}")
                
        db_queue.task_done()
        
    conn.close()
    print(f"[DB WRITER] Completed successfully. Total Raw Lines inserted: {total_inserted}")

def extract_fund_movements(area, year, fund):
    rfc = get_p01_conn()
    skip = 0
    all_fund_rows = []
    
    # We query EXACTLY by Fund to keep the SAP selection pool extremely tiny and avoid paging crashes
    opt = f"FIKRS = '{area}' AND GJAHR = '{year}' AND FONDS = '{fund}'"
    
    while True:
        try:
            res = rfc.call("RFC_READ_TABLE",
                          QUERY_TABLE="FMIFIIT",
                          FIELDS=[{'FIELDNAME': f} for f in RAW_FIELDS],
                          OPTIONS=[{'TEXT': opt}],
                          ROWCOUNT=BATCH_SIZE,
                          ROWSKIPS=skip)
            
            data = res.get("DATA", [])
            meta = res.get("FIELDS", [])
            
            if not data:
                break
                
            parsed_rows = []
            for row in data:
                wa = row.get("WA", "")
                vals = []
                for f in meta:
                    off = int(f.get('OFFSET', 0))
                    l = int(f.get('LENGTH', 0))
                    vals.append(wa[off:off+l].strip())
                parsed_rows.append(tuple(vals))
                
            all_fund_rows.extend(parsed_rows)
            
            if len(data) < BATCH_SIZE:
                break
                
            skip += BATCH_SIZE
            
        except RFCError as e:
            if "TABLE_WITHOUT_DATA" in str(e):
                break # We hit the end
            print(f"    [FETCH ERROR] {area}/{year}/{fund}: {e}")
            break
            
    try: rfc.close()
    except: pass
    
    if all_fund_rows:
        db_queue.put(all_fund_rows)
        print(f"  [RAW SYNC] Fetched {len(all_fund_rows)} lines for {fund} ({area}/{year})")
        
    return True

def main():
    # 1. Get the list of all active funds from our SQLite Gold Database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # We select DISTINCT FIKRS, GJAHR, FONDS from movements_summary because we already know these are the ones with data!
    cursor.execute("SELECT DISTINCT FIKRS, GJAHR, FONDS FROM movements_summary ORDER BY FIKRS, GJAHR")
    active_combinations = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(active_combinations)} discrete active Funds that require RAW extraction.")
    
    # Start DB writer
    writer = threading.Thread(target=db_writer_thread)
    writer.start()
    
    # Process each active fund via ThreadPool
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for area, year, fund in active_combinations:
            executor.submit(extract_fund_movements, area, year, fund)
            
    # Stop writer
    db_queue.put(None)
    writer.join()

if __name__ == "__main__":
    main()
