"""
Brain v2 Transport Ingestor — CTS transports and their objects.
Source: BRAIN_V2_ARCHITECTURE.md Section B.2 (transport_objects), E Phase 2

Reads from Gold DB: cts_transports, cts_objects
"""

import sqlite3
from brain_v2.core.schema import CTS_OBJECT_TYPE_MAP


def ingest_transports(brain, db_path: str):
    """Link transports to the objects they carry."""
    conn = sqlite3.connect(db_path)
    stats = {'transport_nodes': 0, 'object_nodes': 0, 'edges': 0}

    # ── Detect column names (may be upper or lowercase) ──
    tr_cols = [r[1] for r in conn.execute("PRAGMA table_info(cts_transports)").fetchall()]
    obj_cols = [r[1] for r in conn.execute("PRAGMA table_info(cts_objects)").fetchall()]

    # Map to actual column names
    def _col(cols, name):
        for c in cols:
            if c.upper() == name.upper():
                return c
        return name

    # ── Transport nodes ──
    c_trkorr = _col(tr_cols, 'TRKORR')
    c_text = _col(tr_cols, 'AS4TEXT')
    c_status = _col(tr_cols, 'TRSTATUS')
    c_user = _col(tr_cols, 'AS4USER')
    c_date = _col(tr_cols, 'AS4DATE')

    try:
        rows = conn.execute(f"""
            SELECT {c_trkorr}, {c_text}, {c_status}, {c_user}, {c_date}
            FROM cts_transports
            WHERE {c_trkorr} IS NOT NULL
        """).fetchall()
    except Exception:
        rows = []

    for trkorr, text, status, user, date in rows:
        tr_id = f"TR:{trkorr}"
        brain.add_node(tr_id, "TRANSPORT", trkorr,
                       domain="CTS", layer="process",
                       source="gold_db",
                       metadata={
                           "description": text or "",
                           "status": status or "",
                           "user": user or "",
                           "date": date or "",
                       })
        stats['transport_nodes'] += 1

    # ── Transport -> Object edges ──
    c_otrkorr = _col(obj_cols, 'TRKORR')
    c_pgmid = _col(obj_cols, 'PGMID')
    c_object = _col(obj_cols, 'OBJECT')
    c_objname = _col(obj_cols, 'OBJ_NAME')
    # change_cat may exist instead of OBJFUNC
    c_objfunc = _col(obj_cols, 'OBJFUNC') if 'OBJFUNC' in [c.upper() for c in obj_cols] else None

    select_cols = f"{c_otrkorr}, {c_pgmid}, {c_object}, {c_objname}"
    if c_objfunc:
        select_cols += f", {c_objfunc}"

    try:
        rows = conn.execute(f"""
            SELECT {select_cols}
            FROM cts_objects
            WHERE {c_objname} IS NOT NULL AND {c_objname} != ''
        """).fetchall()
    except Exception:
        rows = []

    for row in rows:
        trkorr = row[0]
        pgmid = row[1]
        obj_type = row[2]
        obj_name = row[3]
        objfunc = row[4] if len(row) > 4 else ""

        tr_id = f"TR:{trkorr}"

        # Map CTS object type to graph node type
        node_type = CTS_OBJECT_TYPE_MAP.get(obj_type, "CODE_OBJECT")
        obj_name_clean = obj_name.strip()

        if node_type == "CODE_OBJECT":
            obj_id = f"OBJ:{obj_type}:{obj_name_clean}"
        else:
            obj_id = f"{node_type}:{obj_name_clean}"

        # Ensure object node exists (may already exist from code ingestor)
        if not brain.has_node(obj_id):
            brain.add_node(obj_id, node_type, obj_name_clean,
                           domain="CTS", layer="code",
                           source="gold_db",
                           metadata={"pgmid": pgmid or "", "object_type": obj_type or ""})
            stats['object_nodes'] += 1

        # Ensure transport node exists
        if not brain.has_node(tr_id):
            brain.add_node(tr_id, "TRANSPORT", trkorr,
                           domain="CTS", layer="process",
                           source="gold_db")
            stats['transport_nodes'] += 1

        # Edge: transport carries this object
        is_delete = objfunc == 'D' or (objfunc and 'Delete' in str(objfunc))
        brain.add_edge(tr_id, obj_id, "TRANSPORTS",
                       label=f"{pgmid}/{obj_type}/{obj_name_clean}",
                       evidence="config", confidence=1.0,
                       weight=1.2 if is_delete else 1.0,
                       discovered_in="040")
        stats['edges'] += 1

    conn.close()
    return stats
