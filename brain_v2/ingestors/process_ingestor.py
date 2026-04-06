"""
Brain v2 Process Ingestor — Process mining definitions as graph overlay.
Source: BRAIN_V2_ARCHITECTURE.md Section B.3

Adds PROCESS -> PROCESS_STEP -> SAP_TABLE linkages for proven UNESCO processes.
"""


# UNESCO's proven processes with their table footprints (from process mining sessions)
PROCESS_DEFINITIONS = {
    "P2P": {
        "name": "Procure to Pay",
        "domain": "MM",
        "steps": [
            {"name": "PR Created",       "tables": ["EBAN"],                    "tcodes": ["ME51N"]},
            {"name": "PR Released",       "tables": ["EBAN"],                    "tcodes": ["ME54N"]},
            {"name": "PO Created",        "tables": ["EKKO", "EKPO"],           "tcodes": ["ME21N"]},
            {"name": "PO Released",       "tables": ["EKKO"],                    "tcodes": ["ME29N"]},
            {"name": "GR Posted",         "tables": ["EKBE", "BKPF"],           "tcodes": ["MIGO"]},
            {"name": "SES Created",       "tables": ["ESSR", "ESLL"],           "tcodes": ["ML81N"]},
            {"name": "SES Released",      "tables": ["ESSR"],                    "tcodes": ["ML81N"]},
            {"name": "Invoice Posted",    "tables": ["RBKP", "RSEG", "BKPF"],  "tcodes": ["MIRO"]},
            {"name": "Invoice Verified",  "tables": ["RBKP"],                    "tcodes": ["MRBR"]},
            {"name": "Payment Run",       "tables": ["REGUH", "T042A"],         "tcodes": ["F110"]},
        ],
        "volume": {"events": 848000, "source": "p2p_process_mining.py"},
    },
    "Payment_E2E": {
        "name": "Payment End-to-End",
        "domain": "FI",
        "steps": [
            {"name": "Invoice Received",  "tables": ["RBKP", "BKPF"],          "tcodes": ["MIRO", "FB60"]},
            {"name": "Payment Proposal",  "tables": ["REGUH"],                   "tcodes": ["F110"]},
            {"name": "Payment Execution", "tables": ["REGUH", "BKPF", "PAYR"], "tcodes": ["F110"]},
            {"name": "BCM Batch Created", "tables": ["BNK_BATCH_HEADER"],       "tcodes": ["BNK_MONI"]},
            {"name": "BCM Approved",      "tables": ["BNK_BATCH_HEADER"],       "tcodes": ["BNK_MONI"]},
            {"name": "Bank File Sent",    "tables": ["BNK_BATCH_ITEM"],         "tcodes": ["BNK_MONI"]},
            {"name": "Bank Confirmed",    "tables": ["FEBEP"],                   "tcodes": ["FF_5"]},
        ],
        "volume": {"events": 1400000, "cases": 550000, "source": "payment_event_log.csv"},
    },
    "Bank_Statement": {
        "name": "Bank Statement Processing",
        "domain": "FI",
        "steps": [
            {"name": "Statement Imported", "tables": ["FEBKO"],                  "tcodes": ["FF_5"]},
            {"name": "Items Posted",       "tables": ["FEBEP", "BKPF"],         "tcodes": ["FEBAN"]},
            {"name": "Items Cleared",      "tables": ["FEBEP"],                  "tcodes": ["FEBAN"]},
            {"name": "Reconciled",         "tables": ["FEBRE"],                  "tcodes": ["FEBAN"]},
        ],
        "volume": {"events": 263000, "source": "bank_statement_ebs_companion.html"},
    },
    "B2R": {
        "name": "Budget to Report",
        "domain": "PSM",
        "steps": [
            {"name": "Budget Allocated",   "tables": ["FMIFIIT", "FMBH"],       "tcodes": ["FMBB"]},
            {"name": "Funds Reserved",     "tables": ["FMIFIIT"],               "tcodes": ["FMX1"]},
            {"name": "Commitment Created", "tables": ["FMIFIIT", "EKKO"],       "tcodes": ["ME21N"]},
            {"name": "Actual Posted",      "tables": ["FMIFIIT", "BKPF"],       "tcodes": ["FB60", "MIRO"]},
            {"name": "Carry Forward",      "tables": ["FMIFIIT"],               "tcodes": ["FMCF"]},
        ],
        "volume": {"source": "fmifiit analysis"},
    },
    "H2R": {
        "name": "Hire to Retire",
        "domain": "HCM",
        "steps": [
            {"name": "Employee Hired",     "tables": ["PA0000", "PA0001"],       "tcodes": ["PA30"]},
            {"name": "Payroll Run",        "tables": ["REGUH"],                   "tcodes": ["PC00_M99_CALC"]},
            {"name": "Benefits Enrolled",  "tables": [],                          "tcodes": ["PA30"]},
            {"name": "Employee Separated", "tables": ["PA0000"],                  "tcodes": ["PA30"]},
        ],
        "volume": {"source": "hcm domain analysis"},
    },
}


def ingest_processes(brain):
    """Create process and step nodes with table/tcode linkages."""
    stats = {'process_nodes': 0, 'step_nodes': 0, 'edges': 0}

    for proc_id, proc_def in PROCESS_DEFINITIONS.items():
        p_node_id = f"PROCESS:{proc_id}"
        domain = proc_def.get("domain", "FI")

        brain.add_node(p_node_id, "PROCESS", proc_def["name"],
                       domain=domain, layer="process",
                       source="process_mining",
                       metadata=proc_def.get("volume", {}))
        stats['process_nodes'] += 1

        prev_step_id = None
        for i, step in enumerate(proc_def["steps"]):
            step_id = f"STEP:{proc_id}:{step['name'].replace(' ', '_')}"
            brain.add_node(step_id, "PROCESS_STEP", step["name"],
                           domain=domain, layer="process",
                           source="process_mining",
                           metadata={"order": i, "tcodes": step["tcodes"]})
            stats['step_nodes'] += 1

            # Process contains step
            brain.add_edge(p_node_id, step_id, "PROCESS_CONTAINS",
                           evidence="mined", confidence=0.95,
                           discovered_in="040")
            stats['edges'] += 1

            # Step sequence
            if prev_step_id:
                brain.add_edge(prev_step_id, step_id, "STEP_FOLLOWS",
                               evidence="mined", confidence=0.9,
                               discovered_in="040")
                stats['edges'] += 1
            prev_step_id = step_id

            # Step -> tables
            for table in step["tables"]:
                tbl_id = f"SAP_TABLE:{table}"
                if not brain.has_node(tbl_id):
                    brain.add_node(tbl_id, "SAP_TABLE", table,
                                   domain="DATA_MODEL", layer="data",
                                   source="process_mining")
                brain.add_edge(step_id, tbl_id, "STEP_READS",
                               evidence="mined", confidence=0.85,
                               discovered_in="040")
                stats['edges'] += 1

    return stats
