"""Append 7 Phase 0 consolidated claims + 2 feedback rules to brain_v2."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CLAIMS_FILE = 'brain_v2/claims/claims.json'
RULES_FILE = 'brain_v2/agent_rules/feedback_rules.json'

with open(CLAIMS_FILE, 'r', encoding='utf-8') as f:
    claims = json.load(f)

phase0_claims = [
    {
        "id": 66,
        "claim": "At UNESCO P01 as of 2026-04-24, YCL_IDFI_CGI_DMEE_AE and _BH do NOT exist in TADIR. Only YCL_IDFI_CGI_DMEE_FR, _FALLBACK, _UTIL, _DE, _IT exist as UNESCO country-specific BAdI implementations of FI_CGI_DMEE_EXIT_W_BADI. Handoff doc speculation about AE/BH falsified.",
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": [{"type": "production_data", "ref": "Zagentexecution/mcp-backend-server-python/phase0_gap_probe.py", "cite": "RFC_READ_TABLE TADIR on P01 2026-04-24 returned 0 rows for YCL_IDFI_CGI_DMEE_AE/_BH and Y_IDFI_CGI_DMEE_COUNTRY_AE/_BH.", "added_session": 62, "migrated_from_legacy": False}],
        "evidence_against": None,
        "related_objects": ["YCL_IDFI_CGI_DMEE_FR", "YCL_IDFI_CGI_DMEE_FALLBACK", "YCL_IDFI_CGI_DMEE_UTIL", "YCL_IDFI_CGI_DMEE_DE", "YCL_IDFI_CGI_DMEE_IT"],
        "domain": "Payment",
        "created_session": 62,
        "resolved_session": 62,
        "resolution_notes": "Closes GAP-003 of Phase 0.",
        "status": "active",
        "domain_axes": {"functional": ["Payment", "BCM"], "module": ["FI"], "process": ["P2P", "T2R"]}
    },
    {
        "id": 67,
        "claim": "FPAYHX in P01 has 432 fields, 25 Z-fields. Handoff doc claim about FPAYHX-ZSTRA/ZHSNM/ZPSTL/ZORT1/ZLAND is WRONG - none exist. Actual: ZPFST, ZPLOR, ZLISO, ZLNDX, ZREGX, ZNM1S/2S, ZBANK, ZBNKL_EXT, ZFORN, ZREF01..ZREF10 (customer buffers - 10 not 5), ZSTCEG. FPAYH has ZERO REF fields; buffers live in FPAYHX-ZREF01..ZREF10.",
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": [{"type": "production_data", "ref": "Zagentexecution/mcp-backend-server-python/phase0_gap_probe.py", "cite": "DDIF_FIELDINFO_GET TABNAME=FPAYHX on P01 2026-04-24 returned 432 fields, 25 Z-fields enumerated. TABNAME=FPAYH returned 0 REF fields.", "added_session": 62, "migrated_from_legacy": False}],
        "evidence_against": None,
        "related_objects": ["FPAYHX", "FPAYH", "CI_FPAYHX"],
        "domain": "Payment",
        "created_session": 62,
        "resolved_session": 62,
        "resolution_notes": "Closes GAP-004 of Phase 0. MAJOR correction to handoff doc. Phase 2 user exit signature revised to write FPAYHX-ZREF01..05 not FPAYH-REF01..05.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI"], "process": ["P2P", "T2R"]}
    },
    {
        "id": 68,
        "claim": "No UNESCO custom ABAP code writes to FPAYHX-Z* fields or FPAYH-REF fields. Static scan of 986 ABAP files in extracted_code/ with 8 write-pattern regexes returned 0 hits. FPAYHX Z-fields are SAP-standard populated by Payment Medium Workbench at F110 runtime via CI_FPAYHX append binding to vendor master LFA1+ADRC.",
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": [{"type": "source_code", "ref": "knowledge/domains/Payment/phase0/gap_005_static_analysis.md", "cite": "Scanned 986 abap files for FPAYHX/FPAYH write patterns. Zero matches in payment/DMEE code.", "added_session": 62, "migrated_from_legacy": False}],
        "evidence_against": None,
        "related_objects": ["FPAYHX", "FPAYH", "YCL_IDFI_CGI_DMEE_FALLBACK", "YCL_IDFI_CGI_DMEE_FR", "YCL_IDFI_CGI_DMEE_UTIL"],
        "domain": "Payment",
        "created_session": 62,
        "resolved_session": 62,
        "resolution_notes": "Closes GAP-005 of Phase 0. Supersedes Phase 1 Explore-agent speculation that a UNESCO BAdI populates the Z-fields.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI"], "process": ["P2P", "T2R"]}
    },
    {
        "id": 69,
        "claim": "Across the 4 target DMEE trees (/SEPA_CT_UNES, /CITI/XML/UNESCO/DC_V3_01, /CGI_XML_CT_UNESCO, /CGI_XML_CT_UNESCO_1), 794 of 1,975 nodes (40.2%) have MP_EXIT_FUNC=FI_CGI_DMEE_EXIT_W_BADI and dispatch through UNESCO country-class BAdI implementations at runtime. 146 of those 794 exit-invoking nodes are address-related (SEPA=0, CITI=4, CGI=69, CGI_1=73). 33 distinct MP_EXIT_FUNC values total.",
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": [{"type": "production_data", "ref": "knowledge/domains/Payment/phase0/gap006_dmee_nodes_with_exit.csv", "cite": "RFC_READ_TABLE DMEE_TREE_NODE on P01 2026-04-24 for 4 target trees, 1,975 rows with MP_EXIT_FUNC + CK_EXIT_FUNC columns.", "added_session": 62, "migrated_from_legacy": False}],
        "evidence_against": None,
        "related_objects": ["FI_CGI_DMEE_EXIT_W_BADI", "YCL_IDFI_CGI_DMEE_FR", "YCL_IDFI_CGI_DMEE_FALLBACK", "YCL_IDFI_CGI_DMEE_UTIL", "YCL_IDFI_CGI_DMEE_DE", "YCL_IDFI_CGI_DMEE_IT"],
        "domain": "Payment",
        "created_session": 62,
        "resolved_session": 62,
        "resolution_notes": "Closes GAP-006 of Phase 0. New structured-address nodes in Phase 2 must decide per-node whether to set MP_EXIT_FUNC blank or route through BAdI.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI"], "process": ["P2P", "T2R"]}
    },
    {
        "id": 70,
        "claim": "D01 (dev) is incomplete vs P01 (prod) for UNESCO DMEE BAdI ecosystem. 5 N_MENARD-authored (devclass=YA) objects exist in P01 TADIR but NOT in D01: YCL_IDFI_CGI_DMEE_DE (CLAS), _IT (CLAS), Y_IDFI_CGI_DMEE_COUNTRIES_DE (ENHO), _FR (ENHO), _IT (ENHO). Zero D01-only objects found. Blocks Phase 2: retrofit D01 from P01 is required before any BAdI-ecosystem modification.",
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": [{"type": "production_data", "ref": "knowledge/domains/Payment/phase0/d01_vs_p01_inventory.csv", "cite": "RFC_READ_TABLE TADIR on both P01 and D01 2026-04-24 via phase0_d01_vs_p01_inventory.py.", "added_session": 62, "migrated_from_legacy": False}],
        "evidence_against": None,
        "related_objects": ["YCL_IDFI_CGI_DMEE_DE", "YCL_IDFI_CGI_DMEE_IT", "Y_IDFI_CGI_DMEE_COUNTRIES_DE", "Y_IDFI_CGI_DMEE_COUNTRIES_FR", "Y_IDFI_CGI_DMEE_COUNTRIES_IT"],
        "domain": "Payment",
        "created_session": 62,
        "resolved_session": None,
        "resolution_notes": "Phase 0 finding. Resolution = Phase 0 follow-up Retrofit D01 from P01. Alignment call with N_MENARD required before Phase 2.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI", "BASIS"], "process": ["P2P", "T2R"]}
    },
    {
        "id": 71,
        "claim": "UNESCO vendor master is CBPR+ compliance-ready for survival (Hybrid minimum). Of 111,241 active vendors (LOEVM blank) joined with ADRC via ADRNR, only 5 (0.005%) miss CITY1 or COUNTRY - the only MANDATORY fields under CBPR+ Hybrid (TwnNm+Ctry required). Non-mandatory missing: 5,570 STREET (5.0%), 1,153 POST_CODE1 (1.0%), 76,574 HOUSE_NUM1 (68.8%). Risk downgraded HIGH to LOW.",
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": [{"type": "production_data", "ref": "knowledge/domains/Payment/phase0/vendor_master_dq.md", "cite": "SQL adapted from handoff doc §7.2 executed on Gold DB LFA1 JOIN ADRC 2026-04-24.", "added_session": 62, "migrated_from_legacy": False}],
        "evidence_against": None,
        "related_objects": ["LFA1", "ADRC"],
        "domain": "Payment",
        "created_session": 62,
        "resolved_session": 62,
        "resolution_notes": "Phase 0 vendor DQ audit. Risk downgraded to LOW.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI"], "process": ["P2P", "T2R"]}
    },
    {
        "id": 72,
        "claim": "At UNESCO, total DMEE-touching transports 2017-2026 = 53 by 8 users. M_SPRONK = 31 (primarily CITI DC_V3_01=27, SEPA_CT_UNES=7, CGI_XML_CT_UNESCO=4). N_MENARD = 9 all ABAP class code (YCL_IDFI_CGI_DMEE_*), code owner. FP_SPEZZANO = 5 all 2025 Q1 on CGI trees, all PMF VARIANT customizing (VC_TFPM042F) not tree node changes, classified ASSIST/IRRELEVANT. E_FRATNIK = 4 on ICTP (out of scope).",
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": [{"type": "production_data", "ref": "knowledge/domains/Payment/phase0/cts_dmee_authors.md", "cite": "Parsed all 10 cts_batch_YYYY.json files 2017-2026 filtered for DMEE-touching transports.", "added_session": 62, "migrated_from_legacy": False}],
        "evidence_against": None,
        "related_objects": ["M_SPRONK", "N_MENARD", "FP_SPEZZANO"],
        "domain": "Payment",
        "created_session": 62,
        "resolved_session": 62,
        "resolution_notes": "Phase 0 Francesco audit + CTS author map. Supersedes Phase 1 Explore-agent claim of Marlies=28 transports (actual=31). N_MENARD identified as required reviewer for Phase 2 Step 9.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI", "CTS"], "process": ["P2P", "T2R"]}
    },
]

# Prevent duplicates
existing_ids = {c.get('id') for c in claims}
added = 0
for nc in phase0_claims:
    if nc['id'] in existing_ids:
        print(f"Skipping duplicate id {nc['id']}")
        continue
    claims.append(nc)
    added += 1

with open(CLAIMS_FILE, 'w', encoding='utf-8') as f:
    json.dump(claims, f, indent=2, ensure_ascii=False)

print(f'Appended {added} Phase 0 claims. Total claims: {len(claims)}')

# Append 3 feedback rules
with open(RULES_FILE, 'r', encoding='utf-8') as f:
    rules = json.load(f)

phase0_rules = [
    {
        "id": "feedback_structured_addr_hybrid_is_default_transition",
        "rule": "When migrating an XML payment format to ISO 20022 structured address, default to Hybrid (TwnNm+Ctry mandatory + AdrLine fallback) unless each specific bank spec demands fully-structured. Never assume all banks have identical strictness.",
        "why": "CBPR+ Nov 2026 mandate permits Hybrid (structured + AdrLine coexist) as a valid compliance state. The handoff doc for UNESCO session #62 explicitly confirms TwnNm+Ctry are the only hard-required fields. Defaulting to Hybrid preserves rollback safety and accommodates vendor master DQ gaps (UNESCO 5% missing STREET, 68% missing HOUSE_NUM1 but 99.995% have CITY1+COUNTRY). Going to fully-structured by default wastes effort on vendor master cleanup that may not be required by all banks.",
        "how_to_apply": "Before committing to 'only structured' scope, (1) collect each bank's written spec for structured-address strictness, (2) measure vendor master DQ per field to know the cost of fully-structured, (3) default to Hybrid per bank unless bank spec is explicit. Re-evaluate stricter modes post-go-live on a per-bank basis.",
        "severity": "MEDIUM",
        "source_file": "knowledge/domains/Payment/phase0/gap_closure_report.md",
        "derives_from_core_principle": "CP-003",
        "added_session": 62,
        "tag": ["Payment", "DMEE", "CBPR", "ISO20022"]
    },
    {
        "id": "feedback_structured_addr_three_asymmetric_patterns",
        "rule": "Structured-address migration in SAP DMEE has THREE distinct technical patterns by XML party, not one. Do not confuse them: (1) Cdtr address is SAP-auto-populated via FPAYHX Z-fields bound to vendor master LFA1+ADRC — DMEE tree config only, no ABAP needed. (2) Dbtr address is NOT in FPAYHX/FPAYH — requires ABAP user exit registered in OBPM4 Event 05 that reads T001→ADRC and writes FPAYHX-ZREF01..ZREF05 (NOT FPAYH-REF). (3) UltmtCdtr (alternative payee) may require a data source decision (vendor master / Z-table / separate user exit) per bank/format.",
        "why": "UNESCO handoff doc §5 conflated the three patterns causing scope confusion in session #62. Dbtr requires a new FM while Cdtr does not. Mistaking the two leads to either unnecessary ABAP or missing ABAP — both are schedule-breakers for a Nov 2026 deadline.",
        "how_to_apply": "When scoping a structured-address change, decompose per XML party (Dbtr/Cdtr/UltmtCdtr/CdtrAgt) and apply the correct pattern to each. Cdtr = tree-only. Dbtr = tree + user exit + OBPM4 registration. UltmtCdtr = decision-first, spec-second, code-third.",
        "severity": "HIGH",
        "source_file": "knowledge/domains/Payment/phase0/xml_touch_points_complete.md",
        "derives_from_core_principle": "CP-003",
        "added_session": 62,
        "tag": ["Payment", "DMEE", "CBPR", "ISO20022", "BCM"]
    },
    {
        "id": "feedback_dmee_one_fm_three_pmw",
        "rule": "A user exit FM for DMEE can be registered in multiple PMW formats via OBPM4 simultaneously. Write once, reuse across formats. Avoid per-format FM duplication.",
        "why": "Handoff doc recommends this; UNESCO has 3 target DMEE trees (SEPA_CT_UNES, CITI DC_V3_01, CGI_XML_CT_UNESCO) that all need the same Dbtr address enrichment logic. Building 3 FMs triples maintenance and drift risk.",
        "how_to_apply": "When creating Z_DMEE_UNESCO_DEBTOR_ADDR or similar FMs, register it in OBPM4 for all needed PMW formats using Event 05. Centralize logic; format-specific tweaks go behind IF statements keyed on format name, not in separate FMs.",
        "severity": "MEDIUM",
        "source_file": "C:/Users/jp_lopez/Downloads/UNESCO_BCM_StructuredAddress_AgentHandoff.docx",
        "derives_from_core_principle": "CP-002",
        "added_session": 62,
        "tag": ["Payment", "DMEE", "BCM"]
    },
]

existing_rule_ids = {r.get('id') for r in rules}
added_r = 0
for nr in phase0_rules:
    if nr['id'] in existing_rule_ids:
        print(f"Skipping duplicate rule {nr['id']}")
        continue
    rules.append(nr)
    added_r += 1

with open(RULES_FILE, 'w', encoding='utf-8') as f:
    json.dump(rules, f, indent=2, ensure_ascii=False)

print(f'Appended {added_r} Phase 0 feedback rules. Total rules: {len(rules)}')
