from sap_utils import get_sap_connection
import json

def find_badi_impl():
    try:
        conn = get_sap_connection()
        print("Connected to SAP. Searching for HCMFAB_B_MYFAMILYMEMBERS BAdI implementations...")
        
        # 1. Search for implementation in SXC_IMPL (Classic BAdI or some Kernal BAdIs)
        print("\n--- Searching SXC_IMPL for *MYFAMILYMEMBERS* ---")
        try:
            sxc_result = conn.call('RFC_READ_TABLE', 
                                   QUERY_TABLE='SXC_IMPL', 
                                   OPTIONS=[{'TEXT': "EXIT_NAME LIKE '%MYFAMILYMEMBERS%'"}],
                                   FIELDS=[{'FIELDNAME': 'IMP_NAME'}, {'FIELDNAME': 'EXIT_NAME'}, {'FIELDNAME': 'IMP_CLASS'}])
            if sxc_result['DATA']:
                for row in sxc_result['DATA']:
                    print(row['WA'])
        except Exception as e:
            print(f"Error: {e}")

        # 2. Search for implementation in ENHOBJ (New Kernel BAdIs)
        print("\n--- Searching ENHOBJ for *MYFAMILYMEMBERS* ---")
        try:
            enh_result = conn.call('RFC_READ_TABLE', 
                                   QUERY_TABLE='ENHOBJ', 
                                   OPTIONS=[{'TEXT': "OBJ_NAME LIKE '%MYFAMILYMEMBERS%'"}],
                                   FIELDS=[{'FIELDNAME': 'ENHNAME'}, {'FIELDNAME': 'OBJ_NAME'}, {'FIELDNAME': 'OBJ_TYPE'}])
            if enh_result['DATA']:
                for row in enh_result['DATA']:
                    print(row['WA'])
        except Exception as e:
            print(f"Error: {e}")

        # 3. Check specific UNESCO implementation name if it follows previous pattern
        # Previous was ZHCMFAB_MYPERSONALDATA. Maybe ZHCMFAB_MYFAMILYMEMBERS?
        print("\n--- Searching TADIR for ZHCMFAB*FAMILY* ---")
        tadir_result = conn.call('RFC_READ_TABLE', 
                                 QUERY_TABLE='TADIR', 
                                 OPTIONS=[{'TEXT': "OBJ_NAME LIKE 'ZHCMFAB%FAMILY%'"}],
                                 FIELDS=[{'FIELDNAME': 'OBJ_NAME'}, {'FIELDNAME': 'OBJECT'}, {'FIELDNAME': 'DEVCLASS'}])
        if tadir_result['DATA']:
            for row in tadir_result['DATA']:
                print(row['WA'])

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_badi_impl()
