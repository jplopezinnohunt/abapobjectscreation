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
import json, sys, time
from pathlib import Path

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
    """Trace an incident: root cause objects, annotations, claims, affected tables."""
    objects_in_incident = brain["indexes"]["by_incident"].get(incident_id, [])
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
        "description": d.get("description", "")[:200],
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
