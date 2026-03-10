import os
import sqlite3
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
DOTENV_PATH = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python", ".env")
DB_PATH = os.path.join(PROJECT_ROOT, "knowledge", "domains", "PSM", "p01_gold_master_data.db")

BATCH_SIZE = 5000

PROJ_FIELDS = ["PSPID", "POST1", "VBUKR", "VERNR", "ERDAT", "PSPNR"]
PRPS_FIELDS = ["POSID", "POST1", "PBUKR", "VERNR", "ERDAT", "PSPHI", "PSPNR", "OBJNR"]

def get_p01_conn():
    load_dotenv(DOTENV_PATH)
    return Connection(
        ashost=os.getenv("SAP_P01_ASHOST"),
        sysnr=os.getenv("SAP_P01_SYSNR"),
        client=os.getenv("SAP_P01_CLIENT"),
        user=os.getenv("SAP_P01_USER"),
        lang="EN",
        snc_mode="1",
        snc_partnername=os.getenv("SAP_P01_SNC_PARTNERNAME"),
        snc_qop="9"
    )

def extract_all(rfc, table_name, field_list, opt_filter=""):
    print(f"\n--- Starting {table_name} Full Sync ---")
    skip = 0
    all_rows = []
    
    while True:
        try:
            res = rfc.call("RFC_READ_TABLE",
                          QUERY_TABLE=table_name,
                          FIELDS=[{'FIELDNAME': f} for f in field_list],
                          OPTIONS=[{'TEXT': opt_filter}] if opt_filter else [],
                          ROWCOUNT=BATCH_SIZE,
                          ROWSKIPS=skip)
            
            data = res.get("DATA", [])
            meta = res.get("FIELDS", [])
            
            if not data:
                break
                
            for row in data:
                wa = row.get("WA", "")
                vals = []
                for f in meta:
                    off = int(f.get('OFFSET', 0))
                    l   = int(f.get('LENGTH', 0))
                    vals.append(wa[off:off+l].strip())
                all_rows.append(tuple(vals))
                
            skip += BATCH_SIZE
            print(f"  [{table_name}] Extracted {len(all_rows)} lines...")
            
            if len(data) < BATCH_SIZE:
                break
                
        except RFCError as e:
            print(f"  RFC ERROR at skip {skip}: {e}")
            break
            
    return all_rows

def main():
    rfc = get_p01_conn()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # PROJ
    cols_proj = ", ".join([f"{f} TEXT" for f in PROJ_FIELDS])
    cursor.execute(f"CREATE TABLE IF NOT EXISTS proj ({cols_proj}, PRIMARY KEY (PSPID))")
    proj_data = extract_all(rfc, "PROJ", PROJ_FIELDS)
    if proj_data:
        cursor.execute("DELETE FROM proj")
        ph = ",".join(["?"] * len(PROJ_FIELDS))
        cursor.executemany(f"INSERT OR IGNORE INTO proj ({','.join(PROJ_FIELDS)}) VALUES ({ph})", proj_data)
        conn.commit()
        print(f"SUCCESS: {len(proj_data)} records into PROJ.")

    # PRPS (now with OBJNR and PSPNR)
    cols_prps = ", ".join([f"{f} TEXT" for f in PRPS_FIELDS])
    cursor.execute(f"CREATE TABLE IF NOT EXISTS prps ({cols_prps}, PRIMARY KEY (POSID))")
    prps_data = extract_all(rfc, "PRPS", PRPS_FIELDS)
    if prps_data:
        cursor.execute("DELETE FROM prps")
        ph = ",".join(["?"] * len(PRPS_FIELDS))
        cursor.executemany(f"INSERT OR IGNORE INTO prps ({','.join(PRPS_FIELDS)}) VALUES ({ph})", prps_data)
        conn.commit()
        print(f"SUCCESS: {len(prps_data)} records into PRPS.")

    # Report OBJNR coverage for verification
    cursor.execute("SELECT COUNT(*) FROM prps WHERE OBJNR IS NOT NULL AND OBJNR != ''")
    objnr_count = cursor.fetchone()[0]
    print(f"\nOBJNR populated in PRPS: {objnr_count} rows")

    conn.close()
    rfc.close()
    print("PROJ and PRPS Sync Complete!")

if __name__ == "__main__":
    main()
