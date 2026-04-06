import sys
import os

# Add the mcp-backend-server-python directory to the path to import sap_utils
sys.path.append(r'c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python')

from sap_utils import get_sap_connection

def main():
    try:
        conn = get_sap_connection()
        print("Connected to SAP.")
        fields = [{'FIELDNAME': 'REQUEST_TYPE'}]
        # Querying the table directly via pyrfc to avoid query_table.py overhead
        results = conn.call('RFC_READ_TABLE', 
                           QUERY_TABLE='ZTHRFIORI_UI5PRO', 
                           FIELDS=fields)
        
        unique_types = set()
        for row in results['DATA']:
            unique_types.add(row['WA'].strip())
        
        print("Unique REQUEST_TYPE values in ZTHRFIORI_UI5PRO:")
        for t in sorted(unique_types):
            print(f" - {t}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
