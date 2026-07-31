"""measure_portability.py — how much of what we know would survive installation #2 (s097).

The improvement mechanism ranks algorithms by HEALTH: unguarded, stale, fragile. That is
maintenance. It does not measure DISTANCE TO THE GOAL, and the goal is a product that
instantiates against another organisation.

This measures it directly. Every resolved answer now carries the rung that produced it,
and each rung is either tenant-invariant or not:

    sap_component                       SAP's own taxonomy — travels unchanged
    sap_component_via_function_group    same chain, one hop — travels unchanged
    curated_overlay                     OUR hand-made map — does NOT travel
    unresolved                          no answer anywhere

**The low-confidence answers are the map of what will break next.** Not a guess about
fragility: the actual list of things we know only because someone here typed them.

The uncomfortable framing, and the reason this exists: every algorithm we have is
validated on n=1. Forty-three golden cases, all UNESCO facts. Until the invariant share is
measured, "portable" is an aspiration.
"""
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
BRAIN = HERE.parent
REPO = BRAIN.parent
sys.path.insert(0, str(BRAIN))
from component_map import resolve_domain  # noqa: E402

EMAP = BRAIN / "executed_objects_domain_map.json"
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT = HERE / "portability.json"


def main():
    emap = json.load(open(EMAP, encoding="utf-8")) if EMAP.exists() else {}

    # weight by EXECUTIONS, not by object count: a rung that resolves one object called a
    # million times matters more than one that resolves a hundred called twice.
    by_rung = Counter()
    execs_by_rung = Counter()
    dom_rungs = defaultdict(Counter)

    for dom, objs in emap.get("top_objects_by_domain", {}).items():
        for o in objs:
            r = resolve_domain(o["object"])
            rung = r["rung"]
            by_rung[rung] += 1
            execs_by_rung[rung] += o.get("execs") or 0
            dom_rungs[dom][rung] += 1

    invariant_objs = by_rung["sap_component"] + by_rung["sap_component_via_function_group"]
    tenant_objs = by_rung["curated_overlay"]
    resolved_objs = invariant_objs + tenant_objs
    invariant_execs = (execs_by_rung["sap_component"]
                       + execs_by_rung["sap_component_via_function_group"])
    tenant_execs = execs_by_rung["curated_overlay"]
    resolved_execs = invariant_execs + tenant_execs

    # what specifically will not travel
    curated_size = 0
    if GOLD.exists():
        try:
            con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
            curated_size = con.execute(
                "SELECT COUNT(*) FROM tfdir_custom WHERE APP_DOMAIN IS NOT NULL "
                "AND APP_DOMAIN <> ''").fetchone()[0]
            con.close()
        except sqlite3.Error:
            pass

    out = {
        "_generated_by": "brain_v2/methods/measure_portability.py",
        "_question": "how much of what we know would survive installation #2?",
        "_method": ("every answer carries the rung that produced it; each rung is either "
                    "tenant-invariant or not. Weighted by EXECUTIONS, because a rung that "
                    "resolves one object called a million times matters more than one that "
                    "resolves a hundred called twice."),
        "by_rung_objects": dict(by_rung),
        "by_rung_executions": dict(execs_by_rung),
        "portability": {
            "invariant_share_of_resolved_objects":
                round(100.0 * invariant_objs / max(1, resolved_objs), 1),
            "invariant_share_of_resolved_executions":
                round(100.0 * invariant_execs / max(1, resolved_execs), 1),
            "objects_that_will_not_travel": tenant_objs,
            "executions_that_will_not_travel": tenant_execs,
        },
        "what_will_not_travel": {
            "curated_overlay_entries": curated_size,
            "_meaning": ("hand-curated function-module -> domain assignments. On another "
                         "tenant these are wrong by default: the Z/Y namespace is the "
                         "customer's own. The CHAIN travels; this CONTENT does not."),
            "_but": ("this is not a defect to remove. Custom objects have no SAP component "
                     "BY DEFINITION, and they are exactly where the differentiating "
                     "processes live. The fix is not to delete the overlay — it is to "
                     "DERIVE it from what each custom object reads and writes, so the "
                     "derivation travels even though the content does not."),
        },
        "per_domain": {d: dict(c) for d, c in sorted(
            dom_rungs.items(), key=lambda x: -sum(x[1].values()))},
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    p = out["portability"]
    print(f"wrote {OUT}")
    print(f"  by rung (objects):    {dict(by_rung)}")
    print(f"\n  PORTABILITY — what survives installation #2:")
    print(f"    {p['invariant_share_of_resolved_objects']}% of resolved OBJECTS are tenant-invariant")
    print(f"    {p['invariant_share_of_resolved_executions']}% of resolved EXECUTIONS are tenant-invariant")
    print(f"    {p['objects_that_will_not_travel']} objects / "
          f"{p['executions_that_will_not_travel']:,} executions rest on OUR curated map")
    print(f"    {curated_size:,} hand-curated overlay entries would need re-doing")
    print("\n  The low-confidence answers ARE the map of what breaks next — not a guess "
          "about fragility, the actual list.")


if __name__ == "__main__":
    main()
