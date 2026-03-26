"""
sap_brain.py — UNESCO SAP Living Knowledge Brain
=================================================

A connected knowledge graph that links ALL project knowledge sources:

  SOURCE 1: extracted_sap/       → Code objects (BSP Apps, Classes, Tables, Reports)
  SOURCE 2: SQLite gold DB        → Data entities (Fund Areas, Funds, Fund Centers, Transports)
  SOURCE 3: knowledge/**/*.md     → Domain knowledge documents
  SOURCE 4: .agents/skills/       → Agent skill documents
  SOURCE 5: Expert seed docs      → doc_reference.txt, YRGGBS00, etc.

Living Knowledge Principle: The brain continuously evolves — it is NOT a static snapshot.
Every session adds new nodes and edges. Every extraction enriches the graph.

Usage:
    python sap_brain.py --build               # Build from ALL 5 sources
    python sap_brain.py --build --html        # Build + generate visual graph
    python sap_brain.py --stats               # Show graph statistics
    python sap_brain.py --query offboarding   # Find all related nodes
    python sap_brain.py --domain HCM          # Show full HCM picture
    python sap_brain.py --node ZHROFFBOARDING # Show all connections of one node
    python sap_brain.py --html                # Regenerate HTML from saved brain
"""

import json
import re
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent
BASE_DIR     = PROJECT_ROOT / "extracted_sap"
BRAIN_FILE   = PROJECT_ROOT / ".agents/intelligence/sap_brain.json"


# ══════════════════════════════════════════════════════════════════════════════
#  NODE AND EDGE TYPES
# ══════════════════════════════════════════════════════════════════════════════

NODE_TYPES = {
    # — Code objects (Source 1) —
    "BSP_APP":      "Fiori/BSP Application (UI layer)",
    "CLASS":        "ABAP Class (business logic)",
    "SERVICE":      "OData/Gateway Service",
    "TABLE":        "ABAP Database Table",
    "FUNCTION":     "Function Module/Group",
    "REPORT":       "ABAP Report/Program",
    "INTERFACE":    "RFC/IDoc Interface",
    "DOMAIN":       "Business Domain (HCM, PSM, ...)",
    "APP_AREA":     "Application Area (Offboarding, Benefits, ...)",
    # — Data entities (Source 2) —
    "FUND_AREA":    "FM Area (budget control scope)",
    "FUND":         "Individual Fund (donor/project)",
    "FUND_CENTER":  "Funds Center (responsible unit)",
    "VALIDATION":   "OB28 Validation Rule",
    "SUBSTITUTION": "OBBH Substitution Rule",
    "TRANSPORT":    "CTS Transport Order",
    # — Knowledge (Sources 3-5) —
    "SKILL":        "Agent Skill Document",
    "KNOWLEDGE_DOC":"Domain Knowledge Markdown",
    "DOCUMENT":     "Expert Seed Document",
    # — Processes (coordinator level) —
    "PROCESS":      "End-to-End Business Process",
    # — Operations (Sources 7-8: Jobs & Interfaces) —
    "JOB_PROGRAM":  "Background Job Program (SM37)",
    "RFC_DEST":     "RFC Destination (SM59)",
    "SAP_SYSTEM":   "SAP System Instance",
}

EDGE_TYPES = {
    # — Code relationships —
    "BELONGS_TO":    "Object belongs to domain/area",
    "IMPLEMENTS":    "Class implements service DPC/MPC",
    "CONSUMES":      "BSP app consumes service",
    "EXTENDS":       "Class extends another class",
    "CALLS":         "Object calls function/RFC",
    "READS_TABLE":   "Code reads from table",
    "WRITES_TABLE":  "Code writes to table",
    "SHARES_CODE":   "Shared utility dependency",
    "RELATED_BDC":   "Associated batch input session",
    # — Data relationships —
    "HAS_FUND":      "FM area contains fund",
    "POSTS_TO":      "Code posts financial document to",
    "VALIDATES_FM":  "Validation rule validates FM area",
    "USES_FILTER":   "Object uses filter configuration",
    # — Knowledge relationships —
    "DOCUMENTED_IN": "Object documented in knowledge doc",
    "SKILLED_IN":    "Skill covers this object/pattern",
    "TRANSPORTED_IN":"Object was included in transport",
    "PART_OF":       "Entity is part of a business process",
    "BRIDGES_TO":    "Cross-domain bridge connection",
    # — Data model join relationships —
    "JOINS_VIA":     "Table joins to another table via foreign key",
    # — Operational relationships —
    "RUNS_PROGRAM":  "Job executes this program",
    "CONNECTS_TO":   "RFC destination connects to system",
    "INTEGRATES":    "Integration link between systems/programs",
}


# ══════════════════════════════════════════════════════════════════════════════
#  BRAIN DATA STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════

class SAPBrain:
    def __init__(self):
        self.nodes = {}   # id → {id, type, name, domain, area, path, metadata, tags, added}
        self.edges = []   # [{from, to, type, label}]
        self._edge_set = set()  # dedup

    def add_node(self, node_id, node_type, name, domain="", area="",
                 path="", metadata=None, tags=None):
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id":       node_id,
                "type":     node_type,
                "name":     name,
                "domain":   domain,
                "area":     area,
                "path":     str(path),
                "metadata": metadata or {},
                "tags":     tags or [],
                "added":    datetime.now().isoformat()[:10],
            }

    def add_edge(self, from_id, to_id, edge_type, label=""):
        key = (from_id, to_id, edge_type)
        if key not in self._edge_set:
            self._edge_set.add(key)
            self.edges.append({
                "from":  from_id,
                "to":    to_id,
                "type":  edge_type,
                "label": label or edge_type,
            })

    def save(self):
        BRAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "meta": {
                "built":    datetime.now().isoformat(),
                "nodes":    len(self.nodes),
                "edges":    len(self.edges),
                "base_dir": str(BASE_DIR),
                "sources":  6,
            },
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
        }
        BRAIN_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  [BRAIN] Saved: {len(self.nodes)} nodes, {len(self.edges)} edges -> {BRAIN_FILE}")
        return data

    @classmethod
    def load(cls):
        brain = cls()
        if BRAIN_FILE.exists():
            data = json.loads(BRAIN_FILE.read_text(encoding="utf-8"))
            for n in data.get("nodes", []):
                brain.nodes[n["id"]] = n
            brain.edges = data.get("edges", [])
            brain._edge_set = {(e["from"], e["to"], e["type"]) for e in brain.edges}
        return brain


# ══════════════════════════════════════════════════════════════════════════════
#  BUILD ORCHESTRATOR — 8 SOURCES
# ══════════════════════════════════════════════════════════════════════════════

def build_brain():
    brain = SAPBrain()

    print(f"\n  +---------------------------------------------+")
    print(f"  |  UNESCO SAP LIVING KNOWLEDGE BRAIN - BUILD  |")
    print(f"  +---------------------------------------------+")

    print(f"\n  [SOURCE 1/8] Code objects (extracted_sap/) ...")
    _ingest_code_objects(brain)
    c1 = len(brain.nodes)
    print(f"  -> {c1} nodes after code objects")

    print(f"\n  [SOURCE 2/8] SQLite data entities ...")
    _ingest_sqlite_data(brain)
    c2 = len(brain.nodes)
    print(f"  -> {c2 - c1} new nodes from SQLite  (total: {c2})")

    print(f"\n  [SOURCE 3/8] Knowledge documents (knowledge/) ...")
    _ingest_knowledge_docs(brain)
    c3 = len(brain.nodes)
    print(f"  -> {c3 - c2} new nodes from knowledge docs  (total: {c3})")

    print(f"\n  [SOURCE 4/8] Agent skills (.agents/skills/) ...")
    _ingest_skills(brain)
    c4 = len(brain.nodes)
    print(f"  -> {c4 - c3} new nodes from skills  (total: {c4})")

    print(f"\n  [SOURCE 5/8] Expert seed documents ...")
    _ingest_expert_seeds(brain)
    c5 = len(brain.nodes)
    print(f"  -> {c5 - c4} new nodes from expert seeds  (total: {c5})")

    print(f"\n  [SOURCE 6/8] UNESCO Process Model (coordinator layer) ...")
    _ingest_process_model(brain)
    c6 = len(brain.nodes)
    print(f"  -> {c6 - c5} new nodes from process model  (total: {c6})")

    print(f"\n  [SOURCE 7/8] Background Job Programs (TBTCP/TBTCO) ...")
    _ingest_job_programs(brain)
    c7 = len(brain.nodes)
    print(f"  -> {c7 - c6} new nodes from job programs  (total: {c7})")

    print(f"\n  [SOURCE 8/8] RFC Destinations & System Map (RFCDES) ...")
    _ingest_rfc_destinations(brain)
    c8 = len(brain.nodes)
    print(f"  -> {c8 - c7} new nodes from RFC/systems  (total: {c8})")

    return brain


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 1: CODE OBJECTS (extracted_sap/)
# ══════════════════════════════════════════════════════════════════════════════

