"""
cts_object_classification.py
============================
Classifies EVERY OBJECT individually as either:
  DEVELOPMENT  - Code objects (Programs, Classes, Function Groups, Enhancements, etc.)
  CONFIGURATION - Customizing/config (Table contents, View data, IMG config, etc.)
  INFRASTRUCTURE - Packages, Auth, System objects
  THIRD_PARTY  - EPI-USE Labs deliveries (TRKORR E9BK*)
  SAP_SYSTEM   - SAP/DDIC transported objects

Unlike the previous script which classified by transport header type (K/W),
this goes object-by-object — so a user who puts TABU entries in a Workbench
transport still has those counted as CONFIGURATION.

Output: per-user per-year summary + year totals.
"""
import json
from collections import defaultdict

# ─── Object type → category mapping ──────────────────────────────────────────
DEV_TYPES = {
    'PROG','REPS','REPT','REPY','REPO',   # Programs / reports
    'CLAS','INTF',                          # ABAP OO
    'FUGR','FUNC','FUGA',                   # Function groups/modules
    'ENHO','ENHS','ENHD',                   # Enhancements
    'XSLT','WDYN','WDCA','WDCC','WDCO',    # BSP/Web Dynpro
    'IWSV','IWOM','IWSG','IOBJ',           # OData services
    'WAPA','W3MI','W3HT','W3UD',           # BSP apps / MIME
    'SWFP','SWFT','SWED','SWFL',           # Workflow
    'TYPE','TTYP',                          # Type groups
    'MSAG','MESS',                          # Message classes
    'SSFO','SFPF','SFPS',                   # Smart forms / forms
    'SPRX',                                 # Proxy
    'SHLP',                                 # Search help
    'SOBJ',                                 # Business objects
}

CONFIG_TYPES = {
    'TABU',                                 # Table contents (customizing entries)
    'VDAT','VIEW','VCLS',                   # View maintenance / cluster views
    'CUST',                                 # Customizing objects
    'CUAD','DYNT','DYNP',                   # Screen painter (usually config-related)
    'NROB',                                 # Number range objects
    'PDTS','PDVS','PDAT',                   # Personnel development
    'PARA','PARS',                          # Parameters
    'SM30','SM31',                          # View cluster entries
}

DATA_MODEL_TYPES = {
    'TABL','DTEL','DOMA','INDX','SQLT',    # Data model
    'SQSC','TTYP',
}

INFRA_TYPES = {
    'DEVC',                                 # Packages
    'ACID','AUTH','SUSC','SUSO','PFCG',    # Authorization
    'TRAN',                                 # Transactions
    'DOCT','DOCV',                          # Documentation
    'XPRA',                                 # Migration / post-processing
    'STVI','STOB','SUCU',                   # Other system
}

def classify_object(obj_type: str) -> str:
    t = obj_type.strip().upper()
    if t in DEV_TYPES:        return 'DEVELOPMENT'
    if t in CONFIG_TYPES:     return 'CONFIGURATION'
    if t in DATA_MODEL_TYPES: return 'DATA_MODEL'
    if t in INFRA_TYPES:      return 'INFRASTRUCTURE'
    return 'OTHER'


# ─── Load data ────────────────────────────────────────────────────────────────
with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

YEARS = [str(y) for y in range(2017, 2027)]

# ─── Aggregate: [user][year][category] = {trx_set, obj_count} ────────────────
# Key: obj counts per (user, year, category)
stats = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
trx_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

grand_by_year = defaultdict(lambda: defaultdict(int))
epiuse_by_year = defaultdict(int)
sap_sys_by_year = defaultdict(int)

SAP_SYS_OWNERS = {'SAP', 'DDIC', 'BASIS', 'SAP_SUPPORT'}

for t in raw['transports']:
    owner  = t.get('owner','').strip().upper()
    year   = t.get('date','')[:4]
    trkorr = t.get('trkorr','')
    objs   = t.get('objects', [])

    if year not in YEARS:
        continue

    # Third-party EPI-USE
    if trkorr.upper().startswith('E9BK'):
        epiuse_by_year[year] += len(objs)
        continue

    # SAP system
    if owner in SAP_SYS_OWNERS:
        sap_sys_by_year[year] += len(objs)
        continue

    for o in objs:
        cat = classify_object(o.get('obj_type', o.get('OBJECT', '')))
        stats[owner][year][cat] += 1
        grand_by_year[year][cat] += 1


# ─── Print: Year totals table (100% of objects) ───────────────────────────────
CATS = ['DEVELOPMENT','CONFIGURATION','DATA_MODEL','INFRASTRUCTURE','OTHER']
CAT_SHORT = {'DEVELOPMENT':'DEV','CONFIGURATION':'CFG','DATA_MODEL':'MDL','INFRASTRUCTURE':'INF','OTHER':'OTH'}

