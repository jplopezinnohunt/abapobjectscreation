"""
cts_unique_analysis.py
======================
Re-calculates ALL metrics from unique objects (deduped by type+name).
The raw data has 89,303 object-transport pairs — this script collapses them
to 29,060 unique objects, each with: first_seen, last_seen, total_mods,
users_touched, transports, years_active, domain, type_short.

Output: cts_unique_objects.json
"""
import json, re
from collections import defaultdict, Counter

YEARS     = [str(y) for y in range(2017, 2027)]
SKIP_META = {'RELE', 'MERG', 'SBYP', 'SBYL'}
SAP_SYS   = {'SAP', 'DDIC', 'BASIS', 'SAP_SUPPORT', 'WF-BATCH'}

# ── Type classification ───────────────────────────────────────────────────────
TYPE_SHORT = {
    'PROG':'REP','REPS':'REP','REPT':'REP','REPY':'REP','REPO':'REP',
    'CLAS':'CLAS','INTF':'CLAS','METH':'CLAS','CINC':'CLAS','CINS':'CLAS',
    'CPUB':'CLAS','CPRO':'CLAS','CPRI':'CLAS','CLSD':'CLAS',
    'FUGR':'FUNC','FUNC':'FUNC','FUGA':'FUNC',
    'SWFP':'WF','SWFT':'WF','SWED':'WF','SWFL':'WF','PDWS':'WF','PCYC':'WF',
    'ENHO':'ENH','ENHS':'ENH','ENHD':'ENH','ENHC':'ENH',
    'WAPP':'UI','SMIM':'UI','WDYC':'UI','WDYV':'UI','WDYA':'UI',
    'W3MI':'UI','W3HT':'UI','SICF':'UI','WAPA':'UI',
    'IWSV':'UI','IWOM':'UI','IWSG':'UI',
    'SSFO':'FORM','SFPF':'FORM','SFPS':'FORM','F30':'FORM','DMEE':'FORM','PFRM':'FORM',
    'TABL':'MDL','DTEL':'MDL','DOMA':'MDL','INDX':'MDL','VIEW':'MDL',
    'TABU':'CFG','CUS0':'CFG','NROB':'CFG','TDAT':'CFG','LODE':'CFG',
    'TOBJ':'CFG','SCVI':'CFG','PARA':'CFG','AVAS':'CFG',
    'PDTS':'CFG','PDVS':'CFG','PDAT':'CFG','TABD':'CFG','SOTT':'CFG',
    'VDAT':'CFG',
    'ACGR':'SEC','AUTH':'SEC','ACID':'SEC','SUSC':'SEC',
    'SHLP':'MISC','SOBJ':'MISC','MSAG':'MISC','VARI':'MISC','TYPE':'MISC',
    'DEVC':'INFRA','TRAN':'INFRA',
    'TEXT':'TXT','DOCU':'TXT','SHI3':'TXT','SHI6':'TXT',
}

DEV_CATS = {'REP','CLAS','FUNC','WF','ENH','UI','FORM','MDL'}
CFG_CATS = {'CFG'}
SEC_CATS = {'SEC'}

# ── Domain inference from obj name prefix ─────────────────────────────────────
DOMAIN_RULES = [
    (['ACGR','AUTH','ACID','SUSC'], None,                         'Security'),
    (None, [r'^ZHR_',r'^YHR_',r'^ZPAY_',r'^CL_HRPADUN',r'^CL_HR',
            r'^ZCL_PAY',r'^T7UN',r'^HRPADUN',r'^PUN_',r'^HRSFI_',
            r'^ZN[0-9]',r'^CL_FAA_',r'^ZHR',r'^YHR'],            'HCM'),
    (None, [r'^V_T7UN',r'^T7UN',r'^T5U',r'^T549'],               'HCM'),
    (['PDTS','PDVS','TABD','SOTT','VDAT'], None,                  'HCM'),
    (None, [r'^ZPSM_',r'^ZFM_',r'^ZFMF',r'^RFFM',r'^YFBI',
            r'^RFFMCY',r'^RFFMKU',r'^ZFMG'],                     'PSM/FM'),
    (None, [r'^ZFI_',r'^YNAZ',r'^NAZFI',r'^DMEE_',r'^PAYM'],    'FI'),
    (None, [r'^ZCO_',r'^COST'],                                    'CO'),
    (['IWSV','IWOM','IWSG','SWFL'], None,                         'OData/WF'),
    (['WAPP','SMIM','WDYC','WDYV','WDYA','W3MI','SICF'], None,   'Fiori/UI'),
    (None, [r'^ZFO_',r'^YFO_',r'^ZCRP',r'^YCRP'],               'Fiori/UI'),
    (['SWFP','SWFT','SWED','PDWS','PCYC'], None,                  'Workflow'),
    (None, [r'^ZOMWF',r'^ZWF_'],                                  'Workflow'),
]

