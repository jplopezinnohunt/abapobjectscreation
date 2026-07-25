"""Patch INC-000006906 record in brain_v2/incidents/incidents.json
with the 2026-04-20 pivot findings. Provisional only \u2014 no rebuild.
"""
import json
import os

path = os.path.join(
    os.path.dirname(__file__), '..', '..',
    'brain_v2', 'incidents', 'incidents.json'
)
path = os.path.abspath(path)

with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

idx = None
for i, inc in enumerate(data):
    if inc.get('id') == 'INC-000006906':
        idx = i
        break
if idx is None:
    raise SystemExit('INC-000006906 not found')

inc = data[idx]

inc['status'] = 'PROVISIONAL_ROOT_CAUSE_PIVOTED_2026-04-20'
inc['pivoted'] = True
inc['pivot_date'] = '2026-04-20'
inc['pivot_session'] = 57
inc['pivot_source'] = (
    'user chat: Pivot 1 not-posting-but-dump; '
    'Pivot 2 candidate=YFI_BANK_RECONCILIATION; '
    'Pivot 3 pull J_DAVANE logs 2026-04-13..17'
)

inc['transactions'] = [
    'YFI_BANK1 (custom TCODE) -> YFI_BANK_RECONCILIATION '
    '(main report) -> YCL_FI_BANK_RECONCILIATION_BL (backing class)'
]
inc['transactions_secondary_hypothesis'] = [
    'ZCASHFODET / ZCASH (Report Painter, preserved as alternate)',
    'FBL3N (preserved as alternate)'
]

inc['related_programs'] = [
    'YFI_BANK_RECONCILIATION',
    'YFI_BANK_RECONCILIATION_DATA',
    'YFI_BANK_RECONCILIATION_SEL',
    'YCL_FI_BANK_RECONCILIATION_BL'
]
inc['related_tcodes'] = ['YFI_BANK1']
inc['related_structures'] = [
    'YSFI_BANK_RECONCILIATION',
    'YSFI_BANK_RECONCILIATION_DASH',
    'YSFI_BANK_RECONCILIATION_DET',
    'YTTFI_BANK_RECONCILIATION_DASH',
    'YTTFI_BANK_RECONCILIATION_DET'
]
inc['related_transports_authoring'] = [
    {'trkorr': 'D01K9B0AJD', 'date': '2023-04-14', 'author': 'N_MENARD', 'role': 'initial skeleton'},
    {'trkorr': 'D01K9B0AIH', 'date': '2023-04-20', 'author': 'N_MENARD', 'role': 'main creation transport'},
    {'trkorr': 'D01K9B0AMV', 'date': '2023-05-23', 'author': 'N_MENARD', 'role': 'method additions + CUAD screen'},
    {'trkorr': 'D01K9B0AN7', 'date': '2023-05-25', 'author': 'N_MENARD', 'role': 'GET_HKONT_NAME tweaks'},
    {'trkorr': 'D01K9B0AN9', 'date': '2023-05-25', 'author': 'N_MENARD', 'role': 'GET_CLOPE + PREPARE_DETAILED_DATA + SET_COLUMNS'},
    {'trkorr': 'D01K9B0AOB', 'date': '2023-06-12', 'author': 'N_MENARD', 'role': 'late-stage fixes'},
    {'trkorr': 'D01K9B0AQO', 'date': '2023-06-20', 'author': 'N_MENARD', 'role': ''},
    {'trkorr': 'D01K9B0ARO', 'date': '2023-06-21', 'author': 'N_MENARD', 'role': 'minor'},
    {'trkorr': 'D01K9B0ASU', 'date': '2023-06-29', 'author': 'N_MENARD', 'role': 'final v1'},
    {'trkorr': 'D01K9B0AT0', 'date': '2023-06-29', 'author': 'N_MENARD', 'role': 'final v1 parallel'}
]
inc['related_transports_code_frozen_since'] = '2023-06-29'

inc['root_cause_summary_provisional'] = (
    'PIVOTED 2026-04-20: Josina runs YFI_BANK1 (YFI_BANK_RECONCILIATION) and hits '
    'an ABAP short dump at the ALV export ("download") step. The program plus class '
    'YCL_FI_BANK_RECONCILIATION_BL were built 2023-04 through 2023-06 by external '
    'consultant N_MENARD in 10 transports and have had ZERO changes since 2023-06-29 '
    '-- so this is a latent data-driven defect, not a regression. '
    'Rank-1 predicted dump: COMPUTE_INT_ZERODIVIDE inside GET_DELAY/aging calc when '
    'FEBKO has no rows for the selected period/bank (ECO09/MZN01 has 0 FEBKO rows ever; '
    'BST01/MZM01 stopped 2025-04-17). '
    'Rank-2: TSV_TNEW_PAGE_ALLOC_FAILED during PREPARE_DETAILED_DATA against 686 '
    'uncleared BSIS items on GL 0001022424. '
    'Rank-3: CONVT_NO_NUMBER if WAERS=MZM (deprecated) on BST02 is touched. '
    'Rank-4: OBJECTS_OBJREF_NOT_ASSIGNED in HANDLE_USER_COMMAND on empty ALV. '
    'SECONDARY (demoted): UBA01 / YBANK_ACCOUNTS_FO_OTH set transport collateral. '
    'REQUIRES: (a) source extraction of the 4 objects via sap_adt_api; '
    '(b) live ST22 dump read for J_DAVANE 2026-04-13..17.'
)

