from sap_utils import get_sap_connection
import pprint

def debug_read_report(name):
    try:
        conn = get_sap_connection()
        result = conn.call("SIW_RFC_READ_REPORT", I_NAME=name)
        print(f"Result for {name}:")
        pprint.pprint(result)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "ZCL_ZHRF_OFFBOARD_DPC_EXT=====CM001"
    debug_read_report(name)
