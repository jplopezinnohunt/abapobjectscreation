"""
Brain v2 Knowledge Ingestor — Absorb ALL text artifacts into the graph.
Principle: if it has relationships, it's a node. Zero dead text.

Sources:
  - knowledge/domains/**/*.md (44 docs) → KNOWLEDGE_DOC nodes
  - knowledge/*.md (12 root docs) → KNOWLEDGE_DOC nodes
  - .agents/skills/*/SKILL.md (40 skills) → SKILL nodes
  - knowledge/session_retros/*.md (34 retros) → SESSION nodes
  - .agents/intelligence/PMO_BRAIN.md → extracts references

Each doc is parsed for references to SAP objects (tables, classes, FMs, processes)
and linked via DOCUMENTED_IN / SKILLED_IN / DISCOVERED_IN edges.
"""

import re
from pathlib import Path


# Patterns to detect SAP object references in text
RE_TABLE_REF = re.compile(r'\b([A-Z][A-Z0-9_]{2,20})\b')
RE_CLASS_REF = re.compile(r'\b([YZ]CL_\w{5,40})\b')
RE_FM_REF = re.compile(r'\b([YZ]_\w{5,40}|BAPI_\w{5,40}|RFC_\w{5,40})\b')
RE_TCODE_REF = re.compile(r'\b(SE\d{2}|SM\d{2}|SU\d{2}|ST\d{2}|F110|FB\d{2}|ME\d{2}N?|MIGO|MIRO|BNK_MONI|FEBAN|FF_5|SEGW|OBBH|OB28|GGB[014]|FMBB|FMX1)\b')
RE_PROCESS_REF = re.compile(r'\b(P2P|B2R|H2R|T2R|P2D|Payment_E2E|Bank_Statement)\b')

# Known SAP table names to filter false positives from RE_TABLE_REF
# We'll match against what's already in the brain instead of maintaining a list


def ingest_knowledge(brain, project_root: str):
    """Ingest all knowledge docs, skills, and session retros into the brain."""
    root = Path(project_root)
    stats = {'knowledge_nodes': 0, 'skill_nodes': 0, 'session_nodes': 0,
             'edges': 0}

    # ── Knowledge docs ──
    knowledge_dir = root / 'knowledge'
    if knowledge_dir.exists():
        for md_file in sorted(knowledge_dir.rglob('*.md')):
            if 'session_retros' in str(md_file) or 'session_plans' in str(md_file):
                continue  # Handle separately
            _ingest_knowledge_doc(brain, md_file, root, stats)

    # ── Skills ──
    skills_dir = root / '.agents' / 'skills'
    if skills_dir.exists():
        for skill_md in sorted(skills_dir.rglob('SKILL.md')):
            _ingest_skill(brain, skill_md, root, stats)

    # ── Session retros ──
    retros_dir = knowledge_dir / 'session_retros'
    if retros_dir.exists():
        for retro_md in sorted(retros_dir.glob('session_*_retro.md')):
            _ingest_session_retro(brain, retro_md, root, stats)

    # ── Intelligence docs ──
    intel_dir = root / '.agents' / 'intelligence'
    if intel_dir.exists():
        for md_file in sorted(intel_dir.glob('*.md')):
            _ingest_knowledge_doc(brain, md_file, root, stats, domain="GOVERNANCE")

    # ── HTML Companions (dashboards = knowledge checkpoints) ──
    _ingest_companions(brain, root, stats)

    return stats


