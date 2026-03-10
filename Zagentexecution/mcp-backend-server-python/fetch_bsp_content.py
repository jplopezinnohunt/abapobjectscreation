import sys
from sap_utils import get_sap_connection
import json
import zlib

def fetch_bsp_page_content(bsp_name, page_name):
    """
    Fetches the content of a BSP page (like manifest.json) from SAP.
    """
    try:
        conn = get_sap_connection()
        print(f"Connected to SAP successfully. Fetching {page_name} for {bsp_name}...")
        
        # In SAP BSPs, content is often stored compressed or in raw formats.
        # We will attempt to read the content through standard Function Modules.
        # Function RS_SCRP_GET_RAW_TEXT or similar might be needed, but a standard way
        # is reading from table O2PAGCON which holds the page content.
        
        # Query O2PAGDIR to get the PAGEKEY mapping if needed
        pages_result = conn.call('RFC_READ_TABLE', 
                           QUERY_TABLE='O2PAGDIR', 
                           OPTIONS=[{'TEXT': f"APPLNAME = '{bsp_name}' AND PAGENAME = '{page_name}'"}],
                           FIELDS=[{'FIELDNAME': 'PAGEKEY'}, {'FIELDNAME': 'PAGENAME'}, {'FIELDNAME': 'MIMETYPE'}])
        
        if not pages_result['DATA']:
             print(f"File {page_name} not found in application {bsp_name}.")
             return

        page_info = pages_result['DATA'][0]['WA'].strip()
        print(f"Page found: {page_info}")
        
        # Query O2PAGCON to get the actual content
        print(f"Fetching content from O2PAGCON...")
        content_result = conn.call('RFC_READ_TABLE', 
                           QUERY_TABLE='O2PAGCON', 
                           OPTIONS=[{'TEXT': f"APPLNAME = '{bsp_name}' AND PAGENAME = '{page_name}'"}],
                           FIELDS=[{'FIELDNAME': 'PAGELINE'}])
        
        if content_result['DATA']:
             print("\n--- Content Snippet ---")
             full_content = ""
             for row in content_result['DATA']:
                 full_content += row['WA']
             
             # Attempt to parse as JSON if it's manifest
             try:
                 # SAP sometimes pads text or stores it weirdly, let's just print the raw first
                 print(full_content[:2000]) # Print first 2000 chars

                 # And try to extract the service names
                 if "dataSources" in full_content:
                     print("\n--- Found dataSources in JSON ---")
             except Exception as json_e:
                 print(f"Failed to parse content. Raw dump: {full_content[:500]}")
        else:
             print("No content found in O2PAGCON.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        fetch_bsp_page_content(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python fetch_bsp_content.py APP_NAME FILE_NAME")
        print("Example: python fetch_bsp_content.py ZHROFFBOARDING manifest.json")
