"""
Improve module classification in cts_config_detail.json
Using new Transport Intelligence Skill module map + package/obj_name pattern matching.

New domains being added:
- HCM-PA (Personnel Admin / Infotypes)
- HCM-OM (Org Management / Workflows)
- HCM-Benefits (Fiori Benefits)
- HCM-WF (HR Workflows)
- PSM-FM (Funds Management)
- PSM-BW (BW/Budget Content)
- FI (Finance / Accounting)
- FI-GL (General Ledger)
- FI-Bank (Bank Integration)
- CO (Controlling)
- MM (Materials Mgmt / Procurement)
- SD (Sales & Distribution)
- PS (Project System)
- FIORI (Fiori / Launchpad / BSP)
- ABAP (Pure dev objects, no functional domain)
- BASIS (BC / Technical)
- BASIS-WF (Workflow)
- BASIS-LSMW (Migration)
- BASIS-NR (Number Ranges)
- SECURITY (Auth / Roles)
- TRAVEL (Travel Management)
- LOGISTICS (Logistics)
- CONTRACTS (Contract Management)
"""

import json, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')

# ── 1. Load current data ──────────────────────────────────────────────────────
with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

# ── 2. Package → Module mapping (from Transport Intelligence Skill + UNESCO-specific) ─
PKG_MODULE = {
    # HCM
    'ZHR_DEV':               'HCM-PA',
    'ZHRDEV':                'HCM-PA',
    'ZHRPA':                 'HCM-PA',
    'ZHR_NPO_PA':            'HCM-PA',
    'ZHR_INFOTYPE_EXTENSION':'HCM-PA',
    'PAOC_SFI_EMPL_DATA':    'HCM-PA',
    'YHR_PA_WF':             'HCM-WF',
    'YHR_OM_WF':             'HCM-OM',
    'ZHRBENEFITS_FIORI':     'HCM-Benefits',
    'ZHRHR':                 'HCM-PA',
    'PAOC_FPM_COM_ENGINE':   'HCM-OM',
    'PBUN':                  'HCM-OM',    # Master Data Non Profit Organizations
    'PC_WTI':                'HCM-PY',    # Wage Type Information
    'PCUN':                  'HCM-PY',    # Payroll Non Profit Organizations

    # PSM / FM
    'ZBW':                   'PSM-BW',
    'FMBP_E':                'PSM-FM',
    'YB':                    'PSM-FM',    # Regular Budget
    'YE':                    'PSM-FM',    # Extrabudgetary Project

    # FI / Accounting
    'YA':                    'FI',        # Accounting
    'FIN_BNK_COM_CORE':      'FI-Bank',
    'BBTE':                  'FI',        # Business Transaction Events / Open FI
    'CNPC':                  'PS',        # PP Project Management → PS

    # PS (Project System)
    'PS_HLP_CACHE':          'PS',
    'YCMT2':                 'PS',        # Contract Management Tool

    # Logistics / MM
    'YP':                    'MM',        # Purchasing
    'YL':                    'LOGISTICS',
    'ZEQ':                   'LOGISTICS', # Equipment

    # Travel
    'YV':                    'TRAVEL',

    # Fiori / UI
    'ZFIORI':                'FIORI',
    'APB_LAUNCHPAD':         'FIORI',
    'SWDP_UR_NW7':           'FIORI',     # Unified Rendering / Launchpad
    'ZHRBENEFITS_FIORI':     'FIORI',

    # BASIS / Technical
    'YBC':                   'BASIS',
    '/SAPDMC/LSMW':          'BASIS-LSMW',
    'S_LMCFG_OSS_TASKS':     'BASIS',
    'ZTECH':                 'BASIS',
    '/USE/PQM4_IMP':         'BASIS',
    '/USE/BO1_IMP':          'BASIS',
    'SZC':                   'BASIS',     # Factory Calendar
    'XS4SIC_DIMP':           'BASIS',
    'MCEX':                  'BASIS',     # BW Extraction
}

