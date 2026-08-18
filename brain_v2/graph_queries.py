"""
Agent-reasoning functions for brain_state.json.
These work WITH the brain state already loaded in context — no file I/O.
For heavy algorithms (BFS, impact), use: python -m brain_v2 impact/depends.

Usage (from agent mid-session):
  python brain_v2/graph_queries.py what_reads LFA1
  python brain_v2/graph_queries.py what_depends_on LHRTSF01
  python brain_v2/graph_queries.py incident INC-000006073
  python brain_v2/graph_queries.py uncertain_claims
  python brain_v2/graph_queries.py domain_summary Travel
  python brain_v2/graph_queries.py object_detail LHRTSF01
"""
import io, json, re, sys, time
from pathlib import Path

# Windows consoles default to cp1252: any brain text containing an arrow, an em-dash or an
# accent crashes the drill command with UnicodeEncodeError instead of answering. Since s099
# the incident trace surfaces root_cause_summary verbatim, so this is on the main path.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BRAIN_STATE = Path(__file__).parent / "brain_state.json"
PROJECT_ROOT = Path(__file__).parent.parent

# Source files that should trigger a rebuild if newer than brain_state
SOURCE_FILES = [
    PROJECT_ROOT / "brain_v2" / "annotations" / "annotations.json",
    PROJECT_ROOT / "brain_v2" / "claims" / "claims.json",
    PROJECT_ROOT / "brain_v2" / "agent_rules" / "feedback_rules.json",
    PROJECT_ROOT / "brain_v2" / "agi" / "known_unknowns.json",
    PROJECT_ROOT / "brain_v2" / "agi" / "falsification_log.json",
    PROJECT_ROOT / "brain_v2" / "agi" / "user_questions.json",
    PROJECT_ROOT / "brain_v2" / "agi" / "data_quality_issues.json",
]


def freshness_check():
    """Check if brain_state.json is fresh relative to source files."""
    if not BRAIN_STATE.exists():
        return {"status": "MISSING", "warning": "brain_state.json does not exist. Run: python brain_v2/rebuild_all.py"}

    bs_mtime = BRAIN_STATE.stat().st_mtime
    bs_age_hours = (time.time() - bs_mtime) / 3600

    stale_sources = []
    for src in SOURCE_FILES:
        if src.exists() and src.stat().st_mtime > bs_mtime:
            stale_sources.append(src.name)

    result = {
        "brain_state_age_hours": round(bs_age_hours, 1),
        "stale_sources": stale_sources,
    }
    if stale_sources:
        result["status"] = "STALE"
        result["warning"] = f"brain_state.json is older than {len(stale_sources)} source files. Run: python brain_v2/rebuild_all.py"
    elif bs_age_hours > 72:
        result["status"] = "OLD"
        result["warning"] = f"brain_state.json is {bs_age_hours:.0f} hours old. Consider rebuilding if source data changed."
    else:
        result["status"] = "FRESH"
    return result


def load():
    return json.load(open(BRAIN_STATE, encoding="utf-8"))


def what_reads(brain, table_name):
    """What programs/classes read this table? Reverse lookup."""
    readers = []
    for name, obj in brain["objects"].items():
        if table_name in obj.get("reads_tables", []):
            readers.append({"name": name, "type": obj["type"], "domain": obj.get("domain", "")})
    return {"table": table_name, "read_by": readers, "count": len(readers)}


def what_depends_on(brain, object_name):
    """What does this object depend on? Forward lookup."""
    obj = brain["objects"].get(object_name, {})
    if not obj:
        return {"error": f"{object_name} not in brain_state (try full graph: python -m brain_v2 depends)"}
    return {
        "object": object_name,
        "type": obj.get("type"),
        "reads_tables": obj.get("reads_tables", []),
        "calls_fms": obj.get("calls_fms", []),
        "writes_tables": obj.get("writes_tables", []),
        "read_by": obj.get("read_by", []),
        "called_by": obj.get("called_by", []),
        "annotations": len(obj.get("annotations", [])),
        "claims": len(obj.get("claims", [])),
        "incidents": obj.get("incidents", []),
    }


