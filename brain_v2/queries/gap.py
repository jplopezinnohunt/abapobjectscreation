"""
Brain v2 Gap Analysis — "What's configured but never used? What's dead code?"
Source: BRAIN_V2_ARCHITECTURE.md Section C.4

Discovery engine: finds orphans, dead code, undocumented objects, unused config.
"""


def find_gaps(brain) -> dict:
    """Identify configuration objects with no consumers, and code with no linkage."""
    gaps = {
        "configured_but_unused": [],
        "used_but_undocumented": [],
        "orphan_integrations": [],
        "dead_code": [],
        "isolated_nodes": [],
    }

    # Build sets for fast lookup
    has_incoming = set()
    has_outgoing = set()
    for edge in brain.edges:
        has_incoming.add(edge["to"])
        has_outgoing.add(edge["from"])

    for nid, node in brain.nodes.items():
        ntype = node.get("type", "")
        name = node.get("name", "")

        # Config objects nobody reads
        if ntype in ("DMEE_TREE", "BCM_RULE", "PAYMENT_METHOD",
                      "VALIDATION_RULE", "SUBSTITUTION_RULE"):
            if nid not in has_incoming:
                gaps["configured_but_unused"].append({
                    "node_id": nid, "type": ntype, "name": name,
                    "concern": "Config exists but nothing references it",
                })

        # Code objects with no DOCUMENTED_IN edge
        if ntype in ("ABAP_CLASS", "FUNCTION_MODULE", "ABAP_REPORT"):
            documented = any(
                (e["from"] == nid or e["to"] == nid) and e["type"] == "DOCUMENTED_IN"
                for e in brain.edges
            )
            if not documented and node.get("source") == "extracted_code":
                gaps["used_but_undocumented"].append({
                    "node_id": nid, "type": ntype, "name": name,
                })

        # RFC destinations nobody uses
        if ntype == "RFC_DESTINATION":
            used = nid in has_outgoing or any(
                e["to"] == nid and e["type"] not in ("CALLS_SYSTEM",)
                for e in brain.edges
            )
            if not used:
                gaps["orphan_integrations"].append({
                    "node_id": nid, "name": name,
                    "concern": "RFC destination exists but no code/process uses it",
                })

        # RFC-enabled FMs not called by anything
        if ntype == "FUNCTION_MODULE":
            called = nid in has_incoming
            rfc = node.get("metadata", {}).get("rfc_enabled", False)
            if not called and rfc:
                gaps["dead_code"].append({
                    "node_id": nid, "name": name,
                    "concern": "RFC-enabled FM but no known caller",
                })

        # Completely isolated nodes (no edges at all)
        if nid not in has_incoming and nid not in has_outgoing:
            if ntype not in ("FUND", "FUND_CENTER", "FUND_AREA",
                             "GL_ACCOUNT", "COST_ELEMENT"):
                gaps["isolated_nodes"].append({
                    "node_id": nid, "type": ntype, "name": name,
                })

    # Sort each category by name
    for key in gaps:
        gaps[key].sort(key=lambda x: x.get("name", ""))

    # Summary
    gaps["summary"] = {
        "configured_but_unused": len(gaps["configured_but_unused"]),
        "used_but_undocumented": len(gaps["used_but_undocumented"]),
        "orphan_integrations": len(gaps["orphan_integrations"]),
        "dead_code": len(gaps["dead_code"]),
        "isolated_nodes": len(gaps["isolated_nodes"]),
        "total_gaps": sum(len(v) for v in gaps.values() if isinstance(v, list)),
    }

    return gaps
