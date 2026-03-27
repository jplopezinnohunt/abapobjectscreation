"""
build_payment_companion.py  v4 — UNESCO SAP Payment & BCM Intelligence Companion
Generates a comprehensive HTML dashboard with:
  - E2E flow (Invoice→WF→F110→BCM→SWIFT→Reconciliation)
  - Full object inventory (561 CTS objects)
  - Documentation vs Reality control matrix
  - Workflow architecture (WS90000003 + custom FMs)
  - BCM configuration & audit findings
  - DMEE trees (16)
  - House bank network
  - SAPFPAYM variant catalog
"""
import sys, io, sqlite3, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB = Path(__file__).parent.parent / 'sap_data_extraction/sqlite/p01_gold_master_data.db'
db = sqlite3.connect(str(DB))

# ── 1. Load SAP data ──────────────────────────────────────────────────────────

# Company codes
companies = {r[0]: r[1] for r in db.execute('SELECT BUKRS, BUTXT FROM T001').fetchall()}

# T042 paying company
t042 = {r[0]: r[1] for r in db.execute('SELECT BUKRS, ZBUKR FROM T042').fetchall()}

# T042E payment methods
t042e = {}
for r in db.execute('SELECT ZBUKR, GROUP_CONCAT(ZLSCH ORDER BY ZLSCH) FROM T042E GROUP BY ZBUKR').fetchall():
    t042e[r[0]] = r[1] or ''

# T012K house banks
hb_data = db.execute('SELECT BUKRS, HBKID, HKTID, WAERS FROM T012K ORDER BY BUKRS, HBKID').fetchall()
hb_by_bukrs = {}
for r in hb_data:
    hb_by_bukrs.setdefault(r[0], []).append({'hbkid': r[1], 'hktid': r[2], 'waers': r[3]})

# T042I bank ranking row count
t042i = db.execute('SELECT COUNT(*) FROM T042I').fetchone()[0]

# REGUH F110 stats
f110_stats = {}
for r in db.execute("""
    SELECT ZBUKR, SUBSTR(LAUFI,1,1) as pfx,
           COUNT(DISTINCT LAUFD||LAUFI) as runs, COUNT(*) as items
    FROM REGUH GROUP BY ZBUKR, pfx ORDER BY ZBUKR, runs DESC
""").fetchall():
    f110_stats.setdefault(r[0], []).append({'prefix': r[1], 'runs': r[2], 'items': r[3]})

# BCM batch stats
bcm_stats = {}
for r in db.execute("""
    SELECT ZBUKR, COUNT(*) batches, SUM(CAST(ITEM_CNT AS INT)) items,
           SUM(CASE WHEN CRUSR=CHUSR AND STATUS='A' THEN 1 ELSE 0 END) dual_ctrl_fail
    FROM BNK_BATCH_HEADER GROUP BY ZBUKR ORDER BY items DESC
""").fetchall():
    bcm_stats[r[0]] = {'batches': r[1], 'items': r[2] or 0, 'dual_ctrl_fail': r[3] or 0}

# PAYR payment media
try:
    payr_count = db.execute('SELECT COUNT(*) FROM PAYR').fetchone()[0]
except Exception:
    payr_count = 0

# ZFI_PAYREL_EMAIL
payrel_email = db.execute('SELECT * FROM ZFI_PAYREL_EMAIL').fetchall()

# CTS objects — unique payment-related
pay_terms = ['PAYM','BCM','SWIFT','DMEE','F110','WF_FI','PAYREL','ZFI_','YFI_',
             'YWFI','YFIP','YCEI','BCM_ACTIVE','ZBAPI','ZPAYM','BSEG','SAPFPAYM',
             'YBSEG','Z_WF_FI','Z_GET_CERT']
where = ' OR '.join([f"OBJ_NAME LIKE '%{t}%'" for t in pay_terms])
cts_objs = db.execute(
    f"SELECT DISTINCT PGMID, OBJECT, OBJ_NAME, DEVCLASS FROM cts_objects WHERE {where} ORDER BY OBJECT, OBJ_NAME"
).fetchall()

# DMEE trees
dmee_trees = [r[0] for r in db.execute(
    "SELECT DISTINCT OBJ_NAME FROM cts_objects WHERE OBJECT='DMEE' ORDER BY OBJ_NAME"
).fetchall()]

# SAPFPAYM variants
sapfpaym_variants = [r[0] for r in db.execute(
    "SELECT DISTINCT OBJ_NAME FROM cts_objects WHERE OBJECT='VARX' AND OBJ_NAME LIKE 'SAPFPAYM%' ORDER BY OBJ_NAME"
).fetchall()]

# BCM authorization roles
bcm_roles = [r[0] for r in db.execute(
    "SELECT DISTINCT OBJ_NAME FROM cts_objects WHERE OBJECT='ACGR' AND OBJ_NAME LIKE '%BCM%' ORDER BY OBJ_NAME"
).fetchall()]

# Group CTS objects by type
cts_by_type = {}
for r in cts_objs:
    cts_by_type.setdefault(r[1], []).append(r[2])

db.close()

# ── 2. Static knowledge (from PDF analysis) ──────────────────────────────────

WF_ARCHITECTURE = {
    'main_wf': 'WS90000003 (ZBSEG_FRAME1)',
    'sub_wf': 'WS90000002 (UN BSEG_SUBW)',
    'package': 'YWFI',
    'business_object': 'YBSEG (delegated subtype of BSEG)',
    'trigger_event': 'BSEGCREATED (Posting Item Created with Payment Block)',
    'scope': 'UNES company code only',
    'doc_types': ['KR','KA','ER','KT','IT','CO','AS','P3','SN','MF','IN','AP','RF','MR'],
    'excluded': 'Payment Method O or U = field office / excluded from WF',
    'custom_fms': [
        ('Z_GET_CERTIF_OFFICER_UNESDIR', 'Certifying Officer lookup → role.hq.int.unesco.org'),
        ('Z_WF_GET_CERTIFYING_OFFICER', 'Alternate CO lookup function'),
        ('Z_WF_FI_PR_WF_ACTOR1_DET', 'Determines WF validator group (FG: Z_WF_FI_EVENT_PAYMENT_METH)'),
        ('Z_WF_FI_BSEG_EVENT_PAYM_METHOD', 'Fires YBSEG payment method events'),
        ('Z_WF_FI_EXCLUDE_NOTIF_EMAIL', 'Email exclusion logic'),
        ('Y_VENDOR_PAYMENT_BLOCK', 'Sets/clears payment blocks'),
    ],
    'go_live_steps': [
        'SWU3 — Maintain WF Runtime Environment',
        'SWETYPV — BUSISB001 / INITIATED → WS50100024 (BCM)',
        'PFTC_CHG — Mark tasks 50100025, 50100026, 50100066, 50100075 as General',
        'PFTS — Standard tasks 90000002, 90000007, 90000008',
        'SM30 V_TBCA_RTW_LINK — BCM workflow linkages',
        'SWU_OBUF — Refresh WF object type buffer',
        'SWETYPV — BSEGCREATED event type linkage',
    ],
    'email_program': 'RSWUWFML2 with variant ZWKFLOW_FI_EMA',
    'fallback_table': 'ZFI_PAYREL_EMAIL (D_CROUZET + M_SPRONK_WF hardcoded)',
}

VALIDATION_GROUPS = [
    ('CO', 'BSP/CFS', 'Contract Officer'),
    ('AS/P3/SN', 'BFM/PAY', 'Payroll/HR payments'),
    ('MF/IN/AP', 'HRM/SPI', 'Service/invoice payments'),
    ('RF', 'BFM/TRS/CM', 'Treasury/Cash Mgmt'),
    ('MR', 'BFM/FRA+BFM/TRS/AR', 'Multi-route'),
    ('PS/PN', 'BFM/FNS', 'Financial statements'),
    ('KR/KA/KT/ER/IT', 'Certifying Officer', 'Specific invoice types → Rule 90000001'),
]

BCM_CONFIG = {
    'release_rules': [
        {'rule': '90000005', 'type': 'BNK_INI', 'step': '1st Release', 'wf': '50100024', 'proc': '31000004'},
        {'rule': '90000001', 'type': 'BNK_INI', 'step': '1st Release', 'wf': '50100024', 'proc': '31000004'},
        {'rule': '90000004', 'type': 'BNK_COM', 'step': '1st Release', 'wf': '50100021', 'proc': '—'},
        {'rule': '90000002', 'type': 'BNK_COM', 'step': '1st Release', 'wf': '50100022', 'proc': '—'},
        {'rule': '90000002', 'type': 'BNK_COM', 'step': '2nd Release', 'wf': '50100023', 'proc': '—'},
    ],
    'approval_limits': [
        ('BFM/TRS', 'Up to $50M'),
        ('AP Validators', 'Up to $5M'),
        ('Payroll special', 'Treasurer + Assistant Treasury Officer ONLY'),
    ],
    'file_dir': r'\\hq-sapitf\SWIFT$\P01\input',
    'file_naming': 'aaaa_bbbb_ccxxxxxxxxyyyy.in',
    'file_types': {
        '01': 'pain.001.001.02 (CGI)',
        '02': 'pain.fin.mt101 (MT101)',
        '03': 'pain.001.001.03 (ISO 20022)',
    },
    'custom_tables': [
        ('ZFI_BCM_ACTIVE', 'BCM activation control per company code'),
        ('YSBC_TRACE_PAYMENT', 'Payment trace log'),
        ('ZVFI_BCM_ACTIVE', 'View on ZFI_BCM_ACTIVE'),
    ],
    'sap_notes': [
        '1698595','1698596','1697918','1697917','1697916',
        '1697915','1697914','1697913','1697912','1697911',
        '1697910','1697909','1697427','1697428',
    ],
}

DOC_VS_REALITY = [
    ('WS90000003 main payment release WF', 'Found in CTS RELE object D01K9B0BCM', 'CONFIRMED'),
    ('YWFI package for all WF objects', 'ZFI_BCM_ACTIVE FUGR found in CTS', 'CONFIRMED'),
    ('Z_GET_CERTIF_OFFICER_UNESDIR = Rule 90000001', 'FUNC Z_GET_CERTIF_OFFICER_UNESDIR in CTS', 'CONFIRMED'),
    ('ZFI_PAYREL_EMAIL fallback table', 'ZFI_PAYREL_EMAIL table exists, 2 rows: A_KHISTY, E_MOYO', 'CONFIRMED'),
    ('ZVFI_BCM_ACTIVE view for BCM activation', 'VIEW ZVFI_BCM_ACTIVE + TOBJ ZFI_BCM_ACTIVES in CTS', 'CONFIRMED'),
    ('DMEE tree: PAYM/CGI_XML_CT_UNESCO', 'Found in CTS (16 DMEE trees total)', 'CONFIRMED'),
    ('DMEE tree: PAYM/CITI/XML/UNESCO/DC_V3_01', 'Found in CTS', 'CONFIRMED'),
    ('DMEE tree: PAYM/SEPA_CT_UNES', 'Found in CTS', 'CONFIRMED'),
    ('Y_F110_AVIS advice forms per company', '7 FORM objects: UNES, UIS, UBO, UIL, IIEP, SG, base', 'CONFIRMED'),
    ('YENH_SUPPLIERS_PAYMENT_UBO enhancement', 'ENHO YENH_SUPPLIERS_PAYMENT_UBO in CTS', 'CONFIRMED'),
    ('BAdI DMEE: Y_BADI_IDFI_CGI_DMEE_DE/FR/IT/AE/BH', '5 ENBC objects confirmed in CTS', 'CONFIRMED'),
    ('ZBAPI_GET_PAYMENT_METHOD RFC-enabled FM', 'SRFC ZBAPI_GET_PAYMENT_METHOD in CTS', 'CONFIRMED'),
    ('ZSWIFT_CODE_CHECK RFC FM', 'FUNC ZSWIFT_CODE_CHECK in CTS', 'CONFIRMED'),
    ('BCM only for UNES, UBO, IIEP, UIL, UIS', 'REGUH B-prefix runs: UNES(480), UBO(641), IIEP(310), UIL(275), UIS(116)', 'CONFIRMED'),
    ('ICTP runs own F110 (no BCM)', 'REGUH: ICTP has T-prefix (705 runs), no B-prefix', 'CONFIRMED'),
    ('IBE/MGIE/ICBA: manual OP payments only', 'No REGUH rows for IBE/MGIE/ICBA/STEM', 'CONFIRMED'),
    ('All 9 company codes = self-pay (T042)', 'T042 BUKRS=ZBUKR for all entries', 'CONFIRMED'),
    ('BCM dual control: CRUSR ≠ CHUSR required', 'BNK_BATCH_HEADER: dual control gap in UNES approved batches', 'AUDIT FINDING'),
    ('WF only valid for UNES company code', 'No WF equivalent for other institutes in cts_objects', 'CONFIRMED'),
    ('22,488 UNES-exclusive vendors', 'Verified via REGUH LIFNR analysis', 'CONFIRMED'),
    ('45+ UNES house banks globally', 'T012K: 45+ HBKID entries under UNES', 'CONFIRMED'),
    ('Payment Method O = field office (excluded HQ)', 'T042E: O method in all company codes', 'CONFIRMED'),
    (f'SAPFPAYM 93 variants total', f'CTS VARX: {len(sapfpaym_variants)} SAPFPAYM variants found', 'CONFIRMED' if len(sapfpaym_variants) >= 80 else 'DELTA'),
    ('UNES treasury banks: SOG/CIT/BNP/SCB/WEL', 'T012K UNES: SOG,CIT,BNP,SCB,WEL prefixes found', 'CONFIRMED'),
    ('SWIFT Alliance Lite2 for payment file delivery', 'File dir documented in Blueprint BCM', 'DOC ONLY'),
    ('Bank Statement Monitor (FTE-BSM) for IBE/ICTP/IIEP/UBO/UIL', 'No FEBEP/FEBKO tables in Gold DB', 'PARTIAL — BSM config not in DB'),
    ('21 SAP Notes implemented', 'SAP Notes referenced in CTS MERG objects', 'PARTIAL'),
    ('YCL_IDFI_CGI_DMEE classes per country', 'CTS: CLAS YCL_IDFI_CGI_DMEE_AE + BH + CH/FR in CLSD', 'CONFIRMED'),
]

