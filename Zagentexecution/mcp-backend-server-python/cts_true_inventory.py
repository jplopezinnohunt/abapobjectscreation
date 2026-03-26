"""Rebuild true inventory JSON cleanly (no unicode separators)."""
import json, re, sys
from collections import defaultdict, Counter

with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

YEARS     = [str(y) for y in range(2017, 2027)]
SKIP_META = {'RELE','MERG'}
SAP_SYS   = {'SAP','DDIC','BASIS','SAP_SUPPORT','WF-BATCH'}

def classify(ot, on):
    on_up = on.upper()
    if ot in ('ACGR','AUTH','ACID','SUSC'):
        return 'Security Roles'
    if ot in ('TABU','CUS0'):
        if on_up.startswith('AGR_') or on_up in ('TVDIR','TDDAT','PRGN_STAT'):
            return 'Auth Config Tables'
        if on_up.startswith('USR') or on_up.startswith('UST') or on_up.startswith('SUSR') or on_up in ('SPERS_OBJ','SPERS'):
            return 'User Mgmt Tables'
        if re.match(r'^T7|^T5[0-9]|^PA[0-9]|^T50[0-9]|^T54|^T549|^MOLGA', on_up):
            return 'HCM Config Tables'
        if re.match(r'^UCU|^UGW|^FMFG|^FM[A-Z]', on_up):
            return 'PSM/FM Config'
    if ot in ('VDAT','CDAT','DATED','VIED'):
        return 'HCM Config Views'
    if ot in ('PDTS','PDVS','TABD','SOTT','PDAT','CUS1','TOBJ'):
        return 'HCM Config Objects'
    if ot in ('TABU','CUS0','NROB','TDAT','LODE','PARA','AVAS','SCVI','OSOA',
              'TTYP','VARX','PMKC','LODC','SOTU','TABT','CUAD'):
        return 'General Customizing'
    if ot in ('PROG','REPS','REPT','REPO','REPY'):
        return 'Custom Dev - Reports' if (on_up.startswith('Z') or on_up.startswith('Y')) else 'SAP Standard Dev'
    if ot in ('CLAS','INTF','METH','CINC','CINS','CPUB','CPRO','CPRI','CLSD'):
        return ('Custom Dev - Classes' if (on_up.startswith('Z') or on_up.startswith('Y') or
            on_up.startswith('CL_HRPADUN') or on_up.startswith('PUN_') or on_up.startswith('HRPADUN'))
            else 'SAP Standard Dev')
    if ot in ('FUGR','FUNC','FUGA'):
        return 'Custom Dev - Func/RFC' if (on_up.startswith('Z') or on_up.startswith('Y')) else 'SAP Standard Dev'
    if ot in ('ENHO','ENHS','ENHD','ENHC'):
        return 'Custom Dev - Enhancements'
    if ot in ('WAPP','SMIM','W3MI','W3HT','WAPA','WDYC','WDYV','WDYA'):
        return 'Custom Dev - Fiori/BSP'
    if ot in ('SBYP','SBYL','SBXP'):
        return 'BSP Auto-References'
    if ot in ('SICF','IWSV','IWOM','IWSG','IWMO','IWPR'):
        return 'Custom Dev - OData/ICF'
    if ot in ('SWFP','SWFT','SWED','SWFL','PDWS','PCYC'):
        return 'Custom Dev - Workflow'
    if ot in ('SSFO','SFPF','SFPS','F30','DMEE','PFRM','SFPI','FSL'):
        return 'Custom Dev - Forms'
    if ot in ('TABL','DOMA','DTEL','VIEW','INDX','DTED','DOMD','SMDL'):
        return ('Custom Data Model' if (on_up.startswith('Z') or on_up.startswith('Y') or
            on_up.startswith('PUN') or on_up.startswith('HRPADUN')) else 'SAP Data Model')
    if ot in ('MESS','DOCU','DOCT','TEXT','SHI3','SHI6','MSAG','MSAD','SOTR','SOTS'):
        return 'Texts & Docs'
    if ot in ('NOTE',):
        return 'SAP Notes'
    if ot in ('TRAN','DEVC','ADIR'):
        return 'Infra (TRAN/Package)'
    if ot in ('DYNP','DIAL'):
        return 'Screen Programs'
    if ot in ('SPRX',):
        return 'Enterprise Services'
    return 'Other'

registry = {}
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
            bucket = 'EPI-USE (3rd party)' if is_epi else classify(ot, on)
            registry[key] = {'bucket': bucket, 'mods': 0}
        registry[key]['mods'] += 1

buckets = defaultdict(lambda: {'unique':0,'mods':0,'samples':[]})
for (ot,on), v in registry.items():
    b = v['bucket']
    buckets[b]['unique'] += 1
    buckets[b]['mods']   += v['mods']
    if len(buckets[b]['samples']) < 3:
        buckets[b]['samples'].append(f'{ot}:{on[:30]}')

total = sum(v['unique'] for v in buckets.values())

SUMMARY_GROUPS = {
    'Custom Dev (all)': ['Custom Dev - Classes','Custom Dev - Reports','Custom Dev - Func/RFC',
                          'Custom Dev - Fiori/BSP','Custom Dev - OData/ICF','Custom Dev - Workflow',
                          'Custom Dev - Enhancements','Custom Dev - Forms','Custom Data Model'],
    'SAP Standard (pulled in)': ['SAP Standard Dev','SAP Data Model','BSP Auto-References',
                                   'Screen Programs','Enterprise Services'],
    'Security & Auth Admin': ['Security Roles','Auth Config Tables','User Mgmt Tables'],
    'Config / Customizing': ['HCM Config Views','HCM Config Tables','HCM Config Objects',
                               'PSM/FM Config','General Customizing'],
    'Docs & Infra': ['Texts & Docs','SAP Notes','Infra (TRAN/Package)'],
    'EPI-USE (3rd party)': ['EPI-USE (3rd party)'],
    'Other/Misc': ['Other'],
}

summary = {grp: sum(buckets.get(b,{}).get('unique',0) for b in members)
           for grp, members in SUMMARY_GROUPS.items()}

out = {
    'total': total,
    'buckets': {b: {'unique':v['unique'],'mods':v['mods'],'samples':v['samples'],
                    'avg_mods': round(v['mods']/v['unique'],1) if v['unique'] else 0}
                for b,v in buckets.items()},
    'summary_groups': summary,
    'summary_groups_detail': {grp: members for grp,members in SUMMARY_GROUPS.items()},
}
with open('cts_true_inventory.json','w',encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)

print(f'Total unique objects: {total:,}')
print('\nSummary Groups:')
for grp, cnt in sorted(summary.items(), key=lambda x:-x[1]):
    print(f'  {grp:<35} {cnt:>6,}  ({cnt/total*100:.1f}%)')
print('\nTop buckets:')
for b, v in sorted(buckets.items(), key=lambda x:-x[1]['unique'])[:20]:
    print(f'  {b:<40} unique={v["unique"]:>5,}  mods={v["mods"]:>7,}  avg={round(v["mods"]/v["unique"],1)}x')
print('\nSaved cts_true_inventory.json')
