"""
Brain v2 Domain Knowledge Ingestor — Manual behavioral edges from expert analysis.

These are dependencies the ABAP parser CAN'T find via static analysis because
the data flows through method parameters (BAdI interfaces), configuration tables,
or runtime-determined paths.

Source: Session #039 H18 findings, payment companion analysis, domain expertise.
"""


def ingest_domain_knowledge(brain):
    """Add expert-verified behavioral edges that static analysis misses."""
    stats = {'nodes': 0, 'edges': 0}

    _ingest_dmee_badi_chain(brain, stats)
    _ingest_payment_table_chain(brain, stats)
    _ingest_process_table_links(brain, stats)
    _ingest_bank_statement_chain(brain, stats)
    _ingest_clearing_chain(brain, stats)

    return stats


def _ensure_node(brain, node_id, node_type, name, domain="FI", layer="data",
                 stats=None, **kwargs):
    """Create a node if it doesn't exist."""
    if not brain.has_node(node_id):
        brain.add_node(node_id, node_type, name,
                       domain=domain, layer=layer, source="domain_knowledge",
                       **kwargs)
        if stats:
            stats['nodes'] += 1


def _add_edge(brain, from_id, to_id, edge_type, label="", stats=None, **kwargs):
    """Add an edge with domain_knowledge evidence."""
    brain.add_edge(from_id, to_id, edge_type, label=label,
                   evidence="domain_knowledge", confidence=0.95,
                   discovered_in="041", **kwargs)
    if stats:
        stats['edges'] += 1


def _ingest_dmee_badi_chain(brain, stats):
    """DMEE BAdI classes receive FPAYP, REGUH, T042Z, PAYR as method parameters.

    The parser finds IMPLEMENTS_INTF but can't see that the BAdI framework
    passes these structures. We know from Session #039:
    - FI_CGI_DMEE_EXIT_W_BADI passes I_FPAYP (type FPAYP), I_REGUH (type REGUH)
    - The exit methods read FPAYP-XREF3, FPAYP-SGTXT, FPAYP-LZBKZ, REGUH-VBLNR, etc.
    - The classes also read T042Z, T012, T012K, PAYR for configuration lookups
    """
    DMEE_CLASSES = [
        "YCL_IDFI_CGI_DMEE_FR",
        "YCL_IDFI_CGI_DMEE_FALLBACK",
        "YCL_IDFI_CGI_DMEE_UTIL",
    ]

    # Tables these classes access (via parameters + internal reads)
    DMEE_TABLE_ACCESS = {
        "FPAYP": ["XREF3", "SGTXT", "LZBKZ", "ORIGIN", "STRFR"],
        "REGUH": ["VBLNR", "LIFNR", "ZBUKR", "ZLSCH", "UBNKL"],
        "T042Z": ["DTFOR", "ZBUKR", "ZLSCH"],
        "T012": ["HBKID", "BANKL", "BANKS"],
        "T012K": ["HKTID", "UKONT"],
        "PAYR": ["VBLNR", "ZBUKR"],
    }

    for cls_name in DMEE_CLASSES:
        cls_id = f"CLASS:{cls_name}"
        if not brain.has_node(cls_id):
            continue

        for table, fields in DMEE_TABLE_ACCESS.items():
            tbl_id = f"SAP_TABLE:{table}"
            _ensure_node(brain, tbl_id, "SAP_TABLE", table, stats=stats)

            _add_edge(brain, cls_id, tbl_id, "READS_TABLE",
                      label=f"{cls_name} reads {table} (via BAdI params)",
                      stats=stats)

            for field in fields:
                field_id = f"FIELD:{table}.{field}"
                _ensure_node(brain, field_id, "TABLE_FIELD", f"{table}.{field}",
                             stats=stats, metadata={"table": table, "field": field})
                _add_edge(brain, cls_id, field_id, "READS_FIELD",
                          label=f"{cls_name} reads {table}.{field}",
                          stats=stats)

    # FM calls from DMEE classes (known from source analysis)
    DMEE_FM_CALLS = {
        "YCL_IDFI_CGI_DMEE_FR": [
            "FI_CGI_DMEE_GET_PAYEE_DATA",
            "CONVERSION_EXIT_ALPHA_OUTPUT",
        ],
        "YCL_IDFI_CGI_DMEE_FALLBACK": [
            "FI_CGI_DMEE_GET_PAYEE_DATA",
        ],
    }

    for cls_name, fms in DMEE_FM_CALLS.items():
        cls_id = f"CLASS:{cls_name}"
        if not brain.has_node(cls_id):
            continue
        for fm in fms:
            fm_id = f"FM:{fm}"
            _ensure_node(brain, fm_id, "FUNCTION_MODULE", fm,
                         domain="FI", layer="code", stats=stats)
            _add_edge(brain, cls_id, fm_id, "CALLS_FM",
                      label=f"{cls_name} calls {fm}", stats=stats)


