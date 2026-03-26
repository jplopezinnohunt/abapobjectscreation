"""
transport_adhoc_read.py — Read E071 + E071K objects for specific transport orders
Outputs JSON for companion builder consumption.
"""
import os, sys, json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def env(*keys, default=""):
    for k in keys:
        v = os.getenv(k)
        if v:
            return v
    return default

def rfc_connect():
    import pyrfc
    params = {
        "ashost": env("SAP_D01_ASHOST", "SAP_ASHOST", default="172.16.4.66"),
        "sysnr":  env("SAP_D01_SYSNR", "SAP_SYSNR", default="00"),
        "client": env("SAP_D01_CLIENT", "SAP_CLIENT", default="350"),
    }
    snc_mode = env("SAP_D01_SNC_MODE", "SAP_SNC_MODE")
    snc_pn   = env("SAP_D01_SNC_PARTNERNAME", "SAP_SNC_PARTNERNAME")
    if snc_mode and snc_pn:
        params["snc_mode"] = snc_mode
        params["snc_partnername"] = snc_pn
        params["snc_qop"] = env("SAP_D01_SNC_QOP", "SAP_SNC_QOP", default="9")
        print("[RFC] SNC connection to D01")
    else:
        params["user"]   = env("SAP_D01_USER", "SAP_USER")
        params["passwd"] = env("SAP_D01_PASSWORD", "SAP_PASSWORD")
        print("[RFC] Basic auth to D01")
    return pyrfc.Connection(**params)

def rfc_table(conn, table, field_names, where_clauses, max_rows=5000):
    fields  = [{"FIELDNAME": f} for f in field_names]
    options = [{"TEXT": t} for t in where_clauses]
    r = conn.call(
        "RFC_READ_TABLE",
        QUERY_TABLE=table,
        FIELDS=fields,
        OPTIONS=options,
        ROWCOUNT=max_rows,
        ROWSKIPS=0,
        DELIMITER="|",
    )
    rows = []
    for row in r.get("DATA", []):
        wa = row.get("WA", "")
        parts = wa.split("|")
        if len(parts) == len(field_names):
            rows.append({field_names[i]: parts[i].strip() for i in range(len(field_names))})
    return rows

def main():
    transports = ["D01K9B0CBF", "D01K9B0CBG"]
    conn = rfc_connect()

    result = {}

    for trk in transports:
        print(f"\n--- {trk} ---")

        # E070 header
        headers = rfc_table(conn, "E070",
            ["TRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER", "AS4DATE", "AS4TIME", "STRKORR", "KORRDEV"],
            [f"TRKORR = '{trk}'"])

        # E07T description (E070T not readable via RFC in D01)
        try:
            texts = rfc_table(conn, "E07T",
                ["TRKORR", "AS4TEXT"],
                [f"TRKORR = '{trk}'", "AND LANGU = 'E'"])
        except Exception:
            texts = []

        # E071 objects
        objects = rfc_table(conn, "E071",
            ["TRKORR", "AS4POS", "PGMID", "OBJECT", "OBJ_NAME", "OBJFUNC", "LOCKFLAG"],
            [f"TRKORR = '{trk}'"])

        # E071K keys (for TABU objects)
        keys = rfc_table(conn, "E071K",
            ["TRKORR", "AS4POS", "PGMID", "OBJECT", "OBJNAME", "MASTERTYPE", "MASTERNAME", "TABKEY"],
            [f"TRKORR = '{trk}'"])

        result[trk] = {
            "header": headers[0] if headers else {},
            "description": texts[0].get("AS4TEXT", "") if texts else "",
            "objects": objects,
            "keys": keys,
        }

        print(f"  Header: {result[trk]['header']}")
        print(f"  Description: {result[trk]['description']}")
        print(f"  Objects: {len(objects)}")
        print(f"  Keys: {len(keys)}")
        for obj in objects:
            print(f"    {obj['PGMID']:5} {obj['OBJECT']:10} {obj['OBJ_NAME']:40} func={obj.get('OBJFUNC','')}")
        for key in keys:
            print(f"    KEY: {key['OBJNAME']:30} -> {key['TABKEY']}")

    out_path = os.path.join(os.path.dirname(__file__), "transport_adhoc_result.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to {out_path}")

if __name__ == "__main__":
    main()
