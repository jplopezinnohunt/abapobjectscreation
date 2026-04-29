"""Analyze MGIE + ICBA + ICTP creation transports, cross-check golden list."""
import sys
import json
from collections import defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base = 'Zagentexecution/mcp-backend-server-python/blueprint_output/'

def load(p):
    with open(base + p) as f:
        return json.load(f)

mgie_e = load('phase2_e071_MGIE.json')
mgie_k = load('phase2_e071k_MGIE.json')
icba_e = load('icba_e071_full.json')
icba_k = load('icba_e071k_full.json')
ictp_k = load('ictp_e071k_full.json')

print(f'MGIE  E071={len(mgie_e):6d}  E071K={len(mgie_k):6d}')
print(f'ICBA  E071={len(icba_e):6d}  E071K={len(icba_k):6d}')
print(f'ICTP  E071K={len(ictp_k):6d}')
print()


def extract_objnames(e_list, k_list=None):
    names = set()
    for r in e_list or []:
        n = r.get('OBJ_NAME', r.get('OBJNAME', '')).strip()
        if n:
            names.add(n)
    for r in k_list or []:
        n = r.get('OBJNAME', r.get('OBJ_NAME', '')).strip()
        if n:
            names.add(n)
    return names


mgie_objs = extract_objnames(mgie_e, mgie_k)
icba_objs = extract_objnames(icba_e, icba_k)
ictp_objs = extract_objnames(None, ictp_k)

print(f'Unique OBJNAMEs: MGIE={len(mgie_objs)} ICBA={len(icba_objs)} ICTP={len(ictp_objs)}')
all_objs = mgie_objs | icba_objs | ictp_objs
common = mgie_objs & icba_objs & ictp_objs
print(f'UNION: {len(all_objs)}  Common-to-all-3: {len(common)}')


def cat(n):
    n = n.strip().upper()
    if not n:
        return '99_empty'
    if n.startswith('D01K9') or n.startswith('M01K'):
        return '00_ChildTask'
    if n in ('T001', 'T001Q', 'T001A', 'T001B', 'T001V', 'T001Z', 'T001O', 'T001R', 'T001W'):
        return '01_CoCode'
    if n.startswith('T012') or n in ('TIBAN', 'BNKA') or n.startswith('T028') or n.startswith('T030H') or n.startswith('T018'):
        return '02_HouseBanks'
    if n.startswith('T042') or n.startswith('T033') or n.startswith('TBE') or n.startswith('TRGD'):
        return '03_PaymentProgram'
    if n.startswith('T043') or n.startswith('T169'):
        return '04_Tolerances'
    if n.startswith('T093') or n in ('ATPRA', 'AAACC_OBJ', 'T094', 'T095', 'T096', 'TABWG'):
        return '05_AssetAccounting'
    if n == 'SKB1':
        return '06_GL_CoCode'
    if n in ('SKA1', 'SKAT'):
        return '06b_GLMaster'
    if n == 'MARV':
        return '07_MMPeriod'
    if n in ('T035D', 'T035U', 'T003D', 'T003T', 'T003'):
        return '08_DocType_CashPlan'
    if n.startswith('T047'):
        return '09_Dunning'
    if n == 'T882' or n.startswith('FC'):
        return '10_Consolidation'
    if n.startswith('GB') or n in ('GGB1', 'GGB0'):
        return '11_ValSub_Rules'
    if n in ('TKA00', 'TKA01', 'TKA02', 'TKA07', 'TKA09', 'TKT09', 'TKA3J', 'V_TKA3', 'TKA30', 'TKA31'):
        return '12_ControllingArea'
    if n in ('CSKA', 'CSKU', 'CSKB', 'CSKS', 'CSKT', 'CEPC', 'CEPCT', 'AUFK',
             'SETCLASS', 'SETHEADER', 'SETHEADERT', 'SETLEAF', 'SETNODE'):
        return '12b_COMasterData'
    if n.startswith('FM') or 'FUND' in n or n in ('FMCI', 'FMFCTR', 'FMFINT', 'FMFCTRT', 'FMCIT') or n.startswith('FMUP'):
        return '13_FM'
    if n.startswith('V_T001') or 'CAREAMAINT' in n or 'ADDRESS' in n:
        return '14_ViewMetadata'
    if n.startswith('TPIR') or n == 'T542A' or n.startswith('T500') or n.startswith('T527') or n.startswith('T526'):
        return '15_HR_Travel'
    if n.startswith('T030'):
        return '16_GLAutoPost'
    if n.startswith('TCJ'):
        return '17_CashJournal'
    if n.startswith('TBPF') or n.startswith('FMHIV') or n.startswith('FMFUND'):
        return '18_BudgetPlanning'
    if n.startswith('T004'):
        return '19_ChartOfAccounts'
    if n.startswith('Y_'):
        return '20a_AuthRoles_Custom'
    pair_names = ('MGIE', 'ICTP', 'IIEP', 'UBO', 'UIL', 'UIS', 'UNES', 'IBE', 'ICBA', 'STEM')
    if any(p in n for p in pair_names) and len(n.replace(' ', '')) <= 10 and \
       not n.startswith(('V_', 'VC_', 'T', 'F', 'Y', 'Z', 'VV_', 'W_', 'CS', 'AQ')):
        return '20b_CrossCompanyPair'
    if n == 'GRW_SET' or n.startswith('KE34') or n.startswith('KE4'):
        return '21_COPA_Sets'
    if n == 'FINB_TR_DERIVATION' or n.startswith('FINB_'):
        return '22_CO_Derivation'
    if n.startswith('AQ') or n in ('USR12', 'USR13', 'UST12', 'AGR_TIMEB', 'SPERS_OBJ', 'SUSPR', 'USMD2001', 'USMD2003'):
        return '23_SystemTech'
    if n.startswith('T007') or 'TAXIN' in n or n.startswith('T683') or n.startswith('T005U'):
        return '24_Tax'
    if n.startswith('T024') or n.startswith('T16F') or n.startswith('T027') or \
       n.startswith('T005') or n.startswith('T162') or n.startswith('T161'):
        return '25_MMorg'
    if n in ('UNESGBB', 'UNESWRX') or n.startswith('T023') or n.startswith('T025'):
        return '26_AccountGroups'
    if n.startswith('V_') or n.startswith('VC_') or n.startswith('VV_'):
        return '14_ViewMetadata'
    if n.startswith('F01') or 'F01U' in n:
        return '20b_CrossCompanyPair'
    return '99_Other'