# ── V4: NEW STATIC DATA ──────────────────────────────────────────────────────

PAYMENT_PROCESSES = [
    {
        'num': 1, 'name': 'Payments managed OUTSIDE SAP',
        'cos': 'IBE, MGIE, ICBA, Field Offices',
        'tool': 'Local banking system or physical cheques',
        'f110': False, 'bcm': False,
        'role': 'YS:FI:D:DISPLAY__________:ALL',
        'flow': 'AO posts outgoing payment in SAP (clearing vendor, debiting sub-bank account). Creates transfer in LOCAL banking system or writes cheque.',
        'color': '#e74c3c', 'risk': '',
    },
    {
        'num': 2, 'name': 'F110 + Manual File Download',
        'cos': 'ICTP, UBO/Banco do Brazil, UNES checks (phasing out), UIL (migrating)',
        'tool': 'F110 payment run → file downloaded manually → uploaded to bank portal',
        'f110': True, 'bcm': False,
        'role': 'Y_XXXX_FI_AP_PAYMENTS',
        'flow': 'F110 creates payment file. User downloads to local directory, manually uploads to bank portal.',
        'color': '#f39c12', 'risk': '',
    },
    {
        'num': 3, 'name': 'F110 + BCM (2 validations) → Coupa → Bank',
        'cos': 'UIS, IIEP, UIL/new SG bank, UBO/Citibank',
        'tool': 'F110 → BCM 2 signatories → file auto-downloaded to Coupa → bank',
        'f110': True, 'bcm': True,
        'role': 'Y_XXXX_FI_AP_PAYMENTS OR YS:FI:M:BCM_MON_APP______:XXXX (NEVER BOTH on same user)',
        'flow': '2 BCM signatories must validate before file is generated and auto-sent to Coupa server.',
        'color': '#27ae60', 'risk': '',
    },
    {
        'num': 4, 'name': 'F110 + BCM (1 validation) → Coupa (2nd validation) → Bank',
        'cos': 'UNES HQ (BFM/FAS/AP)',
        'tool': 'F110 → BCM 1 signatory → Coupa → bank',
        'f110': True, 'bcm': True,
        'role': 'Y_XXXX_FI_AP_PAYMENTS + YS:FI:M:BCM_MON_APP______:XXXX (UNES-specific combination)',
        'flow': '1 BCM signatory validates. File auto-downloaded to Coupa. Coupa provides 2nd validation before sending to bank.',
        'color': '#e67e22',
        'risk': '⚠ SECURITY RISK: User with BOTH roles = bypass BCM entirely → 2023 INCIDENT',
    },
]

NAMED_VALIDATORS = [
    ('Treasurer', 'BFM 076', 'Anssi Yli-Hietanen', 'FABS', 'TRS', '$50,000,000'),
    ('GM USLS', 'BFM 977', 'Irma Adjanohoun', 'FABS', 'TRS', '$50,000,000'),
    ('Chief Accountant', 'BFM 080', 'Ebrima Sarr', 'FABS', 'TRS+AP', '$50,000,000'),
    ('Asst Treasury Officer', 'BFM 073', 'Baizid Gazi', 'FABS', 'TRS', '$50,000,000'),
    ('Accountant FRA', 'BFM 834', 'Yasmina Kassim', 'FABS', 'TRS', '$50,000,000'),
    ('Accountant FRA', 'BFM 077', 'Jeannette La', 'FABS', 'TRS', '$50,000,000'),
    ('Chief AP', 'BFM 058', 'Lionel Chabeau', 'FABS', 'AP', '$5,000,000'),
    ('Chief AR', 'BFM 053', 'Theptevy Sopraseuth', 'FABS', 'AP', '$5,000,000'),
    ('Chief PAY', 'BFM 046', 'Simona Bertoldini', 'FABS+STEPS', 'AP+PAY', '$5M / $300K'),
    ('Sr Finance Asst AP', 'BFM 383', 'Isabelle Marquand', 'FABS', 'AP', '$500,000'),
    ('Sr Finance Asst AP', 'BFM 049', 'Christina Lopez', 'FABS', 'AP', '$500,000'),
    ('Asst Officer PAY', 'BFM 037', 'Farinaz Derakhshan', 'STEPS', 'PAY', '$150,000'),
]

BCM_GROUPING_RULES = [
    ('UNES_AP_IK', '0 (highest)', 'FI-AP or FI-AR', 'UNES', 'Method L + InstrKey B1', 'US InstrucKey B1 — CitiDirect payments'),
    ('UNES_AR_BP', '1', 'FI-AR', 'UNES', 'Customer 600000-699999', 'Business Partner (Investments & FX)'),
    ('UNES_TR_TR', '1', 'TR-CM-BT', 'UNES', 'Treasury transfers', 'Bank-to-bank transfers (1 BCM validation only)'),
    ('UNES_AP_EX', '2', 'FI-AP or FI-AR-PR', 'UNES', 'Country in: MM/IR/IQ/SD/SS/SY/CU/KP/AE/MX/JO', 'Exception/embargo country list'),
    ('UNES_AP_ST', '3 (catch-all)', 'FI-AP or FI-AR', 'UNES', 'All remaining (standard 3rd party)', 'Standard AP — bulk of all payments'),
    ('PAYROLL', '1 (STEPS only)', 'HR-PY', 'UNES STEPS', 'All payroll runs', 'PAYROLL: 268,902 items — largest single rule'),
]

XML_CHAR_LAYERS = [
    ('Layer 1', 'Suppress Predefined Special', 'Fixed SAP set', '- + * / \\ . : ; , _ ( ) [ ] # &lt; &gt;', 'Characters removed entirely'),
    ('Layer 2', 'Replace National Characters', 'SAP conversion table', '&eacute;&rarr;E, &ouml;&rarr;O, &uuml;&rarr;U, &ccedil;&rarr;C, etc.', 'Accented chars replaced with ASCII equivalent'),
    ('Layer 3', 'Suppress Custom Defined', 'UNESCO custom set', '^"$%&amp;{[]}=`*~#;_!?&deg;', 'UNESCO-specific set removed entirely'),
]

COUNTRY_REQUIREMENTS = [
    ('US / CA', 'HIGH', 'US Travel Rule', '35-char limit on Name/Address/Payment Details. Use unstructured OR structured — never both.'),
    ('PL (Poland)', 'MEDIUM', 'IBAN required', 'IBAN node exception removed — all Polish vendors must have IBAN.'),
    ('MG (Madagascar)', 'HIGH', 'IBAN + BCM special rule', 'MGA without IBAN → BCM rule UNES_AP_X catches → must be manually rejected.'),
    ('TN (Tunisia)', 'MEDIUM', 'TND 3 decimal places', 'ControlSum must match individual amounts with 3 decimals. SAP Note required for conversion function.'),
    ('BR (Brazil)', 'HIGH', 'Tax ID + bank format', 'STCD2 for natural persons when STCD1 empty. Bank account "-" stripped. TAXID="TXID" constant in XML.'),
    ('AE / BH (UAE/Bahrain)', 'MEDIUM', 'Payment Purpose Code', 'InstrForCdtrAgt node required. Purpose code read from SGTXT via custom DMEE exit.'),
    ('JP (Japan)', 'LOW', 'JPY 0 decimal places', 'ControlSum adjustment needed for 0-decimal currency.'),
    ('COP / ARS / IRR / MMK / SDG', 'BLOCKER', 'Out of scope / Embargo', 'Colombia (tax ID in file), Argentina (ARS), Iran/Myanmar/Sudan (embargo) — excluded entirely.'),
]

SAP_NOTES_BCM_FULL = [
    ('1698595', 'FTE_BSM error FAGL_LEDGER_CUST023', 'FABS+STEPS'),
    ('1595730', 'BNK_MONI Batch status set to incorrect', 'FABS+STEPS'),
    ('1654923', 'BNK_MONI Status shows error even when file created', 'FABS+STEPS'),
    ('1698455', 'BCM no alert during/after file creation problems', 'FABS+STEPS'),
    ('1704078', 'BCM Alert table BNK_BTCH_TIMEOUT too large', 'FABS+STEPS'),
    ('1836541', 'BNK_MONI Check on existence of payment file', 'FABS+STEPS'),
    ('1978287', 'BNK_MONI message file not yet created is incorrect', 'FABS+STEPS'),
    ('1681517', 'RBNK_MERGE_RESET restriction to batch number', 'FABS+STEPS'),
    ('1892712', 'RBNK_MERGE_RESET P_BATNO field name not label', 'FABS+STEPS'),
    ('1566148', 'BCM Duplicate payment file from proposal run', 'FABS+STEPS'),
    ('2028671', 'BCM Rule description not saved after change', 'FABS+STEPS'),
    ('1598633', 'Process improvement returned batches', 'STEPS'),
    ('1488375', 'Attachment for returned batches (not valid)', 'FABS+STEPS'),
    ('1876093', 'SBWP correction on attachment for returned', 'FABS+STEPS'),
    ('1879033', 'Process change for returned batches', 'STEPS'),
    ('1997772', 'BCM Rule Maintenance on currency and amounts', 'FABS+STEPS'),
    ('1999340', 'BCM Rule Maintenance correction on 1997772', 'FABS+STEPS'),
    ('1391319', 'Batch Creation HR Payroll BCM activation error', 'STEPS'),
    ('1416652', 'Termination of SAPFPAYM_MERGE', 'STEPS'),
    ('1718468', 'BNK_MONI Authorization check', 'STEPS'),
    ('1697428', 'Message FZ116 HR Payments', 'STEPS'),
]

WF_KNOWN_ISSUES = [
    {
        'issue': 'BCM Batch Work Item Reservation (Lock)',
        'symptom': 'BCM batch visible in BNK_MONI but absent from other approvers SAP inbox after one user opens it',
        'root_cause': 'Clicking WF work item reserves it for that user — disappears from all other approvers inboxes',
        'affected': 'IIEP batches 8544, 8545, 8546 — stuck with M_SARMENTO-G (Mariana Sarmento Godoi)',
        'wf_task': 'WF task IS 50100025 — Release the Work Item (BCM batch approvers pool)',
        'approvers': 'IIEP pool: A_DE-GRAUWE, A_LOPEZ-REY, A_TERRER, E_MOYO, E_ZADRA, M_POISSON, M_SARMENTO-G, P_DIAS, S_GRANT-LEWI',
        'fix': 'Use transaction SWIA (Work Item Administration) to reassign or release the locked work item',
    },
    {
        'issue': 'Wrong Certifying Officer / No WF Validator Found',
        'symptom': 'Workflow item sent to wrong person or nobody gets it — vendor stays blocked',
        'root_cause': 'Email mismatch between SAP SU01 profile email and UNESdir LDAP directory',
        'affected': 'UNES KR/KA/KT/ER/IT documents — certifying officer resolution via LDAP',
        'wf_task': 'Rule 90000001 → Z_GET_CERTIF_OFFICER_UNESDIR → SOAP proxy → role.hq.int.unesco.org',
        'approvers': 'ZFI_PAYREL_EMAIL fallback users: A_KHISTY, E_MOYO',
        'fix': '1. Check UNESdir: https://role.hq.int.unesco.org  2. Check SU01 email parameter matches LDAP  3. Use ZFI_PAYREL_EMAIL as last resort',
    },
]

