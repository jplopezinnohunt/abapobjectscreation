"""
Brain v2 Incremental Update Protocol — Change tracking for incremental builds.
Source: BRAIN_V2_ARCHITECTURE.md Section B.5
"""

from datetime import datetime


class IncrementalTracker:
    """Wraps BrainGraph with change tracking for incremental updates."""

    def __init__(self, brain):
        self.brain = brain
        self.changelog = []

    def update_from_source(self, source_name: str, ingest_fn, *args, **kwargs):
        """Run an ingest function and track what changed."""
        before_nodes = set(self.brain.G.nodes())
        before_edges = self.brain.edge_count()

        ingest_fn(self.brain, *args, **kwargs)

        after_nodes = set(self.brain.G.nodes())
        new_nodes = after_nodes - before_nodes
        new_edges = self.brain.edge_count() - before_edges

        entry = {
            "source": source_name,
            "timestamp": datetime.now().isoformat(),
            "new_nodes": len(new_nodes),
            "new_edges": new_edges,
            "total_nodes": self.brain.node_count(),
            "total_edges": self.brain.edge_count(),
            "sample_nodes": sorted(new_nodes)[:10],
        }
        self.changelog.append(entry)
        return entry

    def diff_since(self, since_date: str) -> list:
        """Return all changes since a given date."""
        return [e for e in self.changelog if e["timestamp"] >= since_date]

    def summary(self) -> str:
        """Human-readable summary of all changes."""
        lines = ["Brain v2 Build Log:", "=" * 60]
        for entry in self.changelog:
            lines.append(
                f"  {entry['source']:30s} +{entry['new_nodes']:6d} nodes  "
                f"+{entry['new_edges']:6d} edges  "
                f"(total: {entry['total_nodes']:,} / {entry['total_edges']:,})"
            )
        lines.append("=" * 60)
        lines.append(
            f"  TOTAL: {self.brain.node_count():,} nodes, "
            f"{self.brain.edge_count():,} edges"
        )
        return "\n".join(lines)
