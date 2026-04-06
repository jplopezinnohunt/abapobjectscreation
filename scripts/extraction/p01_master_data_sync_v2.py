import sqlite3
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

# Absolute Project Path
PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"

def get_p01_conn():
    dotenv_path = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python", ".env")
    load_dotenv(dotenv_path)
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

DB_PATH = os.path.join(PROJECT_ROOT, "knowledge", "domains", "PSM", "p01_master_data_v2.db")

def init_db():
    print(f"DB: {DB_PATH}")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS funds (FIKRS TEXT, FINCODE TEXT, TYPE TEXT, ERFDAT TEXT, ERFNAME TEXT, PRIMARY KEY (FIKRS, FINCODE))')
    cursor.execute('CREATE TABLE IF NOT EXISTS fc (FIKRS TEXT, FICTR TEXT, ERFDAT TEXT, ERFNAME TEXT, PRIMARY KEY (FIKRS, FICTR))')
    cursor.execute('CREATE TABLE IF NOT EXISTS movements (FIKRS TEXT, GJAHR TEXT, FONDS TEXT, FISTL TEXT, BTART TEXT, COUNT INTEGER, PRIMARY KEY (FIKRS, GJAHR, FONDS, FISTL, BTART))')
    conn.commit()
    return conn

def read_paged(rfc, table, fields, options="", batch=2000):
    all_data = []
    skip = 0
    print(f"Syncing {table}...")
    while True:
        try:
            res = rfc.call("RFC_READ_TABLE",
                          QUERY_TABLE=table,
                          FIELDS=[{'FIELDNAME': f} for f in fields],
                          OPTIONS=[{'TEXT': options}],
                          ROWCOUNT=batch,
                          ROWSKIPS=skip)
            data = res.get("DATA", [])
            meta = res.get("FIELDS", [])
            
            # Parse
            for row in data:
                wa = row.get("WA", "")
                item = {}
                for f in meta:
                    off = int(f.get('OFFSET', 0))
                    len_f = int(f.get('LENGTH', 0))
                    item[f['FIELDNAME']] = wa[off:off+len_f].strip()
                all_data.append(item)
            
            print(f"Batch {skip}: Got {len(data)} rows.")
            if len(data) < batch:
                break
            skip += batch
        except RFCError as e:
            print(f"RFC ERROR at {skip}: {e}")
            break
    return all_data

def sync():
    print("P01 Master Data Full Sync Started.")
    try:
        rfc = get_p01_conn()
        print("P01 Connected.")
    except Exception as e:
        print(f"P01 Failed: {e}")
        return

    db = init_db()
    cursor = db.cursor()
    
    # Target Areas
    areas = "FIKRS IN ('UNES','UBO','IBE','ICTP','IIEP','MGIE','UIS')"

    # 1. Funds
    funds = read_paged(rfc, "FMFINCODE", ["FIKRS", "FINCODE", "TYPE", "ERFDAT", "ERFNAME"], options=areas)
    for f in funds:
        cursor.execute("INSERT OR REPLACE INTO funds VALUES (?,?,?,?,?)", (f['FIKRS'], f['FINCODE'], f['TYPE'], f['ERFDAT'], f['ERFNAME']))
    db.commit() # Commit master data
    print(f"Funds Committed: {len(funds)}")
    
    # 2. Fund Centers
    fcs = read_paged(rfc, "FMFCTR", ["FIKRS", "FICTR", "ERFDAT", "ERFNAME"], options=areas)
    for fc in fcs:
        cursor.execute("INSERT OR REPLACE INTO fc VALUES (?,?,?,?)", (fc['FIKRS'], fc['FICTR'], fc['ERFDAT'], fc['ERFNAME']))
    db.commit() # Commit master data
    print(f"FC Committed: {len(fcs)}")

    # 3. Movements (Summary for UNES/UBO Activity Audit)
    for year in ["2024", "2025", "2026"]:
        opt = f"GJAHR = '{year}' AND ( FIKRS = 'UNES' OR FIKRS = 'UBO' )"
        movs = read_paged(rfc, "FMIFIIT", ["FIKRS", "GJAHR", "FONDS", "FISTL", "BTART"], options=opt, batch=5000)
        sums = {}
        for m in movs:
            key = (m['FIKRS'], m['GJAHR'], m['FONDS'], m['FISTL'], m['BTART'])
            sums[key] = sums.get(key, 0) + 1
        for k, v in sums.items():
            cursor.execute("INSERT OR REPLACE INTO movements VALUES (?,?,?,?,?,?)", (k[0], k[1], k[2], k[3], k[4], v))
        db.commit() # Commit each year
        print(f"Movements for {year} Committed: {len(sums)} unique combinations.")

    db.commit()
    db.close()
    rfc.close()
    print("Done!")

if __name__ == "__main__":
    sync()
