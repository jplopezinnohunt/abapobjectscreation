"""Compare T012T (house bank texts) between P01 and D01 — the real data behind VC_T012N."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection

def read_all(conn, table, fields=None, max_rows=500):
    params = {"QUERY_TABLE": table, "DELIMITER": "|", "ROWCOUNT": max_rows}
    if fields:
        params["FIELDS"] = [{"FIELDNAME": f} for f in fields]
    result = conn.call("RFC_READ_TABLE", **params)
    fnames = [f["FIELDNAME"].strip() for f in result.get("FIELDS", [])]
    rows = []
    for row in result.get("DATA", []):
        parts = row["WA"].split("|")
        rows.append({h: parts[i].strip() for i, h in enumerate(fnames)})
    return fnames, rows

p01 = get_connection(system_id="P01")
d01 = get_connection(system_id="D01")

# T012T — house bank account texts (language-dependent names)
print("="*60)
print("T012T — House Bank Account Texts")
print("="*60)
_, p01_rows = read_all(p01, "T012T")
_, d01_rows = read_all(d01, "T012T")
print(f"P01: {len(p01_rows)} rows, D01: {len(d01_rows)} rows")

p01_map = {(r.get("BUKRS",""), r.get("HBKID",""), r.get("HKTID",""), r.get("SPRAS","")): r for r in p01_rows}
d01_map = {(r.get("BUKRS",""), r.get("HBKID",""), r.get("HKTID",""), r.get("SPRAS","")): r for r in d01_rows}

only_p01 = set(p01_map.keys()) - set(d01_map.keys())
only_d01 = set(d01_map.keys()) - set(p01_map.keys())
common = set(p01_map.keys()) & set(d01_map.keys())

if only_p01:
    print(f"\nONLY IN P01 ({len(only_p01)}):")
    for k in sorted(only_p01):
        print(f"  {p01_map[k]}")

if only_d01:
    print(f"\nONLY IN D01 ({len(only_d01)}):")
    for k in sorted(only_d01):
        print(f"  {d01_map[k]}")

diffs = []
for k in common:
    p, d = p01_map[k], d01_map[k]
    fd = {f: (p[f], d[f]) for f in p if p.get(f) != d.get(f)}
    if fd:
        diffs.append((k, fd))

if diffs:
    print(f"\nVALUE DIFFERENCES ({len(diffs)}):")
    for k, fd in diffs:
        print(f"  Key: BUKRS={k[0]} HBKID={k[1]} HKTID={k[2]} SPRAS={k[3]}")
        for f, (pv, dv) in fd.items():
            print(f"    {f}: P01='{pv}' vs D01='{dv}'")

if not only_p01 and not only_d01 and not diffs:
    print(f"\nIDENTICAL ({len(common)} rows match)")

# T012K — house bank accounts
print(f"\n{'='*60}")
print("T012K — House Bank Accounts")
print(f"{'='*60}")
_, p01_rows = read_all(p01, "T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "BKONT", "WAERS", "HKONT", "ZLSCH"])
_, d01_rows = read_all(d01, "T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "BKONT", "WAERS", "HKONT", "ZLSCH"])
print(f"P01: {len(p01_rows)} rows, D01: {len(d01_rows)} rows")

p01_map = {(r.get("BUKRS",""), r.get("HBKID",""), r.get("HKTID","")): r for r in p01_rows}
d01_map = {(r.get("BUKRS",""), r.get("HBKID",""), r.get("HKTID","")): r for r in d01_rows}

only_p01 = set(p01_map.keys()) - set(d01_map.keys())
only_d01 = set(d01_map.keys()) - set(p01_map.keys())
common = set(p01_map.keys()) & set(d01_map.keys())

if only_p01:
    print(f"\nONLY IN P01 ({len(only_p01)}):")
    for k in sorted(only_p01):
        print(f"  {p01_map[k]}")

if only_d01:
    print(f"\nONLY IN D01 ({len(only_d01)}):")
    for k in sorted(only_d01):
        print(f"  {d01_map[k]}")

diffs = []
for k in common:
    p, d = p01_map[k], d01_map[k]
    fd = {f: (p[f], d[f]) for f in p if p.get(f) != d.get(f)}
    if fd:
        diffs.append((k, fd))

if diffs:
    print(f"\nVALUE DIFFERENCES ({len(diffs)}):")
    for k, fd in diffs:
        print(f"  Key: BUKRS={k[0]} HBKID={k[1]} HKTID={k[2]}")
        for f, (pv, dv) in fd.items():
            print(f"    {f}: P01='{pv}' vs D01='{dv}'")

if not only_p01 and not only_d01 and not diffs:
    print(f"\nIDENTICAL ({len(common)} rows match)")
