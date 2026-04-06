"""
Brain v2 Dependency Tracing — "What does Y depend on?"
Source: BRAIN_V2_ARCHITECTURE.md Section C.2

Traces BACKWARD from a node: "What does this node need to function?"
"""

from collections import deque


# Edge types that represent dependencies (source depends on target)
DEPENDENCY_EDGES = {
    "READS_TABLE", "READS_FIELD", "CALLS_FM", "USES_DMEE_TREE",
    "ROUTES_TO_BANK", "STEP_READS", "CALLS_VIA_RFC", "RUNS_PROGRAM",
    "CALLS_SYSTEM", "SERVES_HTTP",
}

# Reverse dependency edges (target depends on source)
REVERSE_DEPENDENCY_EDGES = {
    "IMPLEMENTS_BADI", "INHERITS_FROM", "CONFIGURES_FORMAT",
    "PROCESS_CONTAINS", "STEP_FOLLOWS",
}


def dependency_tree(brain, node_id: str, max_depth: int = 5) -> dict:
    """Build a complete dependency tree for a node."""
    if not brain.has_node(node_id):
        return {
            "root": node_id,
            "error": f"Node '{node_id}' not found",
            "total_dependencies": 0,
            "dependencies": [],
        }

    # Build reverse adjacency (what does X depend on?)
    depends_on = {}
    for edge in brain.edges:
        etype = edge["type"]
        if etype in DEPENDENCY_EDGES:
            depends_on.setdefault(edge["from"], []).append(
                (edge["to"], etype))
        elif etype in REVERSE_DEPENDENCY_EDGES:
            depends_on.setdefault(edge["to"], []).append(
                (edge["from"], etype))

    dependencies = {}
    queue = deque([(node_id, 0)])
    visited = {node_id}

    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue

        for dep_id, edge_type in depends_on.get(current, []):
            if dep_id not in visited:
                visited.add(dep_id)
                dependencies[dep_id] = {
                    "node_id": dep_id,
                    "node": dict(brain.nodes[dep_id]) if brain.has_node(dep_id) else {},
                    "depth": depth + 1,
                    "via": edge_type,
                    "depended_by": current,
                }
                queue.append((dep_id, depth + 1))

    results = sorted(dependencies.values(), key=lambda x: x["depth"])

    # Group by depth for display
    by_depth = {}
    for dep in results:
        d = dep["depth"]
        by_depth.setdefault(d, []).append(dep)

    summary_lines = [f"Total dependencies: {len(results)}"]
    for d in sorted(by_depth.keys()):
        items = by_depth[d]
        names = [i["node"].get("name", i["node_id"]) for i in items[:10]]
        types = set(i["node"].get("type", "?") for i in items)
        extra = f" (+{len(items)-10} more)" if len(items) > 10 else ""
        summary_lines.append(
            f"  Depth {d} ({', '.join(types)}): {', '.join(names)}{extra}")

    return {
        "root": node_id,
        "root_info": dict(brain.nodes[node_id]),
        "total_dependencies": len(results),
        "dependencies": results,
        "by_depth": {d: len(items) for d, items in by_depth.items()},
        "summary": "\n".join(summary_lines),
    }
