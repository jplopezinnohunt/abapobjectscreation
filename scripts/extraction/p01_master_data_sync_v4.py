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

# FM Areas of Interest
FM_AREAS = ['UNES','UBO','IBE','ICTP','IIEP','MGIE','UIS']

def get_p01_conn():
    load_dotenv(DOTENV_PATH)
    params = {
        "ashost": os.getenv("SAP_P01_ASHOST"),
        "sysnr": os.getenv("SAP_P01_SYSNR"),
        "client": os.getenv("SAP_P01_CLIENT"),
        "user": os.getenv("SAP_P01_USER"),
        "lang": os.getenv("SAP_P01_LANG", "EN"),
        "snc_mode": os.getenv("SAP_P01_SNC_MODE"),
        "snc_partnername": os.getenv("SAP_P01_SNC_PARTNERNAME"),
        "snc_qop": os.getenv("SAP_P01_SNC_QOP")
    }
    return Connection(**params)

def init_db():
    print(f"Initializing SQLite database at: {DB_PATH}")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Ensure all tables exist
    cursor.execute('CREATE TABLE IF NOT EXISTS projects (PSPID TEXTPRIMARY KEY, POST1 TEXT, VERNR TEXT, VBUKR TEXT, ERDAT TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS wbs_elements (POSID TEXT PRIMARY KEY, POST1 TEXT, PSPHI TEXT, ERDAT TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS movements_summary (FIKRS TEXT, GJAHR TEXT, FONDS TEXT, FISTL TEXT, BTART TEXT, HSL_SUM REAL, COUNT INTEGER, PRIMARY KEY (FIKRS, GJAHR, FONDS, FISTL, BTART))')
    conn.commit()
    return conn

def sync_table_safe(rfc, db_conn, sap_table, db_table, fields, options="", batch_size=2000):
    cursor = db_conn.cursor()
    skip = 0
    total_synced = 0
    print(f"--- Syncing {sap_table} safe field set -> {db_table} ---")
    
    while True:
        try:
            res = rfc.call("RFC_READ_TABLE",
                          QUERY_TABLE=sap_table,
                          FIELDS=[{'FIELDNAME': f} for f in fields],
                          OPTIONS=[{'TEXT': options}],
                          ROWCOUNT=batch_size,
                          ROWSKIPS=skip)
            
            data = res.get("DATA", [])
            meta = res.get("FIELDS", [])
            
            if not data:
                break
                
            placeholders = ",".join(["?"] * len(fields))
            insert_query = f"INSERT OR REPLACE INTO {db_table} VALUES ({placeholders})"
            
            rows_to_insert = []
            for row in data:
                wa = row.get("WA", "")
                parsed_row = []
                for f in meta:
                    off = int(f.get('OFFSET', 0))
                    len_f = int(f.get('LENGTH', 0))
                    parsed_row.append(wa[off:off+len_f].strip())
                rows_to_insert.append(tuple(parsed_row))
                
            cursor.executemany(insert_query, rows_to_insert)
            db_conn.commit()
            
            total_synced += len(data)
            print(f"  [{sap_table}] Synced {total_synced} rows...")
            if len(data) < batch_size: break
            skip += batch_size
        except RFCError as e:
            print(f"  ERROR syncing {sap_table}: {e}")
            break

def sync_all_movements(rfc, db_conn):
    cursor = db_conn.cursor()
    for area in FM_AREAS:
        for year in ["2024", "2025", "2026"]:
            opt = f"FIKRS = '{area}' AND GJAHR = '{year}'"
            print(f"Syncing movements for {area} / {year}...")
            skip = 0
            summary = {}
            while True:
                try:
                    res = rfc.call("RFC_READ_TABLE",
                                  QUERY_TABLE="FMIFIIT",
                                  FIELDS=[{'FIELDNAME': f} for f in ["FIKRS", "GJAHR", "FONDS", "FISTL", "BTART", "HSL"]],
                                  OPTIONS=[{'TEXT': opt}],
                                  ROWCOUNT=5000,
                                  ROWSKIPS=skip)
                    data = res.get("DATA", [])
                    meta = res.get("FIELDS", [])
                    if not data: break
                    for row in data:
                        wa = row.get("WA", "")
                        vals = {}
                        for f in meta:
                            off = int(f.get('OFFSET', 0))
                            len_f = int(f.get('LENGTH', 0))
                            vals[f['FIELDNAME']] = wa[off:off+len_f].strip()
                        key = (vals['FIKRS'], vals['GJAHR'], vals['FONDS'], vals['FISTL'], vals['BTART'])
                        hsl = float(vals['HSL']) if vals['HSL'] else 0.0
                        if key not in summary: summary[key] = {'hsl': 0.0, 'count': 0}
                        summary[key]['hsl'] += hsl
                        summary[key]['count'] += 1
                    if len(data) < 5000: break
                    skip += 5000
                except RFCError as e:
                    print(f"  [{area}/{year}] FMIFIIT Sync partial or failed: {e}")
                    break
            if summary:
                rows = [(k[0], k[1], k[2], k[3], k[4], v['hsl'], v['count']) for k, v in summary.items()]
                cursor.executemany("INSERT OR REPLACE INTO movements_summary VALUES (?,?,?,?,?,?,?)", rows)
                db_conn.commit()
                print(f"  [{area}/{year}] Added {len(summary)} unique movement keys.")

def main():
    try:
        rfc = get_p01_conn()
        db = init_db()
        
        # 1. Projects/WBS with limited fields to avoid data loss error
        # PSPID is project definition, POSID is WBS element
        sync_table_safe(rfc, db, "PROJ", "projects", ["PSPID", "POST1", "VERNR", "VBUKR", "ERDAT"], options="VBUKR = 'UNESCO' OR VBUKR = '1000'")
        sync_table_safe(rfc, db, "PRPS", "wbs_elements", ["POSID", "POST1", "PSPHI", "ERDAT"], options="PBUKR = 'UNESCO' OR PBUKR = '1000'")
        
        # 2. Movements (Batch per FM Area)
        sync_all_movements(rfc, db)
        
        db.close()
        rfc.close()
        print("Final Sync v4 Complete.")
    except Exception as e:
        print(f"Global Fail: {e}")

if __name__ == "__main__":
    main()
