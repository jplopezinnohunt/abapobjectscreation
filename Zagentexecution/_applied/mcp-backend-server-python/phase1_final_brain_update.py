"""Final brain update for Phase 1 extraction completion."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('brain_v2/claims/claims.json','r',encoding='utf-8') as f:
    claims = json.load(f)

new_claims = [
    {
        "id": 80,
        "claim": "CITIPMW V3 has TWO architectural layers for CITI tree address: (a) Event 05 FM /CITIPMW/V3_PAYMEDIUM_DMEE_05 pre-populates FPAYHX_FREF for Dbtr only with byte layout identical to SAP-std GENERIC. (b) Node-level EXIT_FUNC FMs /CITIPMW/V3_CGI_CRED_STREET/CITY/PO_CITY/REGION + EXIT_CGI_CRED_NAME/NM2 + GET_CDTR_BLDG mutate Cdtr structured node values at tree traversal time. They read vendor address via READ_BSEC for one-time vendors (gpa1t=14) OR ADDR_GET via FPAYH-ZADNR for regular vendors. All return 35-char values to c_value.",
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": [{"type": "source_code", "ref": "extracted_code/FI/DMEE_full_inventory/CITIPMW_V3_CGI_CRED_STREET.abap:62-90 + CITIPMW_V3_PAYMEDIUM_DMEE_05.abap:81-124", "cite": "Both extracted via RPY_FUNCTIONMODULE_READ_NEW NEW_SOURCE 2026-04-25.", "added_session": 62, "migrated_from_legacy": False}],
        "evidence_against": None,
        "related_objects": ["/CITIPMW/V3_PAYMEDIUM_DMEE_05", "/CITIPMW/V3_CGI_CRED_STREET", "/CITIPMW/V3_CGI_CRED_PO_CITY"],
        "domain": "Payment",
        "created_session": 62,
        "resolved_session": 62,
        "resolution_notes": "CITI tree V001 Cdtr nodes need NO CHANGE. Only Dbtr needs add structured siblings.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI"], "process": ["P2P", "T2R"]}
    },
    {
        "id": 81,
        "claim": "TFPM042FB at P01 confirms /CITI/XML/UNESCO/DC_V3_01 Event 05 = /CITIPMW/V3_PAYMEDIUM_DMEE_05. /CITI/XML/UNESCO/DIRECT_CREDIT Event 05 = /CITIPMW/FI_PAYMEDIUM_DMEE_05 (different FM, NOT in 4-tree scope). RU_CITI/RUR Russian variants out of scope. 7 Y/Z FMs in OBPM4 total: Y_FI_PAYMEDIUM_101_20/30 + ZFI_PAYMEDIUM_CHECK/PDF — none affect our 4 target DMEE trees.",
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": [{"type": "production_data", "ref": "TFPM042FB query on P01 2026-04-25", "cite": "Verified explicit registration row + 7 Y/Z FM enumeration.", "added_session": 62, "migrated_from_legacy": False}],
        "evidence_against": None,
        "related_objects": ["/CITI/XML/UNESCO/DC_V3_01", "/CITIPMW/V3_PAYMEDIUM_DMEE_05"],
        "domain": "Payment",
        "created_session": 62,
        "resolved_session": 62,
        "resolution_notes": "Removes prior agent caveat: confirmed CITI Event 05 registered.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI"], "process": ["P2P", "T2R"]}
    },
    {
        "id": 82,
        "claim": "DMEE_TREE_COND analysis: 614 conditions in 4 target trees. 42 country-gates ALL in CITI tree (UBISO comparisons): TH/GA/CM/BG/AE special handling, USD-zone (US/CA/PR/RU) cluster, non-USD cluster. 60 address-ref conditions: PSTLADRMOR3 (14x UltmtCdtr) + PSTLADRMOR1 (14x UltmtDbtr) + PSTLADRMORE (12x general) + PSTLADRMOR2 (10x Cdtr) + CDAGPSTLADR (2x CdtrAgt) + DBTRPSTLADR (2x Dbtr). PSTLADRMOR1/2/3 confirmed as TECH switch nodes gating structured emission.",
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": [{"type": "production_data", "ref": "knowledge/domains/Payment/phase0/dmee_full/dmee_tree_cond_p01.csv parsed 2026-04-25", "cite": "Counter analysis on 614 rows.", "added_session": 62, "migrated_from_legacy": False}],
        "evidence_against": None,
        "related_objects": ["/CITI/XML/UNESCO/DC_V3_01"],
        "domain": "Payment",
        "created_session": 62,
        "resolved_session": 62,
        "resolution_notes": "Phase 3 unit tests must include cases per CITI country-gate (TH/GA/CM/BG/AE) to verify V001 structured nodes don't conflict with existing UBISO logic.",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI"], "process": ["P2P", "T2R"]}
    },
    {
        "id": 83,
        "claim": "Phase 1 extraction COMPLETE for V001 design lock. 9 of 15 CITIPMW exit FMs extracted (address-relevant ones all captured). Tax/postcode/inv-desc FMs (CGI_TAX_CATEGORY/METHOD, POSTALCODE, INV_DESC, EXIT_CGI_XML, GET_CDTR_EMAIL) not found via RFC — likely renamed/inactive, non-blocking for address scope. SURGICAL CHANGE confirmed by both expert agents: SEPA = +5 Dbtr structured nodes + 1 OBPM4 row. CGI = no tree edits, only Pattern A BAdI 3-line guard. CITI = +5 Dbtr structured nodes (Cdtr exits already structured). UltmtCdtr Worldlink → V002 deferred.",
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": [{"type": "empirical", "ref": "Phase 1 complete extraction batch 2026-04-25 + 2 expert agents re-evaluation", "cite": "9/15 CITIPMW FMs extracted; remaining 6 classified non-blocking.", "added_session": 62, "migrated_from_legacy": False}],
        "evidence_against": None,
        "related_objects": ["/SEPA_CT_UNES", "/CGI_XML_CT_UNESCO", "/CITI/XML/UNESCO/DC_V3_01", "YCL_IDFI_CGI_DMEE_FALLBACK"],
        "domain": "Payment",
        "created_session": 62,
        "resolved_session": 62,
        "resolution_notes": "No more extractions needed. Phase 2 ready to start once user-action items complete (TRM outreach, N_MENARD alignment).",
        "status": "active",
        "domain_axes": {"functional": ["Payment"], "module": ["FI"], "process": ["P2P", "T2R"]}
    },
]

existing = {c["id"] for c in claims}
added = 0
for nc in new_claims:
    if nc["id"] not in existing:
        claims.append(nc)
        added += 1

with open('brain_v2/claims/claims.json','w',encoding='utf-8') as f:
    json.dump(claims, f, indent=2, ensure_ascii=False)
print(f"Claims: +{added} (total {len(claims)})")
