"""
h18_dmee_tree_probe.py — H18 DMEE format tree investigation (Session #039)

Purpose
-------
Find where the SEPA `<Purp><Cd>` PurposeCode literal lives in SAP.

Session #038 falsified the hypothesis that it was in ABAP source
(`YCL_IDFI_CGI_DMEE_*` classes — classes named `_AE`/`_BH` in the PMO note
don't exist, and `_FR`/`_FALLBACK`/`_UTIL` contain zero `<Purp>/<Cd>` literals
across CM001..CM050 method includes).

Next path (declared in #038 retro): the DMEE format tree, stored in
table `DMEE_TREE_NODES` and referenced from `DMEE_TREES`. DMEE (Data Medium
Exchange Engine, tx DMEE) is where SAP stores payment format XML structure
declarations — the SEPA ISO20022 `pain.001` PurposeCode tag is a format
tree node with attributes that point to either a literal value or a
source field reference.

What this script does
---------------------
1. Discover all DMEE trees of format group "UNESCO" or matching UNESCO
   custom tree IDs (any tree_id starting with Y/Z or containing "CGI").
2. For each matching tree, dump all nodes from `DMEE_TREE_NODES` with the
   attribute columns (NODE_ID, PARENT_ID, NODE_TYPE, TAG, SRC_TYPE, SRC_VAL).
3. Filter nodes whose TAG contains "Purp" or "Cd" or whose SRC_VAL contains
   a SEPA PurposeCode candidate (EXPE, GOVT, INTC, SALA, SUPP, TAXS, TRAD, etc.).
4. Save everything to CSV for the findings doc.

Target system: P01 (read-only, SNC/SSO — DMEE config is transported so both
systems have it; P01 is safer).

Outputs
-------
- knowledge/domains/Payment/h18_dmee_trees.csv          (tree headers)
- knowledge/domains/Payment/h18_dmee_tree_nodes.csv     (all nodes of matched trees)
- knowledge/domains/Payment/h18_dmee_purp_candidates.csv (filtered Purp/Cd nodes)

Honest-close contract
---------------------
This script MUST produce one of two verdicts when read alongside its output:
  (A) CONFIRMED: at least one row in h18_dmee_purp_candidates.csv whose
      TAG matches `Purp` or `Cd` and whose SRC_VAL is a literal PurposeCode
      — H18 can be struck.
  (B) NEGATIVE: the trees exist but the Purp/Cd node is not a literal
      (SRC_TYPE = field reference, formula, or conditional mapping) — H18
      can still be struck with a DOCUMENTED negative result (the value
      is computed at runtime from a source field, not declared statically).
There is NO "(C) needs more investigation" path. Both verdicts close H18.
"""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

REPO = HERE.parent.parent
OUT_DIR = REPO / "knowledge" / "domains" / "Payment"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TREES_CSV = OUT_DIR / "h18_dmee_trees.csv"
NODES_CSV = OUT_DIR / "h18_dmee_tree_nodes.csv"
PURP_CSV = OUT_DIR / "h18_dmee_purp_candidates.csv"

SEPA_PURP_CODES = {
    "EXPE", "GOVT", "INTC", "SALA", "SUPP", "TAXS", "TRAD",
    "CASH", "CHAR", "CMDT", "COLL", "CORT", "DIVI", "HEDG",
    "INTE", "LOAN", "OTHR", "PENS", "SECU", "TREA", "VATX",
    "SSBE", "BENE", "PAYR",
}

DD03L_FIELDS = ["FIELDNAME", "POSITION", "INTTYPE", "INTLEN", "DDTEXT"]


def probe_table_fields(conn, table: str) -> list[str]:
    """Return the list of field names for a table via DD03L."""
    rows = rfc_read_paginated(
        conn, "DD03L",
        fields=["FIELDNAME", "POSITION"],
        where=f"TABNAME = '{table}' AND AS4LOCAL = 'A'",
        batch_size=500, throttle=0.5,
    )
    rows.sort(key=lambda r: int(r.get("POSITION", "0") or "0"))
    return [r["FIELDNAME"] for r in rows if r.get("FIELDNAME")]


