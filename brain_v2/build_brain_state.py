"""
Build brain_state.json — the agent's session bootstrap file.

Architecture: object-centric knowledge graph with cross-cutting indexes.
- One Read call at session start = full intelligence in context
- ~2.8% of 1M context window
- All relationships inline (no JOINs needed)

Sources:
  brain_v2/output/brain_v2_graph.json  (NetworkX graph)
  brain_v2/annotations/annotations.json (object findings)
  brain_v2/claims/claims.json           (system facts)
  brain_v2/agent_rules/feedback_rules.json (behavioral rules)

Output: brain_v2/brain_state.json

Usage: python brain_v2/build_brain_state.py
"""
import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
BRAIN_V2 = PROJECT_ROOT / "brain_v2"
GRAPH = BRAIN_V2 / "output" / "brain_v2_graph.json"
ANNOTATIONS = BRAIN_V2 / "annotations" / "annotations.json"
CLAIMS = BRAIN_V2 / "claims" / "claims.json"
RULES = BRAIN_V2 / "agent_rules" / "feedback_rules.json"
BRAIN_STATE = BRAIN_V2 / "brain_state.json"

# AGI self-awareness layers (inspired by PPM-brain S-22)
KNOWN_UNKNOWNS = BRAIN_V2 / "agi" / "known_unknowns.json"
FALSIFICATION = BRAIN_V2 / "agi" / "falsification_log.json"
USER_QUESTIONS = BRAIN_V2 / "agi" / "user_questions.json"
DATA_QUALITY = BRAIN_V2 / "agi" / "data_quality_issues.json"

SKIP_TYPES = {
    "FUND", "FUND_CENTER", "FUND_AREA", "TRANSPORT", "CODE_OBJECT",
    "TABLE_FIELD", "DATA_ELEMENT", "DOMAIN_OBJECT", "PACKAGE",
    "NUMBER_RANGE", "ICF_SERVICE", "TRANSACTION", "KNOWLEDGE_DOC",
    "SKILL", "SESSION", "JOB_DEFINITION",
}

KEY_TABLES = {
    "LFA1", "LFB1", "KNA1", "BKPF", "FEBEP", "FEBKO", "T012", "T012K",
    "T042I", "FPAYP", "REGUH", "PA0001", "PTRV_SCOS", "GGB1", "GB922",
    "BSIS", "BSAS", "FMIFIIT", "PRPS", "T001", "T042A",
}


def is_important(node, annotations):
    """Criteria for including a node in brain_state.json."""
    name = node.get("name", "")
    ntype = node.get("type", "")
    meta = node.get("metadata", {})

    if ntype in SKIP_TYPES:
        return False
    if name in annotations:
        return True
    if ntype in ("ABAP_CLASS", "ABAP_REPORT", "FUNCTION_MODULE", "ENHANCEMENT"):
        if name.startswith(("Y", "Z")) and (meta.get("tables_read") or meta.get("fms_called")):
            return True
    if "SAP_STANDARD" in str(meta.get("path", "")):
        return True
    if ntype == "SAP_TABLE" and name in KEY_TABLES:
        return True
    return False


def build_object_entry(node, out_edges, in_edges, annotations, claims):
    """Build object-centric entry with all relationships inline."""
    nid = node["id"]
    name = node.get("name", "")
    obj = {
        "type": node.get("type", ""),
        "domain": node.get("domain", ""),
    }

    reads, calls, writes, other_out = [], [], [], []
    for e in out_edges.get(nid, []):
        target_name = e["to"].split(":")[-1]
        if e["type"] == "READS_TABLE":
            reads.append(target_name)
        elif e["type"] == "CALLS_FM":
            calls.append(target_name)
        elif e["type"] == "WRITES_TABLE":
            writes.append(target_name)
        else:
            other_out.append({"to": target_name, "type": e["type"]})
    if reads:
        obj["reads_tables"] = sorted(set(reads))
    if calls:
        obj["calls_fms"] = sorted(set(calls))
    if writes:
        obj["writes_tables"] = sorted(set(writes))
    if other_out:
        obj["other_edges"] = other_out[:10]

    read_by, called_by = [], []
    for e in in_edges.get(nid, []):
        source_name = e["from"].split(":")[-1]
        if e["type"] == "READS_TABLE":
            read_by.append(source_name)
        elif e["type"] == "CALLS_FM":
            called_by.append(source_name)
    if read_by:
        obj["read_by"] = sorted(set(read_by))
    if called_by:
        obj["called_by"] = sorted(set(called_by))

    if name in annotations:
        obj["annotations"] = annotations[name]["annotations"]

    obj_claims = [c for c in claims if name in c.get("related_objects", [])]
    if obj_claims:
        obj["claims"] = [
            {
                "id": c["id"],
                "tier": c["confidence"],
                "type": c["claim_type"],
                "claim": c["claim"][:150],
            }
            for c in obj_claims
        ]

    incidents = set()
    if name in annotations:
        for a in annotations[name]["annotations"]:
            if a.get("incident"):
                incidents.add(a["incident"])
    if incidents:
        obj["incidents"] = sorted(incidents)

    return obj


