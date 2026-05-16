"""
Full dump of DMEE_TREE_NODE for /SEPA_CT_UNES (V000 active) D01.
Build complete XPath per node + extract source/exit/condition.
Output to CSV + console table.
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")
TREE_ID = "/SEPA_CT_UNES"
VERSION = "000"

# Pull all nodes
rows = rfc_read_paginated(c, "DMEE_TREE_NODE",
    fields=["NODE_ID","NODE_PARENT","TECH_NAME","NTYPE","SUBSTC",
            "MP_SC_TAB","MP_SC_FLD","MP_EXIT_FUNC","CV_RULE","SUPPRES"],
    where=f"TREE_ID = '{TREE_ID}' AND VERSION = '{VERSION}'",
    batch_size=200, throttle=0.0)
print(f"Got {len(rows)} nodes for {TREE_ID} V{VERSION}")

# Build by NODE_ID dict
by_id = {r["NODE_ID"]: r for r in rows}

def xpath_of(nid, _seen=None):
    if _seen is None: _seen = set()
    if nid in _seen: return "[CYCLE]"
    _seen.add(nid)
    n = by_id.get(nid)
    if not n: return ""
    parent = n.get("NODE_PARENT")
    tech = (n.get("TECH_NAME") or "").strip()
    if parent and parent != "0" and parent in by_id:
        parent_path = xpath_of(parent, _seen)
        return f"{parent_path}/{tech}" if tech else parent_path
    return f"/{tech}" if tech else ""

# NTYPE legend (DMEE)
NTYPE_LEGEND = {
    "1": "ROOT",  "2": "SEGMENT", "3": "ELEMENT", "4": "CONDITION",
    "5": "TECHNICAL", "6": "AGGREGATION", "7": "COMPOSITE", "8": "ATOMIC_LEAF",
}

# enrich + sort by xpath
out_rows = []
for r in rows:
    xp = xpath_of(r["NODE_ID"])
    out_rows.append({
        "node_id":   r["NODE_ID"],
        "xpath":     xp,
        "tech_name": (r.get("TECH_NAME") or "").strip(),
        "ntype":     r.get("NTYPE"),
        "ntype_lbl": NTYPE_LEGEND.get(r.get("NTYPE"),"?"),
        "src_tab":   (r.get("MP_SC_TAB") or "").strip(),
        "src_fld":   (r.get("MP_SC_FLD") or "").strip(),
        "exit":      (r.get("MP_EXIT_FUNC") or "").strip(),
        "cv_rule":   (r.get("CV_RULE") or "").strip(),
        "suppres":   (r.get("SUPPRES") or "").strip(),
    })
out_rows.sort(key=lambda x: x["xpath"])

# Save CSV
csv_path = os.path.join(os.path.dirname(__file__), "..", "..",
                       "knowledge/domains/Payment/dmee_sepa_ct_unes_v000_full.csv")
os.makedirs(os.path.dirname(csv_path), exist_ok=True)
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
    w.writeheader()
    for r in out_rows: w.writerow(r)
print(f"Saved: {csv_path}")

# Print compact table — only LEAF nodes (NTYPE 8 atomic, or 3 element with src/exit)
print(f"\n{'XPath':<70} {'NTYPE':<14} {'SRC':<30} {'EXIT':<32}")
print("="*150)
for r in out_rows:
    if r["ntype"] in ("8","3","4"):  # leafs + conditions
        src = f"{r['src_tab']}-{r['src_fld']}" if r['src_tab'] else r['cv_rule'] or ""
        exit_ = r['exit']
        xp = r['xpath'] or f"[{r['tech_name']}]"
        print(f"{xp[:70]:<70} {r['ntype_lbl']:<14} {src[:30]:<30} {exit_[:32]:<32}")
