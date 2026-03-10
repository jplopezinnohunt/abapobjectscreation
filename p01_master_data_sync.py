import sqlite3
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

# Absolute Project Path
PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
UTILS_PATH = os.path.join(PROJECT_ROOT, 'Zagentexecution', 'mcp-backend-server-python')
sys.path.append(UTILS_PATH)

from sap_utils import get_sap_connection

DB_PATH = os.path.join(PROJECT_ROOT, "knowledge", "domains", "PSM", "master_data.db")

def init_db():
    print(f"Initializing SQLite DB: {DB_PATH}")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Funds
    cursor.execute('''CREATE TABLE IF NOT EXISTS p01_funds (
        FIKRS TEXT, FINCODE TEXT, TYPE TEXT, ERFDAT TEXT, ERFNAME TEXT, AENDAT TEXT, ZZIBF TEXT,
        PRIMARY KEY (FIKRS, FINCODE))''')
    
    # Fund Centers
    cursor.execute('''CREATE TABLE IF NOT EXISTS p01_fund_centers (
        FIKRS TEXT, FICTR TEXT, ERFDAT TEXT, ERFNAME TEXT,
        PRIMARY KEY (FIKRS, FICTR))''')

    # Movements
    cursor.execute('''CREATE TABLE IF NOT EXISTS p01_movements (
        FIKRS TEXT, GJAHR TEXT, FONDS TEXT, FISTL TEXT, BTART TEXT, RECORD_COUNT INTEGER,
        PRIMARY KEY (FIKRS, GJAHR, FONDS, FISTL, BTART))''')
    
    conn.commit()
    return conn

def extract_table(rfc_conn, table_name, fields, options=""):
    print(f"Extraction: {table_name} [Options: {options}]")
    try:
        # Paginating or batching is handled by getting all rows if ROWCOUNT=0
        # However, for massive tables (FMFINCODE is ~20k, FMFCTR is ~10k), 0 is fine.
        result = rfc_conn.call("RFC_READ_TABLE", 
                             QUERY_TABLE=table_name, 
                             FIELDS=[{'FIELDNAME': f} for f in fields],
                             OPTIONS=[{'TEXT': options}],
                             ROWCOUNT=0)
        data = result.get("DATA", [])
        fields_meta = result.get("FIELDS", [])
        print(f"Found {len(data)} records.")
        return data, fields_meta
    except RFCError as e:
        print(f"RFC ERROR during {table_name}: {e}")
        return [], []

def parse_data(raw_data, fields_metadata):
    items = []
    for row in raw_data:
        wa = row.get("WA", "")
        vals = {}
        for f in fields_metadata:
            name = f.get('FIELDNAME', f.get('fieldname'))
            offset = int(f.get('OFFSET', f.get('offset', 0)))
            length = int(f.get('LENGTH', f.get('length', 0)))
            vals[name] = wa[offset:offset+length].strip()
        items.append(vals)
    return items

def run_sync():
    print(f"Process Started: {datetime.now()}")
    try:
        rfc = get_sap_connection(system_id="P01")
        print("P01 Session Established.")
    except Exception as e:
        print(f"P01 Session Failed: {e}")
        return

    db = init_db()
    cursor = db.cursor()
    
    # 1. Funds (Full census for target areas)
    areas = "('UNES','UBO','IBE','ICTP','IIEP','MGIE','UIS')"
    raw, meta = extract_table(rfc, "FMFINCODE", 
                            ["FIKRS", "FINCODE", "TYPE", "ERFDAT", "ERFNAME", "AENDAT", "ZZIBF"],
                            options=f"FIKRS IN {areas}")
    data = parse_data(raw, meta)
    for row in data:
        cursor.execute("INSERT OR REPLACE INTO p01_funds VALUES (?,?,?,?,?,?,?)", 
                      (row['FIKRS'], row['FINCODE'], row['TYPE'], row['ERFDAT'], row['ERFNAME'], row['AENDAT'], row['ZZIBF']))
    print(f"Synced {len(data)} master funds.")

    # 2. Fund Centers
    raw, meta = extract_table(rfc, "FMFCTR", ["FIKRS", "FICTR", "ERFDAT", "ERFNAME"], options=f"FIKRS IN {areas}")
    data = parse_data(raw, meta)
    for row in data:
        cursor.execute("INSERT OR REPLACE INTO p01_fund_centers VALUES (?,?,?,?)", 
                      (row['FIKRS'], row['FICTR'], row['ERFDAT'], row['ERFNAME']))
    print(f"Synced {len(data)} master fund centers.")

    # 3. Movements (2024-2026 Batching) - Critical for "Activity Discovery"
    for year in ["2024", "2025", "2026"]:
        # Querying by year to identify active funds/centers
        opt = f"GJAHR = '{year}' AND ( FIKRS = 'UNES' OR FIKRS = 'UBO' )"
        raw, meta = extract_table(rfc, "FMIFIIT", ["FIKRS", "GJAHR", "FONDS", "FISTL", "BTART"], options=opt)
        data = parse_data(raw, meta)
        
        counts = {}
        for d in data:
            k = (d['FIKRS'], d['GJAHR'], d['FONDS'], d['FISTL'], d['BTART'])
            counts[k] = counts.get(k, 0) + 1
        
        for k, v in counts.items():
            cursor.execute("INSERT OR REPLACE INTO p01_movements VALUES (?,?,?,?,?,?)", (k[0], k[1], k[2], k[3], k[4], v))
        print(f"Analyzed {len(counts)} active combinations for {year}.")

    db.commit()
    db.close()
    rfc.close()
    print(f"Process Complete: {datetime.now()}")

if __name__ == "__main__":
    run_sync()
