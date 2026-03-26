"""
cts_full_classification.py  v2
==============================
Granular object-level classification of all 108,290 SAP objects.

DEVELOPMENT SUB-TYPES:
  DEV_REP    -- Reports / Programs (PROG, REPS includes, REPT, REPY)
  DEV_CLAS   -- ABAP Classes, Interfaces, Methods (CLAS, INTF, METH, C* sub-objects)
  DEV_FUGR   -- Function Groups / BAPIs / RFCs (FUGR, FUNC)
  DEV_WF     -- Workflows (SWFP, SWFT, SWED, SWFL, PDWS)
  DEV_ENH    -- Enhancements / BADIs (ENHO, ENHS, ENHD, ENHC)
  DEV_UI     -- Fiori / BSP / WebDynpro / WAPP (UI code)
  DEV_FORM   -- Forms: Smart Forms, SAPscript, DMEE payment formats
  DEV_MISC   -- Other dev: SHLP, MSAG, IDoc, OData metadata

CONFIGURATION SUB-TYPES:
  CFG_FI     -- FI/CO/PSM customizing (TABU entries in FI-namespace tables)
  CFG_HCM    -- HR/Payroll customizing
  CFG_SEC    -- Security: Roles (ACGR), Auth objects (PFCG)
  CFG_SYS    -- System/Basis config: Number ranges (NROB), params, screen variants
  CFG_GEN    -- General customizing

OTHER CATEGORIES:
  DATA_MODEL -- TABL, DTEL, DOMA, Views
  UI_TEXT    -- Text elements, Help texts
  INFRA      -- Packages (DEVC), Transactions (TRAN)
  DOC        -- Documentation, Notes
  TRANS_META -- RELE/MERG transport plumbing (not real objects)
  THIRD_PARTY-- EPI-USE Labs
  SAP_SYS    -- SAP/DDIC users
  OTHER      -- Not yet classified
"""
import json
from collections import defaultdict, Counter

