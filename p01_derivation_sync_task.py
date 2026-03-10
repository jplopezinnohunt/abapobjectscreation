import sqlite3
import os
import json
import threading
import queue
import time
from dotenv import load_dotenv
from pyrfc import Connection

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
DOTENV_PATH = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python", ".env")
DB_PATH = os.path.join(PROJECT_ROOT, "UNESCO_PSM_MASTER_DATA.db")

load_dotenv(DOTENV_PATH)

def get_conn():
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
    return Connection(**params)

db_queue = queue.Queue()

def db_worker():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    while True:
        task = db_queue.get()
        if task is None:
            break
        sql, params = task
        try:
            cursor.execute(sql, params)
            conn.commit()
        except Exception as e:
            print(f"DB Error: {e}")
        db_queue.task_done()
    conn.close()

def sync_table(table_name):
    print(f"Syncing table {table_name}...")
    conn = get_conn()
    
    # Get fields
    df = conn.call("DDIF_FIELDINFO_GET", TABNAME=table_name)
    fields = [f['FIELDNAME'] for f in df['FIXED_FIELDS']]
    
    # Simple massive pull
    batch_size = 5000
    skip = 0
    total = 0
    
    # Create table
    schema = ", ".join([f"{f} TEXT" for f in fields])
    db_queue.put((f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})", ()))
    db_queue.put((f"DELETE FROM {table_name}", ()))
    
    while True:
        try:
            res = conn.call("RFC_READ_TABLE", 
                          QUERY_TABLE=table_name, 
                          FIELDS=[{'FIELDNAME': f} for f in fields],
                          ROWSKIPS=skip, 
                          ROWCOUNT=batch_size)
            
            data = res['DATA']
            if not data:
                break
                
            for row in data:
                raw = row['WA']
                # Parse WA - this is tricky with RFC_READ_TABLE if fields are wide
                # Better use query_table logic but here we do it simple
                # Actually RFC_READ_TABLE with many fields often fails
                pass 
            
            # Since RFC_READ_TABLE is limited, we use our query_table logic but optimized
            # For simplicity in this script, I'll use the existing query_table tool logic
            # but in a loop.
            
            # RE-IMPLEMENTING PROPER EXTRACTION
            conn.close()
            return inner_extract(table_name, fields)
            
        except Exception as e:
            print(f"Error: {e}")
            break
    conn.close()

def inner_extract(table_name, fields):
    conn = get_conn()
    skip = 0
    batch = 10000
    while True:
        options = []
        res = conn.call("RFC_READ_TABLE", 
                      QUERY_TABLE=table_name, 
                      FIELDS=[{'FIELDNAME': f} for f in fields],
                      ROWSKIPS=skip, 
                      ROWCOUNT=batch)
        
        rows = res['DATA']
        if not rows:
            break
            
        print(f"Extracted {len(rows)} from {table_name} (skip={skip})")
        
        # Calculate offsets based on field info
        df = conn.call("DDIF_FIELDINFO_GET", TABNAME=table_name)
        offsets = []
        for f in df['FIXED_FIELDS']:
            if f['FIELDNAME'] in fields:
                offsets.append({
                    'name': f['FIELDNAME'],
                    'offset': int(f['OFFSET']),
                    'length': int(f['INTLEN'])
                })
        
        for r in rows:
            wa = r['WA']
            vals = []
            # This parsing is system dependent (byte vs char), but usually safe for text
            # Better approach: request fields one by one if it fails or use a robust parser
            # For these derivation tables, we'll pull all at once and trust the layout
            
            # Actually, let's use the query_table logic exactly
            pass

    conn.close()

# SIMPLIFIED ROBUST SYNC
def robust_sync(table_name):
    import subprocess
    print(f"Mass extracting {table_name} using MCP tools logic...")
    # I'll use a series of run_command calls in the main thread for simplicity
    pass

if __name__ == "__main__":
    # Start DB worker
    # t = threading.Thread(target=db_worker)
    # t.start()
    
    # For this specific task, I'll just use the query_table tool from the agent
    # for the most critical tables to ensure data integrity
    pass
