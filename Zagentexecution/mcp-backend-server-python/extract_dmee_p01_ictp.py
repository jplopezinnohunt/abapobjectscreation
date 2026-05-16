"""Extract /SEPA_CT_ICTP_ISO V000 from P01 to compare against /SEPA_CT_UNES V001."""
import sys, os, csv
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path: sys.path.insert(0, SCRIPTS_DIR)
from rfc_helpers import ConnectionGuard

OUT = os.path.abspath(os.path.join(SCRIPTS_DIR, "..", "..", "knowledge", "domains",
    "Payment", "phase0", "dmee_full", "dmee_tree_node_p01_ictp.csv"))

WHERE = ["TREE_ID = '/SEPA_CT_ICTP_ISO'", " AND VERSION = '000'"]
CHUNKS = [
    ["NODE_ID", "PARENT_ID", "TECH_NAME", "NODE_TYPE", "TREE_ID", "VERSION", "LEV", "FIRSTCHILD_ID"],
    ["NODE_ID", "LENGTH", "MP_OFFSET", "MP_SC_OFFSET", "CV_RULE", "TAB_KEYFLD", "MP_SELECTION", "DATA_TYPE"],
    ["NODE_ID", "MP_SC_TAB", "MP_SC_FLD", "MP_EXIT_FUNC", "MP_CONST", "REF_NAME", "MP_IF_TP", "BROTHER_ID"],
]

g = ConnectionGuard("P01"); g.connect()
by_node = {}
for chunk in CHUNKS:
    res = g.call("RFC_READ_TABLE", QUERY_TABLE="DMEE_TREE_NODE", DELIMITER="|",
        FIELDS=[{"FIELDNAME": f} for f in chunk],
        OPTIONS=[{"TEXT": w} for w in WHERE], ROWCOUNT=2000)
    for r in res.get("DATA", []):
        vals = r["WA"].split("|")
        row = dict(zip(chunk, [v.strip() for v in vals]))
        nid = row["NODE_ID"]
        if nid not in by_node: by_node[nid] = {}
        by_node[nid].update(row)
g.close()

all_fields = ["NODE_ID"]
for chunk in CHUNKS:
    for f in chunk:
        if f not in all_fields: all_fields.append(f)

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=all_fields); w.writeheader()
    for nid, row in sorted(by_node.items()):
        w.writerow({k: row.get(k, "") for k in all_fields})
print(f"Wrote {len(by_node)} nodes to {OUT}")