def incident_trace(brain, incident_id):
    """Trace an incident: header, root cause objects, annotations, claims, affected tables.

    `indexes.by_incident[id]` is a DICT (status/title/domain/analysis_doc/root_cause_summary/
    fix_immediate/related_objects), not a list of object names. Iterating it directly yields
    the FIELD NAMES — which is what this function did until s099, so the one drill command the
    incident protocol tells you to run in step 2 returned {'name': 'status'}, {'name': 'title'}…
    A list form is still accepted for older brain states.
    """
    entry = brain["indexes"]["by_incident"].get(incident_id)
    if entry is None:
        known = sorted(brain["indexes"]["by_incident"].keys())
        return {"incident": incident_id, "error": "not found in indexes.by_incident", "known": known}

    if isinstance(entry, dict):
        objects_in_incident = entry.get("related_objects", [])
        trace = {
            "incident": incident_id,
            "status": entry.get("status"),
            "title": entry.get("title"),
            "domain": entry.get("domain"),
            "analysis_doc": entry.get("analysis_doc"),
            "root_cause_summary": entry.get("root_cause_summary"),
            "fix_immediate": entry.get("fix_immediate"),
            "objects": [],
        }
    else:  # legacy: plain list of object names
        objects_in_incident = entry
        trace = {"incident": incident_id, "objects": []}

    for name in objects_in_incident:
        obj = brain["objects"].get(name, {})
        entry = {"name": name, "type": obj.get("type", "")}
        anns = [a for a in obj.get("annotations", []) if a.get("incident") == incident_id]
        if anns:
            entry["findings"] = [{"tag": a["tag"], "line": a.get("line"), "finding": a["finding"][:100]} for a in anns]
        entry["reads_tables"] = obj.get("reads_tables", [])
        trace["objects"].append(entry)
    # Add related claims
    trace["claims"] = [c for c in brain["claims"] if any(o in c.get("related_objects", []) for o in objects_in_incident)]
    return trace


def uncertain_claims(brain):
    """Claims with TIER_3+ confidence — what the agent is uncertain about."""
    return brain["indexes"].get("uncertain_claims", [])


def superseded_claims(brain):
    """Claims that were proven wrong — lessons learned."""
    return brain["indexes"].get("superseded_claims", [])


def domain_summary(brain, domain):
    """All objects in a domain with their key relationships."""
    objects_in_domain = brain["indexes"]["by_domain"].get(domain, [])
    summary = {"domain": domain, "object_count": len(objects_in_domain), "objects": []}
    for name in objects_in_domain:
        obj = brain["objects"].get(name, {})
        summary["objects"].append({
            "name": name, "type": obj.get("type", ""),
            "tables": len(obj.get("reads_tables", [])),
            "annotations": len(obj.get("annotations", [])),
            "incidents": obj.get("incidents", []),
        })
    return summary


def object_detail(brain, name):
    """Full detail about one object — everything the agent knows."""
    obj = brain["objects"].get(name)
    if not obj:
        return {"error": f"{name} not found. Available: {sorted(brain['objects'].keys())[:20]}"}
    result = {"name": name, **obj}
    # Add applicable rules (rules that mention this object or its tables)
    tables = set(obj.get("reads_tables", []) + obj.get("writes_tables", []))
    applicable = []
    for r in brain["rules"]:
        rule_text = (r["rule"] + " " + r.get("why", "") + " " + r.get("how_to_apply", "")).upper()
        if name.upper() in rule_text or any(t in rule_text for t in tables):
            applicable.append({"id": r["id"], "rule": r["rule"]})
    if applicable:
        result["applicable_rules"] = applicable
    return result