def _ingest_companions(brain, project_root: Path, stats: dict):
    """Ingest HTML companion dashboards as KNOWLEDGE_DOC nodes using companions.json registry."""
    import json
    registry_path = project_root / 'companions' / 'companions.json'
    if not registry_path.exists():
        print(f"WARNING: Companion registry not found at {registry_path}")
        return

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    except Exception as e:
        print(f"ERROR reading companions.json: {e}")
        return

    for entry in registry:
        rel_path = entry.get('file')
        if not rel_path:
            continue

        html_file = project_root / rel_path
        if not html_file.exists():
            # If it's not at the exact path, check if it's placed directly under companions/
            alt_file = project_root / 'companions' / Path(rel_path).name
            if alt_file.exists():
                html_file = alt_file
                rel_path = f"companions/{alt_file.name}"

        name = html_file.stem
        node_id = f"COMPANION:{name}"

        title = entry.get('title', name)
        domain = entry.get('domain', 'GENERAL').upper()
        description = entry.get('description', '')
        version = entry.get('version', 'v1.0')
        last_updated = entry.get('last_updated', '')
        status = entry.get('status', 'active')
        keywords = entry.get('keywords', [])
        metrics = entry.get('metrics', [])

        try:
            size = html_file.stat().st_size if html_file.exists() else 0
        except Exception:
            size = 0

        metadata = {
            'path': rel_path,
            'size_bytes': size,
            'type': 'html_companion',
            'description': description,
            'version': version,
            'last_updated': last_updated,
            'status': status,
            'keywords': keywords,
            'metrics': metrics,
            'exists': html_file.exists()
        }

        brain.add_node(node_id, "KNOWLEDGE_DOC", title,
                       domain=domain, layer="process",
                       source="companion",
                       metadata=metadata,
                       tags=[domain.lower(), 'companion', 'dashboard'])
        stats['knowledge_nodes'] += 1

        # Scan text for reference linking if the file exists
        if html_file.exists():
            try:
                content = html_file.read_text(encoding='utf-8', errors='replace')
                # Only scan a reasonable portion for references
                scan_content = content[:50000] if len(content) > 50000 else content
                _create_reference_edges(brain, node_id, scan_content, stats,
                                        edge_type="DOCUMENTED_IN")
            except Exception as e:
                print(f"Error scanning {html_file}: {e}")


def _ingest_knowledge_doc(brain, md_file: Path, project_root: Path, stats: dict,
                          domain: str = None):
    """Ingest a single knowledge doc as a KNOWLEDGE_DOC node with reference edges."""
    try:
        content = md_file.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return

    rel_path = str(md_file.relative_to(project_root)).replace('\\', '/')
    name = md_file.stem
    node_id = f"DOC:{rel_path}"

    # Determine domain from path
    if not domain:
        parts = md_file.parts
        for p in parts:
            if p in ('PSM', 'HCM', 'FI', 'Transport_Intelligence', 'Payment',
                     'Procurement', 'PS', 'RE_FX', 'Output', 'BCM'):
                domain = p
                break
        if not domain:
            domain = "GENERAL"

    # Extract first heading as title
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else name

    brain.add_node(node_id, "KNOWLEDGE_DOC", title,
                   domain=domain, layer="process",
                   source="knowledge",
                   metadata={
                       'path': rel_path,
                       'size_bytes': len(content.encode('utf-8')),
                       'line_count': content.count('\n') + 1,
                   },
                   tags=[domain.lower(), 'knowledge'])
    stats['knowledge_nodes'] += 1

    # Find references to existing brain nodes and create DOCUMENTED_IN edges
    _create_reference_edges(brain, node_id, content, stats, edge_type="DOCUMENTED_IN")


def _ingest_skill(brain, skill_md: Path, project_root: Path, stats: dict):
    """Ingest a SKILL.md as a SKILL node with reference edges."""
    try:
        content = skill_md.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return

    rel_path = str(skill_md.relative_to(project_root)).replace('\\', '/')
    skill_name = skill_md.parent.name

    node_id = f"SKILL:{skill_name}"

    # Extract domain from content or name
    domain = "GENERAL"
    name_upper = skill_name.upper()
    if 'PAYMENT' in name_upper or 'BCM' in name_upper or 'BANK' in name_upper:
        domain = "FI"
    elif 'HCM' in name_upper or 'HR' in name_upper:
        domain = "HCM"
    elif 'PSM' in name_upper or 'FM' in name_upper:
        domain = "PSM"
    elif 'TRANSPORT' in name_upper or 'CTS' in name_upper:
        domain = "CTS"
    elif 'FIORI' in name_upper:
        domain = "HCM"
    elif 'EXTRACTION' in name_upper or 'DATA' in name_upper:
        domain = "DATA"
    elif 'INTEGRATION' in name_upper or 'INTERFACE' in name_upper:
        domain = "BASIS"

    # Extract first heading as title
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else skill_name

    brain.add_node(node_id, "SKILL", title,
                   domain=domain, layer="process",
                   source="skill",
                   metadata={
                       'path': rel_path,
                       'size_bytes': len(content.encode('utf-8')),
                       'line_count': content.count('\n') + 1,
                       'skill_name': skill_name,
                   },
                   tags=[domain.lower(), 'skill'])
    stats['skill_nodes'] += 1

    _create_reference_edges(brain, node_id, content, stats, edge_type="SKILLED_IN")