# ─── TYPE MAP ─────────────────────────────────────────────────────────────────
TYPE_MAP = {
    # ── Reports & Programs ───────────────────────────────────────────────────
    'PROG':  'DEV_REP',
    'REPS':  'DEV_REP',   # Program include (source include of PROG)
    'REPT':  'DEV_REP',   # Program text include
    'REPY':  'DEV_REP',   # Program CUA include
    'REPO':  'DEV_REP',

    # ── Classes & Interfaces ─────────────────────────────────────────────────
    'CLAS':  'DEV_CLAS',
    'INTF':  'DEV_CLAS',
    'METH':  'DEV_CLAS',   # Class method (sub-object)
    'CINS':  'DEV_CLAS',   # Class include (source part)
    'CINC':  'DEV_CLAS',
    'CPUB':  'DEV_CLAS',   # Class public section
    'CPRO':  'DEV_CLAS',   # Class protected section
    'CPRI':  'DEV_CLAS',   # Class private section
    'CLSD':  'DEV_CLAS',   # Class definition
    'TYPE':  'DEV_CLAS',   # Type groups

    # ── Function Groups / BAPIs / RFCs ───────────────────────────────────────
    'FUGR':  'DEV_FUGR',   # Function group
    'FUNC':  'DEV_FUGR',   # Function module
    'FUGA':  'DEV_FUGR',   # Function group include

    # ── Workflows ────────────────────────────────────────────────────────────
    'SWFP':  'DEV_WF',
    'SWFT':  'DEV_WF',
    'SWED':  'DEV_WF',
    'SWFL':  'DEV_WF',
    'PDWS':  'DEV_WF',    # Workflow process definition
    'PCYC':  'DEV_WF',    # Workflow process cycle

    # ── Enhancements / BADIs ─────────────────────────────────────────────────
    'ENHO':  'DEV_ENH',
    'ENHS':  'DEV_ENH',
    'ENHD':  'DEV_ENH',
    'ENHC':  'DEV_ENH',

    # ── Fiori / BSP / Web Dynpro / UI ────────────────────────────────────────
    'WAPP':  'DEV_UI',    # SAPUI5 / Fiori app (JS, XML views)
    'SBYP':  'DEV_UI',    # BSP page
    'SBYL':  'DEV_UI',    # BSP layout
    'SBXP':  'DEV_UI',    # BSP extension
    'SMIM':  'DEV_UI',    # MIME objects (icons, CSS, JS in MIME repo)
    'WDYN':  'DEV_UI',
    'WDCA':  'DEV_UI',
    'WDCC':  'DEV_UI',
    'WDCO':  'DEV_UI',
    'WDYC':  'DEV_UI',   # Web Dynpro component
    'WDYV':  'DEV_UI',   # Web Dynpro view
    'WDYA':  'DEV_UI',   # Web Dynpro application
    'WAPA':  'DEV_UI',
    'W3MI':  'DEV_UI',
    'W3HT':  'DEV_UI',
    'W3UD':  'DEV_UI',
    'SICF':  'DEV_UI',   # ICF service registration
    'IWSV':  'DEV_UI',   # OData service
    'IWOM':  'DEV_UI',
    'IWSG':  'DEV_UI',
    'IOBJ':  'DEV_UI',

    # ── Forms & Output ────────────────────────────────────────────────────────
    'SSFO':  'DEV_FORM',
    'SFPF':  'DEV_FORM',
    'SFPS':  'DEV_FORM',
    'F30':   'DEV_FORM',   # SAPscript form
    'DMEE':  'DEV_FORM',   # Payment medium format tree
    'PFRM':  'DEV_FORM',   # Print form

    # ── Misc Dev ──────────────────────────────────────────────────────────────
    'SHLP':  'DEV_MISC',   # Search help
    'SOBJ':  'DEV_MISC',   # Business object
    'MSAG':  'DEV_MISC',   # Message class
    'MESS':  'DEV_MISC',   # Message
    'SPRX':  'DEV_MISC',   # Proxy
    'VARX':  'DEV_MISC',   # Report selection variant
    'SMDL':  'DEV_MISC',   # Semantic model
    'OSOA':  'DEV_MISC',   # BW object

    # ── Security / Roles ─────────────────────────────────────────────────────
    'ACGR':  'CFG_SEC',   # Activity Groups = Roles (PFCG)
    'PFCG':  'CFG_SEC',
    'ACID':  'CFG_SEC',   # Authorization check ID
    'AUTH':  'CFG_SEC',
    'SUSC':  'CFG_SEC',
    'SUSO':  'CFG_SEC',
    'SUCU':  'CFG_SEC',
    'STVI':  'CFG_SEC',
    'STOB':  'CFG_SEC',

    # ── HR/HCM Configuration ─────────────────────────────────────────────────
    'PDTS':  'CFG_HCM',
    'PDVS':  'CFG_HCM',
    'PDAT':  'CFG_HCM',
    'PSCC':  'CFG_HCM',
    'DTED':  'CFG_HCM',
    'DOMD':  'CFG_HCM',
    'TABD':  'CFG_HCM',   # HR cluster table data
    'SOTT':  'CFG_HCM',   # HCM object type definitions (OM)

    # ── General Customizing ───────────────────────────────────────────────────
    'TABU':  'CFG_GEN',   # Table entries (main customizing carrier)
    'VDAT':  'CFG_GEN',
    'VCLS':  'CFG_GEN',
    'CUST':  'CFG_GEN',
    'CUS0':  'CFG_GEN',
    'CUS1':  'CFG_GEN',
    'CUAD':  'CFG_GEN',
    'DYNT':  'CFG_GEN',
    'DYNP':  'CFG_GEN',
    'TDAT':  'CFG_GEN',
    'TOBJ':  'CFG_GEN',
    'PARA':  'CFG_GEN',
    'PARS':  'CFG_GEN',
    'AVAS':  'CFG_GEN',
    'PMKC':  'CFG_GEN',
    'VIED':  'CFG_GEN',
    'FSL':   'CFG_GEN',
    'LODE':  'CFG_GEN',  # BRF+ / logical unit config
    'SCVI':  'CFG_GEN',

    # ── System / Basis Config ─────────────────────────────────────────────────
    'NROB':  'CFG_SYS',   # Number range objects
    'TTYP':  'CFG_SYS',

    # ── Data Model ────────────────────────────────────────────────────────────
    'TABL':  'DATA_MDL',
    'DTEL':  'DATA_MDL',
    'DOMA':  'DATA_MDL',
    'INDX':  'DATA_MDL',
    'SQLT':  'DATA_MDL',
    'SQSC':  'DATA_MDL',
    'VIEW':  'DATA_MDL',

    # ── UI Text / Localization ────────────────────────────────────────────────
    'TEXT':  'UI_TEXT',
    'DOCU':  'UI_TEXT',
    'SHI3':  'UI_TEXT',
    'SHI6':  'UI_TEXT',

    # ── Infrastructure ────────────────────────────────────────────────────────
    'DEVC':  'INFRA',   # Packages
    'TRAN':  'INFRA',   # Transactions

    # ── Documentation ─────────────────────────────────────────────────────────
    'NOTE':  'DOC',
    'DOCT':  'DOC',
    'DOCV':  'DOC',
    'XPRA':  'DOC',

    # ── Transport Metadata (not real objects) ─────────────────────────────────
    'RELE':  'TRANS_META',
    'MERG':  'TRANS_META',
}

