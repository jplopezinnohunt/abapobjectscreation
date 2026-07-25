"""
extract_ddic_model.py  —  pull the REAL SAP data model from DDIC (not guessed)
=============================================================================
SAP always exposes its data model. This extracts it from the ABAP Dictionary via
RFC_READ_TABLE (the same path we already use) and writes domain_data_model.json:

  * DD03L  -> real PRIMARY KEYS (KEYFLAG='X', ordered by POSITION) + each field's
             CHECKTABLE (the master/value-help table it references).
  * DD08L  -> explicit foreign-key RELATIONSHIPS (header/item, text, etc.).
  * DD02L  -> table class (TRANSP/POOL/CLUSTER/VIEW) + delivery class.

This replaces hand-reverse-engineering of keys/relationships (the s079 error class:
FEBKO/FEBEP, REGUH PK, DORIGIN). DDIC is system-invariant CODE/metadata, so it can be
read from D01 OR P01 (CODE side of the CODE-vs-DATA rule).

ECC, NOT S/4: UNESCO is on ECC (EhP8). CDS views / OData $metadata associations are an
S/4HANA thing — ECC has NO delivered semantic content. Even SAP's Datasphere makes you
build the model BY HAND on ECC (ODP_SAPI extractors mostly lack PKs). So **classic DDIC
(DD03L.KEYFLAG + DD08L) is THE authoritative model source for us** — there is no shortcut.
Optional future enrichment: ROOSOURCE/ROOSFIELD (BW DataSource metadata) for coarse
reporting groupings. Do NOT chase CDS on ECC.

STATUS s079: ready. First run PENDING — P01 not active, D01 also blocked per user.
Run (when a system is active):  python extract_ddic_model.py [P01|D01]
"""
import os, sys, json, sqlite3

MCP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP_DIR))
from rfc_helpers import get_connection, rfc_read_paginated  # skill helpers, not forked

ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD_DB = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                       "p01_gold_master_data.db")
OUT = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "domain_data_model.json")


def gold_db_base_tables(db):
    """Real SAP table names we actually hold (strip our local prefixes/suffixes)."""
    import re
    raw = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    names = set()
    for t in raw:
        b = re.sub(r"^(d01_|p01_|v01_)", "", t, flags=re.I)
        b = re.sub(r"(_history|_fast|_full|_2024_2026|_2024|_2025|_2026|_usd|_dorigin|_8col_backup|_backup|_scenarios|_custom|_enrichment|_edit|_union)$", "", b, flags=re.I)
        if b and not b.startswith("_") and "sqlite" not in b.lower():
            names.add(b.upper())
    return sorted(names)


def infer_role(tabname, pk, checktables):
    """Best-effort role; flagged needs_validation. DDIC keys make this far better
    than column-name guessing, but the user still validates."""
    if tabname.startswith(("DD", "T0", "T1", "T2", "T3", "T4")) or len(pk) <= 2 and "MANDT" in pk:
        cfg = True
    n = len(pk)
    # header vs item heuristic refined later by DD08L parent links
    if any(k in pk for k in ("BUZEI", "POSNR", "EBELP", "ESNUM", "STEPCOUNT", "BUZEI")):
        return "item"
    if tabname in ("BKPF", "EKKO", "RBKP", "FEBKO", "VBAK"):
        return "header"
    if tabname.startswith("T") and n <= 3:
        return "config"
    return "transactional"


