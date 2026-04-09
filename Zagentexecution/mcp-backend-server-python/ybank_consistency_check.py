"""
ybank_consistency_check.py
==========================
Full consistency check of YBANK sets in D01:
  - SETHEADER vs SETLEAF (line count match)
  - SETNODE references (all children exist as headers)
  - SETHEADERT (texts in all expected languages)
  - SETLINE (line descriptions vs SETLEAF entries)
  - Orphan detection (SETLEAF without SETHEADER, etc.)

GRW_SET = SETHEADER + SETHEADERT + SETNODE + SETLEAF + SETLINE
"""
import sys, os, io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

SYSTEM = "D01"
PASS_COUNT = 0
FAIL_COUNT = 0
WARN_COUNT = 0


def status(msg, level="PASS"):
    global PASS_COUNT, FAIL_COUNT, WARN_COUNT
    print(f"  [{level}] {msg}")
    if level == "PASS": PASS_COUNT += 1
    elif level == "FAIL": FAIL_COUNT += 1
    elif level == "WARN": WARN_COUNT += 1


def safe_read(conn, table, fields, where):
    from pyrfc import RFCError
    try:
        return rfc_read_paginated(conn, table, fields, where,
                                  batch_size=5000, throttle=0.5)
    except RFCError as e:
        if "TABLE_NOT_AVAILABLE" in str(e) or "NOT_AUTHORIZED" in str(e):
            print(f"  [WARN] {table}: {e}")
            return []
        raise


