"""
cts_package_config_data.py
Extracts:
  1. Package browser: prefix groups from Z/Y object names → dev package families
  2. Config element drill-down: specific tables from TABU entries, roles from ACGR, etc.
  3. Per-package: object types, top users, years active
  4. Per-config-table: count, top users, years
"""
import json, re
from collections import defaultdict

SKIP_META = {'RELE','MERG'}
SAP_SYS   = {'SAP','DDIC','BASIS','SAP_SUPPORT'}
YEARS     = [str(y) for y in range(2017, 2027)]

# ── Package prefix grouping rules ────────────────────────────────────────────
# We infer "package family" from object name prefix (best proxy for DEVCLASS)
# Rule: (regex, package_label, domain)
PKG_RULES = [
    (r'^ZHR_?PAY',    'ZHCM_PAYROLL',   'HCM'),
    (r'^ZHR_',        'ZHCM_GENERAL',   'HCM'),
    (r'^YHR_?EDUR',   'YHCM_EDUR',      'HCM'),
    (r'^YHR_',        'YHCM_GENERAL',   'HCM'),
    (r'^CL_HRPADUN',  'CL_HRPADUN_*',   'HCM'),
    (r'^HRPADUN',     'HRPADUN_*',      'HCM'),
    (r'^PUN_',        'PUN_*',          'HCM'),
    (r'^T7UN',        'T7UN_*',         'HCM'),
    (r'^ZPAY_',       'ZPAY_*',         'HCM'),
    (r'^ZPSM_',       'ZPSM_*',         'PSM/FM'),
    (r'^ZFM_',        'ZFM_*',          'PSM/FM'),
    (r'^RFFMCY',      'RFFMCY_*',       'PSM/FM'),
    (r'^ZFI_',        'ZFI_*',          'FI'),
    (r'^YNAZ',        'YNAZ_*',         'FI'),
    (r'^DMEE_',       'ZDMEE_PAYMENT',  'FI'),
    (r'^PAYM',        'ZPAYMENT_*',     'FI'),
    (r'^ZCO_',        'ZCO_*',          'CO'),
    (r'^ZFO_',        'ZFO_FIORI',      'Fiori'),
    (r'^YFO_',        'YFO_FIORI',      'Fiori'),
    (r'^YHR_FIORI',   'YHR_FIORI',      'Fiori'),
    (r'^ZCRP',        'ZCRP_*',         'Fiori'),
    (r'^YCRP',        'YCRP_*',         'Fiori'),
    (r'^ZOMWF',       'ZOMWF_*',        'Workflow'),
    (r'^ZWF_',        'ZWF_*',          'Workflow'),
    (r'^Y_FO_HR_',    'Y_FO_HR_ROLES',  'Security'),
    (r'^Y_FI_',       'Y_FI_ROLES',     'Security'),
    (r'^Y_HCM_',      'Y_HCM_ROLES',    'Security'),
    (r'^Y_HR_',       'Y_HR_ROLES',     'Security'),
    (r'^Z[A-Z]{1,2}_','Z_MISC_*',       'Custom'),
    (r'^Z',           'Z_OTHER',         'Custom'),
    (r'^Y',           'Y_OTHER',         'Custom'),
]

def get_package(obj_type, obj_name):
    on = obj_name.strip().upper()
    for rx, pkg, dom in PKG_RULES:
        if re.match(rx, on, re.I):
            return pkg, dom
    return None, None

# Config element classification by obj_type
CFG_TYPES = {'TABU','NROB','CUS0','TDAT','LODE','PDTS','PDVS','TABD','SOTT','PARA','AVAS'}
SEC_TYPES  = {'ACGR','PFCG','AUTH','ACID','SUSC'}

print("Loading cts_10yr_raw.json...")
with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

# ── Aggregation ───────────────────────────────────────────────────────────────
# pkg_data[pkg] = {domain, objects:{name:count}, types:{}, users:{}, years:{}}
pkg_data     = defaultdict(lambda: {'domain':'','objects':defaultdict(int),'types':defaultdict(int),
                                     'users':defaultdict(int),'years':defaultdict(int)})
# cfg_data[table_name] = {obj_type, count, users, years}
cfg_data     = defaultdict(lambda: {'obj_type':'','count':0,'users':defaultdict(int),'years':defaultdict(int)})
# role_data by role name prefix
role_data    = defaultdict(lambda: {'count':0,'users':defaultdict(int),'years':defaultdict(int)})