print("=" * 110)
print("  100% OBJECT-LEVEL CLASSIFICATION BY YEAR")
print("  Every object individually classified: DEV=Code | CFG=Config | MDL=DataModel | INF=Infra | OTH=Other")
print("=" * 110)

header = f"{'YEAR':<6}"
for c in CATS:
    header += f" {CAT_SHORT[c]:>8}"
header += f" {'EPIUSE':>8} {'SAP_SYS':>8} {'TOTAL':>8}"
print(header)
print("-" * 110)

grand_total = defaultdict(int)
for year in YEARS:
    row   = f"{year:<6}"
    total = 0
    for c in CATS:
        v = grand_by_year[year][c]
        grand_total[c] += v
        total += v
        row += f" {v:>8,}"
    epi  = epiuse_by_year[year]
    sap  = sap_sys_by_year[year]
    grand_total['EPIUSE']   += epi
    grand_total['SAP_SYS']  += sap
    row += f" {epi:>8,} {sap:>8,} {total+epi+sap:>8,}"
    print(row)

# Grand total row
print("-" * 110)
row = f"{'TOTAL':<6}"
for c in CATS:
    row += f" {grand_total[c]:>8,}"
row += f" {grand_total['EPIUSE']:>8,} {grand_total['SAP_SYS']:>8,} {sum(grand_total.values()):>8,}"
print(row)

# Percentages
all_obj = sum(v for k, v in grand_total.items())
pct_row = f"{'%':<6}"
for c in CATS:
    pct_row += f" {grand_total[c]/all_obj*100:>7.1f}%"
pct_row += f" {grand_total['EPIUSE']/all_obj*100:>7.1f}% {grand_total['SAP_SYS']/all_obj*100:>7.1f}%"
print(pct_row)
print("=" * 110)


# ─── Per-user per-year table (DEV vs CFG objects) ─────────────────────────────
print("\n  PER USER PER YEAR: DEVELOPMENT objects vs CONFIGURATION objects")
print("  (Classified at object type level — one user can do both)\n")

# Sort users by total objects
user_totals = {u: sum(grand_total[c] for c in CATS
                      for year in YEARS
                      for _ in [True]
                      if True)
               for u in stats}
user_totals = {
    u: sum(stats[u][y][c] for y in YEARS for c in CATS)
    for u in stats
}
top_users = sorted(stats.keys(), key=lambda u: -user_totals[u])

# Header
hdr2 = f"{'USER':<22}"
for y in YEARS:
    hdr2 += f" {'D':>5}{'C':>5}"
hdr2 += f" {'TOT_D':>7} {'TOT_C':>7}  Profile"
print(hdr2)
sub2 = f"{'':22}"
for y in YEARS:
    sub2 += f"  {y[-2:]+'D':>4} {y[-2:]+'C':>4}"
print(sub2)
print("-" * 120)

for user in top_users[:30]:
    if user_totals[user] == 0:
        continue
    row = f"{user.title():<22}"
    tot_d = tot_c = 0
    for y in YEARS:
        d = stats[user][y].get('DEVELOPMENT', 0)
        c = stats[user][y].get('CONFIGURATION', 0)
        tot_d += d; tot_c += c
        row += f" {d:>5} {c:>5}"
    # Profile
    both = tot_d > 20 and tot_c > 20
    if both:       profile = 'DEV+CONFIG'
    elif tot_d > tot_c * 2: profile = 'DEVELOPER'
    elif tot_c > tot_d * 2: profile = 'FUNCTIONAL'
    else:          profile = 'MIXED'
    row += f" {tot_d:>7,} {tot_c:>7,}  {profile}"
    print(row)

print("-" * 120)

# Year totals for DEV vs CFG
print(f"\n  YEAR SUMMARY: Development vs Configuration (all UNESCO team members)\n")
print(f"  {'Year':<6} {'Dev Obj':>9} {'Cfg Obj':>9} {'MDL Obj':>9} {'Total':>9}  Dev%  Cfg%  Visual")
print(f"  {'-'*80}")
for year in YEARS:
    d   = grand_by_year[year].get('DEVELOPMENT', 0)
    c   = grand_by_year[year].get('CONFIGURATION', 0)
    m   = grand_by_year[year].get('DATA_MODEL', 0)
    tot = sum(grand_by_year[year].values()) or 1
    bar_d = '#' * int(d / tot * 30)
    bar_c = '.' * int(c / tot * 30)
    print(f"  {year:<6} {d:>9,} {c:>9,} {m:>9,} {tot:>9,}  {d/tot*100:>4.0f}% {c/tot*100:>4.0f}%  [{bar_d}{bar_c}]")
