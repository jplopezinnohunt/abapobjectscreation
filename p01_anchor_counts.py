import os
import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
DOTENV_PATH = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python", ".env")
ANCHOR_FILE = os.path.join(PROJECT_ROOT, "knowledge", "domains", "PSM", "sap_p01_volume_anchors.json")

FM_AREAS = ['UNES', 'UBO', 'IBE', 'ICTP', 'IIEP', 'MGIE', 'UIS']
YEARS = ['2024', '2025', '2026']
TABLES = {
    'FMIFIIT': {'area_field': 'FIKRS', 'year_field': 'GJAHR'},
    'FMBDT': {'area_field': 'RFIKRS', 'year_field': 'RYEAR'},
    'FMAVCT': {'area_field': 'RFIKRS', 'year_field': 'RYEAR'}
}

MAX_WORKERS = 3

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

def count_single_combination(table, year, area, fields):
    area_field = fields['area_field']
    year_field = fields['year_field']
    
    total = 0
    skip = 0
    batch = 100000 
    opt = f"{area_field} = '{area}' AND {year_field} = '{year}'"
    
    rfc = get_p01_conn()
    print(f"[START] Counting {table} for {area}/{year}...")
    
    while True:
        try:
            res = rfc.call("RFC_READ_TABLE",
                          QUERY_TABLE=table,
                          FIELDS=[{'FIELDNAME': area_field}], 
                          OPTIONS=[{'TEXT': opt}],
                          ROWCOUNT=batch,
                          ROWSKIPS=skip)
            
            data = res.get("DATA", [])
            chunk_size = len(data)
            total += chunk_size
            skip += chunk_size
            
            if chunk_size < batch:
                break
                
        except RFCError as e:
            err_str = str(e)
            if "TABLE_WITHOUT_DATA" in err_str:
                break
                
            print(f"  [ERROR] {table} {area}/{year} at skip {skip}. Reconnecting...")
            try: rfc.close()
            except: pass
            time.sleep(3)
            rfc = get_p01_conn()
            
    try: rfc.close()
    except: pass
    
    print(f"[DONE] {table} {area}/{year}: {total} rows.")
    return table, year, area, total

def main():
    anchors = {}
    if os.path.exists(ANCHOR_FILE):
        with open(ANCHOR_FILE, 'r') as f:
            anchors = json.load(f)

    tasks_to_run = []
    
    for table, fields in TABLES.items():
        if table not in anchors: anchors[table] = {}
        for year in YEARS:
            if year not in anchors[table]: anchors[table][year] = {}
            for area in FM_AREAS:
                if str(anchors[table][year].get(area, -1)) != "-1" and anchors[table][year].get(area) != None:
                    print(f"Skipping {table} {area}/{year}, already counted: {anchors[table][year][area]}")
                    continue
                tasks_to_run.append((table, year, area, fields))

    if not tasks_to_run:
        print("All combinations already counted!")
        return

    print(f"Starting {len(tasks_to_run)} counting tasks with Max Parallel Workers: {MAX_WORKERS}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(count_single_combination, t, y, a, f): (t, y, a) for t, y, a, f in tasks_to_run}
        
        for future in as_completed(futures):
            t, y, a, total = future.result()
            anchors[t][y][a] = total
            
            # Save incremental
            with open(ANCHOR_FILE, 'w') as f:
                json.dump(anchors, f, indent=4)

    print("\nAll baseline anchor counts established successfully!")

if __name__ == "__main__":
    main()
