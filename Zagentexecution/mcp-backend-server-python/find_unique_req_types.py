import sys
from sap_utils import get_sap_connection

def find_unique_req_types():
    try:
        conn = get_sap_connection()
        print(f"Connected to SAP. Reading ZTHRFIORI_UI5PRO...")
        result = conn.call('RFC_READ_TABLE', 
                           QUERY_TABLE='ZTHRFIORI_UI5PRO', 
                           FIELDS=[{'FIELDNAME': 'REQUEST_TYPE'}])
        
        unique_types = set()
        for row in result['DATA']:
            unique_types.add(row['WA'].strip())
            
        print(f"Unique Request Types found: {sorted(list(unique_types))}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    find_unique_req_types()
