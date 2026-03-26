import os, sys
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    p = {"ashost": "172.16.4.66", "sysnr": "00", "client": "350", 
         "user": os.getenv("SAP_USER"), "lang": "EN"}
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"; p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = "9"
    return Connection(**p)

def find_tables(prefix):
    conn = get_conn()
    print(f"Searching for tables matching {prefix}...")
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD02L", DELIMITER="|",
                      OPTIONS=[{"TEXT": f"TABNAME LIKE '{prefix}%' AND TABCLASS = 'TRANSP'"}],
                      FIELDS=[{"FIELDNAME":"TABNAME"}], ROWCOUNT=50)
        tabs = [row['WA'].strip() for row in r['DATA']]
        print(f"  Found: {tabs}")
        return tabs
    except Exception as e:
        print(f"  Error: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    find_tables("SEO")
