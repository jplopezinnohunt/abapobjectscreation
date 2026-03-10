from sap_utils import get_sap_connection
import json

def check_redefs():
    try:
        conn = get_sap_connection()
        print("Connected to SAP. Checking redefinitions for ZCL_HCMFAB_B_MYFAMILYMEMBERS...")
        
        result = conn.call('RFC_READ_TABLE', 
                           QUERY_TABLE='SEOREDEF', 
                           OPTIONS=[{'TEXT': "CLSNAME = 'ZCL_HCMFAB_B_MYFAMILYMEMBERS'"}],
                           FIELDS=[{'FIELDNAME': 'MTDNAME'}])
        
        if result['DATA']:
            for row in result['DATA']:
                print(row['WA'])
        else:
            print("No redefinitions found in SEOREDEF.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_redefs()
