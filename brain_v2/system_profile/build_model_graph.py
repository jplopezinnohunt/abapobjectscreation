"""build_model_graph.py — the BIDIRECTIONAL model (s097).

The profile answers "what is this system?" top-down. That is half a model. The stated
objective is to understand the MACRO PROFILE THROUGH THE DETAILS, which requires the
other direction: from any object, climb to the macro.

    TOP-DOWN   installation -> module -> domain -> subdomain -> object
    BOTTOM-UP  object -> application component -> domain -> module -> tier -> installation

The bottom-up rung that makes this deterministic is SAP's OWN taxonomy:

    object --tadir_prog--> package --tdevc--> component id --df14l--> APPLICATION COMPONENT

2,687 components resolved from P01. This replaces guessing by package-name regex: the
system already knows that ANLA belongs to FI-AA-AA and RHRFPM_ENGINE_PNP to PA-PM-PB.

Three things this computes that nothing else does:

  1. ASCENT      — per object, the full chain up to the installation, with the rung
                   that resolved it recorded (never conflate curated with inferred).
  2. COHERENCE   — the macro tier asserted top-down vs the evidence found bottom-up.
                   A module marked PRODUCTIVE with no objects underneath is an
                   UNSUPPORTED ASSERTION, and the model should say so about itself.
  3. CROSS-CUTTING — domains that span modules (Integration, Closing, Output, Security…)
                   are not failures of the module axis; they are a different KIND of
                   domain and they enrich every module they touch.

Emits: model_graph.json     Runs inside rebuild_all.py (step 2d).
"""
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
BRAIN = HERE.parent
REPO = BRAIN.parent
sys.path.insert(0, str(REPO / "process_mining"))
sys.path.insert(0, str(BRAIN))

PROFILE = HERE / "unesco_system_profile.json"
CONCEPT = HERE / "profile_concept.json"
CAPMODEL = BRAIN / "capability_model" / "capability_model.json"
ONTOLOGY = BRAIN / "capability_model" / "ontology.json"
REGISTRY = BRAIN / "domains" / "domains.json"
INSTALL = BRAIN / "installation" / "installation.json"
STATE = BRAIN / "brain_state.json"
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT = HERE / "model_graph.json"

# ---------------------------------------------------------------------------
# APPLICATION COMPONENT -> canonical domain. Longest prefix wins.
#
# This is the system's own taxonomy, so it is far stronger than package-name regex:
# DF14L already states that ANLA sits in FI-AA-AA and RHRFPM_* in PA-PM-PB. Ordering
# matters only in that more specific prefixes must be able to win — enforced by
# sorting on length at match time, not by list order.
# ---------------------------------------------------------------------------
COMPONENT_TO_DOMAIN = {
    "PSM-FM": "PSM_FM", "PSM": "PSM_FM", "IS-PS-CA": "PSM_FM",
    "PA-PM-PB": "PBC",
    "FI-AA": "FI_AA",
    "RE-FX": "RE_FX", "RE": "RE_FX",
    "SD": "SD",
    "PM": "PM", "PM-EQM": "PM",
    "FIN-FSCM-TRM": "TRM", "TR-TM": "TRM",
    "FIN-FSCM-BNK": "Payment_BCM", "FI-BL-PT-AP": "Payment_BCM",
    "FI-AP-AP-PT": "Payment_BCM", "FI-BL-PT-PO": "Payment_BCM",
    "FI-BL-PT-BS": "Treasury_EBS", "FIN-FSCM-CLM": "Treasury_EBS", "FI-BL": "Treasury_EBS",
    "CO": "CO",
    "MM": "Procurement_P2P", "MM-PUR": "Procurement_P2P", "MM-IM": "Procurement_P2P",
    "FI-TV": "Travel",
    "PA": "HCM", "PY": "HCM", "PT": "HCM", "PE": "HCM", "PA-OS": "HCM",
    "PS": "PS",
    "FI": "FI", "FI-GL": "FI", "FI-AP": "FI", "FI-AR": "FI",
    "BC-SRV-BP": "BusinessPartner", "AP-MD-BF-SYN": "BusinessPartner",
    "LO-MD-BP": "BusinessPartner", "CA-GTF-CVI": "BusinessPartner",
    # cross-cutting / technical substrate — a legitimate tier, not a failure
    "BC": "_Basis", "BW": "_BI", "CA": "_CrossApp", "SV": "_Basis", "ST": "_Basis",
}

