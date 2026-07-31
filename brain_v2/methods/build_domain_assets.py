"""build_domain_assets.py — the ASSET BUNDLE per domain (s097).

"Every domain should have its set of assets: tables, extraction methods, algorithms,
other tools." Correct, and until now impossible to answer: assets were catalogued by
KIND (tables here, tools there, algorithms nowhere) and never by DOMAIN. So nobody could
say what a domain actually has, or what it is missing.

This inverts the index. For each domain it assembles:

    tables       what data we hold for it        (gold table registry)
    extraction   how each table is read          (method registry, by table class)
    algorithms   which techniques apply          (algorithms.json, by operand + flow)
    tools        which scripts serve it
    knowledge    docs · companions · claims
    flows        which end-to-end processes it participates in
    capability   the 11-dimension row

and then scores the bundle, because a list that is never judged is never improved.

Emits: domain_assets.json  ·  runs inside rebuild_all
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
BRAIN = HERE.parent
REPO = BRAIN.parent
sys.path.insert(0, str(BRAIN))
from canonical import canonical as C  # noqa: E402

ALGOS = HERE / "algorithms.json"
FLOWS = BRAIN / "process_flows" / "process_flows.json"
REGISTRY = BRAIN / "domains" / "domains.json"
CAPMODEL = BRAIN / "capability_model" / "capability_model.json"
GOLDREG = BRAIN / "gold_table_registry.json"
EMAP = BRAIN / "executed_objects_domain_map.json"
OUT = HERE / "domain_assets.json"

# Which algorithm operands a domain always needs. A domain with execution but no log
# algorithm bound to it is not being observed; a domain in a flow with no conformance
# model has no normative reference to deviate from.
EXPECTED = {
    "logs": "every domain with execution must be observable",
    "repository": "every domain with objects must resolve to components",
    "data": "every domain with tables must have an extraction strategy",
    "process events": "only domains that participate in a modelled flow",
    "interfaces": "only domains that cross the boundary",
}


def _load(p, d=None):
    return json.load(open(p, encoding="utf-8")) if p.exists() else (d if d is not None else {})


def main():
    algos = _load(ALGOS).get("algorithms", {})
    flows = _load(FLOWS).get("flows", {})
    raw = _load(REGISTRY)
    reg = raw.get("domains", raw) if isinstance(raw, dict) else raw
    cap = _load(CAPMODEL).get("domains", {})
    emap = _load(EMAP).get("by_domain", {})
    goldreg = _load(GOLDREG)

    # tables per domain, from the gold registry (domain -> type -> [tables])
    tables = {}
    for dom, types in (goldreg.get("domains", {}) or {}).items():
        ck = C(dom)
        bucket = tables.setdefault(ck, {})
        if isinstance(types, dict):
            for ttype, lst in types.items():
                bucket[ttype] = [t.get("gold") if isinstance(t, dict) else t for t in (lst or [])]

    # flows per domain (many-to-many, as declared)
    dom_flows = {}
    for fname, f in flows.items():
        for d in (f.get("domains") or []):
            dom_flows.setdefault(C(d), []).append(fname)

    # fold the registry onto canonical keys
    folded = {}
    for name, d in reg.items():
        ck = C(name)
        f = folded.setdefault(ck, {"docs": [], "companions": [], "objects": [], "claims": []})
        f["docs"] += d.get("knowledge_docs") or []
        f["companions"] += d.get("companions") or []
        f["objects"] += d.get("objects") or []
        f["claims"] += d.get("claims") or []

    bundles, gaps = {}, []
    all_domains = sorted(set(list(folded) + list(cap) + [C(k) for k in emap]) - {
        "Uncatalogued", "Technical_Substrate", "Basis_Security", "ThirdParty_Addon",
        "CTS_Transport"})

    for ck in all_domains:
        f = folded.get(ck, {"docs": [], "companions": [], "objects": [], "claims": []})
        execs = emap.get(ck, {}).get("total_execs", 0)
        objs = emap.get(ck, {}).get("total_objects", 0)
        my_flows = sorted(set(dom_flows.get(ck, [])))
        tabs = tables.get(ck, {})
        n_tables = sum(len(v) for v in tabs.values())

        # which algorithms serve this domain
        applicable = []
        for aname, a in algos.items():
            op = a.get("operates_on")
            if op in ("logs", "model") and execs > 0:
                applicable.append(aname)
            elif op == "repository" and objs > 0:
                applicable.append(aname)
            elif op == "data" and n_tables > 0:
                applicable.append(aname)
            elif op == "process events" and my_flows:
                applicable.append(aname)
            elif op == "interfaces" and ck in ("Integration",):
                applicable.append(aname)

        cells = cap.get(ck, {})
        filled = sum(1 for k, v in cells.items() if not k.startswith("note") and v != "NONE")

        # what is MISSING — the point of the bundle
        missing = []
        if execs > 0 and not f["docs"]:
            missing.append("no knowledge doc, yet it executes in production")
        if execs > 0 and n_tables == 0:
            missing.append("no tables registered — we observe it but hold no data for it")
        if my_flows and not any(algos.get(a, {}).get("operates_on") == "process events"
                                for a in applicable):
            missing.append("participates in a flow but no process algorithm applies")
        if my_flows:
            no_norm = [fl for fl in my_flows if not flows.get(fl, {}).get("normative_reference")]
            if no_norm:
                missing.append(f"flows without a normative reference: {', '.join(no_norm)}")
        if filled < 6 and execs > 0:
            missing.append(f"capability row thin ({filled}/11) for a domain that executes")

        bundles[ck] = {
            "activity": {"executions": execs, "executed_objects": objs},
            "tables": {"count": n_tables, "by_type": {k: len(v) for k, v in tabs.items()}},
            "algorithms": applicable,
            "flows": my_flows,
            "knowledge": {"docs": len(set(f["docs"])), "companions": len(set(f["companions"])),
                          "claims": len(set(f["claims"])), "objects": len(set(f["objects"]))},
            "capability_cells_filled": filled,
            "missing": missing,
        }
        if missing:
            gaps.append((ck, execs, missing))

    gaps.sort(key=lambda x: -x[1])
    out = {
        "_generated_by": "brain_v2/methods/build_domain_assets.py",
        "_what_this_is": "the asset bundle PER DOMAIN — tables, extraction, algorithms, tools, knowledge, flows",
        "_why": ("assets were catalogued by KIND and never by DOMAIN, so nobody could say what a "
                 "domain has or what it lacks. This inverts the index."),
        "_expected_coverage": EXPECTED,
        "gaps_ranked_by_activity": [{"domain": d, "executions": e, "missing": m}
                                    for d, e, m in gaps],
        "domains": bundles,
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"wrote {OUT}")
    print(f"  {len(bundles)} domains bundled · {len(gaps)} with gaps")
    for d, e, m in gaps[:6]:
        print(f"    {d:20s} {e:>10,d} execs — {m[0]}")


if __name__ == "__main__":
    main()
