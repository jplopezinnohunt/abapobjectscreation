"""
patch_table_desc_sidebar.py
1. Adds table description lookup to CFGDETAIL
2. Adds collapsible sidebar to the dashboard
3. Adds Description column to config drilldown rows
"""
import json, re, os

# ── Table description dictionary ─────────────────────────────────────────────
TABLE_DESC = {
    # HCM Payroll / Personnel
    'T5ASRFSCNFLDPRP':'HR: Country-Spec Report Field Properties',
    'T5ASRFSCNFLDT':  'HR: Country-Spec Report Field Texts',
    'T5ASRFSCNMDATA_T':'HR: Report Metadata Texts',
    'T5ASRFSCNSTGFAT': 'HR: Report Stage Field Assignment Texts',
    'T5ASRFSCNPRP':   'HR: Country-Spec Report Properties',
    'T5ASRFSCNVERPRP':'HR: Country-Spec Report Version Properties',
    'T500L':   'HR: Countries for HR',
    'T500P':   'HR: Personnel Areas',
    'T501':    'HR: Employee Groups',
    'T503':    'HR: Employee Subgroups',
    'T508A':   'HR: Work Schedule Rules',
    'T510':    'HR: Pay Scales',
    'T510C':   'HR: Pay Scale Groups',
    'T510S':   'HR: Pay Scale Levels',
    'T510N':   'HR: Basic Pay — Wage Type Defaults',
    'T511':    'HR: Wage Types',
    'T511K':   'HR: Wage Type Valuation',
    'T512':    'HR: Wage Type Characteristics',
    'T512T':   'HR: Wage Type Texts',
    'T512W':   'HR: Wage Types for Payroll',
    'T514':    'HR: Evaluation Bases',
    'T52BA':   'HR: Payroll Schema Definition',
    'T52BF':   'HR: Function Codes of Payroll Schema',
    'T52C0':   'HR: Constants for Payroll',
    'T52D5':   'HR: Payroll Driver Schemas',
    'T549':    'HR: Payroll Accounting Areas',
    'T549A':   'HR: Assignment Areas',
    'T596I':   'HR: Cumulation Wage Types in Schema',
    'T700':    'HR: Profile Types',
    'T7UNPAD_DSDA': 'HR UNESCO: Payroll Driver Assignment',
    'T7UNPAD_DSPA': 'HR UNESCO: Payroll Schema Assignment',
    'T77':     'HR: PD Profile (OM)',
    'PA0008':  'HR: Basic Pay Infotype',
    'MOLGA':   'HR: Country Groupings',
    'T001P':   'HR: Personnel Area/Subarea',
    # Specific HCM views
    'V_T510':        'View: Pay Scale Groups',
    'V_T510_C':      'View: Pay Scale Levels',
    'V_T7UNPAD_DSDA':'View: UNESCO Payroll Driver',
    'V_T7UNPAD_DSPA':'View: UNESCO Payroll Schema',
    # Security / Auth
    'AGR_TIMEB':  'Auth: Role Time-Based Assignments',
    'AGR_USERS':  'Auth: User-Role Assignments',
    'AGR_DEFINE': 'Auth: Role Definitions',
    'AGR_AGRS':   'Auth: Composite Roles (child roles)',
    'AGR_TEXTS':  'Auth: Role Description Texts',
    'AGR_1016':   'Auth: Auth Objects in Roles',
    'AGR_1251':   'Auth: Auth Profiles in Roles',
    'USR10':   'Auth: Authorization Profiles for Users',
    'USR11':   'Auth: Authorization Profile Texts',
    'USR12':   'Auth: Authorization Values',
    'UST10S':  'Auth: Single Profiles (User)',
    'UST12':   'Auth: Authorization Values in Profiles',
    'SPERS_OBJ':'Basis: User Personalization Objects',
    'TVDIR':   'Auth: Transaction-to-Auth-Object Map',
    'TDDAT':   'Auth: Table Authorization Groups',
    'PRGN_STAT':'Auth: Role Cache Index',
    # MDG
    'USMD2001':'MDG: Personalization — Default Data Model',
    'USMD2003':'MDG: Personalization — Default UI Model',
    # FI / Finance
    'T001':    'FI: Company Codes',
    'T001B':   'FI: Permitted Posting Periods',
    'T003':    'FI: Document Types',
    'T012':    'FI: House Banks',
    'GB01C':   'FI: Accounting Principle',
    'GB02C':   'FI: Accounting Principle Mapping',
    'TFOR':    'FI: Currency Translation Methods',
    'KE34':    'CO-PA: Profitability Analysis Segment',
    'GRW_SET': 'CO: Report Writer Set',
    'FINB_TR_DERIVATION':'FI: Ledger Derivation Rules',
    'SFOBUFORMULA':'FI: Payment Form Formula',
    'SWOTICE': 'FI: Payment Notice Types',
    # Procurement / MM
    'T16FK':   'MM: Purchasing Order Types',
    'T16FV':   'MM: Purchasing Item Categories',
    'T024':    'MM: Purchasing Groups',
    # Basis / BC
    'TVARVC':  'BC: Table/Variable Values for Reports',
    'TNAPR':   'BC: Output: Process Configuration',
    'T9POST':  'BC: FI Posting from Payroll',
    'NRIV':    'BC: Number Range Intervals',
    'TOBJ':    'BC: Authorizable Objects',
    'TNODEIMG':'BC: IMG Node Authorization',
    'TNODEIMGR':'BC: IMG Node Auth (Req)',
    'TNODEIMGT':'BC: IMG Node Auth (Texts)',
    # Workflow
    'YTHRWF_NOTIF':'Custom WF: Notification Config',
    # CO
    'TCALS':   'CO: Calendar Assignments',
    'TFACD':   'FI: Asset Class Depreciation',
    'TFACS':   'FI: Asset Classes',
    'TFACT':   'FI: Asset Class Texts',
    'TFAIN':   'FI: Asset Class Internal Orders',
    'TFAIT':   'FI: Asset Class Texts (Internal)',
}