def _ingest_code_objects(brain):
    if not BASE_DIR.exists():
        print(f"  [SOURCE 1] Base dir not found: {BASE_DIR} - skipping")
        return

    for domain_dir in sorted(BASE_DIR.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name.startswith('.'):
            continue
        domain = domain_dir.name  # HCM, PSM, _shared

        brain.add_node(domain, "DOMAIN", domain, domain=domain, tags=["domain"])

        for area_or_cat in sorted(domain_dir.iterdir()):
            if not area_or_cat.is_dir():
                continue
            category = area_or_cat.name  # Fiori_Apps, Reports, Interfaces

            if category == "Fiori_Apps":
                for app_area_dir in sorted(area_or_cat.iterdir()):
                    if not app_area_dir.is_dir():
                        continue
                    app_area = app_area_dir.name  # Offboarding, Benefits, _shared

                    area_id = f"{domain}_{app_area}"
                    brain.add_node(area_id, "APP_AREA", f"{domain} / {app_area}",
                                   domain=domain, area=app_area, path=app_area_dir)
                    brain.add_edge(area_id, domain, "BELONGS_TO")

                    # BSP apps
                    bsp_dir = app_area_dir / "bsp"
                    if bsp_dir.exists():
                        for bsp_app in sorted(bsp_dir.iterdir()):
                            if not bsp_app.is_dir():
                                continue
                            bsp_id = bsp_app.name.replace("BSP_", "")
                            manifest = _read_manifest(bsp_app)
                            service_url = manifest.get("service", "")
                            brain.add_node(
                                bsp_id, "BSP_APP", bsp_id,
                                domain=domain, area=app_area, path=bsp_app,
                                metadata={
                                    "files":   len(list(bsp_app.rglob("*.*"))),
                                    "service": service_url,
                                    "manifest": manifest,
                                },
                                tags=["fiori", "ui5", domain.lower(), app_area.lower()]
                            )
                            brain.add_edge(bsp_id, area_id, "BELONGS_TO")

                            svc_name = _extract_service_name(service_url)
                            if svc_name:
                                if svc_name not in brain.nodes:
                                    brain.add_node(svc_name, "SERVICE", svc_name,
                                                   domain=domain, area=app_area,
                                                   tags=["odata", "service", domain.lower()])
                                brain.add_edge(bsp_id, svc_name, "CONSUMES", f"OData: {svc_name}")

                    # Classes
                    classes_dir = app_area_dir / "classes"
                    if classes_dir.exists():
                        for cls_dir in sorted(classes_dir.iterdir()):
                            if not cls_dir.is_dir():
                                continue
                            cls_id = cls_dir.name
                            cls_source = _read_class_source(cls_dir)
                            used_tables = _extract_table_refs(cls_source)
                            called_fms  = _extract_fm_calls(cls_source)
                            inherits    = _extract_inheritance(cls_source)

                            brain.add_node(
                                cls_id, "CLASS", cls_id,
                                domain=domain, area=app_area, path=cls_dir,
                                metadata={
                                    "tables":   used_tables[:10],
                                    "calls":    called_fms[:10],
                                    "inherits": inherits,
                                    "is_dpc":   "_DPC" in cls_id,
                                    "is_mpc":   "_MPC" in cls_id,
                                },
                                tags=["class", domain.lower(), app_area.lower()]
                            )
                            brain.add_edge(cls_id, area_id, "BELONGS_TO")

                            if "_DPC" in cls_id or "_MPC" in cls_id:
                                svc_guess = _guess_service_from_class(cls_id)
                                if svc_guess:
                                    if svc_guess not in brain.nodes:
                                        brain.add_node(svc_guess, "SERVICE", svc_guess,
                                                       domain=domain, area=app_area,
                                                       tags=["odata", "service", domain.lower()])
                                    brain.add_edge(cls_id, svc_guess, "IMPLEMENTS", "OData provider")

                            for tbl in used_tables[:5]:
                                tbl_id = f"TABLE_{tbl}"
                                if tbl_id not in brain.nodes:
                                    brain.add_node(tbl_id, "TABLE", tbl,
                                                   domain="_shared", tags=["table"])
                                brain.add_edge(cls_id, tbl_id, "READS_TABLE")

                            if inherits and inherits != cls_id:
                                brain.add_edge(cls_id, inherits, "EXTENDS")

            elif category == "Reports":
                for report_dir in sorted(area_or_cat.iterdir()):
                    if not report_dir.is_dir():
                        continue
                    r_id = report_dir.name
                    brain.add_node(r_id, "REPORT", r_id, domain=domain,
                                   path=report_dir, tags=["report", domain.lower()])
                    brain.add_edge(r_id, domain, "BELONGS_TO")

            elif category == "Interfaces":
                for iface_dir in sorted(area_or_cat.iterdir()):
                    if not iface_dir.is_dir():
                        continue
                    i_id = iface_dir.name
                    brain.add_node(i_id, "INTERFACE", i_id, domain=domain,
                                   path=iface_dir, tags=["interface", domain.lower()])
                    brain.add_edge(i_id, domain, "BELONGS_TO")


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 2: SQLITE DATA ENTITIES
# ══════════════════════════════════════════════════════════════════════════════

def _ingest_sqlite_data(brain):
    # Single canonical path — no stale copies allowed
    candidate_paths = [
        PROJECT_ROOT / "Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db",
    ]

    db_path = None
    for p in candidate_paths:
        if Path(p).exists():
            db_path = Path(p)
            break

    if not db_path:
        print(f"  [SOURCE 2] p01_gold_master_data.db not found - skipping data entities")
        return

    size_mb = db_path.stat().st_size // 1024 // 1024
    print(f"  [SOURCE 2] SQLite: {db_path.name} ({size_mb} MB)")

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except Exception:
        conn = sqlite3.connect(str(db_path))

    try:
        available = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        print(f"  [SOURCE 2] Tables: {sorted(available)}")

        # Fund Areas + Funds — NO LIMIT (full graph, filter in HTML only)
        # Real schema: funds(FIKRS, FINCODE, TYPE, ERFDAT, ERFNAME)
        if "funds" in available:
            try:
                # Fund areas with aggregate metadata
                area_rows = conn.execute(
                    "SELECT FIKRS, COUNT(*) as cnt FROM funds "
                    "WHERE FIKRS IS NOT NULL AND FIKRS != '' "
                    "GROUP BY FIKRS"
                ).fetchall()
                for (fikrs, cnt) in area_rows:
                    if fikrs and str(fikrs).strip():
                        node_id = f"FA_{fikrs}"
                        brain.add_node(node_id, "FUND_AREA", f"FM Area {fikrs}",
                                       domain="PSM",
                                       metadata={"fikrs": str(fikrs), "fund_count": cnt},
                                       tags=["fm_area", "psm", "budget"])
                        if "PSM" in brain.nodes:
                            brain.add_edge(node_id, "PSM", "BELONGS_TO")
                print(f"  [SOURCE 2] Fund Areas (FIKRS): {len(area_rows)}")
            except Exception as e:
                print(f"  [SOURCE 2] FIKRS query failed: {e}")

            try:
                # ALL funds — no LIMIT
                rows = conn.execute(
                    "SELECT FIKRS, FINCODE, TYPE FROM funds "
                    "WHERE FINCODE IS NOT NULL AND FINCODE != ''"
                ).fetchall()
                for (fikrs, fincode, ftype) in rows:
                    if fincode and str(fincode).strip():
                        fund_id = f"FUND_{fincode}"
                        brain.add_node(fund_id, "FUND", f"Fund {fincode}",
                                       domain="PSM",
                                       metadata={"fincode": str(fincode), "fikrs": str(fikrs),
                                                  "type": str(ftype or "")},
                                       tags=["fund", "psm", "donor"])
                        fa_id = f"FA_{fikrs}"
                        if fa_id in brain.nodes:
                            brain.add_edge(fa_id, fund_id, "HAS_FUND")
                print(f"  [SOURCE 2] Funds (FINCODE): {len(rows)}")
            except Exception as e:
                print(f"  [SOURCE 2] FINCODE query failed: {e}")

            # Enrich fund areas with FMIFIIT aggregates (total amount by area)
            if "fmifiit_full" in available:
                try:
                    agg_rows = conn.execute(
                        "SELECT FIKRS, COUNT(*) as doc_count, "
                        "COUNT(DISTINCT FONDS) as active_funds, "
                        "COUNT(DISTINCT FISTL) as active_fctrs "
                        "FROM fmifiit_full "
                        "WHERE FIKRS IS NOT NULL GROUP BY FIKRS"
                    ).fetchall()
                    for (fikrs, doc_count, active_funds, active_fctrs) in agg_rows:
                        fa_id = f"FA_{fikrs}"
                        if fa_id in brain.nodes:
                            brain.nodes[fa_id]["metadata"].update({
                                "fmifiit_docs": doc_count,
                                "active_funds": active_funds,
                                "active_fund_centers": active_fctrs,
                            })
                    print(f"  [SOURCE 2] Fund Area aggregates enriched: {len(agg_rows)}")
                except Exception as e:
                    print(f"  [SOURCE 2] FMIFIIT aggregates failed: {e}")

        # Fallback: enrich fund areas from fmifiit_full if funds table not present
        elif "fmifiit_full" in available:
            try:
                rows = conn.execute(
                    "SELECT DISTINCT FIKRS FROM fmifiit_full "
                    "WHERE FIKRS IS NOT NULL AND FIKRS != ''"
                ).fetchall()
                for (fikrs,) in rows:
                    if fikrs and str(fikrs).strip():
                        node_id = f"FA_{fikrs}"
                        brain.add_node(node_id, "FUND_AREA", f"FM Area {fikrs}",
                                       domain="PSM",
                                       metadata={"fikrs": str(fikrs)},
                                       tags=["fm_area", "psm", "budget"])
                        if "PSM" in brain.nodes:
                            brain.add_edge(node_id, "PSM", "BELONGS_TO")
                fund_rows = conn.execute(
                    "SELECT DISTINCT FIKRS, FONDS FROM fmifiit_full "
                    "WHERE FONDS IS NOT NULL AND FONDS != ''"
                ).fetchall()
                for (fikrs, fonds) in fund_rows:
                    if fonds:
                        fund_id = f"FUND_{fonds}"
                        brain.add_node(fund_id, "FUND", f"Fund {fonds}",
                                       domain="PSM",
                                       metadata={"fonds": str(fonds)},
                                       tags=["fund", "psm"])
                        fa_id = f"FA_{fikrs}"
                        if fa_id in brain.nodes:
                            brain.add_edge(fa_id, fund_id, "HAS_FUND")
                print(f"  [SOURCE 2] Fund Areas: {len(rows)}, Funds: {len(fund_rows)}")
            except Exception as e:
                print(f"  [SOURCE 2] fmifiit_full fund query failed: {e}")

        # Fund Centers
        for fc_table in ["fund_centers", "fmfctr", "fmfctr_full"]:
            if fc_table in available:
                try:
                    cols = [c[1] for c in conn.execute(
                        f"PRAGMA table_info('{fc_table}')"
                    ).fetchall()]
                    fictr_col = next(
                        (c for c in cols if "fictr" in c.lower() or "fctr" in c.lower()), None
                    )
                    fikrs_col = next((c for c in cols if "fikrs" in c.lower()), None)
                    if fictr_col:
                        sel = f"SELECT DISTINCT {fictr_col}"
                        if fikrs_col:
                            sel += f", {fikrs_col}"
                        rows = conn.execute(f"{sel} FROM {fc_table}").fetchall()
                        for row in rows:
                            fictr = str(row[0]).strip() if row[0] else ""
                            fikrs = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                            if fictr:
                                fc_id = f"FC_{fictr}"
                                brain.add_node(fc_id, "FUND_CENTER", f"Fund Center {fictr}",
                                               domain="PSM",
                                               metadata={"fictr": fictr, "fikrs": fikrs},
                                               tags=["fund_center", "psm", "budget"])
                                fa_id = f"FA_{fikrs}"
                                if fa_id in brain.nodes:
                                    brain.add_edge(fa_id, fc_id, "BELONGS_TO")
                        print(f"  [SOURCE 2] Fund Centers from {fc_table}: {len(rows)}")
                        break
                except Exception as e:
                    print(f"  [SOURCE 2] Fund Centers on {fc_table} failed: {e}")

        # CTS Transports
        for cts_table in ["cts_transports", "e070", "cts_objects"]:
            if cts_table in available:
                try:
                    cols = [c[1] for c in conn.execute(
                        f"PRAGMA table_info('{cts_table}')"
                    ).fetchall()]
                    trkorr_col = next(
                        (c for c in cols if "trkorr" in c.lower() or c.upper() == "TRKORR"), None
                    )
                    if not trkorr_col:
                        continue
                    rows = conn.execute(
                        f"SELECT DISTINCT {trkorr_col} FROM {cts_table} "
                        f"WHERE {trkorr_col} IS NOT NULL"
                    ).fetchall()
                    for (trkorr,) in rows:
                        if trkorr and str(trkorr).strip():
                            t_id = f"TR_{trkorr}"
                            brain.add_node(t_id, "TRANSPORT", str(trkorr),
                                           domain="CTS",
                                           metadata={"trkorr": str(trkorr),
                                                     "source_table": cts_table},
                                           tags=["transport", "cts"])
                    print(f"  [SOURCE 2] Transports from {cts_table}: {len(rows)}")
                    break
                except Exception as e:
                    print(f"  [SOURCE 2] CTS on {cts_table} failed: {e}")

        # ── JOINS_VIA: Table-to-table foreign key relationships ────────────
        # These model the SQLite data model so the brain can traverse joins.
        _TABLE_JOINS = [
            # (from_table, to_table, join_key, label)
            ("FMIFIIT",  "FMFCT",   "FONDS=FINCODE",        "FM doc → Fund master"),
            ("FMIFIIT",  "FMFCTR",  "FISTL=FICTR",          "FM doc → Fund center"),
            ("FMIFIIT",  "BKPF",    "KNBELNR=BELNR",        "FM doc → FI document header"),
            ("PROJ",     "PRPS",    "PSPNR=PSPHI",          "Project → WBS elements"),
            ("E071",     "E070",    "TRKORR=TRKORR",         "CTS object → Transport order"),
            ("FMIFIIT",  "YTFM_WRTTP_GR", "WRTTP=WRTTP",    "FM doc → Value type filter"),
            ("FMIFIIT",  "FMAVCT",  "FONDS+FISTL+FIKRS",    "FM doc → Availability control"),
            ("FMIFIIT",  "FMBDT",   "FONDS+FISTL+FIKRS",    "FM doc → Budget entry"),
        ]

        join_count = 0
        for from_tbl, to_tbl, join_key, label in _TABLE_JOINS:
            from_id = f"TABLE_{from_tbl}"
            to_id   = f"TABLE_{to_tbl}"
            # Ensure table nodes exist
            if from_id not in brain.nodes:
                brain.add_node(from_id, "TABLE", from_tbl,
                               domain="DATA_MODEL", tags=["table", "sap"])
            if to_id not in brain.nodes:
                brain.add_node(to_id, "TABLE", to_tbl,
                               domain="DATA_MODEL", tags=["table", "sap"])
            brain.add_edge(from_id, to_id, "JOINS_VIA", f"{join_key} — {label}")
            join_count += 1

        print(f"  [SOURCE 2] Table join edges (JOINS_VIA): {join_count}")

    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 3: KNOWLEDGE DOCUMENTS (knowledge/**/*.md)
# ══════════════════════════════════════════════════════════════════════════════

_SAP_TABLES_PATTERN = (
    r'\b(FMIFIIT|FMFCTR|FMBDT|FMAVCT|FMFINCODE|FMCIT|'
    r'PROJ|PRPS|BKPF|BSEG|EKKO|EKPO|'
    r'PA0002|PA0021|PA0001|T001|COEP|COOI|RPSCO)\b'
)


def _ingest_knowledge_docs(brain):
    knowledge_dir = PROJECT_ROOT / "knowledge"
    if not knowledge_dir.exists():
        print(f"  [SOURCE 3] knowledge/ dir not found - skipping")
        return

    md_files = list(knowledge_dir.rglob("*.md"))
    print(f"  [SOURCE 3] Found {len(md_files)} markdown files")

    for md_file in sorted(md_files):
        try:
            rel   = md_file.relative_to(knowledge_dir)
            parts = rel.parts

            domain = "_shared"
            if len(parts) >= 3 and parts[0] == "domains":
                # domains/{DOMAIN}/... — parts[1] is a real subdirectory name
                domain = parts[1]
            elif len(parts) >= 1 and parts[0] == "session_retros":
                domain = "META"

            doc_id = f"DOC_{md_file.stem.upper().replace('-', '_').replace(' ', '_')}"
            title  = md_file.stem.replace("_", " ").replace("-", " ").title()

            brain.add_node(
                doc_id, "KNOWLEDGE_DOC", title,
                domain=domain, path=md_file,
                metadata={"filename": md_file.name,
                          "path": str(rel).replace("\\", "/")},
                tags=["knowledge", "markdown", domain.lower()]
            )

            if domain in brain.nodes:
                brain.add_edge(doc_id, domain, "BELONGS_TO")

            try:
                content = md_file.read_text(encoding="utf-8", errors="replace")
                for m in re.finditer(r'\b([YZ]CL_[A-Z0-9_]{3,40})\b', content):
                    cls_id = m.group(1)
                    if cls_id in brain.nodes:
                        brain.add_edge(doc_id, cls_id, "DOCUMENTED_IN")
                for m in re.finditer(_SAP_TABLES_PATTERN, content):
                    tbl_id = f"TABLE_{m.group(1)}"
                    if tbl_id in brain.nodes:
                        brain.add_edge(doc_id, tbl_id, "DOCUMENTED_IN")
            except Exception:
                pass

        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 4: AGENT SKILLS (.agents/skills/*/SKILL.md)
# ══════════════════════════════════════════════════════════════════════════════

_SKILL_LAYER_MAP = {
    "webgui":          "L1",
    "native_desktop":  "L1",
    "debugging":       "L1",
    "data_extract":    "L2",
    "automated_test":  "L2",
    "expert_core":     "L3",
    "filter_registry": "L3",
    "adt_api":         "L4",
    "reverse_eng":     "L4",
    "enhancement":     "L4",
    "transport":       "L5",
    "fiori":           "L6",
    "segw":            "L6",
    "html_build":      "L7",
    "parallel":        "L7",
}


def _skill_layer(skill_name):
    name_lower = skill_name.lower()
    for keyword, layer in _SKILL_LAYER_MAP.items():
        if keyword in name_lower:
            return layer
    return "Meta"


def _ingest_skills(brain):
    skills_dir = PROJECT_ROOT / ".agents/skills"
    if not skills_dir.exists():
        print(f"  [SOURCE 4] .agents/skills/ dir not found - skipping")
        return

    skill_files = list(skills_dir.glob("*/SKILL.md"))
    print(f"  [SOURCE 4] Found {len(skill_files)} skill files")

    for skill_file in sorted(skill_files):
        skill_name = skill_file.parent.name
        skill_id   = f"SKILL_{skill_name.upper().replace('-', '_')}"
        layer      = _skill_layer(skill_name)
        title      = skill_name.replace("_", " ").replace("-", " ").title()

        brain.add_node(
            skill_id, "SKILL", title,
            domain=layer, path=skill_file,
            metadata={"layer": layer, "skill_name": skill_name},
            tags=["skill", "agent", layer.lower()]
        )

        try:
            content = skill_file.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r'\b([YZ]CL_[A-Z0-9_]{3,40})\b', content):
                cls_id = m.group(1)
                if cls_id in brain.nodes:
                    brain.add_edge(skill_id, cls_id, "SKILLED_IN")
            for m in re.finditer(
                r'\b(RFC_READ_TABLE|FMIFIIT|FMFCTR|FMBDT|BKPF|BSEG|EKKO|EKPO)\b', content
            ):
                tbl_id = f"TABLE_{m.group(1)}"
                if tbl_id in brain.nodes:
                    brain.add_edge(skill_id, tbl_id, "SKILLED_IN")
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 5: EXPERT SEED DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════

_EXPERT_SEEDS = [
    ("doc_reference.txt",                     "SAP Transport Intelligence Reference",  "CTS"),
    ("doc_supplement.txt",                    "SAP Transport Modules Supplement",       "CTS"),
    ("YRGGBS00_SOURCE.txt",                   "YRGGBS00 BAdI Substitution Source",      "FI"),
    ("YCL_FI_ACCOUNT_SUBST_BL_METHODS.txt",   "FI Account Substitution BL Methods",    "FI"),
    ("YCL_FI_ACCOUNT_SUBST_BL_CI.txt",        "FI Account Substitution BL CI",         "FI"),
    ("YCL_FI_ACCOUNT_SUBST_BL_CP.txt",        "FI Account Substitution BL CP",         "FI"),
    ("YCL_FI_ACCOUNT_SUBST_BL_CU.txt",        "FI Account Substitution BL CU",         "FI"),
    ("YCL_FI_ACCOUNT_SUBST_READ_METHODS.txt", "FI Account Substitution Read Methods",  "FI"),
    ("YCL_FI_ACCOUNT_SUBST_READ_CU.txt",      "FI Account Substitution Read CU",       "FI"),
    ("YFI_ACCOUNT_SUBSTITUTION.txt",          "YFI Account Substitution Program",       "FI"),
]


def _ingest_process_model(brain):
    """Source 6: UNESCO Business Process Model — coordinator-level nodes.

    5 core processes × their domain connections × key entity bridges.
    This makes the brain answer PROCESS-level questions, not just object questions.
    """
    # ── 5 Core Processes ──────────────────────────────────────────────────────
    processes = [
        ("PROC_B2R", "Budget-to-Report",    "PSM",   ["PSM", "FI"],
         ["FMIFIIT→budgets approved→committed→actual→FI Doc"]),
        ("PROC_H2R", "Hire-to-Retire",      "HCM",   ["HCM", "FI", "PSM"],
         ["Hire→Infotype→Payroll→GL Posting→FM Posting"]),
        ("PROC_P2P", "Procure-to-Pay",      "MM",    ["MM", "FI", "PSM"],
         ["PO→Goods Receipt→Invoice→Payment→FM Commitment cleared"]),
        ("PROC_T2R", "Travel-to-Claim",     "Travel",["Travel", "FI", "PSM"],
         ["Trip Request→Advance→Expense Claim→FM Posting"]),
        ("PROC_P2D", "Project-to-Close",    "PS",    ["PS", "PSM", "FI"],
         ["WBS Created→Budget Assigned→Spending→Project Close"]),
    ]

    for proc_id, proc_name, primary_domain, domains, flow in processes:
        brain.add_node(
            proc_id, "PROCESS", proc_name,
            domain=primary_domain,
            metadata={"domains": domains, "flow": flow},
            tags=["process", "coordinator", primary_domain.lower()]
        )
        # Link process to its primary domain
        if primary_domain in brain.nodes:
            brain.add_edge(proc_id, primary_domain, "BELONGS_TO")
        # Link process to all touching domains
        for d in domains:
            if d in brain.nodes and d != primary_domain:
                brain.add_edge(proc_id, d, "BRIDGES_TO")

    # ── Link processes to existing data entities ───────────────────────────
    # B2R touches all funds and fund areas
    if "PROC_B2R" in brain.nodes:
        for node_id, node in brain.nodes.items():
            if node["type"] == "FUND_AREA":
                brain.add_edge("PROC_B2R", node_id, "PART_OF")
            elif node["type"] == "FUND" and node_id.startswith("FUND_AAF"):
                # Link a sample of donor funds (extrabudgetary)
                brain.add_edge("PROC_B2R", node_id, "PART_OF")

    # H2R links to HCM domain areas
    if "PROC_H2R" in brain.nodes:
        for node_id, node in brain.nodes.items():
            if node["type"] == "APP_AREA" and node["domain"] == "HCM":
                brain.add_edge("PROC_H2R", node_id, "PART_OF")
            elif node["type"] == "BSP_APP" and "HCM" in node.get("domain", ""):
                brain.add_edge("PROC_H2R", node_id, "PART_OF")

    # ── Link coordinator skill to all processes ────────────────────────────
    coord_skill = "SKILL_COORDINATOR"
    if coord_skill not in brain.nodes:
        coord_path = PROJECT_ROOT / ".agents/skills/coordinator/SKILL.md"
        brain.add_node(coord_skill, "SKILL", "UNESCO SAP Intelligence Coordinator",
                       domain="Meta", path=coord_path,
                       metadata={"layer": "Coordinator", "skill_name": "coordinator"},
                       tags=["skill", "coordinator", "meta"])
    for proc_id, _, _, _, _ in processes:
        brain.add_edge(coord_skill, proc_id, "SKILLED_IN")

    # ── Link domain agent skills to their processes ────────────────────────
    domain_skill_map = {
        "SKILL_PSM_DOMAIN_AGENT": ["PROC_B2R", "PROC_P2D"],
        "SKILL_HCM_DOMAIN_AGENT": ["PROC_H2R"],
        "SKILL_FI_DOMAIN_AGENT":  ["PROC_B2R", "PROC_H2R", "PROC_P2P", "PROC_T2R"],
    }
    for skill_id, proc_list in domain_skill_map.items():
        if skill_id in brain.nodes:
            for proc_id in proc_list:
                if proc_id in brain.nodes:
                    brain.add_edge(skill_id, proc_id, "SKILLED_IN")


def _ingest_expert_seeds(brain):
    seeds_dir = PROJECT_ROOT / "Zagentexecution/mcp-backend-server-python"
    ingested  = 0
    seen_ids  = set()

    for filename, title, domain in _EXPERT_SEEDS:
        path = seeds_dir / filename
        if not path.exists():
            continue
        doc_id = f"SEED_{Path(filename).stem.upper().replace('-', '_').replace('.', '_')}"
        if doc_id in seen_ids or doc_id in brain.nodes:
            continue
        seen_ids.add(doc_id)

        size_kb = path.stat().st_size // 1024
        brain.add_node(
            doc_id, "DOCUMENT", title,
            domain=domain, path=path,
            metadata={"filename": filename, "size_kb": size_kb},
            tags=["expert_seed", "document", domain.lower()]
        )
        ingested += 1

        # Link FI seeds to related class/report nodes
        if "SUBST" in filename.upper() or "YRGGBS00" in filename.upper():
            for ref_id in ["YRGGBS00", "YCL_FI_ACCOUNT_SUBST_BL", "YCL_FI_ACCOUNT_SUBST_READ"]:
                if ref_id in brain.nodes:
                    brain.add_edge(doc_id, ref_id, "DOCUMENTED_IN")

    print(f"  [SOURCE 5] Expert seeds ingested: {ingested}")


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 7: JOB PROGRAMS (TBTCP + TBTCO from Gold DB)
# ══════════════════════════════════════════════════════════════════════════════

_JOB_DOMAIN_RULES = [
    (r'^ZFI_|^YFI_|SWIFT|BCM|PAYMENT|BKPF|BSEG',  'FI',   'Finance'),
    (r'^ZHR|^YHR|^Y_HRM|PA0|PAYROLL|PY_|RPRA|RPUA', 'HCM', 'Human Capital'),
    (r'^ZMM|^YMM|PROC|EKKO|EKPO',                  'MM',   'Materials Mgmt'),
    (r'^ZFM|^YFM|PSM|BUDGET|FMBL|RFFM',            'PSM',  'Public Sector'),
    (r'^ZPS|^YPS|PROJECT|PRPS',                     'PS',   'Project System'),
    (r'BW_|^YBW|^ZBW|ODQ_|RSN3|RSCOLL',            'BW',   'BW/Analytics'),
    (r'RBDAPP|ALE|IDOC',                            'ALE',  'ALE/IDoc'),
    (r'RSCONN|SAPCONNECT',                          'COMM', 'SAPConnect'),
    (r'RDDIM|RDDMN|TMS_',                          'TMS',  'Transport Mgmt'),
    (r'RSWW|RSWF|WORKFLOW',                         'WF',   'Workflow'),
    (r'COUPA',                                      'INT',  'Coupa Integration'),
    (r'EBS',                                        'INT',  'EBS Integration'),
    (r'UNJSPF|MULE',                                'INT',  'External Integration'),
    (r'RBNK|FEB_|BANK',                             'FI',   'Bank/Treasury'),
]


def _classify_job_domain(progname):
    u = progname.upper()
    for pattern, domain, label in _JOB_DOMAIN_RULES:
        if re.search(pattern, u):
            return domain, label
    if u.startswith(('Z', 'Y')):
        return 'CUSTOM', 'Custom (Other)'
    return 'BASIS', 'SAP Standard'


def _ingest_job_programs(brain):
    """SOURCE 7: Background job programs from TBTCP/TBTCO in Gold DB."""
    db_path = PROJECT_ROOT / "Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"
    if not db_path.exists():
        print("  [SOURCE 7] Gold DB not found, skipping jobs")
        return

    conn = sqlite3.connect(str(db_path))
    try:
        available = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}

        if 'tbtcp' not in available:
            print("  [SOURCE 7] TBTCP not in Gold DB, skipping")
            return

        # Get distinct programs with step counts
        rows = conn.execute(
            "SELECT PROGNAME, COUNT(*) as steps FROM tbtcp "
            "WHERE PROGNAME IS NOT NULL AND PROGNAME != '' "
            "GROUP BY PROGNAME ORDER BY steps DESC"
        ).fetchall()

        job_count = 0
        for prog, steps in rows:
            domain, domain_label = _classify_job_domain(prog)
            job_id = f"JOB_{prog}"
            brain.add_node(
                job_id, "JOB_PROGRAM", prog,
                domain=domain,
                area=domain_label,
                metadata={"progname": prog, "steps": steps, "domain_label": domain_label},
                tags=["job", "sm37", "background", domain.lower()]
            )
            job_count += 1

            # Link to domain node if it exists
            domain_node = f"DOM_{domain}"
            if domain_node in brain.nodes:
                brain.add_edge(job_id, domain_node, "BELONGS_TO")

            # Link to REPORT node if same program exists as extracted code
            if prog in brain.nodes:
                brain.add_edge(job_id, prog, "RUNS_PROGRAM")

        # Get execution stats from TBTCO if available
        if 'tbtco' in available:
            exec_rows = conn.execute(
                "SELECT JOBNAME, COUNT(*) as runs, MIN(SDLSTRTDT) as first_run, "
                "MAX(SDLSTRTDT) as last_run FROM tbtco "
                "WHERE SDLSTRTDT IS NOT NULL AND SDLSTRTDT != '' "
                "GROUP BY JOBNAME ORDER BY runs DESC LIMIT 50"
            ).fetchall()
            top_jobs = [(jn, runs, fr, lr) for jn, runs, fr, lr in exec_rows]
            print(f"  [SOURCE 7] Top 5 jobs: {', '.join(f'{j[0]}({j[1]})' for j in top_jobs[:5])}")

        print(f"  [SOURCE 7] Job programs ingested: {job_count}")

    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 8: RFC DESTINATIONS & SYSTEM MAP (RFCDES from Gold DB)
