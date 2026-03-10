import os
from dotenv import load_dotenv
from pyrfc import Connection

def inspect_bapi():
    load_dotenv()
    conn = Connection(
        ashost=os.getenv("SAP_ASHOST"),
        sysnr=os.getenv("SAP_SYSNR"),
        client=os.getenv("SAP_CLIENT"),
        user=os.getenv("SAP_USER"),
        lang=os.getenv("SAP_LANG", "EN"),
        snc_mode=os.getenv("SAP_SNC_MODE"),
        snc_partnername=os.getenv("SAP_SNC_PARTNERNAME"),
        snc_qop=os.getenv("SAP_SNC_QOP")
    )
    
    print("Inspecting SIW_RFC_READ_REPORT interface...")
    result = conn.call("RFC_GET_FUNCTION_INTERFACE", FUNCNAME="SIW_RFC_READ_REPORT")
    
    params = result.get("PARAMS", [])
    for p in params:
        print(f"Param: {p['PARAMETER']} | Type: {p['PARAMCLASS']} | Optional: {p['OPTIONAL']}")
        
    conn.close()

if __name__ == "__main__":
    inspect_bapi()
