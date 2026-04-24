"""
phase0_d01_vs_p01_inventory.py — D01 vs P01 component inventory for structured address scope.

Goal: produce a complete diff of which code objects exist where, for all DMEE/payment/address
components in scope. User concern: some BAdIs may exist only in D01, not P01 — we need to know.

Target: D01 + P01, SNC/SSO, read-only
Output: knowledge/domains/Payment/phase0/d01_vs_p01_inventory.csv + .md
"""

from __future__ import annotations
import csv, json, sys
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # noqa

REPO = HERE.parent.parent
OUT_DIR = REPO / "knowledge" / "domains" / "Payment" / "phase0"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Component patterns to inventory — broad coverage
PATTERNS = [
    # DMEE-related classes (UNESCO custom)
    ("CLAS", "YCL_IDFI_CGI_DMEE%"),
    ("CLAS", "YCL_IDFI%DMEE%"),
    ("CLAS", "ZCL_IDFI_CGI_DMEE%"),
    # SAP standard DMEE classes (may be customer-extended)
    ("CLAS", "CL_IDFI_CGI_DMEE%"),
    # Enhancement implementations
    ("ENHO", "Y_IDFI_CGI_DMEE%"),
    ("ENHO", "Z_IDFI_CGI_DMEE%"),
    ("ENHO", "YENH_FI_DMEE%"),
    ("ENHO", "ZENH_FI_DMEE%"),
    # Function groups/modules related
    ("FUGR", "Y_FPAY%"),
    ("FUGR", "Z_FPAY%"),
    ("FUGR", "Y_DMEE%"),
    ("FUGR", "Z_DMEE%"),
    # DMEE tree objects (the trees themselves)
    ("DMEE", "PAYM/SEPA_CT_UNES"),
    ("DMEE", "PAYM/CITI/XML/UNESCO%"),
    ("DMEE", "PAYM/CGI_XML_CT_UNESCO%"),
    # Payment exit FMs
    ("FUNC", "Y_DMEE_EXIT%"),
    ("FUNC", "Z_DMEE_EXIT%"),
    # Enhancement spot implementations for FI_CGI_DMEE_EXIT_W_BADI
    ("ENHS", "FI_CGI_DMEE%"),
]


def tadir_probe(conn, pgmid_or_object: str, name_pattern: str) -> list[dict]:
    """Query TADIR for a pattern. object_type_or_pgmid: if 3-char use as OBJECT; uses R3TR as PGMID."""
    # Accept 4-char object types; R3TR is PGMID for repository objects
    obj = pgmid_or_object
    where = f"PGMID = 'R3TR' AND OBJECT = '{obj}' AND OBJ_NAME LIKE '{name_pattern}'"
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="TADIR",
                      DELIMITER="|",
                      ROWCOUNT=500,
                      OPTIONS=[{"TEXT": where}],
                      FIELDS=[{"FIELDNAME": "PGMID"}, {"FIELDNAME": "OBJECT"},
                              {"FIELDNAME": "OBJ_NAME"}, {"FIELDNAME": "DEVCLASS"},
                              {"FIELDNAME": "AUTHOR"}, {"FIELDNAME": "SRCSYSTEM"}])
        hits = []
        for d in r.get("DATA", []):
            vals = d.get("WA", "").split("|")
            rec = dict(zip(["PGMID", "OBJECT", "OBJ_NAME", "DEVCLASS", "AUTHOR", "SRCSYSTEM"],
                           [v.strip() for v in vals]))
            hits.append(rec)
        return hits
    except Exception as e:
        return [{"_error": f"{obj}/{name_pattern}: {e}"}]