# ══════════════════════════════════════════════════════════════════════════════

_RFC_TYPE_LABELS = {
    '3': 'SAP-to-SAP', 'I': 'Internal', 'T': 'TCP/IP',
    'G': 'HTTP', 'X': 'XML/HTTP', 'H': 'HTTP-ABAP', 'L': 'Logical',
}


def _parse_rfc_options(opts):
    result = {}
    if not opts:
        return result
    for pair in opts.split(','):
        if '=' in pair:
            k, v = pair.split('=', 1)
            result[k.strip()] = v.strip()
    return result


def _extract_system_id(host):
    match = re.search(r'hq-sap-(\w+)', host, re.I)
    if match:
        return match.group(1).upper()
    if re.match(r'\d+\.\d+\.\d+\.\d+', host):
        return None  # IP only, no system ID
    return host.upper() if host else None


def _ingest_rfc_destinations(brain):
    """SOURCE 8: RFC destinations from RFCDES in Gold DB."""
    db_path = PROJECT_ROOT / "Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"
    if not db_path.exists():
        print("  [SOURCE 8] Gold DB not found, skipping RFC destinations")
        return

    conn = sqlite3.connect(str(db_path))
    try:
        available = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}

        if 'rfcdes' not in available:
            print("  [SOURCE 8] RFCDES not in Gold DB, skipping")
            return

        rows = conn.execute(
            "SELECT RFCDEST, RFCTYPE, RFCOPTIONS FROM rfcdes "
            "WHERE RFCDEST IS NOT NULL"
        ).fetchall()

        # First pass: create SAP_SYSTEM nodes for unique target systems
        systems = {}
        for dest, rtype, opts in rows:
            if rtype != '3':
                continue
            parsed = _parse_rfc_options(opts)
            host = parsed.get('H', '')
            sys_id = _extract_system_id(host)
            if sys_id and sys_id not in systems:
                systems[sys_id] = {
                    'host': host,
                    'sysnr': parsed.get('S', ''),
                    'client': parsed.get('M', ''),
                    'connections': []
                }
            if sys_id:
                systems[sys_id]['connections'].append(dest)

        # Add P01 as the source system
        brain.add_node(
            "SYS_P01", "SAP_SYSTEM", "P01 (Production)",
            domain="INFRASTRUCTURE",
            metadata={"host": "hq-sap-p01.hq.int.unesco.org", "sysnr": "00",
                       "client": "350", "role": "Production ECC"},
            tags=["system", "production", "ecc"]
        )

        sys_count = 0
        for sys_id, info in systems.items():
            node_id = f"SYS_{sys_id}"
            # Determine role
            role = "Unknown"
            sid = sys_id.upper()
            if sid in ('D01', 'D11'):
                role = "Development"
            elif sid in ('TS1', 'TS2', 'TS3', 'TS4'):
                role = "Test/QA"
            elif sid in ('V01', 'V11'):
                role = "Validation"
            elif sid.startswith('BW') or sid == 'BRP':
                role = "BW/Reporting"
            elif sid.startswith('SM') or sid == 'SBP':
                role = "Solution Manager"
            elif sid == 'P11':
                role = "S/4 HANA"
            elif 'OSS' in sid or 'LDCI' in sid:
                role = "SAP Support"

            brain.add_node(
                node_id, "SAP_SYSTEM", f"{sys_id} ({role})",
                domain="INFRASTRUCTURE",
                metadata={"host": info['host'], "sysnr": info['sysnr'],
                           "client": info['client'], "role": role,
                           "connection_count": len(info['connections'])},
                tags=["system", role.lower().replace('/', '_')]
            )
            # P01 connects to this system
            brain.add_edge("SYS_P01", node_id, "CONNECTS_TO",
                           f"{len(info['connections'])} RFC dest(s)")
            sys_count += 1

        # Second pass: create RFC_DEST nodes
        rfc_count = 0
        for dest, rtype, opts in rows:
            parsed = _parse_rfc_options(opts)
            host = parsed.get('H', '')
            type_label = _RFC_TYPE_LABELS.get(rtype, f'Type {rtype}')

            rfc_id = f"RFC_{dest}"
            brain.add_node(
                rfc_id, "RFC_DEST", dest,
                domain="INFRASTRUCTURE",
                area=type_label,
                metadata={"rfctype": rtype, "type_label": type_label,
                           "host": host, "user": parsed.get('U', ''),
                           "client": parsed.get('M', '')},
                tags=["rfc", "sm59", rtype, type_label.lower().replace('/', '_')]
            )
            rfc_count += 1

            # Link to target system if type 3
            if rtype == '3':
                sys_id = _extract_system_id(host)
                if sys_id:
                    sys_node = f"SYS_{sys_id}"
                    if sys_node in brain.nodes:
                        brain.add_edge(rfc_id, sys_node, "CONNECTS_TO")

            # Link integration RFCs to integration jobs
            dest_upper = dest.upper()
            if 'COUPA' in dest_upper:
                for nid, n in brain.nodes.items():
                    if n['type'] == 'JOB_PROGRAM' and 'COUPA' in n['name'].upper():
                        brain.add_edge(nid, rfc_id, "INTEGRATES", "Coupa posting")
            if 'MULE' in dest_upper:
                for nid, n in brain.nodes.items():
                    if n['type'] == 'JOB_PROGRAM' and 'MULE' in n['name'].upper():
                        brain.add_edge(nid, rfc_id, "INTEGRATES", "MuleSoft")

        print(f"  [SOURCE 8] SAP systems mapped: {sys_count}, RFC destinations: {rfc_count}")

    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE CODE ANALYSIS HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _read_manifest(bsp_path):
    manifest_path = bsp_path / "manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8", errors="replace"))
        sap_app = data.get("sap.app", {})
        ds = sap_app.get("dataSources", {})
        service = ""
        for ds_name, ds_val in ds.items():
            uri = ds_val.get("uri", "")
            if "/sap/opu/odata" in uri:
                service = uri
                break
        return {
            "id":          sap_app.get("id", ""),
            "title":       sap_app.get("title", ""),
            "description": sap_app.get("description", ""),
            "service":     service,
        }
    except Exception:
        return {}


