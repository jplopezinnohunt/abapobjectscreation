"""Probe UBA01 / GL 0001065424 in LIVE P01 via RFC."""
import os, sys
MCP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP_DIR))
from rfc_helpers import get_connection

conn = get_connection("P01")

def rfc(table, where, fields=None, n=10):
    rfc_fields = [{"FIELDNAME": f} for f in fields] if fields else []
    opts = [{"TEXT": where}] if where else []
    try:
        res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                        ROWCOUNT=n, ROWSKIPS=0, OPTIONS=opts, FIELDS=rfc_fields)
        hdrs = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
        rows = res.get("DATA", [])
        print(f"\n{table}  WHERE {where}  -> {len(rows)} rows, cols={hdrs[:8]}")
        for r in rows[:5]:
            print("  ", r["WA"][:250])
    except Exception as e:
        print(f"\n{table}  WHERE {where}  -> ERR {type(e).__name__}: {str(e)[:180]}")

# UBA01 house bank
rfc("T012", "BUKRS = 'UNES' AND HBKID = 'UBA01'",
    ["BUKRS","HBKID","BANKS","BANKL","BANKN","NAME1"])
rfc("T012K", "BUKRS = 'UNES' AND HBKID = 'UBA01'",
    ["BUKRS","HBKID","HKTID","BANKN","HKONT","WAERS"])
# UBA-family
rfc("T012", "BUKRS = 'UNES' AND HBKID LIKE 'UBA%'",
    ["BUKRS","HBKID","BANKS","BANKL","NAME1"])

# GL 0001065424 in P01 chart of accounts
rfc("SKA1", "SAKNR = '0001065424'",
    ["KTOPL","SAKNR","XINTB","XSPEB","GVTYP","WAERS","GSBER"])
rfc("SKAT", "SAKNR = '0001065424' AND SPRAS = 'E'",
    ["SPRAS","KTOPL","SAKNR","TXT20","TXT50"])
rfc("SKB1", "BUKRS='UNES' AND SAKNR = '0001065424'",
    ["BUKRS","SAKNR","MWSKZ","XOPVW","HBKID","HKTID","FSTAG","WAERS"])

# ECO09 main GL 0001094424 live
rfc("SKA1", "SAKNR = '0001094424'",
    ["KTOPL","SAKNR","XINTB","XSPEB","WAERS","GSBER"])
rfc("T012K", "HKONT = '0001094424'",
    ["BUKRS","HBKID","HKTID","BANKN","HKONT","WAERS"])
