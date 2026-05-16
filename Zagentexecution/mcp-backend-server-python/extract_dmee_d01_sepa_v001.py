"""
extract_dmee_d01_sepa_v001.py
==============================
One-shot extract of DMEE_TREE_NODE rows from D01 dev system, filtered to
TREE_ID='/SEPA_CT_UNES' AND VERSION='001'. Writes CSV to phase0/dmee_full/.

Used to validate user's V001 build in D01 against ground truth (CGI N_8824498030).

Multiple chunks because RFC_READ_TABLE has 512-byte line buffer limit; we read
NODE_ID + 7 other fields per call, then merge by NODE_ID.
"""
import sys, os, csv, time
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path: sys.path.insert(0, SCRIPTS_DIR)
from rfc_helpers import ConnectionGuard

OUT_PATH = os.path.abspath(os.path.join(
    SCRIPTS_DIR, "..", "..", "knowledge", "domains", "Payment", "phase0",
    "dmee_full", "dmee_tree_node_d01_sepa_v001.csv"))

WHERE = ["TREE_ID = '/SEPA_CT_UNES'", " AND VERSION = '001'"]

# Field chunks: NODE_ID is the join key, repeated in each call
CHUNKS = [
    ["NODE_ID", "PARENT_ID", "TECH_NAME", "NODE_TYPE", "TREE_ID", "VERSION", "LEV", "FIRSTCHILD_ID"],
    ["NODE_ID", "LENGTH", "MP_OFFSET", "MP_SC_OFFSET", "CV_RULE", "TAB_KEYFLD", "MP_SELECTION", "DATA_TYPE"],
    ["NODE_ID", "MP_SC_TAB", "MP_SC_FLD", "MP_EXIT_FUNC", "MP_CONST", "REF_NAME", "MP_IF_TP", "BROTHER_ID"],
]

def call_chunk(g, fields):
    res = g.call(
        "RFC_READ_TABLE",
        QUERY_TABLE="DMEE_TREE_NODE",
        DELIMITER="|",
        FIELDS=[{"FIELDNAME": f} for f in fields],
        OPTIONS=[{"TEXT": w} for w in WHERE],
        ROWCOUNT=2000,
    )
    rows = []
    for r in res.get("DATA", []):
        vals = r["WA"].split("|")
        rows.append(dict(zip(fields, [v.strip() for v in vals])))
    return rows

def main():
    print(f"[1/5] Building D01 connection...", flush=True)
    g = ConnectionGuard("D01")
    g.connect()
    print(f"      connected", flush=True)

    by_node = {}
    for i, chunk in enumerate(CHUNKS, 1):
        print(f"[{i+1}/5] Reading chunk {i} (fields: {chunk})...", flush=True)
        t0 = time.time()
        rows = call_chunk(g, chunk)
        print(f"      got {len(rows)} rows in {time.time()-t0:.1f}s", flush=True)
        for r in rows:
            nid = r["NODE_ID"]
            if nid not in by_node:
                by_node[nid] = {}
            by_node[nid].update(r)

    g.close()

    # Write CSV — column order = union of all chunks (NODE_ID first)
    all_fields = ["NODE_ID"]
    for chunk in CHUNKS:
        for f in chunk:
            if f not in all_fields:
                all_fields.append(f)

    print(f"[5/5] Writing {len(by_node)} merged rows to:\n      {OUT_PATH}", flush=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=all_fields)
        w.writeheader()
        for nid, row in sorted(by_node.items()):
            w.writerow({k: row.get(k, "") for k in all_fields})

    print(f"\nDONE. {len(by_node)} V001 SEPA nodes written.", flush=True)

if __name__ == "__main__":
    main()
