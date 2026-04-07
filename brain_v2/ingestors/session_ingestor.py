"""
Brain v2 Session Ingestor — Continuous enrichment from session retros.
Source: BRAIN_V2_ARCHITECTURE.md Design Principles #3, #7B

Every session close triggers `brain_v2 ingest-session N`.
Retro findings → new edges with evidence="session_NNN".
The brain grows without manual intervention.

Implements the Co-Evolutionary Loop (Agentic-KGR):
- Reads session retro → extracts findings/gaps
- Creates DISCOVERED_IN edges from findings to session node
- Creates NEEDS_INVESTIGATION edges for identified gaps
"""

import re
from pathlib import Path


def ingest_session(brain, project_root: str, session_number: int):
    """Ingest a session retro into the brain graph.

    Reads session_NNN_retro.md, extracts references to known objects,
    and creates edges linking discoveries to the session.
    """
    root = Path(project_root)
    stats = {'edges': 0, 'nodes': 0, 'findings': 0}

    # Find the retro file
    retro_path = _find_retro(root, session_number)
    if not retro_path:
        print(f"  No retro file found for session #{session_number:03d}")
        return stats

    text = retro_path.read_text(encoding='utf-8', errors='replace')

    # Create/update session node
    session_id = f"SESSION:{session_number:03d}"
    if not brain.has_node(session_id):
        brain.add_node(session_id, "KNOWLEDGE_DOC", f"Session #{session_number:03d}",
                       domain="SESSION", layer="process",
                       source="session_retro",
                       metadata={"file": str(retro_path)})
        stats['nodes'] += 1

    # Extract references to known brain objects
    _link_referenced_objects(brain, text, session_id, session_number, stats)

    print(f"  Session #{session_number:03d}: {stats['findings']} findings, "
          f"+{stats['nodes']} nodes, +{stats['edges']} edges")
    return stats


def _find_retro(root: Path, session_number: int) -> Path | None:
    """Find the session retro file."""
    # Try standard patterns
    patterns = [
        root / f"session_plans/session_{session_number:03d}_retro.md",
        root / f"session_{session_number:03d}_retro.md",
    ]
    # Also search in knowledge/sessions/ or similar
    for p in patterns:
        if p.exists():
            return p

    # Glob fallback
    for p in root.glob(f"**/session_{session_number:03d}_retro*"):
        return p
    for p in root.glob(f"**/*session*{session_number:03d}*retro*"):
        return p

    return None


def _link_referenced_objects(brain, text: str, session_id: str,
                              session_number: int, stats: dict):
    """Scan retro text for references to brain objects and create edges."""
    text_upper = text.upper()

    # Pattern: class names (YCL_*, ZCL_*, CL_HCMFAB_*)
    for m in re.finditer(r'\b([YZ]CL_[A-Z0-9_]+|CL_HCMFAB_[A-Z0-9_]+)\b', text_upper):
        cls_name = m.group(1)
        cls_id = f"CLASS:{cls_name}"
        if brain.has_node(cls_id):
            brain.add_edge(session_id, cls_id, "DISCOVERED_IN",
                           label=f"Referenced in session #{session_number:03d}",
                           evidence=f"session_{session_number:03d}",
                           confidence=0.8,
                           discovered_in=f"{session_number:03d}")
            stats['edges'] += 1
            stats['findings'] += 1

    # Pattern: SAP table names (known tables in brain)
    known_tables = {n.split(':')[1] for n in brain.nodes
                    if n.startswith('SAP_TABLE:') and len(n.split(':')[1]) >= 4}
    for table in known_tables:
        if table in text_upper:
            tbl_id = f"SAP_TABLE:{table}"
            brain.add_edge(session_id, tbl_id, "DISCOVERED_IN",
                           label=f"Referenced in session #{session_number:03d}",
                           evidence=f"session_{session_number:03d}",
                           confidence=0.7,
                           discovered_in=f"{session_number:03d}")
            stats['edges'] += 1
            stats['findings'] += 1

    # Pattern: function modules (Z_*, Y_*, RFC_*)
    for m in re.finditer(r'\b([ZY]_[A-Z0-9_]{3,}|RFC_[A-Z0-9_]+)\b', text_upper):
        fm_name = m.group(1)
        fm_id = f"FM:{fm_name}"
        if brain.has_node(fm_id):
            brain.add_edge(session_id, fm_id, "DISCOVERED_IN",
                           evidence=f"session_{session_number:03d}",
                           confidence=0.7,
                           discovered_in=f"{session_number:03d}")
            stats['edges'] += 1
            stats['findings'] += 1

    # Pattern: DMEE trees
    for m in re.finditer(r'(/CGI_XML_CT_UNESCO\w*|/CITI[_/]\w+|/SEPA_CT_UNESCO)', text_upper):
        tree_name = m.group(1)
        tree_id = f"DMEE:{tree_name}"
        if brain.has_node(tree_id):
            brain.add_edge(session_id, tree_id, "DISCOVERED_IN",
                           evidence=f"session_{session_number:03d}",
                           confidence=0.9,
                           discovered_in=f"{session_number:03d}")
            stats['edges'] += 1
            stats['findings'] += 1

    # Pattern: transport numbers (D01K9*)
    for m in re.finditer(r'\b(D01K9[A-Z0-9]+)\b', text_upper):
        tr_id = f"TR:{m.group(1)}"
        if brain.has_node(tr_id):
            brain.add_edge(session_id, tr_id, "DISCOVERED_IN",
                           evidence=f"session_{session_number:03d}",
                           confidence=0.9,
                           discovered_in=f"{session_number:03d}")
            stats['edges'] += 1
            stats['findings'] += 1