per_inst = {}
for name, objs in [('MGIE', mgie_objs), ('ICBA', icba_objs), ('ICTP', ictp_objs)]:
    d = defaultdict(set)
    for o in objs:
        d[cat(o)].add(o)
    per_inst[name] = d

all_cats = sorted(set(c for d in per_inst.values() for c in d))

print('\n=== Category presence across institutes ===')
print(f'{"Category":35s} {"MGIE":>6s} {"ICBA":>6s} {"ICTP":>6s} {"Union":>6s}')
for c in all_cats:
    mg = len(per_inst['MGIE'].get(c, set()))
    ic = len(per_inst['ICBA'].get(c, set()))
    it = len(per_inst['ICTP'].get(c, set()))
    un = len(per_inst['MGIE'].get(c, set()) | per_inst['ICBA'].get(c, set()) | per_inst['ICTP'].get(c, set()))
    print(f'  {c:35s} {mg:6d} {ic:6d} {it:6d} {un:6d}')

mgie_cats = set(per_inst['MGIE'].keys())
icba_cats = set(per_inst['ICBA'].keys())
ictp_cats = set(per_inst['ICTP'].keys())
icba_extra_cats = icba_cats - mgie_cats
ictp_extra_cats = ictp_cats - mgie_cats
print(f'\nICBA-only categories (vs MGIE): {sorted(icba_extra_cats)}')
print(f'ICTP-only categories (vs MGIE): {sorted(ictp_extra_cats)}')

print('\n=== Objects in ICBA or ICTP but NOT in MGIE (extras worth considering) ===')
extras = defaultdict(set)
for c in all_cats:
    mgie_set = per_inst['MGIE'].get(c, set())
    icba_set = per_inst['ICBA'].get(c, set())
    ictp_set = per_inst['ICTP'].get(c, set())
    only = (icba_set - mgie_set) | (ictp_set - mgie_set)
    for n in only:
        extras[c].add(n)

for c in sorted(extras):
    items = sorted(extras[c])
    if items:
        print(f'\n{c}: {len(items)} extra')
        for n in items[:25]:
            mark = []
            if n in per_inst['ICBA'].get(c, set()):
                mark.append('ICBA')
            if n in per_inst['ICTP'].get(c, set()):
                mark.append('ICTP')
            print(f'  {n:30s} [{" ".join(mark)}]')
        if len(items) > 25:
            print(f'  ... +{len(items) - 25} more')

