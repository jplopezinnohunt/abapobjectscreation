import os
import argparse
from pyrfc import Connection, RFCError
from dotenv import load_dotenv
import sys

def read_abap_report(report_name, system_id="P01"):
    # Load .env from the server directory
    dotenv_path = os.path.join(os.path.dirname(__file__), "..", "Zagentexecution", "mcp-backend-server-python", ".env")
    load_dotenv(dotenv_path)
    
    # Prefix for system-specific environment variables
    prefix = f"SAP_{system_id}_"
    
    # Fallback to generic SAP_* if specific prefix not found
    def get_env(key, default=None):
        return os.getenv(prefix + key) or os.getenv("SAP_" + key) or default

    try:
        conn_params = {
            "ashost": get_env("ASHOST"),
            "sysnr": get_env("SYSNR"),
            "client": get_env("CLIENT"),
            "user": get_env("USER"),
            "lang": get_env("LANG", "EN")
        }
        
        passwd = get_env("PASSWD") or get_env("PASSWORD")
        if passwd:
            conn_params["passwd"] = passwd

        if get_env("SNC_MODE") == "1":
            conn_params["snc_mode"] = "1"
            conn_params["snc_partnername"] = get_env("SNC_PARTNERNAME")
            conn_params["snc_qop"] = get_env("SNC_QOP", "9")
            
        conn = Connection(**conn_params)
        
        result = conn.call("RPY_PROGRAM_READ", PROGRAM_NAME=report_name)
        source = result.get('SOURCE_EXTENDED', [])
        for line in source:
            print(line['LINE'])
            
        conn.close()
    except Exception as e:
        print(f"Error reading {report_name}: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_include_v2.py <PROGRAM_NAME> [SYSTEM]")
    else:
        report = sys.argv[1]
        sys_id = sys.argv[2] if len(sys.argv) > 2 else "P01"
        read_abap_report(report, sys_id)
