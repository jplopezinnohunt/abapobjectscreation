"""
Brain v2 Integration Ingestor — RFC destinations, IDocs, .NET apps, ICF services.
Source: BRAIN_V2_ARCHITECTURE.md Section B.4

Reads from Gold DB: rfcdes, edidc, tfdir_custom, icfservice
"""

import sqlite3


# Known .NET application -> FM mappings (from Session #032 discovery)
DOTNET_APP_FM_MAP = {
    "SISTER":       {"fm_count": 47, "domain": "FI",
                     "fms_known": ["Z_RFC_READ_FUND_DATA", "Z_RFC_BUDGET_TRANSFER"]},
    "HR_Workflow":   {"fm_count": 87, "domain": "HCM",
                      "fms_known": ["Z_HR_GET_EMPLOYEE", "Z_HR_CREATE_INFOTYPE"]},
    "CMT":           {"fm_count": 44, "domain": "MM",
                      "fms_known": ["Z_RFC_VENDOR_CREATE", "Z_RFC_VENDOR_CHANGE"]},
    "UBO_Field":     {"fm_count": 15, "domain": "FI",
                      "fms_known": ["Z_RFC_FI_POST", "Z_RFC_FM_COMMITMENT"]},
    "Travel":        {"fm_count": 21, "domain": "TV",
                      "fms_known": ["Z_RFC_TRIP_CREATE", "Z_RFC_DSA_RATES"]},
    "Mouv":          {"fm_count": 12, "domain": "AM",
                      "fms_known": ["Z_RFC_ASSET_TRANSFER"]},
    "Procurement":   {"fm_count": 13, "domain": "MM",
                      "fms_known": ["Z_RFC_PO_RELEASE", "Z_RFC_GR_POST"]},
}

# Known middleware integrations
MIDDLEWARE_MAP = {
    "MuleSoft":       {"targets": ["Core_Manager", "Core_Planner"],
                       "protocol": "RFC + IDoc (PROJECT02)"},
    "BizTalk":        {"targets": ["SuccessFactors_EC"],
                       "protocol": "HTTP/ICF"},
}

# Known external bank systems
BANK_SYSTEMS = {
    "SocGen_CGI":     {"protocol": "SWIFT/pain.001", "domain": "FI"},
    "Citibank":       {"protocol": "Proprietary XML", "domain": "FI"},
}


def ingest_integration(brain, db_path: str):
    """Build integration edges from RFC, IDocs, .NET apps, and external systems."""
    conn = sqlite3.connect(db_path)
    stats = {'nodes': 0, 'edges': 0}

    _ingest_rfc_destinations(brain, conn, stats)
    _ingest_rfc_enabled_fms(brain, conn, stats)
    _ingest_dotnet_apps(brain, stats)
    _ingest_middleware(brain, stats)
    _ingest_bank_systems(brain, stats)
    _ingest_idocs(brain, conn, stats)

    conn.close()
    return stats


def _ingest_rfc_destinations(brain, conn, stats):
    """RFCDES -> RFC_DESTINATION + SAP_SYSTEM nodes."""
    try:
        rows = conn.execute("""
            SELECT RFCDEST, RFCTYPE, RFCHOST, RFCSYSID, RFCCLIENT
            FROM rfcdes
            WHERE RFCDEST IS NOT NULL
        """).fetchall()
    except Exception:
        return

    for dest, rfctype, host, sysid, client in rows:
        dest_id = f"RFC:{dest}"
        brain.add_node(dest_id, "RFC_DESTINATION", dest,
                       domain="BASIS", layer="integration",
                       source="gold_db",
                       metadata={"type": rfctype or "", "host": host or "",
                                 "sysid": sysid or "", "client": client or ""})
        stats['nodes'] += 1

        if sysid and sysid.strip():
            sys_id = f"SYSTEM:{sysid.strip()}"
            if not brain.has_node(sys_id):
                brain.add_node(sys_id, "SAP_SYSTEM", sysid.strip(),
                               domain="BASIS", layer="integration",
                               source="gold_db")
                stats['nodes'] += 1
            brain.add_edge(dest_id, sys_id, "CALLS_SYSTEM",
                           evidence="config", confidence=1.0,
                           discovered_in="040")
            stats['edges'] += 1


def _ingest_rfc_enabled_fms(brain, conn, stats):
    """TFDIR_CUSTOM -> mark FMs as RFC-enabled + EXPOSES_FM edges."""
    try:
        rows = conn.execute("""
            SELECT FUNCNAME, PNAME
            FROM tfdir_custom
            WHERE (FUNCNAME LIKE 'Z%' OR FUNCNAME LIKE 'Y%')
        """).fetchall()
    except Exception:
        return

    for funcname, pname in rows:
        fm_id = f"FM:{funcname}"
        if not brain.has_node(fm_id):
            brain.add_node(fm_id, "FUNCTION_MODULE", funcname,
                           domain="CUSTOM", layer="code",
                           source="gold_db",
                           metadata={"fugr": pname or "", "rfc_enabled": True})
            stats['nodes'] += 1
        else:
            brain.nodes[fm_id]["metadata"]["rfc_enabled"] = True
            if pname:
                brain.nodes[fm_id]["metadata"]["fugr"] = pname

        # P01 exposes this FM to external callers
        sys_id = "SYSTEM:P01"
        if not brain.has_node(sys_id):
            brain.add_node(sys_id, "SAP_SYSTEM", "P01",
                           domain="BASIS", layer="integration", source="gold_db")
            stats['nodes'] += 1
        brain.add_edge(sys_id, fm_id, "EXPOSES_FM",
                       evidence="config", confidence=1.0,
                       discovered_in="040")
        stats['edges'] += 1


