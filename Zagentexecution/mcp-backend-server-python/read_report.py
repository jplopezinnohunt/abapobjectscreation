import os
import argparse
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

def read_abap_report(report_name, output_file=None):
    load_dotenv()
    try:
        conn_params = {"ashost": os.getenv("SAP_ASHOST"),"sysnr": os.getenv("SAP_SYSNR"),"client": os.getenv("SAP_CLIENT"),"user": os.getenv("SAP_USER"),"lang": os.getenv("SAP_LANG", "EN")}
        passwd = os.getenv("SAP_PASSWD")
        if passwd: conn_params["passwd"] = passwd
        if os.getenv("SAP_SNC_MODE") == "1":
            conn_params["snc_mode"] = "1"
            conn_params["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
            conn_params["snc_qop"] = os.getenv("SAP_SNC_QOP", "9")
            
        conn = Connection(**conn_params)
        
        result = conn.call("SIW_RFC_READ_REPORT", I_NAME=report_name)
        code_lines = result.get("E_TAB_CODE", [])
        
        output = []
        output.append(f"--- Program: {report_name} (Total lines: {len(code_lines)}) ---")
        for line in code_lines:
            # Depending on the structure of E_TAB_CODE, could be 'LINE' or 'TEXT' etc.
            # Assuming 'LINE' based on standard structures
            if isinstance(line, dict) and 'LINE' in line:
                output.append(line['LINE'].rstrip())
            elif isinstance(line, dict) and 'TEXT' in line:
                output.append(line['TEXT'].rstrip())
            else:
                output.append(str(line).rstrip())
            
        conn.close()
        
        output_str = "\n".join(output)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_str)
            print(f"Saved to {output_file}")
        else:
            print(output_str)

    except RFCError as e:
        print(f"SAP RFC Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="ABAP Report/Program Name")
    parser.add_argument("--out", help="Output file")
    args = parser.parse_args()
    read_abap_report(args.report, args.out)