def domain(brain, dom_name):
    """Layer 14 domain registry lookup. Returns ALL reverse-indexed entities
    for a functional domain: objects, claims, rules, KUs, incidents, skills,
    companions, subtopics. Feeds session_activation_hints."""
    registry = brain.get("domains_layer", {}).get("domains", {})
    d = registry.get(dom_name)
    if not d:
        return {
            "error": f"Domain '{dom_name}' not in registry.",
            "available": sorted(registry.keys()),
        }
    # Also pull in objects by domain (Layer 2 index)
    objects_in_domain = brain["indexes"]["by_domain"].get(dom_name, [])
    result = {
        "domain": dom_name,
        "axis": d.get("axis"),
        "description": d.get("description", ""),
        "knowledge_doc_path": d.get("knowledge_doc_path"),
        "knowledge_docs": d.get("knowledge_docs", []),
        "companions": d.get("companions", []),
        "skills": d.get("skills", []),
        "subtopics": list(d.get("subtopics", {}).keys()),
        "objects_rich": d.get("objects", []),
        "objects_layer2_index": objects_in_domain,
        "claims_ids": d.get("claims_ids", []),
        "rules_ids": d.get("rules_ids", []),
        "incidents": d.get("incidents", []),
        "known_unknowns": d.get("known_unknowns", []),
        "falsification_pending": d.get("falsification_pending", []),
        "data_quality_open": d.get("data_quality_open", []),
        "coverage_pct": d.get("coverage_pct"),
        "last_session_touched": d.get("last_session_touched"),
        "owner_role": d.get("owner_role"),
        "parent_domain": d.get("parent_domain"),
        "child_domains": d.get("child_domains", []),
        "primary_modules": d.get("primary_modules", []),
        "primary_processes": d.get("primary_processes", []),
    }
    # Pass through anything the registry carries that this projection does not name.
    # The whitelist above was silently DROPPING every field a later session added
    # (s099: Support's `tracks`, `recurring_checks`, `procedures` vanished between
    # domains.json and the drill output). A projection that discards what it does not
    # recognise is the same failure mode as a doc with no first-class record: the
    # knowledge exists and cannot be reached.
    for k, v in d.items():
        if k not in result and k not in ("objects", "subtopics"):
            result[k] = v
    return result


def domain_gap(brain):
    """Find domains with missing coverage. Returns list ordered by severity."""
    registry = brain.get("domains_layer", {}).get("domains", {})
    gaps = []
    for name, d in registry.items():
        issues = []
        if not d.get("knowledge_docs") and not d.get("knowledge_doc_path"):
            issues.append("no_knowledge_doc")
        if not d.get("skills"):
            issues.append("no_skill")
        if not d.get("companions"):
            issues.append("no_companion")
        cov = d.get("coverage_pct")
        if cov is not None and cov < 50:
            issues.append(f"coverage_{cov}pct")
        if d.get("last_session_touched") is None:
            issues.append("never_touched")
        if issues:
            gaps.append({
                "domain": name,
                "issues": issues,
                "coverage_pct": cov,
                "last_session_touched": d.get("last_session_touched"),
            })
    gaps.sort(key=lambda g: (-len(g["issues"]), g["coverage_pct"] or 0))
    return {"gaps_found": len(gaps), "gaps": gaps}


def process_view(brain, process_code):
    """Show all domains in a UNESCO process chain (B2R/H2R/P2P/T2R/P2D)."""
    registry = brain.get("domains_layer", {})
    process_map = registry.get("process_map", {})
    pm = process_map.get(process_code)
    if not pm:
        return {
            "error": f"Process '{process_code}' not found.",
            "available": [k for k in process_map.keys() if not k.startswith("_")],
        }
    doms = {}
    for d in pm.get("domains", []):
        entry = registry.get("domains", {}).get(d, {})
        doms[d] = {
            "description": entry.get("description", "")[:120],
            "skills": entry.get("skills", []),
            "objects_count": len(entry.get("objects", [])),
            "incidents": entry.get("incidents", []),
            "open_kus": len(entry.get("known_unknowns", [])),
        }
    return {
        "process": process_code,
        "name": pm.get("name"),
        "domains": doms,
    }


