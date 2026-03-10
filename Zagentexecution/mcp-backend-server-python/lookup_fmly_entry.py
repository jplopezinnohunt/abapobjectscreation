from sap_utils import get_sap_connection
import json

def lookup_entry_points():
    try:
        conn = get_sap_connection()
        print("Connected to SAP. Searching for YHR_FMLY_MAN entry points...")
        
        # 1. TADIR Lookup for BSP (WAPA) and OData (IWSV)
        tadir_queries = [
            "OBJECT = 'WAPA' AND OBJ_NAME LIKE 'YHR%FMLY%'",
            "OBJECT = 'WAPA' AND OBJ_NAME LIKE 'ZHR%FMLY%'",
            "OBJECT = 'IWSV' AND OBJ_NAME LIKE 'ZHR%FMLY%'",
            "OBJECT = 'IWSV' AND OBJ_NAME LIKE 'ZHR%FAMILY%'"
        ]
        
        for query in tadir_queries:
            print(f"\n--- Searching TADIR: {query} ---")
            result = conn.call('RFC_READ_TABLE', 
                               QUERY_TABLE='TADIR', 
                               OPTIONS=[{'TEXT': query}],
                               FIELDS=[{'FIELDNAME': 'OBJECT'}, {'FIELDNAME': 'OBJ_NAME'}, {'FIELDNAME': 'DEVCLASS'}])
            if result['DATA']:
                for row in result['DATA']:
                    print(row['WA'])
        
        # 2. Launchpad Mapping
        # Table /UI2/V_ALIASSET or searching in /UI2/TM_CONFIG
        print("\n--- Searching /UI2/V_ALIASSET for Semantic Object YHR_FMLY_MAN ---")
        try:
            alias_result = conn.call('RFC_READ_TABLE', 
                                     QUERY_TABLE='/UI2/V_ALIASSET', 
                                     OPTIONS=[{'TEXT': "SEMANTIC_OBJECT = 'YHR_FMLY_MAN'"}],
                                     FIELDS=[{'FIELDNAME': 'SEMANTIC_OBJECT'}, {'FIELDNAME': 'SEMANTIC_ACTION'}, {'FIELDNAME': 'URL'}, {'FIELDNAME': 'APP_ID'}])
            if alias_result['DATA']:
                for row in alias_result['DATA']:
                    print(row['WA'])
            else:
                print("No alias found in /UI2/V_ALIASSET.")
        except Exception as e:
            print(f"Error querying /UI2/V_ALIASSET: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    lookup_entry_points()