def infer_domain(ot, on):
    ot_up = ot.upper()
    on_up = on.upper()
    for typ_list, name_pats, dom in DOMAIN_RULES:
        if typ_list is not None:
            if ot_up not in [t.upper() for t in typ_list]:
                continue
            if name_pats is None:
                return dom
        if name_pats:
            for p in name_pats:
                if re.match(p, on_up):
                    return dom
    if on_up.startswith('Z') or on_up.startswith('Y'):
        return 'Custom Z/Y'
    return 'SAP Standard'

# ── Load raw data ─────────────────────────────────────────────────────────────
print("Loading cts_10yr_raw.json...")
with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

# ── Build unique object registry ──────────────────────────────────────────────
# Key: (obj_type, obj_name)
# Value: {mods, users, years, transports, first_year, last_year, domain, type_short}
registry = {}   # deduped unique objects

for t in raw['transports']:
    owner  = t.get('owner', '').strip().upper()
    year   = t.get('date', '')[:4]
    trkorr = t.get('trkorr', '')
    is_epi = trkorr.upper().startswith('E9BK')
    if year not in YEARS:
        continue
    if owner in SAP_SYS:
        continue

    for o in t.get('objects', []):
        ot = o.get('obj_type', o.get('OBJECT', '')).strip().upper()
        on = o.get('obj_name', o.get('OBJ_NAME', '')).strip()
        if not ot or not on or ot in SKIP_META:
            continue

        key = (ot, on)
        if key not in registry:
            ts = TYPE_SHORT.get(ot, 'OTH')
            dom = infer_domain(ot, on)
            nat = 'EPI-USE' if is_epi else (
                  'DEV' if ts in DEV_CATS else
                  'CFG' if ts in CFG_CATS else
                  'SEC' if ts in SEC_CATS else 'MISC')
            registry[key] = {
                'ot': ot, 'on': on,
                'ts': ts, 'dom': dom, 'nat': nat,
                'mods': 0, 'users': set(), 'years': set(), 'trans': set(),
            }

        entry = registry[key]
        entry['mods']  += 1
        entry['users'].add(owner)
        entry['years'].add(year)
        entry['trans'].add(trkorr)

print(f"Unique objects registered: {len(registry):,}")

# ── Build aggregated views ─────────────────────────────────────────────────────

# 1. Domain summary (unique objects)
dom_summary = defaultdict(lambda: {'unique':0,'mods':0,'types':Counter(),'users':set()})
for (ot,on), e in registry.items():
    d = e['dom']
    dom_summary[d]['unique']      += 1
    dom_summary[d]['mods']        += e['mods']
    dom_summary[d]['types'][e['ts']] += 1
    dom_summary[d]['users']      |= e['users']

# 2. Type summary
type_summary = defaultdict(lambda: {'unique':0,'mods':0,'users':set()})
for (ot,on), e in registry.items():
    ts = e['ts']
    type_summary[ts]['unique'] += 1
    type_summary[ts]['mods']   += e['mods']
    type_summary[ts]['users']  |= e['users']

# 3. User summary (unique objects per user = objects first seen by them)
#    Also: objects touched (even if multiple users)
user_unique_owned   = Counter()  # objects where user is the ONLY toucher
user_unique_touched = Counter()  # objects where user is ONE OF the touchers
user_domain_unique  = defaultdict(lambda: defaultdict(int))
user_type_unique    = defaultdict(lambda: defaultdict(int))
user_year_unique    = defaultdict(lambda: defaultdict(int))

# We need user x object tracking (not just aggregated)
# Track which objects each user has touched
user_objects = defaultdict(set)  # user -> set of (ot,on)
obj_first_user = {}