# ── 3. Package prefix → Module (for packages not fully listed) ─────────────────
PKG_PREFIX_MODULE = [
    # HR related
    ('ZHR',      'HCM-PA'),
    ('ZHRHR',    'HCM-PA'),
    ('PAOC',     'HCM-OM'),
    ('PA',       'HCM-PA'),
    ('PC',       'HCM-PY'),
    ('PCHR',     'HCM-PY'),
    ('PB',       'HCM-PA'),
    # PSM/FM
    ('FMBP',     'PSM-FM'),
    ('FMFS',     'PSM-FM'),
    ('FMBS',     'PSM-FM'),
    ('FM',       'PSM-FM'),
    ('GM',       'PSM-FM'),    # Grants
    ('PSBCS',    'PSM-BW'),
    # FI
    ('FIN_BNK',  'FI-Bank'),
    ('FIN',      'FI-GL'),
    ('FAGL',     'FI-GL'),
    # BASIS
    ('BC',       'BASIS'),
    ('SZ',       'BASIS'),
    # Fiori
    ('APB',      'FIORI'),
    ('/UI',      'FIORI'),
    ('/IWFND',   'FIORI'),
    # Security
    ('SAP_SE',   'SECURITY'),
    ('SUSR',     'SECURITY'),
]

# ── 4. Obj_name pattern → Module ──────────────────────────────────────────────
OBJ_NAME_PATTERNS = [
    # HR infotypes
    (r'^(T5|PA|IT|T77|T50[0-9]|T51[0-9]|T52[0-4])',  'HCM-PA'),
    (r'^T512',                                          'HCM-PY'),
    (r'^T549',                                          'HCM-PY'),
    (r'^T554',                                          'HCM-PY'),
    (r'^T510\b',                                        'HCM-PY'),
    (r'^HRP',                                           'HCM-OM'),
    (r'^YHR|^ZHR',                                      'HCM-PA'),
    # PSM / FM
    (r'^FMCI|^FM01|^FMZU|^T043\b|^FMRP|^FMRB|^GMG',  'PSM-FM'),
    (r'^FMDER',                                         'PSM-FM'),
    # FI Critical
    (r'^T030\b|^T030R',                                 'FI'),
    (r'^T001B\b',                                       'FI'),
    (r'^SKA1|^SKB1',                                    'FI-GL'),
    (r'^T011\b|^FAGL_T011',                             'FI-GL'),
    (r'^FAGL',                                          'FI-GL'),
    (r'^T003\b|^T004\b|^T004F',                         'FI'),
    (r'^T880\b',                                        'FI'),
    (r'^T001\b(?!W)',                                   'FI'),
    (r'^T001W\b',                                       'MM'),
    # FI-Bank
    (r'^T012\b|^T042\b',                                'FI-Bank'),
    (r'^DMEE',                                          'FI-Bank'),
    # CO
    (r'^T001C|^CSKS|^AUFK',                             'CO'),
    # MM
    (r'^T156|^T023\b|^T006\b|^MARC|^MARA',             'MM'),
    # PS
    (r'^OPST|^OPS_BUKRS|^T420|^TCNF|^PROJ\b|^PRPS',   'PS'),
    # Security (number ranges)
    (r'^AGR_',                                          'SECURITY'),
    (r'^NROB\b',                                        'BASIS-NR'),
    # Fiori
    (r'^/UI2/|^/IWFND/',                                'FIORI'),
    # Basis / Workflow
    (r'^SWD|^SWXF|^SWPA',                              'BASIS-WF'),
    (r'^RSWFDHEX|^SWF',                                 'BASIS-WF'),
    # ABAP development namespace (catch-all for Z/Y custom objects)
    (r'^[ZY](CL_|PG_|PROG_|INT_|FU_|FG_)',            'ABAP'),
]

# ── 5. Obj_type → Module (for obj_types that always belong to a module) ────────
OBJTYPE_MODULE = {
    'NROB':  'BASIS-NR',
    'XPRA':  'BASIS',
    'LSMW':  'BASIS-LSMW',
}

