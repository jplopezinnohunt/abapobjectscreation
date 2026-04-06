"""
Brain v2 Config Ingestor — Payment config, DMEE trees, house banks, BCM rules.
Source: BRAIN_V2_ARCHITECTURE.md Section B.2

Reads from Gold DB: T042Z, T042A, T012, T012K, BNK_BATCH_HEADER, T001
"""

import sqlite3

# Known DMEE tree -> BAdI exit class mappings (from extracted code analysis, Session #039)
DMEE_EXIT_MAP = {
    "/CGI_XML_CT_UNESCO":    "YCL_IDFI_CGI_DMEE_FR",
    "/CGI_XML_CT_UNESCO_1":  "YCL_IDFI_CGI_DMEE_FR",
    "/CGI_XML_CT_UNESCO_FB": "YCL_IDFI_CGI_DMEE_FALLBACK",
}


def ingest_config(brain, db_path: str):
    """Build config graph from payment and organizational tables."""
    conn = sqlite3.connect(db_path)
    stats = {'nodes': 0, 'edges': 0}

    _ingest_company_codes(brain, conn, stats)
    _ingest_dmee_trees(brain, conn, stats)
    _ingest_payment_methods(brain, conn, stats)
    _ingest_house_banks(brain, conn, stats)
    _ingest_bcm_rules(brain, conn, stats)
    _ingest_dmee_exit_links(brain, stats)

    conn.close()
    return stats


def _ingest_company_codes(brain, conn, stats):
    """T001 -> COMPANY_CODE nodes."""
    try:
        rows = conn.execute("""
            SELECT BUKRS, BUTXT, WAERS, LAND1
            FROM T001
            WHERE BUKRS IS NOT NULL AND BUKRS != ''
        """).fetchall()
        for bukrs, butxt, waers, land1 in rows:
            nid = f"COCODE:{bukrs}"
            brain.add_node(nid, "COMPANY_CODE", bukrs,
                           domain="FI", layer="org",
                           source="gold_db",
                           metadata={"name": butxt or "", "currency": waers or "",
                                     "country": land1 or ""})
            stats['nodes'] += 1
    except Exception:
        pass


def _ingest_dmee_trees(brain, conn, stats):
    """Build DMEE tree nodes from h18_dmee_trees.csv (Session #039 extraction from P01).
    Also use T042A to link payment methods to DMEE trees via known mappings."""
    # Try to load DMEE trees from the Session #039 CSV extraction
    import csv
    from pathlib import Path
    csv_path = Path("knowledge/domains/Payment/h18_dmee_trees.csv")
    if csv_path.exists():
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dtfor = row.get('DMESSION', row.get('FORMI', row.get('FORMAT', '')))
                if not dtfor:
                    continue
                tree_id = f"DMEE:{dtfor}"
                if not brain.has_node(tree_id):
                    brain.add_node(tree_id, "DMEE_TREE", dtfor,
                                   domain="FI", layer="config",
                                   source="session_039",
                                   metadata={k: v for k, v in row.items()})
                    stats['nodes'] += 1

    # Add known DMEE trees from architecture doc (hardcoded from Session #039 findings)
    KNOWN_TREES = [
        "/CGI_XML_CT_UNESCO", "/CGI_XML_CT_UNESCO_1",
        "/CGI_XML_CT_UNESCO_FB",
        "/CITI_XML_CT_UNESCO", "/CITI_XML_CT_UNESCO_DD",
        "/SEPA_CT_UNESCO",
    ]
    for dtfor in KNOWN_TREES:
        tree_id = f"DMEE:{dtfor}"
        if not brain.has_node(tree_id):
            brain.add_node(tree_id, "DMEE_TREE", dtfor,
                           domain="FI", layer="config",
                           source="session_039",
                           metadata={"format": dtfor})
            stats['nodes'] += 1

    # Create payment method nodes from T042A (which HAS ZBUKR + ZLSCH)
    # and link them to company codes
    try:
        rows = conn.execute("""
            SELECT ZBUKR, ZLSCH, HBKID
            FROM T042A
            WHERE ZBUKR IS NOT NULL AND ZLSCH IS NOT NULL
        """).fetchall()
    except Exception:
        return

    for zbukr, zlsch, hbkid in rows:
        pm_id = f"PAYMETHOD:{zbukr}:{zlsch}"
        if not brain.has_node(pm_id):
            brain.add_node(pm_id, "PAYMENT_METHOD", f"{zbukr}-{zlsch}",
                           domain="FI", layer="config", source="gold_db",
                           metadata={"bukrs": zbukr, "zlsch": zlsch})
            stats['nodes'] += 1

        # Link to company code
        cc_id = f"COCODE:{zbukr}"
        if brain.has_node(cc_id):
            brain.add_edge(pm_id, cc_id, "BELONGS_TO",
                           label=f"Payment method {zlsch} belongs to {zbukr}",
                           evidence="config", confidence=1.0,
                           discovered_in="040")
            stats['edges'] += 1


