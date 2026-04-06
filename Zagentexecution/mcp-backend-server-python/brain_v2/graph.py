"""
graph.py — BrainV2 core: NetworkX property graph with temporal edges + confidence decay.

Design: brain_spec.yaml (Session #039)
Patterns: Graphiti (temporal facts), Celonis PI Graph (enrichment), Panaya (impact)
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx


class BrainV2:
    """Universal Knowledge Graph with temporal edges and impact analysis."""

    def __init__(self, spec_version: str = "2.0"):
        self.graph = nx.DiGraph()
        self.spec_version = spec_version
        self.changelog: list[dict] = []
        self._created = datetime.now().isoformat()

    # ── Node Operations ──

    def add_node(self, node_id: str, node_type: str, name: str, *,
                 domain: str = "", layer: str = "",
                 metadata: dict | None = None, tags: list[str] | None = None,
                 source: str = "", session: str = "") -> None:
        """Add or update a node. Existing nodes get metadata merged."""
        if self.graph.has_node(node_id):
            existing = self.graph.nodes[node_id]
            if metadata:
                existing.setdefault("metadata", {}).update(metadata)
            existing["updated"] = datetime.now().isoformat()
        else:
            self.graph.add_node(node_id,
                                type=node_type,
                                name=name,
                                domain=domain,
                                layer=layer,
                                source=source,
                                metadata=metadata or {},
                                tags=tags or [],
                                added=datetime.now().isoformat(),
                                updated=datetime.now().isoformat())

    def get_node(self, node_id: str) -> dict | None:
        if self.graph.has_node(node_id):
            return {"id": node_id, **self.graph.nodes[node_id]}
        return None

    def find_nodes(self, node_type: str | None = None, domain: str | None = None,
                   name_contains: str | None = None) -> list[dict]:
        """Find nodes by type, domain, or name substring."""
        results = []
        for nid, data in self.graph.nodes(data=True):
            if node_type and data.get("type") != node_type:
                continue
            if domain and data.get("domain") != domain:
                continue
            if name_contains and name_contains.lower() not in data.get("name", "").lower():
                continue
            results.append({"id": nid, **data})
        return results

    # ── Edge Operations (Temporal) ──

    def add_edge(self, from_id: str, to_id: str, edge_type: str, *,
                 label: str = "", weight: float = 1.0,
                 evidence: str = "manual", confidence: float = 0.9,
                 session: str = "") -> str:
        """Add a temporal edge. Returns edge key."""
        now = datetime.now().isoformat()
        sess = session or "unknown"

        # Generate stable edge ID
        edge_id = f"{from_id}--{edge_type}-->{to_id}"

        # Check if this exact edge already exists and is still valid
        if self.graph.has_edge(from_id, to_id):
            existing = self.graph.edges[from_id, to_id]
            if existing.get("type") == edge_type and existing.get("valid_until") is None:
                # Update last_validated instead of creating duplicate
                existing["last_validated"] = sess
                existing["confidence"] = min(1.0, existing.get("confidence", 0.5) + 0.05)
                return edge_id

        # For multi-edges of different types, use the key parameter
        self.graph.add_edge(from_id, to_id,
                            key=edge_id,
                            type=edge_type,
                            label=label,
                            weight=weight,
                            evidence=evidence,
                            confidence=confidence,
                            valid_from=now,
                            valid_until=None,
                            superseded_by=None,
                            discovered_in=sess,
                            last_validated=sess)
        return edge_id

    def supersede_edge(self, from_id: str, to_id: str, edge_type: str,
                       new_edge_id: str, session: str = "") -> None:
        """Mark an existing edge as superseded (temporal invalidation)."""
        if self.graph.has_edge(from_id, to_id):
            edge = self.graph.edges[from_id, to_id]
            if edge.get("type") == edge_type and edge.get("valid_until") is None:
                edge["valid_until"] = datetime.now().isoformat()
                edge["superseded_by"] = new_edge_id

    def get_edges(self, node_id: str, direction: str = "both",
                  edge_type: str | None = None,
                  valid_only: bool = True) -> list[dict]:
        """Get edges for a node. direction: 'out', 'in', or 'both'."""
        results = []

        if direction in ("out", "both"):
            for _, to_id, data in self.graph.out_edges(node_id, data=True):
                if edge_type and data.get("type") != edge_type:
                    continue
                if valid_only and data.get("valid_until") is not None:
                    continue
                results.append({"from": node_id, "to": to_id, **data})

        if direction in ("in", "both"):
            for from_id, _, data in self.graph.in_edges(node_id, data=True):
                if edge_type and data.get("type") != edge_type:
                    continue
                if valid_only and data.get("valid_until") is not None:
                    continue
                results.append({"from": from_id, "to": node_id, **data})

        return results

    # ── Confidence Decay ──

    def apply_confidence_decay(self, current_session: int, rate: float = 0.05,
                                sessions_per_decay: int = 10, floor: float = 0.3) -> int:
        """Decay confidence on edges not validated recently. Returns count of decayed edges."""
        decayed = 0
        for u, v, data in self.graph.edges(data=True):
            if data.get("valid_until") is not None:
                continue  # skip superseded edges
            last = data.get("last_validated", "0")
            try:
                sessions_since = current_session - int(last)
            except (ValueError, TypeError):
                sessions_since = 20  # assume stale if unparseable
            if sessions_since >= sessions_per_decay:
                decay_steps = sessions_since // sessions_per_decay
                old_conf = data.get("confidence", 1.0)
                new_conf = max(floor, old_conf - (rate * decay_steps))
                if new_conf < old_conf:
                    data["confidence"] = round(new_conf, 3)
                    decayed += 1
        return decayed

    def get_stale_edges(self, threshold: float = 0.5) -> list[dict]:
        """Return edges below confidence threshold."""
        stale = []
        for u, v, data in self.graph.edges(data=True):
            if data.get("valid_until") is not None:
                continue
            if data.get("confidence", 1.0) < threshold:
                stale.append({"from": u, "to": v, **data})
        return sorted(stale, key=lambda e: e.get("confidence", 0))

    # ── Statistics ──

    def stats(self) -> dict:
        """Return graph statistics."""
        node_types: dict[str, int] = {}
        edge_types: dict[str, int] = {}
        domains: dict[str, int] = {}

        for _, data in self.graph.nodes(data=True):
            nt = data.get("type", "UNKNOWN")
            node_types[nt] = node_types.get(nt, 0) + 1
            d = data.get("domain", "UNKNOWN")
            domains[d] = domains.get(d, 0) + 1

        valid_edges = 0
        superseded_edges = 0
        for _, _, data in self.graph.edges(data=True):
            et = data.get("type", "UNKNOWN")
            edge_types[et] = edge_types.get(et, 0) + 1
            if data.get("valid_until") is None:
                valid_edges += 1
            else:
                superseded_edges += 1

        return {
            "spec_version": self.spec_version,
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "valid_edges": valid_edges,
            "superseded_edges": superseded_edges,
            "node_types": dict(sorted(node_types.items(), key=lambda x: -x[1])),
            "edge_types": dict(sorted(edge_types.items(), key=lambda x: -x[1])),
            "domains": dict(sorted(domains.items(), key=lambda x: -x[1])),
        }

    # ── Persistence ──

    def save(self, path: str | Path) -> None:
        """Save brain to JSON."""
        path = Path(path)
        data = nx.node_link_data(self.graph)
        data["_brain_meta"] = {
            "spec_version": self.spec_version,
            "created": self._created,
            "saved": datetime.now().isoformat(),
            "stats": self.stats(),
            "changelog": self.changelog[-50:],  # keep last 50 entries
        }
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "BrainV2":
        """Load brain from JSON."""
        path = Path(path)
        raw = json.loads(path.read_text(encoding="utf-8"))
        meta = raw.pop("_brain_meta", {})
        brain = cls(spec_version=meta.get("spec_version", "2.0"))
        brain.graph = nx.node_link_graph(raw)
        brain._created = meta.get("created", "")
        brain.changelog = meta.get("changelog", [])
        return brain

    def brain_hash(self) -> str:
        """SHA256 of the graph structure for companion checkpoint metadata."""
        s = json.dumps(self.stats(), sort_keys=True)
        return hashlib.sha256(s.encode()).hexdigest()[:12]

    # ── Changelog ──

    def log_ingestion(self, source: str, nodes_added: int, edges_added: int,
                      session: str = "") -> None:
        self.changelog.append({
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "session": session,
            "nodes_added": nodes_added,
            "edges_added": edges_added,
        })
