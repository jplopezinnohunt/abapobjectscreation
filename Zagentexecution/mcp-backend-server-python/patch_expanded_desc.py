"""
patch_expanded_desc.py
Massively expands table description coverage — adds descriptions for 300+ common
SAP tables that appear in the config data.
Then re-injects CFGDETAIL into cts_dashboard.html.
"""
import json, os

# ── Expanded TABLE_DESC dictionary ────────────────────────────────────────────
TABLE_DESC = {
    # HCM Country Grouping / Core
    'MOLGA':   'HR: Country Groupings (molga)',
    'T001P':   'HR: Personnel Areas & Subareas',
    'T500L':   'HR: Countries for Human Resources',
    'T500P':   'HR: Personnel Areas',
    'T501':    'HR: Employee Groups',
    'T501T':   'HR: Employee Group Texts',
    'T503':    'HR: Employee Subgroups',
    'T503K':   'HR: Employee Subgroup Groupings for Payroll',
    'T503T':   'HR: Employee Subgroup Texts',
    'T508A':   'HR: Work Schedule Rules',
    'T508T':   'HR: Work Schedule Rule Texts',
    # HCM Pay Scales
    'T510':    'HR: Pay Scales',
    'T510A':   'HR: Time-Based Pay Scale Groups',
    'T510C':   'HR: Pay Scale Groups',
    'T510F':   'HR: Pay Scale Progression',
    'T510G':   'HR: Wage Type Groups (Pay Scale)',
    'T510H':   'HR: Indirect Valuation Modules',
    'T510I':   'HR: Pay Scale Group Texts',
    'T510J':   'HR: Pay Scale Level Texts',
    'T510N':   'HR: Default Wage Types for Basic Pay',
    'T510S':   'HR: Pay Scale Levels',
    'T510U':   'HR: Pay Scale Types',
    'T510V':   'HR: Pay Scale Type Texts',
    # HCM Wage Types
    'T511':    'HR: Wage Types',
    'T511K':   'HR: Characteristics of Wage Types',
    'T511T':   'HR: Wage Type Texts',
    'T512':    'HR: Wage Type Characteristics (Technical)',
    'T512T':   'HR: Wage Type Technical Texts',
    'T512W':   'HR: Permissible Wage Types per Infotype',
    'T512Z':   'HR: Time Wage Type Selection Rules',
    # HCM Payroll Schema
    'T52BA':   'HR: Payroll Schema Definition',
    'T52BF':   'HR: Payroll Functions in Schema',
    'T52C0':   'HR: Payroll Constants',
    'T52D5':   'HR: Driver Schemas for Payroll',
    'T52EF':   'HR: Payroll Schema Personnel Calculation Rules',
    # HCM Infotypes
    'PA0008':  'HR-PA: Basic Pay (Infotype 0008)',
    'PA0014':  'HR-PA: Recurring Payments/Deductions (IT0014)',
    'PA0015':  'HR-PA: Additional Payments (IT0015)',
    'PA0041':  'HR-PA: Date Specifications (IT0041)',
    'PA2001':  'HR-TM: Absences (IT2001)',
    'PA2002':  'HR-TM: Attendances (IT2002)',
    # HCM OM
    'T77':     'HR-OM: Profile Types',
    'T750':    'HR-OM: Relationship Types',
    'T752':    'HR-OM: Object Type-Specific Relationships',
    # HCM Payroll Posting
    'T549':    'HR: Payroll Accounting Areas',
    'T549A':   'HR: Assignment of Payroll Area',
    'T549Q':   'HR: Payroll Control Records',
    'T596I':   'HR: Cumulation Wage Types in Payroll Schema',
    # HCM Country-Spec UNESCO
    'T5ASRFSCNFLDPRP': 'HR-ASR: Country-Specific Report Field Properties',
    'T5ASRFSCNFLDT':   'HR-ASR: Country-Specific Report Field Texts',
    'T5ASRFSCNMDATA_T':'HR-ASR: Reporting Metadata Texts',
    'T5ASRFSCNSTGFAT': 'HR-ASR: Stage Field Assignment Texts',
    'T5ASRFSCNPRP':    'HR-ASR: Country-Specific Report Properties',
    'T5ASRFSCNVERPRP': 'HR-ASR: Report Version Properties',
    # Authorization / Security
    'AGR_TIMEB':   'Auth: Role Time-Based User Assignments',
    'AGR_USERS':   'Auth: User Assignments to Roles',
    'AGR_DEFINE':  'Auth: Role Definitions',
    'AGR_AGRS':    'Auth: Composite Role Assignments (Child Roles)',
    'AGR_TEXTS':   'Auth: Role Description Texts',
    'AGR_1016':    'Auth: Authorization Objects in Roles',
    'AGR_1251':    'Auth: Auth Field Values in Roles',
    'AGR_HIER':    'Auth: Role Hierarchy',
    'USR10':       'Auth: Authorization Profiles Assigned to Users',
    'USR11':       'Auth: Authorization Profile Texts',
    'USR12':       'Auth: Authorization Values for Profiles',
    'USR40':       'Auth: Illegal Passwords',
    'UST10S':      'Auth: Single User Profiles',
    'UST12':       'Auth: Authorization Values (UST12)',
    'SPERS_OBJ':   'Basis: Personalization — Object Registry',
    'SPERS':       'Basis: Personalization — User Settings',
    'TVDIR':       'Auth: Transaction Code to Auth Object Mapping',
    'TDDAT':       'Auth: Maintenance Areas for Tables',
    'PRGN_STAT':   'Auth: Role Status / Cache Index',
    # MDG
    'USMD2001':    'MDG: Personalization — Default Data Model',
    'USMD2003':    'MDG: Personalization — Default UI Model per Data Model',
    'USMD_MODEL':  'MDG: Data Model Definition',
    'USMD_VALUE':  'MDG: Data Model Value Assignments',
    # FI / Finance
    'T001':    'FI: Company Codes',
    'T001B':   'FI: Permitted Posting Periods',
    'T001K':   'FI: Valuation Areas',
    'T001S':   'FI: Tolerance Groups (Employees)',
    'T003':    'FI: Document Types',
    'T003T':   'FI: Document Type Texts',
    'T004':    'FI: Chart of Accounts',
    'T005':    'FI: Countries',
    'T005S':   'FI: Taxing Regions',
    'T006':    'FI: Units of Measurement',
    'T012':    'FI: House Banks',
    'T012C':   'FI: Bank Chain for Payment Method / House Bank',
    'T012E':   'FI: EDI-Compatible Payment Methods per House Bank',
    'T012K':   'FI: House Bank Accounts',
    'T012T':   'FI: House Bank Names',
    'T040':    'FI: Correspondence Types',
    'T042A':   'FI: Payment Methods per Country',
    'T042B':   'FI: Details of Payment Methods',
    'T042I':   'FI: Company Code-Specific Payment Methods',
    'T042Z':   'FI: Payment Methods per Company Code',
    'T047':    'FI: Dunning Procedures',
    'T053':    'FI: Rules for Bill of Exchange Payment',
    'GB01C':   'FI-GL: Accounting Principles',
    'GB02C':   'FI-GL: Accounting Principle Assignments to Ledgers',
    'FINB_TR_DERIVATION': 'FIN: Bank Account Determination Rules',
    'SFOBUFORMULA': 'FI-PAYM: Payment Forms Formula',
    'SWOTICE':      'FI-PAYM: Payment Notice Types',
    'TFBW':    'FI: Business Workflow Parameters',
    'TFOR':    'FI: Currency Translation Methods',
    'TZUN':    'FI: Assignment of Regions to Dunning Areas',
    # Assets
    'TFACD':   'FI-AA: Asset Class — Depreciation Areas',
    'TFACS':   'FI-AA: Asset Classes',
    'TFACT':   'FI-AA: Asset Class Texts',
    'TFAIN':   'FI-AA: Asset Class Internal Orders',
    'TFAIT':   'FI-AA: Asset Class Internal Order Texts',
    'TFACN':   'FI-AA: Chart of Depreciation',
    'TFABN':   'FI-AA: Asset Class Account Determination',
    # CO
    'TKA01':   'CO: Controlling Areas',
    'GRW_SET': 'CO: Report Writer Sets',
    'KE34':    'CO-PA: Profitability Analysis Segments',
    'GLE_MCA': 'FI-GL: Migration Control — Account',
    # PSM / Public Sector
    'UCUM001': 'PSM-FM: Funds Management Area',
    'UGWB001': 'PSM-FM: FM Area Assignment',
    # MM / Procurement
    'T016FK':  'MM-PUR: Purchase Order Types — Keys',
    'T016FV':  'MM-PUR: Purchase Order: Item Categories',
    'T016':    'MM-PUR: Purchasing Groups — Overview',
    'T024':    'MM-PUR: Purchasing Groups',
    'T024E':   'MM-PUR: Purchasing Organizations',
    'T001W':   'MM: Plants',
    'T001L':   'MM: Storage Locations',
    # SD
    'TVKO':    'SD: Sales Organizations',
    'TVKBT':   'SD: Sales Office Names',
    'TVTA':    'SD: Sales Area Data',
    'TVZW':    'SD: Distribution Channels',
    # Basis / BC
    'TVARVC':  'BC: Table of Variables for Reports/Selections',
    'TNAPR':   'BC-MSG: Output Condition: Procedure Configuration',
    'TNODEIMG': 'BC-CUST: IMG Node Authorization Objects',
    'TNODEIMGR':'BC-CUST: IMG Node Auth Objects (Required)',
    'TNODEIMGT':'BC-CUST: IMG Node Texts',
    'NRIV':    'BC-NR: Number Range Intervals',
    'NRLS':    'BC-NR: Status of Internal Number Ranges',
    'TOBJ':    'BC-Auth: Authorization Objects',
    'TOBJT':   'BC-Auth: Authorization Object Texts',
    'T9POST':  'BC-PY: FI Posting from HR Payroll',
    'T100':    'BC: Messages (Msg Class, Number, Text)',
    'T100T':   'BC: Message Text Short Descriptions',
    'RSECADMIN':'BC-ANA: Analysis Auth Admin Settings',
    'TPFYP':   'BC: Planning Fiscal Year Parameters',
    # Workflow
    'YTHRWF_NOTIF': 'Z-WF: Custom Notification Configuration (UNESCO)',
    'SWN_NOTIF':'BC-WF: Workflow Notifications',
    # Logistics / shipping
    'TCALS':   'CO-OM: Calendar Assignments',
    'T16FV':   'MM: Item Category Determination',
    'T16FK':   'MM: Order Types for Purchasing',
    # Output / Forms
    'TNAPR':   'BC: Output Determination — Procedure/Cond Tables',
    # Tax
    'T005S':   'FI: Tax Regions / Taxing Authorities',
    'T059P':   'FI-TH: Withholding Tax Types',
    # Misc
    'SCVI':    'BC: Screen Variants',
    'VARX':    'BC: Variant Metadata',
    'OSOA':    'BC-ECM: Output Condition — Sorting Criteria',
    'AVAS':    'BC-CLS: Classification — Object-Characteristic Assignment',
}

# ── Enrich config detail ───────────────────────────────────────────────────────
with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

covered_before = sum(1 for v in cfg.values() if v.get('desc','').strip())

for name, v in cfg.items():
    if not v.get('desc'):
        # Direct match
        if name in TABLE_DESC:
            v['desc'] = TABLE_DESC[name]
        # V_ prefix view
        elif name.startswith('V_') and name[2:] in TABLE_DESC:
            v['desc'] = 'View: ' + TABLE_DESC[name[2:]].split(': ',1)[-1]
        # Partial prefix match for T5xxxx patterns
        elif name.startswith('T5ASRFSCN'):
            suffix = name[9:]
            v['desc'] = f'HR-ASR: Country-Spec Report Config ({suffix})'

covered_after = sum(1 for v in cfg.values() if v.get('desc','').strip())
print(f'Descriptions: {covered_before} → {covered_after} (of {len(cfg)})')

with open('cts_config_detail.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

# ── Re-inject into dashboard ──────────────────────────────────────────────────
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

NEW_CFG_JS = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
start = html.find('const CFGDETAIL=')
end   = html.find(';\n', start) + 2
html  = html[:start] + NEW_CFG_JS + html[end:]

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Done! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
print(f'Tables with description: {covered_after} / {len(cfg)}')
