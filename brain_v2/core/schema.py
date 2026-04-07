"""
Brain v2 Schema — Node and Edge type definitions with validation.
Source: BRAIN_V2_ARCHITECTURE.md Sections A.2, A.3
"""

# ── Node Types (30 types, 6 categories) ──

NODE_TYPES = {
    # Category 1: Code Objects
    "ABAP_CLASS", "ABAP_METHOD", "FUNCTION_MODULE", "ABAP_REPORT",
    "ENHANCEMENT", "BSP_APP", "ODATA_SERVICE", "PACKAGE",
    # Category 2: Data Objects
    "SAP_TABLE", "TABLE_FIELD", "DOMAIN_VALUE",
    # Category 3: Configuration Objects
    "DMEE_TREE", "PAYMENT_METHOD", "BCM_RULE", "HOUSE_BANK",
    "VALIDATION_RULE", "SUBSTITUTION_RULE", "NUMBER_RANGE", "JOB_DEFINITION",
    # Category 4: Organizational / Master Data
    "COMPANY_CODE", "FUND", "FUND_AREA", "FUND_CENTER",
    "GL_ACCOUNT", "COST_ELEMENT",
    # Category 5: Integration / Infrastructure
    "SAP_SYSTEM", "EXTERNAL_SYSTEM", "RFC_DESTINATION", "ICF_SERVICE", "IDOC_TYPE",
    # Category 6: Process / Transport / Knowledge
    "PROCESS", "PROCESS_STEP", "TRANSPORT", "SKILL", "KNOWLEDGE_DOC",
    # Catch-all for unmapped CTS objects
    "CODE_OBJECT", "DATA_ELEMENT", "DOMAIN_OBJECT", "TRANSACTION",
}

NODE_LAYERS = {"code", "config", "data", "process", "integration", "org"}

# ── Edge Types (45 types, 8 categories) ──

EDGE_TYPES = {
    # Category 1: Code Dependency (parsed from ABAP)
    "CALLS_FM", "READS_TABLE", "WRITES_TABLE", "READS_FIELD",
    "IMPLEMENTS_BADI", "INHERITS_FROM", "IMPLEMENTS_INTF",
    "RAISES_EVENT", "BELONGS_TO_PACKAGE",
    # Category 2: Configuration Dependency (from Gold DB)
    "USES_DMEE_TREE", "ROUTES_TO_BANK", "PROCESSES_VIA_BCM",
    "CONFIGURES_FORMAT", "VALIDATES_FIELD", "SUBSTITUTES_FIELD",
    "CONTROLS_POSTING_PERIOD", "ASSIGNS_NUMBER_RANGE",
    # Category 3: Data Join (proven SQL relationships)
    "JOINS_VIA", "FIELD_MAPS_TO",
    # Category 4: Integration (RFCDES, EDIDC, TFDIR)
    "CALLS_SYSTEM", "EXPOSES_FM", "SENDS_IDOC",
    "CALLS_VIA_RFC", "SERVES_HTTP",
    # Category 5: Process (process mining)
    "PROCESS_CONTAINS", "STEP_FOLLOWS", "STEP_READS", "STEP_USES_TCODE",
    # Category 6: Transport (CTS)
    "TRANSPORTS", "MODIFIES_CONFIG", "CO_TRANSPORTED_WITH",
    # Category 7: Knowledge
    "DOCUMENTED_IN", "SKILLED_IN", "DISCOVERED_IN",
    # Category 8: Organizational (existing from v1)
    "BELONGS_TO", "HAS_FUND_CENTER", "POSTS_TO_GL",
    # Infrastructure
    "RUNS_PROGRAM",
}

# ── Impact Direction per Edge Type ──

IMPACT_DIRECTION = {
    "CALLS_FM":           "forward",
    "READS_TABLE":        "forward",
    "WRITES_TABLE":       "forward",
    "READS_FIELD":        "forward",
    "IMPLEMENTS_BADI":    "backward",
    "INHERITS_FROM":      "bidirectional",
    "IMPLEMENTS_INTF":    "backward",
    "RAISES_EVENT":       "forward",
    "USES_DMEE_TREE":     "forward",
    "ROUTES_TO_BANK":     "bidirectional",
    "CONFIGURES_FORMAT":  "forward",
    "VALIDATES_FIELD":    "forward",
    "SUBSTITUTES_FIELD":  "forward",
    "EXPOSES_FM":         "backward",
    "CALLS_VIA_RFC":      "forward",
    "CALLS_SYSTEM":       "forward",
    "TRANSPORTS":         "forward",
    "STEP_READS":         "forward",
    "STEP_FOLLOWS":       "forward",
    "RUNS_PROGRAM":       "forward",
    "SERVES_HTTP":        "forward",
    "SENDS_IDOC":         "forward",
    "PROCESSES_VIA_BCM":  "forward",
    # Informational — no impact propagation
    "DOCUMENTED_IN":      None,
    "SKILLED_IN":         None,
    "DISCOVERED_IN":      None,
    "BELONGS_TO":         None,
    "HAS_FUND_CENTER":    None,
    "BELONGS_TO_PACKAGE": None,
}

# ── Risk Weights per Edge Type ──

RISK_WEIGHTS = {
    "WRITES_TABLE":       0.95,
    "USES_DMEE_TREE":     0.95,
    "ROUTES_TO_BANK":     0.95,
    "IMPLEMENTS_BADI":    0.9,
    "CONFIGURES_FORMAT":  0.9,
    "CALLS_FM":           0.8,
    "EXPOSES_FM":         0.85,
    "CALLS_VIA_RFC":      0.85,
    "INHERITS_FROM":      0.8,
    "VALIDATES_FIELD":    0.75,
    "SUBSTITUTES_FIELD":  0.75,
    "READS_FIELD":        0.7,
    "TRANSPORTS":         0.7,
    "READS_TABLE":        0.6,
    "STEP_READS":         0.5,
    "STEP_FOLLOWS":       0.5,
    "RUNS_PROGRAM":       0.6,
    "CALLS_SYSTEM":       0.7,
    "SENDS_IDOC":         0.8,
    "SERVES_HTTP":        0.6,
    "PROCESSES_VIA_BCM":  0.7,
}

# ── CTS Object Type → Graph Node Type mapping ──

CTS_OBJECT_TYPE_MAP = {
    "PROG": "ABAP_REPORT",
    "CLAS": "ABAP_CLASS",
    "FUGR": "FUNCTION_MODULE",
    "TABL": "SAP_TABLE",
    "TABU": "SAP_TABLE",
    "TRAN": "TRANSACTION",
    "DEVC": "PACKAGE",
    "DTEL": "DATA_ELEMENT",
    "DOMA": "DOMAIN_OBJECT",
    "ENHO": "ENHANCEMENT",
    "NROB": "NUMBER_RANGE",
    "SICF": "ICF_SERVICE",
    "INTF": "ABAP_CLASS",  # interfaces treated as class-like
    "SUSO": "CODE_OBJECT",
    "SXCI": "ENHANCEMENT",
    "VIEW": "SAP_TABLE",
    "TTYP": "DATA_ELEMENT",
    "MSAG": "CODE_OBJECT",
    "XSLT": "CODE_OBJECT",
}