def _ingest_payment_table_chain(brain, stats):
    """Key table relationships in the payment domain.

    These are the critical data flows that make the payment impact chain work:
    FPAYP (payment proposal) → REGUH (payment header) → BKPF (FI doc header)
    """
    # Ensure key payment tables exist as nodes
    PAYMENT_TABLES = {
        "FPAYP": ("FI", "Payment proposal line item"),
        "REGUH": ("FI", "Payment document header"),
        "REGUP": ("FI", "Payment document item"),
        "BKPF": ("FI", "Accounting document header"),
        "BSEG": ("FI", "Accounting document line item"),
        "PAYR": ("FI", "Payment check data"),
        "BNK_BATCH_HEADER": ("FI", "BCM batch header"),
        "BNK_BATCH_ITEM": ("FI", "BCM batch item"),
        "FEBEP": ("FI", "Electronic bank statement item"),
        "FEBKO": ("FI", "Electronic bank statement header"),
    }

    for table, (domain, desc) in PAYMENT_TABLES.items():
        tbl_id = f"SAP_TABLE:{table}"
        _ensure_node(brain, tbl_id, "SAP_TABLE", table,
                     domain=domain, stats=stats,
                     metadata={"description": desc})

    # Key join relationships in the payment chain
    PAYMENT_JOINS = [
        ("REGUH", "BKPF", "VBLNR→BELNR", "JOINS_VIA"),
        ("FPAYP", "REGUH", "LAUFD+LAUFI+ZBUKR", "JOINS_VIA"),
        ("REGUH", "REGUP", "LAUFD+LAUFI+ZBUKR+VBLNR", "JOINS_VIA"),
        ("REGUH", "PAYR", "ZBUKR+VBLNR", "JOINS_VIA"),
        ("BNK_BATCH_HEADER", "BNK_BATCH_ITEM", "BATCH_ID", "JOINS_VIA"),
        ("FEBKO", "FEBEP", "KUKEY", "JOINS_VIA"),
    ]

    for from_tbl, to_tbl, join_key, edge_type in PAYMENT_JOINS:
        from_id = f"SAP_TABLE:{from_tbl}"
        to_id = f"SAP_TABLE:{to_tbl}"
        _add_edge(brain, from_id, to_id, edge_type,
                  label=f"{from_tbl} → {to_tbl} via {join_key}", stats=stats)


def _ingest_process_table_links(brain, stats):
    """Link process steps to the tables they read/write.

    This connects the process overlay to the data layer, enabling
    impact queries like "if I change FPAYP, which process steps break?"
    """
    # Map key tables to the process steps that use them
    TABLE_PROCESS_LINKS = [
        ("SAP_TABLE:FPAYP", "STEP:Payment_E2E:Payment_Proposal"),
        ("SAP_TABLE:FPAYP", "STEP:Payment_E2E:Payment_Execution"),
        ("SAP_TABLE:REGUH", "STEP:Payment_E2E:Payment_Execution"),
        ("SAP_TABLE:BNK_BATCH_HEADER", "STEP:Payment_E2E:BCM_Batch_Created"),
        ("SAP_TABLE:BNK_BATCH_HEADER", "STEP:Payment_E2E:BCM_Approved"),
        ("SAP_TABLE:BNK_BATCH_ITEM", "STEP:Payment_E2E:Bank_File_Sent"),
        ("SAP_TABLE:FEBEP", "STEP:Payment_E2E:Bank_Confirmed"),
    ]

    for table_id, step_id in TABLE_PROCESS_LINKS:
        if brain.has_node(step_id):
            _add_edge(brain, step_id, table_id, "STEP_READS",
                      label=f"Process step reads {table_id.split(':')[1]}",
                      stats=stats)


