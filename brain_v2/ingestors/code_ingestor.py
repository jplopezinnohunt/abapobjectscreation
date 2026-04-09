"""
Brain v2 Code Ingestor — Parse extracted ABAP code into graph nodes and edges.
Source: BRAIN_V2_ARCHITECTURE.md Section B.1, E Phase 1

Scans:
  - extracted_code/  (896 .abap files in class directories + standalone)
  - extracted_sap/   (246 .abap files in Fiori/HCM/PSM trees)
  - extracted_code/YWFI/  (FUGR/CLAS/PROG subdirectories)
"""

import re
from pathlib import Path

from brain_v2.parsers.abap_parser import ABAPDependencyParser


# Map directory name patterns to domains
DOMAIN_MAP = {
    'DMEE': 'FI',
    'YWFI': 'FI',
    'FM_BUDGETING': 'PSM',
    'FM_COCKPIT': 'PSM',
    'FM_MASTER_DATA': 'PSM',
    'BI_REPORTING': 'BI',
    'MM_PROCUREMENT': 'MM',
    'PS_PROJECTS': 'PS',
    'TECH_INTEGRATION': 'BASIS',
    'TV_TRAVEL': 'TV',
    'HCM': 'HCM',
    'PSM': 'PSM',
    'Benefits': 'HCM',
    'Offboarding': 'HCM',
}


def _guess_domain(filepath: Path) -> str:
    """Guess domain from file path."""
    parts = [p.name for p in filepath.parents]
    for part in parts:
        if part in DOMAIN_MAP:
            return DOMAIN_MAP[part]
    name = filepath.parent.name
    if name in DOMAIN_MAP:
        return DOMAIN_MAP[name]
    # Guess from class prefix
    stem = filepath.stem.upper()
    if 'HCMFAB' in stem or 'HCM' in stem or 'HR' in stem or 'BEN' in stem:
        return 'HCM'
    if 'DMEE' in stem or 'CGI' in stem:
        return 'FI'
    if 'CRP' in stem:
        return 'MM'
    if 'OFFBOARD' in stem:
        return 'HCM'
    if 'FIORI' in stem:
        return 'HCM'
    if 'FAMILY' in stem or 'SPSE' in stem:
        return 'HCM'
    return 'CUSTOM'


def _classify_class_name(name: str) -> str:
    """Determine node type from class directory name."""
    upper = name.upper()
    if upper.startswith(('ZCL_', 'YCL_', 'CL_')):
        return 'ABAP_CLASS'
    if upper.startswith('ZIF_'):
        return 'ABAP_CLASS'  # interface, treated as class-like
    return 'ABAP_CLASS'


def _scan_directory(brain, parser, directory: Path, stats: dict,
                    depth: int = 0, max_depth: int = 5):
    """Recursively scan a directory for ABAP code, applying the right ingestion strategy."""
    if depth > max_depth:
        return

    abap_files = list(directory.glob('*.abap'))
    sub_dirs = [d for d in sorted(directory.iterdir()) if d.is_dir()]

    if abap_files:
        # This directory has .abap files — decide how to ingest them
        class_groups = _group_files_by_class(abap_files)

        # Check if any real class grouping happened (multiple files share a prefix)
        has_real_groups = any(len(files) > 1 for files in class_groups.values())

        if len(class_groups) > 1 and has_real_groups:
            # Multiple classes sharing a flat directory (e.g., FI/DMEE/)
            for group_name, group_files in class_groups.items():
                _ingest_file_group_as_class(brain, parser, group_name,
                                            group_files, directory, stats)
        elif len(class_groups) > 1 and not has_real_groups:
            # Many single-file groups = standalone includes/reports (e.g., SAP_STANDARD/)
            _ingest_standalone_files(brain, parser, directory, stats)
        elif len(class_groups) == 1 and len(abap_files) > 1:
            # Single class directory (all files belong to one class)
            _ingest_class_dir(brain, parser, directory, stats)
        else:
            # Single file or mixed standalone files
            _ingest_standalone_files(brain, parser, directory, stats)

    # Always recurse into subdirectories (even if this dir had files)
    for sub_dir in sub_dirs:
        _scan_directory(brain, parser, sub_dir, stats, depth + 1, max_depth)


