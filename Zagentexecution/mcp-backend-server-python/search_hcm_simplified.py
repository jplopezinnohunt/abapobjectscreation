from sap_utils import get_sap_connection
import json

def search_hcm_simplified():
    try:
        conn = get_sap_connection()
        print("Connected to SAP. Simplified search...")
        
        queries = [
            "OBJECT = 'IWSV' AND OBJ_NAME LIKE 'Z_HCMFAB%'",
            "OBJECT = 'IWSV' AND OBJ_NAME LIKE 'ZHR%'",
            "OBJECT = 'WAPA' AND OBJ_NAME LIKE 'Z_HCMFAB%'",
            "OBJECT = 'WAPA' AND OBJ_NAME LIKE 'ZHR%'"
        ]
        
        for q in queries:
            print(f"\n--- Query: {q} ---")
            result = conn.call('RFC_READ_TABLE', 
                               QUERY_TABLE='TADIR', 
                               OPTIONS=[{'TEXT': q}],
                               FIELDS=[{'FIELDNAME': 'OBJ_NAME'}, {'FIELDNAME': 'DEVCLASS'}])
            if result['DATA']:
                for row in result['DATA']:
                    print(row['WA'])
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_hcm_simplified()
