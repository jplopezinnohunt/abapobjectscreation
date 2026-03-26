"""
cts_domain_year_type.py
=======================
3-dimensional view: DOMAIN x YEAR x OBJECT_TYPE

Functional domain is inferred from object name prefixes:
  ZHR_* / YHR_* / CL_HR* / ZPAY_* / T7UN*   -> HCM
  ZFI_* / YNAZ* / NAZFI* / DMEE*             -> FI
  ZPSM_* / ZFM_* / ZFMF* / RFFM*            -> PSM/FM
  ZCO_* / COST* / KO* / GGB0*               -> CO
  YQUI* / YWAPP* / YWD_* / WAPP* / ZOMWF*   -> FIORI
  Y_FO_HR* / Y_FI_* / ACGR entries          -> SECURITY
  ZGLO_* / Z_* (generic)                     -> GENERIC_CUSTOM
  CL_* (SAP-own) / no-Z prefix              -> SAP_STANDARD
  everything else                             -> UNKNOWN
"""
import json, re
from collections import defaultdict, Counter

# ─── Domain inference from object name ───────────────────────────────────────
DOMAIN_RULES = [
    # Security roles first (obj type better classifier)
    (['ACGR','PFCG','AUTH','ACID','SUSC','SUSO'],  None,    'SECURITY'),
    # HCM / Payroll
    (None, [r'^ZHR_', r'^YHR_', r'^ZPAY_', r'^CL_HRPADUN', r'^CL_HR',
            r'^ZCL_PAY', r'^T7UN', r'^HRPADUN', r'^ZN\d{2}',
            r'^PUN_', r'^HRSFI_', r'^YWD_VALID', r'^CL_FAA_',
            r'^ZHR', r'^YHR', r'^ZN[0-9]'], 'HCM'),
    # Public Sector / Funds Mgmt
    (None, [r'^ZPSM_', r'^ZFM_', r'^ZFMF', r'^RFFM', r'^YFBI',
            r'^RFFMCY', r'^RFFMKU', r'^ZFMG'], 'PSM_FM'),
    # Financial Accounting
    (None, [r'^ZFI_', r'^YNAZ', r'^NAZFI', r'^PAYM/', r'^ZFI',
            r'^YQFI', r'^DMEE_', r'^PAYM', r'^FI_'], 'FI'),
    # Controlling
    (None, [r'^ZCO_', r'^COST', r'^GGB0', r'^KE3', r'^KO'], 'CO'),
    # Fiori / UI5 / BSP apps — check obj_name patterns
    (['WAPP','SBYP','SBYL','WDYC','WDYV','WDYA','SMIM','SBXP'], None, 'FIORI_UI'),
    (None, [r'^YHR_EDUR', r'^ZOMWF', r'^YWD_', r'^YWAPP',
            r'^YFI_', r'^ZENH_DOCX', r'^ZCRP'], 'FIORI_UI'),
    # OData / Gateway services
    (['IWSV','IWOM','IWSG'],                        None,    'ODATA_SVC'),
    # Workflow
    (['SWFP','SWFT','SWED','SWFL','PDWS'],          None,    'WORKFLOW'),
    # Generic Z-custom (catch-all for unicode Z/Y namespace)
    (None, [r'^Z[A-Z]', r'^Y[A-Z]'],               'CUSTOM_GENERIC'),
    # SAP standard namespace (A-N, no Z/Y prefix)
    (None, [r'^CL_', r'^IF_', r'^LCL_', r'^T[0-9A-Z]{3}',
            r'^MARA', r'^BKPF'],                    'SAP_STANDARD'),
]

def infer_domain(obj_type: str, obj_name: str) -> str:
    ot = obj_type.strip().upper()
    on = obj_name.strip().upper()
    for type_filter, name_patterns, domain in DOMAIN_RULES:
        # Check type filter
        if type_filter and ot not in [t.upper() for t in type_filter]:
            continue
        # If only type filter (no name pattern needed)
        if type_filter and name_patterns is None:
            return domain
        # Check name patterns
        if name_patterns:
            for pat in name_patterns:
                if re.match(pat, on, re.IGNORECASE):
                    return domain
    return 'OTHER'

