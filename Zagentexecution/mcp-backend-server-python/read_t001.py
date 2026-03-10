import os
from sap_utils import get_sap_connection

def read_t001():
    try:
        conn = get_sap_connection()
        
        # Read T001 (Company Codes)
        # RFC_READ_TABLE returns a list of fields and data
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="T001",
            DELIMITER="|",
            ROWCOUNT=10,
            FIELDS=[{"FIELDNAME": "BUKRS"}, {"FIELDNAME": "BUTXT"}, {"FIELDNAME": "ORT01"}, {"FIELDNAME": "WAERS"}]
        )
        
        data = result.get("DATA", [])
        if not data:
            print("No data found in T001.")
        else:
            print(f"--- Top 10 Company Codes from T001 (Client {os.getenv('SAP_CLIENT')}) ---")
            print("Code | Company Name           | City            | Curr")
            print("-" * 60)
            for row in data:
                # Fields were requested in order: BUKRS, BUTXT, ORT01, WAERS
                vals = row['WA'].split('|')
                if len(vals) >= 4:
                    print(f"{vals[0].strip():4} | {vals[1].strip():20} | {vals[2].strip():15} | {vals[3].strip()}")
                else:
                    print(row['WA'])
        
        conn.close()
    except Exception as e:
        print(f"Error reading T001: {str(e)}")

if __name__ == "__main__":
    read_t001()