def _ingest_payment_methods(brain, conn, stats):
    """T042A -> PAYMENT_METHOD -> HOUSE_BANK routing."""
    try:
        rows = conn.execute("""
            SELECT ZBUKR, ZLSCH, HBKID, HKTID
            FROM T042A
            WHERE HBKID IS NOT NULL AND HBKID != ''
        """).fetchall()
    except Exception:
        return

    for zbukr, zlsch, hbkid, hktid in rows:
        pm_id = f"PAYMETHOD:{zbukr}:{zlsch}"
        if not brain.has_node(pm_id):
            brain.add_node(pm_id, "PAYMENT_METHOD", f"{zbukr}-{zlsch}",
                           domain="FI", layer="config", source="gold_db",
                           metadata={"bukrs": zbukr, "zlsch": zlsch})
            stats['nodes'] += 1

        bank_id = f"HOUSEBANK:{zbukr}:{hbkid}"
        if not brain.has_node(bank_id):
            brain.add_node(bank_id, "HOUSE_BANK", f"{zbukr}/{hbkid}",
                           domain="FI", layer="config", source="gold_db",
                           metadata={"bukrs": zbukr, "hbkid": hbkid,
                                     "hktid": hktid or ""})
            stats['nodes'] += 1

        brain.add_edge(pm_id, bank_id, "ROUTES_TO_BANK",
                       label=f"{zlsch} -> {hbkid}/{hktid}",
                       evidence="config", confidence=1.0,
                       discovered_in="040")
        stats['edges'] += 1


def _ingest_house_banks(brain, conn, stats):
    """T012/T012K -> HOUSE_BANK enrichment."""
    try:
        rows = conn.execute("""
            SELECT BUKRS, HBKID, BANKL, BANKS
            FROM T012
        """).fetchall()
        for bukrs, hbkid, bankl, banks in rows:
            bank_id = f"HOUSEBANK:{bukrs}:{hbkid}"
            if brain.has_node(bank_id):
                meta = brain.nodes[bank_id].get("metadata", {})
                meta["bank_key"] = bankl or ""
                meta["country"] = banks or ""
                brain.nodes[bank_id]["metadata"] = meta
    except Exception:
        pass


def _ingest_bcm_rules(brain, conn, stats):
    """BNK_BATCH_HEADER -> BCM_RULE nodes."""
    try:
        # Check what columns exist
        cols = [r[1] for r in conn.execute("PRAGMA table_info(BNK_BATCH_HEADER)").fetchall()]
    except Exception:
        return

    # Find grouping rule column
    rule_col = None
    for candidate in ['GROUPING_RULE', 'GRPRULE', 'GRP_RULE', 'BATCH_TYPE']:
        if candidate in cols:
            rule_col = candidate
            break

    if not rule_col:
        return

    try:
        rows = conn.execute(f"""
            SELECT {rule_col}, COUNT(*) as cnt
            FROM BNK_BATCH_HEADER
            WHERE {rule_col} IS NOT NULL AND {rule_col} != ''
            GROUP BY {rule_col}
        """).fetchall()
    except Exception:
        return

    for rule, cnt in rows:
        rule_id = f"BCM:{rule}"
        brain.add_node(rule_id, "BCM_RULE", rule,
                       domain="FI", layer="config", source="gold_db",
                       metadata={"batch_count": cnt})
        stats['nodes'] += 1


def _ingest_dmee_exit_links(brain, stats):
    """Link DMEE trees to their BAdI exit classes (known mappings)."""
    for dtfor, cls_name in DMEE_EXIT_MAP.items():
        tree_id = f"DMEE:{dtfor}"
        cls_id = f"CLASS:{cls_name}"
        if brain.has_node(tree_id):
            brain.add_edge(tree_id, cls_id, "CONFIGURES_FORMAT",
                           label=f"DMEE {dtfor} processed by {cls_name}",
                           evidence="manual", confidence=0.9,
                           discovered_in="039")
            stats['edges'] += 1