def main():
    print("=" * 70)
    print("D01 vs P01 component inventory — structured address scope")
    print("=" * 70)

    p01 = get_connection("P01")
    try:
        d01 = get_connection("D01")
        d01_ok = True
    except Exception as e:
        print(f"D01 connection failed: {e}")
        d01 = None
        d01_ok = False

    # Aggregate by obj_name
    all_items = {}  # key: OBJECT|OBJ_NAME -> {p01, d01, devclass_p01, devclass_d01, ...}

    for obj, pat in PATTERNS:
        print(f"\n[{obj} {pat}]")
        p01_hits = tadir_probe(p01, obj, pat)
        d01_hits = tadir_probe(d01, obj, pat) if d01_ok else []
        print(f"  P01: {len([h for h in p01_hits if '_error' not in h])} hits")
        print(f"  D01: {len([h for h in d01_hits if '_error' not in h])} hits")
        for h in p01_hits:
            if "_error" in h: continue
            key = f"{h['OBJECT']}|{h['OBJ_NAME']}"
            it = all_items.setdefault(key, {"OBJECT": h['OBJECT'], "OBJ_NAME": h['OBJ_NAME']})
            it["in_p01"] = True
            it["devclass_p01"] = h['DEVCLASS']
            it["author_p01"] = h['AUTHOR']
        for h in d01_hits:
            if "_error" in h: continue
            key = f"{h['OBJECT']}|{h['OBJ_NAME']}"
            it = all_items.setdefault(key, {"OBJECT": h['OBJECT'], "OBJ_NAME": h['OBJ_NAME']})
            it["in_d01"] = True
            it["devclass_d01"] = h['DEVCLASS']
            it["author_d01"] = h['AUTHOR']

    p01.close()
    if d01_ok:
        d01.close()

    # Compute presence diff
    rows = []
    for key, item in all_items.items():
        in_p = item.get("in_p01", False)
        in_d = item.get("in_d01", False)
        if in_p and in_d:
            state = "BOTH"
        elif in_p:
            state = "P01_ONLY"
        elif in_d:
            state = "D01_ONLY"
        else:
            state = "NONE"
        rows.append({
            "object": item["OBJECT"],
            "name": item["OBJ_NAME"],
            "state": state,
            "devclass_p01": item.get("devclass_p01", ""),
            "devclass_d01": item.get("devclass_d01", ""),
            "author_p01": item.get("author_p01", ""),
            "author_d01": item.get("author_d01", ""),
        })

    # Summary
    from collections import Counter
    state_ct = Counter(r["state"] for r in rows)
    print(f"\n===== SUMMARY =====")
    print(f"  Total distinct objects: {len(rows)}")
    for s, c in state_ct.most_common():
        print(f"  {s}: {c}")

    # D01_ONLY objects in detail (the user's concern)
    d01_only = [r for r in rows if r["state"] == "D01_ONLY"]
    print(f"\n===== D01_ONLY (exists in DEV but not PROD) — {len(d01_only)} =====")
    for r in sorted(d01_only, key=lambda x: x["name"]):
        print(f"  {r['object']:<6} {r['name']:<45} devclass={r['devclass_d01']:<15} author={r['author_d01']}")

    # P01_ONLY
    p01_only = [r for r in rows if r["state"] == "P01_ONLY"]
    if p01_only:
        print(f"\n===== P01_ONLY (in PROD but NOT in DEV — possible anomaly) — {len(p01_only)} =====")
        for r in sorted(p01_only, key=lambda x: x["name"]):
            print(f"  {r['object']:<6} {r['name']:<45} devclass={r['devclass_p01']:<15} author={r['author_p01']}")

    # Save CSV
    out_csv = OUT_DIR / "d01_vs_p01_inventory.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["object", "name", "state", "devclass_p01", "devclass_d01", "author_p01", "author_d01"])
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x["state"], x["object"], x["name"])):
            w.writerow(r)
    print(f"\nSaved: {out_csv}")

    # Save summary JSON
    out_json = OUT_DIR / "d01_vs_p01_inventory.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(rows),
            "state_counts": dict(state_ct),
            "d01_only": d01_only,
            "p01_only": p01_only,
            "rows": rows,
        }, f, indent=2, ensure_ascii=False)
    print(f"Saved: {out_json}")


if __name__ == "__main__":
    main()
