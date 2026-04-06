"""
Brain v2 CLI — Main entry point for all brain operations.
Source: BRAIN_V2_ARCHITECTURE.md Section C.5

Usage:
    python -m brain_v2.cli build              # Full rebuild from all sources
    python -m brain_v2.cli stats              # Show graph statistics
    python -m brain_v2.cli impact NODE_ID     # Impact analysis
    python -m brain_v2.cli depends NODE_ID    # Dependency tracing
    python -m brain_v2.cli similar NODE_ID    # Similarity search
    python -m brain_v2.cli gaps               # Gap analysis (discovery!)
    python -m brain_v2.cli search QUERY       # Search nodes by name
    python -m brain_v2.cli critical           # Show most critical nodes
    python -m brain_v2.cli path FROM TO       # Shortest path between nodes
"""

import sys
import json
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
GOLD_DB = PROJECT_ROOT / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
BRAIN_JSON = PROJECT_ROOT / "brain_v2" / "output" / "brain_v2_graph.json"
BRAIN_SQLITE = PROJECT_ROOT / "brain_v2" / "output" / "brain_v2_index.db"


def cmd_build():
    """Full rebuild from all sources."""
    from brain_v2.core.graph import BrainGraph
    from brain_v2.core.incremental import IncrementalTracker
    from brain_v2.ingestors.code_ingestor import ingest_code
    from brain_v2.ingestors.config_ingestor import ingest_config
    from brain_v2.ingestors.transport_ingestor import ingest_transports
    from brain_v2.ingestors.integration_ingestor import ingest_integration
    from brain_v2.ingestors.sqlite_ingestor import ingest_sqlite_schema, ingest_job_intelligence
    from brain_v2.ingestors.process_ingestor import ingest_processes
    from brain_v2.ingestors.knowledge_ingestor import ingest_knowledge

    brain = BrainGraph()
    tracker = IncrementalTracker(brain)
    db = str(GOLD_DB)

    print("Brain v2 — Full Build")
    print("=" * 60)

    # Phase 1: Code
    r = tracker.update_from_source("Code Parser", ingest_code, str(PROJECT_ROOT))
    print(f"  Code Parser:      +{r['new_nodes']:6d} nodes  +{r['new_edges']:6d} edges")

    # Phase 2: Config, Transports, Integration, Schema, Jobs
    r = tracker.update_from_source("Config", ingest_config, db)
    print(f"  Config:           +{r['new_nodes']:6d} nodes  +{r['new_edges']:6d} edges")

    r = tracker.update_from_source("Transports", ingest_transports, db)
    print(f"  Transports:       +{r['new_nodes']:6d} nodes  +{r['new_edges']:6d} edges")

    r = tracker.update_from_source("Integration", ingest_integration, db)
    print(f"  Integration:      +{r['new_nodes']:6d} nodes  +{r['new_edges']:6d} edges")

    r = tracker.update_from_source("SQLite Schema", ingest_sqlite_schema, db)
    print(f"  SQLite Schema:    +{r['new_nodes']:6d} nodes  +{r['new_edges']:6d} edges")

    r = tracker.update_from_source("Jobs", ingest_job_intelligence, db)
    print(f"  Jobs:             +{r['new_nodes']:6d} nodes  +{r['new_edges']:6d} edges")

    # Phase 3: Processes
    r = tracker.update_from_source("Processes", lambda b: ingest_processes(b))
    print(f"  Processes:        +{r['new_nodes']:6d} nodes  +{r['new_edges']:6d} edges")

    # Phase 4: Knowledge (docs, skills, sessions → graph, zero dead text)
    r = tracker.update_from_source("Knowledge", ingest_knowledge, str(PROJECT_ROOT))
    print(f"  Knowledge:        +{r['new_nodes']:6d} nodes  +{r['new_edges']:6d} edges")

    print("=" * 60)
    print(f"  TOTAL:  {brain.node_count():,} nodes  {brain.edge_count():,} edges")
    print()

    # Save
    BRAIN_JSON.parent.mkdir(parents=True, exist_ok=True)
    brain.save_json(str(BRAIN_JSON))
    brain.save_sqlite(str(BRAIN_SQLITE))
    print(f"Saved: {BRAIN_JSON}")
    print(f"Saved: {BRAIN_SQLITE}")

    # Changelog
    changelog_path = BRAIN_JSON.parent / "brain_v2_changelog.json"
    changelog_path.write_text(
        json.dumps(tracker.changelog, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"Saved: {changelog_path}")


def _load_brain():
    """Load the brain from JSON."""
    from brain_v2.core.graph import BrainGraph
    if not BRAIN_JSON.exists():
        print(f"Brain not built yet. Run: python -m brain_v2.cli build")
        sys.exit(1)
    return BrainGraph.load_json(str(BRAIN_JSON))


def cmd_stats():
    """Show graph statistics."""
    brain = _load_brain()
    s = brain.stats()
    print(f"Brain v2 — {brain.node_count():,} nodes, {brain.edge_count():,} edges")
    print()
    print("NODE TYPES:")
    for t, c in s["node_types"].items():
        print(f"  {t:30s} {c:8,d}")
    print()
    print("EDGE TYPES:")
    for t, c in s["edge_types"].items():
        print(f"  {t:30s} {c:8,d}")
    print()
    print("DOMAINS:")
    for t, c in s["domains"].items():
        print(f"  {t:30s} {c:8,d}")
    print()
    print("LAYERS:")
    for t, c in s["layers"].items():
        print(f"  {t:30s} {c:8,d}")


def cmd_impact(node_id: str, max_depth: int = 4):
    """Run impact analysis on a node."""
    from brain_v2.queries.impact import impact_analysis
    brain = _load_brain()
    result = impact_analysis(brain, node_id, max_depth=max_depth)
    if "error" in result:
        print(f"ERROR: {result['error']}")
        _suggest_nodes(brain, node_id)
        return
    print(f"Impact Analysis: {node_id}")
    print(f"  {result['start_info'].get('type', '?')} / {result['start_info'].get('domain', '?')}")
    print()
    print(result["summary"])


def cmd_depends(node_id: str):
    """Show dependency tree."""
    from brain_v2.queries.dependency import dependency_tree
    brain = _load_brain()
    result = dependency_tree(brain, node_id)
    if "error" in result:
        print(f"ERROR: {result['error']}")
        _suggest_nodes(brain, node_id)
        return
    print(f"Dependency Tree: {node_id}")
    print()
    print(result["summary"])


def cmd_similar(node_id: str):
    """Find similar nodes."""
    from brain_v2.queries.similarity import structural_similarity
    brain = _load_brain()
    result = structural_similarity(brain, node_id)
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return
    print(f"Similar to: {node_id} ({result['query_type']}, {result['query_neighbor_count']} neighbors)")
    print()
    for r in result["results"]:
        print(f"  {r['similarity']:.1%}  {r['name']:40s} ({r['domain']}) — {r['shared_count']} shared")


def cmd_gaps():
    """Run gap analysis (discovery!)."""
    from brain_v2.queries.gap import find_gaps
    brain = _load_brain()
    gaps = find_gaps(brain)
    s = gaps["summary"]
    print(f"Gap Analysis — {s['total_gaps']} total findings")
    print()
    for category, items in gaps.items():
        if category == "summary" or not isinstance(items, list) or not items:
            continue
        print(f"  {category} ({len(items)}):")
        for item in items[:10]:
            name = item.get("name", item.get("node_id", "?"))
            concern = item.get("concern", item.get("type", ""))
            print(f"    {name:40s} {concern}")
        if len(items) > 10:
            print(f"    ... +{len(items)-10} more")
        print()


def cmd_search(query: str):
    """Search nodes by name substring."""
    brain = _load_brain()
    query_upper = query.upper()
    matches = []
    for nid, d in brain.nodes.items():
        name = d.get("name", "")
        if query_upper in nid.upper() or query_upper in name.upper():
            matches.append((nid, d))

    print(f"Search: '{query}' — {len(matches)} matches")
    for nid, d in matches[:30]:
        print(f"  {nid:50s} {d.get('type',''):20s} {d.get('domain',''):10s}")
    if len(matches) > 30:
        print(f"  ... +{len(matches)-30} more")


def cmd_critical():
    """Show most critical nodes by betweenness centrality."""
    brain = _load_brain()
    print("Computing betweenness centrality (excluding FUND/FUND_CENTER nodes)...")
    results = brain.critical_nodes(top_n=20)
    print(f"\nTop 20 Critical Nodes (highest betweenness centrality):")
    for nid, score, name in results:
        ntype = brain.nodes[nid].get("type", "?")
        domain = brain.nodes[nid].get("domain", "?")
        print(f"  {score:.4f}  {name:40s} ({ntype}, {domain})")


def cmd_path(from_id: str, to_id: str):
    """Find shortest path between two nodes."""
    brain = _load_brain()
    result = brain.shortest_path(from_id, to_id)
    if result["length"] < 0:
        print(f"No path: {result.get('message', 'unknown')}")
        return
    print(f"Shortest path ({result['length']} hops):")
    for i, nid in enumerate(result["path"]):
        node = brain.nodes.get(nid, {})
        prefix = "  " if i == 0 else "  → "
        print(f"{prefix}{nid} ({node.get('type', '?')})")
        if i < len(result["edges"]):
            e = result["edges"][i]
            print(f"      [{e.get('type', '?')}]")


def _suggest_nodes(brain, query: str):
    """Suggest similar node IDs when exact match fails."""
    query_upper = query.upper()
    suggestions = []
    for nid in brain.nodes:
        # Check if any part of the query matches
        parts = query_upper.replace(":", " ").replace(".", " ").split()
        if any(p in nid.upper() for p in parts):
            suggestions.append(nid)
    if suggestions:
        print(f"\nDid you mean one of these?")
        for s in suggestions[:10]:
            print(f"  {s}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "build":
        cmd_build()
    elif cmd == "stats":
        cmd_stats()
    elif cmd == "impact":
        if len(sys.argv) < 3:
            print("Usage: brain_v2 impact NODE_ID [max_depth]")
            return
        depth = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        cmd_impact(sys.argv[2], depth)
    elif cmd == "depends":
        if len(sys.argv) < 3:
            print("Usage: brain_v2 depends NODE_ID")
            return
        cmd_depends(sys.argv[2])
    elif cmd == "similar":
        if len(sys.argv) < 3:
            print("Usage: brain_v2 similar NODE_ID")
            return
        cmd_similar(sys.argv[2])
    elif cmd == "gaps":
        cmd_gaps()
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: brain_v2 search QUERY")
            return
        cmd_search(" ".join(sys.argv[2:]))
    elif cmd == "critical":
        cmd_critical()
    elif cmd == "path":
        if len(sys.argv) < 4:
            print("Usage: brain_v2 path FROM_ID TO_ID")
            return
        cmd_path(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
