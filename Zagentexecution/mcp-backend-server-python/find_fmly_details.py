from sap_utils import get_sap_connection
import json

def get_app_details(semantic_object):
    try:
        conn = get_sap_connection()
        print(f"Connected to SAP. Searching for Semantic Object: {semantic_object}")
        
        # 1. Search in /UI2/PB_C_TMAP for Target Mapping
        # This table contains semantic objects and actions mapped to BSP applications.
        # FIELDS: SEMANTIC_OBJECT, SEMANTIC_ACTION, URL, APP_ID, APPLICATION_TYPE
        
        # Note: /UI2/PB_C_TMAP is a cluster/config table, might be easier to check /UI2/V_ALIASSET in some versions
        # or /UI2/TM_CONFIG. Let's try /UI2/PB_C_TMAP first.
        
        print("\n--- Searching /UI2/PB_C_TMAP ---")
        options = [
            {'TEXT': f"SEMANTIC_OBJ = '{semantic_object}'"},
            {'TEXT': " AND SEMANTIC_ACT = 'display'"}
        ]
        
        result = conn.call('RFC_READ_TABLE', 
                           QUERY_TABLE='/UI2/PB_C_TMAP', 
                           OPTIONS=options,
                           FIELDS=[
                               {'FIELDNAME': 'SEMANTIC_OBJ'}, 
                               {'FIELDNAME': 'SEMANTIC_ACT'}, 
                               {'FIELDNAME': 'URL'}, # This often contains the BSP path
                               {'FIELDNAME': 'APP_ID'}
                           ])
        
        if result['DATA']:
            for row in result['DATA']:
                print(f"Target Mapping Found: {row['WA']}")
        else:
            print(f"No match for {semantic_object} in /UI2/PB_C_TMAP.")
            
            # 2. Try searching in TADIR for any WAPA (BSP) matching YHR*FMLY*
            print("\n--- Searching TADIR for BSP applications (WAPA) ---")
            tadir_options = [{'TEXT': "OBJECT = 'WAPA' AND OBJ_NAME LIKE 'YHR%FMLY%'"}]
            tadir_result = conn.call('RFC_READ_TABLE', 
                                    QUERY_TABLE='TADIR', 
                                    OPTIONS=tadir_options,
                                    FIELDS=[{'FIELDNAME': 'OBJ_NAME'}, {'FIELDNAME': 'DEVCLASS'}])
            if tadir_result['DATA']:
                for row in tadir_result['DATA']:
                    print(f"Potential BSP Found: {row['WA']}")
            else:
                print("No BSP found in TADIR.")

        # 3. Search for OData services in /IWFND/I_MED_SRV or /IWBEP/I_MGW_SRH
        print("\n--- Searching for OData Services (ZHR*FMLY*) ---")
        srv_options = [{'TEXT': "TECHNICAL_NAME LIKE 'ZHR%FMLY%'"}]
        # Trying /IWFND/I_MED_SRV (OData service registration)
        try:
            srv_result = conn.call('RFC_READ_TABLE', 
                                   QUERY_TABLE='/IWFND/I_MED_SRV', 
                                   OPTIONS=srv_options,
                                   FIELDS=[{'FIELDNAME': 'TECHNICAL_NAME'}, {'FIELDNAME': 'VERSION'}])
            if srv_result['DATA']:
                for row in srv_result['DATA']:
                    print(f"OData Service Found: {row['WA']}")
            else:
                 print("No OData services found in /IWFND/I_MED_SRV.")
        except Exception as e:
            print(f"Error querying /IWFND/I_MED_SRV: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_app_details("YHR_FMLY_MAN")
