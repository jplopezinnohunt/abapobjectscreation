from sap_utils import get_sap_connection
import json

def find_classes():
    try:
        conn = get_sap_connection()
        print("Connected to SAP. Searching for DPC/MPC classes for Z_HCM_FAMILY...")
        
        # Searching TADIR for classes related to the OData service
        # Service name: Z_HCMFAB_MYFAMILYMEMBERS_SRV
        # Expected classes: ZCL_Z_HCMFAB_MYFAMILY_DPC_EXT, ZCL_Z_HCMFAB_MYFAMILY_MPC_EXT
        tadir_query = "OBJECT = 'CLAS' AND OBJ_NAME LIKE 'ZCL_Z_HCMFAB_MYFAM%'"
        
        print(f"\n--- Searching TADIR: {tadir_query} ---")
        result = conn.call('RFC_READ_TABLE', 
                           QUERY_TABLE='TADIR', 
                           OPTIONS=[{'TEXT': tadir_query}],
                           FIELDS=[{'FIELDNAME': 'OBJ_NAME'}, {'FIELDNAME': 'DEVCLASS'}])
        if result['DATA']:
            for row in result['DATA']:
                print(row['WA'])
        else:
            print("No classes found specifically matching that pattern.")
            
        # Broaden search
        print("\n--- Broadening search for CLAS like *HCMFAB*FAMILY* ---")
        broad_query = "OBJECT = 'CLAS' AND OBJ_NAME LIKE '%HCMFAB%FAM%'"
        result2 = conn.call('RFC_READ_TABLE', 
                            QUERY_TABLE='TADIR', 
                            OPTIONS=[{'TEXT': broad_query}],
                            FIELDS=[{'FIELDNAME': 'OBJ_NAME'}, {'FIELDNAME': 'DEVCLASS'}])
        if result2['DATA']:
            for row in result2['DATA']:
                print(row['WA'])

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_classes()