# Domains that span modules rather than owning one. Declaring this is what turns the
# "mirror gap" (domains with no module) from an anomaly into a modelled KIND.
CROSS_CUTTING = {
    "Integration":       ["ALL"],
    "Closing_Activities": ["FI", "CO", "PSM_FM", "FI_AA", "Treasury_EBS"],
    "Output":            ["PSM_FM", "HCM", "Payment_BCM"],
    "HR_Workflows":      ["HCM", "PBC", "Procurement_P2P"],
    "PY_Finance":        ["HCM", "FI", "PSM_FM", "PBC"],
    "Security":          ["ALL"],
    "Transport_Intelligence": ["ALL"],
    "Support":           ["ALL"],
    "Cost_Recovery_CRP": ["PSM_FM", "PS", "SD", "HCM"],
}


# An object type either CAN carry an application component or it cannot. Users, GL
# accounts, variants and synthesised concepts are not repository objects — no amount of
# TADIR extraction will ever resolve them, and counting them in the denominator measures
# the wrong thing. They get their own rung and their own denominator.
NON_REPOSITORY_TYPES = {
    "CONCEPT", "USER", "GL_ACCOUNT", "VARIANT_OR_SET", "COMPANY_CODE", "VENDOR",
    "CUSTOMER", "BANK", "FUND", "COST_CENTER", "WBS", "DOCUMENT", "INCIDENT",
    "SKILL", "COMPANION", "DOC", "PROCESS", "ROLE", "JOB_NAME", "FIELD",
}


def _load(p, default=None):
    if not p.exists():
        return default if default is not None else {}
    return json.load(open(p, encoding="utf-8"))


def component_to_domain(comp):
    """Longest matching component prefix wins."""
    if not comp:
        return None, None
    c = comp.upper()
    best = None
    for pref, dom in COMPONENT_TO_DOMAIN.items():
        if c == pref or c.startswith(pref + "-"):
            if best is None or len(pref) > len(best[0]):
                best = (pref, dom)
    return (best[1], best[0]) if best else (None, None)


def load_chain():
    """object -> application component, via the Gold DB (offline, deterministic)."""
    if not GOLD.exists():
        return {}, {}
    con = sqlite3.connect(str(GOLD))
    have = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if not {"tdevc", "df14l"} <= have:
        con.close()
        return {}, {}
    pkg_comp = dict(con.execute("SELECT DEVCLASS, COMPONENT FROM tdevc"))
    fid_pos = dict(con.execute("SELECT FCTR_ID, PS_POSID FROM df14l"))
    obj_comp = {}
    # tadir_obj covers TABL/FUGR/CLAS/TRAN/VIEW/DTEL/ENHO/SXCI; tadir_prog covers PROG.
    # Programs alone left 96% of graph objects (tables, function groups, classes,
    # transactions) with no component — the bottom-up chain has to span object TYPES.
    srcs = []
    if "tadir_obj" in have:
        srcs.append("SELECT OBJ_NAME, DEVCLASS FROM tadir_obj")
    if "tadir_prog" in have:
        srcs.append("SELECT OBJ_NAME, DEVCLASS FROM tadir_prog")
    for q in srcs:
        for obj, dc in con.execute(q):
            o = (obj or "").strip()
            if o in obj_comp:
                continue
            pos = fid_pos.get(pkg_comp.get(dc, ""), "")
            if pos:
                obj_comp[o] = (pos, dc)
    con.close()
    return obj_comp, fid_pos