inc['next_validation_step'] = [
    'PRIMARY: Live RFC read SNAP+SNAPT (ST22) filtered UNAME=J_DAVANE DATUM BETWEEN 20260413 AND 20260417 -- one dump = full stack + file:line + runtime error code',
    'REQUIRED: sap_adt_api extract of YFI_BANK_RECONCILIATION, YFI_BANK_RECONCILIATION_DATA, YFI_BANK_RECONCILIATION_SEL, YCL_FI_BANK_RECONCILIATION_BL (all 10 methods) into extracted_code/FI/BANK_RECONCILIATION/ -- BLOCKS file.abap:line citation',
    'SECONDARY: Live BKPF pull USNAM=J_DAVANE CPUDT 20260401..20260420 to confirm April activity (Gold DB stops 2026-03-16)',
    'SECONDARY: Live FEBKO pull WAERS=MZN EDATE 20260401..20260420 to confirm statement feed status (Gold DB stops 2025-04-17 for MZ banks)',
    'SECONDARY: SM20/STAD audit of YFI_BANK1 executions by J_DAVANE',
    'USER ASK: only 2 questions -- (1) exact date+time of dump, (2) ST22 dump ticket number'
]

inc['gold_db_freshness_gap'] = {
    'incident_window': '2026-04-13 to 2026-04-17',
    'bkpf_cpudt_max': '2026-03-16',
    'tbtco_strtdate_max': '2026-03-18',
    'febko_edate_max': '2026-03-31',
    'febko_waers_mzn_max': '2025-04-18',
    'cdhdr_udate_max': '2026-03-16',
    'conclusion': 'Entire incident window is post-Gold-DB-extract. No TIER_1 Gold DB evidence possible for 2026-04-13..17. Live RFC required.'
}

inc['blind_spots_identified'] = [
    'YFI_BANK_RECONCILIATION source -- object exists in Gold DB cts_objects but SOURCE NOT in extracted_code (force-include required)',
    'YCL_FI_BANK_RECONCILIATION_BL source -- same (force-include)',
    'SNAP/SNAPT (ST22 dumps) not extracted to Gold DB',
    'SM20 / RSAU_BUF_DATA audit log not extracted to Gold DB',
    'STAD workload statistics not extracted to Gold DB',
    'REPOSRC / TRDIR / REPOTEXT source code tables not in Gold DB'
]

inc['data_pathology_observed'] = {
    'gl_0001022424_bst01_mzn': {
        'bsis_open_items': 686,
        'bsas_cleared_items': 0,
        'budat_range': '2024-01-03..2025-04-17',
        'notes': 'feed stopped 1yr ago; 0 cleared'
    },
    'gl_0001094424_eco09_mzn': {
        'febko_rows_ever': 0,
        'notes': 'ECO09 has NO MT940 feed at all'
    },
    'bst02_mzm01': {
        'waers': 'MZM (deprecated 2006 ISO code)',
        'gl': '0001022814',
        'notes': 'dormant but present'
    },
    'gl_0001065424_uba01_mzn': {
        'postings': 0,
        'notes': 'new 2026-04-08, zero activity'
    }
}

inc['j_davane_profile_pre_pivot_reconfirmed'] = {
    'bkpf_total_docs': 1364,
    'bkpf_bukrs_waers_split': {'UNES/MZN': 1016, 'UNES/USD': 348},
    'cdhdr_total_events': 1727,
    'cdhdr_top_tcode': 'FBL3N (1449 -- her #1 transaction)',
    'bkpf_top_tcode': 'FBZ2 (560 payments)',
    'tbtco_background_jobs': 0,
    'febko_statement_entries': 0,
    'last_bkpf_posting': '2026-03-12 14:37 MIRO 5100006390 MZN BKTXT=MAP INV # IN070585',
    'interpretation': (
        'Dialog-mode AP/AR accountant for UNES/MZN. Profile consistent with running '
        'YFI_BANK1 in dialog and exporting to Excel. Does NOT create BKPF/CDHDR when '
        'running a read-only report -- so Gold-DB "no YFI_BANK1 trace" is expected, '
        'not disconfirming.'
    )
}

# Preserve analysis_doc pointer (already correct)
# Preserve intake_json pointer (already correct)

# Write back
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('INC-000006906 updated. Status:', inc['status'])
print('Related programs:', inc['related_programs'])
print('Next validation step (first):', inc['next_validation_step'][0])