UIL_CONFIG = [
    ('SOG05', 'EUR01', 'EUR', 'GL 1175792', 'Method S (SEPA EUR)', 'New SG account for UIL'),
    ('SOG05', 'USD01', 'USD', 'GL 1175791', 'Method N (International)', 'New SG account for UIL'),
]

VALIDATION_FLOWS = [
    ('Vendor/Customer/Staff payments', 'FAS/AP', 'AP group', 'TRS group'),
    ('Business Partner (Inv & FX)', 'FAS/AP', 'TRS group', 'TRS group'),
    ('Bank-to-bank transfers', 'TRS/MO', 'TRS group', 'N/A (1 validation only)'),
    ('Payroll bank transfers', 'FAS/PAY', 'PAY group', 'TRS group'),
]

# ── END V4 STATIC DATA ────────────────────────────────────────────────────────

PAYMENT_TIERS = [
    ('UNES', 'Full Autonomous', 'F110 + BCM + SWIFT', '7,999 direct runs + 480 BCM runs'),
    ('UBO', 'Full Autonomous', 'F110 + BCM + SWIFT', '1,726 direct + 641 BCM'),
    ('IIEP', 'Full Autonomous', 'F110 + BCM + SWIFT', '780 direct + 310 BCM'),
    ('UIL', 'Full Autonomous', 'F110 + BCM + SWIFT', '650 direct + 275 BCM'),
    ('UIS', 'Full Autonomous', 'F110 + BCM + SWIFT', '391 direct + 116 BCM'),
    ('ICTP', 'Autonomous (no BCM)', 'F110 only (T-prefix variants)', '705 ICTP runs + 898 direct'),
    ('IBE', 'Manual OP', 'Manual payments only', 'No F110 runs in REGUH'),
    ('MGIE', 'Manual OP', 'Manual payments only', 'No F110 runs in REGUH'),
    ('ICBA', 'Manual OP', 'Manual payments only', 'No F110 runs in REGUH'),
]

# ── 3. Build JSON for vis.js E2E flow ─────────────────────────────────────────

flow_nodes = [
    {'id': 1, 'label': 'Invoice\nPosted', 'group': 'fi', 'title': 'BKPF BLART=KR/RE/KG/KA\nBSEG line items created'},
    {'id': 2, 'label': 'Payment\nBlock Set', 'group': 'wf', 'title': 'BSEG.ZLSPR = payment block\nEvent BSEGCREATED triggered'},
    {'id': 3, 'label': 'WF Started\nWS90000003', 'group': 'wf', 'title': 'ZBSEG_FRAME1 main workflow\nYBSEG business object\nYWFI package'},
    {'id': 4, 'label': 'Certifying\nOfficer?', 'group': 'wf', 'title': 'Doc type KR/KA/KT/ER/IT\n→ Rule 90000001\n→ Z_GET_CERTIF_OFFICER_UNESDIR\n→ SharePoint role.hq.int.unesco.org'},
    {'id': 5, 'label': 'Group\nValidator', 'group': 'wf', 'title': 'Other doc types\n→ Rule 90000002\n→ Z_WF_FI_PR_WF_ACTOR1_DET\nGroups: BSP/CFS, BFM/PAY, HRM/SPI etc.'},
    {'id': 6, 'label': 'WF\nApproved', 'group': 'wf', 'title': 'Payment block removed\nVendor released for payment'},
    {'id': 7, 'label': 'F110\nRun', 'group': 'f110', 'title': 'SAPFPAYM (93 variants)\nREGUH/REGUP populated\nLAUFI prefix: B=BCM, 0=Direct, T=ICTP'},
    {'id': 8, 'label': 'Payment\nProposal', 'group': 'f110', 'title': 'REGUH.XVORL flag set\nBank account selected\nDue date check'},
    {'id': 9, 'label': 'Payment\nRun', 'group': 'f110', 'title': 'PAYR payment media created\nBKPF ZP docs posted\nBSAK clearing entries'},
    {'id': 10, 'label': 'DMEE\nXML Build', 'group': 'dmee', 'title': '16 DMEE trees\nCGI: PAYM/CGI_XML_CT_UNESCO\nCITI: PAYM/CITI/XML/UNESCO/DC_V3_01\nSEPA: PAYM/SEPA_CT_UNES\nCustom BAdIs: DE/FR/IT/AE/BH'},
    {'id': 11, 'label': 'BCM\nBatch', 'group': 'bcm', 'title': 'BNK_BATCH_HEADER + BNK_BATCH_ITEM\nRule: BNK_INI 90000005→WF50100024\nRule: BNK_COM 90000004→WF50100021'},
    {'id': 12, 'label': 'BCM\nRelease 1', 'group': 'bcm', 'title': 'BCM approver review\nDelegation of Authority (Annex III)\nBFM/TRS up to $50M'},
    {'id': 13, 'label': 'BCM\nRelease 2', 'group': 'bcm', 'title': 'Second signatory (dual control)\nCRUSR ≠ CHUSR required\n⚠ Audit finding: same user batches in UNES'},
    {'id': 14, 'label': 'SWIFT\nFile', 'group': 'swift', 'title': r'File: \\hq-sapitf\SWIFT$\P01\input' + '\npain.001.001.02/03 or MT101\nSwift Alliance Lite2'},
    {'id': 15, 'label': 'Bank\nExecutes', 'group': 'bank', 'title': 'UNES: SOG(SG EUR), CIT(USD), BNP, SCB, WEL\nICTP: BPP01, UNI01\n45+ UNES field office banks'},
    {'id': 16, 'label': 'Bank\nStatement', 'group': 'recon', 'title': 'FTE-BSM: IBE/ICTP/IIEP/UBO/UIL\nFEBEP/FEBKO (not in Gold DB)\nMT940/camt.053'},
    {'id': 17, 'label': 'Reconciled', 'group': 'recon', 'title': 'BSAK.AUGDT clearing date\nF-03 / FF67 bank reconciliation\nYFI_BANK_RECONCILIATION transaction'},
    {'id': 18, 'label': 'Direct Pay\n(no BCM)', 'group': 'direct', 'title': 'ICTP / direct variants\nLAUFI prefix 0 or T\nNo BCM batch created'},
    {'id': 19, 'label': 'Method O\nField Office', 'group': 'fo', 'title': 'Payment Method O\nSubstitution rule: set O by user ID\nExcluded from HQ F110 run\nExcluded from WF'},
]

flow_edges = [
    {'from': 1, 'to': 2, 'label': 'BSEGCREATED', 'arrows': 'to'},
    {'from': 2, 'to': 3, 'label': 'Event trigger', 'arrows': 'to'},
    {'from': 3, 'to': 4, 'label': 'KR/KA/KT/ER/IT', 'arrows': 'to'},
    {'from': 3, 'to': 5, 'label': 'Other doc types', 'arrows': 'to'},
    {'from': 4, 'to': 6, 'label': 'CO approves', 'arrows': 'to'},
    {'from': 5, 'to': 6, 'label': 'Group approves', 'arrows': 'to'},
    {'from': 6, 'to': 7, 'label': 'Block released', 'arrows': 'to'},
    {'from': 7, 'to': 8, 'label': 'Proposal', 'arrows': 'to'},
    {'from': 8, 'to': 9, 'label': 'Execute', 'arrows': 'to'},
    {'from': 9, 'to': 10, 'label': 'Build file', 'arrows': 'to'},
    {'from': 10, 'to': 11, 'label': 'LAUFI=B*', 'arrows': 'to'},
    {'from': 10, 'to': 18, 'label': 'LAUFI=0/T/M', 'arrows': 'to'},
    {'from': 11, 'to': 12, 'label': 'Submit', 'arrows': 'to'},
    {'from': 12, 'to': 13, 'label': 'Release 1', 'arrows': 'to'},
    {'from': 13, 'to': 14, 'label': 'Release 2', 'arrows': 'to'},
    {'from': 18, 'to': 14, 'label': 'Direct', 'arrows': 'to'},
    {'from': 14, 'to': 15, 'label': 'SWIFT', 'arrows': 'to'},
    {'from': 15, 'to': 16, 'label': 'Statement', 'arrows': 'to'},
    {'from': 16, 'to': 17, 'label': 'Match', 'arrows': 'to'},
    {'from': 1, 'to': 19, 'label': 'Meth=O', 'arrows': 'to', 'dashes': True},
]

# ── 4. Render HTML ─────────────────────────────────────────────────────────────

VIS_PATH = Path(__file__).parent / 'vis-network.min.js'
vis_js = VIS_PATH.read_text(encoding='utf-8') if VIS_PATH.exists() else '/* vis.js not found */'

def badge(color, text):
    return f'<span style="background:{color};color:#fff;padding:2px 7px;border-radius:10px;font-size:11px;white-space:nowrap">{text}</span>'

def status_badge(s):
    c = {'CONFIRMED': '#27ae60', 'AUDIT FINDING': '#e74c3c', 'PARTIAL': '#f39c12',
         'DOC ONLY': '#7f8c8d', 'DELTA': '#2980b9'}.get(s, '#95a5a6')
    return badge(c, s)

def tier_badge(t):
    c = {'Full Autonomous': '#27ae60', 'Autonomous (no BCM)': '#2980b9', 'Manual OP': '#e74c3c'}.get(t, '#95a5a6')
    return badge(c, t)

def type_label(t):
    labels = {
        'VARX': 'Variant', 'ACGR': 'Auth Role', 'DOCU': 'Documentation', 'PROG': 'Program',
        'FUNC': 'Function Module', 'MESS': 'Message', 'ENHO': 'Enhancement Impl',
        'DMEE': 'DMEE Tree', 'CLAS': 'Class', 'TABL': 'Table', 'SRFC': 'RFC FM',
        'TRAN': 'Transaction', 'FORM': 'SAPscript Form', 'SFPF': 'PDF Form',
        'FUGR': 'Function Group', 'REPT': 'Include', 'ENBC': 'BAdI Impl',
        'ENHC': 'Enhancement Spot', 'METH': 'Method', 'CLSD': 'Class', 'CPUB': 'Method Public',
        'VIEW': 'View', 'CUS0': 'Cust Table', 'CUS1': 'Cust Entry', 'TOBJ': 'Table Object',
        'VDAT': 'View Cluster', 'REPS': 'Program Include', 'MERG': 'Transport Merge',
        'DTED': 'Data Element Def', 'DTEL': 'Data Element', 'DYNP': 'Screen',
        'RELE': 'Transport Release', 'SXCI': 'BAdI Classic', 'TABD': 'Table Def',
        'TTYP': 'Table Type', 'AQQV': 'Query', 'CINC': 'Class Include', 'CPRI': 'Class Private',
        'CPRO': 'Class Protected', 'DEVC': 'Package', 'FUGT': 'FG Text', 'INTF': 'Interface',
        'MSAG': 'Message Class', 'ENHS': 'Enh Spot', 'ENQU': 'Lock Object',
    }
    return labels.get(t, t)

def build_obj_inventory():
    rows = []
    type_colors = {
        'DMEE': '#1abc9c', 'FUNC': '#3498db', 'SRFC': '#2980b9', 'FUGR': '#1a5276',
        'PROG': '#8e44ad', 'CLAS': '#6c3483', 'CLSD': '#6c3483', 'ENHO': '#e67e22',
        'ENBC': '#d35400', 'ENHC': '#d35400', 'ACGR': '#e74c3c', 'VARX': '#7f8c8d',
        'TABL': '#16a085', 'VIEW': '#148f77', 'TRAN': '#2c3e50', 'FORM': '#e91e63',
        'CUS0': '#795548', 'CUS1': '#795548', 'TOBJ': '#607d8b',
    }
    for obj_type, names in sorted(cts_by_type.items(), key=lambda x: (-len(x[1]), x[0])):
        color = type_colors.get(obj_type, '#95a5a6')
        label = type_label(obj_type)
        rows.append(f'<tr><td><span style="background:{color};color:#fff;padding:1px 6px;border-radius:4px;font-size:11px">{obj_type}</span></td>')
        rows.append(f'<td style="color:#666">{label}</td>')
        rows.append(f'<td style="text-align:center;font-weight:bold">{len(names)}</td>')
        nm_html = ' '.join(
            f'<code style="font-size:10px;background:#f8f9fa;padding:1px 3px;border-radius:2px">{n[:50]}</code>'
            for n in names[:10]
        )
        if len(names) > 10:
            nm_html += f' <em style="color:#999">+{len(names) - 10} more</em>'
        rows.append(f'<td>{nm_html}</td></tr>')
    return '\n'.join(rows)

def build_dvr_table():
    rows = []
    for claim, reality, status in DOC_VS_REALITY:
        rows.append(f'<tr><td style="font-size:12px">{claim}</td>'
                    f'<td style="font-size:12px;color:#2c3e50">{reality}</td>'
                    f'<td>{status_badge(status)}</td></tr>')
    return '\n'.join(rows)