# ─── Granular type classification ─────────────────────────────────────────────
TYPE_MAP = {
    'PROG':'REP','REPS':'REP','REPT':'REP','REPY':'REP','REPO':'REP',
    'CLAS':'CLAS','INTF':'CLAS','METH':'CLAS','CINS':'CLAS','CINC':'CLAS',
    'CPUB':'CLAS','CPRO':'CLAS','CPRI':'CLAS','CLSD':'CLAS',
    'FUGR':'FUNC','FUNC':'FUNC','FUGA':'FUNC',
    'SWFP':'WF','SWFT':'WF','SWED':'WF','SWFL':'WF','PDWS':'WF','PCYC':'WF',
    'ENHO':'ENH','ENHS':'ENH','ENHD':'ENH','ENHC':'ENH',
    'WAPP':'UI','SBYP':'UI','SBYL':'UI','SBXP':'UI','SMIM':'UI',
    'WDYN':'UI','WDYC':'UI','WDYV':'UI','WDYA':'UI',
    'WAPA':'UI','W3MI':'UI','W3HT':'UI','W3UD':'UI','SICF':'UI',
    'IWSV':'UI','IWOM':'UI','IWSG':'UI','IOBJ':'UI',
    'SSFO':'FORM','SFPF':'FORM','SFPS':'FORM','F30':'FORM','DMEE':'FORM','PFRM':'FORM',
    'TABL':'MDL','DTEL':'MDL','DOMA':'MDL','INDX':'MDL','SQLT':'MDL','VIEW':'MDL',
    'TABU':'CFG','CUS0':'CFG','CUS1':'CFG','NROB':'CFG','TDAT':'CFG',
    'TOBJ':'CFG','LODE':'CFG','SCVI':'CFG','PARA':'CFG','AVAS':'CFG',
    'PDTS':'HCM_CFG','PDVS':'HCM_CFG','PDAT':'HCM_CFG','TABD':'HCM_CFG','SOTT':'HCM_CFG',
    'ACGR':'SEC','PFCG':'SEC','AUTH':'SEC','ACID':'SEC','SUSC':'SEC',
    'TYPE':'MISC','SHLP':'MISC','SOBJ':'MISC','MSAG':'MISC','VARX':'MISC',
    'DEVC':'INFRA','TRAN':'INFRA',
    'TEXT':'TXT','DOCU':'TXT','SHI3':'TXT','SHI6':'TXT',
    'NOTE':'DOC','DOCT':'DOC','XPRA':'DOC',
    'RELE':'META','MERG':'META',
}
def classify(ot): return TYPE_MAP.get(ot.strip().upper(), 'OTH')

SAP_SYS = {'SAP','DDIC','BASIS','SAP_SUPPORT'}
YEARS = [str(y) for y in range(2017, 2027)]

# ─── Load & aggregate ─────────────────────────────────────────────────────────
with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

# [domain][year][type_short] = count
domain_year_type = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
# [user][domain] = count  (total dev objects for profile building)
user_domain      = defaultdict(lambda: defaultdict(int))
# [year][domain] = count (totals for year summary)
year_domain      = defaultdict(lambda: defaultdict(int))

skipped_epi = skipped_sap = 0

for t in raw['transports']:
    owner  = t.get('owner','').strip().upper()
    year   = t.get('date','')[:4]
    trkorr = t.get('trkorr','')
    if year not in YEARS: continue
    if trkorr.upper().startswith('E9BK'): skipped_epi += 1; continue
    if owner in SAP_SYS: skipped_sap += 1; continue

    for o in t.get('objects', []):
        ot   = o.get('obj_type', o.get('OBJECT','')).strip().upper()
        on   = o.get('obj_name', o.get('OBJ_NAME','')).strip()
        tc   = classify(ot)
        if tc in ('META','DOC'): continue   # exclude transport plumbing
        dom  = infer_domain(ot, on)
        domain_year_type[dom][year][tc] += 1
        user_domain[owner][dom] += 1
        year_domain[year][dom]  += 1

# ─── REPORTS ─────────────────────────────────────────────────────────────────

DOMAINS = ['HCM','FIORI_UI','FI','PSM_FM','SECURITY','WORKFLOW','ODATA_SVC',
           'CO','CUSTOM_GENERIC','SAP_STANDARD','OTHER']
TYPE_COLS = ['REP','CLAS','FUNC','WF','ENH','UI','FORM','CFG','HCM_CFG','MDL','SEC','MISC','INFRA','TXT','OTH']
TYPE_LABEL = {'REP':'Reports','CLAS':'Classes','FUNC':'Func/RFC','WF':'Workflow',
              'ENH':'Enh/BADI','UI':'Fiori/BSP','FORM':'Forms','CFG':'Config',
              'HCM_CFG':'HCM-Cfg','MDL':'DataModel','SEC':'Roles','MISC':'Misc',
              'INFRA':'Infra','TXT':'Texts','OTH':'Other'}

