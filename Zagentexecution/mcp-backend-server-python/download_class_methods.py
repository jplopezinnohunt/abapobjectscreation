import os
import sys
import argparse
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

def download_class_methods(class_name, output_file):
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

        # Standard class method naming convention: CLASSNAME=======CM*
        # We use a wildcard search to find all CM includes
        query_pattern = f"{class_name}%CM%"
        
        print(f"Searching for includes like {query_pattern}")

        result_trdir = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="TRDIR",
            DELIMITER="|",
            ROWCOUNT=500,
            OPTIONS=[{"TEXT": f"NAME LIKE '{query_pattern}'"}]
        )

        includes = [row['WA'].split('|')[0].strip() for row in result_trdir.get("DATA", [])]
        print(f"Found {len(includes)} method includes.")

        with open(output_file, 'w', encoding='utf-8') as out_f:
            for report in includes:
                # First get the method name/description if possible from SEOCOMPO
                # or just the code
                res = conn.call("SIW_RFC_READ_REPORT", I_NAME=report)
                code_lines = res.get("E_TAB_CODE", [])
                out_f.write(f"\n\n--- Method Implementation: {report} ---\n")
                for line in code_lines:
                    if isinstance(line, dict):
                        text = line.get('LINE', '') or line.get('TEXT', '')
                        out_f.write(f"{text.rstrip()}\n")
                    elif isinstance(line, str):
                        out_f.write(f"{line.rstrip()}\n")
                    else:
                        out_f.write(f"{str(line).rstrip()}\n")

        conn.close()
        print(f"All methods downloaded to {output_file}")
    except RFCError as e:
        print(f"SAP RFC Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download all methods of an ABAP class.')
    parser.add_argument('class_name', help='The name of the ABAP class')
    parser.add_argument('--out', default='class_methods.txt', help='Output file name')
    args = parser.parse_args()
    
    download_class_methods(args.class_name.upper(), args.out)
