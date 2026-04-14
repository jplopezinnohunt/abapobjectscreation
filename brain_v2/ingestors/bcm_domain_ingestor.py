"""
Brain v2 BCM domain ingestor — add Bank Communication Management (BCM)
signatory domain objects and relationships to the graph.

Discovered Session #052 (INC-000006313). The BCM signatory domain was a blind
spot: we had tables PA0002/PA0105 classified, but HRP1000/HRP1001/OOCU_RESP/
the 24 RY groups / the two workflow rules / Gold DB tables / check scripts
were either MISSING (not in graph) or GHOSTs (in graph but filtered out).

This ingester closes that gap by registering:
  - 5 SAP tables: HRP1000, HRP1001, USR02, PA0002, PA0105 (last 2 already there)
  - 1 SAP transaction: OOCU_RESP
  - 1 BCM workflow: 90000003
  - 2 workflow rules: BNK_COM_01_01_03 (90000004), BNK_INI_01_01_04 (90000005)
  - 24 RY responsibility groups (UIS / UNES / IIEP / UBO / UIL with tier variants)
  - 2 Gold DB tables: bcm_signatory_responsibility, bcm_signatory_assignment
  - 2 quality check scripts: extract_bcm_signatories, bcm_signatory_reconciliation_check

And the edges between them:
  OOCU_RESP          MAINTAINS          HRP1000, HRP1001
  WORKFLOW 90000003  CALLS_RULE         BNK_COM_01_01_03, BNK_INI_01_01_04
  BNK_COM            RESOLVES_VIA       7 RY_GROUPs
  BNK_INI            RESOLVES_VIA       15 RY_GROUPs
  RY_GROUP           STORED_IN          HRP1000
  RY_GROUP           HAS_ASSIGNMENTS_IN HRP1001
  HRP1001            RESOLVES_PERNR_VIA PA0002, PA0105
  PA0105             RESOLVES_USER_VIA  USR02
  extract_bcm_*      READS              HRP1000, HRP1001, PA0002, PA0105
  extract_bcm_*      POPULATES          bcm_signatory_responsibility, _assignment
  reconciliation_*   READS              bcm_signatory_assignment
  reconciliation_*   DETECTS            dq_ghost_pernr_bcm_oesttveit
  INC-000006313      AFFECTS            RY 50010054, RY 50036801
  RY 50010087        ADJACENT_TRAP_TO   RY 50036801 (lookalike under same rule)
"""

RY_GROUPS_COM = {
    "50010052": "UNES signatures for all transfers",
    "50010054": "UIS signatures for all transfers",
    "50010088": "IIEP signatures for all transfers",
    "50034894": "UBO signatures up to 10.000",
    "50036326": "UIS signatures up to 10.000",
    "50036737": "UBO signatures for transfers over 10.000",
    "50037531": "UIL signatures for all transfers",
}

RY_GROUPS_INI = {
    "50010051": "UIS AP Validation up to 10.000 USD",
    "50010053": "UIS AP Validation up to 5.000.000 USD",
    "50036801": "UIS Validation",
    "50010075": "UNES FAS/PAP/AP Validation to 500.000",
    "50010076": "UNES FAS/PAP/AP Validation to 5.000.000",
    "50010077": "UNES FAS/PAP/AP Validation to 50.000.000",
    "50038878": "UNES FAS/PAP/AP Validation to 7.500.000",
    "50036716": "UNES AP Validation up to 10.000.000 USD",
    "50032363": "UNES FAS/PAP/PAY Validation",
    "50010078": "UNES TRS Validation up to 50.000.000",
    "50010079": "UNESCO bank to bank transfers",
    "50010087": "IIEP Validation",
    "50034892": "UBO Validation up to 10.000 USD",
    "50034893": "UBO Validation up to 5.000.000 USD",
    "50037530": "UIL Validation",
}