for t in raw['transports']:
    owner  = t.get('owner', '').strip().upper()
    year   = t.get('date', '')[:4]
    trkorr = t.get('trkorr', '')
    if year not in YEARS or owner in SAP_SYS: continue
    if trkorr.upper().startswith('E9BK'): continue
    for o in t.get('objects', []):
        ot = o.get('obj_type', o.get('OBJECT', '')).strip().upper()
        on = o.get('obj_name', o.get('OBJ_NAME', '')).strip()
        if not ot or not on or ot in SKIP_META: continue
        user_objects[owner].add((ot, on))

for u, objs in user_objects.items():
    for key in objs:
        e = registry.get(key)
        if not e: continue
        user_unique_touched[u] += 1
        if len(e['users']) == 1:
            user_unique_owned[u] += 1
        user_domain_unique[u][e['dom']] += 1
        user_type_unique[u][e['ts']]   += 1

# 4. Year-unique: which new unique objects appeared each year (first seen)
year_new_unique = defaultdict(lambda: defaultdict(int))  # year -> nature -> count
for (ot,on), e in registry.items():
    fy = min(e['years']) if e['years'] else '?'
    if fy in YEARS:
        year_new_unique[fy][e['nat']] += 1

# 5. Most-modified unique objects (hotspots)
hotspots = sorted(registry.values(), key=lambda x: -x['mods'])[:50]

# 6. Config table analysis (TABU objects specifically)
cfg_tables = {on: {'mods':e['mods'],'users':len(e['users']),'years':sorted(e['years']),
                   'obj_type':e['ot']}
              for (ot,on),e in registry.items()
              if e['ts'] in ('CFG',) and e['mods'] >= 2}
top_cfg = sorted(cfg_tables.items(), key=lambda x: -x[1]['mods'])[:60]

# 7. Package groups (Z-prefix families) with unique count
import re as _re
PKG_MAP = [
    (r'^CL_HRPADUN','CL_HRPADUN_*','HCM'),
    (r'^HRPADUN','HRPADUN_*','HCM'),
    (r'^T7UN','T7UN_*','HCM'),
    (r'^PUN_','PUN_*','HCM'),
    (r'^ZHR_PAY','ZHCM_Payroll','HCM'),
    (r'^ZHR_','ZHCM_General','HCM'),
    (r'^YHR_EDUR','YHCM_EDUR','HCM'),
    (r'^YHR_','YHCM_General','HCM'),
    (r'^ZPAY_','ZPAY_*','HCM'),
    (r'^ZPSM_','ZPSM_*','PSM/FM'),
    (r'^ZFM_','ZFM_*','PSM/FM'),
    (r'^RFFMCY','RFFMCY_*','PSM/FM'),
    (r'^ZFI_','ZFI_*','FI'),
    (r'^YNAZ','YNAZ_*','FI'),
    (r'^DMEE_','ZDMEE_*','FI'),
    (r'^ZCO_','ZCO_*','CO'),
    (r'^ZFO_','ZFO_Fiori','Fiori/UI'),
    (r'^YFO_','YFO_Fiori','Fiori/UI'),
    (r'^ZCRP','ZCRP_*','Fiori/UI'),
    (r'^YCRP','YCRP_*','Fiori/UI'),
    (r'^ZOMWF','ZOMWF_WF','Workflow'),
    (r'^ZWF_','ZWF_*','Workflow'),
    (r'^Y_FO_HR_','Y_FO_HR Roles','Security'),
    (r'^Y_FI_','Y_FI Roles','Security'),
    (r'^Y_HCM_|^Y_HR_','Y_HCM/HR Roles','Security'),
    (r'^Y_ICTP','Y_ICTP Roles','Security'),
]

pkg_data = defaultdict(lambda:{'dom':'','unique':0,'mods':0,'users':set(),'years':set(),
                                'types':Counter(),'sample_objs':[]})
for (ot,on), e in registry.items():
    if e['nat'] in ('EPI-USE','SEC','CFG'): continue  # keep only dev + data model
    matched = False
    for rx, pkg, dom in PKG_MAP:
        if _re.match(rx, on, _re.I):
            pkg_data[pkg]['dom']   = dom
            pkg_data[pkg]['unique']  += 1
            pkg_data[pkg]['mods']    += e['mods']
            pkg_data[pkg]['users']   |= e['users']
            pkg_data[pkg]['years']   |= e['years']
            pkg_data[pkg]['types'][e['ts']] += 1
            if len(pkg_data[pkg]['sample_objs']) < 5:
                pkg_data[pkg]['sample_objs'].append(on)
            matched = True
            break
    if not matched and on.upper().startswith(('Z','Y')):
        first5 = on.upper()[:5]
        pkg_data[first5]['dom']    = 'Custom'
        pkg_data[first5]['unique'] += 1
        pkg_data[first5]['mods']   += e['mods']
        pkg_data[first5]['users']  |= e['users']
        pkg_data[first5]['years']  |= e['years']
        pkg_data[first5]['types'][e['ts']] += 1