def activate(brain, prompt_text):
    """Domain activation: scan a prompt for session_activation_hints keywords,
    return ordered list of activated domains + auto-load manifest."""
    import re
    registry = brain.get("domains_layer", {})
    hints = registry.get("session_activation_hints", {})
    activated = []
    for pattern, domains in hints.items():
        if pattern.startswith("_"):
            continue
        if re.search(pattern, prompt_text, flags=re.IGNORECASE):
            for d in domains:
                if d not in activated:
                    activated.append(d)
    if not activated:
        return {
            "activated_domains": [],
            "warning": "No domain match — session scope UNCLASSIFIED. Consider adding to session_activation_hints or flag as blind_spot.",
        }
    manifest = {}
    domains_reg = registry.get("domains", {})
    for d in activated:
        entry = domains_reg.get(d, {})
        manifest[d] = {
            "knowledge_doc_path": entry.get("knowledge_doc_path"),
            "skills_to_load": entry.get("skills", []),
            "companions": entry.get("companions", []),
            "open_known_unknowns": entry.get("known_unknowns", []),
            "open_data_quality": entry.get("data_quality_open", []),
            "subtopics_available": list(entry.get("subtopics", {}).keys()),
        }
    return {
        "activated_domains": activated,
        "activation_manifest": manifest,
    }


def stats(brain):
    """Quick brain statistics with freshness check."""
    return {
        "freshness": freshness_check(),
        "objects": len(brain["objects"]),
        "rules": len(brain["rules"]),
        "claims": len(brain["claims"]),
        "incidents": len(brain["indexes"]["by_incident"]),
        "domains": {d: len(objs) for d, objs in brain["indexes"]["by_domain"].items()},
        "agi_layers": {
            "known_unknowns": len(brain.get("known_unknowns", [])),
            "falsification_pending": len([f for f in brain.get("falsification", []) if f.get("status") == "PENDING"]),
            "user_questions_open": len([q for q in brain.get("user_questions", []) if q.get("status") != "ANSWERED"]),
            "data_quality_open": len([d for d in brain.get("data_quality", []) if d.get("status") == "OPEN"]),
            "superseded": len(brain.get("superseded", [])),
        },
    }


def capability(brain, dom_name=None):
    """Layer 15 — capability coverage for a domain, or the whole matrix.
    A domain is AS-DESIGNED (standard SAP) + AS-RUN (ours); G = the delta."""
    cm = brain.get("capability_model", {})
    if not cm:
        return {"error": "capability_model layer absent — run rebuild_all.py"}
    doms = cm.get("domains", {})
    if dom_name:
        toks = set(dom_name.lower().replace("/", "_").replace("-", "_").split("_")) - {""}
        hit = {k: v for k, v in doms.items()
               if set(k.lower().replace("/", "_").replace("-", "_").split("_")) & toks}
        return {"dimensions": cm.get("dimensions", {}), "strata": cm.get("_strata", {}),
                "match": hit or f"no domain matching '{dom_name}'"}
    return {"dimensions": list(cm.get("dimensions", {}).keys()),
            "matrix": doms, "rollup": cm.get("_rollup", {})}


def capability_gaps(brain):
    """Layer 15 — every NONE cell ranked; surfaces systemic empty COLUMNS
    (S_STANDARD_REF / E_AUTH / G_CONFORMANCE) that are model gaps, not per-domain."""
    cm = brain.get("capability_model", {})
    if not cm:
        return {"error": "capability_model layer absent — run rebuild_all.py"}
    doms = cm.get("domains", {})
    dims = [d for d in cm.get("dimensions", {}).keys()]
    col_none = {dim: [dn for dn, cov in doms.items() if cov.get(dim) == "NONE"] for dim in dims}
    systemic = {dim: doms_list for dim, doms_list in col_none.items()
                if len(doms_list) == len(doms) and doms}
    return {
        "systemic_empty_columns": list(systemic.keys()),
        "systemic_detail": cm.get("systemic_gaps", []),
        "expansion_order": cm.get("expansion_order", []),
        "none_count_by_dimension": {k: len(v) for k, v in col_none.items()},
    }


