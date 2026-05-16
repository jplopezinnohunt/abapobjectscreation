"""Add brain annotations for objects discovered/refined in session #074."""
import json, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

P = 'brain_v2/annotations/annotations.json'
d = json.load(open(P, encoding='utf-8'))
now = datetime.now().isoformat()
SESSION = '#074'


def add(obj_key, ann):
    ann.setdefault('timestamp', now)
    ann.setdefault('session', SESSION)
    rec = d.setdefault(obj_key, {'annotations': [], 'first_seen': now, 'last_updated': now})
    rec['annotations'].append(ann)
    rec['last_updated'] = now


add('DMEE_TREE_NODE', {
    'tag': 'TREE_TOPOLOGY_TABLE',
    'finding': "Holds the per-format tree topology — NODE_ID, TECH_NAME, PARENT_ID, MP_EXIT_FUNC, MP_SC_TAB/FLD/OFFSET/LENGTH. The MP_EXIT_FUNC column names the FM that overrides the leaf value at runtime; when blank, MP_SC_TAB/FLD provide direct binding to FPAYH/FPAYHX/FPAYP buffers. Address-leaves can also have neither (empty) when populated by Citi PMW runtime or by another evaluation path.",
    'impact': "Source of truth for every per-format address-resolution analysis. RFC_READ_TABLE quirk: DATA_BUFFER_EXCEEDED if too many cols requested at once; OPTION_NOT_VALID for IN clauses or inline AND-joined conditions — must use 'TREE_ID =' + ' AND TECH_NAME =' in separate OPTIONS rows.",
    'field': 'MP_EXIT_FUNC / MP_SC_TAB / MP_SC_FLD',
    'related': ['DMEE_TREE_HEAD', 'DMEE_TREE_COND', 'Y_FI_DMEE_ADR', 'FI_CGI_DMEE_EXIT_W_BADI']
})

add('FI_PAYMEDIUM_DMEE_CGI_05', {
    'tag': 'SAP_STANDARD_EVENT05',
    'finding': "SAP standard Event 05 FM (generic CGI). Populates FPAYHX-REF01[0..60]=street, REF01[60..80]=building, REF01[80..90]=post_code1, REF01[90..100]=region, REF01[100..110]=house_num1; REF02 = Cdtr equivalents; REF06[0..40]=city. The address source is ADRC of the LIFNR — ALWAYS blind read, no KTOKK awareness.",
    'impact': "Root of the structured-address bug surface system-wide. Every UNESCO DMEE tree that binds to FPAYHX-REF01/Z* without an override inherits the dept-code-for-staff defect. Fix paths: (a) replace the binding with Y_FI_DMEE_ADR exit FM, (b) extend a Z BAdI implementation that runs before SAP std and overrides REF buffers for staff LIFNRs.",
    'field': 'FPAYHX-REF01/REF02',
    'related': ['FPAYHX-REF01', 'ADRC', 'Y_FI_DMEE_ADR', 'TFPM042FB']
})

add('FI_CGI_DMEE_EXIT_W_BADI', {
    'tag': 'SAP_BADI_DISPATCHER',
    'finding': "SAP standard BAdI exit FM that dispatches per tag-path to UNESCO country-class hierarchy (YCL_IDFI_CGI_DMEE_FR/DE/IT/GB/FALLBACK). Wired into 794 of 1,975 nodes across the 4 main UNESCO formats (40.2% per claim 69). For address leaves, dispatcher calls YCL_IDFI_CGI_DMEE_FALLBACK::GET_CREDIT which only handles <Cdtr><Nm> overflow concatenation — does NOT override address from PA0006.",
    'impact': "Critical insight: just because a leaf has MP_EXIT_FUNC=FI_CGI_DMEE_EXIT_W_BADI does NOT mean address is overridden. The BAdI dispatcher passes through to country-class GET_VALUE which today returns SY-SUBRC=0 with c_value unchanged for address tags. Net effect: same as direct FPAYHX-REF01 binding (= ADRC blind).",
    'field': '*',
    'related': ['YCL_IDFI_CGI_DMEE_FALLBACK', 'YCL_IDFI_CGI_DMEE_FR', 'YCL_IDFI_CGI_DMEE_UTIL']
})

add('YCL_IDFI_CGI_DMEE_FALLBACK', {
    'tag': 'BADI_FALLBACK_IMPL',
    'finding': "Nicolas's BAdI implementation class for non-country-specific tag overrides. GET_CREDIT method (CM001) only handles <Cdtr><Nm> overflow >35 chars by concatenating excess into <StrtNm>. CM002 GET_DEBIT method exists but minimal. Class hierarchy: FALLBACK is the default; FR/DE/IT/GB country classes override per-country before falling through.",
    'impact': "Read-only per rule feedback_only_modify_our_own_code. Extension of this class for PA0006-first detection would require Nicolas's authorization. UNESCO-controlled alternative: build Z BAdI impl with higher priority, or wire Y_FI_DMEE_ADR into the trees directly.",
    'incident': 'V001-SEPA-Cdtr-StructAddr',
    'field': 'GET_CREDIT',
    'related': ['FI_CGI_DMEE_EXIT_W_BADI', 'Y_FI_DMEE_ADR', 'feedback_only_modify_our_own_code']
})

