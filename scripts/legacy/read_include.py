import os
from pyrfc import Connection, ABAPRuntimeError, ABAPApplicationError, LogonError, CommunicationError
from dotenv import load_dotenv
import sys

# Load environmental variables
load_dotenv('c:/Users/jp_lopez/projects/abapobjectscreation/Zagentexecution/mcp-backend-server-python/.env')

def get_connection(system='P01'):
    try:
        if system == 'D01':
            return Connection(
                ashost=os.getenv('SAP_HOST_D01'),
                sysnr=os.getenv('SAP_SYSNR_D01'),
                client=os.getenv('SAP_CLIENT_D01'),
                user=os.getenv('SAP_USER_D01'),
                passwd=os.getenv('SAP_PASS_D01'),
                snc_mode=os.getenv('SAP_SNC_MODE_D01'),
                snc_partnername=os.getenv('SAP_SNC_PARTNER_D01'),
                snc_qop=os.getenv('SAP_SNC_QOP_D01'),
                snc_lib=os.getenv('SAP_SNC_LIB_D01'),
                snc_myname=os.getenv('SAP_SNC_MYNAME_D01'),
                trace=os.getenv('SAP_TRACE_D01')
            )
        else:
             return Connection(
                ashost=os.getenv('SAP_HOST_P01'),
                sysnr=os.getenv('SAP_SYSNR_P01'),
                client=os.getenv('SAP_CLIENT_P01'),
                user=os.getenv('SAP_USER_P01'),
                passwd=os.getenv('SAP_PASS_P01'),
                snc_mode=os.getenv('SAP_SNC_MODE_P01'),
                snc_partnername=os.getenv('SAP_SNC_PARTNER_P01'),
                snc_qop=os.getenv('SAP_SNC_QOP_P01'),
                snc_lib=os.getenv('SAP_SNC_LIB_P01'),
                snc_myname=os.getenv('SAP_SNC_MYNAME_P01'),
                trace=os.getenv('SAP_TRACE_P01')
            )
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return None

def read_include(program_name, system='P01'):
    conn = get_connection(system)
    if not conn:
        return
    
    try:
        result = conn.call('RPY_PROGRAM_READ', PROGRAM_NAME=program_name)
        source = result.get('SOURCE_EXTENDED', [])
        for line in source:
            print(line['LINE'])
    except Exception as e:
        print(f"Error reading {program_name}: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_include.py <PROGRAM_NAME> [SYSTEM]")
    else:
        prog = sys.argv[1]
        sys_name = sys.argv[2] if len(sys.argv) > 2 else 'P01'
        read_include(prog, sys_name)
