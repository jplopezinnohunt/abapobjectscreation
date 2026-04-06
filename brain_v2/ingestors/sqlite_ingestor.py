"""
Brain v2 SQLite Ingestor — Table fields, join map, and master data from Gold DB.
Source: BRAIN_V2_ARCHITECTURE.md Section A.2 (data objects), A.3 (join edges)
"""

import sqlite3


# Proven join relationships (from Golden Query and skill docs)
JOIN_MAP = [
    ("FMIFIIT", "KNBELNR",  "BKPF", "BELNR",   "FM-to-FI bridge (doc number)"),
    ("FMIFIIT", "KNGJAHR",  "BKPF", "GJAHR",    "FM-to-FI bridge (fiscal year)"),
    ("FMIFIIT", "BUKRS",    "BKPF", "BUKRS",    "FM-to-FI bridge (company code)"),
    ("FMIFIIT", "KNBUZEI",  "BSIS", "BUZEI",    "FM-to-FI line-level bridge"),
    ("FMIFIIT", "FONDS",    "FMFINCODE", "FINCODE", "Fund master lookup"),
    ("FMIFIIT", "FISTL",    "FMFCTR", "FICTR",  "Fund center master lookup"),
    ("FMIFIIT", "OBJNRZ",   "PRPS", "OBJNR",    "WBS element link (85.9% coverage)"),
    ("PRPS",    "PSPHI",    "PROJ", "PSPNR",     "WBS -> Project definition"),
    ("EKKO",    "EBELN",    "EKPO", "EBELN",     "PO header -> PO items"),
    ("EKPO",    "EBELN",    "EKBE", "EBELN",     "PO item -> PO history"),
    ("EKPO",    "EBELN",    "ESSR", "EBELN",     "PO item -> Entry sheets"),
    ("ESSR",    "PACKNO",   "ESLL", "PACKNO",    "Entry sheet -> Service lines"),
    ("RBKP",    "BELNR",    "RSEG", "BELNR",     "Invoice header -> Invoice items"),
    ("REGUH",   "VBLNR",    "BKPF", "BELNR",    "Payment -> FI document"),
    ("T042A",   "ZBUKR",    "T042Z", "ZBUKR",    "Pay method -> DMEE tree (co code)"),
    ("T042A",   "ZLSCH",    "T042Z", "ZLSCH",    "Pay method -> DMEE tree (method)"),
    ("TBTCO",   "JOBNAME",  "TBTCP", "JOBNAME",  "Job header -> Job steps"),
    ("TBTCO",   "JOBCOUNT", "TBTCP", "JOBCOUNT", "Job header -> Job steps (count)"),
]


def ingest_sqlite_schema(brain, db_path: str):
    """Add table nodes, field nodes, and join edges from Gold DB schema."""
    conn = sqlite3.connect(db_path)
    stats = {'table_nodes': 0, 'field_nodes': 0, 'join_edges': 0, 'field_map_edges': 0}

    # ── Get all tables in Gold DB ──
    tables = [row[0] for row in
              conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    for table_name in tables:
        table_upper = table_name.upper()
        tbl_id = f"SAP_TABLE:{table_upper}"

        # Get column info
        try:
            columns = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        except Exception:
            continue

        # Get row count (approximate for large tables)
        try:
            row_count = conn.execute(f"SELECT COUNT(*) FROM '{table_name}'").fetchone()[0]
        except Exception:
            row_count = 0

        # Add/update table node
        brain.add_node(tbl_id, "SAP_TABLE", table_upper,
                       domain="DATA_MODEL", layer="data",
                       source="gold_db",
                       metadata={
                           "column_count": len(columns),
                           "row_count": row_count,
                           "columns": [c[1] for c in columns],
                       })
        stats['table_nodes'] += 1

        # Add field nodes for each column
        for col in columns:
            col_name = col[1].upper()
            field_id = f"FIELD:{table_upper}.{col_name}"
            if not brain.has_node(field_id):
                brain.add_node(field_id, "TABLE_FIELD", f"{table_upper}.{col_name}",
                               domain="DATA_MODEL", layer="data",
                               source="gold_db",
                               metadata={
                                   "table": table_upper,
                                   "field": col_name,
                                   "data_type": col[2] or "",
                                   "nullable": not col[3],
                                   "pk": bool(col[5]),
                               })
                stats['field_nodes'] += 1

    # ── Add proven join relationships ──
    for src_tbl, src_fld, tgt_tbl, tgt_fld, description in JOIN_MAP:
        src_field_id = f"FIELD:{src_tbl}.{src_fld}"
        tgt_field_id = f"FIELD:{tgt_tbl}.{tgt_fld}"
        src_tbl_id = f"SAP_TABLE:{src_tbl}"
        tgt_tbl_id = f"SAP_TABLE:{tgt_tbl}"

        # Table-level join
        if brain.has_node(src_tbl_id) and brain.has_node(tgt_tbl_id):
            brain.add_edge(src_tbl_id, tgt_tbl_id, "JOINS_VIA",
                           label=f"{src_tbl}.{src_fld} = {tgt_tbl}.{tgt_fld}: {description}",
                           evidence="proven", confidence=1.0,
                           discovered_in="040")
            stats['join_edges'] += 1

        # Field-level mapping
        if brain.has_node(src_field_id) and brain.has_node(tgt_field_id):
            brain.add_edge(src_field_id, tgt_field_id, "FIELD_MAPS_TO",
                           label=f"{src_tbl}.{src_fld} -> {tgt_tbl}.{tgt_fld}",
                           evidence="proven", confidence=1.0,
                           discovered_in="040")
            stats['field_map_edges'] += 1

    conn.close()
    return stats


def ingest_job_intelligence(brain, db_path: str):
    """Link background jobs to programs they execute."""
    conn = sqlite3.connect(db_path)
    stats = {'nodes': 0, 'edges': 0}

    try:
        # Fast query: just get distinct programs from tbtcp (no expensive join)
        rows = conn.execute("""
            SELECT PROGNAME, COUNT(*) as exec_count
            FROM tbtcp
            WHERE PROGNAME IS NOT NULL AND PROGNAME != ''
            GROUP BY PROGNAME
            ORDER BY exec_count DESC
        """).fetchall()
    except Exception:
        conn.close()
        return stats

    for progname, exec_count in rows:
        prog_id = f"JOB_PROG:{progname}"
        brain.add_node(prog_id, "JOB_DEFINITION", progname,
                       domain="BASIS", layer="process",
                       source="gold_db",
                       metadata={"exec_count": exec_count})
        stats['nodes'] += 1

        # Link to known ABAP reports
        report_id = f"ABAP_REPORT:{progname}"
        if brain.has_node(report_id):
            brain.add_edge(prog_id, report_id, "RUNS_PROGRAM",
                           evidence="config", confidence=1.0,
                           discovered_in="040")
            stats['edges'] += 1

        # Also check class naming
        class_id = f"CLASS:{progname}"
        if brain.has_node(class_id):
            brain.add_edge(prog_id, class_id, "RUNS_PROGRAM",
                           evidence="config", confidence=1.0,
                           discovered_in="040")
            stats['edges'] += 1

    conn.close()
    return stats
