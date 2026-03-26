"""
enrich_config_detail.py
Regenerates cts_config_detail.json with a 'module' field inferred from
object name patterns — covers HCM, FI/CO, PSM/FM, Security, MDG, BC/Basis, IMG, etc.
This allows the dashboard to show a Package/Module column for classification.
"""
import json, re
from collections import defaultdict

with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

YEARS     = [str(y) for y in range(2017, 2027)]
SAP_SYS   = {'SAP', 'DDIC', 'BASIS', 'SAP_SUPPORT', 'WF-BATCH'}
SKIP_META = {'RELE', 'MERG'}
CFG_TYPES = {'TABU','CUS0','NROB','TDAT','VDAT','CDAT','DATED','VIED',
             'PDTS','PDVS','TABD','SOTT','PDAT','CUS1','TOBJ','OSOA',
             'TTYP','SCVI','VARX','PMKC','LODC','SOTU','TABT','CUAD',
             'LODE','PARA','AVAS'}

def infer_module(name, ot):
    n = name.upper()
    # ── Security / Authorization
    if re.match(r'^AGR_|^PRGN', n): return 'BC-Sec / Auth'
    if re.match(r'^USR|^UST|^SUSR', n): return 'BC-Sec / User Mgmt'
    if n in ('TVDIR','TDDAT'): return 'BC-Sec / Auth'
    # ── SAP MDG (Master Data Governance)
    if n.startswith('USMD'): return 'MDG'
    # ── HCM / Payroll
    if re.match(r'^T5(0|1|2|3|4|5|6|7|8|9)', n): return 'HCM-PY (Payroll)'
    if re.match(r'^T7', n): return 'HCM-PY (Payroll)'
    if re.match(r'^V_T5|^V_T7', n): return 'HCM-PY (Payroll)'
    if re.match(r'^PA[0-9]', n): return 'HCM-PA (Personnel Admin)'
    if n in ('MOLGA','T001P','T508A','T549','T549A'): return 'HCM-PY (Payroll)'
    # ── HCM OM/Org
    if re.match(r'^T77|^T750|^T528', n): return 'HCM-OM (Org Mgmt)'
    # ── HCM specific
    if re.match(r'^T5(A|B|C|D|E|F|G|H)', n): return 'HCM-PY (Payroll)'
    if re.match(r'^V_T7UN', n): return 'HCM (UNESCO specific)'
    # ── CO / Controlling
    if re.match(r'^TKA|^TKEB|^TKEBS|^GRW|^CE[0-9]K', n): return 'CO (Controlling)'
    if re.match(r'^KE|^GLE', n): return 'CO-PA (Profitability)'
    # ── FI / Finance
    if re.match(r'^T001[^P]|^SKA|^BSEG|^T0[0-9][0-9]|^TFBW|^FINB|^TFOR|^TZUN|^T012', n): return 'FI (Finance)'
    if re.match(r'^SWOTICE|^SFOBU|^T53[0-9]', n): return 'FI (Finance)'
    if re.match(r'^GB0|^TFC', n): return 'FI (Accounts)'
    # ── PSM / Public Sector / FM
    if re.match(r'^UCU|^UGW|^FMFG|^FM[A-Z]|^PSCD', n): return 'PSM/FM'
    if re.match(r'^UCUM|^UGWB', n): return 'PSM/FM'
    # ── Logistics / MM / SD
    if re.match(r'^T16|^EKPO|^MARA|^MARC|^T024', n): return 'MM (Procurement)'
    if re.match(r'^TVKO|^TVZW|^TVTA|^T180|^TSPA', n): return 'SD (Sales)'
    # ── PP / Plant Maint
    if re.match(r'^T430|^T399|^CRMC', n): return 'PP/PM'
    # ── Basis / BC
    if re.match(r'^TVAR|^TPFYP|^RSEC|^RSAD|^RSPLS', n): return 'BC-Basis'
    if re.match(r'^TNODE|^TNAPR|^TNAC', n): return 'BC-IMG (Cust Tree)'
    if re.match(r'^NRIV', n): return 'BC-NR (Number Ranges)'
    if re.match(r'^T9POST|^T9', n): return 'BC-Payroll Post'
    # ── IMG / Customizing meta
    if re.match(r'^CVERS|^TADIR|^TOBJ|^REPOS', n): return 'BC-Dev'
    # ── Output / Forms / NAST
    if re.match(r'^T685|^TNAPR|^NAST', n): return 'BC-Output'
    # ── Workflow
    if re.match(r'^SWN|^SWWW|^SWP|^SWT', n): return 'BC-WF (Workflow)'
    # ── VDAT with V_ prefix → usually HCM or FI
    if ot == 'VDAT':
        if re.match(r'^V_T(5|7)', n): return 'HCM-PY (Payroll)'
        if re.match(r'^V_T', n): return 'FI/CO Config View'
        return 'HCM/Config View'
    # ── Fallback: try to infer from T-table number range
    m = re.match(r'^T(\d)', n)
    if m:
        d = int(m.group(1))
        if d == 0: return 'FI/Org'
        if d == 1: return 'FI (Finance)'
        if d == 2: return 'SD/Logistics'
        if d == 3: return 'HR/Payroll'
        if d == 4: return 'MM/Procurement'
        if d == 5: return 'HCM-PY (Payroll)'
        if d == 6: return 'SD/Billing'
        if d == 7: return 'HCM-OM/WF'
        if d == 8: return 'BC/Output'
        if d == 9: return 'BC/Payroll Post'
    return 'General IMG'

# ── Build registry ─────────────────────────────────────────────────────────────
registry = defaultdict(lambda: {
    'obj_type': '', 'mods_by_year': defaultdict(int),
    'users': set(), 'total_mods': 0,
})

for t in raw['transports']:
    owner  = t.get('owner', '').strip().upper()
    year   = t.get('date', '')[:4]
    trkorr = t.get('trkorr', '')
    if year not in YEARS: continue
    if owner in SAP_SYS: continue
    if trkorr.upper().startswith('E9BK'): continue
    for o in t.get('objects', []):
        ot = o.get('obj_type', o.get('OBJECT', '')).strip().upper()
        on = o.get('obj_name', o.get('OBJ_NAME', '')).strip()
        if not ot or not on or ot in SKIP_META: continue
        if ot not in CFG_TYPES: continue
        r = registry[on]
        r['obj_type'] = ot
        r['mods_by_year'][year] += 1
        r['users'].add(owner)
        r['total_mods'] += 1

out = {}
for name, v in registry.items():
    if v['total_mods'] == 0: continue
    years_active = sorted(y for y, c in v['mods_by_year'].items() if c > 0)
    out[name] = {
        'obj_type':     v['obj_type'],
        'module':       infer_module(name, v['obj_type']),
        'total_mods':   v['total_mods'],
        'users':        sorted(v['users']),
        'user_count':   len(v['users']),
        'years_active': years_active,
        'first_seen':   years_active[0] if years_active else '',
        'last_seen':    years_active[-1] if years_active else '',
        'mods_by_year': {y: v['mods_by_year'].get(y, 0) for y in YEARS},
    }

with open('cts_config_detail.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)

# Module distribution report
from collections import Counter
mods = Counter(v['module'] for v in out.values())
print('Module distribution (top 20):')
for mod, cnt in mods.most_common(20):
    print(f'  {mod:<35} {cnt:>5}')
print(f'\nTotal config objects: {len(out):,}')
print('Saved cts_config_detail.json')
