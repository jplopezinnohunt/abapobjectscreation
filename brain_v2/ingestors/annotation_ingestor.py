"""
Brain v2 Annotation Ingestor — Merge object annotations into the graph.

Reads annotations.json and:
1. Adds 'annotations' to existing node metadata
2. Creates edges from incidents to objects (ROOT_CAUSED_BY, CONTRIBUTING_FACTOR)
3. Creates DERIVES_FIELD / CLEARS_FIELD edges from line-level annotations
4. Tags nodes with domains/topics from annotations
5. Materializes tables_read/fms_called from code node metadata into real edges
   (fixes the gap where 4,030 ABAP nodes have metadata but zero edges)
"""

import json
import os
from datetime import datetime


def _find_node(brain, object_name):
    """Find a node by name, trying multiple ID patterns."""
    patterns = [
        object_name,
        f"CLASS:{object_name}",
        f"PROG:{object_name}",
        f"FM:{object_name}",
        f"SAP_TABLE:{object_name}",
        f"CONFIG:{object_name}",
    ]
    for p in patterns:
        if p in brain.G:
            return p
    # Fuzzy: check if any node name contains the object name
    for nid, ndata in brain.G.nodes(data=True):
        if ndata.get("name", "") == object_name:
            return nid
    return None


def ingest_annotations(brain, project_root: str):
    """Merge annotations into the brain graph."""
    annotations_file = os.path.join(project_root, "brain_v2", "annotations", "annotations.json")
    if not os.path.exists(annotations_file):
        print("  [annotations] No annotations.json found — skipping")
        return

    with open(annotations_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = {"annotated": 0, "incident_edges": 0, "field_edges": 0, "not_found": 0}

    for object_id, obj_data in data.items():
        # Find the node in the brain
        node_id = _find_node(brain, object_id.split(":")[0])
        if not node_id:
            stats["not_found"] += 1
            continue

        # Merge annotations into node metadata
        node_data = brain.G.nodes[node_id]
        metadata = node_data.get("metadata", {})
        metadata["annotations"] = obj_data.get("annotations", [])
        metadata["annotation_count"] = len(obj_data.get("annotations", []))
        node_data["metadata"] = metadata

        # Add annotation tags to node tags
        existing_tags = set(node_data.get("tags", []))
        for ann in obj_data.get("annotations", []):
            existing_tags.add(f"ann:{ann['tag']}")
            if ann.get("incident"):
                existing_tags.add(f"incident:{ann['incident']}")
        node_data["tags"] = list(existing_tags)

        stats["annotated"] += 1

        # Create incident edges
        for ann in obj_data.get("annotations", []):
            if ann.get("incident"):
                inc_id = f"INCIDENT:{ann['incident']}"
                # Ensure incident node exists
                if inc_id not in brain.G:
                    brain.add_node(inc_id, "INCIDENT", ann["incident"],
                                   domain="Support", layer="operations",
                                   source="annotation",
                                   tags=["incident"])

                edge_type = "ROOT_CAUSED_BY" if ann.get("tag") == "CRITICAL" else "CONTRIBUTING_FACTOR"
                brain.add_edge(inc_id, node_id, edge_type,
                               label=ann.get("finding", "")[:80],
                               evidence="annotation",
                               discovered_in=ann.get("session", ""))
                stats["incident_edges"] += 1

            # Create field-level edges
            if ann.get("field") and ann.get("tag") in ("CRITICAL", "SIDE_EFFECT", "DERIVES_FIELD"):
                field_id = f"FIELD:{ann['field']}"
                if field_id not in brain.G:
                    brain.add_node(field_id, "SAP_FIELD", ann["field"],
                                   layer="data", source="annotation")
                edge_type = "CLEARS_FIELD" if ann.get("tag") == "SIDE_EFFECT" else "DERIVES_FIELD"
                brain.add_edge(node_id, field_id, edge_type,
                               label=f"line {ann.get('line', '?')}",
                               evidence="annotation",
                               discovered_in=ann.get("session", ""))
                stats["field_edges"] += 1

    # ── Phase 2: Materialize metadata edges ──
    # Fix the gap: 4,030 ABAP nodes have tables_read/fms_called in metadata but zero graph edges
    meta_edges = 0
    for nid, ndata in brain.G.nodes(data=True):
        if ndata.get("type") != "ABAP_CLASS":
            continue
        metadata = ndata.get("metadata", {})

        for table in metadata.get("tables_read", []):
            tbl_id = f"SAP_TABLE:{table}"
            if tbl_id not in brain.G:
                brain.add_node(tbl_id, "SAP_TABLE", table,
                               layer="data", source="code_dependency")
            brain.add_edge(nid, tbl_id, "READS_TABLE",
                           evidence="code_metadata", confidence=0.9)
            meta_edges += 1

        for fm in metadata.get("fms_called", []):
            fm_id = f"FM:{fm}"
            if fm_id not in brain.G:
                brain.add_node(fm_id, "FUNCTION_MODULE", fm,
                               layer="code", source="code_dependency")
            brain.add_edge(nid, fm_id, "CALLS_FM",
                           evidence="code_metadata", confidence=0.9)
            meta_edges += 1

    print(f"  [annotations] {stats['annotated']} objects annotated, "
          f"{stats['not_found']} not found in graph, "
          f"{stats['incident_edges']} incident edges, "
          f"{stats['field_edges']} field edges, "
          f"{meta_edges} metadata edges materialized")
