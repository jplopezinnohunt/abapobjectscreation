"""Check T77HRFPM_CLOSING and variations in both systems."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection

def probe(conn, sys_id, table):
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|", ROWCOUNT=50)
        fnames = [f["FIELDNAME"].strip() for f in result.get("FIELDS", [])]
        rows = []
        for row in result.get("DATA", []):
            parts = row["WA"].split("|")
            rows.append({h: parts[i].strip() for i, h in enumerate(fnames)})
        return fnames, rows
    except Exception as e:
        return None, str(e)[:120]

p01 = get_connection(system_id="P01")
d01 = get_connection(system_id="D01")

candidates = [
    "T77HRFPM_CLOSING",
    "T77HRFPM_CLSNG",
    "T77HRFPM_CLSING",
    "T77HRFPM_CLS",
    "T77HRFPM_CLOSE",
]

for tbl in candidates:
    print(f"\n{tbl}:")
    f1, r1 = probe(p01, "P01", tbl)
    f2, r2 = probe(d01, "D01", tbl)
    if f1:
        print(f"  P01: {len(r1)} rows, fields={f1}")
        for r in r1[:5]:
            print(f"    {r}")
    else:
        print(f"  P01: {r1}")
    if f2:
        print(f"  D01: {len(r2)} rows, fields={f2}")
        for r in r2[:5]:
            print(f"    {r}")
    else:
        print(f"  D01: {r2}")
