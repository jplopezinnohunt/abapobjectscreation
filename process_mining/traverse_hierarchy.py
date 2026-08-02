"""ALGORITHM A12 — SET HIERARCHY TRAVERSAL.

WHAT IT ANSWERS
    "What does each organisational level actually consume?" — and the three questions that
    have to be answered first before that number means anything:
      does every master value roll up somewhere,
      does any value roll up in more than one place,
      and is the hierarchy one structure or several.

WHY IT EXISTS
    SAP keeps hierarchies as SETS: a set contains sets contains values. Nothing in the
    fact tables references them, so consumption is posted flat against a leaf and the
    roll-up exists only in configuration. Until the sets are traversed, a question like
    "what does this sector spend" has no mechanical answer at all.

THE TWO MEASUREMENTS THAT DECIDE WHETHER A ROLL-UP IS SAFE
    ORPHANS — master values that appear in no set. They post, they consume, and they
    appear under no total. Every roll-up silently under-reports by exactly their volume.
    MULTI-PARENT values — a value reachable from more than one node. Summing the nodes
    then double counts it. Both are normal in SAP and both are invisible unless measured,
    which is why they are reported before any amount is.

PORTABILITY
    The set class, the master it should cover and the fact table to join are declared, not
    coded. Point it at another class — cost centres, accounts, funds — and it traverses
    that instead.

USAGE
    python process_mining/traverse_hierarchy.py [spec.json]
"""

import collections
import io
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "brain_v2", "methods"))
from algorithm_memory import remember  # noqa: E402

DEFAULT_SPEC = os.path.join(HERE, "chain_spec.json")
# A cycle in a set hierarchy is a configuration error, not a shape. Stop rather than hang.
MAX_DEPTH = 40


def expand_leaf(valfrom, valto):
    """A set leaf is a RANGE. Single values dominate, but a range is a range.

    Ranges over non-numeric codes cannot be enumerated safely — `ADM` to `OPE` has no
    defined membership without the master — so those are returned as a marker for the
    caller to resolve against the master rather than guessed at.
    """
    a, b = (valfrom or "").strip(), (valto or "").strip()
    if not a:
        return []
    if not b or a == b:
        return [a]
    if a.isdigit() and b.isdigit() and len(b) <= 12:
        lo, hi = int(a), int(b)
        if 0 <= hi - lo <= 5000:
            w = len(a)
            return [str(x).zfill(w) for x in range(lo, hi + 1)]
    return [("__RANGE__", a, b)]


def traverse(cx, h):
    cls, sub_col = h["set_class"], h.get("subclass_column", "SUBCLASS")
    node_rows = cx.execute(
        'SELECT "%s",SETNAME,SUBSETNAME FROM SETNODE WHERE SETCLASS=?' % sub_col, (cls,)).fetchall()
    leaf_rows = cx.execute(
        'SELECT "%s",SETNAME,VALFROM,VALTO FROM SETLEAF WHERE SETCLASS=?' % sub_col,
        (cls,)).fetchall()
    head_rows = cx.execute(
        'SELECT "%s",SETNAME FROM SETHEADER WHERE SETCLASS=?' % sub_col, (cls,)).fetchall()

    children = collections.defaultdict(list)
    for sub, parent, child in node_rows:
        children[(sub, parent)].append((sub, child))
    leaves = collections.defaultdict(list)
    ranges = []
    for sub, name, a, b in leaf_rows:
        for v in expand_leaf(a, b):
            if isinstance(v, tuple):
                ranges.append({"subclass": sub, "set": name, "from": v[1], "to": v[2]})
            else:
                leaves[(sub, name)].append(v)

    allsets = set((s, n) for s, n in head_rows)
    ischild = set(v for vs in children.values() for v in vs)
    # A root is any set nothing points at. That includes FLAT sets — ones with leaves and
    # no child sets at all, which appear in SETLEAF and never in SETNODE. Defining a root
    # as "appears as a parent" silently drops them and reports their whole master as
    # orphaned, which is how a working hierarchy gets scored at 100% missing.
    roots = sorted((set(children) | set(leaves)) - ischild)

    # Walk every root. A value can be reached more than once and that is the point — the
    # paths are collected, not deduplicated, so multi-parent membership stays visible.
    paths = collections.defaultdict(list)
    depth_hist = collections.Counter()
    cycles = []

    def walk(node, path):
        if len(path) > MAX_DEPTH:
            cycles.append(" > ".join(path[:6]) + " ...")
            return
        if node in path_guard:
            cycles.append(" > ".join(list(path)[-4:] + [node[1]]))
            return
        path_guard.add(node)
        here = path + [node[1]]
        for v in leaves.get(node, []):
            paths[v].append(list(here))
            depth_hist[len(here)] += 1
        for ch in children.get(node, []):
            walk(ch, here)
        path_guard.discard(node)

    for r in roots:
        path_guard = set()
        walk(r, [])

    return {"roots": roots, "children": children, "leaves": leaves, "allsets": allsets,
            "paths": paths, "depth_hist": depth_hist, "ranges": ranges, "cycles": cycles}


