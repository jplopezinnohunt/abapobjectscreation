from sap_utils import get_sap_connection
import json

def search_hcm_services():
    try:
        conn = get_sap_connection()
        print("Connected to SAP. Searching for UNESCO HCM OData extensions...")
        
        # 1. Search for all IWSV (OData) starting with Z or Y related to HCM
        queries = [
            "OBJECT = 'IWSV' AND ( OBJ_NAME LIKE 'Z_HCMFAB%' OR OBJ_NAME LIKE 'ZHR%' )",
            "OBJECT = 'WAPA' AND ( OBJ_NAME LIKE 'Z_HCMFAB%' OR OBJ_NAME LIKE 'ZHR%' )"
        ]
        
        for query in queries:
            print(f"\n--- Searching TADIR: {query} ---")
            result = conn.call('RFC_READ_TABLE', 
                               QUERY_TABLE='TADIR', 
                               OPTIONS=[{'TEXT': query}],
                               FIELDS=[{'FIELDNAME': 'OBJECT'}, {'FIELDNAME': 'OBJ_NAME'}, {'FIELDNAME': 'DEVCLASS'}])
            if result['DATA']:
                for row in result['DATA']:
                    print(row['WA'])
        
        # 2. Look for the specific Semantic Object mapping in /UI2/V_ALIASSET (if it exists)
        # or /UI2/TM_CONFIG
        print("\n--- Listing ALL Semantic Objects in /UI2/TM_CONFIG (limit 50) ---")
        try:
            # /UI2/TM_CONFIG is a cluster table, might not work with RFC_READ_TABLE directly
            # Let's try /UI2/PB_C_PAGEM which we know existed from find_tm.py
            tm_result = conn.call('RFC_READ_TABLE', 
                                   QUERY_TABLE='/UI2/PB_C_PAGEM', 
                                   OPTIONS=[{'TEXT': "CATALOG_ID LIKE '%HR%'"}],
                                   FIELDS=[{'FIELDNAME': 'CATALOG_ID'}, {'FIELDNAME': 'TITLE'}])
            if tm_result['DATA']:
                for row in tm_result['DATA']:
                    print(row['WA'])
        except Exception as e:
            print(f"Error: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_hcm_services()
