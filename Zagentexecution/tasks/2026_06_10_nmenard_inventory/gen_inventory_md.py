"""Generate knowledge/abap-style-guide/N_MENARD-OBJECT-INVENTORY.md from nmenard_inventory.json."""
import json, sys
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
OUT = ROOT / 'knowledge' / 'abap-style-guide' / 'N_MENARD-OBJECT-INVENTORY.md'
d = json.load(open(HERE / 'nmenard_inventory.json', encoding='utf-8'))

pkg = d['package_objects']
ao = d['author_objects']
fms = d['fugr_fms']
DESC = d['descriptions']

# The 18 reference files already deep-read (style guide v1, CRP S-63/S-72)
PRIOR_DEEP = {
    'YIF_HRWF_MAIN', 'YIF_HRWF_ACTORS', 'YCL_HRWF_FACTORY', 'YCL_HRWF_MAIN',
    'YCL_HRWF_ACTORS', 'YCL_HRWF_MAIN_S1', 'YCL_HRWF_MAIN_I1', 'YCL_HRWF_MAIN_LX',
    'YCL_HRWF_MAIN_PX', 'YCL_HRWF_ACTORS_S1', 'YCL_HRWF_ACTORS_I1', 'YCL_HRWF_ACTORS_LX',
    'YCL_HRWF_OPERATION', 'YCL_WF_UTILITIES', 'YCL_CA_UTILITIES', 'YCL_HR_WF_MAIL_FACTORY',
    'YBUS1065', 'Y_HRPAWF_NEXT_ACTOR', 'YCX_HRWF',
    'YTHRWF_TYPE', 'YTHRWF_STEP', 'YTHRWF_STEPT', 'YTHRWF_ACT_DEF', 'YTHRWF_NOTIF',
}
# New objects deep-read in THIS session (s081 scan)
NEW_DEEP = {
    'YCL_HR_WF_MAIL_GENERATOR': 'mail engine base class (template method) — package YHR_OM_WF',
    'YCL_HR_WF_MAIL_GENERATOR_PA_S1': 'per-WF-type mail data provider',
    'YCL_HR_WF_MAIL_PA_S1_ACTION': 'per-event mail class (FINAL leaf)',
    'YHR_WF_PA_LIST_1': 'report-as-thin-shell + _BL class pattern',
    'YHR_WF_PA_LIST_1_DATA': 'DATA include of the 3-file report split',
    'YHR_WF_PA_LIST_1_SEL': 'SELECTION-SCREEN include (events + F4 idioms)',
    'Y_HRPAWF_EVENT_RULES_PA0000': 'SAP-contract FM (WF event rule)',
    'Y_HR_PAWF_FILL_REQUEST': 'bridge FM (WF -> Fiori dashboard via singleton class)',
    'YTHRWF_STEP_ACT': 'step-actor assignment table (DDIF_FIELDINFO_GET)',
}

def desc_of(obj_type, name):
    name = name.strip()
    if obj_type in ('CLAS', 'INTF'):
        return DESC['SEOCLASSTX'].get(name, '')
    if obj_type in ('TABL', 'VIEW'):
        return DESC['DD02T'].get(name, '')
    if obj_type == 'PROG':
        return DESC['TRDIRT'].get(name, '')
    if obj_type == 'FUGR':
        return DESC['TLIBT'].get(name, '')
    if obj_type == 'DTEL':
        return DESC['DD04T'].get(name, '')
    return ''

def deep_mark(name):
    name = name.strip()
    if name in PRIOR_DEEP:
        return 'YES (v1, S-63/S-72)'
    if name in NEW_DEEP:
        return f'YES (s081) — {NEW_DEEP[name]}'
    return ''

def md_row(*cells):
    return '| ' + ' | '.join(str(c).replace('|', '\\|') for c in cells) + ' |'

by_type = {}
for r in pkg:
    by_type.setdefault(r['OBJECT'].strip(), []).append(r['OBJ_NAME'].strip())
