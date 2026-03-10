import os
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

def test_connection():
    load_dotenv()
    
    ashost = os.getenv("SAP_ASHOST")
    user = os.getenv("SAP_USER")
    
    if not ashost or ashost == "your_sap_host":
        print("ERROR: Please fill in your real SAP credentials in the .env file.")
        return

    print(f"Attempting to connect to SAP System ({ashost}) as user {user}...")
    
    try:
        conn_params = {
            "ashost": ashost,
            "sysnr": os.getenv("SAP_SYSNR"),
            "client": os.getenv("SAP_CLIENT"),
            "user": user,
            "lang": os.getenv("SAP_LANG", "EN")
        }
        
        # Add password if it exists
        passwd = os.getenv("SAP_PASSWD")
        if passwd:
            conn_params["passwd"] = passwd
            
        # Add SNC parameters if SSO is enabled
        if os.getenv("SAP_SNC_MODE") == "1":
            print("SNC (Single Sign-On) Mode detected. Adding SNC parameters...")
            conn_params["snc_mode"] = "1"
            conn_params["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
            conn_params["snc_qop"] = os.getenv("SAP_SNC_QOP", "9")
            # When using SSO, sap_user is often required but passwd is not.
            
        # Establish connection
        conn = Connection(**conn_params)
        
        print("\n[+] SUCCESS: Successfully authenticated and connected to the SAP Backend over native RFC!")
        
        # Test a simple ping or read table
        print("\nRunning a quick test: Reading SAP Clients (T000) via RFC_READ_TABLE...")
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE="T000", ROWCOUNT=3)
        
        data = result.get("DATA", [])
        print(f"Found {len(data)} clients in T000:")
        for row in data:
            print(f"- {row.get('WA', '').strip()}")
        print("\nTest complete! You are ready to run the MCP Server!")
        
        conn.close()
        
    except RFCError as e:
        print(f"\n[X] SAP RFC CONNECTION ERROR:\n{str(e)}")
    except Exception as e:
        print(f"\n[X] UNEXPECTED ERROR:\n{str(e)}")

if __name__ == "__main__":
    test_connection()
