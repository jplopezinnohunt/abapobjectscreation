"""
build.py — Brain v2 unified build orchestrator.

Runs all ingestors in sequence, validates against spec, saves brain.
Usage:
    python -m brain_v2.build --phase 1        # Code edges only
    python -m brain_v2.build --phase 2        # + Config/integration/transport
    python -m brain_v2.build --phase 3        # + Process overlay
    python -m brain_v2.build --all            # Everything
    python -m brain_v2.build --stats          # Just print stats
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
BRAIN_PATH = REPO / ".agents" / "intelligence" / "brain_v2.json"
GOLD_DB = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
EXTRACTED_CODE = REPO / "extracted_code"
EXTRACTED_SAP = REPO / "extracted_sap"
BRAIN_V1 = REPO / ".agents" / "intelligence" / "sap_brain.json"
SESSION = "039"


def build_phase1(brain, session: str = SESSION) -> None:
    """Phase 1: Parse ABAP code -> behavioral edges."""
    from brain_v2.parsers.abap_parser import ABAPDependencyParser

    parser = ABAPDependencyParser()
    nodes_before = brain.graph.number_of_nodes()
    edges_before = brain.graph.number_of_edges()

    # Parse extracted_code/
    print(f"\n[PHASE 1] Parsing ABAP source code...")
    dirs_to_parse = []
    if EXTRACTED_CODE.exists():
        dirs_to_parse.append(("extracted_code", EXTRACTED_CODE))
    if EXTRACTED_SAP.exists():
        dirs_to_parse.append(("extracted_sap", EXTRACTED_SAP))

    total_files = 0
    total_deps = 0

    for label, base_dir in dirs_to_parse:
        print(f"  [{label}] Scanning {base_dir}...")
        results = parser.parse_directory(base_dir)
        print(f"  [{label}] {len(results)} files with dependencies")
        total_files += len(results)

        for rel_path, deps in results.items():
            # Determine class/report name from path
            parts = Path(rel_path).parts
            if len(parts) >= 1:
                # Use first directory or filename stem as the code object name
                code_name = parts[0] if len(parts) > 1 else Path(rel_path).stem
            else:
                code_name = Path(rel_path).stem

            # Determine node type
            code_name_upper = code_name.upper()
            if code_name_upper.startswith(("ZCL_", "YCL_", "CL_")):
                node_type = "ABAP_CLASS"
            elif code_name_upper.startswith(("Z_", "Y_", "ZXFM", "ZXFI")):
                node_type = "ENHANCEMENT"
            else:
                node_type = "ABAP_REPORT"

            code_id = f"{node_type}:{code_name_upper}"

            # Add code object node
            brain.add_node(code_id, node_type, code_name,
                           domain="CUSTOM", layer="code",
                           source=label, session=session,
                           metadata={
                               "tables_read": deps["tables_read"],
                               "fms_called": deps["fms_called"],
                               "is_badi_impl": deps["is_badi_impl"],
                           })

            # READS_TABLE edges
            for table in deps["tables_read"]:
                tbl_id = f"SAP_TABLE:{table}"
                brain.add_node(tbl_id, "SAP_TABLE", table,
                               domain="DATA_MODEL", layer="data", source="parsed")
                brain.add_edge(code_id, tbl_id, "READS_TABLE",
                               label=f"{code_name} reads {table}",
                               evidence="parsed", confidence=1.0, session=session)
                total_deps += 1

            # READS_FIELD edges
            for table, fields in deps["fields_read"]:
                for field in fields:
                    field_id = f"TABLE_FIELD:{table}.{field}"
                    brain.add_node(field_id, "TABLE_FIELD", f"{table}.{field}",
                                   domain="DATA_MODEL", layer="data", source="parsed",
                                   metadata={"table_name": table, "data_type": ""})
                    brain.add_edge(code_id, field_id, "READS_FIELD",
                                   label=f"{code_name} reads {table}.{field}",
                                   evidence="parsed", confidence=0.9, session=session)
                    total_deps += 1

            # CALLS_FM edges
            for fm in deps["fms_called"]:
                fm_id = f"FUNCTION_MODULE:{fm}"
                brain.add_node(fm_id, "FUNCTION_MODULE", fm,
                               domain="CUSTOM", layer="code", source="parsed",
                               metadata={"rfc_enabled": False})
                brain.add_edge(code_id, fm_id, "CALLS_FM",
                               label=f"{code_name} calls {fm}",
                               evidence="parsed", confidence=1.0, session=session)
                total_deps += 1

            # WRITES_TABLE edges
            for table in deps["tables_written"]:
                tbl_id = f"SAP_TABLE:{table}"
                brain.add_node(tbl_id, "SAP_TABLE", table,
                               domain="DATA_MODEL", layer="data", source="parsed")
                brain.add_edge(code_id, tbl_id, "WRITES_TABLE",
                               label=f"{code_name} writes {table}",
                               evidence="parsed", confidence=1.0, session=session,
                               weight=1.2)  # higher risk for writes
                total_deps += 1

            # INHERITS_FROM edges
            for super_cls in deps["inherits"]:
                super_id = f"ABAP_CLASS:{super_cls}"
                brain.add_node(super_id, "ABAP_CLASS", super_cls,
                               domain="CUSTOM", layer="code", source="parsed")
                brain.add_edge(code_id, super_id, "INHERITS_FROM",
                               label=f"{code_name} inherits from {super_cls}",
                               evidence="parsed", confidence=1.0, session=session)
                total_deps += 1

            # IMPLEMENTS_INTF edges
            for intf in deps["interfaces"]:
                intf_id = f"ABAP_CLASS:{intf}"
                brain.add_node(intf_id, "ABAP_CLASS", intf,
                               domain="CUSTOM", layer="code", source="parsed")
                brain.add_edge(code_id, intf_id, "IMPLEMENTS_INTF",
                               label=f"{code_name} implements {intf}",
                               evidence="parsed", confidence=1.0, session=session)
                total_deps += 1

            # BAdI implementation
            if deps["is_badi_impl"] and deps.get("badi_interface"):
                badi_name = deps["badi_interface"].replace("IF_EX_", "")
                badi_id = f"ENHANCEMENT:{badi_name}"
                brain.add_node(badi_id, "ENHANCEMENT", badi_name,
                               domain="CUSTOM", layer="code", source="parsed",
                               metadata={"enhancement_type": "badi_impl"})
                brain.add_edge(code_id, badi_id, "IMPLEMENTS_BADI",
                               label=f"{code_name} implements BAdI {badi_name}",
                               evidence="parsed", confidence=0.85, session=session)
                total_deps += 1

    nodes_added = brain.graph.number_of_nodes() - nodes_before
    edges_added = brain.graph.number_of_edges() - edges_before
    brain.log_ingestion("abap_parser", nodes_added, edges_added, session)
    print(f"\n[PHASE 1 DONE] {total_files} files parsed -> {nodes_added} nodes + {edges_added} edges ({total_deps} dependencies)")


def build_phase2(brain, session: str = SESSION) -> None:
    """Phase 2: Config + Integration + Transport edges from Gold DB."""
    import sqlite3

    if not GOLD_DB.exists():
        print(f"[PHASE 2] Gold DB not found at {GOLD_DB} — skipping")
        return

    print(f"\n[PHASE 2] Ingesting config + integration from Gold DB...")
    conn = sqlite3.connect(GOLD_DB)
    nodes_before = brain.graph.number_of_nodes()
    edges_before = brain.graph.number_of_edges()

    # Get available tables
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

    # ── T042Z: Payment Method per Country ──
    if "T042Z" in tables:
        print("  [CONFIG] T042Z (payment methods by country)...")
        try:
            rows = conn.execute("SELECT LAND1, ZLSCH, TEXT1 FROM T042Z WHERE LAND1 IS NOT NULL").fetchall()
            for land1, zlsch, text1 in rows:
                land1 = (land1 or "").strip()
                zlsch = (zlsch or "").strip()
                if not land1 or not zlsch:
                    continue
                pm_id = f"PAYMENT_METHOD:{land1}:{zlsch}"
                brain.add_node(pm_id, "PAYMENT_METHOD", f"{land1}-{zlsch}",
                               domain="FI", layer="config", source="gold_db",
                               metadata={"company_code": "", "country": land1,
                                        "method_code": zlsch, "description": (text1 or "").strip()})
            print(f"    {len(rows)} payment methods")
        except Exception as e:
            print(f"    T042Z error: {e}")

    # ── CTS Transports + Objects -> CO_TRANSPORTED_WITH ──
    if "cts_transports" in tables and "cts_objects" in tables:
        print("  [TRANSPORT] cts_transports + cts_objects...")
        try:
            # Add transport nodes
            trs = conn.execute("SELECT TRKORR, AS4USER, TRSTATUS FROM cts_transports").fetchall()
            for trkorr, user, status in trs:
                tr_id = f"TRANSPORT:{(trkorr or '').strip()}"
                brain.add_node(tr_id, "TRANSPORT", (trkorr or "").strip(),
                               domain="CTS", layer="transport", source="gold_db",
                               metadata={"owner": (user or "").strip(), "status": (status or "").strip()})

            # Add transport -> object edges
            objs = conn.execute("""
                SELECT TRKORR, PGMID, OBJECT, OBJ_NAME
                FROM cts_objects
                WHERE OBJ_NAME IS NOT NULL AND OBJ_NAME != ''
            """).fetchall()

            obj_type_map = {
                'PROG': 'ABAP_REPORT', 'CLAS': 'ABAP_CLASS', 'FUGR': 'FUNCTION_MODULE',
                'TABL': 'SAP_TABLE', 'ENHO': 'ENHANCEMENT', 'DEVC': 'PACKAGE',
            }

            # Track objects per transport for co-change edges
            transport_objects: dict[str, list[str]] = {}

            for trkorr, pgmid, obj_type, obj_name in objs:
                trkorr = (trkorr or "").strip()
                obj_name = (obj_name or "").strip()
                obj_type = (obj_type or "").strip()
                if not trkorr or not obj_name:
                    continue

                node_type = obj_type_map.get(obj_type, "ABAP_REPORT")
                obj_id = f"{node_type}:{obj_name.upper()}"

                if not brain.graph.has_node(obj_id):
                    brain.add_node(obj_id, node_type, obj_name,
                                   domain="CTS", layer="code", source="gold_db")

                tr_id = f"TRANSPORT:{trkorr}"
                brain.add_edge(tr_id, obj_id, "TRANSPORTS",
                               label=f"{trkorr} carries {obj_name}",
                               evidence="config", confidence=1.0, session=session)

                transport_objects.setdefault(trkorr, []).append(obj_id)

            # CO_TRANSPORTED_WITH edges (co-change coupling)
            co_change_count = 0
            for trkorr, obj_ids in transport_objects.items():
                if len(obj_ids) <= 1 or len(obj_ids) > 50:  # skip single-object and huge transports
                    continue
                # Connect first 10 pairs to avoid combinatorial explosion
                for i, a in enumerate(obj_ids[:10]):
                    for b in obj_ids[i + 1:10]:
                        if a != b:
                            brain.add_edge(a, b, "CO_TRANSPORTED_WITH",
                                           label=f"co-changed in {trkorr}",
                                           evidence="config", confidence=0.7, session=session,
                                           weight=0.4)
                            co_change_count += 1

            print(f"    {len(trs)} transports, {len(objs)} objects, {co_change_count} co-change edges")
        except Exception as e:
            print(f"    CTS error: {e}")

    # ── RFCDES: RFC Destinations -> Systems ──
    if "rfcdes" in tables:
        print("  [INTEGRATION] rfcdes...")
        try:
            rows = conn.execute("SELECT RFCDEST, RFCTYPE FROM rfcdes WHERE RFCDEST IS NOT NULL").fetchall()
            for dest, rfctype in rows:
                dest = (dest or "").strip()
                if not dest:
                    continue
                dest_id = f"RFC_DESTINATION:{dest}"
                brain.add_node(dest_id, "RFC_DESTINATION", dest,
                               domain="BASIS", layer="integration", source="gold_db",
                               metadata={"rfc_type": (rfctype or "").strip()})
                # Extract system ID from destination name (e.g., P01CLNT350 -> P01)
                sysid = dest[:3] if len(dest) >= 3 and dest[:3].isalnum() else ""
                if sysid and sysid.upper() not in ("SM5", "SAP", "RFC"):
                    sys_id = f"SAP_SYSTEM:{sysid.upper()}"
                    if not brain.graph.has_node(sys_id):
                        brain.add_node(sys_id, "SAP_SYSTEM", sysid.upper(),
                                       domain="BASIS", layer="integration", source="gold_db")
                    brain.add_edge(dest_id, sys_id, "CALLS_SYSTEM",
                                   evidence="config", confidence=0.7, session=session)
            print(f"    {len(rows)} RFC destinations")
        except Exception as e:
            print(f"    RFCDES error: {e}")

    # ── TFDIR_CUSTOM: RFC-enabled FMs ──
    if "tfdir_custom" in tables:
        print("  [INTEGRATION] tfdir_custom (RFC-enabled FMs)...")
        try:
            rows = conn.execute("""
                SELECT FUNCNAME, PNAME FROM tfdir_custom
                WHERE FUNCNAME LIKE 'Z%' OR FUNCNAME LIKE 'Y%'
            """).fetchall()
            for funcname, pname in rows:
                funcname = (funcname or "").strip()
                if not funcname:
                    continue
                fm_id = f"FUNCTION_MODULE:{funcname}"
                brain.add_node(fm_id, "FUNCTION_MODULE", funcname,
                               domain="CUSTOM", layer="code", source="gold_db",
                               metadata={"rfc_enabled": True, "fugr": (pname or "").strip()})
            print(f"    {len(rows)} custom FMs")
        except Exception as e:
            print(f"    TFDIR error: {e}")

    conn.close()
    nodes_added = brain.graph.number_of_nodes() - nodes_before
    edges_added = brain.graph.number_of_edges() - edges_before
    brain.log_ingestion("config+integration+transport", nodes_added, edges_added, session)
    print(f"\n[PHASE 2 DONE] {nodes_added} nodes + {edges_added} edges added")


def build_phase3(brain, session: str = SESSION) -> None:
    """Phase 3: Process overlay."""
    print(f"\n[PHASE 3] Process overlay...")
    nodes_before = brain.graph.number_of_nodes()
    edges_before = brain.graph.number_of_edges()

    PROCESSES = {
        "P2P": {
            "name": "Procure to Pay",
            "domain": "MM",
            "steps": [
                ("PR Created", ["EBAN"], ["ME51N"]),
                ("PR Released", ["EBAN"], ["ME54N"]),
                ("PO Created", ["EKKO", "EKPO"], ["ME21N"]),
                ("PO Released", ["EKKO"], ["ME29N"]),
                ("GR Posted", ["EKBE", "BKPF"], ["MIGO"]),
                ("SES Created", ["ESSR", "ESLL"], ["ML81N"]),
                ("Invoice Posted", ["RBKP", "RSEG", "BKPF"], ["MIRO"]),
                ("Payment Run", ["REGUH"], ["F110"]),
            ],
            "events": 848000,
        },
        "Payment_E2E": {
            "name": "Payment End-to-End",
            "domain": "FI",
            "steps": [
                ("Invoice Received", ["RBKP", "BKPF"], ["MIRO", "FB60"]),
                ("Payment Proposal", ["REGUH"], ["F110"]),
                ("Payment Execution", ["REGUH", "BKPF", "PAYR"], ["F110"]),
                ("BCM Batch Created", ["BNK_BATCH_HEADER"], ["BNK_MONI"]),
                ("BCM Approved", ["BNK_BATCH_HEADER"], ["BNK_MONI"]),
                ("Bank File Sent", ["BNK_BATCH_ITEM"], ["BNK_MONI"]),
                ("Bank Confirmed", ["FEBEP"], ["FF_5"]),
            ],
            "events": 1400000,
        },
        "Bank_Statement": {
            "name": "Bank Statement Processing",
            "domain": "FI",
            "steps": [
                ("Statement Imported", ["FEBKO"], ["FF_5"]),
                ("Items Posted", ["FEBEP", "BKPF"], ["FEBAN"]),
                ("Items Cleared", ["FEBEP"], ["FEBAN"]),
                ("Reconciled", ["FEBRE"], ["FEBAN"]),
            ],
            "events": 263000,
        },
    }

    for proc_id, proc_def in PROCESSES.items():
        p_node = f"PROCESS:{proc_id}"
        brain.add_node(p_node, "PROCESS", proc_def["name"],
                       domain=proc_def["domain"], layer="process", source="process_mining",
                       metadata={"process_type": proc_id, "event_count": proc_def["events"]})

        prev_step = None
        for i, (step_name, tables, tcodes) in enumerate(proc_def["steps"]):
            step_id = f"PROCESS_STEP:{proc_id}:{step_name.replace(' ', '_')}"
            brain.add_node(step_id, "PROCESS_STEP", step_name,
                           domain=proc_def["domain"], layer="process", source="process_mining",
                           metadata={"process_id": proc_id, "step_order": i, "tcodes": tcodes})

            brain.add_edge(p_node, step_id, "PROCESS_CONTAINS",
                           evidence="mined", confidence=0.95, session=session)

            if prev_step:
                brain.add_edge(prev_step, step_id, "STEP_FOLLOWS",
                               evidence="mined", confidence=0.9, session=session)

            for table in tables:
                tbl_id = f"SAP_TABLE:{table}"
                brain.add_node(tbl_id, "SAP_TABLE", table,
                               domain="DATA_MODEL", layer="data", source="process_mining")
                brain.add_edge(step_id, tbl_id, "STEP_READS",
                               evidence="mined", confidence=0.85, session=session)

            prev_step = step_id

    nodes_added = brain.graph.number_of_nodes() - nodes_before
    edges_added = brain.graph.number_of_edges() - edges_before
    brain.log_ingestion("process_overlay", nodes_added, edges_added, session)
    print(f"\n[PHASE 3 DONE] {nodes_added} nodes + {edges_added} edges added")


def main():
    from brain_v2.graph import BrainV2

    ap = argparse.ArgumentParser(description="Brain v2 build orchestrator")
    ap.add_argument("--phase", type=int, choices=[1, 2, 3], help="Run specific phase")
    ap.add_argument("--all", action="store_true", help="Run all phases")
    ap.add_argument("--stats", action="store_true", help="Print stats only")
    ap.add_argument("--session", default=SESSION, help="Session number")
    args = ap.parse_args()

    # Load existing brain or create new
    if BRAIN_PATH.exists() and not args.all:
        print(f"[LOAD] Loading existing brain from {BRAIN_PATH}")
        brain = BrainV2.load(BRAIN_PATH)
    else:
        print(f"[NEW] Creating fresh brain v2")
        brain = BrainV2()

    if args.stats:
        s = brain.stats()
        print(f"\n{'='*60}")
        print(f"  Brain v2 Statistics")
        print(f"{'='*60}")
        print(f"  Spec version: {s['spec_version']}")
        print(f"  Total nodes:  {s['total_nodes']:,}")
        print(f"  Total edges:  {s['total_edges']:,}")
        print(f"  Valid edges:  {s['valid_edges']:,}")
        print(f"  Superseded:   {s['superseded_edges']:,}")
        print(f"\n  Node types:")
        for nt, count in list(s['node_types'].items())[:15]:
            print(f"    {nt:25s} {count:>8,}")
        print(f"\n  Edge types:")
        for et, count in list(s['edge_types'].items())[:15]:
            print(f"    {et:25s} {count:>8,}")
        print(f"\n  Domains:")
        for d, count in list(s['domains'].items())[:10]:
            print(f"    {d:25s} {count:>8,}")
        return

    t0 = time.time()

    if args.all or args.phase == 1:
        build_phase1(brain, args.session)
    if args.all or args.phase == 2:
        build_phase2(brain, args.session)
    if args.all or args.phase == 3:
        build_phase3(brain, args.session)

    # Save
    BRAIN_PATH.parent.mkdir(parents=True, exist_ok=True)
    brain.save(BRAIN_PATH)
    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  Brain saved to {BRAIN_PATH}")
    print(f"  {brain.graph.number_of_nodes():,} nodes / {brain.graph.number_of_edges():,} edges")
    print(f"  Hash: {brain.brain_hash()}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
