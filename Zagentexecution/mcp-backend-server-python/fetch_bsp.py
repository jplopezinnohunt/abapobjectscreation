import sys
from sap_utils import get_sap_connection
import json

def fetch_bsp_app_info(bsp_name):
    """
    Fetches information about a BSP application from SAP tables.
    """
    try:
        conn = get_sap_connection()
        print(f"Connected to SAP successfully. Fetching info for {bsp_name}...")
        
        # Query O2PAGDIR (Pages of BSP Application) without INACTIVE field
        print(f"\n--- Pages / Files in O2PAGDIR ---")
        pages_result = conn.call('RFC_READ_TABLE', 
                           QUERY_TABLE='O2PAGDIR', 
                           OPTIONS=[{'TEXT': f"APPLNAME = '{bsp_name}' AND PAGENAME LIKE '%manifest.json%'"}],
                           FIELDS=[{'FIELDNAME': 'PAGEKEY'}, {'FIELDNAME': 'PAGENAME'}, {'FIELDNAME': 'MIMETYPE'}])
        
        if pages_result['DATA']:
             for row in pages_result['DATA']:
                 print(row['WA'])
        else:
             print("No manifest.json found in O2PAGDIR. Trying full extract...")
             pages_all_result = conn.call('RFC_READ_TABLE', 
                           QUERY_TABLE='O2PAGDIR', 
                           OPTIONS=[{'TEXT': f"APPLNAME = '{bsp_name}'"}],
                           FIELDS=[{'FIELDNAME': 'PAGEKEY'}, {'FIELDNAME': 'PAGENAME'}, {'FIELDNAME': 'MIMETYPE'}])
             if pages_all_result['DATA']:
                 for row in pages_all_result['DATA']:
                     print(row['WA'])
             else:
                  print("No pages found in O2PAGDIR.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fetch_bsp_app_info(sys.argv[1])
    else:
        print("Please provide a BSP app name. Example: python fetch_bsp.py ZHROFFBOARDING")