for v in by_type.values():
    v.sort()

L = []
L.append('# N_MENARD Object Inventory — Full D01 Scan')
L.append('')
L.append('**Scan date:** 2026-06-10 (session #081)')
L.append('**System:** HQ-SAP-D01, client 350 — READ-ONLY (RFC_READ_TABLE on TADIR/TFDIR + texts; ADT GET for deep reads)')
L.append('**Method:** `TADIR WHERE DEVCLASS = \'YHR_PA_WF\'` + `TADIR WHERE AUTHOR = \'N_MENARD\'` + `TFDIR PNAME = SAPL<fugr>`')
L.append('**Scripts:** `Zagentexecution/tasks/2026_06_10_nmenard_inventory/` (scan + this generator). Raw data: `nmenard_inventory.json`.')
L.append('')
L.append('---')
L.append('')
L.append('## Headline numbers')
L.append('')
L.append(f'- Package `YHR_PA_WF`: **{len(pkg)} TADIR objects** ({len(by_type)} object types).')
L.append(f'- N_MENARD authored **{len(ao)} objects** across **{len(set(r["DEVCLASS"] for r in ao))} packages** on D01.')
L.append('- The HR-WF framework is NOT contained in one package: `YCL_HR_WF_MAIL_FACTORY`, `YCL_WF_UTILITIES`,')
L.append('  `YTHRWF_NOTIF` live in **`YHR_OM_WF`**; `YCL_CA_UTILITIES` in **`YBC`**; `YCL_HRWF_MAIN_LX` and')
L.append('  `YCL_HRWF_OPERATION` in **`ZHR_DEV`**. Package `YHR_PA_WF` itself has 740 objects but only 135 are')
L.append('  TADIR-authored by N_MENARD (the rest were created by colleagues/generators inside his package).')
L.append('')
L.append('### Package composition (YHR_PA_WF)')
L.append('')
L.append('| Object type | Count | Meaning |')
L.append('|---|---|---|')
type_meaning = {
    'TABL': 'Tables + structures (DDIC)', 'DTEL': 'Data elements', 'TTYP': 'Table types',
    'CLAS': 'ABAP classes', 'TRAN': 'Transactions', 'FUGR': 'Function groups',
    'CUS0': 'IMG activities', 'CUS1': 'IMG transactions', 'TOBJ': 'View-maintenance objects',
    'VIEW': 'Maintenance views', 'PDTS': 'Workflow standard tasks', 'DOMA': 'Domains',
    'PROG': 'Programs/includes', 'INTF': 'Interfaces', 'PDWS': 'Workflow templates',
    'SICF': 'ICF services (WDA)', 'WDYA': 'Web Dynpro applications', 'WDYN': 'Web Dynpro components',
    'SFPF': 'Adobe forms', 'SMIM': 'MIME objects', 'SFPI': 'Adobe form interfaces',
    'NROB': 'Number range objects', 'SUSH': 'Auth switch', 'XSLT': 'XSLT transformations',
    'SOBJ': 'BOR object types', 'DEVC': 'Package itself', 'ICFA': 'ICF alias',
    'MSAG': 'Message class', 'PDAC': 'Workflow rule (AC)', 'SHI3': 'IMG structure',
    'SOTR': 'OTR texts', 'TYPE': 'Type group',
}
for t, names in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
    L.append(md_row(t, len(names), type_meaning.get(t, '')))
L.append('')
L.append('---')
L.append('')