# ── 6. Pkg_desc keyword → Module ──────────────────────────────────────────────
PKG_DESC_KEYWORDS = [
    ('payroll',          'HCM-PY'),
    ('wage',             'HCM-PY'),
    ('personnel',        'HCM-PA'),
    ('infotype',         'HCM-PA'),
    ('org management',   'HCM-OM'),
    ('org unit',         'HCM-OM'),
    ('position',         'HCM-OM'),
    ('benefits',         'HCM-Benefits'),
    ('fiori',            'FIORI'),
    ('launchpad',        'FIORI'),
    ('odata',            'FIORI'),
    ('funds management', 'PSM-FM'),
    ('budgeting',        'PSM-FM'),
    ('budget',           'PSM-FM'),
    ('grants',           'PSM-FM'),
    ('commitment',       'PSM-FM'),
    ('project management','PS'),
    ('wbs',              'PS'),
    ('accounting',       'FI'),
    ('general ledger',   'FI-GL'),
    ('bank',             'FI-Bank'),
    ('controlling',      'CO'),
    ('cost center',      'CO'),
    ('purchasing',       'MM'),
    ('procurement',      'MM'),
    ('travel',           'TRAVEL'),
    ('logistics',        'LOGISTICS'),
    ('factory calendar', 'BASIS'),
    ('basis',            'BASIS'),
    ('workflow',         'BASIS-WF'),
    ('migration',        'BASIS-LSMW'),
    ('authorization',    'SECURITY'),
    ('security',         'SECURITY'),
]

def classify(obj_name, obj_type, package, pkg_desc, current_module):
    """Return improved module classification."""
    # Keep well-classified ones (not General IMG)
    if current_module and current_module != 'General IMG':
        return current_module

    pkg = (package or '').strip()
    desc = (pkg_desc or '').lower()
    name = obj_name.strip()
    otype = obj_type.strip()

    # 1. Exact package match
    if pkg and pkg in PKG_MODULE:
        return PKG_MODULE[pkg]

    # 2. Package prefix
    for prefix, mod in PKG_PREFIX_MODULE:
        if pkg.startswith(prefix):
            return mod

    # 3. Obj_type override
    if otype in OBJTYPE_MODULE:
        return OBJTYPE_MODULE[otype]

    # 4. Obj_name pattern
    for pattern, mod in OBJ_NAME_PATTERNS:
        if re.match(pattern, name, re.IGNORECASE):
            return mod

    # 5. Pkg_desc keyword
    for kw, mod in PKG_DESC_KEYWORDS:
        if kw in desc:
            return mod

    return 'General IMG'  # still unclassified

# ── 7. Apply classification ───────────────────────────────────────────────────
before = collections.Counter(v.get('module','?') for v in cfg.values())
changes = 0
new_assignments = collections.Counter()

for obj_name, item in cfg.items():
    old = item.get('module', 'General IMG')
    new = classify(
        obj_name,
        item.get('obj_type', ''),
        item.get('package', ''),
        item.get('pkg_desc', ''),
        old
    )
    if new != old:
        item['module'] = new
        changes += 1
        new_assignments[new] += 1

after = collections.Counter(v.get('module','?') for v in cfg.values())

print(f'Changes made: {changes}')
print()
print('=== BEFORE (top 25) ===')
for m, c in before.most_common(25):
    print(f'  {c:5d}  {m}')
print()
print('=== AFTER (top 35) ===')
for m, c in after.most_common(35):
    print(f'  {c:5d}  {m}')
print()
print('=== NEW ASSIGNMENTS ===')
for m, c in new_assignments.most_common(30):
    print(f'  {c:4d}  → {m}')

# ── 8. Save updated config detail ─────────────────────────────────────────────
with open('cts_config_detail.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

print('\nSaved cts_config_detail.json')
print(f'General IMG reduction: {before["General IMG"]} → {after["General IMG"]} ({before["General IMG"]-after["General IMG"]} reclassified)')
