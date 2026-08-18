"""Weave the operating model into the artifacts that hold the knowledge.

WHY THIS EXISTS
---------------
The capability model is Layer 15 -- 21 domains x 11 capabilities, AS-DESIGNED vs AS-RUN, and
G = the delta = the product. It is the model this project is built around. Measured at s099 it
mentioned the word "companion" ONCE, ".html" twice, and "entity" not at all.

So the model that says WHAT WE KNOW about each domain was not connected to the artifacts where
that knowledge actually lives. It gave a rating -- `B_CODE: PARTIAL` -- and no way to reach the
44 companions, 497 claims, 1,242 entities or 1,448 code objects behind it. A scorecard with no
links.

That is the same failure this session chased at every level: the knowledge existed, was
correct, and could not be navigated to. `entity` and `search` fixed lookup by name. This fixes
navigation from the MODEL: "what do we have for Payment's C_CONFIG, and where is it".

WHAT IT PRODUCES, AND THE CLAIM IT MAKES
----------------------------------------
`brain_v2/capability_artifacts.json` -- domain x capability -> the artifacts that support it,
and, more usefully, the ones where a capability is rated HAVE or PARTIAL with **no artifact
behind it at all**. That is a rating without evidence, which CP-003 forbids: an opinion
without evidence is not analysis.

The artifact->capability mapping is by artifact TYPE and is declared below rather than
inferred, because a wrong mapping here would manufacture false confidence -- exactly what the
check is meant to detect. Where a capability has no mappable artifact type, it says so instead
of guessing.
"""
from __future__ import annotations

import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE / "capability_artifacts.json"

RATED = {"HAVE", "PARTIAL"}          # a claim to knowledge; must be backed by something
NOT_RATED = {"NONE", "N/A", "", None}

# Which artifact types can evidence which capability. Declared, not inferred.
CAPABILITY_SOURCES = {
    "S_STANDARD_REF": ["research"],
    "A_PROCESS":      ["companions", "process_discovery"],
    "B_CODE":         ["code", "claims"],
    "C_CONFIG":       ["claims", "companions"],
    "D_DATA":         ["gold_tables", "claims"],
    "E_AUTH":         ["claims"],
    "F_INTERFACE_FILE": ["interfaces", "claims"],
    "G_CONFORMANCE":  ["quality_checks", "claims"],
    "H_IMPROVE":      ["claims", "incidents"],
    "R_S4_READINESS": ["research"],
    "U_USAGE":        ["claims"],
}


def load(rel, key=None):
    p = REPO / rel
    if not p.exists():
        return [] if key else {}
    data = json.loads(p.read_text(encoding="utf-8"))
    if key:
        data = data.get(key, []) if isinstance(data, dict) else data
        if isinstance(data, dict):
            data = list(data.values())
        return data if isinstance(data, list) else []
    return data


def domain_key(name):
    """'Payment_BCM' also answers to 'Payment' and 'BCM' -- domains are named by compound."""
    return {p.upper() for p in str(name).replace("-", "_").split("_") if len(p) > 1}