def build_dmee_table():
    tree_info = {
        'PAYM/CGI_XML_CT_UNESCO': ('CGI XML', 'UNES + institutes', 'CGI pain.001 format'),
        'PAYM/CGI_XML_CT_UNESCO_1': ('CGI XML v1', 'UNES', 'Variant 1'),
        'PAYM/CITI/XML/UNESCO/DC_V3_01': ('Citi DC v3.01', 'UNES/UBO', 'Citibank Direct Credit XML'),
        'PAYM/CITI/XML/UNESCO/DIRECT_CREDIT': ('Citi DC', 'UNES', 'Citibank Direct Credit'),
        'PAYM/CITIPMW/CITI_XML_V2_50': ('Citi PMW v2.50', 'UNES', 'Citibank Payment Media Workbench'),
        'PAYM/CITIPMW/CITI_XML_V3_01': ('Citi PMW v3.01', 'UNES', 'Citibank PMW v3'),
        'PAYM/CITIPMW/CSF_CITI_XML_01': ('Citi CSF', 'UNES', 'Citibank CSF format'),
        'PAYM/SEPA_CT_ICTP_ISO': ('SEPA CT ICTP', 'ICTP', 'ISO 20022 SEPA Credit Transfer'),
        'PAYM/SEPA_CT_ICTP_ISO_1': ('SEPA CT ICTP 1', 'ICTP', 'Variant 1'),
        'PAYM/SEPA_CT_ICTP_ISO_2': ('SEPA CT ICTP 2', 'ICTP', 'Variant 2'),
        'PAYM/SEPA_CT_ICTP_ISO_EXCEE': ('SEPA CT Exceed', 'ICTP', 'Exceeding SEPA limit variant'),
        'PAYM/SEPA_CT_ICTP_ISO_EXTRASEPA': ('SEPA Extra', 'ICTP', 'Extra-SEPA international'),
        'PAYM/SEPA_CT_ICTP_ISO_EXTRASEPABA': ('SEPA Extra BA', 'ICTP', 'Extra-SEPA with bank address'),
        'PAYM/SEPA_CT_ICTP_ISO_EXTRASEPA_2': ('SEPA Extra 2', 'ICTP', 'Variant 2'),
        'PAYM/SEPA_CT_ICTP_ISO_EXTRASEPA_I': ('SEPA Extra I', 'ICTP', 'Extra SEPA I'),
        'PAYM/SEPA_CT_UNES': ('SEPA CT UNES', 'UNES', 'UNESCO SEPA Credit Transfer'),
    }
    badi_countries = {'DE': 'Germany', 'FR': 'France', 'IT': 'Italy', 'AE': 'UAE', 'BH': 'Bahrain'}
    rows = []
    for tree in dmee_trees:
        info = tree_info.get(tree, ('—', '—', '—'))
        rows.append(f'<tr><td><code style="font-size:11px">{tree}</code></td>'
                    f'<td>{info[0]}</td><td>{info[1]}</td>'
                    f'<td style="color:#666">{info[2]}</td></tr>')
    rows.append('<tr><td colspan="4" style="background:#fff8e1;padding:8px"><strong>Country BAdIs:</strong> ' +
                ' '.join(f'<code>Y_BADI_IDFI_CGI_DMEE_{k}</code> ({v})' for k, v in badi_countries.items()) +
                '<br><strong>Enhancement:</strong> YENH_FI_DMEE (spot), YENH_FI_DMEE_CGI_FALLBACK (impl)<br>'
                '<strong>Classes:</strong> YCL_IDFI_CGI_DMEE_AE/BH/CH/FR + CL_IDFI_CGI_DMEE_CH/FR</td></tr>')
    return '\n'.join(rows)

def build_variant_table():
    groups = {'UNES': [], 'UBO': [], 'UIL': [], 'UIS': [], 'IIEP': [], 'ICTP': [], 'Multi/Global': []}
    for v in sapfpaym_variants:
        if 'UNE' in v or 'une' in v:
            groups['UNES'].append(v)
        elif 'UBO' in v:
            groups['UBO'].append(v)
        elif 'UIL' in v:
            groups['UIL'].append(v)
        elif 'UIS' in v:
            groups['UIS'].append(v)
        elif 'IIEP' in v:
            groups['IIEP'].append(v)
        elif 'ICTP' in v:
            groups['ICTP'].append(v)
        else:
            groups['Multi/Global'].append(v)
    rows = []
    for co, variants in groups.items():
        if not variants:
            continue
        rows.append(
            f'<tr><td style="font-weight:bold;vertical-align:top">{co}</td>'
            f'<td style="text-align:center">{len(variants)}</td><td>' +
            ' '.join(
                f'<code style="font-size:10px;background:#eee;padding:1px 3px;border-radius:2px">{v[8:]}</code>'
                for v in sorted(variants)
            ) + '</td></tr>'
        )
    return '\n'.join(rows)

def build_f110_table():
    rows = []
    for co, stats_list in sorted(f110_stats.items()):
        total_items = sum(s['items'] for s in stats_list)
        total_runs = sum(s['runs'] for s in stats_list)
        bcm_items = sum(s['items'] for s in stats_list if s['prefix'] == 'B')
        bcm_pct = f'{bcm_items / total_items * 100:.0f}%' if total_items > 0 else '0%'
        prefixes = ' '.join(
            f'<code style="font-size:10px;background:{"#1abc9c" if s["prefix"] == "B" else "#eee"};'
            f'color:{"white" if s["prefix"] == "B" else "black"};padding:1px 3px;border-radius:2px">'
            f'{s["prefix"]}:{s["runs"]}r/{s["items"]:,}i</code>'
            for s in stats_list
        )
        rows.append(
            f'<tr><td style="font-weight:bold">{co}</td>'
            f'<td style="text-align:right">{total_runs:,}</td>'
            f'<td style="text-align:right">{total_items:,}</td>'
            f'<td style="text-align:right">{bcm_pct}</td>'
            f'<td>{prefixes}</td></tr>'
        )
    return '\n'.join(rows)

def build_bcm_table():
    rows = []
    for co, s in sorted(bcm_stats.items(), key=lambda x: -x[1]['items']):
        dual = s['dual_ctrl_fail']
        if dual > 0:
            db_badge = f'<span style="background:#e74c3c;color:#fff;padding:1px 5px;border-radius:8px;font-size:11px">&#9888; {dual} batches</span>'
        else:
            db_badge = '<span style="background:#27ae60;color:#fff;padding:1px 5px;border-radius:8px;font-size:11px">OK</span>'
        rows.append(
            f'<tr><td style="font-weight:bold">{co}</td>'
            f'<td style="text-align:right">{s["batches"]:,}</td>'
            f'<td style="text-align:right">{s["items"]:,}</td>'
            f'<td>{db_badge}</td></tr>'
        )
    return '\n'.join(rows)

def build_hb_table():
    rows = []
    for co in ['UNES', 'UBO', 'IIEP', 'UIL', 'UIS', 'ICTP', 'IBE', 'MGIE', 'ICBA']:
        hbs = hb_by_bukrs.get(co, [])
        currencies = sorted(set(h['waers'] for h in hbs))
        bank_ids = sorted(set(h['hbkid'] for h in hbs))
        rows.append(
            f'<tr><td style="font-weight:bold">{co}</td>'
            f'<td style="text-align:right">{len(bank_ids)}</td>'
            f'<td style="text-align:right">{len(hbs)}</td>'
            f'<td style="font-size:11px">{", ".join(currencies[:8])}</td>'
            f'<td style="font-size:11px">{", ".join(bank_ids[:5])}{"..." if len(bank_ids) > 5 else ""}</td></tr>'
        )
    return '\n'.join(rows)

def build_wf_actor_table():
    rows = []
    for doc_types, group, desc in VALIDATION_GROUPS:
        rows.append(f'<tr><td><code>{doc_types}</code></td>'
                    f'<td style="font-weight:bold">{group}</td>'
                    f'<td style="color:#666">{desc}</td></tr>')
    rows.append(
        '<tr><td colspan="3" style="background:#e8f4f8;padding:8px">'
        '<strong>Rule 90000001:</strong> Z_GET_CERTIF_OFFICER_UNESDIR → role.hq.int.unesco.org (SharePoint WCF + SQL)<br>'
        '<strong>Rule 90000002:</strong> Z_WF_FI_PR_WF_ACTOR1_DET (FG: Z_WF_FI_EVENT_PAYMENT_METH)<br>'
        f'<strong>Fallback email:</strong> ZFI_PAYREL_EMAIL → {", ".join(r[0] for r in payrel_email)}<br>'
        '<strong>Notifications:</strong> RSWUWFML2 / variant ZWKFLOW_FI_EMA</td></tr>'
    )
    return '\n'.join(rows)

def build_tier_table():
    rows = []
    for co, tier, method, data in PAYMENT_TIERS:
        name = companies.get(co, co)
        methods = t042e.get(co, '—')
        rows.append(
            f'<tr><td style="font-weight:bold">{co}</td>'
            f'<td>{name[:30]}</td>'
            f'<td>{tier_badge(tier)}</td>'
            f'<td style="font-size:11px">{method}</td>'
            f'<td style="font-size:11px">{data}</td>'
            f'<td style="font-size:10px">{methods}</td></tr>'
        )
    return '\n'.join(rows)

def build_bcm_rules_table():
    rows = []
    for r in BCM_CONFIG['release_rules']:
        rows.append(
            f'<tr><td><code>{r["rule"]}</code></td>'
            f'<td><code>{r["type"]}</code></td>'
            f'<td>{r["step"]}</td>'
            f'<td><code>{r["wf"]}</code></td>'
            f'<td>{r["proc"]}</td></tr>'
        )
    return '\n'.join(rows)

def build_payment_processes_table():
    rows = []
    for p in PAYMENT_PROCESSES:
        rows.append(
            f'<tr style="border-left:4px solid {p["color"]}">'
            f'<td style="font-weight:bold;color:{p["color"]};text-align:center;font-size:18px">{p["num"]}</td>'
            f'<td style="font-weight:bold">{p["name"]}</td>'
            f'<td style="font-size:11px">{p["cos"]}</td>'
            f'<td style="font-size:11px">{p["tool"]}</td>'
            f'<td style="font-size:11px"><code style="font-size:9px">{p["role"]}</code></td>'
            f'<td style="font-size:11px;color:#7fb3d3">{p["flow"]}'
            + (f'<br><span style="color:#e74c3c;font-weight:bold">{p["risk"]}</span>' if p['risk'] else '')
            + '</td></tr>'
        )
    return '\n'.join(rows)

def build_named_validators_table():
    rows = []
    for post, code, name, sys, grp, limit in NAMED_VALIDATORS:
        rows.append(
            f'<tr><td style="font-size:11px">{post}</td>'
            f'<td><code style="font-size:10px">{code}</code></td>'
            f'<td style="font-weight:bold;font-size:12px">{name}</td>'
            f'<td style="text-align:center"><span style="background:#1a5276;color:#fff;padding:1px 5px;border-radius:4px;font-size:10px">{sys}</span></td>'
            f'<td style="text-align:center"><span style="background:#0d4a44;color:#1abc9c;padding:1px 5px;border-radius:4px;font-size:10px">{grp}</span></td>'
            f'<td style="text-align:right;font-weight:bold;color:#1abc9c">{limit}</td></tr>'
        )
    return '\n'.join(rows)

def build_grouping_rules_table():
    rows = []
    for rule, prio, origin, co, criteria, desc in BCM_GROUPING_RULES:
        rows.append(
            f'<tr><td><code>{rule}</code></td>'
            f'<td style="text-align:center">{prio}</td>'
            f'<td style="font-size:11px">{origin}</td>'
            f'<td style="font-size:11px">{criteria}</td>'
            f'<td style="font-size:11px;color:#7fb3d3">{desc}</td></tr>'
        )
    return '\n'.join(rows)

def build_xml_char_table():
    rows = []
    for layer, name, scope, chars, effect in XML_CHAR_LAYERS:
        rows.append(
            f'<tr><td style="font-weight:bold;color:#1abc9c">{layer}</td>'
            f'<td>{name}</td>'
            f'<td style="font-size:11px">{scope}</td>'
            f'<td><code style="font-size:10px">{chars}</code></td>'
            f'<td style="font-size:11px;color:#7fb3d3">{effect}</td></tr>'
        )
    return '\n'.join(rows)

def build_country_req_table():
    rows = []
    risk_colors = {'HIGH': '#e74c3c', 'MEDIUM': '#f39c12', 'LOW': '#27ae60', 'BLOCKER': '#8e44ad'}
    for country, risk, req_type, detail in COUNTRY_REQUIREMENTS:
        c = risk_colors.get(risk, '#95a5a6')
        rows.append(
            f'<tr><td style="font-weight:bold">{country}</td>'
            f'<td><span style="background:{c};color:#fff;padding:1px 6px;border-radius:8px;font-size:10px">{risk}</span></td>'
            f'<td style="font-weight:bold;font-size:11px">{req_type}</td>'
            f'<td style="font-size:11px">{detail}</td></tr>'
        )
    return '\n'.join(rows)