top_pkgs = sorted(pkg_data.items(), key=lambda x: -x[1]['unique'])[:40]

# ── Serialize output ──────────────────────────────────────────────────────────
def ser(v):
    if isinstance(v, set): return sorted(v)
    if isinstance(v, Counter): return dict(v)
    return v

out = {
    'summary': {
        'total_transport_pairs': sum(e['mods'] for e in registry.values()),
        'unique_objects': len(registry),
        'unique_dev':  sum(1 for e in registry.values() if e['nat']=='DEV'),
        'unique_cfg':  sum(1 for e in registry.values() if e['nat']=='CFG'),
        'unique_sec':  sum(1 for e in registry.values() if e['nat']=='SEC'),
        'unique_epi':  sum(1 for e in registry.values() if e['nat']=='EPI-USE'),
        'avg_mods': round(sum(e['mods'] for e in registry.values())/len(registry),1),
    },
    'domain_unique': {d:{'unique':v['unique'],'mods':v['mods'],'users':len(v['users']),
                          'types':dict(v['types'])} for d,v in dom_summary.items()},
    'type_unique': {ts:{'unique':v['unique'],'mods':v['mods'],'users':len(v['users'])}
                    for ts,v in type_summary.items()},
    'user_unique': {u:{'touched':user_unique_touched[u],
                        'owned':  user_unique_owned[u],
                        'domains':user_domain_unique[u],
                        'types':  user_type_unique[u]}
                    for u in user_objects if user_unique_touched[u]>5},
    'year_new_unique': {yr:{nat:cnt for nat,cnt in d.items()} for yr,d in year_new_unique.items()},
    'hotspots': [{'ot':e['ot'],'on':e['on'],'ts':e['ts'],'dom':e['dom'],
                   'mods':e['mods'],'users':len(e['users']),'years':len(e['years'])}
                 for e in hotspots],
    'top_cfg_tables': [{'name':tbl,'mods':v['mods'],'users':v['users'],
                         'years':len(v['years']),'obj_type':v['obj_type']}
                        for tbl,v in top_cfg],
    'top_packages': [{
        'pkg':pkg,'dom':v['dom'],'unique':v['unique'],'mods':v['mods'],
        'users':len(v['users']),'years':len(v['years']),
        'types':dict(v['types']),'samples':v['sample_objs']
    } for pkg,v in top_pkgs if v['unique'] >= 3],
}

with open('cts_unique_objects.json','w',encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)

print(f"\nSaved cts_unique_objects.json")
print(f"\n=== REAL UNIQUE OBJECT COUNTS ===")
s = out['summary']
print(f"Transport pairs (raw):   {s['total_transport_pairs']:>7,}")
print(f"Unique objects (real):   {s['unique_objects']:>7,}")
print(f"  - Dev/Tech:            {s['unique_dev']:>7,}")
print(f"  - Config (TABU etc):   {s['unique_cfg']:>7,}")
print(f"  - Security roles:      {s['unique_sec']:>7,}")
print(f"  - EPI-USE:             {s['unique_epi']:>7,}")
print(f"Avg mods per object:     {s['avg_mods']:>7}x")

print("\nDomain (unique objects):")
for d,v in sorted(out['domain_unique'].items(), key=lambda x:-x[1]['unique'])[:12]:
    print(f"  {d:<20} unique={v['unique']:>5,}  mods={v['mods']:>6,}  ratio={round(v['mods']/max(v['unique'],1),1)}x")

print("\nTop packages (unique objs):")
for p in out['top_packages'][:15]:
    print(f"  {p['pkg']:<25} unique={p['unique']:>4}  mods={p['mods']:>5}  dom={p['dom']}")

print("\nTop 15 config table hotspots:")
for c in out['top_cfg_tables'][:15]:
    print(f"  {c['name']:<35} {c['mods']:>4}x  users={c['users']}")
