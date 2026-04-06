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

# Full Universe of FM Areas from previous check
FM_AREAS = ['IBE', 'ICTP', 'IIEP', 'MGIE', 'UBO', 'UIS', 'UNES']
YEARS = ['2024', '2025', '2026']

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

def sync_all_movements_v6(rfc, db_conn):
    cursor = db_conn.cursor()
    print(f"Starting Comprehensive Activity Audit for {len(FM_AREAS)} Areas...")
    
    for area in FM_AREAS:
        for year in YEARS:
            # We use distinct objects discovery strategy
            opt = f"FIKRS = '{area}' AND GJAHR = '{year}'"
            print(f"Processing Universe: {area} | {year}")
            
            skip = 0
            batch = 10000 # Large batch for faster activity discovery
            summary = {} # (FIKRS, GJAHR, FONDS, FISTL, BTART) -> Count
            
            while True:
                try:
                    # Capture basic activity keys
                    res = rfc.call("RFC_READ_TABLE",
                                  QUERY_TABLE="FMIFIIT",
                                  FIELDS=[{'FIELDNAME': f} for f in ["FIKRS", "GJAHR", "FONDS", "FISTL", "BTART"]],
                                  OPTIONS=[{'TEXT': opt}],
                                  ROWCOUNT=batch,
                                  ROWSKIPS=skip)
                    
                    data = res.get("DATA", [])
                    meta = res.get("FIELDS", [])
                    
                    if not data:
                        break
                    
                    for row in data:
                        wa = row.get("WA", "")
                        # Generic parser based on metadata to ensure robustness
                        vals = {}
                        for f in meta:
                            off = int(f.get('OFFSET', 0))
                            l = int(f.get('LENGTH', 0))
                            vals[f['FIELDNAME']] = wa[off:off+l].strip()
                        
                        key = (vals['FIKRS'], vals['GJAHR'], vals['FONDS'], vals['FISTL'], vals['BTART'])
                        summary[key] = summary.get(key, 0) + 1
                    
                    if len(data) < batch:
                        break
                    skip += batch
                    print(f"  Processed {skip} rows for {area}/{year}...")
                    
                except RFCError as e:
                    print(f"  RFC ERROR for {area}/{year} at skip {skip}: {e}")
                    break
            
            # Commit this area/year batch to SQLite
            if summary:
                rows = [(k[0], k[1], k[2], k[3], k[4], 0.0, v) for k, v in summary.items()]
                cursor.executemany("INSERT OR REPLACE INTO movements_summary (FIKRS, GJAHR, FONDS, FISTL, BTART, HSL_SUM, COUNT) VALUES (?,?,?,?,?,?,?)", rows)
                db_conn.commit()
                print(f"  >>> SUCCESS: {len(summary)} active combinations identified for {area}/{year}.")
            else:
                print(f"  No activity found for {area}/{year}.")

def main():
    try:
        rfc = get_p01_conn()
        conn = sqlite3.connect(DB_PATH)
        sync_all_movements_v6(rfc, conn)
        conn.close()
        rfc.close()
        print("\nActivity Universe Capture Complete for all FM Areas (2024-2026).")
    except Exception as e:
        print(f"Global Fail: {e}")

if __name__ == "__main__":
    main()