# Cross-check against golden list (19 phases / 76 items with specific TCodes/tables)
golden_covered_tables = {
    # Phase 1 Foundation
    'T001', 'T001Q', 'T001A', 'T001B', 'T001W',
    # Phase 2 Banking/Payment
    'T012', 'T012D', 'T012K', 'T012T', 'T018V', 'T028', 'T030H', 'T035D', 'T035U',
    'T042', 'T042A', 'T042B', 'T042C', 'T042D', 'T042E', 'T042I', 'T042T', 'T042V',
    # Phase 3 GL
    'SKA1', 'SKAT', 'SKB1', 'T030',
    # Phase 4 ValSub
    'GB01C', 'GB02C', 'GB90', 'GB901', 'GB903', 'GB90T', 'GB92', 'GB921', 'GB922', 'GB92T', 'GB921T', 'GB93', 'GGB0', 'GGB1',
    # Phase 5 Tolerances
    'T043G', 'T043GT', 'T043S', 'T043ST', 'T043T', 'T169G', 'T169P', 'T169V',
    # Phase 6 Tax
    'T007V', 'T007A', 'T030K',
    # Phase 7 Dunning
    'T047',
    # Phase 8 AA
    'T093B', 'T093C', 'T093D', 'T093U', 'T093V', 'AAACC_OBJ', 'ATPRA',
    # Phase 9 CO
    'TKA00', 'TKA01', 'TKA02', 'TKA07', 'TKA09', 'TKT09', 'V_TKA3', 'CSKA', 'CSKB', 'CSKS', 'CSKU', 'CSKT',
    # Phase 10 FM
    'FM01', 'FMCI', 'FMFCTR', 'FMFINT', 'V_FMFUNDTYPE', 'FMUP00_F',
    # Phase 12 Consol
    'T882',
    # Phase 13 CashJournal
    'TCJ_C_JOURNALS', 'TCJ_CJ_NAMES', 'TCJ_PRINT', 'TCJ_TRANSACTIONS', 'TCJ_TRANS_NAMES',
    # Phase 15 HR/Travel
    'T500P', 'T542A', 'TPIR2', 'TPIR2T',
    # Phase 14 Cross-company (F01U - dynamic names)
    # Phase 16 MM (T024/T161/T162 etc if used)
    'T024', 'T024E', 'T024W',
    # Phase 19 Testing - no tables
    # Chart of accounts
    'T003', 'T003D', 'T003T', 'T004',
    # Account groups
    'T077S', 'T077K',
}

# Categories covered (approximate)
golden_categories = {
    '00_ChildTask', '01_CoCode', '02_HouseBanks', '03_PaymentProgram', '04_Tolerances',
    '05_AssetAccounting', '06_GL_CoCode', '06b_GLMaster', '07_MMPeriod', '08_DocType_CashPlan',
    '09_Dunning', '10_Consolidation', '11_ValSub_Rules', '12_ControllingArea', '12b_COMasterData',
    '13_FM', '14_ViewMetadata', '15_HR_Travel', '16_GLAutoPost', '17_CashJournal',
    '18_BudgetPlanning', '19_ChartOfAccounts', '20a_AuthRoles_Custom', '20b_CrossCompanyPair',
    '22_CO_Derivation', '24_Tax',
    # Not in golden yet:
    # '21_COPA_Sets', '25_MMorg', '26_AccountGroups', '23_SystemTech'
}

print('\n=== GOLDEN LIST COVERAGE AUDIT ===')
print('Categories found across 3 institutes but NOT explicitly in golden list:')
missing_cats = set(all_cats) - golden_categories
for c in sorted(missing_cats):
    union = per_inst['MGIE'].get(c, set()) | per_inst['ICBA'].get(c, set()) | per_inst['ICTP'].get(c, set())
    if union:
        print(f'\n  !!! {c}: {len(union)} objects')
        for n in sorted(union)[:15]:
            print(f'      {n}')
        if len(union) > 15:
            print(f'      ... +{len(union) - 15} more')

print('\n=== 99_Other deep inspection (may contain uncategorized activities) ===')
other_objs = per_inst['MGIE'].get('99_Other', set()) | per_inst['ICBA'].get('99_Other', set()) | per_inst['ICTP'].get('99_Other', set())
print(f'Total 99_Other objects union: {len(other_objs)}')
for n in sorted(other_objs)[:50]:
    print(f'  {n}')

summary = {
    'per_institute': {k: {c: sorted(list(v)) for c, v in d.items()} for k, d in per_inst.items()},
    'categories_present': {k: sorted(list(d.keys())) for k, d in per_inst.items()},
    'missing_from_golden': sorted(missing_cats),
    'stats': {
        'MGIE_objs': len(mgie_objs),
        'ICBA_objs': len(icba_objs),
        'ICTP_objs': len(ictp_objs),
        'union': len(all_objs),
        'common_all3': len(common),
    }
}
with open('Zagentexecution/mcp-backend-server-python/all3_institutes_analysis.json', 'w') as f:
    json.dump(summary, f, indent=2)
print('\nSaved: all3_institutes_analysis.json')