# Classes
L.append('## 1. Classes (CLAS) — 41 in package')
L.append('')
L.append('| Class | Description | Deep-read | Pattern notes |')
L.append('|---|---|---|---|')
notes = {
    'YCL_HRWF_FACTORY': 'Factory/singleton (Pattern 1)',
    'YCL_HRWF_MAIN': 'Abstract base — main algorithm',
    'YCL_HRWF_ACTORS': 'Abstract base — actor determination',
    'YCX_HRWF': 'Domain exception class (Pattern 4)',
    'YCL_HRWF_REPORT_2_BL': 'Business-logic class behind report (report->class split)',
    'YCL_HR_PA_WF_ASSIST': 'Web Dynpro assistance class',
    'YCL_HR_INT_WF_ASSIST': 'Web Dynpro assistance class',
    'YCL_HR_PDF_ADM_DETAILS': 'PDF generation class',
    'YCL_TO_DEL': 'Dead object kept in package (anti-pattern: delete instead)',
}
for n in by_type.get('CLAS', []):
    note = notes.get(n, '')
    if not note and n.startswith('YCL_HR_WF_MAIL_GENERATOR'):
        note = 'Mail GENERATOR family — one per WF type (S1/I1/LX/PX)'
    elif not note and n.startswith('YCL_HR_WF_MAIL_PA'):
        note = 'Mail ACTION family — one class per notification event'
    elif not note and 'MAIL' in n:
        note = 'Mail family'
    L.append(md_row(f'`{n}`', desc_of('CLAS', n), deep_mark(n), note))
L.append('')
L.append('Out-of-package framework classes (sibling packages):')
L.append('')
L.append('| Class | Package | Description | Deep-read |')
L.append('|---|---|---|---|')
for n, p in [('YCL_HR_WF_MAIL_FACTORY', 'YHR_OM_WF'), ('YCL_HR_WF_MAIL_GENERATOR', 'YHR_OM_WF'),
             ('YCL_WF_UTILITIES', 'YHR_OM_WF'),
             ('YCL_CA_UTILITIES', 'YBC'), ('YCL_HRWF_MAIN_LX', 'ZHR_DEV'),
             ('YCL_HRWF_OPERATION', 'ZHR_DEV')]:
    L.append(md_row(f'`{n}`', p, desc_of('CLAS', n), deep_mark(n)))
L.append('')

# Interfaces
L.append('## 2. Interfaces (INTF) — 11')
L.append('')
L.append('| Interface | Description | Deep-read | Notes |')
L.append('|---|---|---|---|')
for n in by_type.get('INTF', []):
    note = 'Generated WDA component interface (ZIWCI* = SAP-generated, not a style reference)' if n.startswith('ZIWCI') else ''
    L.append(md_row(f'`{n}`', desc_of('INTF', n), deep_mark(n), note))
L.append('')

# Function groups
L.append('## 3. Function groups (FUGR) — 37 in package, with their FMs')
L.append('')
L.append('Most FUGRs here are **view-maintenance groups** (generated by SE54 for the YV*/YT* maintenance views —')
L.append('2 generated FMs each, TABLEPROC_/TABLEFRAME_). The hand-written ones are `YHRPAWF1` and `YHR_WF_EVENT`.')
L.append('')
L.append('| Function group | Description | FMs | FM names |')
L.append('|---|---|---|---|')
for n in by_type.get('FUGR', []):
    fmlist = [f['FUNCNAME'].strip() for f in fms.get(n, [])]
    L.append(md_row(f'`{n}`', desc_of('FUGR', n), len(fmlist),
                    ', '.join(f'`{x}`' for x in fmlist) if len(fmlist) <= 10 else f'{len(fmlist)} FMs'))
L.append('')
L.append('### YHRPAWF1 function modules (the hand-written WF group)')
L.append('')
L.append('| FM | Description | Deep-read |')
L.append('|---|---|---|')
for f in fms.get('YHRPAWF1', []):
    n = f['FUNCNAME'].strip()
    L.append(md_row(f'`{n}`', DESC['TFTIT'].get(n, ''), deep_mark(n)))
L.append('')

