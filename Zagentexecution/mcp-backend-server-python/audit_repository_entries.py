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

def check_obj(conn, obj_name):
    print(f"\n[AUDIT: {obj_name}]")
    
    # 1. Check TADIR (Repository entry)
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR", DELIMITER="|",
                      OPTIONS=[{"TEXT": f"OBJ_NAME = '{obj_name}' AND OBJECT = 'CLAS'"}],
                      FIELDS=[{"FIELDNAME":"PGMID"},{"FIELDNAME":"OBJECT"},
                              {"FIELDNAME":"OBJ_NAME"},{"FIELDNAME":"DEVCLASS"}])
        if r["DATA"]:
            print(f"  TADIR: Found - {r['DATA'][0]['WA']}")
        else:
            print("  TADIR: NOT FOUND")
    except Exception as e:
        print(f"  TADIR error: {e}")

    # 2. Check TRDIR (Includes/Reports)
    try:
        r2 = conn.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR", DELIMITER="|",
                       OPTIONS=[{"TEXT": f"NAME LIKE '{obj_name}%'"}],
                       FIELDS=[{"FIELDNAME":"NAME"},{"FIELDNAME":"SUBC"}],
                       ROWCOUNT=20)
        print(f"  TRDIR ({len(r2['DATA'])} matches):")
        for row in r2["DATA"]:
            print(f"    {row['WA']}")
    except Exception as e:
        print(f"  TRDIR error: {e}")

    # 3. Check SEOCLASS (Class metadata)
    try:
        r3 = conn.call("RFC_READ_TABLE", QUERY_TABLE="SEOCLASS", DELIMITER="|",
                       OPTIONS=[{"TEXT": f"CLSNAME = '{obj_name}'"}],
                       FIELDS=[{"FIELDNAME":"CLSNAME"},{"FIELDNAME":"VERSION"},
                               {"FIELDNAME":"STATE"}])
        if r3["DATA"]:
            print(f"  SEOCLASS: Found - {r3['DATA'][0]['WA']}")
        else:
            print("  SEOCLASS: NOT FOUND")
    except Exception as e:
        print(f"  SEOCLASS error: {e}")

if __name__ == "__main__":
    conn = get_conn()
    check_obj(conn, "ZCL_CRP_PROCESS_REQ")
    check_obj(conn, "ZCL_Z_CRP_SRV_DPC_EXT")
    conn.close()
