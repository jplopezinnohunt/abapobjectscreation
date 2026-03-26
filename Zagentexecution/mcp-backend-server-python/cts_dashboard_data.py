"""
cts_dashboard_data.py - Generate all JSON data for the enhanced dashboard.
Produces cts_dashboard_data.json with:
  - user_year_domain:  {user -> {year -> {domain -> count}}}  
  - user_year_type:    {user -> {year -> {type_short -> count}}}
  - domain_user_year:  {domain -> {user -> {year -> count}}}
  - year_domain_type:  {year -> {domain -> {type -> count}}}
"""
import json, re
from collections import defaultdict

# ── Same classification maps as cts_domain_year_type.py ───────────────────────
TYPE_MAP = {
    'PROG':'REP','REPS':'REP','REPT':'REP','REPY':'REP','REPO':'REP',
    'CLAS':'CLAS','INTF':'CLAS','METH':'CLAS','CINS':'CLAS','CINC':'CLAS',
    'CPUB':'CLAS','CPRO':'CLAS','CPRI':'CLAS','CLSD':'CLAS',
    'FUGR':'FUNC','FUNC':'FUNC','FUGA':'FUNC',
    'SWFP':'WF','SWFT':'WF','SWED':'WF','SWFL':'WF','PDWS':'WF','PCYC':'WF',
    'ENHO':'ENH','ENHS':'ENH','ENHD':'ENH','ENHC':'ENH',
    'WAPP':'UI','SBYP':'UI','SBYL':'UI','SBXP':'UI','SMIM':'UI',
    'WDYN':'UI','WDYC':'UI','WDYV':'UI','WDYA':'UI',
    'WAPA':'UI','W3MI':'UI','W3HT':'UI','SICF':'UI',
    'IWSV':'UI','IWOM':'UI','IWSG':'UI',
    'SSFO':'FORM','SFPF':'FORM','SFPS':'FORM','F30':'FORM','DMEE':'FORM','PFRM':'FORM',
    'TABL':'MDL','DTEL':'MDL','DOMA':'MDL','INDX':'MDL','VIEW':'MDL',
    'TABU':'CFG','CUS0':'CFG','CUS1':'CFG','NROB':'CFG','TDAT':'CFG','LODE':'CFG',
    'TOBJ':'CFG','SCVI':'CFG','PARA':'CFG','AVAS':'CFG',
    'PDTS':'CFG','PDVS':'CFG','PDAT':'CFG','TABD':'CFG','SOTT':'CFG',
    'ACGR':'SEC','PFCG':'SEC','AUTH':'SEC','ACID':'SEC','SUSC':'SEC',
    'TYPE':'MISC','SHLP':'MISC','SOBJ':'MISC','MSAG':'MISC','VARX':'MISC',
    'DEVC':'INFRA','TRAN':'INFRA',
    'TEXT':'TXT','DOCU':'TXT','SHI3':'TXT','SHI6':'TXT',
    'RELE':'META','MERG':'META',
}

DOMAIN_RULES = [
    (['ACGR','PFCG','AUTH','ACID','SUSC'],  None,    'Security'),
    (None, [r'^ZHR_', r'^YHR_', r'^ZPAY_', r'^CL_HRPADUN', r'^CL_HR',
            r'^ZCL_PAY', r'^T7UN', r'^HRPADUN', r'^PUN_', r'^HRSFI_',
            r'^ZHR', r'^YHR', r'^ZN[0-9]', r'^CL_FAA_'], 'HCM'),
    (None, [r'^ZPSM_', r'^ZFM_', r'^ZFMF', r'^RFFM', r'^YFBI',
            r'^RFFMCY', r'^RFFMKU', r'^ZFMG'], 'PSM/FM'),
    (None, [r'^ZFI_', r'^YNAZ', r'^NAZFI', r'^ZFI', r'^YQFI',
            r'^DMEE_', r'^PAYM'], 'FI'),
    (None, [r'^ZCO_', r'^COST', r'^GGB0', r'^KE3', r'^KO'], 'CO'),
    (['WAPP','SBYP','SBYL','SBXP','SMIM','WDYC','WDYV','WDYA'], None, 'Fiori/UI'),
    (None, [r'^YHR_EDUR', r'^ZOMWF', r'^YWD_', r'^YWAPP',
            r'^YFI_', r'^ZCRP'], 'Fiori/UI'),
    (['IWSV','IWOM','IWSG'], None, 'OData'),
    (['SWFP','SWFT','SWED','SWFL','PDWS'], None, 'Workflow'),
    (None, [r'^Z[A-Z]', r'^Y[A-Z]'], 'Custom'),
    (None, [r'^CL_', r'^IF_', r'^T[0-9A-Z]{3}'], 'SAP Std'),
]

