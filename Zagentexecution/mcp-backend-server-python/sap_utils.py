import os
from dotenv import load_dotenv
from pyrfc import Connection

def get_sap_connection(system_id="D01"):
    """
    Establishes and returns an SAP RFC connection based on .env parameters.
    Supports system_id (e.g., 'D01', 'P01') to choose configuration.
    """
    load_dotenv()
    
    # Prefix for system-specific environment variables
    prefix = f"SAP_{system_id}_"
    
    # Fallback to generic SAP_* if specific prefix not found (for backward compatibility)
    def get_env(key, default=None):
        return os.getenv(prefix + key) or os.getenv("SAP_" + key) or default

    try:
        conn_params = {
            "ashost": get_env("ASHOST"),
            "sysnr": get_env("SYSNR"),
            "client": get_env("CLIENT"),
            "user": get_env("USER"),
            "passwd": get_env("PASSWD") or get_env("PASSWORD"), 
            "lang": get_env("LANG", "EN")
        }
        
        if get_env("SNC_MODE") == "1":
            conn_params["snc_mode"] = "1"
            conn_params["snc_partnername"] = get_env("SNC_PARTNERNAME")
            conn_params["snc_qop"] = get_env("SNC_QOP", "9")
            
        conn = Connection(**conn_params)
        return conn
    except Exception as e:
        raise Exception(f"Failed to connect to SAP system {system_id}: {str(e)}")