def run():
    profile = _load(PROFILE)
    concept = _load(CONCEPT)
    cap = _load(CAPMODEL).get("domains", {})
    onto = _load(ONTOLOGY)
    reg_raw = _load(REGISTRY)
    reg = reg_raw.get("domains", reg_raw) if isinstance(reg_raw, dict) else {}
    install = _load(INSTALL)
    state = _load(STATE)
    objects = state.get("objects", {})
    mapping = concept.get("_module_to_domain", {})
    dom_to_module = {v: k for k, v in mapping.items() if v}

    obj_comp, _ = load_chain()

    # ALIAS NORMALISATION -> brain_v2/canonical.py, the single shared resolver.
    # This logic used to be re-implemented in every consumer; the same defect then
    # appeared three times in one session. Import the lookup, never re-derive it.
    from canonical import canonical as C

    # ---------------- BOTTOM-UP: ascent per object -------------------------
    # Evidence ladder, most authoritative first. `resolved_by` is recorded so a
    # curated assignment is never presented as an inference (CP-003).
    curated = {}
    for dname, d in reg.items():
        for o in (d.get("objects") or []):
            curated[o] = dname

    ascent, by_rung, dom_objects = {}, defaultdict(int), defaultdict(list)
    for name, o in objects.items():
        dom = rung = comp = None
        if name in curated:
            dom, rung = C(curated[name]), "1_registry_curated"
        if not dom and name in obj_comp:
            comp = obj_comp[name][0]
            d2, _pref = component_to_domain(comp)
            if d2:
                dom, rung = d2, "2_sap_application_component"
        if not dom:
            ax = (o.get("domain_axes") or {}).get("functional") or []
            if ax:
                dom, rung = C(ax[0]), "3_derived_domain_axis"
        if not dom:
            # separate "cannot be resolved this way" from "should be and is not"
            otype = str(o.get("type", "")).upper()
            rung = ("8_non_repository_entity"
                    if otype in NON_REPOSITORY_TYPES or "." in name
                    else "9_unresolved")
        by_rung[rung] += 1
        if dom:
            dom_objects[dom].append(name)
        module = dom_to_module.get(dom)
        ascent[name] = {
            "application_component": comp,
            "domain": dom,
            "module": module,
            "profile_status": (profile.get("modules", {}).get(module) or {}).get("status")
            if module else None,
            "resolved_by": rung,
        }

    # ---------------- COHERENCE: macro assertion vs detail evidence --------
    coherence, unsupported = {}, []
    for mod, m in profile.get("modules", {}).items():
        if not isinstance(m, dict):
            continue
        dom = mapping.get(mod)
        n_obj = len(dom_objects.get(dom, [])) if dom else 0
        n_cap = 0
        if dom and dom in cap:
            n_cap = sum(1 for k, v in cap[dom].items()
                        if not k.startswith("note") and v != "NONE")
        row = {
            "asserted_status": m.get("status"),
            "objects_underneath": n_obj,
            "capability_cells_filled": n_cap,
            "has_registry_entry": bool(dom and (dom in reg or any(C(k) == dom for k in reg))),
        }
        if m.get("status") == "PRODUCTIVE" and n_obj == 0:
            row["verdict"] = "UNSUPPORTED — asserted PRODUCTIVE with no object evidence beneath it"
            unsupported.append(mod)
        elif m.get("status") == "PRODUCTIVE" and n_obj < 3:
            row["verdict"] = "THIN — productive but almost nothing modelled underneath"
        else:
            row["verdict"] = "OK"
        coherence[mod] = row

    # ---------------- TOP-DOWN: the domain / subdomain tree ----------------
    tree, roots = {}, []
    for dname_raw, d in reg.items():
        dname = C(dname_raw)
        parent = C(d.get("parent_domain"))
        node = {
            "parent": parent,
            "children": [],
            "cross_cutting": dname in CROSS_CUTTING,
            "spans_modules": CROSS_CUTTING.get(dname),
            "registry_key": dname_raw,
            "module": dom_to_module.get(dname),
            "objects_resolved": len(dom_objects.get(dname, [])),
            "subtopics": d.get("subtopics") or [],
            "knowledge_docs": d.get("knowledge_docs") or [],
        }
        tree[dname] = node
    for dname, node in tree.items():
        p = node["parent"]
        if p and p in tree:
            tree[p]["children"].append(dname)
        elif not p:
            roots.append(dname)

    # cross-cutting domains ENRICH the modules they span — make the edge explicit
    enrich = defaultdict(list)
    all_mods = [k for k, v in profile.get("modules", {}).items()
                if isinstance(v, dict) and v.get("status") == "PRODUCTIVE"]
    for cc, spans in CROSS_CUTTING.items():
        targets = all_mods if spans == ["ALL"] else spans
        for t in targets:
            enrich[t].append(cc)

    out = {
        "_generated_by": "brain_v2/system_profile/build_model_graph.py",
        "_objective": ("Understand the MACRO profile THROUGH the details. Top-down alone is a "
                       "fact-sheet; bottom-up is what makes it verifiable."),
        "_chain": ("object -> tadir_prog(DEVCLASS) -> tdevc(COMPONENT) -> df14l(PS_POSID) "
                   "= SAP's own application component. Deterministic, no name guessing."),
        "installation": install.get("identity", {}).get("installation_id"),
        "resolution": {
            "_meaning": ("Which rung of the evidence ladder resolved each object. The "
                         "DENOMINATOR matters: users, GL accounts, variants and synthesised "
                         "concepts are not repository objects and can never carry an "
                         "application component. Counting them as 'unresolved' measures the "
                         "wrong thing — they are reported separately."),
            "by_rung": dict(sorted(by_rung.items())),
            "objects_total": len(objects),
            "non_repository": by_rung.get("8_non_repository_entity", 0),
            "resolvable_total": len(objects) - by_rung.get("8_non_repository_entity", 0),
            "objects_resolved": sum(v for k, v in by_rung.items()
                                    if k not in ("9_unresolved", "8_non_repository_entity")),
            "pct_resolved": round(100.0 * sum(
                v for k, v in by_rung.items()
                if k not in ("9_unresolved", "8_non_repository_entity"))
                / max(1, len(objects) - by_rung.get("8_non_repository_entity", 0)), 1),
            "_pct_meaning": "of RESOLVABLE (repository) objects, not of all nodes",
        },
        "coherence": {
            "_meaning": ("Does the macro assertion survive contact with the detail? A module "
                         "asserted PRODUCTIVE with nothing modelled underneath is the model "
                         "believing its own summary."),
            "unsupported_modules": unsupported,
            "per_module": coherence,
        },
        "cross_cutting": {
            "_meaning": ("Domains that span modules instead of owning one. They are not gaps in "
                         "the module axis — they are a different KIND of domain, and each one "
                         "enriches every module it touches."),
            "domains": CROSS_CUTTING,
            "enriches_module": {k: sorted(v) for k, v in sorted(enrich.items())},
        },
        "tree": {"roots": sorted(roots), "nodes": tree},
        "objects_per_domain": {k: len(v) for k, v in sorted(
            dom_objects.items(), key=lambda x: -len(x[1]))},
    }
    # The FULL ascent (one row per object) goes to its own file. brain_state attaches
    # model_graph.json wholesale and is already at ~80% of the context window, so only a
    # bounded sample travels with it — the rest stays queryable on disk (CP-002: preserve,
    # but do not force it into every session's context).
    json.dump({"_generated_by": OUT.name, "ascent": ascent},
              open(OUT.parent / "model_ascent.json", "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    out["ascent_sample"] = {k: v for k, v in list(
        sorted(ascent.items(), key=lambda x: (x[1]["resolved_by"], x[0])))[:120]}
    out["_full_ascent"] = "brain_v2/system_profile/model_ascent.json (one row per object)"

    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    r = out["resolution"]
    print(f"wrote {OUT}")
    print(f"  ASCENT: {r['objects_resolved']}/{r['objects_total']} objects resolve "
          f"upward ({r['pct_resolved']}%)")
    for k, v in r["by_rung"].items():
        print(f"    {k:32s} {v}")
    print(f"  COHERENCE: {len(unsupported)} unsupported module(s): "
          f"{', '.join(unsupported) or 'none'}")
    print(f"  CROSS-CUTTING: {len(CROSS_CUTTING)} domains spanning modules")
    print(f"  TREE: {len(tree)} nodes, {len(out['tree']['roots'])} roots")


if __name__ == "__main__":
    run()