def ingest_code(brain, project_root: str):
    """Parse all extracted ABAP code and add to the brain graph."""
    parser = ABAPDependencyParser()
    root = Path(project_root)
    extracted_code = root / 'extracted_code'
    extracted_sap = root / 'extracted_sap'

    stats = {'classes': 0, 'standalone_files': 0, 'total_files': 0,
             'edges_added': 0, 'nodes_added': 0}

    # ── Phase A: Recursively scan extracted_code/ ──
    if extracted_code.exists():
        _scan_directory(brain, parser, extracted_code, stats, depth=0, max_depth=5)

    # ── Phase B: extracted_sap/ tree ──
    if extracted_sap.exists():
        for abap_file in sorted(extracted_sap.rglob('*.abap')):
            # Check if this file is in a class-like directory
            parent = abap_file.parent
            siblings = list(parent.glob('*.abap'))
            if len(siblings) > 1 and parent.name not in ('classes', 'reports', 'includes'):
                # Multiple .abap files in same dir = class directory
                # Only process once per directory
                if abap_file == siblings[0]:
                    _ingest_class_dir(brain, parser, parent, stats)
            else:
                _ingest_single_file(brain, parser, abap_file, stats)

    return stats


# ABAP class method suffixes — used to group flat files by class prefix
_METHOD_SUFFIXES = re.compile(
    r'_(CCDEF|CCIMP|CCMAC|CCAU|CO|CP|CU|CI|CM\d{3}|CPRI|CPRO|CPUB)$',
    re.IGNORECASE
)


def _group_files_by_class(abap_files: list) -> dict:
    """Group .abap files by class prefix when multiple classes share a directory.

    E.g., YCL_IDFI_CGI_DMEE_FR_CCDEF.abap -> class prefix = YCL_IDFI_CGI_DMEE_FR
          YCL_IDFI_CGI_DMEE_FR_CM001.abap -> same prefix
          YCL_IDFI_CGI_DMEE_UTIL_CM003.abap -> different prefix
    """
    groups = {}
    for f in abap_files:
        stem = f.stem.upper()
        m = _METHOD_SUFFIXES.search(stem)
        if m:
            prefix = stem[:m.start()]
        else:
            prefix = stem
        groups.setdefault(prefix, []).append(f)
    return groups


