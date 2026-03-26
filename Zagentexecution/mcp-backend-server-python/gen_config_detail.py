"""
gen_config_detail.py  
Generates cts_config_detail.json — per-config-object deep data:
mods per year, contributing users, first/last seen.
"""
import json, re
from collections import defaultdict

with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

YEARS     = [str(y) for y in range(2017, 2027)]
SAP_SYS   = {'SAP','DDIC','BASIS','SAP_SUPPORT','WF-BATCH'}
SKIP_META = {'RELE','MERG'}
CFG_TYPES = {'TABU','CUS0','NROB','TDAT','VDAT','CDAT','DATED','VIED',
             'PDTS','PDVS','TABD','SOTT','PDAT','CUS1','TOBJ','OSOA',
             'TTYP','SCVI','VARX','PMKC','LODC','SOTU','TABT','CUAD','LODE','PARA','AVAS'}

# registry[name] -> {obj_type, mods_by_year, users, total_mods}
registry = defaultdict(lambda: {
    'obj_type': '', 'mods_by_year': defaultdict(int),
    'users': set(), 'total_mods': 0,
})

for t in raw['transports']:
    owner  = t.get('owner','').strip().upper()
    year   = t.get('date','')[:4]
    trkorr = t.get('trkorr','')
    if year not in YEARS: continue
    if owner in SAP_SYS: continue
    if trkorr.upper().startswith('E9BK'): continue
    for o in t.get('objects',[]):
        ot = o.get('obj_type', o.get('OBJECT','')).strip().upper()
        on = o.get('obj_name', o.get('OBJ_NAME','')).strip()
        if not ot or not on or ot in SKIP_META: continue
        if ot not in CFG_TYPES: continue
        r = registry[on]
        r['obj_type'] = ot
        r['mods_by_year'][year] += 1
        r['users'].add(owner)
        r['total_mods'] += 1

# Serialise (sets → lists)
out = {}
for name, v in registry.items():
    if v['total_mods'] == 0: continue
    years_active = sorted(y for y, c in v['mods_by_year'].items() if c > 0)
    out[name] = {
        'obj_type':     v['obj_type'],
        'total_mods':   v['total_mods'],
        'users':        sorted(v['users']),
        'user_count':   len(v['users']),
        'years_active': years_active,
        'first_seen':   years_active[0] if years_active else '',
        'last_seen':    years_active[-1] if years_active else '',
        'mods_by_year': {y: v['mods_by_year'].get(y, 0) for y in YEARS},
    }

with open('cts_config_detail.json','w',encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)

total = len(out)
top = sorted(out.items(), key=lambda x: -x[1]['total_mods'])[:10]
print(f'Config detail: {total} unique config objects')
print('Top 10:')
for name, v in top:
    print(f"  {name:<30} {v['obj_type']}  {v['total_mods']}x  {v['user_count']} users  {v['years_active']}")
print('Saved cts_config_detail.json')
