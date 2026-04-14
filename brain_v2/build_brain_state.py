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
# LAYER 11: First-class incident records (added Session #050 — fixes the
# "agent has brain context but doesn't use it" failure mode)
INCIDENTS = BRAIN_V2 / "incidents" / "incidents.json"
# LAYER 0: Core principles — constitutional layer above all rules/claims.
# Added Session #054. Governs HOW the agent decides, stores, compresses.
# Every feedback_rule should derive_from one of these. Zero-tolerance violations.
CORE_PRINCIPLES = BRAIN_V2 / "core_principles" / "core_principles.json"

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


def is_important(node, annotations, mandatory_names=frozenset()):
    """Criteria for including a node in brain_state.json."""
    name = node.get("name", "")
    ntype = node.get("type", "")
    meta = node.get("metadata", {})

    if name in mandatory_names:
        # Forced inclusion: referenced from incidents/annotations/claims.
        # Even if SKIP_TYPES says no, an object the brain has talked about
        # must remain queryable from the brain.
        return True
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


def collect_referenced_names(annotations, claims, incidents_records):
    """Walk every annotation/claim/incident record and gather every object
    name referenced. Used both to FORCE inclusion in objects[] and to flag
    blind spots (referenced but missing from the graph entirely)."""
    names = set()
    # From annotations
    for obj_name, payload in annotations.items():
        names.add(obj_name)
        for ann in payload.get("annotations", []):
            for rel in ann.get("related", []):
                if rel:
                    names.add(rel)
    # From claims
    for c in claims:
        for rel in c.get("related_objects", []):
            if rel:
                names.add(rel)
    # From incidents.json — related_objects + the names parsed from
    # code_validation_chain (objects appear as ZCL_..., LHRTS..., GB901, etc)
    for rec in incidents_records:
        for rel in rec.get("related_objects", []):
            if rel:
                names.add(rel)
    return names