def _read_class_source(cls_path):
    parts = []
    for f in cls_path.rglob("*.abap"):
        try:
            parts.append(f.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            pass
    for f in cls_path.iterdir():
        if f.is_file() and f.suffix == "":
            try:
                parts.append(f.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                pass
    return "\n".join(parts)


def _extract_table_refs(source):
    tables = set()
    for m in re.finditer(r'\bFROM\s+([A-Z][A-Z0-9_]{2,29})\b', source, re.IGNORECASE):
        t = m.group(1).upper()
        if len(t) > 2 and not t.startswith("@"):
            tables.add(t)
    return sorted(tables)[:15]


def _extract_fm_calls(source):
    fms = set()
    for m in re.finditer(r"CALL FUNCTION\s+'([^']+)'", source, re.IGNORECASE):
        fms.add(m.group(1).upper())
    return sorted(fms)[:10]


def _extract_inheritance(source):
    m = re.search(r'INHERITING FROM\s+([A-Z][A-Z0-9_]+)', source, re.IGNORECASE)
    return m.group(1).upper() if m else ""


def _extract_service_name(service_url):
    m = re.search(r'/([A-Z][A-Z0-9_]+_SRV)/?', service_url, re.IGNORECASE)
    return m.group(1).upper() if m else ""


def _guess_service_from_class(class_name):
    name = class_name
    for suffix in ["_DPC_EXT", "_DPC", "_MPC_EXT", "_MPC"]:
        name = name.replace(suffix, "")
    name = re.sub(r'^ZCL_', '', name)
    name = re.sub(r'^YCL_', '', name)
    return (name + "_SRV").upper() if name else ""


# ══════════════════════════════════════════════════════════════════════════════
#  QUERY
# ══════════════════════════════════════════════════════════════════════════════

def query_brain(brain, keyword):
    kw = keyword.upper()
    matches = [
        n for n in brain.nodes.values()
        if kw in n["id"].upper()
        or kw in n["name"].upper()
        or any(kw in t.upper() for t in n.get("tags", []))
        or kw in n.get("domain", "").upper()
        or kw in n.get("area", "").upper()
    ]

    related_ids = {n["id"] for n in matches}
    for m in matches:
        for edge in brain.edges:
            if edge["from"] == m["id"]:
                related_ids.add(edge["to"])
            if edge["to"] == m["id"]:
                related_ids.add(edge["from"])

    all_nodes = {nid: brain.nodes[nid] for nid in related_ids if nid in brain.nodes}

    print(f"\n  [BRAIN] Query: '{keyword}' -> {len(all_nodes)} connected nodes\n")
    _print_nodes(list(all_nodes.values()))

    print(f"\n  Connections:")
    for e in brain.edges:
        if e["from"] in related_ids or e["to"] in related_ids:
            print(f"    {e['from']:45}  --[{e['type']}]-->  {e['to']}")


def _print_nodes(nodes):
    by_type = {}
    for n in nodes:
        by_type.setdefault(n["type"], []).append(n)
    for ntype, group in sorted(by_type.items()):
        print(f"  [{ntype}]")
        for n in sorted(group, key=lambda x: x["id"]):
            meta_str = ""
            if n["type"] == "BSP_APP":
                meta_str = f"  -> svc: {n['metadata'].get('service','?')[:40]}"
            elif n["type"] == "CLASS":
                tables = n["metadata"].get("tables", [])
                meta_str = f"  -> tbls: {', '.join(tables[:3])}" if tables else ""
            elif n["type"] == "SKILL":
                meta_str = f"  -> layer: {n['metadata'].get('layer','')}"
            print(f"    {n['id']:50}  dom:{n.get('domain',''):10}{meta_str}")


# ══════════════════════════════════════════════════════════════════════════════
#  HTML VISUALIZATION
# ══════════════════════════════════════════════════════════════════════════════

_TYPE_COLORS = {
    "DOMAIN":       "#FF6B6B",
    "APP_AREA":     "#4ECDC4",
    "BSP_APP":      "#45B7D1",
    "CLASS":        "#96CEB4",
    "SERVICE":      "#FFEAA7",
    "TABLE":        "#DDA0DD",
    "REPORT":       "#98D8C8",
    "INTERFACE":    "#F0B27A",
    "FUND_AREA":    "#E17055",
    "FUND":         "#FDCB6E",
    "FUND_CENTER":  "#E8B84B",
    "TRANSPORT":    "#A29BFE",
    "VALIDATION":   "#FF7675",
    "SUBSTITUTION": "#D63031",
    "SKILL":        "#FD79A8",
    "KNOWLEDGE_DOC":"#55EFC4",
    "DOCUMENT":     "#74B9FF",
    "PROCESS":      "#FFFFFF",
    "JOB_PROGRAM":  "#9B59B6",
    "RFC_DEST":     "#E67E22",
    "SAP_SYSTEM":   "#1ABC9C",
}


_HTML_MAX_NODES_PER_TYPE = {
    "FUND":         50,     # 64K funds → sample 50 per area
    "FUND_CENTER":  50,     # 764 → sample 50
    "TRANSPORT":    100,    # 7.7K → sample 100
    "JOB_PROGRAM":  100,    # 228 → sample 100 most-used
    # All other types: unlimited (small counts)
}


def _sample_nodes_for_html(brain):
    """Return a subset of nodes suitable for vis-network rendering.

    High-cardinality types (FUND, FUND_CENTER, TRANSPORT) are sampled down.
    All other types pass through unfiltered. Edges are filtered to only
    include connections between visible nodes.
    """
    from collections import defaultdict
    import random

    by_type = defaultdict(list)
    for n in brain.nodes.values():
        by_type[n["type"]].append(n)

    sampled = {}
    for ntype, nodes in by_type.items():
        max_n = _HTML_MAX_NODES_PER_TYPE.get(ntype)
        if max_n and len(nodes) > max_n:
            # Sample evenly across fund areas / domains
            by_domain = defaultdict(list)
            for n in nodes:
                by_domain[n.get("domain", "")].append(n)
            per_domain = max(1, max_n // max(1, len(by_domain)))
            chosen = []
            for domain_nodes in by_domain.values():
                random.seed(42)  # deterministic sampling
                chosen.extend(random.sample(domain_nodes, min(per_domain, len(domain_nodes))))
            for n in chosen[:max_n]:
                sampled[n["id"]] = n
        else:
            for n in nodes:
                sampled[n["id"]] = n

    # Filter edges to only visible nodes
    sampled_edges = [
        e for e in brain.edges
        if e["from"] in sampled and e["to"] in sampled
    ]

    return sampled, sampled_edges


def generate_html(brain):
    sampled_nodes, sampled_edges = _sample_nodes_for_html(brain)
    full_stats = Counter(n["type"] for n in brain.nodes.values())

    nodes_js = []
    for n in sampled_nodes.values():
        color = _TYPE_COLORS.get(n["type"], "#aaaaaa")
        label = n["id"][:28].replace('"', "'")
        title = (f"{n['type']}: {n['name']}<br>"
                 f"Domain: {n.get('domain','')}<br>"
                 f"Area: {n.get('area','')}").replace('"', "'")
        nodes_js.append(
            f'{{id:"{n["id"]}",label:"{label}",color:"{color}",'
            f'title:"{title}",group:"{n["type"]}"}}'
        )

    edges_js = []
    for i, e in enumerate(sampled_edges):
        edges_js.append(
            f'{{id:{i},from:"{e["from"]}",to:"{e["to"]}",'
            f'label:"{e["type"]}",arrows:"to"}}'
        )

    built_str    = datetime.now().strftime("%Y-%m-%d %H:%M")
    viz_stats    = Counter(n["type"] for n in sampled_nodes.values())
    legend_html  = "\n".join(
        f'    <div class="leg"><div class="dot" style="background:{c}"></div>'
        f'{t} ({viz_stats.get(t,0)}/{full_stats.get(t,0)})</div>'
        for t, c in _TYPE_COLORS.items() if full_stats.get(t, 0) > 0
    )
    stats_rows = "".join(
        f'<tr><td>{t}</td><td style="text-align:right;color:#4ECDC4;padding-left:12px">'
        f'{viz_stats.get(t,0)}/{c}</td></tr>'
        for t, c in full_stats.most_common()
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>UNESCO SAP Living Knowledge Brain</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:#1a1a2e;font-family:Inter,sans-serif;color:#eee}}
    #hdr{{padding:12px 20px;background:#16213e;border-bottom:1px solid #0f3460;
          display:flex;justify-content:space-between;align-items:center}}
    #hdr h1{{font-size:17px;color:#4ECDC4}}
    .meta{{font-size:11px;color:#888}}
    #network{{width:100%;height:calc(100vh - 52px)}}
    #legend{{position:fixed;top:64px;right:12px;background:#16213e88;backdrop-filter:blur(4px);
             padding:12px 16px;border-radius:8px;border:1px solid #0f3460;
             font-size:11px;max-height:calc(100vh - 90px);overflow-y:auto;width:230px}}
    #legend b{{color:#4ECDC4;display:block;margin-bottom:6px}}
    .leg{{display:flex;align-items:center;gap:7px;margin:2px 0}}
    .dot{{width:9px;height:9px;border-radius:50%;flex-shrink:0}}
    #stats{{margin-top:10px;border-top:1px solid #0f3460;padding-top:8px}}
    table{{width:100%;border-collapse:collapse;font-size:10px}}
    td{{padding:1px 3px}}
  </style>
</head>
<body>
  <div id="hdr">
    <h1>UNESCO SAP — Living Knowledge Brain</h1>
    <div class="meta">
      Graph: {len(brain.nodes)} nodes / {len(brain.edges)} edges &nbsp;|&nbsp;
      Viz: {len(sampled_nodes)} nodes / {len(sampled_edges)} edges &nbsp;|&nbsp;
      6 sources &nbsp;|&nbsp; Built: {built_str}
    </div>
  </div>
  <div id="network"></div>
  <div id="legend">
    <b>Node Types (viz/total)</b>
{legend_html}
    <div id="stats">
      <b>Counts by Type</b>
      <table>{stats_rows}</table>
    </div>
  </div>
  <script>
    var nodes = new vis.DataSet([{",".join(nodes_js)}]);
    var edges = new vis.DataSet([{",".join(edges_js)}]);
    var options = {{
      edges:{{font:{{size:8,color:'#555'}},color:{{color:'#333',highlight:'#4ECDC4'}},
              smooth:{{type:'curvedCW',roundness:0.15}}}},
      nodes:{{shape:'dot',size:13,font:{{size:10,color:'#ccc'}},
              borderWidth:2,borderWidthSelected:3}},
      physics:{{barnesHut:{{gravitationalConstant:-4000,springLength:160,damping:0.2}},
                stabilization:{{iterations:400,updateInterval:50}}}},
      interaction:{{hover:true,tooltipDelay:200}},
    }};
    new vis.Network(document.getElementById('network'),{{nodes,edges}},options);
  </script>
</body>
</html>"""

    out = BRAIN_FILE.parent / "sap_knowledge_graph.html"
    out.write_text(html, encoding="utf-8")
    print(f"  [BRAIN] HTML graph -> {out}")
    return out


# ══════════════════════════════════════════════════════════════════════════════
#  STATS
# ══════════════════════════════════════════════════════════════════════════════

def _print_summary(brain):
    types   = Counter(n["type"]   for n in brain.nodes.values())
    domains = Counter(n["domain"] for n in brain.nodes.values())
    edges   = Counter(e["type"]   for e in brain.edges)

    print(f"\n  +-- BRAIN STATS -------------------------------------------+")
    print(f"  |  Total Nodes: {len(brain.nodes):<6}  Total Edges: {len(brain.edges):<6}               |")
    print(f"  +-----------------------------------------------------------+")

    print(f"\n  Nodes by type:")
    for t, c in types.most_common():
        bar = "#" * min(c, 40)
        print(f"    {t:<18} {c:>4}  {bar}")

    print(f"\n  Nodes by domain:")
    for d, c in domains.most_common():
        print(f"    {d:<18} {c:>4}")

    print(f"\n  Edges by type:")
    for e, c in edges.most_common():
        print(f"    {e:<22} {c:>4}")


# ══════════════════════════════════════════════════════════════════════════════
#  BRAIN SUMMARY — Tiered Access L1 (Anthropic Progressive Disclosure)
# ══════════════════════════════════════════════════════════════════════════════
#
# Three levels of brain access:
#   L1: BRAIN_SUMMARY.md  — always loadable, ~50 lines, stats + domain map
#   L2: --focus <domain>  — JIT load one domain's nodes + edges (~100-500 nodes)
#   L3: sap_brain.json    — full graph (73K+ nodes), only for rebuild/bulk analysis
#

def generate_summary(brain):
    """Generate BRAIN_SUMMARY.md — the L1 lightweight index.

    This file is designed to be loaded into agent context at startup.
    It gives enough structure to decide WHAT to query, without loading
    the full 73K-node graph.
    """
    types   = Counter(n["type"]   for n in brain.nodes.values())
    domains = Counter(n["domain"] for n in brain.nodes.values())
    edges   = Counter(e["type"]   for e in brain.edges)

    # Fund area details with aggregates
    fa_details = []
    for nid, node in sorted(brain.nodes.items()):
        if node["type"] == "FUND_AREA":
            meta = node.get("metadata", {})
            fa_details.append(
                f"| {meta.get('fikrs','?'):6} | {meta.get('fund_count',0):>6} "
                f"| {meta.get('active_funds','?'):>6} | {meta.get('active_fund_centers','?'):>6} "
                f"| {meta.get('fmifiit_docs','?'):>10} |"
            )

    # Non-data structural nodes (code, knowledge, skills)
    structural = []
    for nid, node in sorted(brain.nodes.items()):
        if node["type"] in ("BSP_APP", "CLASS", "SERVICE", "REPORT", "INTERFACE",
                            "PROCESS", "DOMAIN", "APP_AREA"):
            structural.append(f"  - `{nid}` ({node['type']}) — {node['name']} [{node['domain']}]")

    # Join map
    join_lines = []
    for e in brain.edges:
        if e["type"] == "JOINS_VIA":
            join_lines.append(f"  - `{e['from']}` → `{e['to']}` — {e.get('label', '')}")

    built = datetime.now().strftime("%Y-%m-%d %H:%M")

    md = f"""# BRAIN SUMMARY — Progressive Disclosure L1
> Auto-generated by `sap_brain.py --build`. Do NOT edit manually.
> Built: {built} | Full graph: {len(brain.nodes):,} nodes / {len(brain.edges):,} edges

## How to Use This File
- **L1 (this file)**: Read at session start. Enough to route queries.
- **L2 (focus)**: `python sap_brain.py --focus PSM` — loads one domain's nodes.
- **L3 (full)**: `python sap_brain.py --build` — rebuilds entire 73K+ node graph.

## Graph Overview

| Metric | Count |
|--------|------:|
| Total Nodes | {len(brain.nodes):,} |
| Total Edges | {len(brain.edges):,} |
| Sources | 6 |

### Nodes by Type
| Type | Count |
|------|------:|
""" + "\n".join(f"| {t} | {c:,} |" for t, c in types.most_common()) + """

### Nodes by Domain
| Domain | Count |
|--------|------:|
""" + "\n".join(f"| {d} | {c:,} |" for d, c in domains.most_common() if c > 0) + """

### Edge Types
| Edge | Count | Description |
|------|------:|-------------|
""" + "\n".join(
    f"| {e} | {c:,} | {EDGE_TYPES.get(e, '')} |" for e, c in edges.most_common()
) + """

## Fund Area Aggregates
| Area | Total Funds | Active Funds | Active FCs | FMIFIIT Docs |
|------|------------|-------------|-----------|-------------|
""" + "\n".join(fa_details) + """

## Table Join Map (JOINS_VIA)
""" + "\n".join(join_lines) + """

## Structural Nodes (Code + Process)
""" + "\n".join(structural[:60]) + """

## Quick Access Commands
```bash
# Full stats
python sap_brain.py --stats

# Focus on one domain (JIT load)
python sap_brain.py --focus PSM
python sap_brain.py --focus HCM
python sap_brain.py --focus CTS

# Query by keyword
python sap_brain.py --query offboarding
python sap_brain.py --query FMIFIIT

# Single node deep dive
python sap_brain.py --node FUND_AAFRA2023

# Rebuild everything
python sap_brain.py --build --html --stats
```
"""

    out = BRAIN_FILE.parent / "BRAIN_SUMMARY.md"
    out.write_text(md, encoding="utf-8")
    print(f"  [BRAIN] Summary -> {out}  ({len(md)} chars)")
    return out


def focus_domain(brain, domain):
    """L2 JIT loading: show all nodes and edges for a specific domain."""
    domain_upper = domain.upper()
    matched = {
        nid: n for nid, n in brain.nodes.items()
        if n.get("domain", "").upper() == domain_upper
        or domain_upper in nid.upper()
    }

    if not matched:
        print(f"\n  [FOCUS] No nodes found for domain '{domain}'")
        return

    # Find all edges touching matched nodes
    matched_ids = set(matched.keys())
    related_edges = []
    neighbor_ids = set()
    for e in brain.edges:
        if e["from"] in matched_ids or e["to"] in matched_ids:
            related_edges.append(e)
            neighbor_ids.add(e["from"])
            neighbor_ids.add(e["to"])

    # Add neighbor nodes (1 hop)
    for nid in neighbor_ids - matched_ids:
        if nid in brain.nodes:
            matched[nid] = brain.nodes[nid]

    # Print focused view
    types = Counter(n["type"] for n in matched.values())
    print(f"\n  [FOCUS] Domain: {domain}")
    print(f"  Nodes: {len(matched)} | Edges: {len(related_edges)}")
    print(f"\n  Types: {dict(types.most_common())}")

    # Show non-bulk nodes (skip individual funds/transports, show structure)
    for nid, n in sorted(matched.items()):
        if n["type"] not in ("FUND", "TRANSPORT", "FUND_CENTER"):
            meta_str = ""
            if n.get("metadata"):
                meta_str = f"  meta: {json.dumps(n['metadata'], ensure_ascii=True)[:120]}"
            print(f"    {n['type']:<18} {nid:<50} {n.get('domain',''):<10}{meta_str}")

    # Show edge summary
    edge_types = Counter(e["type"] for e in related_edges)
    print(f"\n  Edge breakdown: {dict(edge_types.most_common())}")

    # Show join edges explicitly
    for e in related_edges:
        if e["type"] == "JOINS_VIA":
            print(f"    JOIN: {e['from']} → {e['to']}  ({e.get('label','')})")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="UNESCO SAP Living Knowledge Brain — 6-source knowledge graph"
    )
    parser.add_argument("--build",   action="store_true", help="Build from all 6 sources")
    parser.add_argument("--query",   help="Search related nodes by keyword")
    parser.add_argument("--domain",  help="Show all nodes in a domain (HCM, PSM, CTS...)")
    parser.add_argument("--focus",   help="L2 JIT load: show focused view of one domain")
    parser.add_argument("--summary", action="store_true", help="L1: regenerate BRAIN_SUMMARY.md")
    parser.add_argument("--node",    help="Show all connections of a specific node ID")
    parser.add_argument("--html",    action="store_true", help="Generate visual HTML graph")
    parser.add_argument("--stats",   action="store_true", help="Show graph statistics")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  UNESCO SAP LIVING KNOWLEDGE BRAIN")
    print(f"  Project: {PROJECT_ROOT}")
    print(f"{'='*60}")

    if args.build:
        brain = build_brain()
        brain.save()
        generate_summary(brain)     # L1: always regenerate summary on build
        _print_summary(brain)
        if args.html:
            generate_html(brain)
    else:
        brain = SAPBrain.load()
        if not brain.nodes:
            print("  No brain data. Run: python sap_brain.py --build")
            return

        if args.summary:
            generate_summary(brain)

        if args.focus:
            focus_domain(brain, args.focus)

        if args.stats:
            _print_summary(brain)

        if args.query:
            query_brain(brain, args.query)

        if args.domain:
            query_brain(brain, args.domain)

        if args.node:
            node_id = args.node.upper()
            node = brain.nodes.get(node_id)
            if node:
                print(f"\n  Node: {node_id}")
                print(f"  Type:   {node['type']}")
                print(f"  Domain: {node['domain']} / Area: {node.get('area','')}")
                print(f"  Tags:   {', '.join(node['tags'])}")
                print(f"  Meta:\n{json.dumps(node['metadata'], indent=4)[:600]}")
                print(f"\n  Outgoing edges:")
                for e in brain.edges:
                    if e["from"] == node_id:
                        print(f"    --> [{e['type']:20}] {e['to']}")
                print(f"\n  Incoming edges:")
                for e in brain.edges:
                    if e["to"] == node_id:
                        print(f"    <-- [{e['type']:20}] {e['from']}")
            else:
                print(f"  Node '{node_id}' not found. Try --query {args.node}")

        if args.html:
            generate_html(brain)


if __name__ == "__main__":
    main()