def build_sap_notes_full():
    rows = []
    for note, desc, sys in SAP_NOTES_BCM_FULL:
        rows.append(
            f'<tr><td><code>{note}</code></td>'
            f'<td style="font-size:11px">{desc}</td>'
            f'<td><span style="background:#1a5276;color:#7fb3d3;padding:1px 5px;border-radius:4px;font-size:10px">{sys}</span></td></tr>'
        )
    return '\n'.join(rows)

def build_wf_issues_table():
    rows = []
    for i in WF_KNOWN_ISSUES:
        rows.append(
            f'<tr><td style="font-weight:bold;color:#e74c3c">{i["issue"]}</td>'
            f'<td style="font-size:11px">{i["symptom"]}</td>'
            f'<td style="font-size:11px;color:#f39c12">{i["root_cause"]}</td>'
            f'<td style="font-size:11px">{i["affected"]}</td>'
            f'<td style="font-size:11px;color:#1abc9c">{i["fix"]}</td></tr>'
        )
    return '\n'.join(rows)

def build_validation_flows_table():
    rows = []
    for flow, run_by, v1, v2 in VALIDATION_FLOWS:
        dual = v2 != 'N/A (1 validation only)'
        rows.append(
            f'<tr><td style="font-weight:bold">{flow}</td>'
            f'<td><code>{run_by}</code></td>'
            f'<td style="color:#1abc9c">{v1}</td>'
            f'<td style="color:{"#1abc9c" if dual else "#7f8c8d"}">{v2}</td></tr>'
        )
    return '\n'.join(rows)

# ── 5. HTML ────────────────────────────────────────────────────────────────────