def detect_blind_spots(referenced_names, graph_node_names, objects):
    """Blind spot = a name we have TALKED about (annotations / incidents /
    claims) that is NOT present in the brain as an object. The agent should
    treat these as 'extract me' priorities."""
    in_objects = set(objects.keys())
    in_graph = set(graph_node_names)
    blind = []
    for name in sorted(referenced_names):
        if name in in_objects:
            continue  # already classified
        # Two flavors:
        #   GHOST   — name appears in graph but was filtered out by is_important
        #   MISSING — name does not exist in graph at all (not extracted)
        flavor = "GHOST" if name in in_graph else "MISSING"
        blind.append({"name": name, "flavor": flavor})
    return blind


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
    # Pre-load incidents.json so we can FORCE-include any object referenced
    # from a first-class incident record. Without this the brain stays blind
    # to the very objects whose annotations explain past incidents.
    def _load_optional_local(path):
        if path.exists():
            return json.load(open(path, encoding="utf-8"))
        return []
    incidents_pre = _load_optional_local(INCIDENTS)
    referenced_names = collect_referenced_names(annotations, claims, incidents_pre)
    print(f"  {len(referenced_names)} names referenced from annotations/claims/incidents")

    objects = {}
    graph_node_names = set()
    for n in nodes:
        graph_node_names.add(n.get("name", ""))
        if not is_important(n, annotations, mandatory_names=referenced_names):
            continue
        name = n.get("name", "")
        objects[name] = build_object_entry(n, out_edges, in_edges, annotations, claims)

    # Detect blind spots: names we keep TALKING about but don't classify.
    blind_spots = detect_blind_spots(referenced_names, graph_node_names, objects)
    print(f"  {len(blind_spots)} blind spots detected (referenced but missing from objects[])")

    print("Building cross-cutting indexes...")
    # by_incident now stores dict with related_objects + the first-class
    # record fields (status, root_cause, doc, fix_path) so an agent that
    # reads the index alone gets enough to act without grepping.
    incidents_records_local = incidents_pre  # already loaded
    inc_record_by_id = {r["id"]: r for r in incidents_records_local}

    by_incident_objs = defaultdict(list)
    for name, obj in objects.items():
        for inc in obj.get("incidents", []):
            by_incident_objs[inc].append(name)

    by_incident = {}
    # Merge: every incident referenced from an object annotation OR from a
    # first-class incidents.json record gets an entry.
    all_inc_ids = set(by_incident_objs.keys()) | set(inc_record_by_id.keys())
    for inc_id in sorted(all_inc_ids):
        rec = inc_record_by_id.get(inc_id, {})
        related = sorted(set(by_incident_objs.get(inc_id, []))
                         | set(rec.get("related_objects", [])))
        by_incident[inc_id] = {
            "status": rec.get("status", "UNKNOWN"),
            "title": rec.get("title", ""),
            "domain": rec.get("domain", ""),
            "analysis_doc": rec.get("analysis_doc", ""),
            "root_cause_summary": rec.get("root_cause_summary", "")[:300],
            "fix_immediate": rec.get("fix_path", {}).get("immediate", "") if isinstance(rec.get("fix_path"), dict) else "",
            "related_objects": related,
        }

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
    incidents_records = incidents_pre  # already loaded above
    core_principles = load_optional(CORE_PRINCIPLES)  # LAYER 0 — constitutional
    superseded_full = [c for c in claims if c.get("claim_type") == "superseded"]

    # Coverage metrics — what's the brain's percent-coverage of the objects
    # it has TALKED about? This is what tells the agent at session-start
    # "you don't know what you don't know".
    coverage = {
        "objects_in_brain": len(objects),
        "names_referenced": len(referenced_names),
        "names_classified": len(referenced_names & set(objects.keys())),
        "blind_spots_total": len(blind_spots),
        "blind_spots_ghosts": sum(1 for b in blind_spots if b["flavor"] == "GHOST"),
        "blind_spots_missing": sum(1 for b in blind_spots if b["flavor"] == "MISSING"),
    }
    if referenced_names:
        coverage["pct_classified"] = round(
            100 * coverage["names_classified"] / len(referenced_names), 1
        )

    brain_state = {
        "_design": "Object-centric knowledge graph with 13 layers (0-12). 1 Read = full self-aware intelligence. Layer 0 (core_principles) added Session #054 — constitutional tier above rules. Layer 11 (incidents) added Session #050 to fix 'context loaded but not used' failure mode.",
        "_stats": {
            "core_principles": len(core_principles),
            "objects": len(objects),
            "rules": len(rules),
            "claims": len(claims),
            "incidents": len(by_incident),
            "incident_records": len(incidents_records),
            "domains": len(by_domain),
            "known_unknowns": len(known_unknowns),
            "falsification_pending": len([f for f in falsification if f.get("status") == "PENDING"]),
            "user_questions_open": len([q for q in user_questions if q.get("status") != "ANSWERED"]),
            "data_quality_open": len([d for d in data_quality if d.get("status") == "OPEN"]),
            "superseded": len(superseded_full),
            "session": 54,
        },
        # LAYER 0: Core principles — constitutional tier above all rules/claims.
        # Governs HOW the agent decides, stores, compresses. Zero-tolerance
        # violations. Every feedback_rule should derive_from one of these.
        # Read this BEFORE any other layer. Established Session #054.
        "core_principles": core_principles,
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
        # LAYER 11: First-class incident records — full root cause + fix path
        # + analysis_doc inline. When user mentions an incident ID, the agent
        # MUST read incidents[id].analysis_doc as the first action, not grep.
        "incidents": incidents_records,
        # LAYER 12: Blind spots — names the brain has talked about (in
        # annotations / claims / incidents) but does NOT carry as first-class
        # objects. Each is a queue item: extract or upgrade. The agent should
        # read this at session start and treat MISSING flavor entries as
        # extraction-priority work, GHOST entries as filter-tuning work.
        "blind_spots": blind_spots,
        "_coverage": coverage,
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
    print(f"  {len(incidents_records)} first-class incident records")
    print(f"  Coverage: {coverage.get('pct_classified', 0)}% "
          f"({coverage['names_classified']}/{coverage['names_referenced']} referenced names classified)")
    print(f"  Blind spots: {coverage['blind_spots_total']} "
          f"(ghosts={coverage['blind_spots_ghosts']}, missing={coverage['blind_spots_missing']})")


if __name__ == "__main__":
    main()
