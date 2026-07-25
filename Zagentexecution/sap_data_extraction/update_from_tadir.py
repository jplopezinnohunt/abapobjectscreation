"""Updates General IMG classifications using new TADIR enrichment DB data"""
import sqlite3
import json
import collections
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

# DB Connection
conn = sqlite3.connect('sqlite/p01_gold_master_data.db')
c = conn.cursor()

# Load config detail
cfg_path = '../mcp-backend-server-python/cts_config_detail.json'
with open(cfg_path, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

general_img_keys = [k for k, v in cfg.items() if v.get('module') == 'General IMG']
print(f"Starting General IMG count: {len(general_img_keys)}")

# Fetch all TADIR enrichment data into memory mapped by (obj_type, obj_name)
c.execute("SELECT obj_type, obj_name, devclass FROM tadir_enrichment")
tadir_cache = {}
for r in c.fetchall():
    tadir_cache[(r[0], r[1])] = r[2]

print(f"Loaded {len(tadir_cache)} TADIR enrichment records into memory.")

matched_packages = 0
for k in general_img_keys:
    item = cfg[k]
    otype = item.get('obj_type')
    
    # Check cache
    devclass = tadir_cache.get((otype, k))
    if devclass:
        item['package'] = devclass
        matched_packages += 1

print(f"Found new DevClass for {matched_packages} items out of {len(general_img_keys)}")

# --- Re-Classification Logic using updated package ---

PKG_MODULE = {
    'ZHR_DEV': 'HCM-PA', 'ZHRDEV': 'HCM-PA', 'ZHRPA': 'HCM-PA', 'ZHR_NPO_PA': 'HCM-PA',
    'ZHR_INFOTYPE_EXTENSION': 'HCM-PA', 'PAOC_SFI_EMPL_DATA': 'HCM-PA',
    'YHR_PA_WF': 'HCM-WF', 'YHR_OM_WF': 'HCM-OM', 'ZHRHR': 'HCM-PA',
    'PAOC_FPM_COM_ENGINE': 'HCM-OM', 'PBUN': 'HCM-OM', 'PC_WTI': 'HCM-PY', 'PCUN': 'HCM-PY',
    'ZBW': 'PSM-BW', 'FMBP_E': 'PSM-FM', 'YB': 'PSM-FM', 'YE': 'PSM-FM',
    'YA': 'FI', 'FIN_BNK_COM_CORE': 'FI-Bank', 'BBTE': 'FI', 'CNPC': 'PS',
    'PS_HLP_CACHE': 'PS', 'YCMT2': 'PS', 'YP': 'MM', 'YL': 'LOGISTICS', 'ZEQ': 'LOGISTICS',
    'YV': 'TRAVEL', 'ZFIORI': 'FIORI', 'APB_LAUNCHPAD': 'FIORI', 'SWDP_UR_NW7': 'FIORI',
    'ZHRBENEFITS_FIORI': 'FIORI', 'YBC': 'BASIS', '/SAPDMC/LSMW': 'BASIS-LSMW',
    'S_LMCFG_OSS_TASKS': 'BASIS', 'ZTECH': 'BASIS', '/USE/PQM4_IMP': 'BASIS',
    'MCEX': 'BASIS', 'Y-BW': 'BW', 'ZBC': 'BASIS', 'ZRE_CONTRACT': 'MM-Contracts',
    'PUN_CMT': 'MM-Contracts', '/USE/UCP2_IMP': 'BASIS', 'YHR_CORE_MANAGER': 'HCM-OM',
    'SWDP_CONFIGURATION': 'FIORI', 'IBO_INBOX_FEEDER': 'FIORI',
}

PKG_PREFIX_MODULE = [
    ('ZHR', 'HCM-PA'), ('ZHRHR', 'HCM-PA'), ('PAOC', 'HCM-OM'), ('PA', 'HCM-PA'),
    ('PC', 'HCM-PY'), ('PCHR', 'HCM-PY'), ('PB', 'HCM-PA'), ('FMBP', 'PSM-FM'),
    ('FMFS', 'PSM-FM'), ('FMBS', 'PSM-FM'), ('FM', 'PSM-FM'), ('GM', 'PSM-FM'),
    ('PSBCS', 'PSM-BW'), ('FIN_BNK', 'FI-Bank'), ('FIN', 'FI-GL'), ('FAGL', 'FI-GL'),
    ('BC', 'BASIS'), ('SZ', 'BASIS'), ('APB', 'FIORI'), ('/UI', 'FIORI'),
    ('/IWFND', 'FIORI'), ('SAP_SE', 'SECURITY'), ('SUSR', 'SECURITY'),
]

OBJ_NAME_PATTERNS = [
    (r'^(T5|PA|IT|T77|T50[0-9]|T51[0-9]|T52[0-4])', 'HCM-PA'), (r'^T512', 'HCM-PY'),
    (r'^T549', 'HCM-PY'), (r'^T554', 'HCM-PY'), (r'^T510\b', 'HCM-PY'),
    (r'^HRP', 'HCM-OM'), (r'^YHR|^ZHR', 'HCM-PA'),
    (r'^FMCI|^FM01|^FMZU|^T043\b|^FMRP|^FMRB|^GMG', 'PSM-FM'), (r'^FMDER', 'PSM-FM'),
    (r'^T030\b|^T030R', 'FI'), (r'^T001B\b', 'FI'), (r'^SKA1|^SKB1', 'FI-GL'),
    (r'^T011\b|^FAGL_T011', 'FI-GL'), (r'^FAGL', 'FI-GL'),
    (r'^T003\b|^T004\b|^T004F', 'FI'), (r'^T880\b', 'FI'), (r'^T001\b(?!W)', 'FI'),
    (r'^T001W\b', 'MM'), (r'^T012\b|^T042\b', 'FI-Bank'), (r'^DMEE', 'FI-Bank'),
    (r'^T001C|^CSKS|^AUFK', 'CO'), (r'^T156|^T023\b|^T006\b|^MARC|^MARA', 'MM'),
    (r'^OPST|^OPS_BUKRS|^T420|^TCNF|^PROJ\b|^PRPS', 'PS'), (r'^AGR_', 'SECURITY'),
    (r'^NROB\b', 'BASIS-NR'), (r'^/UI2/|^/IWFND/', 'FIORI'),
    (r'^SWD|^SWXF|^SWPA', 'BASIS-WF'), (r'^RSWFDHEX|^SWF', 'BASIS-WF'),
    (r'^[ZY](CL_|PG_|PROG_|INT_|FU_|FG_)', 'ABAP'),
]

OBJTYPE_MODULE = {'NROB': 'BASIS-NR', 'XPRA': 'BASIS', 'LSMW': 'BASIS-LSMW'}

def classify(name, otype, pkg):
    pkg = pkg.strip()
    name = name.strip()
    otype = otype.strip()
    
    if pkg and pkg in PKG_MODULE: return PKG_MODULE[pkg]
    for prefix, mod in PKG_PREFIX_MODULE:
        if pkg.startswith(prefix): return mod
    if otype in OBJTYPE_MODULE: return OBJTYPE_MODULE[otype]
    for pattern, mod in OBJ_NAME_PATTERNS:
        if re.match(pattern, name, re.IGNORECASE): return mod
    return 'General IMG'

reclassified = 0
for k in general_img_keys:
    item = cfg[k]
    old_mod = item['module']
    pkg = item.get('package', '')
    
    new_mod = classify(k, item.get('obj_type', ''), pkg)
    if new_mod != 'General IMG':
        item['module'] = new_mod
        reclassified += 1

print(f"\nReclassified {reclassified} items out of {matched_packages} packages found.")

# Distribution
modules = collections.Counter(v.get('module', '?') for v in cfg.values())
print('\n=== OVERALL MODULE DISTRIBUTION (Top 20) ===')
for m, c in modules.most_common(20):
    print(f'  {c:5d}  {m}')

# Save
with open(cfg_path, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)
    
print('\nSaved cts_config_detail.json')

# Inject to dashboard using reinject script approach
dashboard_path = '../mcp-backend-server-python/cts_dashboard.html'
with open(dashboard_path, 'r', encoding='utf-8') as f:
    html = f.read()

cfg_json = json.dumps(cfg, ensure_ascii=False, separators=(',', ':'))

start = html.find('const CFGDETAIL={')
if start >= 0:
    count = 0
    i = start + len('const CFGDETAIL=')
    end = -1
    while i < len(html):
        if html[i] == '{': count += 1
        elif html[i] == '}':
            count -= 1
            if count == 0:
                end = i + 1
                break
        i += 1
    
    if end > 0:
        new_html = html[:start] + 'const CFGDETAIL=' + cfg_json + html[end:]
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(new_html)
        print('SUCCESS: cts_dashboard.html injected')
    else:
        print('Failed to find JSON end brace')
else:
    print('Failed to find const CFGDETAIL={')