add('YCL_IDFI_CGI_DMEE_UTIL', {
    'tag': 'PPC_FRAMEWORK',
    'finding': "Implements the PPC framework — GET_TAG_VALUE_FROM_CUSTO method resolves DMEE tag value at runtime by reading YTFI_PPC_TAG (tag → PPC_CODE mapping per country) + YTFI_PPC_STRUC (sub-segment composition) + T015L (lookup values). Built by N_MENARD 2024-09-06. Dispatched from FR country class (YCL_IDFI_CGI_DMEE_FR::CM002).",
    'impact': "Framework is DORMANT for UNESCO main flows: YTFI_PPC_TAG has 11 rows covering only AE/BH/CN/ID/IN/JO/MA/MY/PH; ZERO rows for FR/DE/IT/GB/US/BR (the countries of UNESCO's main paying banks). Configured tags are narrative (<InstrInf>, <Ustrd>) — NOT address tags. PPC cannot resolve the staff-address bug without (a) adding FR rows AND (b) extending PPC_CODE domain to support PA0006 lookup.",
    'field': 'GET_TAG_VALUE_FROM_CUSTO',
    'related': ['YTFI_PPC_TAG', 'YTFI_PPC_STRUC', 'T015L', 'YCL_IDFI_CGI_DMEE_FR']
})

add('YTFI_PPC_TAG', {
    'tag': 'PPC_CONFIG_TABLE',
    'finding': "11 rows in P01. Maps (LAND1, TAG_LAST_LEAF, DEB_CRE) → TAG_FULL_PATH. Currently configured for 9 countries (AE, BH, CN, ID, IN, JO, MA, MY, PH). Tags handled: INSTRINF, -INSTRINF, USTRD, RMTINF — all narrative payment instruction tags. NO address tags configured.",
    'impact': "Adding FR rows would unlock the PPC framework for UNESCO's predominant flow but only for narrative tags as currently supported. Address handling would require extending YTFI_PPC_STRUC PPC_CODE values (currently SEPARATOR, FIXED_VAL, PPC_VAR, PPC_DESCR, PAY_FIELD) to support a new ADRC_PAY or PA0006_PAY value.",
    'field': 'TAG_FULL_PATH',
    'related': ['YTFI_PPC_STRUC', 'YCL_IDFI_CGI_DMEE_UTIL']
})

add('YCL_IDFI_CGI_DMEE_FR', {
    'tag': 'BADI_COUNTRY_FR',
    'finding': "FR country class for BAdI dispatcher. CM002 GET_VALUE implementation calls YCL_IDFI_CGI_DMEE_UTIL::GET_TAG_VALUE_FROM_CUSTO for every tag — i.e. PPC framework is the FR-specific override path. Today returns SY-SUBRC<>0 for all tags because YTFI_PPC_TAG has zero FR rows — falls through to FALLBACK class (which only handles Nm overflow).",
    'impact': "Strategic anchor: this class is the natural extension point if UNESCO wanted to fix CGI staff addresses via PPC. Adding FR rows in YTFI_PPC_TAG/STRUC for Cdtr/PstlAdr/StrtNm + PA0006 lookup PPC_CODE would activate the fix without touching Nicolas's code or the tree.",
    'incident': 'V001-SEPA-Cdtr-StructAddr',
    'field': 'GET_VALUE',
    'related': ['YCL_IDFI_CGI_DMEE_UTIL', 'YTFI_PPC_TAG']
})

add('/CITIPMW/V3_GET_CDTR_BLDG', {
    'tag': 'CITI_PROPRIETARY',
    'finding': "Citi proprietary FM (namespace /CITIPMW/) wired into /CITI/XML/UNESCO/DC_V3_01 tree for <BldgNb> Cdtr leaves. Source code not in UNESCO Z-namespace — delivered by Citi as add-on. Cannot be modified per rule feedback_only_modify_our_own_code.",
    'impact': "If staff-address fix is to land in CITI tree, this FM (and /CITIPMW/V3_CGI_CRED_REGION for CtrySubDvsn) cannot be modified — only replaced or bypassed via tree config or Z BAdI.",
    'field': '*',
    'related': ['/CITIPMW/V3_CGI_CRED_REGION', '/CITI/XML/UNESCO/DC_V3_01']
})

add('FPAYHX-REF01', {
    'tag': 'BYTE_STRUCTURED_BUFFER',
    'finding': "Extended payment buffer field — 60+ bytes structured per SAP std layout: [0..60]=street, [60..80]=building, [80..90]=post_code1, [90..100]=region, [100..110]=house_num1. Populated by SAP std FI_PAYMEDIUM_DMEE_CGI_05 (Event 05) from ADRC of the LIFNR at every payment medium creation. DMEE trees can bind to it via MP_SC_TAB=FPAYHX + MP_SC_FLD=REF01 + MP_OFFSET + MP_LENGTH for sub-range reads.",
    'impact': "The actual bug surface: this buffer carries ADRC blind read for every payment. Any tree using REF01 inherits the dept-code-for-staff defect. Fixing means either (a) overriding the FM that populates it (TFPM042FB Event 05 — currently FI_PAYMEDIUM_DMEE_CGI_05) or (b) overriding at the leaf level via Y_FI_DMEE_ADR.",
    'field': 'REF01',
    'related': ['FI_PAYMEDIUM_DMEE_CGI_05', 'ADRC', 'DMEE_TREE_NODE']
})

json.dump(d, open(P, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f"Annotated 9 objects (session #074). Total objects in annotations.json: {len(d)}")