def profile(brain, module=None):
    """LAYER 16 — the tenant PROFILE. No arg = the fact-sheet + the gap report;
    with a module name = that module crossed against capability model, claims and docs.

    This is the answer to 'what is this system?' — ask it BEFORE re-deriving the
    footprint from cvers or the audit log (rule feedback_profile_first...)."""
    p = brain.get("system_profile", {})
    if not p:
        return {"error": "no system_profile layer — run brain_v2/rebuild_all.py"}
    links = p.get("_links", {})
    if module:
        row = links.get("modules", {}).get(module)
        if not row:
            return {"error": f"unknown module {module!r}",
                    "known": sorted(links.get("modules", {}))}
        return {"module": module, "profile": p.get("modules", {}).get(module), "links": row}
    return {
        "platform": p.get("landscape", {}).get("product"),
        "org_structure": p.get("org_structure"),
        "operating_model_headline": p.get("operating_model", {}).get("headline"),
        "modules_by_status": {
            s: sorted(k for k, v in p.get("modules", {}).items()
                      if isinstance(v, dict) and v.get("status") == s)
            for s in ("PRODUCTIVE", "CONFIGURED", "INSTALLED", "NOT_USED", "NOT_EVIDENCED")
        },
        "third_party_addons_active": sorted(
            k for k, v in p.get("third_party_addons", {}).items()
            if isinstance(v, dict) and v.get("status") == "ACTIVE"),
        "coverage": links.get("coverage"),
        "system_level_blind_spots": links.get("system_level_blind_spots"),
    }


def ascend(brain, obj):
    """BOTTOM-UP: from one object, climb to the macro profile.

    The counterpart of `profile`. `profile` answers "what is this system?"; `ascend`
    answers "what does THIS detail belong to, and how do I know?" — the resolution
    rung is always returned so a curated assignment is never mistaken for a guess."""
    g = (brain.get("system_profile", {}) or {}).get("_model_graph", {})
    if not g:
        return {"error": "no model graph — run brain_v2/system_profile/build_model_graph.py"}
    return {"object": obj, "ascent": g.get("ascent_sample", {}).get(obj)
            or "not in sample; see brain_v2/system_profile/model_graph.json",
            "chain": g.get("_chain")}


def coherence(brain, _=None):
    """Does the macro assertion survive contact with the detail?"""
    g = (brain.get("system_profile", {}) or {}).get("_model_graph", {})
    if not g:
        return {"error": "no model graph"}
    return {"resolution": g.get("resolution"), "coherence": g.get("coherence"),
            "objects_per_domain": g.get("objects_per_domain")}


def tree(brain, _=None):
    """TOP-DOWN: the domain / subdomain tree with the cross-cutting overlay."""
    g = (brain.get("system_profile", {}) or {}).get("_model_graph", {})
    if not g:
        return {"error": "no model graph"}
    return {"tree": g.get("tree"), "cross_cutting": g.get("cross_cutting")}


def methods(brain, _=None):
    """The repeatable activities that mature the model — what to RUN, not what was found."""
    m = (brain.get("system_profile", {}) or {}).get("_maturity_methods", {})
    if not m:
        return {"error": "no methods registry"}
    return {"lifecycle": m.get("_lifecycle"),
            "methods": {k: {"activity": v.get("activity"), "stage": v.get("stage"),
                            "tool": v.get("tool") or v.get("tools")}
                        for k, v in m.get("methods", {}).items()},
            "anti_methods": m.get("_anti_methods"),
            "next_promotions": m.get("_next_promotions")}