def _ingest_bank_statement_chain(brain, stats):
    """E2E bank statement flow: MT940 import → EBS posting → clearing → reconciliation.

    Source: Session #029-#030 bank statement deep dive.
    Architecture: knowledge/domains/FI/bank_statement_ebs_architecture.md

    Flow:
    1. MT940 file → RFEBKA00 (import program) → FEBKO (statement header) + FEBEP (items)
    2. FEBEP items → EBS posting rules (T028G/T028B/T028D) → BKPF+BSIS (FI documents)
    3. BSIS items → auto-clearing (RFEBKA30/F.13) → BSAS (cleared items)
    4. FEBRE (raw MT940 text) linked to FEBEP via KUKEY+ESNUM

    Account structure:
    - 10xxxxx (T012K.HKONT) = bank main GL (permanent ledger)
    - 11xxxxx (T012K.UKONT) = bank sub-account (clearing/reconciliation)
    """
    # Bank statement config tables
    BS_CONFIG = {
        "T028G": ("FI", "EBS posting rule — external→internal transaction mapping"),
        "T028B": ("FI", "EBS bank account assignment — bank→GL account"),
        "T028D": ("FI", "EBS internal transaction types"),
        "T028E": ("FI", "EBS transaction type texts"),
        "FEBRE": ("FI", "Electronic bank statement raw text (MT940 tag 86)"),
        "YBASUBST": ("FI", "UNESCO custom BA substitution — BUKRS+BLART→GSBER"),
        "YTFI_BA_SUBST": ("FI", "UNESCO custom BA substitution ranges"),
    }

    for table, (domain, desc) in BS_CONFIG.items():
        tbl_id = f"SAP_TABLE:{table}"
        _ensure_node(brain, tbl_id, "SAP_TABLE", table,
                     domain=domain, stats=stats, metadata={"description": desc})

    # Bank statement data chain (E2E)
    BS_JOINS = [
        # MT940 raw → statement items
        ("FEBRE", "FEBEP", "KUKEY+ESNUM", "Raw text links to posted item"),
        # Statement header → config
        ("FEBKO", "T012K", "HBKID+HKTID→HBKID+HKTID", "Statement header links to bank account"),
        ("FEBKO", "T012", "HBKID→HBKID", "Statement header links to house bank master"),
        # Posting rule chain
        ("FEBEP", "T028G", "VGEXT→VGEXT+VGTYP", "Statement item uses posting rule"),
        ("T028G", "T028D", "VGINT→VGINT", "Posting rule maps to internal transaction"),
        ("T028G", "T028B", "via VGINT", "Posting rule links to bank account assignment"),
        # EBS → FI posting
        ("FEBEP", "BKPF", "BELNR+GJAHR→BELNR+GJAHR", "Statement item creates FI document"),
        # FI posted items
        ("BKPF", "BSIS", "BELNR+GJAHR+BUKRS", "FI doc header → open items"),
        # Clearing
        ("BSIS", "BSAS", "AUGBL→BELNR", "Open item → cleared by clearing doc"),
        # Bank account GL
        ("T012K", "T028B", "HKONT→BNKKO", "Bank account GL maps to posting config"),
    ]

    for from_tbl, to_tbl, join_key, desc in BS_JOINS:
        from_id = f"SAP_TABLE:{from_tbl}"
        to_id = f"SAP_TABLE:{to_tbl}"
        _ensure_node(brain, from_id, "SAP_TABLE", from_tbl, stats=stats)
        _ensure_node(brain, to_id, "SAP_TABLE", to_tbl, stats=stats)
        _add_edge(brain, from_id, to_id, "JOINS_VIA",
                  label=f"{from_tbl}→{to_tbl}: {desc}", stats=stats)

    # Key bank statement fields for impact analysis
    BS_FIELDS = {
        "FEBEP": ["KUKEY", "ESNUM", "ESTAT", "BELNR", "GJAHR", "BUDAT",
                  "KWBTR", "VGEXT", "VGINT", "KWAER", "FWBTR", "AVKON", "AVKOA"],
        "FEBKO": ["KUKEY", "HBKID", "HKTID", "BUKRS", "HKONT", "EFART", "WAERS"],
        "FEBRE": ["KUKEY", "ESNUM", "VWEZW"],
        "T028G": ["VGTYP", "VGEXT", "VGINT", "VGSAP", "PFORM"],
        "T028B": ["BUKRS", "BANKL", "KTONR", "BNKKO", "VGTYP"],
        "T012K": ["BUKRS", "HBKID", "HKTID", "HKONT", "BANKN", "WAERS"],
    }

    for table, fields in BS_FIELDS.items():
        tbl_id = f"SAP_TABLE:{table}"
        for field in fields:
            field_id = f"FIELD:{table}.{field}"
            _ensure_node(brain, field_id, "TABLE_FIELD", f"{table}.{field}",
                         stats=stats, metadata={"table": table, "field": field})
            _add_edge(brain, tbl_id, field_id, "FIELD_MAPS_TO",
                      label=f"{table} contains {field}", stats=stats)

    # Programs that drive bank statement processing
    BS_PROGRAMS = [
        ("RFEBKA00", "Bank statement import (MT940/SWIFT)"),
        ("RFEBKA30", "Bank statement auto-clearing"),
        ("RFEBKORD", "Bank statement reprocessing"),
    ]
    for prog, desc in BS_PROGRAMS:
        prog_id = f"REPORT:{prog}"
        _ensure_node(brain, prog_id, "ABAP_REPORT", prog,
                     domain="FI", layer="code", stats=stats,
                     metadata={"description": desc})
        # These programs read/write FEBEP and FEBKO
        _add_edge(brain, prog_id, f"SAP_TABLE:FEBEP", "WRITES_TABLE",
                  label=f"{prog} writes FEBEP", stats=stats)
        _add_edge(brain, prog_id, f"SAP_TABLE:FEBKO", "READS_TABLE",
                  label=f"{prog} reads FEBKO", stats=stats)
        if prog == "RFEBKA00":
            _add_edge(brain, prog_id, f"SAP_TABLE:FEBRE", "WRITES_TABLE",
                      label=f"{prog} writes FEBRE (raw MT940)", stats=stats)
        if prog in ("RFEBKA30",):
            _add_edge(brain, prog_id, f"SAP_TABLE:BSIS", "READS_TABLE",
                      label=f"{prog} reads BSIS for clearing", stats=stats)
            _add_edge(brain, prog_id, f"SAP_TABLE:BSAS", "WRITES_TABLE",
                      label=f"{prog} writes BSAS (cleared)", stats=stats)