def _ingest_session_retro(brain, retro_md: Path, project_root: Path, stats: dict):
    """Ingest a session retro as a SESSION node."""
    try:
        content = retro_md.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return

    # Extract session number from filename
    session_match = re.search(r'session_(\d+)', retro_md.stem)
    if not session_match:
        return
    session_num = session_match.group(1)
    node_id = f"SESSION:{session_num}"

    # Extract date
    date_match = re.search(r'\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})', content)
    date = date_match.group(1) if date_match else ""

    # Extract first heading
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else f"Session #{session_num}"

    rel_path = str(retro_md.relative_to(project_root)).replace('\\', '/')

    brain.add_node(node_id, "KNOWLEDGE_DOC", title,
                   domain="SESSION", layer="process",
                   source="session_retro",
                   metadata={
                       'session': session_num,
                       'date': date,
                       'path': rel_path,
                       'line_count': content.count('\n') + 1,
                   },
                   tags=['session', 'retro'])
    stats['session_nodes'] += 1

    _create_reference_edges(brain, node_id, content, stats, edge_type="DISCOVERED_IN")


def _create_reference_edges(brain, doc_node_id: str, content: str, stats: dict,
                            edge_type: str = "DOCUMENTED_IN"):
    """Find references to existing brain nodes in text content and create edges."""
    linked = set()

    # Match classes (YCL_*, ZCL_*)
    for m in RE_CLASS_REF.finditer(content):
        cls_name = m.group(1).upper()
        cls_id = f"CLASS:{cls_name}"
        if brain.has_node(cls_id) and cls_id not in linked:
            brain.add_edge(doc_node_id, cls_id, edge_type,
                           evidence="text_reference", confidence=0.8,
                           discovered_in="040")
            stats['edges'] += 1
            linked.add(cls_id)

    # Match FMs
    for m in RE_FM_REF.finditer(content):
        fm_name = m.group(1).upper()
        fm_id = f"FM:{fm_name}"
        if brain.has_node(fm_id) and fm_id not in linked:
            brain.add_edge(doc_node_id, fm_id, edge_type,
                           evidence="text_reference", confidence=0.7,
                           discovered_in="040")
            stats['edges'] += 1
            linked.add(fm_id)

    # Match tables (only against known tables in brain to avoid false positives)
    for m in RE_TABLE_REF.finditer(content):
        tbl_name = m.group(1)
        tbl_id = f"SAP_TABLE:{tbl_name}"
        if brain.has_node(tbl_id) and tbl_id not in linked:
            brain.add_edge(doc_node_id, tbl_id, edge_type,
                           evidence="text_reference", confidence=0.6,
                           discovered_in="040")
            stats['edges'] += 1
            linked.add(tbl_id)

    # Match processes
    for m in RE_PROCESS_REF.finditer(content):
        proc = m.group(1)
        proc_id = f"PROCESS:{proc}"
        if brain.has_node(proc_id) and proc_id not in linked:
            brain.add_edge(doc_node_id, proc_id, edge_type,
                           evidence="text_reference", confidence=0.9,
                           discovered_in="040")
            stats['edges'] += 1
            linked.add(proc_id)

    # Match DMEE trees
    for tree_name in ['/CGI_XML_CT_UNESCO', '/CITI_XML_CT_UNESCO', '/SEPA_CT_UNESCO']:
        if tree_name in content:
            tree_id = f"DMEE:{tree_name}"
            if brain.has_node(tree_id) and tree_id not in linked:
                brain.add_edge(doc_node_id, tree_id, edge_type,
                               evidence="text_reference", confidence=0.9,
                               discovered_in="040")
                stats['edges'] += 1
                linked.add(tree_id)

    # Match skill references
    for m in re.finditer(r'`(sap_\w+)`|skills/(\w+)/SKILL', content):
        skill_name = m.group(1) or m.group(2)
        skill_id = f"SKILL:{skill_name}"
        if brain.has_node(skill_id) and skill_id not in linked:
            brain.add_edge(doc_node_id, skill_id, edge_type,
                           evidence="text_reference", confidence=0.8,
                           discovered_in="040")
            stats['edges'] += 1
            linked.add(skill_id)