print("=" * 100)
print("  FUNCTIONAL DOMAIN x YEAR x OBJECT TYPE  (excluding EPI-USE, SAP system, transport metadata)")
print("=" * 100)

# ── Table 1: Domain totals per year ─────────────────────────────────────────
dom_short = {'HCM':'HCM','FIORI_UI':'FIORI','FI':'FI','PSM_FM':'PSM',
             'SECURITY':'SEC','WORKFLOW':'WF','ODATA_SVC':'ODATA','CO':'CO',
             'CUSTOM_GENERIC':'CUST','SAP_STANDARD':'SAP-STD','OTHER':'OTH'}

print(f"\n  DOMAIN TOTALS BY YEAR")
print(f"  {'YEAR':<6}", end='')
for d in DOMAINS: print(f" {dom_short[d]:>8}", end='')
print(f"  {'TOTAL':>7}")
print(f"  {'-'*95}")

for year in YEARS:
    print(f"  {year:<6}", end='')
    tot = 0
    for d in DOMAINS:
        v = year_domain[year].get(d, 0)
        tot += v
        print(f" {v:>8,}", end='') if v else print(f" {'':>8}", end='')
    print(f"  {tot:>7,}")

grand_dom = {d: sum(year_domain[y].get(d,0) for y in YEARS) for d in DOMAINS}
print(f"  {'-'*95}")
print(f"  {'TOTAL':<6}", end='')
for d in DOMAINS: print(f" {grand_dom[d]:>8,}", end='')
print(f"  {sum(grand_dom.values()):>7,}")

print()
print("=" * 100)

# ── Table 2: Per domain — object type breakdown ───────────────────────────────
print(f"\n  OBJECT TYPE BREAKDOWN PER DOMAIN")
print(f"  {'DOMAIN':<16}", end='')
for tc in TYPE_COLS: print(f" {tc:>7}", end='')
print(f"  {'TOTAL':>7}")
print(f"  {'-'*118}")

for d in DOMAINS:
    total = sum(domain_year_type[d][y][tc] for y in YEARS for tc in TYPE_COLS)
    if total == 0: continue
    print(f"  {dom_short[d]:<16}", end='')
    for tc in TYPE_COLS:
        v = sum(domain_year_type[d][y].get(tc,0) for y in YEARS)
        print(f" {v:>7,}", end='') if v else print(f" {'':>7}", end='')
    print(f"  {total:>7,}")

print()
print("=" * 100)

# ── Table 3: Deep dive per domain — year x type ───────────────────────────────
TOP_DOMAINS = ['HCM','FIORI_UI','FI','PSM_FM','SECURITY']
for d in TOP_DOMAINS:
    dom_total = sum(domain_year_type[d][y][tc] for y in YEARS for tc in TYPE_COLS)
    if dom_total == 0: continue
    print(f"\n  [{dom_short[d]}] Domain — {dom_total:,} total objects — year x type")
    active_types = [tc for tc in TYPE_COLS
                    if sum(domain_year_type[d][y].get(tc,0) for y in YEARS) > 0]
    print(f"  {'Year':<6}", end='')
    for tc in active_types: print(f" {tc:>7}", end='')
    print(f"  {'TOTAL':>7}")
    print(f"  {'-'*75}")
    for year in YEARS:
        tot = sum(domain_year_type[d][year].get(tc,0) for tc in active_types)
        if tot == 0: continue
        print(f"  {year:<6}", end='')
        for tc in active_types:
            v = domain_year_type[d][year].get(tc,0)
            print(f" {v:>7,}", end='') if v else print(f" {'':>7}", end='')
        print(f"  {tot:>7,}")

# ── Table 4: User → Domain profile ───────────────────────────────────────────
print(f"\n\n{'='*100}")
print(f"  USER x DOMAIN PROFILE  (object count by functional area — reveals specialization)")
print(f"{'='*100}")
print(f"  {'USER':<22}", end='')
for d in DOMAINS: print(f" {dom_short[d]:>8}", end='')
print()
print(f"  {'-'*100}")

user_totals = {u: sum(user_domain[u].values()) for u in user_domain}
top_users = sorted(user_domain.keys(), key=lambda u: -user_totals[u])

for user in top_users[:25]:
    if user_totals[user] < 5: continue
    print(f"  {user.title():<22}", end='')
    for d in DOMAINS:
        v = user_domain[user].get(d, 0)
        print(f" {v:>8,}", end='') if v else print(f" {'':>8}", end='')
    print()