def run():
    print(f"{'='*70}")
    print(f"  YBANK SET CONSISTENCY CHECK — {SYSTEM}")
    print(f"{'='*70}")

    conn = get_connection(SYSTEM)

    # ── 1. SETHEADER — all set headers ──
    print(f"\n--- CHECK 1: SETHEADER ---")
    headers = safe_read(conn, "SETHEADER",
        ["SETCLASS", "SUBCLASS", "SETNAME", "SETTYPE"],
        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")
    # Also get audit fields separately
    headers_audit = safe_read(conn, "SETHEADER",
        ["SETNAME", "UPDUSER", "UPDDATE", "UPDTIME"],
        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")
    audit_map = {r["SETNAME"].strip(): r for r in headers_audit}

    header_names = set()
    for h in headers:
        sn = h.get("SETNAME","").strip()
        header_names.add(sn)

    print(f"  Found {len(header_names)} set headers")
    for sn in sorted(header_names):
        a = audit_map.get(sn, {})
        print(f"    {sn} | upd={a.get('UPDUSER','').strip()} "
              f"{a.get('UPDDATE','').strip()} {a.get('UPDTIME','').strip()}")

    # ── 2. SETHEADERT — texts per language ──
    print(f"\n--- CHECK 2: SETHEADERT (texts) ---")
    texts = safe_read(conn, "SETHEADERT",
        ["SETCLASS", "SUBCLASS", "SETNAME", "LANESSION", "DESSION"],
        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")

    text_map = {}  # setname -> {lang: description}
    for t in texts:
        sn = t.get("SETNAME","").strip()
        lang = t.get("LANESSION","").strip()
        desc = t.get("DESSION","").strip()
        if sn not in text_map:
            text_map[sn] = {}
        text_map[sn][lang] = desc

    expected_langs = {"D", "E", "F", "P"}  # German, English, French, Portuguese
    for sn in sorted(header_names):
        langs = text_map.get(sn, {})
        lang_keys = set(langs.keys())
        missing = expected_langs - lang_keys
        if missing:
            status(f"{sn}: langs={sorted(lang_keys)}, MISSING: {sorted(missing)}", "WARN")
        else:
            status(f"{sn}: all 4 langs present (D/E/F/P)")
        # Show English text
        if "E" in langs:
            print(f"         EN: {langs['E']}")

    # ── 3. SETNODE — hierarchy consistency ──
    print(f"\n--- CHECK 3: SETNODE (hierarchy) ---")
    nodes = safe_read(conn, "SETNODE",
        ["SETCLASS", "SUBCLASS", "SETNAME", "LINEID", "SUBSETCLS", "SUBSETSCLS", "SUBSETNAME"],
        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")

    parent_child = {}  # parent -> [children]
    all_children = set()
    all_parents = set()
    for n in nodes:
        parent = n.get("SETNAME","").strip()
        child = n.get("SUBSETNAME","").strip()
        if parent not in parent_child:
            parent_child[parent] = []
        parent_child[parent].append(child)
        all_children.add(child)
        all_parents.add(parent)

    # Check: every child referenced in SETNODE must exist in SETHEADER
    for parent in sorted(parent_child.keys()):
        children = parent_child[parent]
        for child in children:
            if child in header_names:
                status(f"{parent} -> {child}: child exists in SETHEADER")
            else:
                status(f"{parent} -> {child}: child MISSING from SETHEADER", "FAIL")

    # Check: leaf sets (no children) should have SETLEAF entries
    leaf_sets = header_names - all_parents
    print(f"\n  Leaf sets (no children): {sorted(leaf_sets)}")
    branch_sets = header_names & all_parents
    print(f"  Branch sets (have children): {sorted(branch_sets)}")

    # ── 4. SETLEAF — entries per set ──
    print(f"\n--- CHECK 4: SETLEAF (values) ---")
    leaves = safe_read(conn, "SETLEAF",
        ["SETCLASS", "SUBCLASS", "SETNAME", "LINEID", "VALSIGN", "VALOPTION", "VALFROM", "VALTO", "SEQNR"],
        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")

    leaf_counts = {}
    leaf_by_set = {}
    for l in leaves:
        sn = l.get("SETNAME","").strip()
        leaf_counts[sn] = leaf_counts.get(sn, 0) + 1
        if sn not in leaf_by_set:
            leaf_by_set[sn] = []
        leaf_by_set[sn].append(l)

    # Leaf sets should have entries, branch sets should not
    for sn in sorted(header_names):
        count = leaf_counts.get(sn, 0)
        is_leaf = sn in leaf_sets
        is_branch = sn in branch_sets

        if is_leaf and count == 0:
            status(f"{sn}: LEAF set with 0 entries", "FAIL")
        elif is_leaf and count > 0:
            status(f"{sn}: {count} entries")
        elif is_branch and count > 0:
            status(f"{sn}: BRANCH set with {count} entries (unexpected but valid)", "WARN")
        elif is_branch and count == 0:
            status(f"{sn}: branch set, 0 leaf entries (correct)")

    # Check for orphan SETLEAF (entries for sets without header)
    orphan_sets = set(leaf_counts.keys()) - header_names
    if orphan_sets:
        for sn in sorted(orphan_sets):
            status(f"ORPHAN: {sn} has {leaf_counts[sn]} SETLEAF entries but no SETHEADER", "FAIL")
    else:
        status("No orphan SETLEAF entries")

    # ── 5. SETLINE — line descriptions ──
    print(f"\n--- CHECK 5: SETLINE (line descriptions) ---")
    setlines = safe_read(conn, "SETLINE",
        ["SETCLASS", "SUBCLASS", "SETNAME", "LINEID", "LANESSION", "DESSION"],
        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")

    line_map = {}  # setname -> {lineid: {lang: desc}}
    for sl in setlines:
        sn = sl.get("SETNAME","").strip()
        lid = sl.get("LINEID","").strip()
        lang = sl.get("LANESSION","").strip()
        desc = sl.get("DESSION","").strip()
        if sn not in line_map:
            line_map[sn] = {}
        if lid not in line_map[sn]:
            line_map[sn][lid] = {}
        line_map[sn][lid][lang] = desc

    # Cross-check: every SETLEAF LINEID should have SETLINE descriptions
    leaf_lineids = {}  # setname -> set of lineids
    for l in leaves:
        sn = l.get("SETNAME","").strip()
        lid = l.get("LINEID","").strip()
        if sn not in leaf_lineids:
            leaf_lineids[sn] = set()
        leaf_lineids[sn].add(lid)

    # Also check SETNODE lineids
    node_lineids = {}
    for n in nodes:
        sn = n.get("SETNAME","").strip()
        lid = n.get("LINEID","").strip()
        if sn not in node_lineids:
            node_lineids[sn] = set()
        node_lineids[sn].add(lid)

    for sn in sorted(header_names):
        sl_ids = set(line_map.get(sn, {}).keys())
        lf_ids = leaf_lineids.get(sn, set())
        nd_ids = node_lineids.get(sn, set())
        all_ids = lf_ids | nd_ids

        if not sl_ids and not all_ids:
            continue  # empty set, ok

        missing_lines = all_ids - sl_ids
        orphan_lines = sl_ids - all_ids

        if not missing_lines and not orphan_lines:
            status(f"{sn}: SETLINE consistent ({len(sl_ids)} line descriptions)")
        else:
            if missing_lines:
                status(f"{sn}: {len(missing_lines)} LINEIDs without SETLINE description: {sorted(missing_lines)}", "WARN")
            if orphan_lines:
                status(f"{sn}: {len(orphan_lines)} orphan SETLINE entries (no matching SETLEAF/SETNODE): {sorted(orphan_lines)}", "WARN")

    # ── 6. Duplicate check in SETLEAF ──
    print(f"\n--- CHECK 6: Duplicate SETLEAF values ---")
    for sn in sorted(leaf_by_set.keys()):
        entries = leaf_by_set[sn]
        values = [(e.get("VALOPTION","").strip(), e.get("VALFROM","").strip(), e.get("VALTO","").strip())
                  for e in entries]
        seen = set()
        dupes = []
        for v in values:
            if v in seen:
                dupes.append(v)
            seen.add(v)
        if dupes:
            status(f"{sn}: {len(dupes)} DUPLICATE values: {dupes[:5]}", "FAIL")
        else:
            status(f"{sn}: no duplicates ({len(values)} unique values)")

    # ── SUMMARY ──
    print(f"\n{'='*70}")
    print(f"  SUMMARY: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL / {WARN_COUNT} WARN")
    print(f"{'='*70}")

    conn.close()


if __name__ == "__main__":
    run()
