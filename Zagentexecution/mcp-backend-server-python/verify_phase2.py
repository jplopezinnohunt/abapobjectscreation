import os
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

def verify_phase2():
    load_dotenv()
    ashost = os.getenv("SAP_ASHOST")
    user = os.getenv("SAP_USER")
    
    print(f"Verifying Phase 2 Tools for SAP System ({ashost})...")
    
    try:
        conn_params = {
            "ashost": ashost,
            "sysnr": os.getenv("SAP_SYSNR"),
            "client": os.getenv("SAP_CLIENT"),
            "user": user,
            "lang": os.getenv("SAP_LANG", "EN")
        }
        
        if os.getenv("SAP_SNC_MODE") == "1":
            conn_params["snc_mode"] = "1"
            conn_params["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
            conn_params["snc_qop"] = os.getenv("SAP_SNC_QOP", "9")
            
        conn = Connection(**conn_params)
        print("[+] Connected successfully.")
        
        # 1. Test Search
        print("\n[Test 1] Searching for 'RS*' Programs...")
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="TADIR",
            DELIMITER="|",
            ROWCOUNT=5,
            OPTIONS=[{"TEXT": "OBJ_NAME LIKE 'RS*' AND OBJECT = 'PROG'"}]
        )
        data = result.get("DATA", [])
        if data:
            prog_name = data[0]['WA'].split('|')[0].strip()
            print(f"Found program: {prog_name}")
            
            # 2. Test Get Source
            print(f"\n[Test 2] Reading source code for: {prog_name}...")
            source_result = conn.call("SIW_RFC_READ_REPORT", I_NAME=prog_name)
            lines = source_result.get("E_TAB_CODE", [])
            print(f"Successfully read {len(lines)} lines.")
            if lines:
                print(f"Line 1: {lines[0].get('LINE', '')}")
                
        # 3. Test Class Methods
        print("\n[Test 3] Listing methods for class 'CL_SALV_TABLE'...")
        res_class = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="SEOCOMPO",
            DELIMITER="|",
            ROWCOUNT=5,
            OPTIONS=[{"TEXT": "CLSNAME = 'CL_SALV_TABLE' AND CMPTYPE = '1'"}]
        )
        methods = res_class.get("DATA", [])
        print(f"Found {len(methods)} methods.")
        for m in methods:
            print(f"  - {m['WA'].split('|')[1].strip()}")

        conn.close()
        print("\nPhase 2 Verification Successful!")
        print("\nPhase 2 Verification Complete!")
        
    except Exception as e:
        print(f"\n[X] Error during verification: {str(e)}")

if __name__ == "__main__":
    verify_phase2()
