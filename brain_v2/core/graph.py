"""
Brain v2 Graph — NetworkX-based property graph with dual-store persistence.
Source: BRAIN_V2_ARCHITECTURE.md Sections D.1, D.2, A.4
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import networkx as nx


class BrainGraph:
    """Thin wrapper around NetworkX DiGraph with the Brain v2 property model."""

    def __init__(self):
        self.G = nx.DiGraph()
        self._meta = {
            "version": "2.0",
            "created": datetime.now().isoformat(),
        }

    # ── Node operations ──

    @property
    def nodes(self):
        """Dict-like access to node data: brain.nodes[node_id]"""
        return self.G.nodes

    @property
    def edges(self):
        """Iterate all edges as dicts with from/to + properties."""
        for u, v, d in self.G.edges(data=True):
            yield {"from": u, "to": v, **d}

    def add_node(self, node_id: str, node_type: str, name: str, *,
                 domain: str = "", layer: str = "code",
                 source: str = "", metadata: dict = None,
                 tags: list = None):
        """Add or update a node with the Brain v2 property model."""
        now = datetime.now().isoformat()
        props = {
            "type": node_type,
            "name": name,
            "domain": domain,
            "layer": layer,
            "source": source,
            "metadata": metadata or {},
            "tags": tags or [],
            "updated": now,
        }
        if node_id not in self.G:
            props["added"] = now
        else:
            props["added"] = self.G.nodes[node_id].get("added", now)
        self.G.add_node(node_id, **props)

    def add_edge(self, from_id: str, to_id: str, edge_type: str,
                 label: str = "", *, weight: float = 1.0,
                 evidence: str = "parsed", confidence: float = 1.0,
                 valid_from: str = None, valid_until: str = None,
                 discovered_in: str = "", last_validated: str = ""):
        """Add an edge with the Brain v2 temporal property model."""
        now = datetime.now().isoformat()
        self.G.add_edge(from_id, to_id,
                        type=edge_type,
                        label=label,
                        weight=weight,
                        evidence=evidence,
                        confidence=confidence,
                        valid_from=valid_from or now,
                        valid_until=valid_until,
                        discovered_in=discovered_in,
                        last_validated=last_validated or discovered_in)

    def has_node(self, node_id: str) -> bool:
        return node_id in self.G

    def node_count(self) -> int:
        return self.G.number_of_nodes()

    def edge_count(self) -> int:
        return self.G.number_of_edges()

    # ── Statistics ──

    def stats(self) -> dict:
        """Return summary statistics about the graph."""
        type_counts = {}
        domain_counts = {}
        layer_counts = {}
        for _, d in self.G.nodes(data=True):
            t = d.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
            dm = d.get("domain", "unknown")
            domain_counts[dm] = domain_counts.get(dm, 0) + 1
            ly = d.get("layer", "unknown")
            layer_counts[ly] = layer_counts.get(ly, 0) + 1

        edge_type_counts = {}
        for _, _, d in self.G.edges(data=True):
            et = d.get("type", "unknown")
            edge_type_counts[et] = edge_type_counts.get(et, 0) + 1

        return {
            "nodes": self.node_count(),
            "edges": self.edge_count(),
            "node_types": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
            "edge_types": dict(sorted(edge_type_counts.items(), key=lambda x: -x[1])),
            "domains": dict(sorted(domain_counts.items(), key=lambda x: -x[1])),
            "layers": dict(sorted(layer_counts.items(), key=lambda x: -x[1])),
        }

    # ── Persistence: JSON ──

    def save_json(self, filepath: str):
        """Serialize to JSON (backward-compatible with sap_brain.py format)."""
        data = {
            "meta": {
                **self._meta,
                "saved": datetime.now().isoformat(),
                "nodes": self.node_count(),
                "edges": self.edge_count(),
            },
            "nodes": [{"id": n, **d} for n, d in self.G.nodes(data=True)],
            "edges": [{"from": u, "to": v, **d} for u, v, d in self.G.edges(data=True)],
        }
        Path(filepath).write_text(
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8"
        )

    @classmethod
    def load_json(cls, filepath: str) -> "BrainGraph":
        """Load from JSON."""
        brain = cls()
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        brain._meta = data.get("meta", {})
        for n in data.get("nodes", []):
            nid = n.pop("id")
            brain.G.add_node(nid, **n)
        for e in data.get("edges", []):
            f, t = e.pop("from"), e.pop("to")
            brain.G.add_edge(f, t, **e)
        return brain

    # ── Persistence: SQLite index ──

    def save_sqlite(self, db_path: str):
        """Save an SQLite index for fast lookups without loading full graph."""
        conn = sqlite3.connect(db_path)
        conn.execute("DROP TABLE IF EXISTS nodes")
        conn.execute("DROP TABLE IF EXISTS edges")
        conn.execute("""
            CREATE TABLE nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                domain TEXT,
                layer TEXT,
                metadata_json TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE edges (
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                type TEXT NOT NULL,
                label TEXT,
                weight REAL DEFAULT 1.0,
                evidence TEXT,
                confidence REAL DEFAULT 1.0,
                PRIMARY KEY (from_id, to_id, type)
            )
        """)
        for nid, d in self.G.nodes(data=True):
            conn.execute(
                "INSERT OR REPLACE INTO nodes VALUES (?,?,?,?,?,?)",
                (nid, d.get("type", ""), d.get("name", ""),
                 d.get("domain", ""), d.get("layer", ""),
                 json.dumps(d.get("metadata", {}), default=str))
            )
        for u, v, d in self.G.edges(data=True):
            conn.execute(
                "INSERT OR REPLACE INTO edges VALUES (?,?,?,?,?,?,?)",
                (u, v, d.get("type", ""), d.get("label", ""),
                 d.get("weight", 1.0), d.get("evidence", ""),
                 d.get("confidence", 1.0))
            )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_domain ON nodes(domain)")
        conn.commit()
        conn.close()

    # ── Graph algorithms ──

    def critical_nodes(self, top_n: int = 20, exclude_types: set = None):
        """Nodes with highest betweenness centrality (most critical for system integrity)."""
        exclude = exclude_types or {"FUND", "FUND_CENTER", "FUND_AREA"}
        subgraph = self.G.subgraph(
            [n for n, d in self.G.nodes(data=True) if d.get("type") not in exclude]
        )
        if len(subgraph) == 0:
            return []
        centrality = nx.betweenness_centrality(subgraph, k=min(500, len(subgraph)))
        results = sorted(centrality.items(), key=lambda x: -x[1])[:top_n]
        return [(nid, round(score, 4), self.G.nodes[nid].get("name", ""))
                for nid, score in results if score > 0]

    def decay_confidence(self, current_session: int, decay_rate: float = 0.05,
                        decay_interval: int = 10, floor: float = 0.3) -> dict:
        """Apply confidence decay to edges not revalidated recently.

        Per Architecture Principle 4: edges lose -decay_rate per decay_interval
        sessions without revalidation. Never drops below floor.

        Returns summary of decayed edges.
        """
        decayed = 0
        stale = 0
        for u, v, d in self.G.edges(data=True):
            last_val = d.get("last_validated", "")
            if not last_val:
                continue
            # Parse session number from last_validated (could be "041" or "session_041")
            try:
                val_session = int("".join(c for c in str(last_val) if c.isdigit()) or "0")
            except ValueError:
                continue
            sessions_since = current_session - val_session
            if sessions_since <= 0:
                continue
            # Apply decay
            intervals = sessions_since // decay_interval
            if intervals > 0:
                old_conf = d.get("confidence", 1.0)
                new_conf = max(floor, old_conf - (decay_rate * intervals))
                if new_conf < old_conf:
                    d["confidence"] = round(new_conf, 2)
                    decayed += 1
                if new_conf <= floor:
                    stale += 1

        return {
            "current_session": current_session,
            "decayed_edges": decayed,
            "stale_edges_at_floor": stale,
            "decay_rate": decay_rate,
            "decay_interval": decay_interval,
            "floor": floor,
        }

    def stale_edges(self, threshold: float = 0.5) -> list:
        """Return edges with confidence below threshold, sorted by confidence."""
        results = []
        for u, v, d in self.G.edges(data=True):
            conf = d.get("confidence", 1.0)
            if conf < threshold:
                results.append({
                    "from": u, "to": v,
                    "type": d.get("type", ""),
                    "confidence": conf,
                    "last_validated": d.get("last_validated", ""),
                    "evidence": d.get("evidence", ""),
                })
        results.sort(key=lambda x: x["confidence"])
        return results

    def shortest_path(self, from_id: str, to_id: str):
        """Find shortest dependency chain between two nodes."""
        try:
            path = nx.shortest_path(self.G, from_id, to_id)
            edges_on_path = []
            for i in range(len(path) - 1):
                edge_data = self.G.edges[path[i], path[i + 1]]
                edges_on_path.append({
                    "from": path[i], "to": path[i + 1],
                    **edge_data
                })
            return {"path": path, "length": len(path) - 1, "edges": edges_on_path}
        except nx.NetworkXNoPath:
            return {"path": [], "length": -1, "message": "No path exists"}
        except nx.NodeNotFound as e:
            return {"path": [], "length": -1, "message": str(e)}
