import sys
import os
from sap_utils import get_sap_connection

def extract_class_methods(class_name, output_dir="extracted_code"):
    """
    Extracts all method source codes for a given ABAP class and saves them to files.
    """
    try:
        conn = get_sap_connection()
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        class_dir = os.path.join(output_dir, class_name)
        if not os.path.exists(class_dir):
            os.makedirs(class_dir)

        print(f"Connected to SAP. Searching TRDIR for {class_name} methods...")
        search_pattern = f"{class_name}%CM%"
        
        dir_result = conn.call('RFC_READ_TABLE', 
                           QUERY_TABLE='TRDIR', 
                           OPTIONS=[{'TEXT': f"NAME LIKE '{search_pattern}'"}],
                           FIELDS=[{'FIELDNAME': 'NAME'}])
        
        includes = [row['WA'].strip() for row in dir_result.get('DATA', [])]
        
        if not includes:
            print(f"No method includes found for {class_name}.")
            return

        print(f"Found {len(includes)} method includes. Extracting...")
        
        for inc in includes:
            try:
                src_result = conn.call("SIW_RFC_READ_REPORT", I_NAME=inc)
                lines = src_result.get("E_TAB_CODE", [])
                
                if lines:
                    # Detect method name from the first few lines
                    method_name = f"method_{inc[-3:]}" # Default to CMxxx
                    for line in lines[:20]:
                        if 'METHOD ' in line.upper():
                            # Extract method name: METHOD /IWBEP/IF_MGW_APPL_SRV_RUNTIME~EXECUTE_ACTION.
                            parts = line.strip().split()
                            if len(parts) > 1:
                                method_name = parts[1].replace('.', '').replace('~', '_').replace('/', '_')
                            break
                    
                    filename = os.path.join(class_dir, f"{method_name}.abap")
                    with open(filename, 'w', encoding='utf-8') as f:
                        for line in lines:
                            f.write(line + "\n")
                    print(f"  - Saved {method_name} ({inc})")
                    
            except Exception as read_err:
                print(f"  - Error reading {inc}: {read_err}")

        print(f"\nAll methods for {class_name} saved to {class_dir}")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        extract_class_methods(sys.argv[1])
    else:
        print("Usage: python extract_methods.py CLASS_NAME")