# Category groups for summary display
DEV_CATS    = ['DEV_REP','DEV_CLAS','DEV_FUGR','DEV_WF','DEV_ENH','DEV_UI','DEV_FORM','DEV_MISC']
CFG_CATS    = ['CFG_SEC','CFG_HCM','CFG_GEN','CFG_SYS']
OTHER_CATS  = ['DATA_MDL','UI_TEXT','INFRA','DOC','TRANS_META','OTHER']
ALL_CATS    = DEV_CATS + CFG_CATS + OTHER_CATS

SAP_SYS_OWNERS = {'SAP','DDIC','BASIS','SAP_SUPPORT'}
YEARS = [str(y) for y in range(2017, 2027)]

def classify(obj_type):
    return TYPE_MAP.get(obj_type.strip().upper(), 'OTHER')

# ─── Load & Aggregate ─────────────────────────────────────────────────────────
with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

year_cat      = defaultdict(lambda: defaultdict(int))
user_year_cat = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
dev_pkg_year  = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
epiuse_yr     = defaultdict(int)
sapsys_yr     = defaultdict(int)

for t in raw['transports']:
    owner  = t.get('owner','').strip().upper()
    year   = t.get('date','')[:4]
    trkorr = t.get('trkorr','')
    objs   = t.get('objects', [])
    if year not in YEARS: continue
    if trkorr.upper().startswith('E9BK'):
        epiuse_yr[year] += len(objs); continue
    if owner in SAP_SYS_OWNERS:
        sapsys_yr[year] += len(objs); continue
    for o in objs:
        ot   = o.get('obj_type', o.get('OBJECT','')).strip().upper()
        pkg  = o.get('devclass', '').strip().upper() or '(no-pkg)'
        c    = classify(ot)
        year_cat[year][c]             += 1
        user_year_cat[owner][year][c] += 1
        if c.startswith('DEV'):
            dev_pkg_year[owner][year][pkg][ot] += 1

# ─── REPORT 1: YEAR TOTALS ────────────────────────────────────────────────────
SHORT = {
    'DEV_REP':'REP','DEV_CLAS':'CLAS','DEV_FUGR':'FUNC','DEV_WF':'WF',
    'DEV_ENH':'ENH','DEV_UI':'UI','DEV_FORM':'FORM','DEV_MISC':'MISC',
    'CFG_SEC':'SEC','CFG_HCM':'HCM','CFG_GEN':'CFG','CFG_SYS':'SYS',
    'DATA_MDL':'MDL','UI_TEXT':'TXT','INFRA':'INF','DOC':'DOC',
    'TRANS_META':'META','OTHER':'OTH',
}

print("=" * 130)
print("  GRANULAR OBJECT CLASSIFICATION BY YEAR  (108,290 objects, 2017-2026)")
print("  [DEVELOPMENT]             [CONFIG]        [INFRA/OTHER]")
print("  REP=Reports CLAS=Classes FUNC=FuncGroups WF=Workflow ENH=Enhancements UI=Fiori/BSP FORM=Forms")
print("  SEC=Roles/Auth HCM=HRConfig CFG=GeneralConfig MDL=DataModel META=TransportMeta")
print("=" * 130)

print(f"{'YEAR':<6}", end="")
for c in ALL_CATS: print(f" {SHORT[c]:>5}", end="")
print(f" {'EPI':>5} {'SAP':>4} {'TOTAL':>7}")
print("-" * 130)

grand = defaultdict(int)
for year in YEARS:
    print(f"{year:<6}", end="")
    tot = 0
    for c in ALL_CATS:
        v = year_cat[year][c]; grand[c] += v; tot += v
        print(f" {v:>5,}", end="") if v else print(f" {'':>5}", end="")
    epi = epiuse_yr[year]; sap = sapsys_yr[year]
    grand['EPI'] += epi; grand['SAP'] += sap
    print(f" {epi:>5,} {sap:>4,} {tot+epi+sap:>7,}")

print("-" * 130)
print(f"{'TOTAL':<6}", end="")
for c in ALL_CATS: print(f" {grand[c]:>5,}", end="")
print(f" {grand['EPI']:>5,} {grand['SAP']:>4,} {sum(grand.values()):>7,}")
pct_line = f"{'%':<6}"
tot = sum(grand.values()) or 1
for c in ALL_CATS: pct_line += f" {grand[c]/tot*100:>4.0f}%"
print(pct_line)
print("=" * 130)

