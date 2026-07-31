"""build_profile_links.py — cross the PROFILE against the rest of the brain (s097).

The profile alone is a fact-sheet. Its value is the CROSSING: for every module the
tenant actually runs, do we have a capability row, claims, a domain doc, a companion?

The gap that crossing exposes is the one that matters:

    PRODUCTIVE module  x  no capability row  =  SYSTEM-LEVEL BLIND SPOT

That is a different animal from the object-level blind_spots (L12). L12 catches names
we mentioned without a graph node. This catches whole business modules the tenant runs
in production that our operating model has never looked at. s097 found six of them.

Every link is an explicit LOOKUP via profile_concept._module_to_domain — never a fuzzy
token match. ontology.json already had to correct that mistake once; we do not repeat it.

Emits: profile_links.json   Run standalone or inside rebuild_all.py.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
BRAIN = HERE.parent
PROFILE = HERE / "unesco_system_profile.json"
CONCEPT = HERE / "profile_concept.json"
CAPMODEL = BRAIN / "capability_model" / "capability_model.json"
ONTOLOGY = BRAIN / "capability_model" / "ontology.json"
CLAIMS = BRAIN / "claims" / "claims.json"
KNOWLEDGE = BRAIN.parent / "knowledge" / "domains"
COMPANIONS = BRAIN.parent / "companions"
OUT = HERE / "profile_links.json"

PRODUCTIVE = ("PRODUCTIVE",)


def _load(p):
    return json.load(open(p, encoding="utf-8"))


def check_invariants(profile, concept):
    """I1/I2 + the mapping completeness gate. Fail loud — a silent profile is worse
    than no profile, because it reads as 'we checked'."""
    errs = []
    mapping = concept["_module_to_domain"]
    tiers = set(concept["_evidence_tiers"]) - {"_rule"}
    for name, m in profile.get("modules", {}).items():
        if not isinstance(m, dict):
            continue
        st = m.get("status")
        if st not in tiers:
            errs.append(f"I1 {name}: status {st!r} is not one of {sorted(tiers)}")
        if not m.get("evidence"):
            errs.append(f"I1 {name}: no evidence string")
        if st == "NOT_USED" and "0 " not in (m.get("evidence") or ""):
            errs.append(f"I2 {name}: NOT_USED must cite the probe that returned zero")
        if name not in mapping:
            errs.append(f"MAP {name}: not in profile_concept._module_to_domain")
    return errs


def claims_for(claims, domain_key, module_name):
    """Claims that speak about this module.

    STRUCTURED FIELDS ONLY (domain + module axis), plus a word-boundary text match
    that is deliberately restricted to names of 4+ characters.

    The first version matched the module name as a plain substring of the claim text.
    For two-letter modules that is catastrophic: 'CO' matched 337 claims, 'PM' 47,
    'SD' 30 — noise presented as linkage, which is worse than an empty list because
    it reads as coverage. Same class of error ontology.json already had to correct.
    """
    hits = []
    long_enough = len(module_name) >= 4
    pat = re.compile(r"\b%s\b" % re.escape(module_name.replace("_", " ")), re.I) \
        if long_enough else None
    for c in claims:
        if not isinstance(c, dict):
            continue
        # domain_axes is a dict in the current schema but older claims carry a bare
        # list — tolerate both rather than dropping those claims silently.
        axes = c.get("domain_axes") or {}
        mods = [str(x).upper() for x in (axes.get("module") or [])] if isinstance(axes, dict) \
            else [str(x).upper() for x in axes]
        matched = (domain_key and c.get("domain") == domain_key) \
            or module_name.upper().replace("_", "-") in mods \
            or module_name.upper() in mods
        if not matched and pat and pat.search(str(c.get("claim", ""))):
            matched = True
        if matched:
            hits.append(c.get("id"))
    return hits


def run():
    profile = _load(PROFILE)
    concept = _load(CONCEPT)
    cap = _load(CAPMODEL).get("domains", {}) if CAPMODEL.exists() else {}
    onto = _load(ONTOLOGY) if ONTOLOGY.exists() else {}
    onto_keys = {d.get("canonical_key") for d in onto.get("domains", [])}
    raw = _load(CLAIMS) if CLAIMS.exists() else []
    claims = raw.get("claims", raw) if isinstance(raw, dict) else raw

    errs = check_invariants(profile, concept)
    if errs:
        print("INVARIANT BREACH — profile not linked:", file=sys.stderr)
        for e in errs:
            print("  -", e, file=sys.stderr)
        sys.exit(1)

    mapping = concept["_module_to_domain"]
    docs = {p.name.upper(): p.name for p in KNOWLEDGE.iterdir()} if KNOWLEDGE.exists() else {}
    comps = [p.name for p in COMPANIONS.glob("*.html")] if COMPANIONS.exists() else []

    # Doc folders are named by ALIAS, not by canonical key: PSM_FM lives in PSM/,
    # Payment_BCM in Payment/, Treasury_EBS in Treasury/, Procurement_P2P in
    # Procurement/. Alias resolution lives in brain_v2/canonical.py — one shared
    # implementation, because re-deriving it per consumer is what produced the same
    # defect three times in one session.
    sys.path.insert(0, str(BRAIN))
    from canonical import aliases_of

    def resolve_doc(module_name, dom_key):
        """Folder for this module, tried canonical -> declared aliases -> hyphen form."""
        cands = [module_name, module_name.replace("_", "-")]
        if dom_key:
            for a in aliases_of(dom_key):
                cands += [a, a.replace("_", "-"), a.replace("-", "_")]
        for c in cands:
            if c.upper() in docs:
                return docs[c.upper()]
        return None

    links, blind = {}, []
    for name, m in profile.get("modules", {}).items():
        if not isinstance(m, dict):
            continue
        dom = mapping.get(name)
        doc = resolve_doc(name, dom)
        comp = [c for c in comps if name.lower().split("_")[0] in c.lower()]
        row = {
            "status": m.get("status"),
            "capability_domain": dom,
            "in_ontology": bool(dom and dom in onto_keys),
            "capability_cells": cap.get(dom) and {k: v for k, v in cap[dom].items()
                                                  if not k.startswith("note")} or None,
            "claims": claims_for(claims, dom, name),
            "knowledge_doc": f"knowledge/domains/{doc}" if doc else None,
            "companions": comp[:3],
            "technical_component": next(
                (v for k, v in profile.get("technical_component_names", {}).items()
                 if k.lower().startswith(name.lower()[:6])), None),
        }
        links[name] = row
        if row["status"] in PRODUCTIVE and not dom:
            blind.append(name)

    unmodelled_docs = sorted(set(cap) - {v for v in mapping.values() if v})

    out = {
        "_generated_by": "brain_v2/system_profile/build_profile_links.py",
        "_what_this_is": ("The PROFILE crossed against capability_model / ontology / claims / "
                          "knowledge docs / companions. Read `system_level_blind_spots` first."),
        "system_level_blind_spots": {
            "_meaning": ("Modules the tenant runs IN PRODUCTION that have NO row in the capability "
                         "model — i.e. our operating model has never looked at them. Distinct from "
                         "L12 blind_spots (names without a graph node). These are the expensive ones."),
            "count": len(blind),
            "modules": blind,
        },
        "capability_domains_without_a_profile_module": {
            "_meaning": ("The mirror gap: domains we model but never tied to a real module — either "
                         "cross-cutting (Integration, Closing) or a modelling artefact to reconcile."),
            "domains": unmodelled_docs,
        },
        "coverage": {
            "modules_total": len(links),
            "productive": sum(1 for r in links.values() if r["status"] in PRODUCTIVE),
            "productive_with_capability_row": sum(
                1 for r in links.values() if r["status"] in PRODUCTIVE and r["capability_domain"]),
            "productive_with_knowledge_doc": sum(
                1 for r in links.values() if r["status"] in PRODUCTIVE and r["knowledge_doc"]),
            "modules_with_claims": sum(1 for r in links.values() if r["claims"]),
        },
        "modules": links,
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    cv = out["coverage"]
    print(f"wrote {OUT}")
    print(f"  modules {cv['modules_total']} · productive {cv['productive']} · "
          f"with capability row {cv['productive_with_capability_row']} · "
          f"with doc {cv['productive_with_knowledge_doc']}")
    print(f"  SYSTEM-LEVEL BLIND SPOTS ({len(blind)}): {', '.join(blind) or 'none'}")


if __name__ == "__main__":
    run()
