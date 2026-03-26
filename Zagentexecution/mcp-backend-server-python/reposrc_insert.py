"""
reposrc_insert.py

Write ABAP source code lines directly into SAP's REPOSRC table via the ABAP bridge.
REPOSRC stores source code for all ABAP programs/includes.

The key design: Python passes the actual source code lines as the PROGRAM rows 
(the RFC_ABAP_INSTALL_AND_RUN input), and we use a special ABAP technique to
avoid the single-quote problem:
- Use cl_abap_conv_codepage text streaming
- Or: pass code via function import parameter (avoid inline strings)
- Or: use INSERT INTO dynpsource (byte values)

Simplest reliable approach: Detect existing REPOSRC rows, 
then DELETE + INSERT fresh rows from the bridge ABAP.

But the quotes inside quotes ABAP limitation only applies if the outer ABAP
has WRITE: / 'quoted string containing single quotes'.

The ACTUAL approach we use:
1. Call SWI_RFC_WRITE (not remote) via bridge - uses PROGTAB format
2. The PROGTAB (LINE CHAR 72) rows in RFC_ABAP_INSTALL_AND_RUN input 
   ARE THEMSELVES the code lines - so if we feed the actual CCIMP code
   AS THE PROGRAM parameter, it will TRY TO EXECUTE IT. That doesn't work.

NEW APPROACH: Use ABAP string buffer with REPLACE operations.
Build the string from character codes (CHARCODE -> CHAR conversion) to avoid
single quotes entirely in the ABAP generation script.
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pyrfc import Connection, RFCError
from dotenv import load_dotenv
load_dotenv()

def get_conn():
    p = {"ashost": "172.16.4.66", "sysnr": "00", "client": "350",
         "user": os.getenv("SAP_USER"), "lang": "EN",
         "snc_mode": "1", "snc_partnername": os.getenv("SAP_SNC_PARTNERNAME"),
         "snc_qop": "9"}
    return Connection(**p)

def execute_abap(code, label=""):
    conn = get_conn()
    if label: print(f"\n[{label}]")
    src = [{"LINE": l[:72]} for l in code.split('\n')]
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
        for w in res.get("WRITES", []):
            print(f"  SAP: {w.get('ZEILE') or list(w.values())[0]}")
        if res.get("ERRORMESSAGE"):
            print(f"  ERROR: {res.get('ERRORMESSAGE')}")
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
    finally:
        conn.close()

def python_char_to_abap_hex(char):
    """Convert a Python char to its hex representation for ABAP."""
    return format(ord(char), '02X')

def escape_line_for_abap(line):
    """
    Replace single quotes with a double-quote workaround.
    In ABAP: lv_line+N(1) = 'x'.  where x is a non-quote char.
    Or: use CHAR4 = X'27' for single quote (hex 27).
    """
    # Replace ' with the ABAP escape sequence approach
    # We'll use a marker character that doesn't appear in ABAP code 
    # and replace it after
    return line.replace("'", "||SQ||")

def build_abap_assign(var_name, line, line_idx):
    """
    Build ABAP code to assign a line to a variable safely.
    Replaces single quotes using hex assignment for problematic chars.
    """
    result = []
    # Replace single quotes in source lines with a special marker
    clean_line = line.replace("'", "''")  # ABAP double-quote escape
    
    # If the line contains no single quotes, use simple assignment
    if "'" not in line:
        result.append(f"{var_name} = '{clean_line[:70]}'.")
    else:
        # Use ABAP concatenation to handle quotes
        parts = line.split("'")
        sq_var = "lv_sq"  # Variable holding single quote char
        abap_parts = []
        for i, part in enumerate(parts):
            if part:
                abap_parts.append(f"'{part[:30]}'")
            if i < len(parts) - 1:
                abap_parts.append(sq_var)
        result.append(f"{var_name} = {' && '.join(abap_parts)}.")
    
    return result

if __name__ == "__main__":
    # Test the hex approach for writing single-quote containing code
    execute_abap("""
REPORT Z_TEST_HEX.
DATA: lv_sq  TYPE c LENGTH 1.
DATA: lv_line TYPE abaptxt255.
DATA: lt_code TYPE TABLE OF abaptxt255.

* Build single quote character via hex
lv_sq = cl_abap_conv_codepage=>create_in( )->convert(
  source = xstring`27` ) .

WRITE: / 'sq char is:',  lv_sq.
""", "TEST CL_ABAP_CONV")
