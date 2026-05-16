"""Read SEPA payment medium file from D01 via RFC for collector 00004B."""
import sys, os
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path: sys.path.insert(0, SCRIPTS_DIR)
from rfc_helpers import ConnectionGuard

g = ConnectionGuard("D01"); g.connect()

# Try common SAP server paths for payment medium files
candidate_dirs = [
    "/usr/sap/D01/work",
    "/usr/sap/D01/SYS/global",
    "/usr/sap/trans/data",
    "//hq-sapitf/SWIFT$/D01/input",
    "C:\\INT\\Outbound\\EFT",
]

for d in candidate_dirs:
    try:
        res = g.call("EPS_GET_DIRECTORY_LISTING", DIR_NAME=d)
        files = res.get("DIR_LIST", [])
        if files:
            print(f"\n=== Directory: {d} ===")
            for f in files[:20]:
                name = f.get("NAME", "")
                if "SEPA" in name.upper() or "00004B" in name or "20260507" in name or "FPAYM" in name.upper():
                    print(f"  MATCH: {name}")
            print(f"  ({len(files)} total files)")
    except Exception as e:
        msg = str(e).split('\n')[0][:80]
        print(f"  ERROR {d}: {msg}")

# Also try TemSe — payment medium files often stored there
print("\n=== TemSe TBPM* objects (payment medium TemSe) ===")
try:
    res = g.call("RFC_READ_TABLE", QUERY_TABLE="TST01", DELIMITER="|",
        FIELDS=[{"FIELDNAME":"DNAME"},{"FIELDNAME":"DOWNERAM"},{"FIELDNAME":"DTIME"}],
        OPTIONS=[{"TEXT":"DOWNERAM = 'JP_LOPEZ'"},{"TEXT":" AND DDATE = '20260507'"}],
        ROWCOUNT=20)
    for r in res.get("DATA", [])[:10]:
        print(f"  {r['WA']}")
except Exception as e:
    print(f"  ERROR TST01: {str(e)[:100]}")

g.close()