def _ingest_clearing_chain(brain, stats):
    """Clearing relationships: how open items become cleared items.

    Source: Golden Query design, Session #016+#030.

    Open items (BSIS/BSIK/BSID) move to cleared (BSAS/BSAK/BSAD) when cleared.
    Key field: AUGBL (clearing document), AUGDT (clearing date).
    The bseg_union VIEW unifies all 6 tables.
    """
    CLEARING_PAIRS = [
        ("BSIS", "BSAS", "GL open → GL cleared"),
        ("BSIK", "BSAK", "Vendor open → Vendor cleared"),
        ("BSID", "BSAD", "Customer open → Customer cleared"),
    ]

    for open_tbl, clear_tbl, desc in CLEARING_PAIRS:
        open_id = f"SAP_TABLE:{open_tbl}"
        clear_id = f"SAP_TABLE:{clear_tbl}"
        _ensure_node(brain, open_id, "SAP_TABLE", open_tbl,
                     domain="FI", stats=stats)
        _ensure_node(brain, clear_id, "SAP_TABLE", clear_tbl,
                     domain="FI", stats=stats)
        _add_edge(brain, open_id, clear_id, "JOINS_VIA",
                  label=f"{desc} via AUGBL+AUGDT", stats=stats)

    # Golden Query chain: FMIFIIT → BKPF → bseg_union → PRPS
    GQ_JOINS = [
        ("FMIFIIT", "BKPF", "KNBELNR→BELNR + KNGJAHR→GJAHR + BUKRS",
         "FM→FI bridge (Golden Query core join)"),
        ("BKPF", "BSIS", "BELNR+GJAHR+BUKRS",
         "FI header → GL line items"),
        ("FMIFIIT", "PRPS", "OBJNRZ→OBJNR",
         "FM commitment → WBS element (85.9% coverage)"),
    ]

    for from_tbl, to_tbl, join_key, desc in GQ_JOINS:
        from_id = f"SAP_TABLE:{from_tbl}"
        to_id = f"SAP_TABLE:{to_tbl}"
        _ensure_node(brain, from_id, "SAP_TABLE", from_tbl, domain="FI", stats=stats)
        _ensure_node(brain, to_id, "SAP_TABLE", to_tbl, domain="FI", stats=stats)
        _add_edge(brain, from_id, to_id, "JOINS_VIA",
                  label=f"{from_tbl}→{to_tbl}: {desc}", stats=stats)
