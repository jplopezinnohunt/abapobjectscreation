"""Retry the 2 failed tables with alternative names."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection

def probe(conn, sys_id, table):
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|", ROWCOUNT=5)
        fnames = [f["FIELDNAME"].strip() for f in result.get("FIELDS", [])]
        rows = len(result.get("DATA", []))
        return f"{sys_id}: OK - {rows} rows, fields={fnames[:8]}"
    except Exception as e:
        return f"{sys_id}: FAIL - {str(e)[:100]}"

p01 = get_connection(system_id="P01")
d01 = get_connection(system_id="D01")

# T77HRFPM_CLSNG alternatives
for tbl in ["T77HRFPM_CLSNG", "HRP1000", "T77HRFPM", "T77HR", "PA0001"]:
    print(f"\n{tbl}:")
    print(f"  {probe(p01, 'P01', tbl)}")

# T012N alternatives - house bank names
for tbl in ["T012N", "T012", "T012T", "T012K"]:
    print(f"\n{tbl}:")
    print(f"  {probe(p01, 'P01', tbl)}")
    print(f"  {probe(d01, 'D01', tbl)}")

# Compare T012 (house bank master) and T012T (texts) directly
print("\n" + "="*60)
print("T012 full comparison (house bank master):")
for sys_id, conn in [("P01", p01), ("D01", d01)]:
    result = conn.call("RFC_READ_TABLE", QUERY_TABLE="T012", DELIMITER="|", ROWCOUNT=200,
                       FIELDS=[{"FIELDNAME": f} for f in ["BUKRS", "HBKID", "BANKS", "BANKL", "BANKN", "BRNCH"]])
    fnames = [f["FIELDNAME"].strip() for f in result.get("FIELDS", [])]
    rows = []
    for row in result.get("DATA", []):
        parts = row["WA"].split("|")
        rows.append({h: parts[i].strip() for i, h in enumerate(fnames)})
    print(f"\n  {sys_id}: {len(rows)} house banks")
    for r in rows[:5]:
        print(f"    {r}")
    if len(rows) > 5:
        print(f"    ... +{len(rows)-5} more")

# Compare T012T (house bank texts)
print("\n" + "="*60)
print("T012T comparison (house bank texts):")
for sys_id, conn in [("P01", p01), ("D01", d01)]:
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE="T012T", DELIMITER="|", ROWCOUNT=200)
        fnames = [f["FIELDNAME"].strip() for f in result.get("FIELDS", [])]
        rows = []
        for row in result.get("DATA", []):
            parts = row["WA"].split("|")
            rows.append({h: parts[i].strip() for i, h in enumerate(fnames)})
        print(f"  {sys_id}: {len(rows)} rows")
        for r in rows[:5]:
            print(f"    {r}")
    except Exception as e:
        print(f"  {sys_id}: {str(e)[:100]}")