def _load_code_inventory():
    p = PROJECT_ROOT / "brain_v2" / "code_inventory.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def code(brain, name):
    """Where does this object's SOURCE actually live, is it complete, whose is it?

    Answers the question that burned s099: the canonical path held a 29-line stub while
    the 1,593-line body sat outside the corpus in UTF-16. Matches on name AND token, so
    asking for YRGGBS00 finds YRGGBS00_SOURCE.txt and YFI_YRGGBS00_EXIT.abap together.
    """
    inv = _load_code_inventory()
    if inv is None:
        return {"error": "code_inventory.json missing — run python brain_v2/build_code_inventory.py"}
    objs = inv["objects"]
    key = (name or "").upper()
    if key in objs:
        hits = [key]
    else:
        hits = sorted(k for k in objs if key in k)
        if not hits:
            hits = sorted({o for t, names in inv.get("token_index", {}).items()
                           if key in t for o in names})
    if not hits:
        return {"error": f"{name} not found in code inventory",
                "hint": "try a shorter fragment; matching is substring + token"}

    secs = _load_code_sections()
    out = []
    for h in hits[:8]:
        o = dict(objs[h])
        s = (secs or {}).get("objects", {}).get(h)
        if s:
            # The routine is the unit of behaviour — an object is a container of rules.
            o["sections"] = {
                "count": s["section_count"],
                "roles": s["roles"],
                "can_block_posting": s["blocking_sections"],
                "routines": [{"routine": x["routine"], "lines": f'{x["start_line"]}-{x["end_line"]}',
                              "role": x["role"], "intent": x["header_comment"][:90],
                              "reads": x["reads_tables"][:6], "blocks": x["can_block_posting"]}
                             for x in s["sections"]],
            }
        out.append(o)
    return {"query": name, "matches": len(hits), "objects": out}


def _load_code_sections():
    p = PROJECT_ROOT / "brain_v2" / "code_sections.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def section(brain, name):
    """One routine: where it lives, what it does, when it declines to act, what it can block.

    s099: mapping objects is not enough. YRGGBS00 is one object holding ~29 parsed routines
    and 8 that can stop a posting — UXR2, U915, U916, U917 among them. The rule you care
    about is a line range, not a file.
    """
    secs = _load_code_sections()
    if secs is None:
        return {"error": "code_sections.json missing — run python brain_v2/build_code_sections.py"}
    key = (name or "").upper()
    found = []
    for obj, o in secs["objects"].items():
        for s in o["sections"]:
            if key == s["routine"] or key in s["routine"]:
                found.append(s)
    if not found:
        return {"error": f"routine {name} not found",
                "hint": "try `search` — routine names are also indexed there"}
    return {"query": name, "matches": len(found), "sections": found[:10]}


def blocking_code(brain, domain=None):
    """Every routine that can STOP a posting — the real control surface, by domain."""
    secs = _load_code_sections()
    if secs is None:
        return {"error": "code_sections.json missing — run build_code_sections.py"}
    rows = []
    for obj, o in secs["objects"].items():
        if domain and domain not in (o.get("domains") or []):
            continue
        for s in o["sections"]:
            if s["can_block_posting"]:
                rows.append({"object": obj, "routine": s["routine"],
                             "lines": f'{s["start_line"]}-{s["end_line"]}',
                             "intent": s["header_comment"][:110],
                             "reads": s["reads_tables"][:6],
                             "messages": s["messages"],
                             "domains": (o.get("domains") or [])[:5],
                             "source": o["source"]})
    return {"domain": domain, "count": len(rows),
            "controls": sorted(rows, key=lambda r: (r["object"], r["routine"]))}


def entity(brain, name):
    """What do we know about THIS THING? The drill that did not exist until s099.

    The brain had four indexes and none by entity, so "what do we know about DMEE" could only
    be answered by scanning text -- and text scans fail on wording. This reads the reverse
    index built from the typed link fields that already existed.
    """
    f = Path(__file__).parent / "entity_index.json"
    if not f.exists():
        return {"error": "entity_index.json missing - run python brain_v2/build_entity_index.py"}
    idx = json.loads(f.read_text(encoding="utf-8")).get("entities", {})
    key = (name or "").strip().upper()
    if not key:
        return {"error": "give an entity name"}
    if key in idx:
        return {"entity": key, **idx[key]}

    near = sorted(k for k in idx if key in k or k in key)[:15]
    return {"entity": key, "found": False,
            "did_you_mean": near,
            "hint": "not in the index. Typed links only (claims.related_objects, "
                    "incidents.related_*, companion entities, code inventory). For prose use "
                    "`search`."}


