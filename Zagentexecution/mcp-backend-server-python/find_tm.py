import sys
from sap_utils import get_sap_connection
import json

def find_app_mapping(search_term):
    """
    Search Fiori App mappings in /UI2/ tables
    """
    try:
        conn = get_sap_connection()
        print(f"Connected to SAP successfully. Searching Launchpad Maps for '{search_term}'...")
        
        # Searching Launchpad catalogs /UI2/PB_C_PAGEM /UI2/PB_C_PAGE
        
        try:
             print("\n--- Searching /UI2/PB_C_PAGEM (Page/Catalog Items) ---")
             tm_result = conn.call('RFC_READ_TABLE', 
                               QUERY_TABLE='/UI2/PB_C_PAGEM', 
                               OPTIONS=[{'TEXT': f"CATALOG_ID LIKE '%{search_term}%' OR TITLE LIKE '%{search_term}%'"}],
                               FIELDS=[{'FIELDNAME': 'CATALOG_ID'}, {'FIELDNAME': 'PAGE_ID'}])
             if tm_result['DATA']:
                 for row in tm_result['DATA']:
                     print(row['WA'])
             else:
                  print("No semantic objects found.")
        except Exception as e1:
            print(f"Error querying /UI2/: {e1}")

        # Try to find exactly what OData services exist in the system matching ZHR*
        try:
             print("\n--- Listing ALL ZHR* OData Services ---")
             # Try other table if /IWBEP/I_MGW_SRH was empty. Let's try /IWBEP/I_SBD_SV
             srv_result = conn.call('RFC_READ_TABLE', 
                               QUERY_TABLE='/IWBEP/I_SBD_SV', 
                               OPTIONS=[{'TEXT': "SERVICE_NAME LIKE 'ZHR%OFF%'"}],
                               FIELDS=[{'FIELDNAME': 'PROJECT'}, {'FIELDNAME': 'SERVICE_NAME'}])
             if srv_result['DATA']:
                 for row in srv_result['DATA']:
                     print(row['WA'])
             else:
                  print("No services found in /IWBEP/I_SBD_SV.")
        except Exception as e2:
             print(f"Error: {e2}")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    find_app_mapping("yhrappoffboardingemp")
