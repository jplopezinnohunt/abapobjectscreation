"""algorithm_status.py — is an algorithm REAL, or only declared? (s097)

The registry holds 24 algorithms. Some run in the rebuild and write artifacts; some run on
demand; some are proposals with no code at all. Reading the registry, you cannot tell them
apart — which is a real failure: a catalogue that mixes what exists with what is planned
makes the whole thing untrustworthy.

This derives the answer instead of asserting it, from three checks:

    BOUND      does every tool it claims actually exist on disk?
    PERSISTED  does it write an artifact that is on disk right now?
    GATED      does the golden-case harness cover it?

Status is then one of:
    RUNNING     bound + persisted        it produced the artifact you can open
    ON_DEMAND   bound, no artifact       real code, run when needed
    PROPOSED    not bound                an idea in the registry, no implementation

The distinction matters most for the ROADMAP. Of the three techniques proposed in s097,
concept drift is now BUILT (A7) and appears in the registry; DECLARE constraint mining and
LLM-assisted overlay derivation have zero code and are backlog tasks, not algorithms.
Saying otherwise would be the same confident-and-wrong the golden cases exist to prevent.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
BRAIN = HERE.parent
REPO = BRAIN.parent
ALGOS = HERE / "algorithms.json"
VALIDATOR = HERE / "validate_algorithms.py"
OUT = HERE / "algorithm_status.json"

# Artifact each algorithm writes, when it writes one. Declared here rather than guessed:
# an algorithm that runs inside another tool legitimately has none of its own.
ARTIFACT = {
    "A4": "brain_v2/executed_objects_domain_map.json",
    "A5": "process_mining/learned_rules.json",
    "A6": "brain_v2/executed_objects_domain_map.json",
    "C1": "brain_v2/methods/portability.json",
    "C2": "brain_v2/system_profile/model_ascent.json",
    "C3": "brain_v2/output/brain_v2_graph.json",
    "E1": "brain_v2/system_profile/profile_links.json",
    "E2": "brain_v2/system_profile/model_graph.json",
    "E3": "brain_v2/methods/trigger_state.json",
    "F1": "brain_v2/interface_boundary.json",
    "F2": "brain_v2/satellites.json",
    "B5": "Zagentexecution/sap_data_extraction/process_discovery/p2p.ocel2.sqlite",
}


def main():
    algos = json.load(open(ALGOS, encoding="utf-8")).get("algorithms", {})
    guard_text = VALIDATOR.read_text(encoding="utf-8", errors="replace") \
        if VALIDATOR.exists() else ""

    rows, counts = {}, {"RUNNING": 0, "ON_DEMAND": 0, "PROPOSED": 0}
    for aid, a in sorted(algos.items()):
        key = aid.split("_")[0]
        tools = a.get("bound_in") or []
        bound = bool(tools) and all((REPO / t.split(" (")[0]).exists() for t in tools)
        art = ARTIFACT.get(key)
        persisted = bool(art) and (REPO / art).exists()
        gated = f" {key} " in guard_text or f"# {key} " in guard_text

        status = "RUNNING" if (bound and persisted) else ("ON_DEMAND" if bound else "PROPOSED")
        counts[status] += 1
        rows[aid] = {"status": status, "state": a.get("state"),
                     "operates_on": a.get("operates_on"), "origin": a.get("origin"),
                     "bound_in": tools, "artifact": art if persisted else None,
                     "gated_by_golden_case": gated}

    proposed = [k for k, v in rows.items() if v["status"] == "PROPOSED"]
    ungated = [k for k, v in rows.items() if not v["gated_by_golden_case"]]

    out = {
        "_generated_by": "brain_v2/methods/algorithm_status.py",
        "_question": "which algorithms are REAL, and which are only declared?",
        "_why": ("a catalogue that mixes what exists with what is planned makes the whole "
                 "catalogue untrustworthy. Derived from disk, never asserted."),
        "_legend": {
            "RUNNING": "bound to real code AND its artifact is on disk right now",
            "ON_DEMAND": "real code, run when needed, writes no standing artifact",
            "PROPOSED": "an entry in the registry with no implementation — NOT part of the model",
        },
        "counts": counts,
        "proposed_not_yet_real": proposed,
        "not_covered_by_a_golden_case": ungated,
        "algorithms": rows,
        "_roadmap_note": ("Of the three roadmap techniques: CONCEPT DRIFT is BUILT (A7, "
                          "s097) and appears above. DECLARE constraint mining and "
                          "LLM-assisted overlay derivation have ZERO code — they are backlog "
                          "tasks, not algorithms. DECLARE is blocked on an event log that "
                          "does not exist; the overlay derivation is partially runnable "
                          "today and has a ready-made test set in the 334 curated entries."),
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"[algorithm status] {len(rows)} in the registry")
    for s in ("RUNNING", "ON_DEMAND", "PROPOSED"):
        print(f"    {s:11s} {counts[s]}")
    if proposed:
        print(f"  PROPOSED (declared, no code): {', '.join(proposed)}")
    print(f"  not gated by a golden case: {len(ungated)} of {len(rows)}")
    print("\n  Roadmap: drift is BUILT (A7). DECLARE and LLM-overlay have zero code.")


if __name__ == "__main__":
    main()