def _ingest_file_group_as_class(brain, parser, class_name: str,
                                 files: list, parent_dir: Path, stats: dict):
    """Ingest a group of files as a single ABAP class node."""
    domain = _guess_domain(parent_dir)
    node_type = _classify_class_name(class_name)

    merged = {
        'tables_read': set(), 'fields_read': set(), 'fms_called': set(),
        'tables_written': set(), 'inherits': set(), 'interfaces': set(),
        'is_badi_impl': False, 'class_refs': set(),
        'methods': {}, 'file_count': 0, 'total_lines': 0,
    }

    for abap_file in sorted(files):
        deps = parser.parse_file(abap_file)
        method_name = abap_file.stem
        merged['methods'][method_name] = deps
        merged['file_count'] += 1
        try:
            merged['total_lines'] += sum(
                1 for _ in open(abap_file, encoding='utf-8', errors='replace'))
        except Exception:
            pass
        for key in ['tables_read', 'fms_called', 'tables_written',
                    'inherits', 'interfaces', 'class_refs']:
            merged[key].update(deps[key])
        merged['fields_read'].update(tuple(f) for f in deps['fields_read'])
        if deps['is_badi_impl']:
            merged['is_badi_impl'] = True

    if merged['file_count'] == 0:
        return

    # Convert sets to sorted lists
    for key in ['tables_read', 'fms_called', 'tables_written',
                'inherits', 'interfaces', 'class_refs']:
        merged[key] = sorted(merged[key])
    merged['fields_read'] = sorted(merged['fields_read'])

    # Now ingest exactly like a class directory would
    class_id = f"CLASS:{class_name}"
    is_badi = merged['is_badi_impl'] or class_name.startswith(('YCL_IM_', 'ZCL_IM_'))

    brain.add_node(class_id, node_type, class_name,
                   domain=domain, layer="code", source="extracted_code",
                   metadata={
                       'file_count': merged['file_count'],
                       'total_lines': merged['total_lines'],
                       'method_count': len(merged['methods']),
                       'tables_read': merged['tables_read'],
                       'fms_called': merged['fms_called'],
                       'is_badi_impl': is_badi,
                       'path': str(parent_dir),
                   },
                   tags=[domain, node_type.lower()])
    stats['classes'] += 1
    stats['nodes_added'] += 1
    stats['total_files'] += merged['file_count']

    # Create all edges
    for table in merged['tables_read']:
        _ensure_table_node(brain, table, stats)
        brain.add_edge(class_id, f"SAP_TABLE:{table}", "READS_TABLE",
                       label=f"{class_name} reads {table}",
                       evidence="parsed", confidence=1.0, discovered_in="040")
        stats['edges_added'] += 1

    for table, field in merged['fields_read']:
        _ensure_field_node(brain, table, field, stats)
        brain.add_edge(class_id, f"FIELD:{table}.{field}", "READS_FIELD",
                       label=f"{class_name} reads {table}.{field}",
                       evidence="parsed", confidence=0.9, discovered_in="040")
        stats['edges_added'] += 1

    for fm in merged['fms_called']:
        _ensure_fm_node(brain, fm, stats)
        brain.add_edge(class_id, f"FM:{fm}", "CALLS_FM",
                       label=f"{class_name} calls {fm}",
                       evidence="parsed", confidence=1.0, discovered_in="040")
        stats['edges_added'] += 1

    for table in merged['tables_written']:
        _ensure_table_node(brain, table, stats)
        brain.add_edge(class_id, f"SAP_TABLE:{table}", "WRITES_TABLE",
                       label=f"{class_name} writes {table}",
                       evidence="parsed", confidence=1.0, discovered_in="040")
        stats['edges_added'] += 1

    for super_cls in merged['inherits']:
        super_id = f"CLASS:{super_cls}"
        if not brain.has_node(super_id):
            brain.add_node(super_id, "ABAP_CLASS", super_cls,
                           domain=domain, layer="code", source="inferred")
            stats['nodes_added'] += 1
        brain.add_edge(class_id, super_id, "INHERITS_FROM",
                       evidence="parsed", confidence=1.0, discovered_in="040")
        stats['edges_added'] += 1

    for intf in merged['interfaces']:
        intf_id = f"CLASS:{intf}"
        if not brain.has_node(intf_id):
            brain.add_node(intf_id, "ABAP_CLASS", intf,
                           domain=domain, layer="code", source="inferred",
                           metadata={'is_interface': True})
            stats['nodes_added'] += 1
        brain.add_edge(class_id, intf_id, "IMPLEMENTS_INTF",
                       evidence="parsed", confidence=1.0, discovered_in="040")
        stats['edges_added'] += 1

    if is_badi:
        badi_name = _infer_badi_name(class_name)
        if badi_name:
            badi_id = f"ENHANCEMENT:{badi_name}"
            if not brain.has_node(badi_id):
                brain.add_node(badi_id, "ENHANCEMENT", badi_name,
                               domain=domain, layer="code", source="inferred")
                stats['nodes_added'] += 1
            brain.add_edge(class_id, badi_id, "IMPLEMENTS_BADI",
                           evidence="parsed", confidence=0.7, discovered_in="040")
            stats['edges_added'] += 1