# Summary: Total dev vs total config
total_dev = sum(grand[c] for c in DEV_CATS)
total_cfg = sum(grand[c] for c in CFG_CATS)
print(f"\n  SUMMARY: Dev={total_dev:,} ({total_dev/tot*100:.1f}%)  Config={total_cfg:,} ({total_cfg/tot*100:.1f}%)  EPI-USE={grand['EPI']:,} ({grand['EPI']/tot*100:.1f}%)")
print(f"  SIGNAL: {grand['TRANS_META']:,} objects are transport metadata (RELE/MERG) — not real SAP objects")

# ─── REPORT 2: USER PROFILES ──────────────────────────────────────────────────
user_totals = {u: sum(user_year_cat[u][y][c] for y in YEARS for c in ALL_CATS) for u in user_year_cat}
top_users   = sorted(user_year_cat.keys(), key=lambda u: -user_totals[u])

print(f"\n\n  USER PROFILES — granular object sub-type breakdown")
print(f"  {'USER':<22} {'REP':>5} {'CLAS':>6} {'FUNC':>5} {'WF':>4} {'ENH':>4} {'UI':>5} | {'SEC':>6} {'HCM':>6} {'CFG':>6} | {'MDL':>5} {'META':>5} {'OTH':>5}  PROFILE")
print(f"  {'-'*105}")

for user in top_users[:25]:
    if user_totals.get(user, 0) == 0: continue
    def s(c): return sum(user_year_cat[user][y][c] for y in YEARS)
    rp=s('DEV_REP'); cl=s('DEV_CLAS'); fu=s('DEV_FUGR'); wf=s('DEV_WF')
    en=s('DEV_ENH'); ui=s('DEV_UI');   fm=s('DEV_FORM')
    sec=s('CFG_SEC'); hcm=s('CFG_HCM'); cfg=s('CFG_GEN')+s('CFG_SYS')
    mdl=s('DATA_MDL'); meta=s('TRANS_META'); oth=s('OTHER')+s('UI_TEXT')
    total_dev_u = rp+cl+fu+wf+en+ui+fm
    total_cfg_u = sec+hcm+cfg
    # Profile
    if sec > 500:   profile = 'SECURITY ADMIN'
    elif hcm > 300 and total_dev_u < 100: profile = 'HCM FUNCTIONAL'
    elif ui > 500:  profile = 'FIORI DEV'
    elif cl > 1000: profile = 'CLASS DEV (OO)'
    elif rp > 200:  profile = 'REPORT DEV'
    elif total_dev_u > 200 and total_cfg_u > 100: profile = 'FULL-STACK'
    elif total_cfg_u > 200: profile = 'FUNCTIONAL'
    else: profile = 'MIXED'
    vals = f"{rp:>5} {cl:>6} {fu:>5} {wf:>4} {en:>4} {ui:>5} | {sec:>6} {hcm:>6} {cfg:>6} | {mdl:>5} {meta:>5} {oth:>5}"
    print(f"  {user.title():<22} {vals}  {profile}")

# ─── REPORT 3: DEVELOPER PACKAGE BREAKDOWN BY YEAR ───────────────────────────
print(f"\n\n{'='*90}")
print(f"  DEVELOPER DETAIL: Top packages worked on per year")
print(f"  Shows how each developer's work evolved across SAP packages/years")
print(f"{'='*90}")

DEVS = [u for u in top_users
        if sum(user_year_cat[u][y][c] for y in YEARS for c in DEV_CATS) > 30]

for user in DEVS[:15]:
    total_dev_u = sum(user_year_cat[user][y][c] for y in YEARS for c in DEV_CATS)
    if total_dev_u == 0: continue
    # Breakdown by dev sub-type
    by_type = {c: sum(user_year_cat[user][y][c] for y in YEARS) for c in DEV_CATS}
    type_str = ' | '.join(f"{SHORT[c]}:{by_type[c]}" for c in DEV_CATS if by_type[c] > 0)
    print(f"\n  [{user.title()}]  {total_dev_u:,} dev objects  ({type_str})")
    print(f"  {'Year':<6} {'DevObj':>7}  Top Packages (object count)")
    print(f"  {'-'*75}")
    for year in YEARS:
        d = sum(user_year_cat[user][year][c] for c in DEV_CATS)
        if d == 0: continue
        pkgs = {pkg: sum(ctr.values()) for pkg, ctr in dev_pkg_year[user][year].items()}
        top3 = sorted(pkgs.items(), key=lambda x: -x[1])[:3]
        pkg_str = '  |  '.join(f"{p}({c})" for p,c in top3)
        print(f"  {year:<6} {d:>7,}  {pkg_str}")