def search(brain, text):
    """Full-text across every knowledge store AND the code inventory.

    The drill that did not exist until s099. 19 commands and none searched text, so
    'purpose of payment' returned nothing while 91 Payment claims sat in the brain.
    Case-insensitive; the code inventory is already encoding-normalised at build time.
    """
    q = (text or "").strip().lower()
    if len(q) < 3:
        return {"error": "give at least 3 characters"}

    # Phrase match is brittle on wording: 'purpose of payment' misses 91 claims that all
    # say 'Payment Purpose Code'. So a phrase hit wins, but ALL-WORDS-PRESENT also counts.
    _STOP = {"of", "the", "a", "an", "in", "on", "for", "to", "and", "is", "at", "by"}
    words = [w for w in re.split(r"[^a-z0-9_]+", q) if w and w not in _STOP]

    def hit(blob):
        low = blob.lower()
        if q in low:
            return True
        return bool(words) and all(w in low for w in words)

    out = {"query": text, "matched_words": words, "claims": [], "rules": [],
           "incidents": [], "annotations": [], "code": [], "domains": [],
           "companions": []}

    # Companions carry the deepest analysis we produce, and they were UNSEARCHABLE: the DMEE
    # work lives in a companion titled "BCM Structured Address Change" tagged "finance" --
    # 965 mentions of DMEE, and nothing in its name or registry entry says so. The signal
    # already existed (build_companion_graph.py extracts SAP vocabulary into node.entities,
    # 15 companions carry 'dmee'); it was computed and never queried.
    try:
        cg = json.loads((PROJECT_ROOT / "companions" / "companion_graph.json")
                        .read_text(encoding="utf-8"))
        for n in cg.get("nodes", []):
            blob = " ".join([str(n.get("title") or ""), str(n.get("file") or ""),
                             " ".join(str(e) for e in n.get("entities") or []),
                             " ".join(str(i) for i in n.get("incidents") or [])])
            if hit(blob):
                out["companions"].append({
                    "file": "companions/" + str(n.get("file")),
                    "title": n.get("title"), "domain": n.get("domain"),
                    "incidents": n.get("incidents") or [],
                    "matched_entities": [e for e in (n.get("entities") or [])
                                         if any(w in str(e).lower() for w in words)][:8],
                })
    except (OSError, ValueError):
        out["companions"] = [{"error": "companion_graph.json unreadable - run "
                                       "scripts/build_companion_graph.py"}]

    for c in brain.get("claims", []):
        if hit(json.dumps(c, ensure_ascii=False)):
            out["claims"].append({"id": c.get("id"), "domain": c.get("domain"),
                                  "confidence": c.get("confidence"),
                                  "status": c.get("status"),
                                  "claim": (c.get("claim") or "")[:220]})
    for r in brain.get("rules", []):
        if hit(json.dumps(r, ensure_ascii=False)):
            out["rules"].append({"id": r.get("id"), "severity": r.get("severity"),
                                 "rule": (r.get("rule") or "")[:200]})
    incs = brain.get("incidents", [])
    incs = incs.values() if isinstance(incs, dict) else incs
    for i in incs:
        if isinstance(i, dict) and hit(json.dumps(i, ensure_ascii=False)):
            out["incidents"].append({"id": i.get("id"), "status": i.get("status"),
                                     "title": i.get("title"),
                                     "analysis_doc": i.get("analysis_doc")})
    for name, o in (brain.get("objects") or {}).items():
        for a in (o.get("annotations") or []):
            if hit(json.dumps(a, ensure_ascii=False)):
                out["annotations"].append({"object": name, "tag": a.get("tag"),
                                           "finding": (a.get("finding") or "")[:200]})
                break
    for dname, d in ((brain.get("domains_layer") or {}).get("domains") or {}).items():
        if hit(json.dumps(d, ensure_ascii=False)):
            out["domains"].append(dname)

    inv = _load_code_inventory()
    if inv:
        for name, o in inv["objects"].items():
            if hit(name) or hit(json.dumps(o.get("domains", []), ensure_ascii=False)):
                out["code"].append({"object": name, "source": o["primary_source"],
                                    "lines": o["lines"],
                                    "integrity": o["integrity"]["status"],
                                    "domains": [d["domain"] for d in o["domains"]]})

    out["_counts"] = {k: len(v) for k, v in out.items() if isinstance(v, list)}
    for k in ("claims", "rules", "incidents", "annotations", "code"):
        out[k] = out[k][:12]
    return out