def _ingest_dotnet_apps(brain, stats):
    """.NET application -> FM edges (known mappings from Session #032)."""
    for app_name, app_info in DOTNET_APP_FM_MAP.items():
        app_id = f"EXTERNAL:{app_name}"
        brain.add_node(app_id, "EXTERNAL_SYSTEM", app_name,
                       domain=app_info["domain"], layer="integration",
                       source="session_032",
                       metadata={"fm_count": app_info["fm_count"],
                                 "protocol": ".NET RFC"})
        stats['nodes'] += 1

        for fm_name in app_info.get("fms_known", []):
            fm_id = f"FM:{fm_name}"
            if not brain.has_node(fm_id):
                brain.add_node(fm_id, "FUNCTION_MODULE", fm_name,
                               domain=app_info["domain"], layer="code",
                               source="inferred",
                               metadata={"rfc_enabled": True})
                stats['nodes'] += 1
            brain.add_edge(app_id, fm_id, "CALLS_VIA_RFC",
                           label=f"{app_name} calls {fm_name}",
                           evidence="manual", confidence=0.8,
                           discovered_in="032")
            stats['edges'] += 1


def _ingest_middleware(brain, stats):
    """MuleSoft, BizTalk -> target system edges."""
    for mw_name, mw_info in MIDDLEWARE_MAP.items():
        mw_id = f"EXTERNAL:{mw_name}"
        brain.add_node(mw_id, "EXTERNAL_SYSTEM", mw_name,
                       domain="BASIS", layer="integration",
                       source="session_032",
                       metadata={"protocol": mw_info["protocol"]})
        stats['nodes'] += 1

        for target in mw_info["targets"]:
            target_id = f"EXTERNAL:{target}"
            if not brain.has_node(target_id):
                brain.add_node(target_id, "EXTERNAL_SYSTEM", target,
                               domain="BASIS", layer="integration",
                               source="inferred")
                stats['nodes'] += 1
            brain.add_edge(mw_id, target_id, "CALLS_SYSTEM",
                           label=f"{mw_name} -> {target}",
                           evidence="manual", confidence=0.8,
                           discovered_in="032")
            stats['edges'] += 1


def _ingest_bank_systems(brain, stats):
    """External banking systems."""
    for bank_name, bank_info in BANK_SYSTEMS.items():
        bank_id = f"EXTERNAL:{bank_name}"
        brain.add_node(bank_id, "EXTERNAL_SYSTEM", bank_name,
                       domain=bank_info["domain"], layer="integration",
                       source="session_032",
                       metadata={"protocol": bank_info["protocol"]})
        stats['nodes'] += 1


def _ingest_idocs(brain, conn, stats):
    """EDIDC -> IDoc type nodes + SENDS_IDOC edges."""
    try:
        rows = conn.execute("""
            SELECT MESTYP, SNDPRT, SNDPRN, RCVPRT, RCVPRN, COUNT(*) as cnt
            FROM edidc
            WHERE MESTYP IS NOT NULL AND MESTYP != ''
            GROUP BY MESTYP, SNDPRT, SNDPRN, RCVPRT, RCVPRN
        """).fetchall()
    except Exception:
        return

    for mestyp, sndprt, sndprn, rcvprt, rcvprn, cnt in rows:
        idoc_id = f"IDOC:{mestyp}"
        if not brain.has_node(idoc_id):
            brain.add_node(idoc_id, "IDOC_TYPE", mestyp,
                           domain="BASIS", layer="integration",
                           source="gold_db",
                           metadata={"total_count": 0})
            stats['nodes'] += 1

        brain.nodes[idoc_id]["metadata"]["total_count"] = \
            brain.nodes[idoc_id]["metadata"].get("total_count", 0) + cnt

        # Edge from sender to IDoc
        if sndprn and sndprn.strip():
            sender_id = f"SYSTEM:{sndprn.strip()}"
            if not brain.has_node(sender_id):
                brain.add_node(sender_id, "SAP_SYSTEM", sndprn.strip(),
                               domain="BASIS", layer="integration", source="gold_db")
                stats['nodes'] += 1
            brain.add_edge(sender_id, idoc_id, "SENDS_IDOC",
                           label=f"{sndprn} sends {mestyp} ({cnt} docs)",
                           evidence="config", confidence=1.0,
                           discovered_in="040")
            stats['edges'] += 1
