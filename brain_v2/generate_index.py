"""
Generate text object index — one markdown file per analyzed object.
Reads the built graph + annotations + claims to produce agent-readable .md files.

Usage: python -m brain_v2.generate_index
       OR: python brain_v2/generate_index.py
"""
import json, os, shutil
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
GRAPH_PATH = PROJECT_ROOT / "brain_v2" / "output" / "brain_v2_graph.json"
ANNOTATIONS_PATH = PROJECT_ROOT / "brain_v2" / "annotations" / "annotations.json"
CLAIMS_PATH = PROJECT_ROOT / "brain_v2" / "claims" / "claims.json"
INDEX_DIR = PROJECT_ROOT / "brain_v2" / "index"


def load_graph():
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_annotations():
    if ANNOTATIONS_PATH.exists():
        with open(ANNOTATIONS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_claims():
    if CLAIMS_PATH.exists():
        with open(CLAIMS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def build_edge_index(edges):
    """Build source→targets and target→sources lookup."""
    outgoing = defaultdict(list)  # source_id → [(target_id, edge_type, evidence, confidence)]
    incoming = defaultdict(list)  # target_id → [(source_id, edge_type, evidence, confidence)]
    for e in edges:
        s = e.get("source", "")
        t = e.get("target", "")
        etype = e.get("edge_type", "")
        evidence = e.get("metadata", {}).get("evidence", "")
        confidence = e.get("metadata", {}).get("confidence", "")
        outgoing[s].append((t, etype, evidence, confidence))
        incoming[t].append((s, etype, evidence, confidence))
    return outgoing, incoming


def select_important_objects(nodes, outgoing, incoming, annotations):
    """Select objects important enough to get their own index file."""
    important = set()
    node_map = {n["id"]: n for n in nodes}

    for n in nodes:
        nid = n["id"]
        ntype = n.get("type", "")
        name = n.get("name", "")

        # Has annotations
        if name in annotations or name.upper() in annotations:
            important.add(nid)
            continue

        # Referenced in an incident (check annotation incident links)
        for obj_id, obj_data in annotations.items():
            for ann in obj_data.get("annotations", []):
                for rel in ann.get("related", []):
                    if name.upper() in rel.upper():
                        important.add(nid)

        # Is a custom Y*/Z* code object with edges
        if ntype in ("ABAP_CLASS", "ABAP_REPORT", "FUNCTION_MODULE", "ENHANCEMENT"):
            if name.startswith(("Y", "Z", "y", "z")):
                edge_count = len(outgoing.get(nid, [])) + len(incoming.get(nid, []))
                if edge_count >= 3:
                    important.add(nid)

        # Is an extracted SAP_STANDARD file
        meta = n.get("metadata", {})
        if "SAP_STANDARD" in str(meta.get("path", "")):
            important.add(nid)

        # Hub table (>=3 incoming READS_TABLE edges)
        if ntype == "SAP_TABLE":
            reads_in = [e for e in incoming.get(nid, []) if e[1] == "READS_TABLE"]
            if len(reads_in) >= 3:
                important.add(nid)

    return important, node_map


def generate_object_md(nid, node, outgoing, incoming, annotations, claims):
    """Generate markdown content for a single object."""
    name = node.get("name", nid)
    ntype = node.get("type", "unknown")
    meta = node.get("metadata", {})
    domain = node.get("domain", "")
    layer = node.get("layer", "")
    path = meta.get("path", "")
    total_lines = meta.get("total_lines", "")

    lines = []
    lines.append(f"# {name}")
    parts = [f"**Type:** {ntype}"]
    if domain:
        parts.append(f"**Domain:** {domain}")
    if layer:
        parts.append(f"**Layer:** {layer}")
    lines.append(" | ".join(parts))
    if path:
        source_info = f"**Source:** {path}"
        if total_lines:
            source_info += f" ({total_lines} lines)"
        lines.append(source_info)
    lines.append("")

    # Dependencies: outgoing edges
    out_edges = outgoing.get(nid, [])
    reads_table = [(t, ev, conf) for t, et, ev, conf in out_edges if et == "READS_TABLE"]
    calls_fm = [(t, ev, conf) for t, et, ev, conf in out_edges if et == "CALLS_FM"]
    writes_table = [(t, ev, conf) for t, et, ev, conf in out_edges if et == "WRITES_TABLE"]
    other_out = [(t, et, ev, conf) for t, et, ev, conf in out_edges
                 if et not in ("READS_TABLE", "CALLS_FM", "WRITES_TABLE", "TRANSPORTS")]

    # Called by / read by: incoming edges
    in_edges = incoming.get(nid, [])
    called_by = [(s, et, ev, conf) for s, et, ev, conf in in_edges
                 if et in ("CALLS_FM", "READS_TABLE") and not s.startswith("TR:")]
    transported_by = [(s, ev, conf) for s, et, ev, conf in in_edges if et == "TRANSPORTS"]

    if reads_table or calls_fm or writes_table:
        lines.append("## Dependencies")

    if reads_table:
        lines.append("### Reads Tables")
        lines.append("| Table | Confidence | Evidence |")
        lines.append("|-------|-----------|----------|")
        for t, ev, conf in sorted(reads_table):
            tname = t.split(":")[-1] if ":" in t else t
            lines.append(f"| {tname} | {conf} | {ev} |")
        lines.append("")

    if calls_fm:
        lines.append("### Calls Functions")
        lines.append("| FM | Confidence | Evidence |")
        lines.append("|----|-----------|----------|")
        for t, ev, conf in sorted(calls_fm):
            tname = t.split(":")[-1] if ":" in t else t
            lines.append(f"| {tname} | {conf} | {ev} |")
        lines.append("")

    if writes_table:
        lines.append("### Writes Tables")
        lines.append("| Table | Confidence | Evidence |")
        lines.append("|-------|-----------|----------|")
        for t, ev, conf in sorted(writes_table):
            tname = t.split(":")[-1] if ":" in t else t
            lines.append(f"| {tname} | {conf} | {ev} |")
        lines.append("")

    if called_by:
        lines.append("### Called By / Read By")
        lines.append("| Source | Edge Type | Evidence |")
        lines.append("|--------|----------|----------|")
        for s, et, ev, conf in sorted(called_by):
            sname = s.split(":")[-1] if ":" in s else s
            lines.append(f"| {sname} | {et} | {ev} |")
        lines.append("")

    if other_out:
        lines.append("### Other Relationships")
        lines.append("| Target | Edge Type | Evidence |")
        lines.append("|--------|----------|----------|")
        for t, et, ev, conf in sorted(other_out)[:20]:
            tname = t.split(":")[-1] if ":" in t else t
            lines.append(f"| {tname} | {et} | {ev} |")
        lines.append("")

    # Annotations
    ann_key = name if name in annotations else name.upper() if name.upper() in annotations else None
    if ann_key:
        ann_data = annotations[ann_key]
        ann_list = ann_data.get("annotations", [])
        lines.append(f"## Annotations ({len(ann_list)})")
        for a in ann_list:
            tag = a.get("tag", "INFO")
            finding = a.get("finding", "")
            impact = a.get("impact", "")
            line_num = a.get("line", "")
            session = a.get("session", "")
            incident = a.get("incident", "")
            field = a.get("field", "")

            title = f"[{tag}]"
            if line_num:
                title += f" Line {line_num}"
            lines.append(f"### {title}")
            lines.append(finding)
            if impact:
                lines.append(f"**Impact:** {impact}")
            meta_parts = []
            if incident:
                meta_parts.append(f"**Incident:** {incident}")
            if session:
                meta_parts.append(f"**Session:** {session}")
            if field:
                meta_parts.append(f"**Field:** {field}")
            if meta_parts:
                lines.append(" | ".join(meta_parts))
            lines.append("")

    # Claims
    related_claims = [c for c in claims
                      if name in c.get("related_objects", [])
                      or name.upper() in [o.upper() for o in c.get("related_objects", [])]]
    if related_claims:
        lines.append("## Claims")
        for c in related_claims:
            tier = c.get("confidence", "?")
            claim = c.get("claim", "")
            ctype = c.get("claim_type", "")
            session = c.get("created_session", "")
            status = c.get("status", "active")
            prefix = f"[{tier}]"
            if status == "superseded":
                prefix += " ~~SUPERSEDED~~"
            lines.append(f"- **{prefix}** {claim} ({ctype}, session #{session})")
        lines.append("")

    # Transports
    if transported_by:
        lines.append(f"## Transports ({len(transported_by)})")
        for s, ev, conf in sorted(transported_by)[:10]:
            tr = s.split(":")[-1] if ":" in s else s
            lines.append(f"- {tr}")
        if len(transported_by) > 10:
            lines.append(f"- ... and {len(transported_by) - 10} more")
        lines.append("")

    return "\n".join(lines)


def generate_index():
    print("Loading graph...")
    graph = load_graph()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    print("Loading annotations...")
    annotations = load_annotations()

    print("Loading claims...")
    claims = load_claims()

    print("Building edge index...")
    outgoing, incoming = build_edge_index(edges)

    print("Selecting important objects...")
    important, node_map = select_important_objects(nodes, outgoing, incoming, annotations)
    print(f"  Selected {len(important)} objects for indexing")

    # Clean and recreate index directory
    if INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Generate index files
    generated = 0
    for nid in sorted(important):
        node = node_map.get(nid, {})
        name = node.get("name", nid.split(":")[-1])
        safe_name = name.replace("/", "_").replace("\\", "_").replace(":", "_")

        md = generate_object_md(nid, node, outgoing, incoming, annotations, claims)

        outpath = INDEX_DIR / f"{safe_name}.md"
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(md)
        generated += 1

    print(f"Generated {generated} index files in {INDEX_DIR}")
    return generated


if __name__ == "__main__":
    generate_index()
