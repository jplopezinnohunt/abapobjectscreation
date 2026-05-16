"""Extract DMEE_TREE_COND for V001 SEPA from D01."""
import sys, os, csv
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path: sys.path.insert(0, SCRIPTS_DIR)
from rfc_helpers import ConnectionGuard

OUT = os.path.abspath(os.path.join(SCRIPTS_DIR, "..", "..", "knowledge", "domains",
    "Payment", "phase0", "dmee_full", "dmee_tree_cond_d01_sepa_v001.csv"))

g = ConnectionGuard("D01"); g.connect()
fields = ["NODE_ID", "VERSION", "COND_NUMBER", "ARG1_TYPE", "ARG1_TAB", "ARG1_FLD", "OPERATOR", "ARG2_CONST"]
res = g.call("RFC_READ_TABLE", QUERY_TABLE="DMEE_TREE_COND", DELIMITER="|",
    FIELDS=[{"FIELDNAME": f} for f in fields],
    OPTIONS=[{"TEXT": "TREE_ID = '/SEPA_CT_UNES'"}, {"TEXT": " AND VERSION = '001'"}],
    ROWCOUNT=500)
g.close()

rows = []
for r in res.get("DATA", []):
    rows.append(dict(zip(fields, [v.strip() for v in r["WA"].split("|")])))

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
    for r in rows: w.writerow(r)
print(f"Wrote {len(rows)} rows to {OUT}")