# Programs
L.append('## 4. Programs (PROG) — 16')
L.append('')
L.append('| Program | Description | Deep-read | Notes |')
L.append('|---|---|---|---|')
prog_notes = {
    'YHR_WF_PA_LIST_1': 'Main WF reporting program',
    'YHR_WF_PA_LIST_1_DATA': 'DATA include of YHR_WF_PA_LIST_1',
    'YHR_WF_PA_LIST_1_SEL': 'SELECTION-SCREEN include of YHR_WF_PA_LIST_1',
    'YRBUS1065': 'BOR program for YBUS1065',
    'YRBUS2065': 'BOR program for YBUS2065',
    'YIMGPAWF': 'IMG structure program',
    'YHR_TO_DEL': 'Dead object kept in package',
}
for n in by_type.get('PROG', []):
    L.append(md_row(f'`{n}`', desc_of('PROG', n), deep_mark(n), prog_notes.get(n, '')))
L.append('')

# BOR + workflow
L.append('## 5. BOR objects (SOBJ) + Workflow templates/tasks')
L.append('')
L.append('| Object | Type | Notes |')
L.append('|---|---|---|')
for n in by_type.get('SOBJ', []):
    L.append(md_row(f'`{n}`', 'SOBJ (BOR object type)',
                    'Deep-read v1 (YBUS1065 = EmployeeUnesco)' if n == 'YBUS1065' else ''))
L.append(md_row(f"{len(by_type.get('PDWS', []))} workflow templates", 'PDWS',
                ', '.join(by_type.get('PDWS', []))))
L.append(md_row(f"{len(by_type.get('PDTS', []))} standard tasks", 'PDTS',
                ', '.join(by_type.get('PDTS', []))))
L.append('')

# Tables
L.append('## 6. DDIC — Tables and structures (TABL) — 193')
L.append('')
L.append('Naming families (the structure prefix IS the convention):')
L.append('')
L.append('- `YTHRWF_*` — WF engine catalog tables (type/step/actor) — the core covered in style guide §12')
L.append('- `YTHRPAWF_*` — PA-WF specific config + temp-save tables')
L.append('- `YTHRINT*` — Internship WF tables')
L.append('- `YSHRWF_*` / `YSHR_*` — structures (`YS` prefix = structure, not table)')
L.append('- `YSHR_DD_*` — Web Dynpro dropdown structures (one per dropdown)')
L.append('- `YSHR_WD_*` — Web Dynpro context node structures (one per infotype/view)')
L.append('- `ZSHR_JSON_*` — SuccessFactors JSON interface structures')
L.append('')
L.append('| Table/structure | Description | Deep-read |')
L.append('|---|---|---|')
for n in by_type.get('TABL', []):
    L.append(md_row(f'`{n}`', desc_of('TABL', n), deep_mark(n)))
L.append('')

# Views
L.append('## 7. DDIC — Maintenance views (VIEW) — 21')
L.append('')
L.append('| View | Description |')
L.append('|---|---|')
for n in by_type.get('VIEW', []):
    L.append(md_row(f'`{n}`', desc_of('VIEW', n)))
L.append('')

# DTEL/DOMA/TTYP summary
L.append('## 8. DDIC — Data elements / Domains / Table types')
L.append('')
L.append(f"- **{len(by_type.get('DTEL', []))} data elements** (`YE_*` pattern dominates)")
L.append(f"- **{len(by_type.get('DOMA', []))} domains**")
L.append(f"- **{len(by_type.get('TTYP', []))} table types** (`YT*`/`YTT*` pattern)")
L.append('')
L.append('<details><summary>Full DTEL list</summary>')
L.append('')
L.append('| Data element | Description |')
L.append('|---|---|')
for n in by_type.get('DTEL', []):
    L.append(md_row(f'`{n}`', desc_of('DTEL', n)))
L.append('')
L.append('</details>')
L.append('')
L.append('<details><summary>Full DOMA / TTYP lists</summary>')
L.append('')
L.append('Domains: ' + ', '.join(f'`{n}`' for n in by_type.get('DOMA', [])))
L.append('')
L.append('Table types: ' + ', '.join(f'`{n}`' for n in by_type.get('TTYP', [])))
L.append('')
L.append('</details>')
L.append('')

