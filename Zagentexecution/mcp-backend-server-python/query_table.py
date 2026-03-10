import os
import argparse
import csv
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

def query_sap_table(table_name, options, fields=None, total_rows=1000, delimiter="|", system_id="D01"):
    # Load .env from the server directory
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)
    
    # Prefix for system-specific environment variables
    prefix = f"SAP_{system_id}_"
    
    # Fallback to generic SAP_* if specific prefix not found
    def get_env(key, default=None):
        return os.getenv(prefix + key) or os.getenv("SAP_" + key) or default

    try:
        conn_params = {
            "ashost": get_env("ASHOST"),
            "sysnr": get_env("SYSNR"),
            "client": get_env("CLIENT"),
            "user": get_env("USER"),
            "lang": get_env("LANG", "EN")
        }
        
        passwd = get_env("PASSWD") or get_env("PASSWORD")
        if passwd:
            conn_params["passwd"] = passwd

        if get_env("SNC_MODE") == "1":
            conn_params["snc_mode"] = "1"
            conn_params["snc_partnername"] = get_env("SNC_PARTNERNAME")
            conn_params["snc_qop"] = get_env("SNC_QOP", "9")
            
        conn = Connection(**conn_params)
        
        rfc_fields = []
        if fields:
            rfc_fields = [{"FIELDNAME": f.strip()} for f in fields.split(',')]

        rfc_options = []
        if options:
            rfc_options = [{"TEXT": options}]

        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE=table_name,
            DELIMITER=delimiter,
            ROWCOUNT=total_rows,
            OPTIONS=rfc_options,
            FIELDS=rfc_fields
        )
        
        all_data = result.get("DATA", [])
        field_metadata = result.get("FIELDS", [])
        headers = [f["FIELDNAME"] for f in field_metadata]
        
        # Show preview (max 100 rows)
        preview_limit = 100
        print(f"--- Table: {table_name} (System: {system_id}) (Total rows: {len(all_data)}) ---")
        print(" | ".join(headers))
        print("-" * 50)
        
        for i, row in enumerate(all_data[:preview_limit]):
            print(row['WA'])
            
        conn.close()
    except RFCError as e:
        print(f"SAP RFC Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query SAP Table")
    parser.add_argument("table", help="SAP Table Name")
    parser.add_argument("--options", help="WHERE clause")
    parser.add_argument("--fields", help="Comma-separated fields")
    parser.add_argument("--total_rows", type=int, default=1000)
    parser.add_argument("--system", default="D01", help="Target system (D01, P01)")
    
    args = parser.parse_args()
    query_sap_table(args.table, args.options, args.fields, args.total_rows, system_id=args.system)
