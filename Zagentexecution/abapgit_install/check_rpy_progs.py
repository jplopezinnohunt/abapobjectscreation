"""Check which RPY_PROGRAM_* FMs are RFC-enabled on D01."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-backend-server-python", ".env"))
from pyrfc import Connection

p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
     "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"),
     "passwd": os.getenv("SAP_PASSWD"), "lang": "EN"}
conn = Connection(**p)

# TFDIR rows for RPY_PROGRAM_* + RS_DELETE_PROGRAM + INSERT_REPORT_*
for pat in ["RPY_PROGRAM_%", "RS_INSERT_INTO_WORKING%", "INSERT_REPORT_%",
            "RS_PROGRAM_%", "RS_DELETE_PROGRAM"]:
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TFDIR", DELIMITER="|",
                  OPTIONS=[{"TEXT": f"FUNCNAME LIKE '{pat}'"}],
                  FIELDS=[{"FIELDNAME": "FUNCNAME"}, {"FIELDNAME": "FMODE"}],
                  ROWCOUNT=30)
    print(f"\n[{pat}]  {len(r.get('DATA', []))} rows")
    for row in r.get("DATA", []):
        print(f"  {row['WA']}")

# Also try direct interface lookup
print("\n=== Try calling RPY_PROGRAM_INSERT info via RFC_FUNCTION_SEARCH ===")
try:
    r = conn.call("RFC_FUNCTION_SEARCH", FUNCNAME="RPY_PROGRAM_INSERT")
    print(f"  rows: {len(r.get('FUNCTIONS', []))}")
    for row in r.get("FUNCTIONS", [])[:10]:
        print(f"  {row}")
except Exception as e:
    print(f"  error: {e}")

conn.close()
