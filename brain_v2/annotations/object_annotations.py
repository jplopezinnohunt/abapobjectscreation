"""
object_annotations.py — Make objects smarter across sessions.

Every analyzed program, table, or config object accumulates annotations.
Annotations survive brain rebuilds. They are the learnings FROM analysis,
tagged back TO the objects.

Usage:
    from brain_v2.annotations.object_annotations import annotate, get_annotations, search_annotations

    # Add a learning to an object
    annotate("LHRTSF01", line=852, tag="CRITICAL",
             finding="IF bukst=bukrs — only fills GSBER for same-company",
             impact="Intercompany counterpart lines get no GSBER",
             session="#048", incident="INC-000006073")

    # Query what we know about an object
    get_annotations("LHRTSF01")

    # Find all CRITICAL annotations
    search_annotations(tag="CRITICAL")

    # Find all objects related to an incident
    search_annotations(incident="INC-000006073")
"""

import json
import os
from datetime import datetime

ANNOTATIONS_FILE = os.path.join(os.path.dirname(__file__), "annotations.json")


def _load():
    if os.path.exists(ANNOTATIONS_FILE):
        with open(ANNOTATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(data):
    with open(ANNOTATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def annotate(object_id, tag, finding, impact=None, line=None,
             session=None, incident=None, field=None, related=None):
    """Add an annotation to an object. Object gets smarter."""
    data = _load()
    if object_id not in data:
        data[object_id] = {"annotations": [], "first_seen": datetime.now().isoformat()}

    annotation = {
        "tag": tag,
        "finding": finding,
        "timestamp": datetime.now().isoformat(),
    }
    if impact:
        annotation["impact"] = impact
    if line:
        annotation["line"] = line
    if session:
        annotation["session"] = session
    if incident:
        annotation["incident"] = incident
    if field:
        annotation["field"] = field
    if related:
        annotation["related"] = related

    data[object_id]["annotations"].append(annotation)
    data[object_id]["last_updated"] = datetime.now().isoformat()
    _save(data)
    return len(data[object_id]["annotations"])


def get_annotations(object_id):
    """Get all annotations for an object."""
    data = _load()
    return data.get(object_id, {}).get("annotations", [])


def get_object(object_id):
    """Get full object record with all annotations."""
    data = _load()
    return data.get(object_id)


def search_annotations(tag=None, incident=None, session=None, keyword=None):
    """Search across all objects for matching annotations."""
    data = _load()
    results = []
    for obj_id, obj in data.items():
        for ann in obj.get("annotations", []):
            match = True
            if tag and ann.get("tag") != tag:
                match = False
            if incident and ann.get("incident") != incident:
                match = False
            if session and ann.get("session") != session:
                match = False
            if keyword and keyword.lower() not in ann.get("finding", "").lower():
                match = False
            if match:
                results.append({"object": obj_id, **ann})
    return results


def list_objects():
    """List all annotated objects with annotation count."""
    data = _load()
    return {k: len(v.get("annotations", [])) for k, v in data.items()}


def stats():
    """Summary statistics."""
    data = _load()
    total_objects = len(data)
    total_annotations = sum(len(v.get("annotations", [])) for v in data.values())
    tags = {}
    incidents = set()
    for obj in data.values():
        for ann in obj.get("annotations", []):
            t = ann.get("tag", "UNKNOWN")
            tags[t] = tags.get(t, 0) + 1
            if ann.get("incident"):
                incidents.add(ann["incident"])
    return {
        "objects": total_objects,
        "annotations": total_annotations,
        "tags": tags,
        "incidents": list(incidents),
    }
