"""
discover_dpc_includes.py
Discovers the exact method CM include names for ZCL_Z_CRP_SRV_DPC_EXT
and ZCL_CRP_PROCESS_REQ (if it exists) by reading TRDIR and SEOCOMPO.
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

load_dotenv()

def get_conn():
    params = {
        "ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
        "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"), "lang": "EN",
    }
    if os.getenv("SAP_PASSWD"): params["passwd"] = os.getenv("SAP_PASSWD")
    if os.getenv("SAP_SNC_MODE") == "1":
        params["snc_mode"] = "1"
        params["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        params["snc_qop"] = os.getenv("SAP_SNC_QOP", "9")
    return Connection(**params)

def query(conn, table, options, fields, rowcount=100):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                  OPTIONS=[{"TEXT": options}],
                  FIELDS=[{"FIELDNAME": f} for f in fields],
                  ROWCOUNT=rowcount)
    rows = []
    field_meta = r.get("FIELDS", [])
    for row in r.get("DATA", []):
        parts = row["WA"].split("|")
        rows.append({field_meta[i]["FIELDNAME"]: parts[i].strip() for i in range(len(parts))})
    return rows

def main():
    conn = get_conn()
    print(f"Connected to {os.getenv('SAP_ASHOST')} / {os.getenv('SAP_CLIENT')}")

    for cls in ["ZCL_Z_CRP_SRV_DPC_EXT", "ZCL_Z_CRP_SRV_DPC", "ZCL_CRP_PROCESS_REQ"]:
        print(f"\n=== TRDIR programs for {cls} ===")
        rows = query(conn, "TRDIR", f"NAME LIKE '{cls}%'", ["NAME", "CLAS"], rowcount=50)
        if rows:
            for r in rows:
                print(f"  {r.get('NAME',''):<50} class={r.get('CLAS','')}")
        else:
            print("  (none found)")

    print("\n=== Methods defined in SEOCOMPO for DPC_EXT ===")
    rows = query(conn, "SEOCOMPO",
                 "CLSNAME = 'ZCL_Z_CRP_SRV_DPC_EXT' AND CMPTYPE = '0'",
                 ["CMPNAME", "DESCRIPT"], rowcount=60)
    for r in rows:
        print(f"  {r.get('CMPNAME',''):<60} {r.get('DESCRIPT','')}")

    print("\n=== SEEOIMPLEM — method implementations ===")
    rows = query(conn, "SEEOIMPLEM",
                 "CLSNAME = 'ZCL_Z_CRP_SRV_DPC_EXT'",
                 ["CMPNAME", "INCNAME"], rowcount=60)
    for r in rows:
        print(f"  {r.get('CMPNAME',''):<50} -> include: {r.get('INCNAME','')}")

    conn.close()

if __name__ == "__main__":
    main()
