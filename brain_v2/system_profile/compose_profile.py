"""compose_profile.py — ALGORITHM P1: the profile as COMPONENTS, each with its own derivation.

**The profile was hand-maintained, and that is the defect this closes.** `profile_concept.json`
said it plainly: *"who_updates: any session that measures something — EDIT
unesco_system_profile.json"*. A hand-edited profile cannot be reproduced on a second
installation, cannot go stale visibly, and cannot tell you what it is missing.

So the profile stops being a document and becomes a COMPOSITION: a declared list of components,
each bound to the algorithm that derives it, each carrying its own provenance.

    DERIVED    an algorithm produced it from tenant data — reproducible anywhere
    DECLARED   a human established it; correct, but it must be re-established per tenant
    MISSING    nothing produces it yet — the honest gap

**The number that matters is the DERIVED share**, because that is the part of "profile this
installation" that costs nothing on installation number two. Everything DECLARED is work that
has to be redone by hand, and calling it out is the only way it ever shrinks.

**Why one algorithm per component rather than one big prober.** The components answer genuinely
different questions and fail in different ways: the footprint needs a bounded read of component
tables, the operation needs a full log scan, the boundary needs configuration crossed against
traffic, the rules-in-code need production source. A single script would either do all of them
badly or refuse to run when any one input is missing. Composed, a missing input costs exactly
one component and says so.

**This composes; it does not extract.** Every component reads an artifact that already exists,
so P1 runs offline in seconds. When a component is MISSING the fix is to run its algorithm, and
the entry names which one.

Emits: brain_v2/system_profile/installation_profile.json
Run:   python brain_v2/system_profile/compose_profile.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
BRAIN = HERE.parent
REPO = BRAIN.parent
OUT = HERE / "installation_profile.json"

# component -> (question it answers, artifact that holds it, algorithm that derives it,
#               how to reach the value, whether a human had to establish it)
COMPONENTS = [
    ("identity", "which organisation and which system is this?",
     "brain_v2/installation/installation.json", None,
     ["identity"], True),
    ("landscape", "which systems exist and what may we do in each?",
     "brain_v2/system_profile/unesco_system_profile.json", None,
     ["landscape"], True),
    ("footprint", "which modules are installed, configured, PRODUCTIVE?",
     "brain_v2/system_profile/unesco_system_profile.json",
     "D5 bounded probe — probes/probe_footprint.py",
     ["modules"], True),
    ("org_structure", "how many company codes, plants, currencies?",
     "brain_v2/system_profile/unesco_system_profile.json",
     "D5 bounded probe — probes/probe_footprint.py",
     ["org_structure"], True),
    ("taxonomy", "which domains exist, and which process does each serve?",
     "brain_v2/brain_state.json",
     "C1 component resolution — component_map.py + extract_component_hierarchy.py",
     ["domains_layer", "domains"], False),
    ("operation", "HOW is it run — dialog, RFC, batch, file? who orchestrates?",
     "brain_v2/executed_objects_domain_map.json",
     "A3/A4/A6 — executed_objects_domain_map.py",
     ["by_domain"], False),
    ("write_channels", "what WRITES each object class, through which channel?",
     "brain_v2/change_attribution.json",
     "A8 — attribute_changes_to_programs.py",
     ["classes"], False),
    ("boundary", "which interfaces are configured, LIVE, dead, undeclared?",
     "brain_v2/interface_boundary.json",
     "F1 — interface_boundary.py",
     ["summary"], False),
    ("interfaces", "every inbound and outbound path, as records",
     "brain_v2/interface_inventory.json",
     "brain_v2/build_interface_inventory.py",
     ["interfaces"], False),
    ("satellites", "which external systems drive this one, and how much?",
     "brain_v2/satellites.json",
     "F2 — derive_satellites.py",
     ["satellites"], False),
    ("object_roles", "what is each object FOR — poster, report, interface?",
     "brain_v2/object_roles.json",
     "C4 — derive_object_roles.py",
     ["objects"], False),
    ("rules_in_code", "which decisions live in code rather than configuration?",
     "brain_v2/business_rules.json",
     "A9 — extract_business_rules.py",
     ["objects"], False),
    ("normative", "what does CORRECT mean, per flow?",
     "brain_v2/normative_models/normative_models.json", None,
     ["models"], True),
    ("drift", "is the operating model still the one we measured?",
     "brain_v2/drift_signals.json",
     "A7 — detect_drift.py",
     ["signals"], False),
    ("capability", "what do WE know about each domain, per dimension?",
     "brain_v2/capability_model/capability_model.json",
     "the model itself",
     ["domains"], False),
    ("maturity", "how good is our METHOD, measured from artifacts?",
     "brain_v2/meta_capability.json",
     "meta_capability.py",
     ["dimensions"], False),
    # The one component with NO artifact and NO algorithm, left visible on purpose. It is
    # not an oversight: nothing in this repository derives a security posture, and the
    # capability grid says the same thing from the other side (E_AUTH empty in 16 of 21).
    # Two instruments agreeing that the same thing is absent is worth more than a placeholder.
    ("security_posture", "where is the control surface, and does the role model hold it?",
     None, None, None, True),
    ("periphery", "add-ons, front-end, users and licences — every data EXIT",
     "brain_v2/system_profile/unesco_system_profile.json", None,
     ["third_party_addons"], True),
]


def _reach(blob, path):
    cur = blob
    for k in path or []:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def main():
    out, counts = [], {"DERIVED": 0, "DECLARED": 0, "MISSING": 0}
    for name, question, artifact, algo, path, human in COMPONENTS:
        entry = {"component": name, "question": question,
                 "artifact": artifact, "derived_by": algo}
        blob, size = None, None
        if artifact and (REPO / artifact).exists():
            try:
                blob = json.load(open(REPO / artifact, encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                blob = None
        if blob is not None:
            v = _reach(blob, path)
            if v is not None:
                size = len(v) if isinstance(v, (list, dict)) else 1

        if size:
            entry["present"] = True
            entry["size"] = size
            entry["state"] = "DECLARED" if human else "DERIVED"
        else:
            entry["present"] = False
            entry["state"] = "MISSING"
            entry["to_fix"] = (f"run {algo}" if algo else
                               "nothing produces this yet — it must be established by hand "
                               "or an algorithm has to be built for it")
        if human and size:
            entry["_cost_on_next_tenant"] = ("re-established BY HAND — this is the part of "
                                             "profiling that does not come free")
        counts[entry["state"]] += 1
        out.append(entry)

    derived = counts["DERIVED"]
    total = len(COMPONENTS)
    json.dump({
        "_generated_by": "brain_v2/system_profile/compose_profile.py",
        "_algorithm": "P1 — profile composition",
        "_what_this_is": ("the profile as COMPONENTS, each bound to the algorithm that derives "
                          "it. Replaces a hand-maintained document that could not be "
                          "reproduced, could not go stale visibly, and could not say what it "
                          "was missing."),
        "_the_number_that_matters": (
            f"{derived} of {total} components are DERIVED ({100 * derived // total}%). That is "
            f"the share of 'profile this installation' that costs nothing on the next tenant. "
            f"The {counts['DECLARED']} DECLARED ones are hand work that must be redone, and "
            f"naming them is the only way that number ever shrinks."),
        "_how_to_use": ("MISSING tells you which algorithm to run. DECLARED tells you what a "
                        "human still owes. DERIVED is free."),
        "counts": counts,
        "components": out,
    }, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"[profile P1] {total} components — "
          f"{counts['DERIVED']} derived · {counts['DECLARED']} declared · "
          f"{counts['MISSING']} missing")
    for e in out:
        mark = {"DERIVED": "  ", "DECLARED": "H ", "MISSING": "! "}[e["state"]]
        size = f"{e.get('size'):>6}" if e.get("size") else "     -"
        print(f"  {mark}{e['component']:18s} {size}  {e['state']:9s} {e['derived_by'] or ''}")
    print(f"\n  PORTABLE SHARE: {100 * derived // total}% of the profile derives itself.")
    print("  H = a human established it and must again on the next tenant.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
