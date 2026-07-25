"""
explain_implementation.py  —  the DIFFERENTIATED capability
===========================================================
Given a process step (a tcode discovered by process mining), descend into the
brain to explain HOW it is IMPLEMENTED and WHY it behaves that way — the program,
tables/views, users, and the curated knowledge (claims, root cause, incident).
This is what Celonis/Signavio structurally cannot do: connect the mined process to
the CODE/OBJECTS/CONFIG that produce it.

Usage: python explain_implementation.py F.05 OB09 ME29N
"""
import os, sys, json, io
from collections import defaultdict

ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GRAPH = os.path.join(ROOT, "brain_v2", "output", "brain_v2_graph.json")
STATE = os.path.join(ROOT, "brain_v2", "brain_state.json")


def load():
    g = json.load(io.open(GRAPH, encoding="utf-8"))
    nodes = {n["id"]: n for n in g["nodes"]}
    edges = g.get("edges") or g.get("links") or []
    out, inn = defaultdict(list), defaultdict(list)
    for e in edges:
        f = e.get("from") or e.get("source"); t = e.get("to") or e.get("target")
        out[f].append((e.get("type"), t)); inn[t].append((e.get("type"), f))
    state = json.load(io.open(STATE, encoding="utf-8"))
    return nodes, out, inn, state.get("objects", {})


def explain(tcode, nodes, out, inn, objs):
    print(f"\n{'='*64}\nHOW IT WORKS:  {tcode}\n{'='*64}")
    tid = f"TRANSACTION:{tcode}"
    # 1. implementation edges from the connective layer
    progs = [t.split(':')[-1] for ty, t in out.get(tid, []) if ty == "EXECUTES_PROGRAM"]
    views = [t.split(':')[-1] for ty, t in out.get(tid, []) if ty == "MAINTAINS_VIEW"]
    ccs   = [t.split(':')[-1] for ty, t in out.get(tid, []) if ty == "USED_IN_CC"]
    users = [f.split(':')[-1] for ty, f in inn.get(tid, []) if ty == "OPERATES_TCODE"]
    if progs: print(f"  runs program(s):   {progs}")
    if views: print(f"  maintains table:   {views}")
    if ccs:   print(f"  used in co.codes:  {ccs[:8]}")
    if users: print(f"  real operators:    {len(users)} users e.g. {users[:5]}")
    # 2. for each program, its code-level dependencies (if parsed) + curated knowledge
    for p in progs:
        pobj = objs.get(p, {})
        rt = pobj.get("reads_tables", []); cf = pobj.get("calls_fms", [])
        if rt: print(f"  [{p}] reads tables:  {rt[:12]}")
        if cf: print(f"  [{p}] calls FMs:     {cf[:8]}")
    # 3. curated knowledge on the tcode + its objects (claims / root cause / incident)
    for name in [tcode] + progs + views:
        o = objs.get(name)
        if not o:
            continue
        if o.get("incident_root_cause"):
            print(f"  WHY ({name}): {o['incident_root_cause'][:200]}")
        if o.get("incident_fix_path"):
            print(f"  FIX ({name}): {o['incident_fix_path'][:160]}")
        cl = o.get("claims", [])
        if cl:
            verified = [c for c in cl if c.get("verified") == "CONFIRMED"]
            print(f"  knowledge ({name}): {len(cl)} claims ({len(verified)} machine-verified), "
                  f"e.g. \"{cl[0]['claim'][:120]}\"")
        if o.get("incidents"):
            print(f"  incidents ({name}): {o['incidents']}")
        if o.get("analysis_doc"):
            print(f"  deep-dive ({name}): {o['analysis_doc']}")


def main():
    tcodes = sys.argv[1:] or ["F.05", "OB09"]
    nodes, out, inn, objs = load()
    for tc in tcodes:
        explain(tc, nodes, out, inn, objs)
    print("\n(process step -> its real implementation + why. The process<->code unification.)")


if __name__ == "__main__":
    main()
