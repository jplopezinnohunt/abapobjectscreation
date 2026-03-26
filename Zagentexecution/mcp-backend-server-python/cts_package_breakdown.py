"""
cts_package_breakdown.py
Breaks 27,938 unique objects into clear buckets:
  1. Security/Auth Admin (ACGR roles + AGR_*/USR*/UST* tables)
  2. User Management system tables
  3. HCM config tables (T7*, V_T5*, VDAT HCM views)
  4. FM/PSM config tables
  5. Real Custom Dev (Z/Y namespace programs, classes, etc.)
  6. SAP Standard (delivered objects pulled along in transports)
  7. EPI-USE (already excluded)
"""
import json, re
from collections import defaultdict, Counter

with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

YEARS     = [str(y) for y in range(2017, 2027)]
SKIP_META = {'RELE','MERG'}
SAP_SYS   = {'SAP','DDIC','BASIS','SAP_SUPPORT','WF-BATCH'}

# ── Package / Bucket Classification ──────────────────────────────────────────
def classify(ot, on):
    ot = ot.upper()
    on = on.upper()

    # 1. Security Roles (PFCG ACGR objects)
    if ot in ('ACGR', 'AUTH', 'ACID', 'SUSC'):
        return 'Security Roles (PFCG)'

    # 2. Authorization & User Management config tables
    if ot in ('TABU', 'CUS0', 'NROB'):
        if on.startswith('AGR_'):   return 'Auth Config (AGR_*)'
        if on.startswith('USR'):    return 'User Mgmt (USR*)'
        if on.startswith('UST'):    return 'User Mgmt (UST*)'
        if on.startswith('SUSR'):   return 'User Mgmt (SUSR*)'
        if on.startswith('PRGN'):   return 'Auth Config (PRGN*)'
        if on in ('SPERS_OBJ','SPERS'): return 'User Mgmt (SUSR*)'
        if on.startswith('TVDIR') or on.startswith('TDDAT'): return 'Auth Config (AGR_*)'

    # 3. HCM Config tables
    if ot in ('VDAT', 'PDTS', 'PDVS', 'TABD', 'SOTT', 'PDAT'):
        return 'HCM Config (V_T*/VDAT)'
    if ot == 'TABU':
        if re.match(r'^T7', on):         return 'HCM Config (V_T*/VDAT)'
        if re.match(r'^T5[0-9]', on):    return 'HCM Config (V_T*/VDAT)'
        if re.match(r'^V_T5', on):       return 'HCM Config (V_T*/VDAT)'
        if re.match(r'^PA0', on):        return 'HCM Config (V_T*/VDAT)'
        if on in ('MOLGA','T500L','T001P','T549','T549A','T508A'): return 'HCM Config (V_T*/VDAT)'
        # Fund Management / PSM config
        if re.match(r'^UCU', on):        return 'PSM/FM Config'
        if re.match(r'^FMFG', on):       return 'PSM/FM Config'
        if re.match(r'^UGWB', on):       return 'PSM/FM Config'
        if re.match(r'^FM', on):         return 'PSM/FM Config'

    # 4. Remaining generic TABU/config
    if ot in ('TABU', 'CUS0', 'NROB', 'TDAT', 'LODE', 'PARA', 'AVAS'):
        return 'General Config (TABU)'

    # 5. EPI-USE (excluded)
    # (handled separately by trkorr prefix)

    # 6. Real Custom Dev — Z/Y namespace
    if ot in ('PROG','REPS','REPT','REPO','REPY',
              'CLAS','INTF','METH','CINC','CINS','CPUB','CPRO','CPRI','CLSD',
              'FUGR','FUNC','FUGA',
              'SWFP','SWFT','SWED','SWFL','PDWS','PCYC',
              'ENHO','ENHS','ENHD','ENHC',
              'WAPP','SMIM','WDYC','WDYV','WDYA','W3MI','W3HT','SICF','WAPA',
              'IWSV','IWOM','IWSG',
              'SSFO','SFPF','SFPS','DMEE','F30','PFRM'):
        if on.startswith('Z') or on.startswith('Y'):
            return 'Custom Dev (Z/Y namespace)'
        return 'SAP-Delivered Dev Object'

    if ot in ('TABL','DETA','DOMA','DTEL','VIEW','INDX'):
        if on.startswith('Z') or on.startswith('Y'):
            return 'Custom Data Model (Z/Y)'
        return 'SAP Data Model'

    return 'Other (MISC/META)'

