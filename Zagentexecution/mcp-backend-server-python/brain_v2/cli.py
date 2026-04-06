"""
cli.py -- Brain v2 command-line interface.

Usage:
    python -m brain_v2.cli --impact "FPAYP.XREF3"
    python -m brain_v2.cli --impact "YCL_IDFI_CGI_DMEE_FR"
    python -m brain_v2.cli --depends-on "PROCESS:Payment_E2E"
    python -m brain_v2.cli --similar-to "ABAP_CLASS:YCL_IDFI_CGI_DMEE_FR"
    python -m brain_v2.cli --gaps --domain FI
    python -m brain_v2.cli --stale
    python -m brain_v2.cli --stats
    python -m brain_v2.cli --node "FPAYP"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
BRAIN_PATH = REPO / ".agents" / "intelligence" / "brain_v2.json"


def main():
    ap = argparse.ArgumentParser(description="Brain v2 Query CLI")
    ap.add_argument("--impact", type=str, help="Impact analysis: what breaks if this changes?")
    ap.add_argument("--depends-on", type=str, help="Dependency trace: what does this depend on?")
    ap.add_argument("--similar-to", type=str, help="Similarity search: what's like this?")
    ap.add_argument("--gaps", action="store_true", help="Gap analysis")
    ap.add_argument("--stale", action="store_true", help="Stale edges report")
    ap.add_argument("--stats", action="store_true", help="Graph statistics")
    ap.add_argument("--node", type=str, help="Show node details + edges")
    ap.add_argument("--domain", type=str, help="Filter by domain")
    ap.add_argument("--depth", type=int, default=4, help="Max traversal depth")
    ap.add_argument("--min-risk", type=float, default=0.1, help="Min cumulative risk for impact")
    args = ap.parse_args()

    from brain_v2.graph import BrainV2
    from brain_v2.query import impact_analysis, dependency_trace, similarity_search, gap_analysis

    if not BRAIN_PATH.exists():
        print(f"Brain not found at {BRAIN_PATH}. Run: python -m brain_v2.build --all")
        return 1

    brain = BrainV2.load(BRAIN_PATH)
    print(f"[Brain v2] {brain.graph.number_of_nodes():,} nodes / {brain.graph.number_of_edges():,} edges\n")

    if args.stats:
        s = brain.stats()
        print("Node types:")
        for nt, c in list(s["node_types"].items())[:15]:
            print(f"  {nt:30s} {c:>8,}")
        print("\nEdge types:")
        for et, c in list(s["edge_types"].items())[:15]:
            print(f"  {et:30s} {c:>8,}")
        return 0

    if args.node:
        query = args.node.upper()
        # Find matching nodes
        matches = [n for n in brain.graph.nodes if query in n.upper()]
        if not matches:
            print(f"No nodes matching '{args.node}'")
            return 1
        for nid in matches[:5]:
            nd = brain.graph.nodes[nid]
            print(f"NODE: {nid}")
            print(f"  type:   {nd.get('type', '?')}")
            print(f"  name:   {nd.get('name', '?')}")
            print(f"  domain: {nd.get('domain', '?')}")
            print(f"  layer:  {nd.get('layer', '?')}")
            meta = nd.get("metadata", {})
            if meta:
                print(f"  metadata: {meta}")
            edges = brain.get_edges(nid)
            if edges:
                print(f"  edges ({len(edges)}):")
                for e in edges[:20]:
                    direction = "->" if e["from"] == nid else "<-"
                    other = e["to"] if e["from"] == nid else e["from"]
                    print(f"    {direction} [{e.get('type','')}] {other} (conf={e.get('confidence',0):.2f})")
                if len(edges) > 20:
                    print(f"    ... and {len(edges)-20} more")
            print()
        return 0

    if args.impact:
        print(f"IMPACT ANALYSIS: What breaks if '{args.impact}' changes?\n")
        results = impact_analysis(brain, args.impact, max_depth=args.depth, min_risk=args.min_risk)
        if not results:
            print("  No impact found (node may not exist or has no forward dependencies)")
            return 0
        print(f"  {len(results)} affected nodes:\n")
        for r in results[:30]:
            risk_bar = "#" * int(r["cumulative_risk"] * 20)
            print(f"  [{r['cumulative_risk']:.3f}] {risk_bar:20s} {r['node_type']:20s} {r['node_name']}")
            if r["depth"] <= 2:
                # Show path for close neighbors
                path_str = " ".join(str(p) for p in r["path"])
                print(f"         path: {path_str[:120]}")
        if len(results) > 30:
            print(f"\n  ... and {len(results)-30} more. Use --depth or --min-risk to filter.")
        return 0

    if args.depends_on:
        print(f"DEPENDENCY TRACE: What does '{args.depends_on}' depend on?\n")
        results = dependency_trace(brain, args.depends_on, max_depth=args.depth,
                                   domain_filter=args.domain)
        if not results:
            print("  No dependencies found")
            return 0
        print(f"  {len(results)} dependencies:\n")
        for r in results[:30]:
            print(f"  depth={r['depth']}  [{r['edge_type']:25s}] {r['node_type']:20s} {r['node_name']}")
        return 0

    if args.similar_to:
        print(f"SIMILARITY SEARCH: What's similar to '{args.similar_to}'?\n")
        results = similarity_search(brain, args.similar_to)
        if not results:
            print("  No similar nodes found")
            return 0
        for r in results[:15]:
            print(f"  sim={r['similarity']:.3f}  shared={r['shared_neighbors']:3d}  {r['node_type']:20s} {r['node_name']}")
        return 0

    if args.gaps:
        print(f"GAP ANALYSIS{' (domain=' + args.domain + ')' if args.domain else ''}:\n")
        gaps = gap_analysis(brain, domain_filter=args.domain)
        for gap_type, items in gaps.items():
            if items:
                print(f"  {gap_type}: {len(items)} items")
                for item in items[:10]:
                    print(f"    {item['node_type']:20s} {item['node_name']}")
                if len(items) > 10:
                    print(f"    ... and {len(items)-10} more")
                print()
        return 0

    if args.stale:
        stale = brain.get_stale_edges()
        print(f"STALE EDGES (confidence < 0.5): {len(stale)}\n")
        for e in stale[:20]:
            print(f"  conf={e.get('confidence',0):.2f}  [{e.get('type','')}] {e['from']} -> {e['to']}")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
