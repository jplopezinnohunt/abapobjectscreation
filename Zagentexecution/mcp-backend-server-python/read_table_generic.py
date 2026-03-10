import os
import argparse
import csv
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

def read_sap_table(table_name, total_rows=100, batch_size=50000, fields=None, delimiter="|", output_csv=None, system_id="D01"):
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

        all_data = []
        rows_fetched = 0
        
        current_rows_to_fetch = min(total_rows, batch_size)
        
        while rows_fetched < total_rows:
            batch_count = min(batch_size, total_rows - rows_fetched)
            
            result = conn.call(
                "RFC_READ_TABLE",
                QUERY_TABLE=table_name,
                DELIMITER=delimiter,
                ROWCOUNT=batch_count,
                ROWSKIPS=rows_fetched, 
                FIELDS=rfc_fields
            )
            
            batch_data = result.get("DATA", [])
            if not batch_data:
                break
                
            all_data.extend(batch_data)
            rows_fetched += len(batch_data)
            
            if len(batch_data) < batch_count:
                break 
        
        field_metadata = result.get("FIELDS", [])
        headers = [f["FIELDNAME"] for f in field_metadata]
        
        if output_csv:
            with open(output_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in all_data:
                    writer.writerow(row['WA'].split(delimiter))
            print(f"Successfully saved {len(all_data)} rows to {output_csv}")

        preview_limit = 100
        print(f"--- Table: {table_name} (System: {system_id}) (Total rows: {len(all_data)}) ---")
        print(" | ".join(headers))
        print("-" * 50)
        
        for i, row in enumerate(all_data[:preview_limit]):
            print(row['WA'])
            
        if len(all_data) > preview_limit:
            print(f"... and {len(all_data) - preview_limit} more rows hidden in preview.")
            
        conn.close()
    except RFCError as e:
        print(f"SAP RFC Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read any SAP Table via RFC with Batching")
    parser.add_argument("table", help="SAP Table Name")
    parser.add_argument("--total_rows", type=int, default=100, help="Total rows to fetch")
    parser.add_argument("--batch_size", type=int, default=50000, help="Rows per batch")
    parser.add_argument("--fields", help="Comma-separated fields")
    parser.add_argument("--output", help="Optional CSV output file path")
    parser.add_argument("--system", default="D01", help="Target system (D01, P01)")
    
    args = parser.parse_args()
    read_sap_table(args.table, args.total_rows, args.batch_size, args.fields, "|", args.output, system_id=args.system)
