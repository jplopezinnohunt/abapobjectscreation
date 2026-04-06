import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
DOTENV_PATH = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python", ".env")
ANCHOR_FILE = os.path.join(PROJECT_ROOT, "knowledge", "domains", "PSM", "sap_p01_ps_anchors.json")

# Tables to anchor for Project System. We filter for OBJNR LIKE 'PR%' to only get WBS-related rows.
TABLES = {
    'RPSCO': {'opt': "OBJNR LIKE 'PR%'", 'field': 'OBJNR'},        # Project Info DB: Totals
    'COOI':  {'opt': "OBJNR LIKE 'PR%' AND GJAHR IN ('2024', '2025', '2026')", 'field': 'OBJNR'}, # Commitments
    'COEP':  {'opt': "OBJNR LIKE 'PR%' AND GJAHR IN ('2024', '2025', '2026')", 'field': 'OBJNR'}  # Actuals Line Items
}

MAX_WORKERS = 3

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

def count_table(table, config):
    total = 0
    skip = 0
    batch = 100000 
    
    rfc = get_p01_conn()
    print(f"[START] Counting {table}...")
    
    while True:
        try:
            res = rfc.call("RFC_READ_TABLE",
                          QUERY_TABLE=table,
                          FIELDS=[{'FIELDNAME': config['field']}], 
                          OPTIONS=[{'TEXT': config['opt']}],
                          ROWCOUNT=batch,
                          ROWSKIPS=skip)
            
            data = res.get("DATA", [])
            chunk_size = len(data)
            total += chunk_size
            skip += chunk_size
            
            print(f"  {table}: {total} rows counted...")
            if chunk_size < batch:
                break
                
        except RFCError as e:
            err_str = str(e)
            if "TABLE_WITHOUT_DATA" in err_str:
                break
                
            print(f"  [ERROR] {table} at skip {skip}: {e}")
            try: rfc.close()
            except: pass
            time.sleep(3)
            rfc = get_p01_conn()
            
    try: rfc.close()
    except: pass
    
    print(f"[DONE] {table}: {total} total rows.")
    return table, total

def main():
    anchors = {}
    if os.path.exists(ANCHOR_FILE):
        with open(ANCHOR_FILE, 'r') as f:
            anchors = json.load(f)

    tasks_to_run = []
    for table, config in TABLES.items():
        if table not in anchors:
            tasks_to_run.append((table, config))
        else:
            print(f"Skipping {table}, already counted: {anchors[table]}")

    if not tasks_to_run:
        print("All PS tables already anchored!")
        return

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(count_table, t, c): t for t, c in tasks_to_run}
        
        for future in as_completed(futures):
            table, total = future.result()
            anchors[table] = total
            
            with open(ANCHOR_FILE, 'w') as f:
                json.dump(anchors, f, indent=4)

    print("\nAll PS volume anchors established successfully!")

if __name__ == "__main__":
    main()
