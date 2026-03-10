from sap_utils import get_sap_connection
import json

def search_broadly():
    try:
        conn = get_sap_connection()
        print("Connected to SAP. Broad search for FMLY/FAMILY related objects...")
        
        # 1. Search OData Services by technically name or description
        print("\n--- Searching /IWFND/I_MED_SRV for *FMLY* or *FAMILY* ---")
        srv_result = conn.call('RFC_READ_TABLE', 
                               QUERY_TABLE='/IWFND/I_MED_SRV', 
                               OPTIONS=[{'TEXT': "SRV_IDENTIFIER LIKE '%FMLY%' OR SRV_IDENTIFIER LIKE '%FAMILY%'"}],
                               FIELDS=[{'FIELDNAME': 'TECHNICAL_NAME'}, {'FIELDNAME': 'VERSION'}])
        if srv_result['DATA']:
            for row in srv_result['DATA']:
                print(row['WA'])
        else:
            print("No matches in /IWFND/I_MED_SRV.")

        # 2. Search TADIR for WAPA (BSP) containing FMLY or FAMILY
        print("\n--- Searching TADIR for WAPA containing FMLY or FAMILY ---")
        tadir_result = conn.call('RFC_READ_TABLE', 
                                 QUERY_TABLE='TADIR', 
                                 OPTIONS=[{'TEXT': "OBJECT = 'WAPA' AND ( OBJ_NAME LIKE '%FMLY%' OR OBJ_NAME LIKE '%FAMILY%' )"}],
                                 FIELDS=[{'FIELDNAME': 'OBJ_NAME'}, {'FIELDNAME': 'DEVCLASS'}])
        if tadir_result['DATA']:
            for row in tadir_result['DATA']:
                print(row['WA'])
        else:
            print("No matches in TADIR (WAPA).")

        # 3. Search for the Semantic Object in /UI2/TM_CONFIG (Target Mapping)
        # Some systems use /UI2/TM_CONFIG
        print("\n--- Searching /UI2/NWBC_CFG for 'FMLY' ---")
        try:
            nwbc_result = conn.call('RFC_READ_TABLE', 
                                     QUERY_TABLE='/UI2/NWBC_CFG', 
                                     OPTIONS=[{'TEXT': "VALUE LIKE '%FMLY%'"}],
                                     FIELDS=[{'FIELDNAME': 'VALUE'}])
            if nwbc_result['DATA']:
                for row in nwbc_result['DATA']:
                    print(row['WA'])
        except Exception:
            pass

        # 4. Search for the Semantic Object in /UI2/PB_C_TMAP if it was a view
        print("\n--- Searching /UI2/PB_C_TMAP again (as a view check) ---")
        try:
            tmap_result = conn.call('RFC_READ_TABLE', 
                                     QUERY_TABLE='/UI2/PB_C_TMAP', 
                                     OPTIONS=[{'TEXT': "SEMANTIC_OBJ LIKE '%FMLY%'"}] ,
                                     FIELDS=[{'FIELDNAME': 'SEMANTIC_OBJ'}, {'FIELDNAME': 'SEMANTIC_ACT'}, {'FIELDNAME': 'URL'}])
            if tmap_result['DATA']:
                for row in tmap_result['DATA']:
                    print(row['WA'])
        except Exception:
            print("Table /UI2/PB_C_TMAP not available (likely restricted or wrong name).")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_broadly()
