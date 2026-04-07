"""
Brain v2 Gap Analysis — "What's configured but never used? What's dead code?"
Source: BRAIN_V2_ARCHITECTURE.md Section C.4

Discovery engine with severity filtering.
Severity levels: CRITICAL > HIGH > MEDIUM > LOW
"""

# Severity ranking (lower number = more severe)
SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

# Isolated node types that are LOW severity (mass/taxonomic — expected to be isolated)
LOW_SEVERITY_ISOLATED = {
    "JOB_DEFINITION", "CODE_OBJECT", "DATA_ELEMENT", "DOMAIN_OBJECT",
    "TRANSACTION", "ICF_SERVICE", "NUMBER_RANGE", "IDOC_TYPE",
}


def find_gaps(brain, min_severity: str = "LOW") -> dict:
    """Identify configuration gaps, dead code, orphans with severity filtering.

    Args:
        brain: BrainGraph instance
        min_severity: Minimum severity to include ("CRITICAL", "HIGH", "MEDIUM", "LOW")

    Returns dict with categorized gaps and summary.
    """
    threshold = SEVERITY_RANK.get(min_severity, 3)

    # Pre-compute edge sets (O(E) once, not O(N*E))
    has_incoming = set()
    has_outgoing = set()
    documented_nodes = set()
    for edge in brain.edges:
        has_incoming.add(edge["to"])
        has_outgoing.add(edge["from"])
        if edge["type"] == "DOCUMENTED_IN":
            documented_nodes.add(edge["from"])
            documented_nodes.add(edge["to"])

    gaps = {
        "configured_but_unused": [],
        "dead_code": [],
        "orphan_integrations": [],
        "used_but_undocumented": [],
        "isolated_nodes": [],
    }

    for nid, node in brain.nodes.items():
        ntype = node.get("type", "")
        name = node.get("name", "")
        domain = node.get("domain", "")

        # --- CRITICAL: Config objects nobody references ---
        if ntype in ("DMEE_TREE", "BCM_RULE"):
            if nid not in has_incoming and threshold <= SEVERITY_RANK["CRITICAL"]:
                gaps["configured_but_unused"].append({
                    "node_id": nid, "type": ntype, "name": name,
                    "severity": "CRITICAL", "domain": domain,
                    "concern": f"{ntype} exists but nothing references it — may be dead config",
                })

        # --- HIGH: Payment methods / validation / substitution nobody uses ---
        elif ntype in ("PAYMENT_METHOD", "VALIDATION_RULE", "SUBSTITUTION_RULE"):
            if nid not in has_incoming and threshold <= SEVERITY_RANK["HIGH"]:
                gaps["configured_but_unused"].append({
                    "node_id": nid, "type": ntype, "name": name,
                    "severity": "HIGH", "domain": domain,
                    "concern": f"{ntype} configured but no incoming edges",
                })

        # --- HIGH: RFC-enabled FMs not called by anything ---
        if ntype == "FUNCTION_MODULE":
            rfc = node.get("metadata", {}).get("rfc_enabled", False)
            if not (nid in has_incoming) and rfc:
                sev = "HIGH"
                if threshold <= SEVERITY_RANK[sev]:
                    gaps["dead_code"].append({
                        "node_id": nid, "name": name,
                        "severity": sev, "domain": domain,
                        "concern": "RFC-enabled FM but no known caller in graph",
                    })

        # --- HIGH: RFC destinations nobody uses ---
        if ntype == "RFC_DESTINATION":
            if nid not in has_outgoing and nid not in has_incoming:
                if threshold <= SEVERITY_RANK["HIGH"]:
                    gaps["orphan_integrations"].append({
                        "node_id": nid, "name": name,
                        "severity": "HIGH", "domain": domain,
                        "concern": "RFC destination with no connected code or process",
                    })

        # --- MEDIUM: Code objects with no documentation ---
        if ntype in ("ABAP_CLASS", "FUNCTION_MODULE", "ABAP_REPORT"):
            if node.get("source") == "extracted_code" and nid not in documented_nodes:
                if threshold <= SEVERITY_RANK["MEDIUM"]:
                    gaps["used_but_undocumented"].append({
                        "node_id": nid, "type": ntype, "name": name,
                        "severity": "MEDIUM", "domain": domain,
                    })

        # --- LOW/MEDIUM: Completely isolated nodes ---
        if nid not in has_incoming and nid not in has_outgoing:
            if ntype in ("FUND", "FUND_CENTER", "FUND_AREA",
                         "GL_ACCOUNT", "COST_ELEMENT"):
                continue  # Skip taxonomic mass nodes entirely
            if ntype in LOW_SEVERITY_ISOLATED:
                sev = "LOW"
            elif ntype in ("ABAP_CLASS", "ABAP_REPORT", "ENHANCEMENT",
                           "BSP_APP", "ODATA_SERVICE"):
                sev = "MEDIUM"
            elif ntype in ("KNOWLEDGE_DOC", "SKILL"):
                sev = "LOW"
            else:
                sev = "LOW"
            if threshold <= SEVERITY_RANK[sev]:
                gaps["isolated_nodes"].append({
                    "node_id": nid, "type": ntype, "name": name,
                    "severity": sev, "domain": domain,
                })

    # Sort each category: severity first (CRITICAL→LOW), then name
    for key in gaps:
        gaps[key].sort(key=lambda x: (SEVERITY_RANK.get(x.get("severity", "LOW"), 3),
                                       x.get("name", "")))

    # Summary
    total = sum(len(v) for v in gaps.values() if isinstance(v, list))
    by_severity = {}
    for cat in gaps.values():
        if not isinstance(cat, list):
            continue
        for item in cat:
            s = item.get("severity", "LOW")
            by_severity[s] = by_severity.get(s, 0) + 1

    gaps["summary"] = {
        "configured_but_unused": len(gaps["configured_but_unused"]),
        "used_but_undocumented": len(gaps["used_but_undocumented"]),
        "orphan_integrations": len(gaps["orphan_integrations"]),
        "dead_code": len(gaps["dead_code"]),
        "isolated_nodes": len(gaps["isolated_nodes"]),
        "total_gaps": total,
        "by_severity": by_severity,
        "min_severity_applied": min_severity,
    }

    return gaps
