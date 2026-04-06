"""
query.py — Brain v2 query engine: impact, dependency, similarity, gap analysis.

Design: brain_spec.yaml Section query_engine
"""
from __future__ import annotations

from collections import deque
from typing import Any

from brain_v2.graph import BrainV2

# Impact direction per edge type
IMPACT_DIRECTION = {
    "CALLS_FM": "forward", "READS_TABLE": "forward", "WRITES_TABLE": "forward",
    "READS_FIELD": "forward", "IMPLEMENTS_BADI": "backward", "INHERITS_FROM": "bidirectional",
    "IMPLEMENTS_INTF": "backward", "USES_DMEE_TREE": "forward", "ROUTES_TO_BANK": "forward",
    "CONFIGURES_FORMAT": "forward", "VALIDATES_FIELD": "forward", "SUBSTITUTES_FIELD": "forward",
    "EXPOSES_FM": "backward", "CALLS_VIA_RFC": "forward", "TRANSPORTS": "forward",
    "STEP_READS": "forward", "STEP_FOLLOWS": "forward", "RUNS_PROGRAM": "forward",
    "READS_DMEE_FIELD": "forward", "PROCESSES_VIA_BCM": "forward",
    "CALLS_SYSTEM": "forward", "SENDS_IDOC": "forward",
    "CO_TRANSPORTED_WITH": "bidirectional",
}

RISK_WEIGHTS = {
    "WRITES_TABLE": 0.95, "USES_DMEE_TREE": 0.95, "ROUTES_TO_BANK": 0.95,
    "ASSIGNS_NUMBER_RANGE": 0.95, "IMPLEMENTS_BADI": 0.9, "CONFIGURES_FORMAT": 0.9,
    "PROCESSES_VIA_BCM": 0.9, "READS_DMEE_FIELD": 0.9,
    "VALIDATES_FIELD": 0.85, "SUBSTITUTES_FIELD": 0.85,
    "EXPOSES_FM": 0.85, "CALLS_VIA_RFC": 0.85, "IMPLEMENTS_INTF": 0.85,
    "CALLS_FM": 0.8, "INHERITS_FROM": 0.8, "CALLS_SYSTEM": 0.8,
    "READS_FIELD": 0.7, "TRANSPORTS": 0.7, "RUNS_PROGRAM": 0.7,
    "READS_TABLE": 0.6, "STEP_READS": 0.6, "FIELD_MAPS_TO": 0.6,
    "STEP_FOLLOWS": 0.5, "JOINS_VIA": 0.5, "STEP_USES_TCODE": 0.5,
    "CO_TRANSPORTED_WITH": 0.4, "POSTS_TO_GL": 0.3,
}


def impact_analysis(brain: BrainV2, node_id: str, max_depth: int = 5,
                    min_risk: float = 0.1) -> list[dict]:
    """BFS with risk decay: what breaks if node_id changes?

    Returns list of {node_id, node_name, node_type, depth, cumulative_risk, path}.
    """
    if not brain.graph.has_node(node_id):
        # Try fuzzy match
        candidates = [n for n in brain.graph.nodes if node_id.upper() in n.upper()]
        if candidates:
            node_id = candidates[0]
        else:
            return []

    visited = {node_id}
    queue = deque([(node_id, 0, 1.0, [node_id])])
    results = []

    while queue:
        current, depth, cum_risk, path = queue.popleft()
        if depth >= max_depth:
            continue

        # Forward edges (outgoing): things that depend on current
        for _, target, data in brain.graph.out_edges(current, data=True):
            if target in visited:
                continue
            if data.get("valid_until") is not None:
                continue
            edge_type = data.get("type", "")
            direction = IMPACT_DIRECTION.get(edge_type, "none")
            if direction not in ("forward", "bidirectional"):
                continue
            weight = RISK_WEIGHTS.get(edge_type, 0.5)
            new_risk = cum_risk * weight * data.get("confidence", 1.0)
            if new_risk < min_risk:
                continue
            visited.add(target)
            new_path = path + [f"--{edge_type}-->", target]
            target_data = brain.graph.nodes.get(target, {})
            results.append({
                "node_id": target,
                "node_name": target_data.get("name", target),
                "node_type": target_data.get("type", "UNKNOWN"),
                "domain": target_data.get("domain", ""),
                "depth": depth + 1,
                "cumulative_risk": round(new_risk, 4),
                "edge_type": edge_type,
                "path": new_path,
            })
            queue.append((target, depth + 1, new_risk, new_path))

        # Backward edges (incoming): things current depends on that could break it
        for source, _, data in brain.graph.in_edges(current, data=True):
            if source in visited:
                continue
            if data.get("valid_until") is not None:
                continue
            edge_type = data.get("type", "")
            direction = IMPACT_DIRECTION.get(edge_type, "none")
            if direction not in ("backward", "bidirectional"):
                continue
            weight = RISK_WEIGHTS.get(edge_type, 0.5)
            new_risk = cum_risk * weight * data.get("confidence", 1.0)
            if new_risk < min_risk:
                continue
            visited.add(source)
            new_path = path + [f"<--{edge_type}--", source]
            source_data = brain.graph.nodes.get(source, {})
            results.append({
                "node_id": source,
                "node_name": source_data.get("name", source),
                "node_type": source_data.get("type", "UNKNOWN"),
                "domain": source_data.get("domain", ""),
                "depth": depth + 1,
                "cumulative_risk": round(new_risk, 4),
                "edge_type": edge_type,
                "path": new_path,
            })
            queue.append((source, depth + 1, new_risk, new_path))

    # Sort by cumulative risk descending
    results.sort(key=lambda r: -r["cumulative_risk"])
    return results


