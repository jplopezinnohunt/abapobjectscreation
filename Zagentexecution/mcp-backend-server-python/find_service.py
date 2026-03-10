import sys
from sap_utils import get_sap_connection
import json

def find_odata_services(search_term):
    """
    Search for OData services in the SAP Gateway mapping tables.
    """
    try:
        conn = get_sap_connection()
        print(f"Connected to SAP successfully. Searching OData Services for '{search_term}'...")
        
        # In SAP Gateway, services are registered in /IWBEP/I_SBD_GA (Service Builder Project)
        # or /IWBEP/I_SBD_MV (Model to Service Mapping) or simply the base catalog
        # Let's try to query /IWBEP/I_MGW_SRH (Service Header) or /IWBEP/I_SBD_GA
        
        try:
             print("\n--- Searching /IWBEP/I_SBD_GA (Projects) ---")
             proj_result = conn.call('RFC_READ_TABLE', 
                               QUERY_TABLE='/IWBEP/I_SBD_GA', 
                               OPTIONS=[{'TEXT': f"PROJECT LIKE '%{search_term}%' OR DESCRIPTION LIKE '%{search_term}%'"}],
                               FIELDS=[{'FIELDNAME': 'PROJECT'}, {'FIELDNAME': 'DESCRIPTION'}])
             if proj_result['DATA']:
                 for row in proj_result['DATA']:
                     print(row['WA'])
             else:
                  print("No projects found matching search term.")
        except Exception as e1:
            print(f"Error querying /IWBEP/I_SBD_GA: {e1}")

        # Let's also check standard TSTC if a specific transation was tied
        # Or look into /IWBEP/I_MGW_SRH
        try:
             print("\n--- Searching /IWBEP/I_MGW_SRH (Services) ---")
             srv_result = conn.call('RFC_READ_TABLE', 
                               QUERY_TABLE='/IWBEP/I_MGW_SRH', 
                               OPTIONS=[{'TEXT': f"TECHNICAL_NAME LIKE '%{search_term}%'"}],
                               FIELDS=[{'FIELDNAME': 'TECHNICAL_NAME'}, {'FIELDNAME': 'VERSION'}, {'FIELDNAME': 'CLASS_MDP'}])
             if srv_result['DATA']:
                 for row in srv_result['DATA']:
                     print(row['WA'])
             else:
                  print("No services found in /IWBEP/I_MGW_SRH matching search term.")
        except Exception as e2:
             print(f"Error querying /IWBEP/I_MGW_SRH: {e2}")
             
        # HR specific check:
        print("\n--- Searching /IWBEP/I_MGW_SRH for HR* Services ---")
        try:
             hr_srv_result = conn.call('RFC_READ_TABLE', 
                               QUERY_TABLE='/IWBEP/I_MGW_SRH', 
                               OPTIONS=[{'TEXT': f"TECHNICAL_NAME LIKE 'ZHR%OFF%' OR TECHNICAL_NAME LIKE 'ZHR_%OFF%'"}],
                               FIELDS=[{'FIELDNAME': 'TECHNICAL_NAME'}, {'FIELDNAME': 'VERSION'}, {'FIELDNAME': 'CLASS_MDP'}])
             if hr_srv_result['DATA']:
                 for row in hr_srv_result['DATA']:
                     print(row['WA'])
             else:
                  print("No specific HR offboarding services identified based on name match.")
        except Exception as e3:
             pass

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        find_odata_services(sys.argv[1])
    else:
        print("Usage: python find_service.py SEARCH_TERM")
