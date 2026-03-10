import sqlite3
import os
import sys
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
DB_PATH = os.path.join(PROJECT_ROOT, "knowledge", "domains", "PSM", "p01_gold_master_data.db")
DOTENV_PATH = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python", ".env")

FM_AREAS = "('UNES','UBO','IBE','ICTP','IIEP','MGIE','UIS')"

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

def get_sap_count(rfc, table, field, options=""):
    total = 0
    skip = 0
    batch = 50000
    while True:
        try:
            res = rfc.call("RFC_READ_TABLE",
                          QUERY_TABLE=table,
                          FIELDS=[{'FIELDNAME': field}],
                          OPTIONS=[{'TEXT': options}] if options else [],
                          ROWCOUNT=batch,
                          ROWSKIPS=skip)
            data = res.get("DATA", [])
            total += len(data)
            if len(data) < batch:
                break
            skip += batch
        except RFCError as e:
            print(f"SAP count error on {table}: {e}")
            break
    return total

def main():
    try:
        rfc = get_p01_conn()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        tables = [
            ("FMFINCODE", "funds", "FIKRS", f"FIKRS IN {FM_AREAS}"),
            ("FMFCTR", "fund_centers", "FIKRS", f"FIKRS IN {FM_AREAS}"),
            ("YTFM_FUND_CPL", "ytfm_fund_cpl", "FIKRS", f"FIKRS IN {FM_AREAS}"),
            ("YTFM_WRTTP_GR", "ytfm_wrttp_gr", "WRTTP_GRP", "")
        ]

        print(f"{'Table':<20} | {'SAP P01 Count':<15} | {'SQLite Count':<15} | {'Status'}")
        print("-" * 75)

        for sap_tab, sql_tab, filter_fld, opts in tables:
            sap_cnt = get_sap_count(rfc, sap_tab, filter_fld, opts)
            
            try:
                sql_cnt = cursor.execute(f"SELECT COUNT(*) FROM {sql_tab}").fetchone()[0]
            except:
                sql_cnt = 0
                
            status = "MATCH" if sap_cnt == sql_cnt else "MISMATCH"
            print(f"{sap_tab:<20} | {sap_cnt:<15} | {sql_cnt:<15} | {status}")

        print("-" * 75)
        conn.close()
        rfc.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