def measure(cx, h, t):
    master_vals = set()
    if h.get("master_table"):
        master_vals = set((r[0] or "").strip() for r in cx.execute(
            'SELECT "%s" FROM "%s"' % (h["master_column"], h["master_table"])) if r[0])

    reached = set(t["paths"])
    # Reachable from several places is TWO different situations and only one is a defect.
    # Appearing in more than one ROOT TREE is versioning — here the trees are C/5 bienniums,
    # and a value living in both is correct; you pick a biennium. Appearing more than once
    # INSIDE one tree is what double counts a roll-up.
    multi, versioned = {}, {}
    for v, plist in t["paths"].items():
        roots_of = collections.Counter(p[0] for p in plist)
        within = max(roots_of.values())
        if within > 1:
            multi[v] = within
        if len(roots_of) > 1:
            versioned[v] = len(roots_of)
    orphans = sorted(master_vals - reached) if master_vals else []
    unknown = sorted(reached - master_vals) if master_vals else []

    rec = {
        "set_class": h["set_class"], "what": h.get("what"),
        "sets": len(t["allsets"]), "roots": t["roots"], "root_count": len(t["roots"]),
        "values_reached": len(reached),
        "depth_distribution": {str(k): v for k, v in sorted(t["depth_hist"].items())},
        "max_depth": max(t["depth_hist"]) if t["depth_hist"] else 0,
        "unenumerable_ranges": len(t["ranges"]),
        "cycles": t["cycles"][:5],
    }
    if master_vals:
        rec["master"] = "%s.%s" % (h["master_table"], h["master_column"])
        rec["master_values"] = len(master_vals)
        rec["orphans"] = len(orphans)
        rec["orphan_examples"] = orphans[:10]
        rec["orphan_pct"] = round(100.0 * len(orphans) / len(master_vals), 1)
        rec["in_hierarchy_not_in_master"] = len(unknown)
    rec["multi_parent_within_one_tree"] = len(multi)
    rec["multi_parent_examples"] = sorted(multi.items(), key=lambda x: -x[1])[:8]
    rec["values_in_several_root_trees"] = len(versioned)
    rec["_versioning_note"] = (
        "a value in several root trees is normally VERSIONING, not a defect — these roots "
        "are C/5 bienniums, so a fund centre belongs to both and a report must choose one. "
        "Only repetition INSIDE a single tree double counts a roll-up.")
    return rec, reached, multi, set(orphans)


def consumption(cx, h, t, multi, orphans):
    """What each level of the hierarchy actually consumes.

    Reported ONLY alongside the orphan and multi-parent counts. A roll-up total presented
    without them invites a reader to add the levels together, which is wrong whenever
    either number is non-zero.
    """
    f = h.get("fact")
    if not f:
        return None
    col, tab = f["column"], f["table"]
    vol = {k: n for k, n in cx.execute(
        'SELECT trim("%s"),count(*) FROM "%s" GROUP BY 1' % (col, tab)) if k}

    per_node = collections.Counter()
    for v, plist in t["paths"].items():
        n = vol.get(v, 0)
        if not n:
            continue
        for p in plist:
            for node in p:
                per_node[node] += n

    total = sum(vol.values())
    posted_orphan = sum(vol.get(v, 0) for v in orphans)
    # Counted per tree: repetition inside ONE tree is the double count. Cross-tree
    # repetition is versioning and is excluded, or every biennium would look like an error.
    double = 0
    for v, times in multi.items():
        double += vol.get(v, 0) * (times - 1)
    return {
        "fact": "%s.%s" % (tab, col), "fact_rows": total,
        "rows_on_orphan_values": posted_orphan,
        "rows_on_orphan_pct": round(100.0 * posted_orphan / total, 1) if total else 0,
        "rows_double_counted_if_levels_summed": double,
        "double_count_pct": round(100.0 * double / total, 1) if total else 0,
        "top_nodes_by_rows": per_node.most_common(15),
        "_how_to_read": (
            "top_nodes_by_rows is a ROLL-UP: a parent includes everything beneath it, so the "
            "levels must never be added together. rows_on_orphan_values is what no node "
            "contains at all — that volume is missing from every total on this hierarchy."),
    }