def infer_domain(ot, on):
    ot = ot.strip().upper(); on = on.strip().upper()
    for tf, np, dom in DOMAIN_RULES:
        if tf and ot not in [t.upper() for t in tf]: continue
        if tf and np is None: return dom
        if np:
            for p in np:
                if re.match(p, on, re.IGNORECASE): return dom
    return 'Other'

def classify(ot):
    return TYPE_MAP.get(ot.strip().upper(), 'OTH')

SAP_SYS = {'SAP','DDIC','BASIS','SAP_SUPPORT'}
YEARS   = [str(y) for y in range(2017, 2027)]
SKIP_META = {'META', 'DOC'}

print("Loading cts_10yr_raw.json...")
with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

# Aggregation structures
user_year_domain = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
user_year_type   = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
domain_user_year = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
year_domain_type = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
user_totals      = defaultdict(int)
epi_by_year      = defaultdict(int)

for t in raw['transports']:
    owner  = t.get('owner','').strip()
    year   = t.get('date','')[:4]
    trkorr = t.get('trkorr','')
    if year not in YEARS: continue

    if trkorr.upper().startswith('E9BK'):
        for o in t.get('objects', []):
            epi_by_year[year] += 1
        continue

    if owner.upper() in SAP_SYS: continue

    u = owner  # keep original case for display

    for o in t.get('objects', []):
        ot  = o.get('obj_type', o.get('OBJECT','')).strip().upper()
        on  = o.get('obj_name', o.get('OBJ_NAME','')).strip()
        tc  = classify(ot)
        if tc in SKIP_META: continue
        dom = infer_domain(ot, on)

        user_year_domain[u][year][dom] += 1
        user_year_type[u][year][tc]   += 1
        domain_user_year[dom][u][year] += 1
        year_domain_type[year][dom][tc]+= 1
        user_totals[u] += 1

# Identify top users (>50 objects)
top_users = sorted([u for u in user_totals if user_totals[u] > 50],
                   key=lambda u: -user_totals[u])[:20]
all_domains = ['HCM','Fiori/UI','Security','FI','PSM/FM','CO','OData','Workflow','Custom','SAP Std','Other','CFG']
all_types   = ['REP','CLAS','FUNC','WF','ENH','UI','FORM','CFG','MDL','SEC','MISC','INFRA','TXT','OTH']

def to_dict(dd):
    if isinstance(dd, defaultdict):
        return {k: to_dict(v) for k, v in dd.items()}
    return dd

data = {
    'years': YEARS,
    'top_users': top_users,
    'domains': all_domains,
    'types': all_types,
    'user_totals': {u: user_totals[u] for u in top_users},
    'user_year_domain':  {u: {yr: dict(user_year_domain[u].get(yr,{})) for yr in YEARS} for u in top_users},
    'user_year_type':    {u: {yr: dict(user_year_type[u].get(yr,{}))   for yr in YEARS} for u in top_users},
    'domain_user_year':  {d: {u: {yr: domain_user_year[d].get(u,{}).get(yr,0) for yr in YEARS} for u in top_users} for d in all_domains},
    'year_domain_type':  {yr: {d: dict(year_domain_type[yr].get(d,{})) for d in all_domains} for yr in YEARS},
    'epi_by_year':       {yr: epi_by_year.get(yr,0) for yr in YEARS},
}

with open('cts_dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print(f"Saved cts_dashboard_data.json")
print(f"Users: {len(top_users)}, Domains: {len(all_domains)}")
for u in top_users[:8]:
    print(f"  {u.title():<22} {user_totals[u]:>6,} objects")