def main(system="P01"):
    db = sqlite3.connect(GOLD_DB)
    tables = gold_db_base_tables(db)
    print(f"{len(tables)} SAP base tables to model from DDIC ({system})")
    conn = get_connection(system)
    model = {"as_of_system": system, "source": "DDIC (DD03L/DD08L/DD02L)",
             "note": "PKs = DD03L.KEYFLAG; relationships = DD08L + DD03L.CHECKTABLE. "
                     "DDIC is system-invariant. role is heuristic -> validate.",
             "entities": {}}
    in_list = "TABNAME IN (" + ",".join(f"'{t}'" for t in tables) + ")"

    # DD02L: table class
    cls = {r[0]: {"tabclass": r[1], "contflag": r[2]} for r in
           rfc_read_paginated(conn, "DD02L", ["TABNAME", "TABCLASS", "CONTFLAG"], in_list)}
    # DD03L: fields + keys + checktable
    fields = rfc_read_paginated(conn, "DD03L",
              ["TABNAME", "FIELDNAME", "POSITION", "KEYFLAG", "ROLLNAME", "CHECKTABLE"], in_list)
    # DD08L: foreign-key relationships
    fks = rfc_read_paginated(conn, "DD08L",
              ["TABNAME", "FIELDNAME", "CHECKTABLE", "FRKART"],
              in_list + " AND AS4LOCAL = 'A'")

    # LDBN/LDBS: the STANDARD hierarchical (header->item) model — SAP's Logical
    # Databases, whose node tree adopts the foreign-key hierarchy of the tables.
    # Discover each table's own columns from DD03L first (no column guessing),
    # then pull all of them so we capture node + parent + table regardless of
    # the exact field names in this release.
    def _cols_of(meta_table):
        rows = rfc_read_paginated(conn, "DD03L", ["FIELDNAME", "POSITION"],
                                  f"TABNAME = '{meta_table}' AND AS4LOCAL = 'A'")
        flds = [f for f, _ in sorted(rows, key=lambda r: int(r[1] or 0))
                if f and not f.startswith(".")]
        return flds[:40]  # stay within RFC_READ_TABLE row-width

    ldb = {}
    for meta in ("LDBS", "LDBN"):
        try:
            cols = _cols_of(meta)
            data = rfc_read_paginated(conn, meta, cols, "")
            ldb[meta] = {"columns": cols, "rows": [list(r) for r in data]}
            print(f"  {meta}: {len(data)} rows, cols={cols}")
        except Exception as e:
            ldb[meta] = {"error": str(e)[:120]}
            print(f"  {meta}: extraction error -> {str(e)[:80]}")
    conn.close()

    per = {}
    for tab, fld, pos, key, roll, chk in fields:
        e = per.setdefault(tab, {"keys": [], "checktable_refs": {}})
        if key == "X" and fld not in ("MANDT", ".INCLUDE"):
            e["keys"].append((int(pos or 0), fld))
        if chk and chk not in ("", " "):
            e["checktable_refs"][fld] = chk
    rel = {}
    for tab, fld, chk, frkart in fks:
        rel.setdefault(tab, []).append({"field": fld, "references": chk, "fk_type": frkart})

    for t in tables:
        e = per.get(t, {"keys": [], "checktable_refs": {}})
        pk = [f for _, f in sorted(e["keys"])]
        model["entities"][t] = {
            "tabclass": cls.get(t, {}).get("tabclass", ""),
            "delivery_class": cls.get(t, {}).get("contflag", ""),
            "pk": pk,
            "pk_source": "DD03L.KEYFLAG" if pk else "NONE_FOUND",
            "checktable_refs": e["checktable_refs"],
            "fk_relationships": rel.get(t, []),
            "role_inferred": infer_role(t, pk, e["checktable_refs"]),
            "needs_validation": True,
        }

    # Logical Database hierarchy = SAP's standard header->item / parent-child model.
    # Stored raw (columns + rows) so we can map node->parent->table once the real
    # LDBN/LDBS columns are seen; this is the authoritative ECC hierarchy, not guessed.
    model["ldb_hierarchy"] = ldb
    model["ldb_note"] = ("LDBN=nodes, LDBS=directory/structure. node name = table name; "
                         "parent links give the standard header->item hierarchy. Walk LDBN per "
                         "our LDB (see our_logical_databases) to build the authoritative tree. "
                         "CAUTION: some LDBs put header+item at the same level (BRF: BKPF & BSEG) "
                         "- read the real tree, don't assume parent-child.")
    # interpretation guide: our domains -> standard LDBs (BRF/SDF/KDF/DDF/ADA/PNP...)
    ldb_map_path = os.path.join(os.path.dirname(__file__), "..", "logical_databases_map.json")
    if os.path.exists(ldb_map_path):
        model["our_logical_databases"] = json.load(open(ldb_map_path, encoding="utf-8"))

    json.dump(model, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"wrote {OUT}: {len(model['entities'])} entities (DDIC keys+FKs) + LDB hierarchy")
    db.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "P01")
