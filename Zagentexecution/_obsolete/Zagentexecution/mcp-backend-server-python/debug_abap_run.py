import os, sys
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    p = {"ashost": "172.16.4.66", "sysnr": "00", "client": "350", 
         "user": os.getenv("SAP_USER"), "lang": "EN"}
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"; p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = "9"
    return Connection(**p)

def execute_abap_script(abap_code):
    conn = get_conn()
    print("Executing ABAP Bridge script...")
    # Wrap in simple report statement if not provided
    if "REPORT " not in abap_code.upper():
        abap_code = "REPORT Z_AI_TOOL.\n" + abap_code
    
    abap_source = [{"LINE": line[:72]} for line in abap_code.split('\n')]
    
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap_source)
        print("  [OK] Script finished.")
        print(f"  Result Keys: {list(res.keys())}")
        
        # Inspection of WRITES
        writes = res.get("WRITES", [])
        if writes:
            for w in writes:
                # Some versions use 'LINE', 'TEXT' or 'ZEILE'
                val = w.get('ZEILE') or w.get('LINE') or w.get('TEXT') or list(w.values())[0]
                print(f"  SAP Log: {val}")
        else:
            print("  WRITES table is empty.")
            
        error = res.get("ERRORMESSAGE")
        if error:
            print(f"  SAP ERROR: {error}")
            
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    abap_reg = """
REPORT Z_AI_TEST.
WRITE: / 'HELLO FROM SAP'.
"""
    execute_abap_script(abap_reg)