def main():
    print("Loading sources...")
    rules = json.load(open(RULES, encoding="utf-8"))
    claims = json.load(open(CLAIMS, encoding="utf-8"))
    annotations = json.load(open(ANNOTATIONS, encoding="utf-8"))
    graph = json.load(open(GRAPH, encoding="utf-8"))
    nodes = graph["nodes"]
    edges = graph["edges"]

    print("Indexing edges...")
    out_edges = defaultdict(list)
    in_edges = defaultdict(list)
    for e in edges:
        if e["type"] == "TRANSPORTS":
            continue
        out_edges[e["from"]].append(e)
        in_edges[e["to"]].append(e)

    print("Selecting important objects...")
    objects = {}
    for n in nodes:
        if not is_important(n, annotations):
            continue
        name = n.get("name", "")
        objects[name] = build_object_entry(n, out_edges, in_edges, annotations, claims)

    print("Building cross-cutting indexes...")
    by_incident = defaultdict(list)
    for name, obj in objects.items():
        for inc in obj.get("incidents", []):
            by_incident[inc].append(name)

    by_domain = defaultdict(list)
    for name, obj in objects.items():
        if obj.get("domain"):
            by_domain[obj["domain"]].append(name)

    uncertain = [
        {"id": c["id"], "tier": c["confidence"], "claim": c["claim"][:100]}
        for c in claims
        if c["confidence"] in ("TIER_3", "TIER_4", "TIER_5")
    ]
    superseded = [
        {
            "id": c["id"],
            "claim": c["claim"][:100],
            "resolution": c.get("resolution_notes", ""),
        }
        for c in claims
        if c["claim_type"] == "superseded"
    ]

    # Load AGI self-awareness layers (5 layers from PPM-brain S-22)
    def load_optional(path):
        if path.exists():
            return json.load(open(path, encoding="utf-8"))
        return []

    known_unknowns = load_optional(KNOWN_UNKNOWNS)
    falsification = load_optional(FALSIFICATION)
    user_questions = load_optional(USER_QUESTIONS)
    data_quality = load_optional(DATA_QUALITY)
    superseded_full = [c for c in claims if c.get("claim_type") == "superseded"]

    brain_state = {
        "_design": "Object-centric knowledge graph with 10 AGI layers. 1 Read = full self-aware intelligence.",
        "_stats": {
            "objects": len(objects),
            "rules": len(rules),
            "claims": len(claims),
            "incidents": len(by_incident),
            "domains": len(by_domain),
            "known_unknowns": len(known_unknowns),
            "falsification_pending": len([f for f in falsification if f.get("status") == "PENDING"]),
            "user_questions_open": len([q for q in user_questions if q.get("status") != "ANSWERED"]),
            "data_quality_open": len([d for d in data_quality if d.get("status") == "OPEN"]),
            "superseded": len(superseded_full),
            "session": 49,
        },
        # LAYER 1: Object-centric graph
        "objects": objects,
        # LAYER 2: Cross-cutting indexes
        "indexes": {
            "by_incident": dict(by_incident),
            "by_domain": dict(by_domain),
            "uncertain_claims": uncertain,
            "superseded_claims": superseded,
        },
        # LAYER 3: Behavioral rules (agent DNA)
        "rules": rules,
        # LAYER 4: Claims with evidence
        "claims": claims,
        # LAYER 5: Sessions → in brain_v2_active.db (for filtering)
        # LAYER 6: Known unknowns — explicit gaps (what I don't know)
        "known_unknowns": known_unknowns,
        # LAYER 7: Falsification log — predictions being tested
        "falsification": falsification,
        # LAYER 8: Superseded claims — what I was wrong about (anti-regression)
        "superseded": superseded_full,
        # LAYER 9: User questions — parked/answered questions (nothing gets lost)
        "user_questions": user_questions,
        # LAYER 10: Data quality issues — source data bugs to flag
        "data_quality": data_quality,
    }

    out = json.dumps(brain_state, indent=2, ensure_ascii=False)
    BRAIN_STATE.write_text(out, encoding="utf-8")
    tokens = len(out) // 4
    print(
        f"\nbrain_state.json: {len(out):,} bytes, ~{tokens:,} tokens "
        f"({tokens/1000000*100:.1f}% of 1M context)"
    )
    print(f"  {len(objects)} objects with inline relationships")
    print(f"  {len(rules)} rules | {len(claims)} claims")
    print(f"  {len(by_incident)} incidents | {len(by_domain)} domains indexed")


if __name__ == "__main__":
    main()
