"""Add feedback rules for session #074 learnings."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

P = 'brain_v2/agent_rules/feedback_rules.json'
d = json.load(open(P, encoding='utf-8'))
existing = {r.get('id') for r in d}

new_rules = [
    {
        "id": "feedback_verify_dmee_tree_wiring_before_assuming_fix_scope",
        "rule": "Before claiming a custom FM (e.g. Y_FI_DMEE_ADR) fixes a payment-format bug, query DMEE_TREE_NODE.MP_EXIT_FUNC for every relevant tree to confirm the FM is actually wired. A fix only applies where the tree calls it.",
        "why": "Session #074: I initially extended the v6 simulator across all SEPA formats — but Y_FI_DMEE_ADR is wired ONLY in /SEPA_CT_UNES. The drift forecast for /SEPA_CT_ICTP_* was theoretical (would-happen-if), not in-scope. User caught this: 'no cambien nunca estos formatos cómo puede ser que funcione'. The same logic applies to /CGI_XML_CT_UNESCO and /CITI/XML/UNESCO/DC_V3_01 — they wire FI_CGI_DMEE_EXIT_W_BADI and /CITIPMW/* FMs, not Y_FI_DMEE_ADR. The fix surface is bounded by tree wiring, not by FM availability.",
        "how_to_apply": "(1) For any payment-format bug claim, query DMEE_TREE_NODE for the affected leaves with MP_EXIT_FUNC populated. (2) Separate 'in-scope' (FM is wired) from 'theoretical' (FM would fix if wired). (3) When reporting drift across formats, label each row as IN-SCOPE or OUT-OF-SCOPE based on tree wiring evidence, not on assumed coverage. (4) Reference: extracted DMEE_TREE_NODE topology for the 5 active formats in claim 185.",
        "severity": "HIGH",
        "created_session": "#074",
        "source_file": "knowledge/domains/Payment/e2e_vendor_payment_to_medium.md",
        "derives_from_core_principle": "CP-003",
        "cp_derivation_method": "session_074_user_correction",
        "domain_axes": {
            "functional": ["Payment", "DMEE"],
            "module": ["FI", "DMEE"],
            "process": ["P2P", "T2R"]
        }
    },
    {
        "id": "feedback_dfpayg_dfpayv_are_payment_audit_trail",
        "rule": "DFPAYG (execution evidence) and DFPAYV (config matrix) are the canonical source for any 'which payment format/run/vendor' question. Always cross-reference both before answering scope or coverage questions about UNESCO payments.",
        "why": "Session #074 added both tables to Gold DB. DFPAYG = 9,848 rows = ground truth for what actually fired in the last 2 years; DFPAYV = 84 rows = static config showing what CAN fire (with 6 lapsed configs that never run). Combined with REGUH, they let SQL answer: 'which staff vendor was paid via which format×cocode×bank×account×PM combination?' — replacing ad-hoc P01 RFC queries.",
        "how_to_apply": "(1) Format scope questions: SELECT DISTINCT FORMI FROM DFPAYG WHERE LAUFD >= '<window>' (= active set); SELECT FORMI FROM DFPAYV (= configured set); difference = lapsed configs. (2) Vendor questions: JOIN DFPAYG to REGUH on (LAUFD, LAUFI, ZBUKR) to get the vendor list paid via each format. (3) Bank/account/PM granularity: REGUH_FAST has HBKID, HKTID, RZAWE — better than DFPAYG for the routing breakdown. (4) Indexes: idx_reguh_run on (LAUFD,LAUFI,ZBUKR), idx_dfpayg_formi, idx_dfpayg_zbukr.",
        "severity": "HIGH",
        "created_session": "#074",
        "source_file": "knowledge/domains/Payment/e2e_vendor_payment_to_medium.md",
        "derives_from_core_principle": "CP-002",
        "cp_derivation_method": "session_074_tool_addition",
        "domain_axes": {
            "functional": ["Payment", "DataExtraction"],
            "module": ["FI", "DMEE"],
            "process": ["P2P", "T2R"]
        }
    },
    {
        "id": "feedback_label_distinct_vendors_vs_payment_lines",
        "rule": "When reporting payment metrics, ALWAYS label whether the count is 'distinct LIFNRs' or 'REGUH payment lines'. Same employee paid 30 times = 1 distinct LIFNR = 30 lines. The two scales differ by 5-30x in typical UNESCO data.",
        "why": "Session #074 user clarification: 'O sea son la cantidades de pagos staff que se hacen para ese formato' — user assumed 'staff drift = number of payments' but my number was 'distinct staff vendors'. The actual XMLs emitted = REGUH lines, not vendors. For /SEPA_CT_UNES UNES 2025-26: 1,659 staff vendors but 12,107 lines (7.3x factor).",
        "how_to_apply": "(1) Default to BOTH counts when reporting: e.g. '1,659 staff vendors → 12,107 lines'. (2) For business impact (XMLs emitted with wrong data, bank rejection volume), use LINES. (3) For root-cause analysis (which employees are affected), use VENDORS. (4) Include the multiplier explicitly: 'pays/vendor ratio = 7.3x'.",
        "severity": "MEDIUM",
        "created_session": "#074",
        "source_file": "knowledge/domains/Payment/e2e_vendor_payment_to_medium.md",
        "derives_from_core_principle": "CP-003",
        "cp_derivation_method": "session_074_user_question",
        "domain_axes": {
            "functional": ["Payment", "Reporting"],
            "module": ["FI"],
            "process": ["P2P"]
        }
    },
    {
        "id": "feedback_use_explicit_business_column_labels",
        "rule": "When presenting tables to operational users, use the FULL business name for each column (Company Code, House Bank, Bank Account, Payment Method) — NOT the SAP technical abbreviation (ZBUKR, HBKID, HKTID, RZAWE) or my shorthand (COCO, BANK, ACCT, PM).",
        "why": "Session #074 user feedback: 'O faltan las columnas, Company code, house bank bank Account, and mediunm payment please' — when I used abbreviated headers, the user explicitly asked for the full names. Treasury and finance operators read SAP tables every day but the technical names slow them down vs business labels.",
        "how_to_apply": "(1) First column header row uses business names: 'Company Code (ZBUKR)' is acceptable, 'ZBUKR' alone is not. (2) Apply consistently across companions and brain output. (3) Exception: when the audience is purely technical (ABAP devs / brain agents), abbreviations are fine.",
        "severity": "LOW",
        "created_session": "#074",
        "source_file": "—",
        "derives_from_core_principle": "CP-001",
        "cp_derivation_method": "session_074_user_correction",
        "domain_axes": {
            "functional": ["UX", "Reporting"],
            "module": ["*"],
            "process": ["*"]
        }
    },
    {
        "id": "feedback_rfc_read_table_quirks",
        "rule": "RFC_READ_TABLE has narrow accepted OPTIONS syntax: (a) NO 'IN (...)' clauses — use multiple single-field calls instead; (b) leading space required when concatenating conditions (' AND TECH_NAME = ...'); (c) DATA_BUFFER_EXCEEDED on wide tables — limit FIELDS to <20 columns or expect 512-byte WA truncation. Document tables that are DMEE_TREE_NODE, REGUH, etc. often hit these limits.",
        "why": "Session #074 wasted ~15 minutes debugging OPTION_NOT_VALID errors when querying DMEE_TREE_NODE with IN clauses. Once switched to per-TECH_NAME calls in a loop, queries worked. This is a recurring pattern across sessions but never captured as a rule.",
        "how_to_apply": "(1) When OPTION_NOT_VALID appears, simplify OPTIONS: one condition per row, leading space on continuation rows, no IN clauses. (2) For multi-value filtering, loop the query per value instead. (3) When DATA_BUFFER_EXCEEDED hits, narrow FIELDS list or split into multiple narrow queries. (4) Verified working pattern: OPTIONS=[{'TEXT':\"TREE_ID = '/X'\"}, {'TEXT':\" AND TECH_NAME = 'StrtNm'\"}]. Bad: OPTIONS=[{'TEXT':\"TREE_ID='/X' AND TECH_NAME IN ('StrtNm','BldgNb')\"}].",
        "severity": "MEDIUM",
        "created_session": "#074",
        "source_file": "Zagentexecution/mcp-backend-server-python/rfc_helpers.py",
        "derives_from_core_principle": "CP-001",
        "cp_derivation_method": "session_074_debugging_loss",
        "domain_axes": {
            "functional": ["DataExtraction", "Tooling"],
            "module": ["*"],
            "process": ["*"]
        }
    },
]

added = 0
for r in new_rules:
    if r['id'] not in existing:
        d.append(r)
        added += 1
        print(f"  + {r['id']}")
    else:
        print(f"  = {r['id']} (already exists, skipped)")

json.dump(d, open(P, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f"\nAdded {added} rules. Total: {len(d)}")
