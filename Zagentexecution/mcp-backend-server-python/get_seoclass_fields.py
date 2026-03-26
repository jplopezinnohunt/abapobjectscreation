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

def get_table_fields(table_name):
    conn = get_conn()
    print(f"Reading fields for table {table_name}...")
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE=table_name, FIELDS=[{"FIELDNAME":"FIELDNAME"}], ROWCOUNT=1)
        fields = [f['FIELDNAME'] for f in r.get('FIELDS', [])]
        print(f"  Fields: {fields}")
        return fields
    except Exception as e:
        print(f"  Error: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    get_table_fields("SEOCLASS")
