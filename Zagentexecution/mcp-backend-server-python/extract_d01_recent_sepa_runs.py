"""Find recent F110 runs in D01 — broad filter for any SEPA-eligible run."""
import sys, os
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path: sys.path.insert(0, SCRIPTS_DIR)
from rfc_helpers import ConnectionGuard

g = ConnectionGuard("D01"); g.connect()

fields = ["LAUFD", "LAUFI", "ZBUKR", "LIFNR", "RBETR", "WAERS", "HBKID", "RZAWE"]

# Broad filter — last 6 months any UNES F110
res = g.call(
    "RFC_READ_TABLE",
    QUERY_TABLE="REGUH",
    DELIMITER="|",
    FIELDS=[{"FIELDNAME": f} for f in fields],
    OPTIONS=[
        {"TEXT": "LAUFD > '20251101'"},
        {"TEXT": " AND ZBUKR = 'UNES'"},
    ],
    ROWCOUNT=500,
)

rows = []
for r in res.get("DATA", []):
    vals = r["WA"].split("|")
    rows.append(dict(zip(fields, [v.strip() for v in vals])))

g.close()

from collections import defaultdict
runs = defaultdict(lambda: {"count": 0, "vendors": set(), "sum": 0.0, "currencies": set(), "hbkids": set(), "rzawes": set()})
for r in rows:
    key = (r["LAUFD"], r["LAUFI"], r["ZBUKR"])
    runs[key]["count"] += 1
    runs[key]["vendors"].add(r["LIFNR"])
    runs[key]["currencies"].add(r["WAERS"])
    runs[key]["hbkids"].add(r["HBKID"])
    runs[key]["rzawes"].add(r["RZAWE"])
    try:
        runs[key]["sum"] += float(r["RBETR"])
    except: pass

sorted_runs = sorted(runs.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True)

print(f"Found {len(rows)} REGUH rows across {len(runs)} unique D01 UNES runs since 2025-11-01")
print(f"\nMost recent UNES F110 runs in D01:")
print(f"{'LAUFD':<10} {'LAUFI':<10} {'Pmts':>5} {'Curr':<8} {'HBank':<10} {'PMethod':<8} {'Sum':>14}")
print("-" * 75)
for (laufd, laufi, zbukr), info in sorted_runs[:20]:
    curr = ",".join(sorted(info["currencies"]))[:7] if info["currencies"] else ""
    hbk = ",".join(sorted(info["hbkids"]))[:10]
    rzv = ",".join(sorted(info["rzawes"]))[:7]
    print(f"{laufd:<10} {laufi:<10} {info['count']:>5} {curr:<8} {hbk:<10} {rzv:<8} {info['sum']:>14.2f}")