def code_gaps(brain, _=None):
    """Every object whose source is split, stubbed, or has no domain link."""
    inv = _load_code_inventory()
    if inv is None:
        return {"error": "code_inventory.json missing — run build_code_inventory.py"}
    broken = [{"object": n, "status": o["integrity"]["status"],
               "note": o["integrity"]["note"], "source": o["primary_source"]}
              for n, o in inv["objects"].items()
              if o["integrity"]["status"] != "OK"]
    return {"integrity": inv["_integrity"],
            "broken": sorted(broken, key=lambda x: x["object"]),
            "undomained_count": inv["_undomained_count"],
            "undomained_sample": inv["_undomained"][:40]}


COMMANDS = {
    "what_reads": lambda b, args: what_reads(b, args[0]),
    "what_depends_on": lambda b, args: what_depends_on(b, args[0]),
    "incident": lambda b, args: incident_trace(b, args[0]),
    "uncertain_claims": lambda b, args: uncertain_claims(b),
    "superseded_claims": lambda b, args: superseded_claims(b),
    "domain_summary": lambda b, args: domain_summary(b, args[0]),
    "object_detail": lambda b, args: object_detail(b, args[0]),
    "stats": lambda b, args: stats(b),
    # Layer 14 (session #059+)
    "domain": lambda b, args: domain(b, args[0]),
    "domain_gap": lambda b, args: domain_gap(b),
    "process": lambda b, args: process_view(b, args[0]),
    "activate": lambda b, args: activate(b, " ".join(args) if args else ""),
    # Layer 15 (session #079) — capability model (4th axis)
    "capability": lambda b, args: capability(b, args[0] if args else None),
    "capability_gaps": lambda b, args: capability_gaps(b),
    # Layer 16 (session #097) — the tenant PROFILE (what the SYSTEM IS)
    "profile": lambda b, args: profile(b, args[0] if args else None),
    # s097 — the bidirectional model
    "ascend": lambda b, args: ascend(b, args[0]),
    "coherence": lambda b, args: coherence(b),
    "tree": lambda b, args: tree(b),
    "methods": lambda b, args: methods(b),
    # s099 — code as a first-class brain layer (source integrity + multi-domain linkage)
    "code": lambda b, args: code(b, args[0] if args else ""),
    "code_gaps": lambda b, args: code_gaps(b),
    "search": lambda b, args: search(b, " ".join(args) if args else ""),
    "entity": lambda b, args: entity(b, args[0] if args else ""),
    "section": lambda b, args: section(b, args[0] if args else ""),
    "blocking_code": lambda b, args: blocking_code(b, args[0] if args else None),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python {sys.argv[0]} <command> [args]")
        print(f"Commands: {', '.join(COMMANDS.keys())}")
        sys.exit(1)

    brain = load()
    cmd = sys.argv[1]
    args = sys.argv[2:]
    result = COMMANDS[cmd](brain, args)
    print(json.dumps(result, indent=2, ensure_ascii=False))