total_processed = 0
for t in raw['transports']:
    owner  = t.get('owner','').strip().upper()
    year   = t.get('date','')[:4]
    trkorr = t.get('trkorr','')
    if year not in YEARS: continue
    if trkorr.upper().startswith('E9BK'): continue
    if owner in SAP_SYS: continue

    for o in t.get('objects', []):
        ot = o.get('obj_type', o.get('OBJECT','')).strip().upper()
        on = o.get('obj_name', o.get('OBJ_NAME','')).strip()
        if ot in SKIP_META or not on: continue
        total_processed += 1

        # ─ Package inference (dev objects)
        pkg, dom = get_package(ot, on)
        if pkg and ot not in CFG_TYPES and ot not in SEC_TYPES:
            pkg_data[pkg]['domain'] = dom
            pkg_data[pkg]['objects'][on] += 1
            pkg_data[pkg]['types'][ot]   += 1
            pkg_data[pkg]['users'][owner] += 1
            pkg_data[pkg]['years'][year]  += 1

        # ─ Config element (TABU and friends)
        if ot in CFG_TYPES:
            cfg_data[on]['obj_type'] = ot
            cfg_data[on]['count']   += 1
            cfg_data[on]['users'][owner] += 1
            cfg_data[on]['years'][year]  += 1

        # ─ Security roles by prefix
        if ot in SEC_TYPES:
            prefix = re.sub(r'[^A-Z0-9_]','_',on.upper()[:12])
            # Group by first 8 chars as role family
            role_fam = on.upper()[:8]
            role_data[role_fam]['count'] += 1
            role_data[role_fam]['users'][owner] += 1
            role_data[role_fam]['years'][year]  += 1

print(f"Processed {total_processed:,} objects")

# ── Serialize ─────────────────────────────────────────────────────────────────
# Top packages (by total object modifications, min 5)
top_pkgs = sorted(
    [(pkg, sum(v['objects'].values())) for pkg,v in pkg_data.items() if sum(v['objects'].values())>=5],
    key=lambda x:-x[1]
)[:60]

pkg_out = {}
for pkg,_ in top_pkgs:
    v = pkg_data[pkg]
    total = sum(v['objects'].values())
    top_objs = sorted(v['objects'].items(), key=lambda x:-x[1])[:20]
    top_users= sorted(v['users'].items(),   key=lambda x:-x[1])[:8]
    top_types= sorted(v['types'].items(),   key=lambda x:-x[1])[:8]
    pkg_out[pkg] = {
        'domain': v['domain'],
        'total':  total,
        'unique_objs': len(v['objects']),
        'top_objects': top_objs,
        'top_users':   top_users,
        'top_types':   top_types,
        'by_year':     {yr:v['years'].get(yr,0) for yr in YEARS},
    }

# Top config tables (by count, min 3)
top_cfg = sorted(
    [(tbl,v) for tbl,v in cfg_data.items() if v['count']>=3],
    key=lambda x:-x[1]['count']
)[:80]

cfg_out = {}
for tbl,v in top_cfg:
    cfg_out[tbl] = {
        'obj_type':  v['obj_type'],
        'count':     v['count'],
        'top_users': sorted(v['users'].items(), key=lambda x:-x[1])[:6],
        'by_year':   {yr:v['years'].get(yr,0) for yr in YEARS},
    }

# Top role families
top_roles = sorted(role_data.items(), key=lambda x:-x[1]['count'])[:40]
roles_out = {rf:{'count':v['count'],
                  'top_users':sorted(v['users'].items(),key=lambda x:-x[1])[:4],
                  'by_year':{yr:v['years'].get(yr,0) for yr in YEARS}}
             for rf,v in top_roles}

out = {
    'years':   YEARS,
    'packages': pkg_out,
    'pkg_order': [p for p,_ in top_pkgs],
    'config_tables': cfg_out,
    'cfg_order': [tbl for tbl,_ in top_cfg],
    'role_families': roles_out,
    'role_order': [rf for rf,_ in top_roles],
}
with open('cts_package_config_data.json','w',encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, separators=(',',':'))

sz = sum(1 for _ in open('cts_package_config_data.json','rb').read())
print(f"Saved cts_package_config_data.json ({sz//1024}KB)")
print(f"\nTop 15 packages:")
for p,n in top_pkgs[:15]: print(f"  {p:<30} {n:>5,} obj-changes  | dom={pkg_data[p]['domain']}")
print(f"\nTop 15 config tables:")
for tbl,v in list(top_cfg)[:15]: print(f"  {tbl:<30} {v['count']:>5,} times  | type={v['obj_type']}")
print(f"\nTop 10 role families:")
for rf,v in list(top_roles)[:10]: print(f"  {rf:<15} {v['count']:>4,}")
