"""
Brain v2 Similarity Search — "What's similar to X?"
Source: BRAIN_V2_ARCHITECTURE.md Section C.3

Structural similarity via Jaccard coefficient on shared neighbors.
"""


def structural_similarity(brain, node_id: str, top_n: int = 10) -> dict:
    """Find nodes that share the most neighbors (Jaccard similarity)."""
    if not brain.has_node(node_id):
        return {"query": node_id, "error": f"Node '{node_id}' not found", "results": []}

    target_type = brain.nodes[node_id].get("type")

    # Get neighbors of target
    target_neighbors = set()
    for edge in brain.edges:
        if edge["from"] == node_id:
            target_neighbors.add(edge["to"])
        elif edge["to"] == node_id:
            target_neighbors.add(edge["from"])

    if not target_neighbors:
        return {"query": node_id, "note": "Node has no neighbors", "results": []}

    # Pre-compute all neighbor sets for same-type nodes
    all_neighbors = {}
    for edge in brain.edges:
        for nid in (edge["from"], edge["to"]):
            if nid != node_id:
                other = edge["to"] if nid == edge["from"] else edge["from"]
                all_neighbors.setdefault(nid, set()).add(other)

    scores = []
    for nid, neighbors in all_neighbors.items():
        if nid == node_id:
            continue
        node = brain.nodes.get(nid, {})
        if node.get("type") != target_type:
            continue

        intersection = len(target_neighbors & neighbors)
        if intersection == 0:
            continue
        union = len(target_neighbors | neighbors)
        score = intersection / union

        scores.append({
            "node_id": nid,
            "name": node.get("name", ""),
            "type": node.get("type", ""),
            "domain": node.get("domain", ""),
            "similarity": round(score, 3),
            "shared_count": intersection,
            "shared_neighbors": sorted(target_neighbors & neighbors)[:5],
        })

    scores.sort(key=lambda x: -x["similarity"])

    return {
        "query": node_id,
        "query_type": target_type,
        "query_neighbor_count": len(target_neighbors),
        "results": scores[:top_n],
    }
