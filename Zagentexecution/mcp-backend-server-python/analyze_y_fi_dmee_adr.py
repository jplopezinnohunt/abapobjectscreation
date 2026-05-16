"""
1) Re-extract DMEE_TREE_NODE for /SEPA_CT_UNES V001 D01 (fresh).
2) Find all nodes whose MP_EXIT_FUNC = Y_FI_DMEE_ADR.
3) Extract Y_FI_DMEE_ADR FM source to see how the mapping works.
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

print("=== Re-extract DMEE_TREE_NODE /SEPA_CT_UNES V001 ===")
rows = rfc_read_paginated(c, "DMEE_TREE_NODE",
    fields=["NODE_ID","PARENT_ID","TECH_NAME","NODE_TYPE",
            "MP_SC_TAB","MP_SC_FLD","MP_EXIT_FUNC","MP_CONST",
            "CV_RULE","DATA_TYPE","LENGTH"],
    where="TREE_ID = '/SEPA_CT_UNES' AND VERSION = '001'",
    batch_size=200, throttle=0.0)
print(f"Got {len(rows)} nodes")

# Save updated CSV
csv_path = os.path.join(os.path.dirname(__file__), "..", "..",
                       "knowledge/domains/Payment/phase0/dmee_full",
                       "dmee_tree_node_d01_sepa_v001_fresh.csv")
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    if rows:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows: w.writerow(r)
print(f"Saved: {csv_path}\n")

# Group by MP_EXIT_FUNC
print("=== Distinct MP_EXIT_FUNC values ===")
exit_count = {}
for r in rows:
    e = (r.get("MP_EXIT_FUNC") or "").strip()
    if e:
        exit_count[e] = exit_count.get(e, 0) + 1
for e, n in sorted(exit_count.items(), key=lambda x: -x[1]):
    marker = " ★" if e == "Y_FI_DMEE_ADR" else ""
    print(f"  {n:3} × {e}{marker}")

# List Y_FI_DMEE_ADR nodes specifically
print("\n=== Nodes using Y_FI_DMEE_ADR ===")
by_id = {r["NODE_ID"]: r for r in rows}
def xpath(nid, _seen=None):
    if _seen is None: _seen = set()
    if nid in _seen or nid not in by_id: return ""
    _seen.add(nid)
    n = by_id[nid]
    p = n.get("PARENT_ID","").strip()
    t = (n.get("TECH_NAME") or "").strip()
    if p and p in by_id and p != nid:
        return f"{xpath(p,_seen)}/{t}" if t else xpath(p,_seen)
    return f"/{t}" if t else ""

for r in rows:
    if (r.get("MP_EXIT_FUNC") or "").strip() == "Y_FI_DMEE_ADR":
        xp = xpath(r["NODE_ID"])
        src = f"{r.get('MP_SC_TAB','').strip()}-{r.get('MP_SC_FLD','').strip()}"
        const = r.get("MP_CONST","").strip()
        print(f"  {xp[:80]:<80} src={src:<20} const={const}")

# Pull Y_FI_DMEE_ADR FM source
print("\n=== Y_FI_DMEE_ADR source ===")
try:
    r = c.call("RPY_FUNCTIONMODULE_READ_NEW", FUNCTIONNAME="Y_FI_DMEE_ADR")
    out_path = os.path.join(os.path.dirname(__file__), "..", "..",
                           "extracted_code/FI/DMEE_full_inventory/Y_FI_DMEE_ADR.abap")
    parts = []
    for tabname in ("IMPORT_PARAMETER","EXPORT_PARAMETER","CHANGING_PARAMETER",
                    "TABLES_PARAMETER","EXCEPTION_LIST","SOURCE","GLOBAL_DATA"):
        tab = r.get(tabname)
        if tab:
            parts.append(f"* === {tabname} ===")
            for row in tab:
                if isinstance(row, dict):
                    parts.append(" | ".join(f"{k}={v}" for k, v in row.items() if v))
                else:
                    parts.append(str(row))
    src_text = "\n".join(parts)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(src_text)
    print(f"Saved: {out_path}")
    # Print interface params
    for tabname in ("IMPORT_PARAMETER","EXPORT_PARAMETER","CHANGING_PARAMETER","TABLES_PARAMETER"):
        tab = r.get(tabname) or []
        if tab:
            print(f"\n--- {tabname} ---")
            for row in tab:
                print(f"  {row}")
    # Show first 60 lines of SOURCE
    print("\n--- SOURCE (first 80 lines) ---")
    src_tab = r.get("SOURCE") or []
    for i, row in enumerate(src_tab[:80], 1):
        line = row.get("LINE","") if isinstance(row, dict) else str(row)
        print(f"  {i:3} {line}")
except Exception as e:
    print(f"FM read error: {e}")