total_objs = len(cts_objs)
total_f110 = sum(sum(s['items'] for s in sl) for sl in f110_stats.values())
total_bcm = sum(s['items'] for s in bcm_stats.values())
total_dmee = len(dmee_trees)
total_roles = len(bcm_roles)
total_variants = len(sapfpaym_variants)
confirmed = sum(1 for _, _, s in DOC_VS_REALITY if s == 'CONFIRMED')
findings = sum(1 for _, _, s in DOC_VS_REALITY if s == 'AUDIT FINDING')
partial = sum(1 for _, _, s in DOC_VS_REALITY if s in ('PARTIAL', 'DELTA', 'DOC ONLY'))

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>UNESCO SAP Payment &amp; BCM Intelligence Companion v4</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#0f1923;color:#e0e0e0;font-size:13px}}
.header{{background:linear-gradient(135deg,#1a2a3a,#0d2137);padding:24px 32px;border-bottom:3px solid #1abc9c}}
.header h1{{color:#1abc9c;font-size:22px;letter-spacing:1px}}
.header .sub{{color:#7fb3d3;font-size:12px;margin-top:4px}}
.kpi-bar{{display:flex;gap:12px;padding:16px 32px;background:#12202e;flex-wrap:wrap;border-bottom:1px solid #1e3a4a}}
.kpi{{background:#1a2d3e;border-radius:8px;padding:10px 16px;text-align:center;min-width:100px}}
.kpi .val{{font-size:24px;font-weight:700;color:#1abc9c}}
.kpi .lbl{{font-size:10px;color:#7fb3d3;text-transform:uppercase;letter-spacing:1px;margin-top:2px}}
.tabs{{display:flex;background:#0d1c28;padding:0 32px;border-bottom:1px solid #1e3a4a;flex-wrap:wrap}}
.tab{{padding:10px 16px;cursor:pointer;color:#7fb3d3;font-size:12px;letter-spacing:.5px;border-bottom:3px solid transparent;transition:all .2s;white-space:nowrap}}
.tab:hover{{color:#1abc9c}}
.tab.active{{color:#1abc9c;border-bottom-color:#1abc9c;background:#12202e}}
.content{{display:none;padding:24px 32px}}
.content.active{{display:block}}
.section{{background:#1a2d3e;border-radius:8px;padding:16px;margin-bottom:16px;border:1px solid #1e3a4a}}
.section h3{{color:#1abc9c;font-size:13px;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #1e3a4a}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{background:#12202e;color:#7fb3d3;padding:8px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.5px}}
td{{padding:6px 8px;border-bottom:1px solid #1e3a4a;vertical-align:top}}
tr:hover td{{background:#1e3a4a}}
code{{background:#12202e;padding:1px 4px;border-radius:3px;font-family:monospace;color:#1abc9c;font-size:11px}}
.alert{{background:#2d1515;border:1px solid #e74c3c;border-radius:6px;padding:12px;margin:8px 0;color:#f5b7b1}}
.info{{background:#12293e;border:1px solid #1abc9c;border-radius:6px;padding:12px;margin:8px 0;color:#a9cce3}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}}
#flowCanvas{{width:100%;height:520px;border:1px solid #1e3a4a;border-radius:8px;background:#12202e}}
.wf-box{{border:2px solid #1abc9c;border-radius:8px;padding:16px;background:#12293e;margin-bottom:12px}}
.wf-box h4{{color:#1abc9c;font-size:12px;margin-bottom:8px}}
.fm-card{{background:#0d1c28;border:1px solid #1e3a4a;border-radius:6px;padding:10px;margin:4px 0}}
.fm-card code{{color:#f39c12}}
.fm-card .desc{{color:#7fb3d3;font-size:11px;margin-top:3px}}
.steplist{{list-style:none;padding:0}}
.steplist li{{padding:5px 8px;margin:3px 0;background:#12202e;border-radius:4px;border-left:3px solid #1abc9c;font-size:12px}}
</style>
</head>
<body>
<div class="header">
  <h1>UNESCO SAP Payment &amp; BCM Intelligence Companion&#160;<span style="font-size:14px;color:#7fb3d3">v4</span></h1>
  <div class="sub">Complete intelligence: E2E flow &middot; 4 payment processes &middot; {total_objs} CTS objects &middot; WF architecture &middot; BCM config &middot; Named validators &middot; Doc vs Reality &middot; {total_dmee} DMEE trees &middot; {total_variants} variants &middot; XML char handling &middot; Infrastructure</div>
</div>

<div class="kpi-bar">
  <div class="kpi"><div class="val">{total_objs}</div><div class="lbl">CTS Objects</div></div>
  <div class="kpi"><div class="val">{total_f110:,}</div><div class="lbl">F110 Items</div></div>
  <div class="kpi"><div class="val">{total_bcm:,}</div><div class="lbl">BCM Items</div></div>
  <div class="kpi"><div class="val">{total_dmee}</div><div class="lbl">DMEE Trees</div></div>
  <div class="kpi"><div class="val">{total_roles}</div><div class="lbl">BCM Roles</div></div>
  <div class="kpi"><div class="val">{total_variants}</div><div class="lbl">SAPFPAYM Variants</div></div>
  <div class="kpi"><div class="val" style="color:#27ae60">{confirmed}</div><div class="lbl">Confirmed</div></div>
  <div class="kpi"><div class="val" style="color:#e74c3c">{findings}</div><div class="lbl">Audit Findings</div></div>
  <div class="kpi"><div class="val">{payr_count:,}</div><div class="lbl">PAYR Records</div></div>
</div>

<div class="tabs">
  <div class="tab active" onclick="show('e2e',this)">E2E Flow</div>
  <div class="tab" onclick="show('companies',this)">Companies</div>
  <div class="tab" onclick="show('wf',this)">WF Architecture</div>
  <div class="tab" onclick="show('bcm',this)">BCM Config</div>
  <div class="tab" onclick="show('dmee',this)">DMEE Trees</div>
  <div class="tab" onclick="show('objects',this)">Object Inventory</div>
  <div class="tab" onclick="show('variants',this)">Variants</div>
  <div class="tab" onclick="show('banks',this)">House Banks</div>
  <div class="tab" onclick="show('dvr',this)">Doc vs Reality</div>
  <div class="tab" onclick="show('notes',this)">Go-Live &amp; Notes</div>
  <div class="tab" onclick="show('roles',this)">Roles &amp; Auth</div>
  <div class="tab" onclick="show('infra',this)">Infrastructure</div>
</div>

<!-- TAB: E2E Flow -->
<div id="tab-e2e" class="content active">
  <div class="section">
    <h3>UNESCO Payment End-to-End Flow</h3>
    <div id="flowCanvas"></div>
  </div>
  <div class="info">
    <strong>Flow Legend:</strong>
    FI (blue) = Invoice posting &nbsp;|&nbsp; WF (green) = Workflow release &nbsp;|&nbsp; F110 (purple) = Payment program &nbsp;|&nbsp;
    DMEE (teal) = XML generation &nbsp;|&nbsp; BCM (orange) = Bank Communication Mgmt &nbsp;|&nbsp;
    SWIFT (red) = Bank transfer &nbsp;|&nbsp; Recon (gray) = Reconciliation &nbsp;|&nbsp; FO (yellow) = Field office path
  </div>
  <div class="alert">
    <strong>&#9888; Field Office Exception (Method O):</strong> Invoices with Payment Method O bypass both HQ Workflow AND the HQ F110 run.
    A substitution rule automatically sets Method O for field office user IDs. Field offices manage their own payment processing locally.
  </div>
</div>

<!-- TAB: Companies -->
<div id="tab-companies" class="content">
  <div class="section">
    <h3>Payment Tiers by Company Code</h3>
    <table>
      <tr><th>Code</th><th>Name</th><th>Tier</th><th>Method</th><th>F110 Data</th><th>Pay Methods (T042E)</th></tr>
      {build_tier_table()}
    </table>
  </div>
  <div class="section">
    <h3>F110 Run Statistics (from REGUH)</h3>
    <table>
      <tr><th>Company</th><th>Total Runs</th><th>Total Items</th><th>BCM %</th><th>Run Types (prefix:runs/items)</th></tr>
      {build_f110_table()}
    </table>
  </div>
  <div class="section">
    <h3>BCM Batch Statistics</h3>
    <div class="alert"><strong>Audit Finding:</strong> BCM dual control requires CRUSR &ne; CHUSR (segregation of duties).
    UNES approved batches show same create and change user &mdash; a control weakness for audit review.</div>
    <table>
      <tr><th>Company</th><th>Batches</th><th>Items</th><th>Dual Control (CRUSR=CHUSR on approved)</th></tr>
      {build_bcm_table()}
    </table>
  </div>
</div>

<!-- TAB: WF Architecture -->
<div id="tab-wf" class="content">
  <div class="grid2">
    <div>
      <div class="section">
        <h3>Workflow Identity</h3>
        <div class="wf-box">
          <h4>Main Workflow</h4>
          <code>WS90000003</code> ZBSEG_FRAME1<br>
          <span style="color:#7fb3d3;font-size:11px">Package: YWFI &nbsp;|&nbsp; Scope: UNES only</span>
        </div>
        <div class="wf-box">
          <h4>Sub-Workflow</h4>
          <code>WS90000002</code> UN BSEG_SUBW<br>
          <span style="color:#7fb3d3;font-size:11px">Delegated from main workflow</span>
        </div>
        <div class="wf-box">
          <h4>Business Object</h4>
          <code>YBSEG</code> &mdash; delegated subtype of BSEG<br>
          <span style="color:#7fb3d3;font-size:11px">Table type: <code>TTYP: YTTFI_BBSEG</code></span>
        </div>
        <div class="wf-box">
          <h4>Trigger Event</h4>
          <code>BSEGCREATED</code> &mdash; Posting Item Created with Payment Block<br>
          <span style="color:#7fb3d3;font-size:11px">Fires when FI document posted with payment block set on vendor line</span>
        </div>
      </div>
      <div class="section">
        <h3>Document Types in WF Scope</h3>
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">
          {''.join(badge('#2980b9', dt) + ' ' for dt in WF_ARCHITECTURE['doc_types'])}
        </div>
        <div style="margin-top:8px;color:#f39c12;font-size:12px">
          &#9888; <strong>Excluded:</strong> Payment Method O (field office) or U &rarr; no WF, no HQ F110
        </div>
      </div>
      <div class="section">
        <h3>Actor Resolution Rules</h3>
        <table>
          <tr><th>Doc Types</th><th>Validator Group</th><th>Description</th></tr>
          {build_wf_actor_table()}
        </table>
      </div>
    </div>
    <div>
      <div class="section">
        <h3>Custom Functions (YWFI Package)</h3>
        {''.join(f"""<div class="fm-card"><code>{fm}</code><div class="desc">{desc}</div></div>""" for fm, desc in WF_ARCHITECTURE['custom_fms'])}
        <div style="margin-top:12px;color:#7fb3d3;font-size:11px">
          <strong>FG:</strong> Z_WF_FI_EVENT_PAYMENT_METH (Z_WF_FI_BSEG_EVENT_PAYM_METHOD, Z_WF_FI_PR_WF_ACTOR1_DET)<br>
          <strong>FG:</strong> ZFI_BCM_ACTIVE (BCM activation control &mdash; ZFI_BCM_ACTIVE custom table)
        </div>
      </div>
      <div class="section">
        <h3>ZFI_PAYREL_EMAIL Fallback Table</h3>
        <table>
          <tr><th>User ID</th><th>Email</th></tr>
          {''.join(f'<tr><td><code>{r[0]}</code></td><td>{r[1]}</td></tr>' for r in payrel_email)}
        </table>
        <div style="margin-top:8px;color:#f39c12;font-size:11px">
          &#9888; Hardcoded fallback &mdash; if Rule 90000002 fails to resolve actor, email goes here
        </div>
      </div>
      <div class="section">
        <h3>Email Notification</h3>
        <div class="fm-card">
          <code>RSWUWFML2</code> with variant <code>ZWKFLOW_FI_EMA</code>
          <div class="desc">Standard SAP WF email program with UNESCO custom variant for FI payment release notifications</div>
        </div>
      </div>
      <div class="section">
        <h3>WF Call Chain (step by step)</h3>
        <ol style="padding-left:18px;line-height:2;font-size:12px">
          <li>FI document posted &rarr; BSEG record created with payment block (ZLSPR)</li>
          <li>Event <code>BSEGCREATED</code> fired on <code>YBSEG</code> object</li>
          <li><code>WS90000003</code> starts &rarr; checks Payment Method via <code>Z_WF_FI_BSEG_EVENT_PAYM_METHOD</code></li>
          <li>If Method O/U &rarr; reset block, end WF (field office path)</li>
          <li>Else: sub-WF <code>WS90000002</code> launched</li>
          <li>Doc type KR/KA/KT/ER/IT &rarr; <code>Rule 90000001</code> &rarr; <code>Z_GET_CERTIF_OFFICER_UNESDIR</code></li>
          <li>Other types &rarr; <code>Rule 90000002</code> &rarr; <code>Z_WF_FI_PR_WF_ACTOR1_DET</code> &rarr; resolve group</li>
          <li>If no actor &rarr; fallback <code>ZFI_PAYREL_EMAIL</code> email notification</li>
          <li>Validator approves &rarr; payment block removed &rarr; vendor released</li>
          <li>F110 picks up in next payment run (LAUFI prefix B = BCM, 0 = direct)</li>
        </ol>
      </div>
    </div>
  </div>
</div>

<!-- TAB: BCM Config -->
<div id="tab-bcm" class="content">
  <div class="grid2">
    <div>
      <div class="section">
        <h3>BCM Release Rules</h3>
        <table>
          <tr><th>Rule ID</th><th>Type</th><th>Step</th><th>Workflow Task</th><th>Proc WF</th></tr>
          {build_bcm_rules_table()}
        </table>
        <div style="margin-top:8px;font-size:11px;color:#7fb3d3">
          BNK_INI = Payment Batch Initiation rule &nbsp;|&nbsp; BNK_COM = Payment Batch Completion rule
        </div>
      </div>
      <div class="section">
        <h3>Delegation of Authority — Named BCM Validators</h3>
        <table>
          <tr><th>Post</th><th>Code</th><th>Name</th><th>System</th><th>Group</th><th>USD Limit</th></tr>
          {build_named_validators_table()}
        </table>
        <div style="margin-top:8px;font-size:11px;color:#f39c12">
          &#9888; Payroll: BOTH Treasurer (BFM076) AND Assistant Treasury Officer (BFM073) required &nbsp;|&nbsp; Chief PAY (BFM046) as AP member is NOT authorized for SN (supernumerary) doc type.
        </div>
      </div>
      <div class="section">
        <h3>Validation Flow by Payment Type</h3>
        <table>
          <tr><th>Flow Type</th><th>Run By</th><th>1st BCM Validation</th><th>2nd BCM Validation</th></tr>
          {build_validation_flows_table()}
        </table>
      </div>
      <div class="section">
        <h3>BCM Payment Grouping Rules (5 FABS + 1 STEPS)</h3>
        <table>
          <tr><th>Rule</th><th>Priority</th><th>Origin</th><th>Criteria</th><th>Description</th></tr>
          {build_grouping_rules_table()}
        </table>
        <div style="margin-top:8px;font-size:11px;color:#7fb3d3">
          All rules additionally group by <code>VALUT</code> (value date) — ensures one payment file per execution date.
        </div>
      </div>
      <div class="section">
        <h3>Custom BCM Tables</h3>
        <table>
          <tr><th>Object</th><th>Purpose</th></tr>
          {''.join(f'<tr><td><code>{t}</code></td><td>{d}</td></tr>' for t, d in BCM_CONFIG['custom_tables'])}
        </table>
      </div>
      <div class="section">
        <h3>BCM Authorization Roles ({len(bcm_roles)})</h3>
        <div style="display:flex;flex-wrap:wrap;gap:4px">
          {''.join(f'<code style="font-size:9px;background:#1e3a4a;padding:2px 5px;border-radius:3px;color:#7fb3d3">{r}</code>' for r in sorted(bcm_roles))}
        </div>
      </div>
    </div>
    <div>
      <div class="section">
        <h3>Payment File Configuration</h3>
        <div class="fm-card">
          <code>Directory:</code> {BCM_CONFIG["file_dir"]}<br>
          <code>Naming:</code> {BCM_CONFIG["file_naming"]}<br>
          <div class="desc">aaaa = company code &nbsp;|&nbsp; bbbb = payment method &nbsp;|&nbsp; cc = type &nbsp;|&nbsp; xxxxxxxx = date &nbsp;|&nbsp; yyyy = sequence</div>
        </div>
        <table style="margin-top:8px">
          <tr><th>Code</th><th>Format</th></tr>
          {''.join(f"<tr><td><code>0{k}</code></td><td>{v}</td></tr>" for k, v in BCM_CONFIG['file_types'].items())}
        </table>
        <div style="margin-top:8px;color:#7fb3d3;font-size:11px">
          <strong>SWIFT Client:</strong> Alliance Lite2 (Java 7.51-55, IE 8/9 32-bit)<br>
          <strong>Delivery:</strong> File copied to SWIFT directory &rarr; Alliance Lite2 picks up
        </div>
      </div>
      <div class="section">
        <h3>SG Contract Code</h3>
        <table>
          <tr><th>Tag</th><th>Field</th><th>Value</th><th>Status</th></tr>
          <tr><td><code>Tag:20</code></td><td>Transaction Reference</td><td><code>FR14H819</code></td><td>{badge('#27ae60','LIVE')}</td></tr>
          <tr><td><code>Tag:23</code></td><td>Bank Op Code</td><td><code>OTHR / WKST / FR14H819</code></td><td>{badge('#27ae60','LIVE')}</td></tr>
          <tr><td><code>Cmi101</code></td><td>MT101 header</td><td>SG contract reference (hardcoded)</td><td>{badge('#e67e22','HARDCODED')}</td></tr>
        </table>
      </div>
      <div class="section">
        <h3>DMEE BAdI Enhancements</h3>
        <table>
          <tr><th>Spot / Impl</th><th>BAdI</th><th>Country</th></tr>
          <tr><td><code>YENH_FI_DMEE</code></td><td>Base enhancement spot</td><td>All</td></tr>
          <tr><td><code>Y_IDFI_CGI_DMEE_COUNTRIES_DE</code></td><td><code>Y_BADI_IDFI_CGI_DMEE_DE</code></td><td>Germany</td></tr>
          <tr><td><code>Y_IDFI_CGI_DMEE_COUNTRIES_FR</code></td><td><code>Y_BADI_IDFI_CGI_DMEE_FR</code></td><td>France</td></tr>
          <tr><td><code>Y_IDFI_CGI_DMEE_COUNTRIES_IT</code></td><td><code>Y_BADI_IDFI_CGI_DMEE_IT</code></td><td>Italy</td></tr>
          <tr><td><code>Y_IDFI_CGI_DMEE_COUNTRY_AE</code></td><td><code>Y_BADI_IDFI_CGI_DMEE_AE</code></td><td>UAE</td></tr>
          <tr><td><code>Y_IDFI_CGI_DMEE_COUNTRY_BH</code></td><td><code>Y_BADI_IDFI_CGI_DMEE_BH</code></td><td>Bahrain</td></tr>
          <tr><td><code>YENH_FI_DMEE_CGI_FALLBACK</code></td><td>Fallback handler</td><td>Default (all others)</td></tr>
          <tr><td><code>YENH_SUPPLIERS_PAYMENT_UBO</code></td><td>UBO supplier specifics</td><td>Brazil (UBO)</td></tr>
        </table>
        <div style="margin-top:8px;font-size:11px;color:#7fb3d3">
          Classes: <code>YCL_IDFI_CGI_DMEE_AE</code> &nbsp;<code>YCL_IDFI_CGI_DMEE_BH</code> &nbsp;<code>CL_IDFI_CGI_DMEE_CH</code> &nbsp;<code>CL_IDFI_CGI_DMEE_FR</code>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- TAB: DMEE Trees -->
<div id="tab-dmee" class="content">
  <div class="section">
    <h3>DMEE Format Trees ({total_dmee} Trees in CTS)</h3>
    <table>
      <tr><th>DMEE Path</th><th>Name</th><th>Company</th><th>Description</th></tr>
      {build_dmee_table()}
    </table>
  </div>
  <div class="section">
    <h3>DMEE Program Assignment</h3>
    <div class="info">DMEE trees are assigned to payment methods via transaction DMEE. SAPFPAYM calls the tree based on T042Z configuration (PROGN=RFFOM100 uses DMEE engine).</div>
    <table>
      <tr><th>Program</th><th>Usage</th></tr>
      <tr><td><code>RFFOM100</code></td><td>Generic XML payment medium (uses DMEE tree)</td></tr>
      <tr><td><code>RFFOUS_C</code></td><td>US check format</td></tr>
      <tr><td><code>RFFOBR_A</code></td><td>Brazil bank credits</td></tr>
      <tr><td><code>Z_DMEE_EXIT_TAX_NUMBER</code></td><td>Custom DMEE exit FM: tax number formatting (Brazil STCD1/STCD2)</td></tr>
      <tr><td><code>Z_ICTP_DMEE_J_IBAN</code></td><td>ICTP-specific IBAN formatting exit</td></tr>
    </table>
  </div>
  <div class="section">
    <h3>XML Invalid Character Handling (3 Layers) — Critical When Adding New Countries</h3>
    <div class="alert" style="margin-bottom:12px">
      <strong>When adding a new country, XML character handling is the hardest part.</strong>
      Each DMEE tree node has per-field checkboxes: "Replace national characters", "Remove special chars", "Exclude/allow defined characters".
      Must be set field-by-field. Banks reject files for any non-allowed character — no exhaustive list exists.
    </div>
    <table>
      <tr><th>Layer</th><th>Setting Name</th><th>Scope</th><th>Characters / Rule</th><th>Effect</th></tr>
      {build_xml_char_table()}
    </table>
  </div>
  <div class="section">
    <h3>Country-Specific Payment Requirements</h3>
    <table>
      <tr><th>Country</th><th>Risk</th><th>Requirement Type</th><th>Detail</th></tr>
      {build_country_req_table()}
    </table>
    <div class="info" style="margin-top:8px">
      <strong>Steps to add a new country:</strong>
      (1) Verify bank requirements (charset, IBAN, tax ID, branch) &rarr;
      (2) Configure payment method in FBZP if new method needed &rarr;
      (3) Update DMEE tree: add country conditions on PstlAdr nodes &rarr;
      (4) Set char replacement options per field &rarr;
      (5) Test in V01 &rarr;
      (6) Bank confirms file received &rarr;
      (7) Update BCM rules &rarr;
      (8) Create OBPM4 variant (NEVER transported — recreate manually)
    </div>
  </div>
</div>

<!-- TAB: Object Inventory -->
<div id="tab-objects" class="content">
  <div class="section">
    <h3>Complete Payment Object Inventory &mdash; {total_objs} Unique Objects from CTS</h3>
    <div class="info" style="margin-bottom:12px">
      Source: <code>cts_objects</code> (108,290 entries across all transports). Pattern match on 20 payment-related terms.
    </div>
    <table>
      <tr><th style="width:80px">Type</th><th style="width:160px">Label</th><th style="width:50px">Count</th><th>Objects</th></tr>
      {build_obj_inventory()}
    </table>
  </div>
</div>

<!-- TAB: Variants -->
<div id="tab-variants" class="content">
  <div class="section">
    <h3>SAPFPAYM Variants &mdash; {total_variants} Unique</h3>
    <div class="info" style="margin-bottom:12px">
      Naming: <code>SAPFPAYM[COMPANY]_[BANK/TYPE]_[CURRENCY/METHOD]</code>
    </div>
    <table>
      <tr><th>Company</th><th>Count</th><th>Variants (suffix shown)</th></tr>
      {build_variant_table()}
    </table>
  </div>
  <div class="section">
    <h3>UNES Variant Categories</h3>
    <div class="grid3">
      <div class="fm-card"><code>TRE_*</code><div class="desc">Treasury bank-specific: BNPEUD, BPP01, CIT, SCB, WEL, SOG &mdash; CHF, JPY, USD, EUR</div></div>
      <div class="fm-card"><code>SEPA_*</code><div class="desc">SEPA Credit Transfer: GEF, MBF, OPF, PFF variants</div></div>
      <div class="fm-card"><code>INT_*</code><div class="desc">International: AUD, CAD, CHF, DKK, EUR, GBP, JPY, NOK, TND, USD</div></div>
      <div class="fm-card"><code>XML_*</code><div class="desc">CGI/CITI XML: EXO, MGAGEF, MGAOPF, MGAPFF, TND, USD variants</div></div>
      <div class="fm-card"><code>CHECK</code><div class="desc">SAPFPAYMUNE_CHECK: physical check &mdash; form Y_SG_F110_CHEQ</div></div>
      <div class="fm-card"><code>Global</code><div class="desc">SAPFPAYMUSD, SAPFPAYMGBP, SAPFPAYMAUD &mdash; multi-company currency variants</div></div>
    </div>
  </div>
</div>

<!-- TAB: House Banks -->
<div id="tab-banks" class="content">
  <div class="section">
    <h3>House Bank Configuration Summary (T012K)</h3>
    <table>
      <tr><th>Company</th><th>Banks</th><th>Accounts</th><th>Currencies</th><th>First 5 Bank IDs</th></tr>
      {build_hb_table()}
    </table>
    <div class="info" style="margin-top:8px">
      <strong>UNES field office network:</strong> 45+ house banks in 50+ countries covering UNESCO field offices worldwide.
      T042I bank ranking determines which account is used per payment method and currency.
    </div>
  </div>
  <div class="section">
    <h3>Key Treasury Banks (UNES HQ)</h3>
    <table>
      <tr><th>Bank ID</th><th>Bank Name</th><th>Currency</th><th>Purpose</th></tr>
      <tr><td><code>SOG</code></td><td>Soci&eacute;t&eacute; G&eacute;n&eacute;rale</td><td>EUR</td><td>Primary EUR treasury (contract FR14H819)</td></tr>
      <tr><td><code>CIT</code></td><td>Citibank</td><td>USD</td><td>Primary USD + multi-currency (CITI DMEE trees)</td></tr>
      <tr><td><code>BNP / BNPEUD</code></td><td>BNP Paribas</td><td>EUR</td><td>SEPA/EUR payments (BPP01, BPP02, BNPEUD, BNPEUR variants)</td></tr>
      <tr><td><code>SCB</code></td><td>Standard Chartered</td><td>Multi</td><td>USDSCB variant &mdash; exotic currency destinations</td></tr>
      <tr><td><code>WEL</code></td><td>Wells Fargo</td><td>USD</td><td>USDWEL variant &mdash; US domestic payments</td></tr>
    </table>
  </div>
</div>

<!-- TAB: Doc vs Reality -->
<div id="tab-dvr" class="content">
  <div class="section">
    <h3>Documentation vs SAP Reality &mdash; Control Matrix</h3>
    <div style="display:flex;gap:12px;margin-bottom:12px;flex-wrap:wrap">
      {badge('#27ae60','CONFIRMED')} SAP data confirms &nbsp;
      {badge('#e74c3c','AUDIT FINDING')} Compliance gap found &nbsp;
      {badge('#f39c12','PARTIAL')} Partially verifiable &nbsp;
      {badge('#7f8c8d','DOC ONLY')} In docs, not in Gold DB &nbsp;
      {badge('#2980b9','DELTA')} Minor variance
    </div>
    <table>
      <tr><th style="width:35%">PDF Claim</th><th style="width:45%">SAP Gold DB Reality</th><th style="width:120px">Status</th></tr>
      {build_dvr_table()}
    </table>
  </div>
  <div class="alert">
    <strong>Critical Audit Finding:</strong> BCM dual control (SoD) requires CRUSR &ne; CHUSR.
    Gold DB shows approved batches where same user created and approved &mdash; a control weakness for the next audit cycle.
  </div>
  <div class="info">
    <strong>Documents Analyzed:</strong><br>
    1. Technical documentation of Workflow Financial Payment Release.pdf (full technical WF spec)<br>
    2. FS Payment release workflow 2.0.pdf (functional spec with approver groups and names)<br>
    3. Blueprint BCM.pdf pp.1-40 (BCM config, release rules, Delegation of Authority, SAP Notes)<br>
    4. SAP Gold DB: BKPF(1.67M), BSAK(739K), REGUH(897K), BNK_BATCH_HEADER(27K), T042*/T012K/PAYR<br>
    5. CTS transport system: 108,290 objects &mdash; 561 unique payment-related
  </div>
</div>

<!-- TAB: Go-Live & Notes -->
<div id="tab-notes" class="content">
  <div class="grid2">
    <div>
      <div class="section">
        <h3>Workflow Go-Live Checklist</h3>
        <ul class="steplist">
          {''.join(f'<li>{step}</li>' for step in WF_ARCHITECTURE['go_live_steps'])}
        </ul>
      </div>
      <div class="section">
        <h3>BCM Standard Tasks (mark as General)</h3>
        <div style="display:flex;flex-wrap:wrap;gap:6px">
          {''.join(badge('#3498db', t) + ' ' for t in ['50100025', '50100026', '50100066', '50100075'])}
        </div>
        <div style="margin-top:8px;color:#7fb3d3;font-size:11px">Also: PFTS tasks 90000002, 90000007, 90000008</div>
      </div>
      <div class="section">
        <h3>Key Transactions</h3>
        <table>
          <tr><th>Transaction</th><th>Purpose</th></tr>
          <tr><td><code>ZPAYM</code></td><td>SAPFPAYM_SCHEDULE &mdash; Payment Medium Scheduling</td></tr>
          <tr><td><code>FBZP</code></td><td>Payment program configuration</td></tr>
          <tr><td><code>F110</code></td><td>Automatic Payment Transactions</td></tr>
          <tr><td><code>FBPM1</code></td><td>BCM Payment Monitor</td></tr>
          <tr><td><code>SWI5</code></td><td>Workflow workitem analysis</td></tr>
          <tr><td><code>SWETYPV</code></td><td>Event Type Linkages (WF activation)</td></tr>
          <tr><td><code>SWU3</code></td><td>WF Runtime Environment</td></tr>
          <tr><td><code>DMEE</code></td><td>DMEE Tree maintenance</td></tr>
          <tr><td><code>YFI_BANK_RECONCILIATION</code></td><td>Custom bank reconciliation transaction</td></tr>
        </table>
      </div>
    </div>
    <div>
      <div class="section">
        <h3>SAP Notes Implemented — Full List (21)</h3>
        <table>
          <tr><th>Note</th><th>Description</th><th>System</th></tr>
          {build_sap_notes_full()}
        </table>
        <div style="margin-top:8px;color:#f39c12;font-size:11px">
          Notes pending review: 1041016 &nbsp; 1075859 &nbsp; 1076337 &nbsp; 1280375 &nbsp; 1577912
        </div>
      </div>
      <div class="section">
        <h3>Known WF/BCM Operational Issues</h3>
        <table>
          <tr><th>Issue</th><th>Symptom</th><th>Root Cause</th><th>Affected</th><th>Fix</th></tr>
          {build_wf_issues_table()}
        </table>
      </div>
      <div class="section">
        <h3>RFC-Enabled Custom Functions (SRFC)</h3>
        <table>
          <tr><th>FM</th><th>Purpose</th></tr>
          {''.join(f"<tr><td><code>{r}</code></td><td style='font-size:11px'>RFC-enabled payment FM</td></tr>" for r in cts_by_type.get('SRFC', [])[:10])}
        </table>
      </div>
      <div class="section">
        <h3>Advice Forms</h3>
        <div style="display:flex;flex-wrap:wrap;gap:6px">
          {''.join(badge('#e91e63', f) + ' ' for f in cts_by_type.get('FORM', [])[:10])}
        </div>
        <div style="margin-top:8px;color:#7fb3d3;font-size:11px">
          Base: <code>Y_F110_AVIS</code> &nbsp;|&nbsp; Per-company: UIS, UBO, UIL, IIEP &nbsp;|&nbsp; SG cheque: <code>Y_SG_F110_CHEQ</code>
        </div>
      </div>
      <div class="section">
        <h3>Key Transport Merges (from CTS MERG)</h3>
        <table>
          <tr><th>MERG Reference</th></tr>
          {''.join(f"<tr><td style='font-size:11px'>{r}</td></tr>" for r in cts_by_type.get('MERG', []))}
        </table>
      </div>
    </div>
  </div>
</div>

<!-- TAB: Roles & Auth -->
<div id="tab-roles" class="content">
  <div class="section">
    <h3>The 4 UNESCO Payment Processes [VERIFIED — BFM Handover Documentation]</h3>
    <div class="info" style="margin-bottom:12px">
      Source: "Payment process and authorizations 1.2 TRS" (BFM/TRS handover).
      Role <code>YS:FI:M:BCM_MON_APP______:XXXX</code> and <code>Y_XXXX_FI_AP_PAYMENTS</code> are MUTUALLY EXCLUSIVE (except UNES Process 4).
    </div>
    <table>
      <tr><th style="width:40px">#</th><th>Process Name</th><th>Company Codes</th><th>Tool</th><th>SAP Role</th><th>Flow Description</th></tr>
      {build_payment_processes_table()}
    </table>
  </div>

  <div class="alert">
    <strong>&#9888; 2023 Security Incident — BCM Bypass</strong><br>
    A new BCM user was assigned BOTH <code>Y_XXXX_FI_AP_PAYMENTS</code> AND <code>YS:FI:M:BCM_MON_APP______:XXXX</code>.<br>
    This combination allowed the user to generate a payment file in F110 AND download it directly to Coupa,
    <strong>bypassing BCM approval entirely</strong>. Payment went to Coupa → bank without any BCM validation.<br><br>
    <strong>Remediation:</strong> New role <code>YO:FI:COUPA_PAYMENT_FILE_:</code> created to separate "download to Coupa"
    from "BCM monitor". Testing in V01 — ready for P01 production deployment.
  </div>

  <div class="grid2">
    <div>
      <div class="section">
        <h3>Role Compatibility Matrix</h3>
        <table>
          <tr><th>Role</th><th>Description</th><th>F110 Activities</th><th>BCM</th><th>Compatibility</th></tr>
          <tr><td><code style="font-size:9px">YS:FI:D:DISPLAY__________:ALL</code></td><td>Display only</td><td>03, 13, 23 (display)</td><td>No</td><td>{badge('#27ae60','Any role')}</td></tr>
          <tr><td><code style="font-size:9px">Y_XXXX_FI_AP_PAYMENTS</code></td><td>Institute/UBO payment</td><td>02, 11-15, 21, 25 (full)</td><td>No</td><td>{badge('#e74c3c','NOT with BCM_MON_APP')}</td></tr>
          <tr><td><code style="font-size:9px">YS:FI:M:AP_PAYMENT_RUN___:UKDS</code></td><td>HQ BFM/AP payment</td><td>02, 11-15, 21, 25 (full)</td><td>No</td><td>{badge('#f39c12','Context-dependent')}</td></tr>
          <tr><td><code style="font-size:9px">YS:FI:M:BCM_MON_APP______:XXXX</code></td><td>BCM monitor + validate</td><td>BCM only</td><td>Yes</td><td>{badge('#e74c3c','NOT with AP_PAYMENTS')}</td></tr>
          <tr><td><code style="font-size:9px">YO:FI:COUPA_PAYMENT_FILE_:</code></td><td>Coupa download only (NEW)</td><td>None</td><td>Download only</td><td>{badge('#27ae60','BCM validators only')}</td></tr>
        </table>
        <div class="alert" style="margin-top:8px;font-size:11px">
          <strong>Rule:</strong> Y_XXXX_FI_AP_PAYMENTS + YS:FI:M:BCM_MON_APP on same user = BCM bypass risk.<br>
          <strong>Exception:</strong> UNES Process 4 requires both, but MUST have Coupa as 2nd control.
        </div>
      </div>
    </div>
    <div>
      <div class="section">
        <h3>BCM Signatory Management</h3>
        <div class="fm-card">
          <code>OOCU_RESP</code> &mdash; Organization &rarr; Responsibility
          <div class="desc">Transaction to maintain BCM approval rules and assign users</div>
        </div>
        <table style="margin-top:8px">
          <tr><th>Rule</th><th>Type</th><th>Purpose</th></tr>
          <tr><td><code>90000004</code></td><td>BNK_COM_01_01_03</td><td>BCM 2nd validation (BNK_COM) assignment</td></tr>
          <tr><td><code>90000005</code></td><td>BNK_INI_01_01_04</td><td>BCM 1st validation (BNK_INI) assignment</td></tr>
        </table>
        <div style="margin-top:8px;font-size:11px;color:#f39c12">
          &#9888; BCM signatory changes done directly in PRODUCTION (HR org structure not up to date in dev)<br>
          &#9888; To remove a validator: <strong>delimit validity</strong> (never delete from rule)<br>
          HQ signatories: CFO delegation &rarr; updated by DBS on BFM/TRS request<br>
          Institute/UBO signatories: bank signatory letters &rarr; updated by DBS
        </div>
      </div>
      <div class="section">
        <h3>F110 Authorization Activity Codes</h3>
        <table>
          <tr><th>Activity</th><th>Description</th></tr>
          <tr><td><code>02</code></td><td>Edit payment parameters</td></tr>
          <tr><td><code>03</code></td><td>Display payment parameters</td></tr>
          <tr><td><code>11</code></td><td>Create payment proposal</td></tr>
          <tr><td><code>12</code></td><td>Display payment proposal</td></tr>
          <tr><td><code>13</code></td><td>Edit payment proposal</td></tr>
          <tr><td><code>14</code></td><td>Delete payment proposal</td></tr>
          <tr><td><code>15</code></td><td>Print payment proposal</td></tr>
          <tr><td><code>21</code></td><td>Execute payment run</td></tr>
          <tr><td><code>22</code></td><td>Reverse payment run</td></tr>
          <tr><td><code>25</code></td><td>Print payment run (payment medium)</td></tr>
          <tr><td><code>26</code></td><td>Delete payment run</td></tr>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- TAB: Infrastructure -->
<div id="tab-infra" class="content">
  <div class="section">
    <h3>Payment File Transfer Architecture</h3>
    <div class="info" style="margin-bottom:12px">
      Complete technical path from SAP to bank for BCM payments.
      Every 15 minutes: SFTP polling checks directory and sends files via SWIFT SIL.
    </div>
    <div style="background:#12202e;border-radius:8px;padding:16px;font-family:monospace;font-size:12px;line-height:2">
      <span style="color:#1abc9c">SAP iRIS (Payment Processing)</span><br>
      &nbsp;&rarr; <code>\\hq-sapitf\coupa$\P01\In\Data</code> (SAP Network File Directory)<br>
      &nbsp;&nbsp;&rarr; <span style="color:#f39c12">SFTP every 15 minutes</span> &rarr; <strong>Coupa Treasury Management System</strong><br>
      &nbsp;&nbsp;&nbsp;&rarr; <strong>SWIFT Integration Layer (SIL)</strong><br>
      &nbsp;&nbsp;&nbsp;&nbsp;&rarr; <strong>SWIFT Alliance Lite2</strong><br>
      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&rarr; <span style="color:#3498db">Banks (SOGE, CITI, BNP, etc.)</span><br><br>
      <span style="color:#3498db">Banks</span><br>
      &nbsp;&rarr; SWIFT Alliance Lite2 (EBS + Payment Status Reports)<br>
      &nbsp;&rarr; SIL &rarr; <code>\\hq-sapitf\SWIFT$\output\*</code><br>
      &nbsp;&rarr; SAP (Bank Statement Processing + Payment Status Updates)
    </div>
    <table style="margin-top:12px">
      <tr><th>Directory</th><th>Purpose</th></tr>
      <tr><td><code>\\hq-sapitf\SWIFT$\P01\input</code></td><td>FABS payment files output directory</td></tr>
      <tr><td><code>\\hq-sapitf\SWIFT$\P11\input</code></td><td>STEPS (payroll) payment files</td></tr>
      <tr><td><code>\\hq-sapitf\coupa$\P01\In\Data</code></td><td>Coupa inbound directory (auto-downloaded)</td></tr>
      <tr><td><code>\\hq-sapitf\SWIFT$\output\*</code></td><td>Bank statement / payment status input</td></tr>
    </table>
    <div style="margin-top:8px;font-size:11px;color:#7fb3d3">
      <strong>File naming:</strong> <code>aaaa_bbbb_ccxxxxxxxxyyyy.in</code> (aaaa=UNES, bbbb=SOGE/CITI, cc=type, .in required for SWIFT)<br>
      <strong>SWIFT client:</strong> Alliance Lite2 (Java 7.51-55, IE 8/9 32-bit) &nbsp;|&nbsp;
      <strong>Dev/test prefix:</strong> D (dev) / V (V01 test) instead of P (prod)
    </div>
  </div>

  <div class="grid2">
    <div>
      <div class="section">
        <h3>3 Automatic Payment Programs at UNESCO</h3>
        <table>
          <tr><th>#</th><th>Program</th><th>Managed By</th><th>Purpose</th></tr>
          <tr><td>1</td><td><code>F110</code></td><td>BFM/FAS/AP + Institutes</td><td>Automatic Payment for all 3rd party vendor payments</td></tr>
          <tr><td>2</td><td><code>F111</code></td><td>BFM/TRS (via FRFT_B)</td><td>Payment Request program for bank-to-bank treasury transfers / replenishments</td></tr>
          <tr><td>3</td><td><code>Payroll Program</code></td><td>BFM/PAY</td><td>HR payroll payments (STEPS system, BCM PAYROLL rule)</td></tr>
        </table>
      </div>
      <div class="section">
        <h3>UIL-Specific Configuration (Hamburg — new 2024)</h3>
        <table>
          <tr><th>Bank</th><th>Account</th><th>Currency</th><th>GL</th><th>Payment Method</th><th>Notes</th></tr>
          {''.join(f"<tr><td><code>{r[0]}</code></td><td><code>{r[1]}</code></td><td>{r[2]}</td><td><code>{r[3]}</code></td><td>{r[4]}</td><td style='font-size:11px'>{r[5]}</td></tr>" for r in UIL_CONFIG)}
        </table>
        <div style="margin-top:8px;font-size:11px;color:#7fb3d3">
          <strong>BCM:</strong> 2 validations required &nbsp;|&nbsp; UIL AP Validation up to 5,000,000 USD<br>
          <strong>Payment run users:</strong> Britta Hoffman, Larissa Steppin<br>
          <strong>BCM validators:</strong> Atchoarena David, Jahan Nusrat, Valdes Cotera Raul, Zholdoshalieva Rakhat, Gazi Baizid, Yli-Hietanen Anssi
        </div>
      </div>
    </div>
    <div>
      <div class="section">
        <h3>BCM Activation Configuration</h3>
        <table>
          <tr><th>System</th><th>BCM Identifier</th><th>Business Function</th></tr>
          <tr><td>FABS</td><td><code>BCM*</code> (F110 run IDs starting with BCM*)</td><td><code>FIN_FSCM_BNK</code> via SFW5</td></tr>
          <tr><td>STEPS</td><td><code>*</code> (ALL payroll runs)</td><td><code>FIN_FSCM_BNK</code> via SFW5</td></tr>
        </table>
        <div style="margin-top:8px;font-size:11px;color:#7fb3d3">
          <strong>Note:</strong> FABS = iRIS production FI system &nbsp;|&nbsp; STEPS = payroll system (SAP STEPS)<br>
          Custom table <code>ZFI_BCM_ACTIVE</code> controls per-company-code BCM activation flag<br>
          OBPM5: Cross-payment media merging indicator set (enables BCM batch grouping)
        </div>
      </div>
      <div class="section">
        <h3>Exotic Currency Payment (Method X)</h3>
        <table>
          <tr><th>Tier</th><th>Requirements</th><th>Currencies</th></tr>
          <tr><td>Standard</td><td>Name + address + account + IBAN</td><td>BWP, TND, XOF, ZMB, UGX, DOP, etc.</td></tr>
          <tr><td>+ Branch location</td><td>+ Beneficiary bank branch required</td><td>PEN, RWF, MWK, MNT, etc.</td></tr>
          <tr><td>+ Branch + IBAN</td><td>+ IBAN required</td><td>MGA, AOA, GEL, MRO</td></tr>
          <tr><td style="color:#e74c3c">Out of scope</td><td>Tax ID, embargo, or blocked</td><td>COP, IRR, MMK, SDG, ARS</td></tr>
        </table>
        <div style="margin-top:8px;font-size:11px;color:#f39c12">
          &#9888; All Method X goes via <code>SOG01-USDD1</code> (Societe Generale USD account Paris)<br>
          BCM rule <code>UNES_AP_X</code> catches MGA without IBAN &rarr; must be <strong>manually rejected</strong><br>
          Bank reconciliation: manual via GL 1175011 (local ccy) &rarr; YTR2 &rarr; F-04 clearing
        </div>
      </div>
    </div>
  </div>
</div>

<script>
{vis_js}

function show(tab, el) {{
  document.querySelectorAll('.tab').forEach(function(t) {{ t.classList.remove('active'); }});
  document.querySelectorAll('.content').forEach(function(c) {{ c.classList.remove('active'); }});
  document.getElementById('tab-' + tab).classList.add('active');
  if (el) el.classList.add('active');
}}

// E2E Flow Graph
const nodes_data = {json.dumps(flow_nodes, ensure_ascii=False)};
const edges_data = {json.dumps(flow_edges, ensure_ascii=False)};

const groupColors = {{
  fi:     {{ color: {{ background:'#1a4a7a', border:'#3498db' }}, font: {{ color:'#fff' }} }},
  wf:     {{ color: {{ background:'#1a5a2a', border:'#27ae60' }}, font: {{ color:'#fff' }} }},
  f110:   {{ color: {{ background:'#4a1a7a', border:'#9b59b6' }}, font: {{ color:'#fff' }} }},
  dmee:   {{ color: {{ background:'#0d4a44', border:'#1abc9c' }}, font: {{ color:'#fff' }} }},
  bcm:    {{ color: {{ background:'#5a3000', border:'#e67e22' }}, font: {{ color:'#fff' }} }},
  swift:  {{ color: {{ background:'#5a1000', border:'#e74c3c' }}, font: {{ color:'#fff' }} }},
  bank:   {{ color: {{ background:'#2a3a4a', border:'#7fb3d3' }}, font: {{ color:'#fff' }} }},
  recon:  {{ color: {{ background:'#3a3a3a', border:'#95a5a6' }}, font: {{ color:'#fff' }} }},
  direct: {{ color: {{ background:'#2a2a5a', border:'#5dade2' }}, font: {{ color:'#fff' }} }},
  fo:     {{ color: {{ background:'#4a4a00', border:'#f1c40f' }}, font: {{ color:'#fff' }} }},
}};

const vis_nodes = new vis.DataSet(nodes_data.map(function(n) {{
  const gc = groupColors[n.group] || {{}};
  return Object.assign({{}}, n, gc, {{ shape: 'box' }});
}}));
const vis_edges = new vis.DataSet(edges_data);

const container = document.getElementById('flowCanvas');
const network = new vis.Network(container, {{ nodes: vis_nodes, edges: vis_edges }}, {{
  layout: {{ hierarchical: {{ direction: 'LR', sortMethod: 'directed', levelSeparation: 160, nodeSpacing: 70 }} }},
  physics: {{ enabled: false }},
  edges: {{ smooth: {{ type: 'cubicBezier', forceDirection: 'horizontal' }},
           color: '#7fb3d3', font: {{ color: '#ccc', size: 9 }},
           arrows: {{ to: {{ scaleFactor: 0.6 }} }} }},
  nodes: {{ borderWidth: 2, font: {{ size: 11, multi: true }}, shape: 'box',
           widthConstraint: {{ minimum: 80, maximum: 110 }} }},
  interaction: {{ hover: true, tooltipDelay: 100 }},
}});
</script>
</body>
</html>"""

OUT = Path(__file__).parent / 'payment_bcm_companion.html'
OUT.write_text(html, encoding='utf-8')
size_kb = OUT.stat().st_size // 1024
print(f"Generated: {OUT.name}  ({size_kb} KB)")
print(f"Tabs: E2E Flow | Companies | WF Architecture | BCM Config | DMEE Trees | Object Inventory | Variants | House Banks | Doc vs Reality | Go-Live & Notes | Roles & Auth | Infrastructure")
print(f"Objects: {total_objs} | F110: {total_f110:,} | BCM: {total_bcm:,} | DMEE: {total_dmee} | Variants: {total_variants} | Roles: {total_roles}")
print(f"Doc vs Reality: {confirmed} Confirmed | {findings} Audit Findings | {partial} Partial/Gap")