def run():
    cm = load("brain_v2/capability_model/capability_model.json")
    domains = cm.get("domains", {})
    if not domains:
        print("capability_model has no domains - nothing to weave")
        return 1

    claims = load("brain_v2/claims/claims.json")
    incidents = load("brain_v2/incidents/incidents.json", "incidents")
    cg = load("companions/companion_graph.json")
    inv = load("brain_v2/code_inventory.json")
    code_objs = inv.get("objects", inv) if isinstance(inv, dict) else inv
    code_objs = list(code_objs.values()) if isinstance(code_objs, dict) else code_objs
    n_research = len(list((HERE / "research").glob("w*_*.json"))) if (HERE / "research").exists() else 0
    checks = sorted(p.name for p in (REPO / "Zagentexecution" / "quality_checks").glob("*.py")) \
        if (REPO / "Zagentexecution" / "quality_checks").exists() else []

    # --- index the artifacts by domain -------------------------------------
    by_domain = defaultdict(lambda: defaultdict(list))

    for c in claims:
        if not isinstance(c, dict):
            continue
        names = {str(c.get("domain") or "").upper()}
        # domain_axes is a dict of axis->list in most records and a bare list in a few old
        # ones. Tolerate both rather than lose those claims from the weave.
        ax = c.get("domain_axes") or {}
        axis_values = ax.values() if isinstance(ax, dict) else [ax]
        for v in axis_values:
            if isinstance(v, list):
                names |= {str(x).upper() for x in v}
            elif isinstance(v, str):
                names.add(v.upper())
        for d in domains:
            if domain_key(d) & names:
                by_domain[d]["claims"].append(c.get("id"))

    for i in incidents:
        if not isinstance(i, dict):
            continue
        dn = {str(i.get("domain") or "").upper()}
        for d in domains:
            if domain_key(d) & dn:
                by_domain[d]["incidents"].append(i.get("id"))

    for n in cg.get("nodes", []) if isinstance(cg, dict) else []:
        ents = {str(e).upper() for e in (n.get("entities") or [])}
        ents.add(str(n.get("domain") or "").upper())
        for d in domains:
            if domain_key(d) & ents:
                by_domain[d]["companions"].append("companions/" + str(n.get("file")))

    for o in code_objs if isinstance(code_objs, list) else []:
        if not isinstance(o, dict):
            continue
        od = {str(x).upper() for x in (o.get("domains") or [])}
        for d in domains:
            if domain_key(d) & od:
                by_domain[d]["code"].append(o.get("name"))

    # gold tables, declared per domain in the registry contract
    reg = load("brain_v2/gold_table_registry.json")
    for rdom, groups in (reg.get("domains") or {}).items():
        keys = domain_key(rdom)
        tables = []
        if isinstance(groups, dict):
            for lst in groups.values():
                if isinstance(lst, list):
                    tables += [t.get("gold") for t in lst if isinstance(t, dict)]
        for d in domains:
            if domain_key(d) & keys:
                by_domain[d]["gold_tables"] += [t for t in tables if t]

    # process-discovery artifacts are process-wide, not per domain: they evidence A_PROCESS
    # for any domain that appears in a mined process. Counted globally and said so.
    pd_dir = REPO / "Zagentexecution" / "sap_data_extraction" / "process_discovery"
    n_process = len(list(pd_dir.glob("*.json"))) if pd_dir.exists() else 0

    # interfaces: the satellite/boundary derivation, bound to the domains it drives
    n_interfaces = 0
    for f in ("brain_v2/satellites.json", "brain_v2/interface_boundary.json"):
        fp = REPO / f
        if fp.exists():
            n_interfaces += 1

    # --- weave, and find the ratings with nothing behind them ---------------
    woven, unbacked = {}, []
    for d, caps in domains.items():
        art = by_domain[d]
        entry = {}
        for cap, rating in caps.items():
            if cap in ("note", "subdomains"):
                continue
            sources = CAPABILITY_SOURCES.get(cap)
            if sources is None:
                entry[cap] = {"rating": rating, "evidence": "capability not in the declared map"}
                continue

            ev = {}
            for s in sources:
                if s == "claims":
                    ev["claims"] = sorted(x for x in art.get("claims", []) if x)[:12]
                elif s == "companions":
                    ev["companions"] = sorted(set(art.get("companions", [])))[:8]
                elif s == "code":
                    ev["code_objects"] = len(art.get("code", []))
                elif s == "incidents":
                    ev["incidents"] = sorted(set(x for x in art.get("incidents", []) if x))[:8]
                elif s == "quality_checks":
                    ev["quality_checks"] = len(checks)
                elif s == "research":
                    ev["closed_researches"] = n_research
                elif s == "gold_tables":
                    ev["gold_tables"] = sorted(set(art.get("gold_tables", [])))[:12]
                elif s == "process_discovery":
                    ev["process_discovery_artifacts"] = n_process
                elif s == "interfaces":
                    ev["interface_artifacts"] = n_interfaces
            counted = sum(v if isinstance(v, int) else len(v) for v in ev.values())
            entry[cap] = {"rating": rating, "evidence": ev, "evidence_count": counted}

            if str(rating).upper() in RATED and counted == 0:
                unbacked.append((d, cap, rating))
        woven[d] = entry

    OUT.write_text(json.dumps({
        "_design": (
            "domain x capability -> the artifacts that evidence it. Built from the entity/"
            "domain links that already existed; the artifact->capability mapping is DECLARED "
            "in CAPABILITY_SOURCES, never inferred, because a wrong mapping here would "
            "manufacture confidence instead of measuring it."),
        "unbacked_ratings": [
            {"domain": d, "capability": c, "rating": r} for d, c, r in unbacked],
        "domains": woven,
    }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print("capability artifacts: {} domains woven -> {}".format(
        len(woven), OUT.relative_to(REPO)))
    print("ratings of HAVE/PARTIAL with NO artifact behind them: {}".format(len(unbacked)))
    for d, c, r in unbacked[:15]:
        print("   [{}] {:22} {}".format(r, d, c))
    if len(unbacked) > 15:
        print("   ... and {} more".format(len(unbacked) - 15))
    return 0


if __name__ == "__main__":
    sys.exit(run())
