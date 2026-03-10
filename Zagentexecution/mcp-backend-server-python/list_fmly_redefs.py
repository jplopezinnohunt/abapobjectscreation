from sap_utils import get_sap_connection
import json

def list_redefined_methods(class_name):
    try:
        conn = get_sap_connection()
        print(f"Connected to SAP. Checking redefinitions for {class_name}...")
        
        # Table SEOREDEF contains method redefinitions
        # FIELDS: CLSNAME, REFCLSNAME, MTDNAME
        result = conn.call('RFC_READ_TABLE', 
                           QUERY_TABLE='SEOREDEF', 
                           OPTIONS=[{'TEXT': f"CLSNAME = '{class_name}'"}],
                           FIELDS=[{'FIELDNAME': 'MTDNAME'}, {'FIELDNAME': 'REFCLSNAME'}])
        
        if result['DATA']:
            print(f"\n--- Redefined Methods in {class_name} ---")
            for row in result['DATA']:
                print(row['WA'])
        else:
            print(f"No redefinitions found for {class_name} in SEOREDEF.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_redefined_methods("ZCL_Z_HCMFAB_MYFAMILYM_DPC_EXT")
    print("-" * 40)
    list_redefined_methods("ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT")