def main(argv):
    spec_path = argv[0] if argv and not argv[0].startswith("--") else DEFAULT_SPEC
    if not os.path.isabs(spec_path):
        spec_path = os.path.join(ROOT, spec_path)
    spec = json.load(io.open(spec_path, encoding="utf-8"))
    db = spec["golden_db"]
    db = db if os.path.isabs(db) else os.path.join(ROOT, db)
    cx = sqlite3.connect("file:%s?mode=ro" % db, uri=True)

    out = []
    print("A12 SET HIERARCHY TRAVERSAL  instance=%s" % spec.get("instance"))
    print("=" * 78)
    for h in spec.get("hierarchies", []):
        t = traverse(cx, h)
        rec, reached, multi, orphans = measure(cx, h, t)
        rec["consumption"] = consumption(cx, h, t, multi, orphans)
        out.append(rec)

        print("\nclase %s — %s" % (h["set_class"], h.get("what")))
        print("   %d sets · %d raices · %d valores alcanzados · profundidad max %d"
              % (rec["sets"], rec["root_count"], rec["values_reached"], rec["max_depth"]))
        if "orphans" in rec:
            print("   maestro %s: %d valores, HUERFANOS %d (%.1f%%)"
                  % (rec["master"], rec["master_values"], rec["orphans"], rec["orphan_pct"]))
            if rec["orphan_examples"]:
                print("      ej: %s" % ", ".join(rec["orphan_examples"][:8]))
        print("   repetidos DENTRO de un mismo arbol (doble conteo): %d"
              % rec["multi_parent_within_one_tree"])
        print("   presentes en VARIOS arboles raiz (versionado, no defecto): %d"
              % rec["values_in_several_root_trees"])
        if rec["multi_parent_examples"]:
            print("      ej: %s" % ", ".join("%s x%d" % (v, n)
                                             for v, n in rec["multi_parent_examples"][:6]))
        if rec["cycles"]:
            print("   CICLOS detectados: %s" % rec["cycles"][:2])
        c = rec["consumption"]
        if c:
            print("   sobre %s (%d filas):" % (c["fact"], c["fact_rows"]))
            print("      filas en valores HUERFANOS: %d (%.1f%%) — fuera de todo total"
                  % (c["rows_on_orphan_values"], c["rows_on_orphan_pct"]))
            print("      filas DUPLICADAS si se suman niveles: %d (%.1f%%)"
                  % (c["rows_double_counted_if_levels_summed"], c["double_count_pct"]))
            print("      nodos mayores: %s"
                  % ", ".join("%s %d" % (k, v) for k, v in c["top_nodes_by_rows"][:6]))

    p = os.path.join(ROOT, "brain_v2", "hierarchy_traversal.json")
    json.dump({"_algorithm": "A12 traverse_hierarchy.py", "instance": spec.get("instance"),
               "hierarchies": out},
              io.open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for rec in out:
        c = rec.get("consumption") or {}
        remember(subject="SETCLASS %s" % rec["set_class"], kind="CARRIER",
                 learned_by="A12_traverse_hierarchy", session=spec.get("session"),
                 fact=("%s — %d sets, %d roots, max depth %d, %d values reached; %s orphans, "
                       "%d multi-parent values"
                       % (rec.get("what"), rec["sets"], rec["root_count"], rec["max_depth"],
                          rec["values_reached"], rec.get("orphans", "n/a"),
                          rec["multi_parent_within_one_tree"])),
                 evidence=json.dumps({k: rec.get(k) for k in
                                      ("orphan_pct", "multi_parent_within_one_tree",
                                       "values_in_several_root_trees", "max_depth")}),
                 implication=("never sum levels of this hierarchy — a parent already contains "
                              "its children, and %.1f%% of fact rows would double count. "
                              "%.1f%% of rows sit on values no node contains."
                              % (c.get("double_count_pct", 0), c.get("rows_on_orphan_pct", 0))))
    print("\nescrito: brain_v2/hierarchy_traversal.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