# UI layer
L.append('## 9. UI + integration layer')
L.append('')
L.append('| Type | Objects |')
L.append('|---|---|')
for t in ('WDYN', 'WDYA', 'SICF', 'SFPF', 'SFPI', 'TRAN', 'XSLT', 'NROB', 'MSAG'):
    L.append(md_row(t + f' ({type_meaning.get(t,"")})', ', '.join(f'`{n}`' for n in by_type.get(t, []))))
L.append('')

# Sibling packages
L.append('## 10. N_MENARD beyond YHR_PA_WF — sibling packages')
L.append('')
L.append(f'`TADIR WHERE AUTHOR = N_MENARD` returns {len(ao)} objects. Distribution:')
L.append('')
L.append('| Package | Objects | Role |')
L.append('|---|---|---|')
pkg_roles = {
    'ZHR_DEV': 'Older HR dev package — holds YCL_HRWF_MAIN_LX + YCL_HRWF_OPERATION',
    '$TMP': 'Local objects (not transported)',
    'YA': 'Cross-application Y objects',
    'YBC': 'Basis/cross-app tools — holds YCL_CA_UTILITIES, Excel/BTCI/mail-auth tools',
    'ZHRDEV': 'Older HR dev package',
    'YHR_OM_WF': 'OM workflow framework (sibling of PA WF) — holds YCL_HR_WF_MAIL_FACTORY, YCL_WF_UTILITIES, YTHRWF_NOTIF',
    'YHR_PA_WF': 'THIS package (PA workflow framework)',
    'YB': 'Y basis objects', 'YP': 'HR/payroll objects', 'YE': '—', 'YL': '—', 'YV': '—',
    'YU': '—', 'YT': '—', 'ZTECH': 'Technical sandbox', 'ZHR_EVE': 'HR events',
    'YHR_CORE_MANAGER': 'Core Manager interface', 'ZHRBENEFITS_FIORI': 'Benefits Fiori',
    '/SDF/FDQ_API': 'SAP support tool (not his design)',
}
for p, n in Counter(r['DEVCLASS'] for r in ao).most_common():
    L.append(md_row(f'`{p}`', n, pkg_roles.get(p, '')))
L.append('')

# Deep-read log
L.append('---')
L.append('')
L.append('## 11. Deep-read log')
L.append('')
L.append('**Prior (style guide v1, CRP S-63/S-72): 18 reference files** — see README.md of the style guide.')
L.append('Note: the file named `YTHRWF_EVAL_PATH` in the v1 reference set has **no TADIR object of that name on D01**')
L.append('(closest: eval-path logic lives in `YCL_WF_UTILITIES=>GET_OBJECTS_WITH_EVAL_PATH`). Flagged as naming drift.')
L.append('')
L.append('**This session (s081) — new deep-reads via ADT GET (read-only):**')
L.append('')
L.append('| Object | Type | Why chosen |')
L.append('|---|---|---|')
for n, why in NEW_DEEP.items():
    L.append(md_row(f'`{n}`', '', why))
L.append('')
L.append('**Golden locations** (code and objects are data too):')
L.append('')
L.append('- Sources (canonical, brain-ingested): `extracted_code/HCM/YHR_PA_WF/` — 8 .abap + table-structure JSON.')
L.append('- Object catalog (Gold DB, D01 provenance): `d01_tadir_yhr_pa_wf` (740), `d01_tadir_nmenard` (3,463),')
L.append('  `d01_tfdir_nmenard_fugr` (297 FMs) in `p01_gold_master_data.db`.')
L.append('- Raw session artifact: `Zagentexecution/tasks/2026_06_10_nmenard_inventory/` (scan JSON + readback).')
L.append('')
L.append('## 12. Style-guide impact')
L.append('')
L.append('See `UNESCO-ABAP-STYLE-GUIDE.md` — "Extended patterns (from full D01 scan)" subsections appended in s081.')
L.append('')

OUT.write_text('\n'.join(L), encoding='utf-8')
print(f'Wrote {OUT} ({len(L)} lines)')