def _ingest_class_dir(brain, parser, class_dir: Path, stats: dict):
    """Ingest a class directory as a single ABAP_CLASS node + method nodes + edges."""
    class_name = class_dir.name.upper()
    node_type = _classify_class_name(class_name)
    domain = _guess_domain(class_dir)

    deps = parser.parse_class_directory(class_dir)

    if deps['file_count'] == 0:
        return

    class_id = f"CLASS:{class_name}"

    # Determine if BAdI impl from naming convention
    is_badi = deps['is_badi_impl'] or class_name.startswith(('YCL_IM_', 'ZCL_IM_'))

    brain.add_node(class_id, node_type, class_name,
                   domain=domain, layer="code",
                   source="extracted_code",
                   metadata={
                       'file_count': deps['file_count'],
                       'total_lines': deps['total_lines'],
                       'method_count': len(deps['methods']),
                       'tables_read': deps['tables_read'],
                       'fms_called': deps['fms_called'],
                       'is_badi_impl': is_badi,
                       'path': str(class_dir),
                   },
                   tags=[domain, node_type.lower()])
    stats['classes'] += 1
    stats['nodes_added'] += 1

    # ── Edges from class ──

    # READS_TABLE
    for table in deps['tables_read']:
        tbl_id = f"SAP_TABLE:{table}"
        _ensure_table_node(brain, table, stats)
        brain.add_edge(class_id, tbl_id, "READS_TABLE",
                       label=f"{class_name} reads {table}",
                       evidence="parsed", confidence=1.0,
                       discovered_in="040")
        stats['edges_added'] += 1

    # READS_FIELD
    for table, field in deps['fields_read']:
        field_id = f"FIELD:{table}.{field}"
        _ensure_field_node(brain, table, field, stats)
        brain.add_edge(class_id, field_id, "READS_FIELD",
                       label=f"{class_name} reads {table}.{field}",
                       evidence="parsed", confidence=0.9,
                       discovered_in="040")
        stats['edges_added'] += 1

    # CALLS_FM
    for fm in deps['fms_called']:
        fm_id = f"FM:{fm}"
        _ensure_fm_node(brain, fm, stats)
        brain.add_edge(class_id, fm_id, "CALLS_FM",
                       label=f"{class_name} calls {fm}",
                       evidence="parsed", confidence=1.0,
                       discovered_in="040")
        stats['edges_added'] += 1

    # WRITES_TABLE
    for table in deps['tables_written']:
        tbl_id = f"SAP_TABLE:{table}"
        _ensure_table_node(brain, table, stats)
        brain.add_edge(class_id, tbl_id, "WRITES_TABLE",
                       label=f"{class_name} writes {table}",
                       evidence="parsed", confidence=1.0,
                       discovered_in="040")
        stats['edges_added'] += 1

    # INHERITS_FROM
    for super_cls in deps['inherits']:
        super_id = f"CLASS:{super_cls}"
        if not brain.has_node(super_id):
            brain.add_node(super_id, "ABAP_CLASS", super_cls,
                           domain=domain, layer="code", source="inferred")
            stats['nodes_added'] += 1
        brain.add_edge(class_id, super_id, "INHERITS_FROM",
                       label=f"{class_name} inherits from {super_cls}",
                       evidence="parsed", confidence=1.0,
                       discovered_in="040")
        stats['edges_added'] += 1

    # IMPLEMENTS_INTF
    for intf in deps['interfaces']:
        intf_id = f"CLASS:{intf}"
        if not brain.has_node(intf_id):
            brain.add_node(intf_id, "ABAP_CLASS", intf,
                           domain=domain, layer="code", source="inferred",
                           metadata={'is_interface': True})
            stats['nodes_added'] += 1
        brain.add_edge(class_id, intf_id, "IMPLEMENTS_INTF",
                       label=f"{class_name} implements {intf}",
                       evidence="parsed", confidence=1.0,
                       discovered_in="040")
        stats['edges_added'] += 1

    # IMPLEMENTS_BADI (from naming convention)
    if is_badi:
        # Try to infer BAdI name from class name
        badi_name = _infer_badi_name(class_name)
        if badi_name:
            badi_id = f"ENHANCEMENT:{badi_name}"
            if not brain.has_node(badi_id):
                brain.add_node(badi_id, "ENHANCEMENT", badi_name,
                               domain=domain, layer="code", source="inferred")
                stats['nodes_added'] += 1
            brain.add_edge(class_id, badi_id, "IMPLEMENTS_BADI",
                           label=f"{class_name} implements BAdI {badi_name}",
                           evidence="parsed", confidence=0.7,
                           discovered_in="040")
            stats['edges_added'] += 1

    stats['total_files'] += deps['file_count']


def _ingest_standalone_files(brain, parser, directory: Path, stats: dict):
    """Ingest standalone .abap files (reports, includes) from a directory."""
    for abap_file in sorted(directory.glob('*.abap')):
        _ingest_single_file(brain, parser, abap_file, stats)