def dependency_trace(brain: BrainV2, node_id: str, max_depth: int = 5,
                     domain_filter: str | None = None) -> list[dict]:
    """Reverse BFS: what does node_id depend on?"""
    if not brain.graph.has_node(node_id):
        candidates = [n for n in brain.graph.nodes if node_id.upper() in n.upper()]
        if candidates:
            node_id = candidates[0]
        else:
            return []

    visited = {node_id}
    queue = deque([(node_id, 0)])
    results = []

    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue

        # Outgoing edges = things this node uses/reads/calls
        for _, target, data in brain.graph.out_edges(current, data=True):
            if target in visited:
                continue
            if data.get("valid_until") is not None:
                continue
            target_data = brain.graph.nodes.get(target, {})
            if domain_filter and target_data.get("domain", "") != domain_filter:
                continue
            visited.add(target)
            results.append({
                "node_id": target,
                "node_name": target_data.get("name", target),
                "node_type": target_data.get("type", "UNKNOWN"),
                "domain": target_data.get("domain", ""),
                "depth": depth + 1,
                "edge_type": data.get("type", ""),
            })
            queue.append((target, depth + 1))

    return results


def similarity_search(brain: BrainV2, node_id: str, min_similarity: float = 0.2,
                      node_type_filter: str | None = None) -> list[dict]:
    """Jaccard similarity on typed neighbor sets."""
    if not brain.graph.has_node(node_id):
        candidates = [n for n in brain.graph.nodes if node_id.upper() in n.upper()]
        if candidates:
            node_id = candidates[0]
        else:
            return []

    # Build typed neighbor set for target
    target_neighbors = set()
    for _, to_id, data in brain.graph.out_edges(node_id, data=True):
        if data.get("valid_until") is None:
            target_neighbors.add((data.get("type", ""), to_id))

    if not target_neighbors:
        return []

    # Compare with all other nodes of same type
    target_type = brain.graph.nodes[node_id].get("type", "")
    results = []

    for nid, ndata in brain.graph.nodes(data=True):
        if nid == node_id:
            continue
        if node_type_filter and ndata.get("type") != node_type_filter:
            continue
        if not node_type_filter and ndata.get("type") != target_type:
            continue

        # Build neighbor set
        n_neighbors = set()
        for _, to_id, data in brain.graph.out_edges(nid, data=True):
            if data.get("valid_until") is None:
                n_neighbors.add((data.get("type", ""), to_id))

        if not n_neighbors:
            continue

        # Jaccard
        intersection = len(target_neighbors & n_neighbors)
        union = len(target_neighbors | n_neighbors)
        jaccard = intersection / union if union > 0 else 0

        if jaccard >= min_similarity:
            results.append({
                "node_id": nid,
                "node_name": ndata.get("name", nid),
                "node_type": ndata.get("type", ""),
                "domain": ndata.get("domain", ""),
                "similarity": round(jaccard, 4),
                "shared_neighbors": intersection,
            })

    results.sort(key=lambda r: -r["similarity"])
    return results[:20]


def gap_analysis(brain: BrainV2, domain_filter: str | None = None,
                 gap_type: str = "all") -> dict[str, list[dict]]:
    """Find gaps: configured-but-unused, used-but-undocumented, orphan nodes."""
    gaps: dict[str, list[dict]] = {
        "no_outgoing": [],      # nodes with 0 outgoing edges (dead ends)
        "no_incoming": [],      # nodes with 0 incoming edges (orphans)
        "undocumented": [],     # code nodes not linked to any KNOWLEDGE_DOC
    }

    for nid, ndata in brain.graph.nodes(data=True):
        if domain_filter and ndata.get("domain", "") != domain_filter:
            continue

        node_type = ndata.get("type", "")

        # Skip organizational nodes (funds, fund centers) — they're leaf nodes by design
        if node_type in ("FUND", "FUND_CENTER", "FUND_AREA", "GL_ACCOUNT", "COST_ELEMENT"):
            continue

        out_edges = [d for _, _, d in brain.graph.out_edges(nid, data=True)
                     if d.get("valid_until") is None and d.get("type") not in ("BELONGS_TO", "HAS_FUND_CENTER")]
        in_edges = [d for _, _, d in brain.graph.in_edges(nid, data=True)
                    if d.get("valid_until") is None and d.get("type") not in ("BELONGS_TO", "HAS_FUND_CENTER")]

        entry = {
            "node_id": nid,
            "node_name": ndata.get("name", nid),
            "node_type": node_type,
            "domain": ndata.get("domain", ""),
        }

        if gap_type in ("all", "no_outgoing"):
            if not out_edges and node_type in ("ABAP_CLASS", "ABAP_REPORT", "FUNCTION_MODULE"):
                gaps["no_outgoing"].append(entry)

        if gap_type in ("all", "no_incoming"):
            if not in_edges and node_type in ("SAP_TABLE", "FUNCTION_MODULE"):
                gaps["no_incoming"].append(entry)

    return gaps
