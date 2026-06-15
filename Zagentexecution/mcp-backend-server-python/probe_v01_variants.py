import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("V01")
def read(table, where, fields, rc=50):
    try:
        r = c.call("RFC_READ_TABLE", QUERY_TABLE=table,
                   OPTIONS=[{"TEXT": where}] if where else [],
                   FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=rc)
        return [x["WA"] for x in r.get("DATA", [])]
    except Exception as e:
        return [f"ERR: {e}"]
print("=== Saved SAPFPAYM variants in V01 (VARID) ===")
for w in read("VARID", "REPORT = 'SAPFPAYM'", ["REPORT","VARIANT"], rc=200):
    print("  ", w)
print("\n=== TBTCO PAYM jobs full (JOBNAME/STATUS/STRTDATE/STRTTIME) ===")
for w in read("TBTCO", "JOBNAME LIKE 'PAYM:%'", ["JOBNAME","STATUS","STRTDATE","STRTTIME"], rc=50):
    print("  ", w)
c.close()