# Load and enrich config detail
with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

for name, v in cfg.items():
    v['desc'] = TABLE_DESC.get(name, '')
    # Also try partial match for V_ prefix views
    if not v['desc'] and name.startswith('V_'):
        base = name[2:]
        v['desc'] = 'View: ' + TABLE_DESC.get(base, base)
        if v['desc'] == 'View: ' + base:
            v['desc'] = ''

with open('cts_config_detail.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

covered = sum(1 for v in cfg.values() if v.get('desc'))
print(f'Table descriptions: {covered} of {len(cfg)} objects have description')

# ── Now patch the dashboard HTML ──────────────────────────────────────────────
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# 1. Re-inject CFGDETAIL with descriptions
NEW_CFG_JS = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
start = html.find('const CFGDETAIL=')
end   = html.find(';\n', start) + 2
html  = html[:start] + NEW_CFG_JS + html[end:]
print('Re-injected CFGDETAIL')

# 2. Add Description to row template
OLD_NAME_CELL = """<td style="padding-left:16px"><code style="color:${g.color}">${c.name}</code></td>"""
NEW_NAME_CELL = """<td style="padding-left:16px">
          <code style="color:${g.color}">${c.name}</code>
          ${c.desc ? `<div style="font-size:.62rem;color:var(--mu2);margin-top:2px">${c.desc}</div>` : ''}
        </td>"""
if OLD_NAME_CELL in html:
    html = html.replace(OLD_NAME_CELL, NEW_NAME_CELL, 1)
    print('Added description sub-line under table name')

# 3. Add Description column header
OLD_TH = '<th>Table / View</th><th>Type</th><th>Module (inferred)</th>'
NEW_TH = '<th style="min-width:160px">Table / View</th><th>Type</th><th>Module</th>'
if OLD_TH in html:
    html = html.replace(OLD_TH, NEW_TH, 1)
    print('Updated column header')

# 4. Collapsible sidebar — add toggle button to topbar and wire CSS
OLD_TOPBAR_END = '</div>\n<div class="shell">'
NEW_TOPBAR_End = '''<button onclick="toggleSidebar()" id="sb-toggle"
  style="background:rgba(79,142,247,.12);border:1px solid rgba(79,142,247,.25);
         color:var(--acc);border-radius:6px;padding:4px 10px;cursor:pointer;
         font-size:.78rem;display:flex;align-items:center;gap:5px;margin-left:8px">
  <span id="sb-ico">◀</span> <span id="sb-lbl">Hide</span>
</button>
</div>
<div class="shell">'''

if OLD_TOPBAR_END in html:
    html = html.replace(OLD_TOPBAR_END, NEW_TOPBAR_End, 1)
    print('Added sidebar toggle button to topbar')

# 5. Add toggleSidebar JS function
SB_TOGGLE_JS = """
// ── Sidebar collapse ──────────────────────────────────────────────────────────
function toggleSidebar() {
  const sb  = document.querySelector('.sidebar');
  const ico = document.getElementById('sb-ico');
  const lbl = document.getElementById('sb-lbl');
  const open = sb.style.display !== 'none';
  sb.style.display = open ? 'none' : '';
  ico.textContent  = open ? '▶' : '◀';
  lbl.textContent  = open ? 'Menu' : 'Hide';
}

"""
# Insert right after the go() nav function
INSERT_AFTER = 'function go(id,btn){'
idx = html.find(INSERT_AFTER)
closing = html.find('\n}', idx) + 2
html = html[:closing] + '\n' + SB_TOGGLE_JS + html[closing:]
print('Added toggleSidebar() JS')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\nDone! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
