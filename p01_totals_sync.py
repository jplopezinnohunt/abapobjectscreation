import sqlite3
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

# Configuration
PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
DB_PATH = os.path.join(PROJECT_ROOT, "knowledge", "domains", "PSM", "p01_gold_master_data.db")
DOTENV_PATH = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python", ".env")

FM_AREAS = ['UNES', 'UBO', 'IBE', 'ICTP', 'IIEP', 'MGIE', 'UIS']

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

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Simplified summary for totals
    cursor.execute('''CREATE TABLE IF NOT EXISTS fmbdt_summary 
                      (RFIKRS TEXT, RYEAR TEXT, RFUND TEXT, RFUNDSCTR TEXT, COUNT INTEGER, 
                      PRIMARY KEY (RFIKRS, RYEAR, RFUND, RFUNDSCTR))''')
                      
    cursor.execute('''CREATE TABLE IF NOT EXISTS fmavct_summary 
                      (RFIKRS TEXT, RYEAR TEXT, RFUND TEXT, RFUNDSCTR TEXT, COUNT INTEGER, 
                      PRIMARY KEY (RFIKRS, RYEAR, RFUND, RFUNDSCTR))''')
    conn.commit()
    return conn

def sync_totals(rfc, db_conn, table_name, db_table, target_year):
    cursor = db_conn.cursor()
    print(f"\n--- Starting {table_name} Summary Sync for Year: {target_year} ---")
    
    for area in FM_AREAS:
        opt = f"RFIKRS = '{area}' AND RYEAR = '{target_year}'"
        print(f"Processing Universe: {area} | {target_year}")
        
        skip = 0
        batch = 20000  # Large batch to navigate the 1.5M lines efficiently 
        summary = {}   # (RFIKRS, RYEAR, RFUND, RFUNDSCTR) -> Count
        
        while True:
            try:
                res = rfc.call("RFC_READ_TABLE",
                              QUERY_TABLE=table_name,
                              FIELDS=[{'FIELDNAME': f} for f in ["RFIKRS", "RYEAR", "RFUND", "RFUNDSCTR"]],
                              OPTIONS=[{'TEXT': opt}],
                              ROWCOUNT=batch,
                              ROWSKIPS=skip)
                
                data = res.get("DATA", [])
                meta = res.get("FIELDS", [])
                
                if not data:
                    break
                
                for row in data:
                    wa = row.get("WA", "")
                    vals = {}
                    for f in meta:
                        off = int(f.get('OFFSET', 0))
                        l = int(f.get('LENGTH', 0))
                        vals[f['FIELDNAME']] = wa[off:off+l].strip()
                    
                    key = (vals['RFIKRS'], vals['RYEAR'], vals['RFUND'], vals['RFUNDSCTR'])
                    summary[key] = summary.get(key, 0) + 1
                
                if len(data) < batch:
                    break
                
                skip += batch
                print(f"  [{table_name}] Processed {skip} lines for {area}/{target_year}...")
                
            except RFCError as e:
                print(f"  RFC ERROR for {area}/{target_year} at skip {skip}: {e}")
                break
        
        if summary:
            rows = [(k[0], k[1], k[2], k[3], v) for k, v in summary.items()]
            cursor.executemany(f"INSERT OR REPLACE INTO {db_table} (RFIKRS, RYEAR, RFUND, RFUNDSCTR, COUNT) VALUES (?,?,?,?,?)", rows)
            db_conn.commit()
            print(f"  >>> SUCCESS: {len(summary)} active master data combinations identified in {table_name} for {area}.")
        else:
            print(f"  No records found for {area}/{target_year}.")

def main():
    if len(sys.argv) < 3:
        print("Usage: python p01_totals_sync.py <TABLE> <YEAR>")
        print("Example: python p01_totals_sync.py FMBDT 2024")
        sys.exit(1)
        
    target_sap_table = sys.argv[1].upper()
    target_year = sys.argv[2]
    
    if target_sap_table == "FMBDT":
        db_table = "fmbdt_summary"
    elif target_sap_table == "FMAVCT":
        db_table = "fmavct_summary"
    else:
        print("Only FMBDT and FMAVCT supported.")
        sys.exit(1)
        
    try:
        rfc = get_p01_conn()
        conn = init_db()
        
        # Sync only ONE table for ONE year to avoid massive memory issues
        sync_totals(rfc, conn, target_sap_table, db_table, target_year)
        
        conn.close()
        rfc.close()
        print(f"\nCompleted {target_sap_table} for {target_year}.")
    except Exception as e:
        print(f"Global Fail: {e}")

if __name__ == "__main__":
    main()