# ── Build unique object registry ──────────────────────────────────────────────
registry = {}  # (ot, on) -> bucket

for t in raw['transports']:
    owner  = t.get('owner','').strip().upper()
    year   = t.get('date','')[:4]
    trkorr = t.get('trkorr','')
    is_epi = trkorr.upper().startswith('E9BK')
    if year not in YEARS: continue
    if owner in SAP_SYS: continue

    for o in t.get('objects',[]):
        ot = o.get('obj_type', o.get('OBJECT','')).strip().upper()
        on = o.get('obj_name', o.get('OBJ_NAME','')).strip()
        if not ot or not on or ot in SKIP_META: continue
        key = (ot, on)
        if key not in registry:
            registry[key] = 'EPI-USE (3rd party)' if is_epi else classify(ot, on)

# ── Aggregate ──────────────────────────────────────────────────────────────────
bucket_counts = Counter()
bucket_objects = defaultdict(list)

for (ot,on), bucket in registry.items():
    bucket_counts[bucket] += 1
    if len(bucket_objects[bucket]) < 10:
        bucket_objects[bucket].append(f'{ot}: {on}')

total = sum(bucket_counts.values())
print(f'\n=== UNIQUE OBJECT BREAKDOWN — {total:,} objects ===\n')
print(f'{"Bucket":<40} {"Count":>6}  {"Pct":>6}  Examples')
print('-'*100)

ordered = [
    'Custom Dev (Z/Y namespace)',
    'Custom Data Model (Z/Y)',
    'SAP-Delivered Dev Object',
    'SAP Data Model',
    'HCM Config (V_T*/VDAT)',
    'PSM/FM Config',
    'General Config (TABU)',
    'Auth Config (AGR_*)',
    'User Mgmt (USR*)',
    'User Mgmt (UST*)',
    'User Mgmt (SUSR*)',
    'Auth Config (PRGN*)',
    'Security Roles (PFCG)',
    'EPI-USE (3rd party)',
    'Other (MISC/META)',
]

total_sec_admin = 0
total_real_custom = 0

for b in ordered:
    c = bucket_counts.get(b, 0)
    if c == 0: continue
    pct = c/total*100
    sample = bucket_objects.get(b,['—'])[0]
    print(f'  {b:<38} {c:>6,}  {pct:>5.1f}%  {sample}')
    if 'Auth' in b or 'User Mgmt' in b or 'Security Roles' in b:
        total_sec_admin += c
    if b in ('Custom Dev (Z/Y namespace)', 'Custom Data Model (Z/Y)'):
        total_real_custom += c

# Anything not in ordered list
for b, c in bucket_counts.most_common():
    if b not in ordered:
        pct = c/total*100
        sample = bucket_objects.get(b,['—'])[0]
        print(f'  {b:<38} {c:>6,}  {pct:>5.1f}%  {sample}')

print('-'*100)
print(f'  {"TOTAL":<38} {total:>6,}')
print(f'\n  >>> Security/Auth Admin objects:  {total_sec_admin:>5,}  ({total_sec_admin/total*100:.1f}%)')
print(f'  >>> Real Custom Dev (Z/Y):        {total_real_custom:>5,}  ({total_real_custom/total*100:.1f}%)')
print(f'  >>> EPI-USE (excl 3rd party):     {bucket_counts["EPI-USE (3rd party)"]:>5,}  ({bucket_counts["EPI-USE (3rd party)"]/total*100:.1f}%)')

# Save for dashboard
out = {
    'buckets': dict(bucket_counts),
    'total': total,
    'sec_admin_total': total_sec_admin,
    'custom_dev_total': total_real_custom,
    'bucket_samples': {b: bucket_objects[b] for b in bucket_objects},
}
with open('cts_pkg_breakdown.json','w',encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)
print('\nSaved cts_pkg_breakdown.json')
