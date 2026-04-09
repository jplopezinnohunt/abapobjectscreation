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
