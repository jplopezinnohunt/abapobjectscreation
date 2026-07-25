"""Append 6 new brain claims from session #074."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

P = 'brain_v2/claims/claims.json'
d = json.load(open(P, encoding='utf-8'))
next_id = max(c['id'] for c in d) + 1
S = 74

new_claims = [
    {
        "id": next_id,
        "claim": "Across all 5 active SEPA/CGI/CITI formats in UNESCO production (2025-2026), the staff-address bug affects 5,686 distinct staff-vendor cases (12.4% of 61,476 paid vendors). v6 PA0006-first detection in Y_FI_DMEE_ADR covers 1,905 cases (33.5% of impact) — limited to /SEPA_CT_UNES tree only. 3,781 staff cases remain unfixed across /CGI_XML_CT_UNESCO (1,882), /CITI/XML/UNESCO/DC_V3_01 (1,818), and /SEPA_CT_ICTP_* (81). Theory ('only employees vary') confirmed: zero drift cases without a PA0006 SUBTY=1 hit across the 21,507-tuple in-scope universe.",
        "claim_type": "verified_fact", "confidence": "TIER_1",
        "evidence_for": [{
            "type": "production_data",
            "ref": "Gold DB sim_all_formats + sim_sepa_all (2026-05-10)",
            "cite": "SQL replay from DFPAYG joined REGUH/LFA1/PA0006/ADRC. Reproducible via Zagentexecution/sim_all_formats.py.",
            "added_session": S
        }],
        "evidence_against": None,
        "related_objects": ["Y_FI_DMEE_ADR", "PA0006", "ADRC", "DFPAYG", "DFPAYV",
                            "/SEPA_CT_UNES", "/CGI_XML_CT_UNESCO", "/CITI/XML/UNESCO/DC_V3_01"],
        "domain": "Payment",
        "created_session": S, "resolved_session": S,
        "resolution_notes": "Quantifies the remaining fix surface. Next priority is /CGI_XML_CT_UNESCO + /CITI/XML/UNESCO/DC_V3_01 which account for 65% of unfixed impact.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI", "DMEE", "HCM"], "process": ["P2P", "H2R"]}
    },
    {
        "id": next_id + 1,
        "claim": "DMEE_TREE_NODE address-leaf inventory across the 5 active UNESCO payment formats (D01 2026-05-11): /SEPA_CT_UNES = 61 nodes (HYBRID — V0 AdrLine + V001 PstlAdr coexisten); /CGI_XML_CT_UNESCO = 140 nodes (FULL STRUCTURED via FI_CGI_DMEE_EXIT_W_BADI for Cdtr leaves); /CITI/XML/UNESCO/DC_V3_01 = 110 nodes (uses Citi proprietary /CITIPMW/V3_GET_CDTR_BLDG + /CITIPMW/V3_CGI_CRED_REGION); /SEPA_CT_ICTP_ISO = 20 nodes (MINIMAL — only StrtNm/PstCd/TwnNm/Ctry, no BldgNb/CtrySubDvsn/Dept/SubDept/AdrLine, NO exit FM); /SEPA_CT_ICTP_ISO_EXTRASEPA = 22 nodes (minimal + 1 BAdI on Dbtr StrtNm).",
        "claim_type": "verified_fact", "confidence": "TIER_1",
        "evidence_for": [{
            "type": "production_data",
            "ref": "DMEE_TREE_NODE D01 RFC_READ_TABLE 2026-05-11",
            "cite": "Per-format query NODE_ID + TECH_NAME + PARENT_ID + MP_EXIT_FUNC + MP_SC_TAB + MP_SC_FLD. Reproducible via 4-call shell pattern (no IN clauses).",
            "added_session": S
        }],
        "evidence_against": None,
        "related_objects": ["DMEE_TREE_NODE", "Y_FI_DMEE_ADR", "FI_CGI_DMEE_EXIT_W_BADI",
                            "/CITIPMW/V3_GET_CDTR_BLDG", "/CITIPMW/V3_CGI_CRED_REGION"],
        "domain": "Payment",
        "created_session": S, "resolved_session": S,
        "resolution_notes": "First time the full per-format tree topology is documented with line-by-line bindings.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI", "DMEE"], "process": ["P2P", "T2R"]}
    },
    {
        "id": next_id + 2,
        "claim": "The structured-address bug is NOT exclusive to Y_FI_DMEE_ADR scope — it lives in SAP std FI_PAYMEDIUM_DMEE_CGI_05 (Event 05) which populates FPAYHX-REF01/REF02 buffers from ADRC blindly at every payment medium creation. Every UNESCO format that reads FPAYHX-REF01/-Z* without an override emits the dept code for SCSA staff. Includes /CGI_XML_CT_UNESCO (FI_CGI_DMEE_EXIT_W_BADI only handles Nm overflow), /CITI/XML/UNESCO/DC_V3_01 (Citi proprietary FMs read same buffer), /SEPA_CT_ICTP_* (direct field bindings). Nicolas YCL_IDFI_CGI_DMEE_FALLBACK::GET_CREDIT does NOT address-override — only Nm overflow truncation.",
        "claim_type": "verified_fact", "confidence": "TIER_1",
        "evidence_for": [{
            "type": "code_extract",
            "ref": "extracted_code/FI/DMEE_p01_canonical/YCL_IDFI_CGI_DMEE_FALLBACK====CM001.abap",
            "cite": "GET_CREDIT method 1-37: only WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>' overflow concat (mv_cdtr_name+35), no PA0006/ADRC read.",
            "added_session": S
        }],
        "evidence_against": None,
        "related_objects": ["FI_PAYMEDIUM_DMEE_CGI_05", "FPAYHX-REF01", "ADRC",
                            "FI_CGI_DMEE_EXIT_W_BADI", "YCL_IDFI_CGI_DMEE_FALLBACK",
                            "/CGI_XML_CT_UNESCO", "/CITI/XML/UNESCO/DC_V3_01"],
        "domain": "Payment",
        "created_session": S, "resolved_session": S,
        "resolution_notes": "Identifies the true bug surface: SAP std Event 05 reading ADRC. The 4 unfixed formats all read this buffer.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI", "DMEE"], "process": ["P2P"]}
    },
    {
        "id": next_id + 3,
        "claim": "UNESCO PPC framework (YCL_IDFI_CGI_DMEE_UTIL::GET_TAG_VALUE_FROM_CUSTO + YTFI_PPC_TAG + YTFI_PPC_STRUC + T015L) is technically wired from FR country class (YCL_IDFI_CGI_DMEE_FR::CM002::GET_VALUE) into CGI BAdI dispatcher, but DORMANT for UNESCO. YTFI_PPC_TAG has 11 rows for AE/BH/CN/ID/IN/JO/MA/MY/PH; ZERO rows for FR/DE/IT/GB/US/BR (countries of SocGen/Citi/Unicredit). Configured tags are narrative (<InstrInf>, <Ustrd>) — NOT address tags. PPC cannot resolve staff-address bug as currently designed.",
        "claim_type": "verified_fact", "confidence": "TIER_1",
        "evidence_for": [{
            "type": "production_data",
            "ref": "Gold DB YTFI_PPC_TAG (11 rows) + YTFI_PPC_STRUC (133 rows) + T015L (73 rows)",
            "cite": "Query 2026-05-11. PPC dispatch verified in extracted_code/FI/DMEE_p01_canonical/YCL_IDFI_CGI_DMEE_FR==========CM002.abap get_value lines 1-17.",
            "added_session": S
        }],
        "evidence_against": None,
        "related_objects": ["YCL_IDFI_CGI_DMEE_UTIL", "YCL_IDFI_CGI_DMEE_FR",
                            "YTFI_PPC_TAG", "YTFI_PPC_STRUC", "T015L"],
        "domain": "Payment",
        "created_session": S, "resolved_session": S,
        "resolution_notes": "Closes ambiguity: PPC not usable for address fix without (a) FR config rows AND (b) extending PPC_CODE domain for PA0006 lookup.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI", "DMEE"], "process": ["P2P"]}
    },
    {
        "id": next_id + 4,
        "claim": "F110 alt-payee resolution lands the resolved payee LIFNR in FPAYH-GPA1R (not invoice vendor). 16 LFA1.LNRZA + 9 LFB1.LNRZB populated in D01; 2 alt-payee-fired records in sampled REGUH (EMPFG <> LIFNR). v6 Y_FI_DMEE_ADR uses FPAYH-GPA1R for both PA0006 cast and ADRC fallback — handles alt-payees correctly by construction. Edge case: ICVS VS90* alphanumeric LIFNRs — ABAP NUMC8 cast well-defined (e.g. VS90033973 → 90033973) and empirically never collides with real PERNR; risk theoretical only.",
        "claim_type": "verified_fact", "confidence": "TIER_1",
        "evidence_for": [{
            "type": "production_data",
            "ref": "D01 RFC verification 2026-05-09",
            "cite": "LFA1.LNRZA (16) + LFB1.LNRZB (9). REGUH alt-payee sample 300 rows / 2 fired. PA0006 hit check 5 chains incl ICVS VS90001303→VS90033973 (miss).",
            "added_session": S
        }],
        "evidence_against": None,
        "related_objects": ["LFA1", "LFB1", "REGUH", "FPAYH-GPA1R", "Y_FI_DMEE_ADR"],
        "domain": "Payment",
        "created_session": S, "resolved_session": S,
        "resolution_notes": "Closes alt-payee concern. v6 needs no extra guard. Optional v7 with CO '0123456789' guard is preventive only.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI", "HCM"], "process": ["P2P", "H2R"]}
    },
    {
        "id": next_id + 5,
        "claim": "UNESCO operates exactly 7 active payment formats over last 2 years (2024-05-09 to 2026-05-08) per DFPAYG: /CGI_XML_CT_UNESCO (3,772 runs), /CITI/XML/UNESCO/DC_V3_01 (3,336), /SEPA_CT_UNES (1,783), /SEPA_CT_ICTP_ISO (514), /SEPA_CT_ICTP_ISO_EXTRASEPA (431), /SEPA_CT_ICTP_ISO_EXTRASEPA_I (6 dormant since 2025-11-25), ZSETIF_FOR_ICTP (6 dormant since 2024-08-20). DFPAYV (config) has 10 distinct formats; 6 are LAPSED in DFPAYG (CMI101, CITI_XML_MASTER, DIRECT_CREDIT, DTAZV, SEPA_CT, SETIF, Z_SEPA_CT_DB_XML) — customized but never fire.",
        "claim_type": "verified_fact", "confidence": "TIER_1",
        "evidence_for": [{
            "type": "production_data",
            "ref": "Gold DB DFPAYG (9,848 rows last 2y) + DFPAYV (84 rows full config)",
            "cite": "SELECT FORMI, COUNT(*) FROM DFPAYG GROUP BY FORMI. DFPAYV vs DFPAYG set difference 2026-05-10.",
            "added_session": S
        }],
        "evidence_against": None,
        "related_objects": ["DFPAYG", "DFPAYV", "T042Z", "TFPM042FB"],
        "domain": "Payment",
        "created_session": S, "resolved_session": S,
        "resolution_notes": "Canonical scope for impact analysis. Address-fix project covers 5 active formats + ICTP variants; ignore 6 lapsed configs (housekeeping).",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI", "DMEE"], "process": ["P2P", "T2R"]}
    },
]

d.extend(new_claims)
json.dump(d, open(P, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f"Appended {len(new_claims)} claims (id {next_id}-{next_id + len(new_claims) - 1}). Total: {len(d)}")