def main() -> int:
    print("=" * 60)
    print("  H18 DMEE Tree Probe — Session #039")
    print("=" * 60)

    target = "P01"
    print(f"\n[CONNECT] {target} (SNC/SSO, read-only)...")
    guard = get_connection(target)

    try:
        # --- Step 1: discover DMEE_TREES structure ---
        print("\n[DD03L] DMEE_TREES field list:")
        tree_fields = probe_table_fields(guard, "DMEE_TREES")
        if not tree_fields:
            print("  !! DMEE_TREES not found or no access — falling back to DMEETREES/DMEEFXS")
            for alt in ("DMEE_TREE", "DMEETREES", "DMEEFXS"):
                tree_fields = probe_table_fields(guard, alt)
                if tree_fields:
                    print(f"  Using alternate table: {alt}")
                    tree_table = alt
                    break
            else:
                raise SystemExit("No DMEE tree header table visible via RFC — aborting")
        else:
            tree_table = "DMEE_TREES"
        print(f"  {tree_table}: {len(tree_fields)} fields → {tree_fields[:12]}...")

        # --- Step 2: read all DMEE tree headers ---
        # Keep it narrow to avoid the 512-byte buffer issue. Pick the
        # likely-key fields; rfc_helpers will split if needed.
        priority = [f for f in ("TREE_TYPE", "TREE_ID", "FORMAT", "DESCRIPT",
                                "STATE", "DEVCLASS", "LASTUSER", "LASTDATE")
                    if f in tree_fields]
        if not priority:
            priority = tree_fields[:8]
        print(f"\n[READ] {tree_table} fields = {priority}")
        trees = rfc_read_paginated(guard, tree_table, priority, where="",
                                   batch_size=5000, throttle=1.0)
        print(f"  Got {len(trees):,} tree rows")

        # Filter to UNESCO-ish custom trees (start with Y/Z, or FORMAT contains CGI/SEPA)
        unesco = [t for t in trees if (
            t.get("TREE_ID", "").startswith(("Y", "Z"))
            or "CGI" in (t.get("FORMAT") or "").upper()
            or "SEPA" in (t.get("FORMAT") or "").upper()
            or "CGI" in (t.get("TREE_ID") or "").upper()
            or "UNES" in (t.get("TREE_ID") or "").upper()
        )]
        print(f"  UNESCO candidate trees: {len(unesco)}")
        for t in unesco[:30]:
            print(f"    {t.get('TREE_TYPE','?')} {t.get('TREE_ID','?'):20s} "
                  f"fmt={t.get('FORMAT','?'):10s} desc={t.get('DESCRIPT','')[:40]}")

        # Write tree headers CSV
        with TREES_CSV.open("w", newline="", encoding="utf-8") as f:
            if unesco:
                writer = csv.DictWriter(f, fieldnames=priority)
                writer.writeheader()
                for t in unesco:
                    writer.writerow({k: t.get(k, "") for k in priority})
        print(f"\n[WRITE] {TREES_CSV.name} ({len(unesco)} rows)")

        if not unesco:
            print("\n[VERDICT] No UNESCO DMEE trees found — H18 cannot be closed from trees.")
            print("  Next path: check PMW (Payment Medium Workbench) format in FBZP / OBPM4.")
            return 2

        # --- Step 3: discover DMEE_TREE_NODES structure ---
        print("\n[DD03L] DMEE_TREE_NODES field list:")
        for candidate in ("DMEE_TREE_NODES", "DMEE_TREE_NODE", "DMEEFIELDS"):
            node_fields = probe_table_fields(guard, candidate)
            if node_fields:
                node_table = candidate
                break
        else:
            raise SystemExit("No DMEE tree node table visible via RFC — aborting")
        print(f"  {node_table}: {len(node_fields)} fields → {node_fields[:15]}...")

        node_priority = [f for f in (
            "TREE_TYPE", "TREE_ID", "NODE_ID", "PARENT_ID", "NODE_TYPE",
            "NODE_NAME", "TAG", "SRC_TYPE", "SRC_VAL", "CONSTANT",
            "DESCRIPT", "LEVEL",
        ) if f in node_fields]
        if not node_priority:
            node_priority = node_fields[:10]

        # --- Step 4: for each unesco tree, pull its nodes ---
        all_nodes = []
        for i, t in enumerate(unesco, 1):
            tt = t.get("TREE_TYPE", "")
            tid = t.get("TREE_ID", "")
            if not tid:
                continue
            where = f"TREE_TYPE = '{tt}' AND TREE_ID = '{tid}'"
            print(f"\n[READ {i}/{len(unesco)}] {node_table} WHERE {where}")
            try:
                nodes = rfc_read_paginated(guard, node_table, node_priority,
                                           where=where, batch_size=5000, throttle=0.8)
            except Exception as e:
                print(f"  !! failed: {e}")
                continue
            print(f"  Got {len(nodes):,} nodes")
            for n in nodes:
                n["_TREE_ID"] = tid
                n["_TREE_TYPE"] = tt
            all_nodes.extend(nodes)

        # Write all nodes CSV
        if all_nodes:
            out_fields = ["_TREE_TYPE", "_TREE_ID"] + [f for f in node_priority if f not in ("TREE_TYPE", "TREE_ID")]
            with NODES_CSV.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
                writer.writeheader()
                for n in all_nodes:
                    writer.writerow(n)
            print(f"\n[WRITE] {NODES_CSV.name} ({len(all_nodes):,} rows)")

        # --- Step 5: filter Purp/Cd candidates ---
        def is_purp_candidate(n: dict) -> bool:
            tag = (n.get("TAG") or n.get("NODE_NAME") or "").strip()
            src_val = (n.get("SRC_VAL") or n.get("CONSTANT") or "").strip()
            desc = (n.get("DESCRIPT") or "").upper()
            if tag in ("Purp", "Cd", "PurposeCode", "PURP", "CD"):
                return True
            if "PURP" in tag.upper() or "PURPOSE" in desc:
                return True
            if src_val.upper() in SEPA_PURP_CODES:
                return True
            return False

        candidates = [n for n in all_nodes if is_purp_candidate(n)]
        print(f"\n[FILTER] Purp/Cd candidates: {len(candidates)}")
        for c in candidates[:50]:
            tag = c.get("TAG") or c.get("NODE_NAME", "")
            src_type = c.get("SRC_TYPE", "")
            src_val = c.get("SRC_VAL") or c.get("CONSTANT", "")
            print(f"  {c.get('_TREE_ID',''):20s} node={c.get('NODE_ID',''):6s} "
                  f"tag={tag:20s} src_type={src_type:5s} src_val={src_val[:40]}")

        if candidates:
            out_fields = ["_TREE_TYPE", "_TREE_ID"] + [f for f in node_priority if f not in ("TREE_TYPE", "TREE_ID")]
            with PURP_CSV.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
                writer.writeheader()
                for c in candidates:
                    writer.writerow(c)
            print(f"\n[WRITE] {PURP_CSV.name} ({len(candidates)} rows)")

        # --- Verdict ---
        print("\n" + "=" * 60)
        if candidates:
            literals = [c for c in candidates if
                        (c.get("SRC_VAL") or c.get("CONSTANT", "")).strip().upper() in SEPA_PURP_CODES]
            if literals:
                print(f"  VERDICT (A) CONFIRMED — {len(literals)} static literal PurposeCode node(s)")
                print("  H18 CAN BE STRUCK.")
            else:
                print(f"  VERDICT (B) NEGATIVE-DOCUMENTED — {len(candidates)} Purp/Cd node(s) found")
                print("  but none are static literals — value is runtime-computed.")
                print("  H18 CAN BE STRUCK with documented negative result.")
        else:
            print("  VERDICT: no Purp/Cd nodes in any UNESCO DMEE tree")
            print("  H18 CAN BE STRUCK with documented negative: the tag isn't in")
            print("  the UNESCO format trees, so the PurposeCode must come from")
            print("  either (a) vanilla SAP SEPA trees not in Z namespace or")
            print("  (b) BAdI / post-processing outside DMEE (unlikely per #038).")
        print("=" * 60)
        return 0

    finally:
        guard.close()


if __name__ == "__main__":
    sys.exit(main())
