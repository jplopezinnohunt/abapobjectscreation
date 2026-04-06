"""
Brain v2 Impact Analysis — "What breaks if I change X?"
Source: BRAIN_V2_ARCHITECTURE.md Section C.1

BFS traversal with risk decay. Each hop multiplies risk by edge weight.
Follows impact direction (forward/backward/bidirectional) per edge type.
"""

from collections import deque
from brain_v2.core.schema import IMPACT_DIRECTION, RISK_WEIGHTS


def impact_analysis(brain, start_node_id: str, max_depth: int = 4,
                    min_risk: float = 0.1) -> dict:
    """
    Traverse the graph from a starting node, following impact-propagating edges.
    Returns all affected nodes with cumulative risk scores.
    """
    if not brain.has_node(start_node_id):
        return {
            "start_node": start_node_id,
            "error": f"Node '{start_node_id}' not found in brain",
            "total_affected": 0,
            "affected": [],
        }

    # Build adjacency lists for fast traversal
    # For impact analysis: if A --READS_TABLE--> B (forward edge),
    # then changing B impacts A. So we need REVERSE traversal for forward edges.
    # Impact means: "who would break if THIS node changes?"
    #
    # Forward edge (A reads B):  changing B breaks A  → from B, find A
    # Backward edge (A implements BAdI B): changing B breaks A → from B, find A
    # Bidirectional: both directions
    #
    # So: for FORWARD edges, we traverse BACKWARDS (target→source)
    #     for BACKWARD edges, we traverse FORWARDS (source→target)
    neighbors = {}  # node_id -> [(affected_node, edge_type, weight)]

    for edge in brain.edges:
        etype = edge["type"]
        direction = IMPACT_DIRECTION.get(etype)
        if not direction:
            continue

        weight = RISK_WEIGHTS.get(etype, 0.5)

        if direction == "forward":
            # A --READS_TABLE--> B: changing B breaks A → from B, reach A
            neighbors.setdefault(edge["to"], []).append(
                (edge["from"], etype, weight))
        elif direction == "backward":
            # A --IMPLEMENTS_BADI--> B: changing B affects A → from B, reach A
            neighbors.setdefault(edge["to"], []).append(
                (edge["from"], etype, weight))
        elif direction == "bidirectional":
            neighbors.setdefault(edge["to"], []).append(
                (edge["from"], etype, weight))
            neighbors.setdefault(edge["from"], []).append(
                (edge["to"], etype, weight))

    # BFS with risk accumulation
    affected = {}
    queue = deque([(start_node_id, 1.0, 0, [start_node_id])])
    visited = {start_node_id}

    while queue:
        node_id, cumulative_risk, depth, path = queue.popleft()

        if depth >= max_depth:
            continue

        for affected_node, etype, weight in neighbors.get(node_id, []):
            new_risk = cumulative_risk * weight
            if new_risk < min_risk:
                continue
            if affected_node not in affected or new_risk > affected[affected_node]["risk"]:
                visited.add(affected_node)
                affected[affected_node] = {
                    "node_id": affected_node,
                    "node": dict(brain.nodes[affected_node]) if brain.has_node(affected_node) else {},
                    "risk": round(new_risk, 3),
                    "depth": depth + 1,
                    "path": path + [affected_node],
                    "edge_type": etype,
                }
                queue.append((affected_node, new_risk, depth + 1, path + [affected_node]))

    results = sorted(affected.values(), key=lambda x: -x["risk"])

    return {
        "start_node": start_node_id,
        "start_info": dict(brain.nodes[start_node_id]),
        "total_affected": len(results),
        "max_risk": results[0]["risk"] if results else 0,
        "affected": results,
        "summary": _summarize_impact(results),
    }


def _summarize_impact(results: list) -> str:
    """Human-readable impact summary."""
    by_type = {}
    by_domain = {}
    critical = []

    for r in results:
        node = r.get("node", {})
        ntype = node.get("type", "unknown")
        domain = node.get("domain", "unknown")

        by_type[ntype] = by_type.get(ntype, 0) + 1
        by_domain[domain] = by_domain.get(domain, 0) + 1

        if r["risk"] >= 0.5:
            name = node.get("name", r["node_id"])
            critical.append(f"  [{r['risk']:.0%}] {name} ({ntype}) via {r['edge_type']}")

    lines = [f"Impact radius: {len(results)} objects affected"]
    lines.append(f"By type: {dict(sorted(by_type.items(), key=lambda x: -x[1]))}")
    lines.append(f"By domain: {dict(sorted(by_domain.items(), key=lambda x: -x[1]))}")
    if critical:
        lines.append("CRITICAL (>=50% risk):")
        lines.extend(critical[:30])

    return "\n".join(lines)
