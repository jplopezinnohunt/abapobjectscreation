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

FM_AREAS = ['UNES','UBO','IBE','ICTP','IIEP','MGIE','UIS']

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

def sync_simple(rfc, db_conn, table, db_table, fields, options=""):
    cursor = db_conn.cursor()
    print(f"Syncing {table} (Minimal Fields)...")
    try:
        # Using a safer batch size and NO SKIP initially to see if it works
        res = rfc.call("RFC_READ_TABLE",
                      QUERY_TABLE=table,
                      FIELDS=[{'FIELDNAME': f} for f in fields],
                      OPTIONS=[{'TEXT': options}],
                      ROWCOUNT=1000)
        data = res.get("DATA", [])
        meta = res.get("FIELDS", [])
        if not data:
            print(f"  No data for {table}")
            return
        
        rows = []
        for row in data:
            wa = row.get("WA", "")
            item = []
            for f in meta:
                off = int(f.get('OFFSET', 0))
                l = int(f.get('LENGTH', 0))
                item.append(wa[off:off+l].strip())
            rows.append(tuple(item))
        
        placeholders = ",".join(["?"] * len(fields))
        cursor.executemany(f"INSERT OR REPLACE INTO {db_table} VALUES ({placeholders})", rows)
        db_conn.commit()
        print(f"  Synced {len(data)} rows into {db_table}")
    except Exception as e:
        print(f"  Failed {table}: {e}")

def main():
    try:
        rfc = get_p01_conn()
        conn = sqlite3.connect(DB_PATH)
        
        # 1. Projects - Trying ONLY PSPID first to avoid data loss
        sync_simple(rfc, conn, "PROJ", "projects", ["PSPID", "POST1", "VERNR", "VBUKR", "ERDAT"], options="VBUKR = 'UNESCO'")

        # 2. Movements - Trying without HSL
        for area in ['UNES', 'UBO']:
            for year in ["2024", "2025"]:
                # We save into the summary table but with HSL_SUM = 0 for now
                opt = f"FIKRS = '{area}' AND GJAHR = '{year}'"
                print(f"Syncing {area}/{year} movements...")
                res = rfc.call("RFC_READ_TABLE",
                              QUERY_TABLE="FMIFIIT",
                              FIELDS=[{'FIELDNAME': f} for f in ["FIKRS", "GJAHR", "FONDS", "FISTL", "BTART"]],
                              OPTIONS=[{'TEXT': opt}],
                              ROWCOUNT=1000)
                data = res.get("DATA", [])
                meta = res.get("FIELDS", [])
                if data:
                    rows = []
                    for row in data:
                        wa = row.get("WA", "")
                        # Parse explicitly
                        fi = wa[0:4].strip()
                        gj = wa[4:8].strip()
                        fo = wa[8:18].strip()
                        fs = wa[18:34].strip()
                        bt = wa[34:38].strip()
                        # FIKRS(4), GJAHR(4), FONDS(10), FISTL(16), BTART(4)
                        # Offset/Length mapping is better via Meta though
                        rows.append((fi, gj, fo, fs, bt, 0.0, 1))
                    
                    conn.cursor().executemany("INSERT OR REPLACE INTO movements_summary VALUES (?,?,?,?,?,?,?)", rows)
                    conn.commit()
                    print(f"  Inserted {len(rows)} movements.")

        conn.close()
        rfc.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
