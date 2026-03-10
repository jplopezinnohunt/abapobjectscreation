import sys
from sap_utils import get_sap_connection
import json

def find_icf_service():
    """
    Search ICF nodes
    """
    try:
        conn = get_sap_connection()
        print(f"Connected to SAP successfully. Searching ICF Nodes...")
        
        # Searching ICF nodes which always records activated services
        try:
             print("\n--- Searching ICFSERVICE for ZHR* ---")
             tm_result = conn.call('RFC_READ_TABLE', 
                               QUERY_TABLE='ICFSERVICE', 
                               OPTIONS=[{'TEXT': "ICF_NAME LIKE 'ZHR%OFF%' OR ICF_NAME LIKE '%OFFBOARD%'" }],
                               FIELDS=[{'FIELDNAME': 'ICF_NAME'}, {'FIELDNAME': 'ICF_ALTRT'}])
             if tm_result['DATA']:
                 for row in tm_result['DATA']:
                     print(row['WA'])
             else:
                  print("No ICF nodes found matching.")
        except Exception as e1:
            print(f"Error querying ICFSERVICE: {e1}")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    find_icf_service()
