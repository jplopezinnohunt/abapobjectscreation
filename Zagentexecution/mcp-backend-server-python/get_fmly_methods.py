from sap_utils import get_sap_connection
import json

def get_class_methods(class_name):
    try:
        conn = get_sap_connection()
        print(f"Connected to SAP. Getting methods for {class_name}...")
        
        # Table TMDIR contains class methods
        result = conn.call('RFC_READ_TABLE', 
                           QUERY_TABLE='TMDIR', 
                           OPTIONS=[{'TEXT': f"CLSNAME = '{class_name}'"}],
                           FIELDS=[{'FIELDNAME': 'CMPNAME'}])
        
        if result['DATA']:
            print(f"\n--- Methods in {class_name} ---")
            for row in result['DATA']:
                print(row['WA'])
        else:
            print(f"No methods found for {class_name} in TMDIR.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_class_methods("ZCL_HCMFAB_B_MYFAMILYMEMBERS")