def _ingest_single_file(brain, parser, abap_file: Path, stats: dict):
    """Ingest a single standalone ABAP file as a report/enhancement node."""
    deps = parser.parse_file(abap_file)
    name = abap_file.stem.upper()
    domain = _guess_domain(abap_file)

    # Determine type from name
    if name.endswith('_RPY') or name.startswith('ZX'):
        node_type = 'ENHANCEMENT'
    else:
        node_type = 'ABAP_REPORT'

    node_id = f"{node_type}:{name}"

    try:
        line_count = sum(1 for _ in open(abap_file, encoding='utf-8', errors='replace'))
    except Exception:
        line_count = 0

    brain.add_node(node_id, node_type, name,
                   domain=domain, layer="code",
                   source="extracted_code",
                   metadata={
                       'tables_read': deps['tables_read'],
                       'fms_called': deps['fms_called'],
                       'line_count': line_count,
                       'path': str(abap_file),
                   },
                   tags=[domain, node_type.lower()])
    stats['standalone_files'] += 1
    stats['nodes_added'] += 1
    stats['total_files'] += 1

    # Same edge creation as classes
    for table in deps['tables_read']:
        tbl_id = f"SAP_TABLE:{table}"
        _ensure_table_node(brain, table, stats)
        brain.add_edge(node_id, tbl_id, "READS_TABLE",
                       evidence="parsed", confidence=1.0, discovered_in="040")
        stats['edges_added'] += 1

    for table, field in deps['fields_read']:
        field_id = f"FIELD:{table}.{field}"
        _ensure_field_node(brain, table, field, stats)
        brain.add_edge(node_id, field_id, "READS_FIELD",
                       evidence="parsed", confidence=0.9, discovered_in="040")
        stats['edges_added'] += 1

    for fm in deps['fms_called']:
        fm_id = f"FM:{fm}"
        _ensure_fm_node(brain, fm, stats)
        brain.add_edge(node_id, fm_id, "CALLS_FM",
                       evidence="parsed", confidence=1.0, discovered_in="040")
        stats['edges_added'] += 1

    for table in deps['tables_written']:
        tbl_id = f"SAP_TABLE:{table}"
        _ensure_table_node(brain, table, stats)
        brain.add_edge(node_id, tbl_id, "WRITES_TABLE",
                       evidence="parsed", confidence=1.0, discovered_in="040")
        stats['edges_added'] += 1


# ── Helper functions for ensuring referenced nodes exist ──

def _ensure_table_node(brain, table_name: str, stats: dict):
    tbl_id = f"SAP_TABLE:{table_name}"
    if not brain.has_node(tbl_id):
        brain.add_node(tbl_id, "SAP_TABLE", table_name,
                       domain="DATA_MODEL", layer="data",
                       source="inferred_from_code")
        stats['nodes_added'] += 1


def _ensure_field_node(brain, table: str, field: str, stats: dict):
    field_id = f"FIELD:{table}.{field}"
    if not brain.has_node(field_id):
        brain.add_node(field_id, "TABLE_FIELD", f"{table}.{field}",
                       domain="DATA_MODEL", layer="data",
                       source="inferred_from_code",
                       metadata={'table': table, 'field': field})
        stats['nodes_added'] += 1
    # Also ensure parent table exists
    _ensure_table_node(brain, table, stats)


def _ensure_fm_node(brain, fm_name: str, stats: dict):
    fm_id = f"FM:{fm_name}"
    if not brain.has_node(fm_id):
        brain.add_node(fm_id, "FUNCTION_MODULE", fm_name,
                       domain="CUSTOM" if fm_name.startswith(('Z', 'Y')) else "SAP_STANDARD",
                       layer="code",
                       source="inferred_from_code")
        stats['nodes_added'] += 1


def _infer_badi_name(class_name: str) -> str:
    """Try to infer BAdI name from implementation class name."""
    # Known mappings
    known = {
        'YCL_IDFI_CGI_DMEE_FR': 'FI_CGI_DMEE_EXIT_W_BADI',
        'YCL_IDFI_CGI_DMEE_FALLBACK': 'FI_CGI_DMEE_EXIT_W_BADI',
        'YCL_IDFI_CGI_DMEE_UTIL': 'FI_CGI_DMEE_EXIT_W_BADI',
        'YCL_IM_PERSINFOUI_0006': 'HCMFAB_PERSINFOUI_0006',
        'YCL_IM_PERSINFO_0006': 'HCMFAB_PERSINFO_0006',
    }
    if class_name in known:
        return known[class_name]
    # Convention: YCL_IM_XXXX -> BAdI XXXX
    if class_name.startswith(('YCL_IM_', 'ZCL_IM_')):
        return class_name[7:]  # Strip YCL_IM_ or ZCL_IM_
    return ""