def ingest_bcm_domain(brain, project_root: str):
    """Register BCM signatory objects and relationships in the graph."""
    stats = {"nodes_added": 0, "nodes_existed": 0, "edges_added": 0}

    def ensure_node(nid, ntype, name, **kwargs):
        if nid in brain.G:
            stats["nodes_existed"] += 1
            # still tag/update domain if not set
            node_data = brain.G.nodes[nid]
            if not node_data.get("domain") and kwargs.get("domain"):
                node_data["domain"] = kwargs["domain"]
            return
        brain.add_node(nid, ntype, name, source="bcm_domain_ingestor", **kwargs)
        stats["nodes_added"] += 1

    def add_edge(src, tgt, etype, **kwargs):
        if src not in brain.G or tgt not in brain.G:
            return
        brain.add_edge(src, tgt, etype,
                       evidence="bcm_domain_ingestor",
                       confidence=1.0,
                       discovered_in="052",
                       **kwargs)
        stats["edges_added"] += 1

    # ── 1. Core HR / user master tables ──────────────────────────────────
    ensure_node("SAP_TABLE:HRP1000", "SAP_TABLE", "HRP1000",
                domain="HCM", layer="data",
                metadata={"purpose": "PD object header — OTYPE='RY' = BCM responsibility groups"})
    ensure_node("SAP_TABLE:HRP1001", "SAP_TABLE", "HRP1001",
                domain="HCM", layer="data",
                metadata={"purpose": "PD relationships — RELAT='007' SCLAS='P' = PERNR assignment"})
    ensure_node("SAP_TABLE:PA0002", "SAP_TABLE", "PA0002",
                domain="HCM", layer="data",
                metadata={"purpose": "HR personal data — VORNA/NACHN (name)"})
    ensure_node("SAP_TABLE:PA0105", "SAP_TABLE", "PA0105",
                domain="HCM", layer="data",
                metadata={"purpose": "HR communication — SUBTY='0001' USRID = SAP user, SUBTY='0010' USRID_LONG = email"})
    ensure_node("SAP_TABLE:USR02", "SAP_TABLE", "USR02",
                domain="BASIS", layer="data",
                metadata={"purpose": "SAP user master — BNAME, UFLAG (lock), GLTGV/GLTGB (validity)"})

    # ── 2. Transaction + workflow ─────────────────────────────────────────
    ensure_node("SAP_TRANSACTION:OOCU_RESP", "SAP_TRANSACTION", "OOCU_RESP",
                domain="Treasury", layer="operations",
                metadata={"purpose": "Organization & Responsibility — maintain BCM signatory groups"})
    ensure_node("WORKFLOW:90000003", "WORKFLOW", "90000003",
                domain="Treasury", layer="operations",
                metadata={"purpose": "BNK_BATCH_HEADER approval — resolves INI then COM rules"})

    # ── 3. BCM rules (workflow_rule) ─────────────────────────────────────
    ensure_node("WORKFLOW_RULE:BNK_COM_01_01_03", "WORKFLOW_RULE", "BNK_COM_01_01_03",
                domain="Treasury", layer="operations",
                metadata={"rule_number": "90000004",
                          "role": "COMMIT — final release (2nd signature)"})
    ensure_node("WORKFLOW_RULE:BNK_INI_01_01_04", "WORKFLOW_RULE", "BNK_INI_01_01_04",
                domain="Treasury", layer="operations",
                metadata={"rule_number": "90000005",
                          "role": "INITIATE / VALIDATION — 1st approval"})

    # ── 4. RY responsibility groups ───────────────────────────────────────
    for ry_id, stext in RY_GROUPS_COM.items():
        ensure_node(f"RY_GROUP:{ry_id}", "RY_GROUP", ry_id,
                    domain="Treasury", layer="operations",
                    metadata={"stext": stext, "rule": "90000004", "short": "BNK_01_01_03"})
    for ry_id, stext in RY_GROUPS_INI.items():
        ensure_node(f"RY_GROUP:{ry_id}", "RY_GROUP", ry_id,
                    domain="Treasury", layer="operations",
                    metadata={"stext": stext, "rule": "90000005", "short": "BNK_01_01_04"})

    # ── 5. Gold DB materialized tables ────────────────────────────────────
    ensure_node("GOLD_DB_TABLE:bcm_signatory_responsibility", "GOLD_DB_TABLE",
                "bcm_signatory_responsibility",
                domain="Treasury", layer="gold_db",
                metadata={"populated_by": "extract_bcm_signatories.py",
                          "snapshot_of": "HRP1000 OTYPE='RY' SHORT IN ('BNK_01_01_03','BNK_01_01_04')"})
    ensure_node("GOLD_DB_TABLE:bcm_signatory_assignment", "GOLD_DB_TABLE",
                "bcm_signatory_assignment",
                domain="Treasury", layer="gold_db",
                metadata={"populated_by": "extract_bcm_signatories.py",
                          "snapshot_of": "HRP1001 OTYPE='RY' RELAT='007' SCLAS='P' + PA0002 + PA0105"})

    # ── 6. Quality check + extraction scripts ─────────────────────────────
    ensure_node("SCRIPT:extract_bcm_signatories", "EXTRACTION_SCRIPT",
                "extract_bcm_signatories",
                domain="Treasury", layer="extraction",
                metadata={"path": "Zagentexecution/mcp-backend-server-python/extract_bcm_signatories.py",
                          "system": "P01", "access": "read-only via RFC_READ_TABLE"})
    ensure_node("SCRIPT:bcm_signatory_reconciliation_check", "QUALITY_CHECK_SCRIPT",
                "bcm_signatory_reconciliation_check",
                domain="Treasury", layer="quality",
                metadata={"path": "Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py",
                          "exit_0_meaning": "no ghost PERNR, no role-split, carton diff clean",
                          "exit_1_meaning": "at least one defect detected"})

    # ────────────────────────────────────────────────────────────────────
    # EDGES
    # ────────────────────────────────────────────────────────────────────

    # Transaction maintains core tables
    add_edge("SAP_TRANSACTION:OOCU_RESP", "SAP_TABLE:HRP1000", "MAINTAINS",
             label="OOCU_RESP maintains RY responsibility groups (HRP1000 OTYPE='RY')")
    add_edge("SAP_TRANSACTION:OOCU_RESP", "SAP_TABLE:HRP1001", "MAINTAINS",
             label="OOCU_RESP maintains RY -> Person assignments (HRP1001 RELAT='007' SCLAS='P')")

    # Workflow calls rules
    add_edge("WORKFLOW:90000003", "WORKFLOW_RULE:BNK_INI_01_01_04", "CALLS_RULE",
             label="90000003 resolves 90000005 (BNK_INI) for validators")
    add_edge("WORKFLOW:90000003", "WORKFLOW_RULE:BNK_COM_01_01_03", "CALLS_RULE",
             label="90000003 resolves 90000004 (BNK_COM) for committers")

    # Rules resolve to RY groups
    for ry_id in RY_GROUPS_COM:
        add_edge("WORKFLOW_RULE:BNK_COM_01_01_03", f"RY_GROUP:{ry_id}",
                 "RESOLVES_VIA",
                 label=f"BNK_COM resolves to {RY_GROUPS_COM[ry_id]}")
    for ry_id in RY_GROUPS_INI:
        add_edge("WORKFLOW_RULE:BNK_INI_01_01_04", f"RY_GROUP:{ry_id}",
                 "RESOLVES_VIA",
                 label=f"BNK_INI resolves to {RY_GROUPS_INI[ry_id]}")

    # RY groups stored in HRP1000/HRP1001
    for ry_id in list(RY_GROUPS_COM) + list(RY_GROUPS_INI):
        add_edge(f"RY_GROUP:{ry_id}", "SAP_TABLE:HRP1000", "STORED_IN",
                 label="RY object header row")
        add_edge(f"RY_GROUP:{ry_id}", "SAP_TABLE:HRP1001", "HAS_ASSIGNMENTS_IN",
                 label="RELAT='007' SCLAS='P' rows = PERNR assignments")

    # Lookalike trap — explicit edge (INC-000006313 Part 2 learning)
    add_edge("RY_GROUP:50010087", "RY_GROUP:50036801", "ADJACENT_TRAP_TO",
             label="IIEP Validation sits next to UIS Validation under rule 90000005 — DBS mis-clicked 2026-04-13")
    add_edge("RY_GROUP:50036801", "RY_GROUP:50010087", "ADJACENT_TRAP_TO",
             label="UIS Validation lookalike — distinguish only by RY OBJID (50036801 vs 50010087)")

    # PERNR resolution chain
    add_edge("SAP_TABLE:HRP1001", "SAP_TABLE:PA0002", "RESOLVES_PERNR_VIA",
             label="HRP1001.SOBID = PERNR -> PA0002.PERNR (name)")
    add_edge("SAP_TABLE:HRP1001", "SAP_TABLE:PA0105", "RESOLVES_PERNR_VIA",
             label="HRP1001.SOBID = PERNR -> PA0105.PERNR (SAP user + email)")
    add_edge("SAP_TABLE:PA0105", "SAP_TABLE:USR02", "RESOLVES_USER_VIA",
             label="PA0105 SUBTY='0001' USRID -> USR02.BNAME")

    # Extraction script
    for tbl in ["HRP1000", "HRP1001", "PA0002", "PA0105"]:
        add_edge("SCRIPT:extract_bcm_signatories", f"SAP_TABLE:{tbl}", "READS_TABLE",
                 label=f"extract_bcm_signatories reads {tbl}")
    add_edge("SCRIPT:extract_bcm_signatories",
             "GOLD_DB_TABLE:bcm_signatory_responsibility", "POPULATES",
             label="writes snapshot of the 24 RY groups")
    add_edge("SCRIPT:extract_bcm_signatories",
             "GOLD_DB_TABLE:bcm_signatory_assignment", "POPULATES",
             label="writes snapshot of the 255+ PERNR assignments with name/user/email")

    # Reconciliation check script
    add_edge("SCRIPT:bcm_signatory_reconciliation_check",
             "GOLD_DB_TABLE:bcm_signatory_assignment", "READS",
             label="consumes the materialized snapshot for ghost/role-split/carton diff")
    add_edge("SCRIPT:bcm_signatory_reconciliation_check",
             "SAP_TABLE:PA0105", "VALIDATES",
             label="check 1: SOBID must resolve to a non-empty PA0105/0001 USRID (ghost-PERNR detector)")

    # INC-000006313 affects RY groups
    inc_id = "INCIDENT:INC-000006313"
    if inc_id not in brain.G:
        brain.add_node(inc_id, "INCIDENT", "INC-000006313",
                       domain="Treasury", layer="operations",
                       source="bcm_domain_ingestor",
                       tags=["incident", "bcm", "closed_with_cleanup"])
        stats["nodes_added"] += 1
    add_edge(inc_id, "RY_GROUP:50010054", "AFFECTS",
             label="INC-000006313 added Said + cleanup on UIS Commit")
    add_edge(inc_id, "RY_GROUP:50036801", "AFFECTS",
             label="INC-000006313 added Said + cleanup on UIS Validation")
    add_edge(inc_id, "RY_GROUP:50010087", "NEAR_MISS_AFFECTED",
             label="DBS mis-added Svein to IIEP Validation before correction (caught 2026-04-13)")

    print(f"  [bcm_domain] +{stats['nodes_added']} nodes, "
          f"{stats['nodes_existed']} already existed, "
          f"+{stats['edges_added']} edges")
