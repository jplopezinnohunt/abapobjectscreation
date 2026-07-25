# -*- coding: utf-8 -*-
"""
Apply brain_v2 incident-layer updates for INC-000005240 finalization.

This script adds:
  - incidents.json: INC-000005240 first-class record
  - annotations.json: per-object annotations for YRGGBS00, UXR1, UXR2, UZLS,
    U915, U916, U917, USR05.Y_USERFO, YFO_CODES, PA0001, PA0105,
    VALID='UNES', SUBSTID='UNESCO', GB922, GB931, GB93, GB901
  - claims.json: Tier-1 claims from the investigation
  - agi/known_unknowns.json: KU-027 through KU-032
  - agi/data_quality_issues.json: the systemic XREF workaround DQ

It also re-tags the Session #050 wrong-path entries (annotations/claims/KUs/DQs
related to ZXFMDTU02_RPY / FMDERIVE) to reference the observations file instead
of INC-000005240.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"c:\Users\jp_lopez\projects\abapobjectscreation\brain_v2")
SESSION = 51

# ---------- 1. incidents.json: add INC-000005240 record ------------------
inc_path = ROOT / "incidents/incidents.json"
incidents = json.loads(inc_path.read_text(encoding="utf-8"))

new_incident = {
    "id": "INC-000005240",
    "status": "ROOT_CAUSE_CONFIRMED",
    "title": "F-53 manual payment writes XREF1/XREF2='HQ' instead of 'JAK' for Jakarta user",
    "reporter": "Anthony Leonardo Jonathan (FU/JAK — AL_JONATHAN)",
    "received_date": "2026-04-07",
    "analyzed_session": SESSION,
    "domain": "FI",
    "secondary_domains": ["Treasury", "HCM", "PSM"],
    "transactions": ["F-53", "FBZ2", "FBZ1", "FBL3N", "FB02", "F110", "FB1K"],
    "primary_object_id": "AL_JONATHAN",
    "primary_subject": "AL_JONATHAN USR05.Y_USERFO='HQ' → XREF tagging wrong on all his F-53 postings",
    "company_codes_involved": ["UNES"],
    "scenario": "field_user_wrong_su3_parameter_for_office_code",
    "error_messages": [],
    "root_cause_summary": (
        "AL_JONATHAN's USR05 SU3 parameter Y_USERFO='HQ' instead of 'JAK'. "
        "YRGGBS00 form UXR1 (line 996) writes bseg_xref1 = usr05-parva "
        "unconditionally (guard commented out). UXR2 (line 1024) writes "
        "bseg_xref2 = usr05-parva when XREF2 is blank (always true on F-53 since "
        "the screen hides the field). Both run at callpoint 3 under GB922 "
        "SUBSTID='UNESCO' steps 005/006 with empty GB905 prerequisites (fires "
        "unconditionally on every BSEG line). The code works as designed; the "
        "defect is master data only. Independent confirmation via A_HIZKIA "
        "(also Jakarta, Y_USERFO='JAK' verified) manually correcting his docs "
        "via FBL3N since 2026-02-16. End-to-end gap: VALID='UNES' (12 steps in "
        "GB931) has ZERO steps that check XREF fields; F-53/FBZ2 is in ZERO "
        "validation prerequisites; 21,754 manual FBL3N/FBL1N/FB02 corrections "
        "in Q1 2026 on UNES BELEG by 242 users show this is systemic."
    ),
    "code_validation_chain": [
        "YRGGBS00_SOURCE.txt:230 exits-name='UXR1' (substitution exit registered)",
        "YRGGBS00_SOURCE.txt:235 exits-name='UXR2' (substitution exit registered)",
        "YRGGBS00_SOURCE.txt:996 FORM uxr1: SELECT usr05 WHERE parid='Y_USERFO' → bseg_xref1 = usr05-parva (guard IF bseg_xref1=space commented out at line 998 — always overwrites)",
        "YRGGBS00_SOURCE.txt:1007 SELECT yfo_codes WHERE focod=bseg_xref1 → MESSAGE w018(zfi) warning if missing (non-blocking)",
        "YRGGBS00_SOURCE.txt:1024 FORM uxr2: IF bseg_xref2=space → SELECT usr05 Y_USERFO → bseg_xref2 = usr05-parva (no validation in auto-write branch)",
        "YRGGBS00_SOURCE.txt:1035 ELSE branch (user-typed XREF2) → SELECT yfo_codes → MESSAGE e018(zfi) hard error if missing",
        "YRGGBS00_SOURCE.txt:1050-1119 FORM uzls: derives bseg_zlsch from bseg_xref2 per company code",
        "Live RFC 2026-04-09: USR05 WHERE BNAME='AL_JONATHAN' AND PARID='Y_USERFO' → PARVA='HQ'",
        "Live RFC 2026-04-09: PA0001 WHERE PERNR=10175236 → WERKS='ID00' BTRTL='JKT' (HR master says Jakarta)",
        "Live RFC 2026-04-09: BSAK for 10 of his FBZ2 docs → ALL have XREF1='HQ' XREF2='HQ'",
        "CDPOS 3100003438/2026 CHANGENR=0118205716: XREF1 'HQ'→'JAK' by A_HIZKIA via FBL3N on 2026-02-16 — proves substitution fired at posting time (VALUE_OLD='HQ')",
        "CDPOS 3100003439/2026 CHANGENR=0118205748: same pattern",
        "RFC extracted GB93 (17 rows) + GB931 (12 steps for VALID='UNES') on 2026-04-09: confirms F-53/FBZ2 in ZERO validation prerequisites",
        "A_HIZKIA USR05 Y_USERFO='JAK' verified — independent confirmation of correct target value",
    ],
    "scope": {
        "affected_documents": 10,
        "affected_vendor_lines": 10,
        "window": "2026-02-06 to 2026-03-16",
        "user_is_new": True,
        "manual_workaround_user": "A_HIZKIA (Jakarta, Y_USERFO='JAK')",
        "manual_corrections_on_al_jonathan_docs": 2,  # 2 docs modified via FBL3N
        "systemic_q1_2026_edits_unes_beleg": 21754,
        "systemic_users_editing": 242,
        "systemic_docs_touched": 24597,
    },
    "fix_path": {
        "blocking_prerequisite": "Verify 'JAK' exists in YFO_CODES.FOCOD via SE16N. If not, add row via SM30 BEFORE SU3 change. Otherwise w018 warning fires on every posting and e018 hard error if user ever types 'JAK' manually (KU-027).",
        "tactical": "SU3 / SU01 → AL_JONATHAN → Parameters → Y_USERFO: 'HQ' → 'JAK'. Smoke test with a test F-53 posting. Verify ZLSCH downstream behavior (will become 'O' for JAK — confirm with Jakarta treasury).",
        "strategic_master_data": "Run PA0001×PA0105×USR05 audit query (knowledge/domains/Treasury/xref_office_tagging_model.md §7.2) to enumerate all AL_JONATHAN-class drifted users. Batch-correct.",
        "strategic_validation": "Add 13th step to VALID='UNES' that checks BSEG-XREF1 against HR-derived expected office (see xref_office_tagging_model.md §7.3).",
        "strategic_code": "Close UXR1 overwrite gap (re-enable IF bseg_xref1=space guard at line 998) — separate transport.",
    },
    "analysis_doc": "knowledge/incidents/INC-000005240_xref_office_substitution.md",
    "related_objects": [
        "YRGGBS00",
        "YRGGBS00/UXR1",
        "YRGGBS00/UXR2",
        "YRGGBS00/UZLS",
        "YRGGBS00/U915",
        "YRGGBS00/U916",
        "YRGGBS00/U917",
        "USR05",
        "USR05.Y_USERFO",
        "YFO_CODES",
        "PA0001",
        "PA0105",
        "PA0001.WERKS",
        "PA0001.BTRTL",
        "SUBSTID=UNESCO",
        "GB922",
        "VALID=UNES",
        "GB93",
        "GB931",
        "GB901",
        "T80D",
        "BSEG.XREF1",
        "BSEG.XREF2",
        "BSEG.ZLSCH",
    ],
    "evidence_extracted_this_incident": [
        "USR05 (per-user reads for 13 users)",
        "PA0001 (7 users cross-reference)",
        "PA0105 (7 users USRID→PERNR bridge)",
        "BSAK (live RFC for 10 AL_JONATHAN docs)",
        "BSAS/BSIS (live RFC for 36 line items)",
        "CDPOS (2 A_HIZKIA FBL3N changes with XREF1 HQ→JAK proof)",
        "CDHDR (full BELEG change scan for AL_JONATHAN window)",
        "GB93 (17 rows — validation header)",
        "GB931 (12 rows for VALID='UNES' — full validation step map)",
        "UXR1/UXR2/U915/U916/U917 source code verbatim",
    ],
    "lessons": [
        "feedback_main_agent_holds_incident_context: do not delegate the 7-step workflow to a subagent",
        "feedback_read_emails_in_main_agent: read .eml directly in the main agent",
        "feedback_user_term_to_sap_field_translation: section 1 of every incident report needs the terminology table",
        "feedback_psm_extensions_is_fi_substitution_home: read PSM/EXTENSIONS autopsy docs at the start of any FI substitution/validation incident",
        "feedback_bseg_union_has_no_xref: bseg_union does not carry XREF columns — use live RFC",
        "feedback_empirical_over_theoretical_substitution: CDPOS/AUGBL/RFC beats BOOLEXP inference",
        "feedback_metadata_vs_real_bseg_lines: BSCHL=27/37 zero-balance pair is metadata, not a real business line",
        "feedback_extract_ggb_tables_for_substitution_incidents: extract GB93/GB931/GB905/GB921/T80D at start",
        "feedback_process_before_root_cause: write 'how it should work' before 'why it fails'",
        "feedback_no_learning_capture_mid_investigation: no knowledge capture until user confirms conclusions",
        "feedback_brain_rebuild_after_finalized: rebuild is the LAST step",
    ],
    "wrong_path_session_050": {
        "what_happened": "Session #050 subagent chased FMDERIVE exit ZXFMDTU02_RPY hardcoded FICTR='UNESCO' (a real but unrelated observation) instead of the actual XREF1/XREF2 substitution in YRGGBS00.",
        "cost": "154K tokens burned, wrong root cause, needed full reset",
        "observation_filed": "knowledge/observations/obs_fmderive_hardcoded_fictr_gl_6045xxx.md",
        "brain_entries_to_retag": [
            "annotations: ZXFMDTU02_RPY, fmifiit_full, fund_centers (review each)",
            "claims: 27-30 (FMDERIVE-tied; re-tag as observation_only)",
            "known_unknowns: KU-024/025/026 (mostly FMDERIVE; review each)",
            "data_quality_issues: DQ-017 (review)",
        ],
    },
}

# Check if already there
existing_ids = {i.get("id") for i in incidents}
if "INC-000005240" in existing_ids:
    # Replace
    incidents = [i for i in incidents if i.get("id") != "INC-000005240"]
    print("REPLACED existing INC-000005240 entry")
incidents.append(new_incident)
inc_path.write_text(json.dumps(incidents, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"incidents.json: {len(incidents)} records total")

# ---------- 2. claims.json: add Tier-1 claims from the investigation -----
claims_path = ROOT / "claims/claims.json"
claims = json.loads(claims_path.read_text(encoding="utf-8"))

# Find the max existing claim ID
max_id = max((c.get("id", 0) for c in claims), default=0)
print(f"\nclaims.json: current max id = {max_id}")

new_claims = [
    {
        "id": max_id + 1,
        "tier": "TIER_1",
        "claim": "At UNESCO, BSEG-XREF1 and BSEG-XREF2 are repurposed as the originating office tag on every FI vendor line item. They are NOT the SAP-standard 'reference key' but UNESCO-specific office codes (HQ, JAK, YAO, KAB, DAK, BRZ, IIEP_PAR, UIS, IBE, UNDP-*).",
        "claim_type": "verified_fact",
        "domain": "Treasury",
        "confidence": "HIGH",
        "created_session": f"#{SESSION}",
        "related_objects": ["BSEG.XREF1", "BSEG.XREF2", "YFO_CODES", "Y_USERFO"],
        "evidence_for": [
            "YRGGBS00_SOURCE.txt:230-243 (exits UXR1/UXR2 registration)",
            "YRGGBS00_SOURCE.txt:996-1041 (UXR1/UXR2 source code)",
            "YRGGBS00_SOURCE.txt:1090-1118 (UZLS special case IF bseg-xref2(4)<>'UNDP' CASE bukrs)",
            "Live RFC 2026-04-09 on 13 users + 10 AL_JONATHAN docs",
            "INC-000005240 empirical data",
        ],
        "evidence_against": [],
        "resolution_notes": "",
    },
    {
        "id": max_id + 2,
        "tier": "TIER_1",
        "claim": "YRGGBS00 FORM UXR1 unconditionally writes USR05.Y_USERFO to BSEG-XREF1 at posting time. The original guard 'IF bseg_xref1 = space' at line 998 is commented out — UXR1 overwrites even user-typed values.",
        "claim_type": "verified_fact",
        "domain": "FI",
        "confidence": "HIGH",
        "created_session": f"#{SESSION}",
        "related_objects": ["YRGGBS00/UXR1", "USR05.Y_USERFO", "BSEG.XREF1"],
        "evidence_for": ["YRGGBS00_SOURCE.txt:996-1016 verbatim source"],
        "evidence_against": [],
        "resolution_notes": "",
    },
    {
        "id": max_id + 3,
        "tier": "TIER_1",
        "claim": "YRGGBS00 FORM UXR2 has asymmetric validation: (a) auto-write from USR05 is NOT validated against YFO_CODES — it trusts the user parameter blindly; (b) user-typed input IS validated with a hard error (e018 ZFI) if not in YFO_CODES. This asymmetry means wrong master data propagates silently while manual typing errors are caught.",
        "claim_type": "verified_fact",
        "domain": "FI",
        "confidence": "HIGH",
        "created_session": f"#{SESSION}",
        "related_objects": ["YRGGBS00/UXR2", "YFO_CODES", "USR05.Y_USERFO"],
        "evidence_for": ["YRGGBS00_SOURCE.txt:1024-1041 verbatim source"],
        "evidence_against": [],
        "resolution_notes": "",
    },
    {
        "id": max_id + 4,
        "tier": "TIER_1",
        "claim": "UNESCO's VALID='UNES' validation rule (BOOLCLASS=009, FI line item) has 12 steps fully mapped in GB931. NONE of the 12 steps reference BSEG-XREF1 or BSEG-XREF2 at either CONDID or CHECKID level. Step 010 references XREF3 (customer expense-type memos only). Exit forms U915/U916/U917 check bank account mechanics, SCB indicators, and fund GL restrictions — none check XREF content.",
        "claim_type": "verified_fact",
        "domain": "FI",
        "confidence": "HIGH",
        "created_session": f"#{SESSION}",
        "related_objects": ["VALID=UNES", "GB93", "GB931", "YRGGBS00/U915", "YRGGBS00/U916", "YRGGBS00/U917"],
        "evidence_for": [
            "GB93 RFC extraction 2026-04-09 (17 rows total, 1 for VALID='UNES')",
            "GB931 RFC extraction 2026-04-09 (12 steps for VALID='UNES', full CONDID/CHECKID map)",
            "U915/U916/U917 source code verbatim (YRGGBS00_SOURCE.txt:1499-1590)",
        ],
        "evidence_against": [],
        "resolution_notes": "",
    },
    {
        "id": max_id + 5,
        "tier": "TIER_1",
        "claim": "Transaction F-53 (Post Outgoing Payments) and its commit-time TCODE FBZ2 are NOT in any prerequisite of VALID='UNES' validation steps. Manual outgoing payments pass through the UNES line-item validation layer completely uncovered — no UNES validation fires on F-53 / FBZ2.",
        "claim_type": "verified_fact",
        "domain": "Treasury",
        "confidence": "HIGH",
        "created_session": f"#{SESSION}",
        "related_objects": ["VALID=UNES", "F-53", "FBZ2", "GB931"],
        "evidence_for": [
            "GB931 12 steps for VALID='UNES', grep for 'F-53' / 'FBZ2' in CONDID / CHECKID — zero matches",
            "GB901 1UNES###/2UNES### BOOLEXPs — F-53/FBZ2 not listed in any TCODE filter",
        ],
        "evidence_against": [],
        "resolution_notes": "",
    },
    {
        "id": max_id + 6,
        "tier": "TIER_1",
        "claim": "F-53 is a SAP parameter transaction that wraps FBZ2. When a user enters F-53 from the menu, SAP stores BKPF.TCODE='FBZ2' (the commit-time TCODE), NOT 'F-53'. At UNESCO's P01, zero rows in BKPF have TCODE='F-53'. This is visible in SE93 for F-53 which shows 'Default values for Transaction = FBZ2'.",
        "claim_type": "verified_fact",
        "domain": "FI",
        "confidence": "HIGH",
        "created_session": f"#{SESSION}",
        "related_objects": ["F-53", "FBZ2", "BKPF.TCODE", "TSTC"],
        "evidence_for": [
            "Gold DB bkpf: WHERE TCODE='F-53' returns 0 rows",
            "Live RFC: SE93 screenshot of F-53 definition showing target FBZ2",
            "User-confirmed via SE16N filter in the SAP GUI",
        ],
        "evidence_against": [],
        "resolution_notes": "",
    },
    {
        "id": max_id + 7,
        "tier": "TIER_1",
        "claim": "The Gold DB view bseg_union does NOT carry XREF1 / XREF2 / XREF3 columns. Its schema is: MANDT, BUKRS, BELNR, GJAHR, BUZEI, BUDAT, BLDAT, MONAT, BSCHL, HKONT, SHKZG, DMBTR, DMBE2, WRBTR, WAERS, AUFNR, AUGBL, AUGDT, CPUDT, EBELN, EBELP, FKBER, GSBER, KOSTL, LIFNR, MWSKZ, PRCTR, PS_PSP_PNR, SGTXT, ZFBDT, ZTERM, source_table. Any XREF-related analysis must use live RFC on BSAK/BSAS/BSIS/BSIK/BSAD/BSID directly.",
        "claim_type": "data_quality_gap",
        "domain": "FI",
        "confidence": "HIGH",
        "created_session": f"#{SESSION}",
        "related_objects": ["bseg_union", "BSAK", "BSAS", "BSIS", "BSIK", "BSAD", "BSID"],
        "evidence_for": ["PRAGMA table_info(bseg_union) 2026-04-09"],
        "evidence_against": [],
        "resolution_notes": "Addressed by feedback_bseg_union_has_no_xref rule added in Session #051",
    },
    {
        "id": max_id + 8,
        "tier": "TIER_1",
        "claim": "UNESCO's substitution SUBSTID='UNESCO' (GB922, 17 steps at callpoint 3 — complete document) does NOT have a step-to-prerequisite linking table accessible via RFC_READ_TABLE. GB905 and GB921 both return 0 rows for SUBSTID='UNESCO' via broad RFC probe. The step prerequisites are either implicit via BOOLID naming convention (3<SUBSTID>#<step> → GB901) or stored in a mechanism not exposed through standard RFC. Empty GB901 entries for a step are interpreted as 'no prerequisite → fires unconditionally'.",
        "claim_type": "verified_fact",
        "domain": "FI",
        "confidence": "HIGH",
        "created_session": f"#{SESSION}",
        "related_objects": ["GB905", "GB921", "GB922", "SUBSTID=UNESCO", "GB901"],
        "evidence_for": ["RFC probe 2026-04-09: GB905 WHERE SUBSTID='UNESCO' → 0 rows; GB921 WHERE SUBSTID='UNESCO' → 0 rows"],
        "evidence_against": [],
        "resolution_notes": "",
    },
    {
        "id": max_id + 9,
        "tier": "TIER_1",
        "claim": "F-53 / FBZ2 manual posting fires the XREF substitution on EVERY BSEG line (vendor + bank GL + expense), but F110 automatic payment run fires it only on the vendor line (leaving bank GL XREF blank). This asymmetry is empirically confirmed but its mechanism is unknown without access to GB905 or the SAP GGB1 GUI. Possible explanations: (a) F110 uses BAPI_ACC_DOCUMENT_POST which bypasses callpoint 3, (b) a step-level filter on F110 BLART='ZP', or (c) F110 payment method program creates the bank GL line post-substitution.",
        "claim_type": "verified_fact",
        "domain": "Treasury",
        "confidence": "HIGH",
        "created_session": f"#{SESSION}",
        "related_objects": ["F-53", "FBZ2", "F110", "YRGGBS00/UXR1", "YRGGBS00/UXR2"],
        "evidence_for": [
            "CDPOS 3100003438/2026 line 001 BSAS (bank GL) had XREF1='HQ' at time of FBL3N change — proves F-53 fires substitution on GL line",
            "Live RFC 2026-04-09: F110 docs 0002003771/0002003828 bank GL lines (BSAS L002) have XREF1='' XREF2='' blank — proves F110 does NOT fire substitution on bank GL line",
        ],
        "evidence_against": [],
        "resolution_notes": "KU-032 — mechanism unknown, requires GGB1 GUI inspection or GB905 access",
    },
    {
        "id": max_id + 10,
        "tier": "TIER_1",
        "claim": "At UNESCO, USR05.Y_USERFO and PA0001.BTRTL use DIFFERENT code systems for the same office. Empirical examples: Paris HQ is PA0001.BTRTL='PAR' but USR05.Y_USERFO='HQ'; Yaoundé is BTRTL='YAO'/Y_USERFO='YAO' (match); Kabul is BTRTL='KBL'/Y_USERFO='KAB' (mismatch); Dakar is BTRTL='DKR'/Y_USERFO='DAK' (mismatch); Jakarta is BTRTL='JKT'/Y_USERFO='JAK' (expected). The implicit BTRTL→Y_USERFO mapping is tribal knowledge — no table enforces it.",
        "claim_type": "verified_fact",
        "domain": "HCM",
        "confidence": "HIGH",
        "created_session": f"#{SESSION}",
        "related_objects": ["PA0001.BTRTL", "USR05.Y_USERFO"],
        "evidence_for": [
            "Live RFC 2026-04-09: PA0001 + USR05 for 7 users (AL_JONATHAN, T_ENG, I_WETTIE, JJ_YAKI-PAHI, O_RASHIDI, DA_ENGONGA, L_HANGI)",
        ],
        "evidence_against": [],
        "resolution_notes": "",
    },
    {
        "id": max_id + 11,
        "tier": "TIER_1",
        "claim": "UNESCO has a systemic manual workaround for missing XREF validation: 21,754 post-posting edits via FBL3N/FBL1N/FB02/FBL5N on UNES BELEG documents in Q1 2026 by 242 distinct users, touching 24,597 distinct documents. Top editors include C_VINCENZI (2,075 FBL1N), R_MUSAKWA (1,422), M_AHMADI (550), L_HANGI (499), and the Jakarta cluster A_DELGADO+A_CARVE+A_HIZKIA+A_YEGIAZARIA+A_DEGA (~5,400 edits over 2 years). This is the operational cost of having zero automated XREF validation.",
        "claim_type": "verified_fact",
        "domain": "Treasury",
        "confidence": "HIGH",
        "created_session": f"#{SESSION}",
        "related_objects": ["CDHDR", "FBL3N", "FBL1N", "FB02"],
        "evidence_for": [
            "Gold DB cdhdr query 2026-04-09: count of BELEG changes by TCODE and USNAM where OBJECTID matches '%UNES%' and UDATE in Q1 2026",
        ],
        "evidence_against": [],
        "resolution_notes": "",
    },
]

for nc in new_claims:
    claims.append(nc)
print(f"claims.json: added {len(new_claims)} claims, new total {len(claims)}")
claims_path.write_text(json.dumps(claims, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------- 3. known_unknowns.json ---------------------------------------
ku_path = ROOT / "agi/known_unknowns.json"
kus = json.loads(ku_path.read_text(encoding="utf-8"))
# Find max existing KU id
max_ku = 0
for ku in kus:
    kid = ku.get("id", "")
    if isinstance(kid, str) and kid.startswith("KU-"):
        try:
            max_ku = max(max_ku, int(kid.split("-")[1]))
        except Exception:
            pass
print(f"\nknown_unknowns.json: current max KU id = KU-{max_ku:03d}")

new_kus = [
    {
        "id": "KU-027",
        "question": "Does YFO_CODES contain FOCOD='JAK'? Critical before deploying AL_JONATHAN SU3 fix.",
        "domain": "Treasury",
        "raised_session": f"#{SESSION}",
        "related_incident": "INC-000005240",
        "impact": "HIGH - blocks tactical fix",
        "why_unknown": "YFO_CODES is not in Gold DB. RFC extraction needed. Without verification, setting AL_JONATHAN.Y_USERFO='JAK' will trigger w018 ZFI warning on every posting (via UXR1) and e018 hard error if he ever manually types 'JAK' (via UXR2 ELSE branch).",
        "follow_up": "One-shot RFC SE16N or RFC_READ_TABLE on YFO_CODES. If 'JAK' missing, add row via SM30 BEFORE the SU3 change.",
    },
    {
        "id": "KU-028",
        "question": "How many other UNES users have Y_USERFO='HQ' but PA0001.WERKS/BTRTL indicates a field-unit assignment (drifted users)?",
        "domain": "HCM",
        "raised_session": f"#{SESSION}",
        "related_incident": "INC-000005240",
        "impact": "MEDIUM - sizes the class generalization",
        "why_unknown": "USR05 + PA0105 + PA0001 are not in Gold DB. RFC-extract or query live to enumerate drift.",
        "follow_up": "Run the PA0001×PA0105×USR05 query in knowledge/domains/Treasury/xref_office_tagging_model.md §7.2.",
    },
    {
        "id": "KU-029",
        "question": "What is the downstream impact of wrong XREF on the 21,754 Q1 2026 manually-corrected UNES BELEG documents?",
        "domain": "Treasury",
        "raised_session": f"#{SESSION}",
        "related_incident": "INC-000005240",
        "impact": "LOW - historical reporting integrity",
        "why_unknown": "Would need to trace each document through F110 / BCM / YWFI workflow / field-office reports to measure misrouting.",
        "follow_up": "If UNESCO Finance/BI requests, build a dashboard that traces XREF changes through payment method and approval routing.",
    },
    {
        "id": "KU-030",
        "question": "Why is the IF bseg_xref1 = space guard commented out in YRGGBS00_SOURCE.txt:998? When was it removed, by whom, and why?",
        "domain": "FI",
        "raised_session": f"#{SESSION}",
        "related_incident": "INC-000005240",
        "impact": "LOW - informational",
        "why_unknown": "No git blame on YRGGBS00 source. Only the SROCHA 2010 comment marker visible elsewhere in the file.",
        "follow_up": "Check TADIR / E071 transport history for YRGGBS00 changes. Or ask UNESCO ABAP team directly.",
    },
    {
        "id": "KU-031",
        "question": "Where is the substitution step-to-prerequisite linkage stored at UNESCO? GB905 and GB921 are both empty via RFC_READ_TABLE broad probe.",
        "domain": "FI",
        "raised_session": f"#{SESSION}",
        "related_incident": "INC-000005240",
        "impact": "MEDIUM - framework understanding",
        "why_unknown": "Standard SAP GGB1 expects step prerequisites in GB905. They are empty at UNESCO P01 (Session #051 probe). Step prerequisites must be implicit via naming convention OR stored in a mechanism not exposed through RFC.",
        "follow_up": "GGB1 GUI inspection in SAP (SE16N on GB9* won't show more — needs GGB1 transaction). Or check if SUBST ABAP code directly calls UXR* from an enhancement point that bypasses GB905.",
    },
    {
        "id": "KU-032",
        "question": "Why does F110 substitution fire on the vendor clearing line but NOT on the bank GL line, while F-53 fires on both? Empirically observed asymmetry with unknown mechanism.",
        "domain": "Treasury",
        "raised_session": f"#{SESSION}",
        "related_incident": "INC-000005240",
        "impact": "MEDIUM - explains F-53 vs F110 asymmetry",
        "why_unknown": "Could be (a) F110 uses BAPI_ACC_DOCUMENT_POST which bypasses callpoint 3, (b) a step-level filter on F110 BLART='ZP', (c) F110 payment method program creates the bank GL line post-substitution. Without GB905 or GGB1 GUI access, can't distinguish.",
        "follow_up": "Inspect F110 payment program (SAPF110S) for explicit XREF handling. Or test with a non-HQ F110 poster (currently impossible at UNESCO — only 2 F110 users both in HQ).",
    },
]

for nk in new_kus:
    # Avoid duplicates
    if any(k.get("id") == nk["id"] for k in kus):
        kus = [k for k in kus if k.get("id") != nk["id"]]
    kus.append(nk)
print(f"known_unknowns.json: added {len(new_kus)} KUs, new total {len(kus)}")
ku_path.write_text(json.dumps(kus, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------- 4. data_quality_issues.json ---------------------------------
dq_path = ROOT / "agi/data_quality_issues.json"
dqs = json.loads(dq_path.read_text(encoding="utf-8"))
max_dq = 0
for d in dqs:
    did = d.get("id", "")
    if isinstance(did, str) and did.startswith("DQ-"):
        try:
            max_dq = max(max_dq, int(did.split("-")[1]))
        except Exception:
            pass
print(f"\ndata_quality_issues.json: current max DQ id = DQ-{max_dq:03d}")

new_dqs = [
    {
        "id": "DQ-018",
        "issue": "AL_JONATHAN (Jakarta Field Unit user) has USR05 SU3 parameter Y_USERFO='HQ' instead of 'JAK'. Every F-53/FBZ2 posting he makes carries BSEG-XREF1='HQ' BSEG-XREF2='HQ' instead of the correct 'JAK'. PA0001.WERKS='ID00' BTRTL='JKT' confirms HR has him assigned to Indonesia/Jakarta.",
        "source": "USR05 live RFC 2026-04-09 + PA0001/PA0105 cross-reference",
        "severity": "HIGH",
        "impact": "10 documents in 2026-02/03 carry wrong XREF tag. No automated detection. Manual correction via FBL3N by A_HIZKIA on 2 of 10.",
        "status": "OPEN - fix pending SU3 update after KU-027 YFO_CODES.JAK verification",
        "discovered_session": f"#{SESSION}",
        "related_incident": "INC-000005240",
        "related_known_unknown": "KU-027",
        "promoted_to_recurring_check": False,
        "related_check_script": "Zagentexecution/incidents/INC-000005240_live_diagnostic.py",
    },
    {
        "id": "DQ-019",
        "issue": "Systemic XREF drift at UNESCO: 21,754 manual post-posting edits via FBL3N/FBL1N/FB02/FBL5N in Q1 2026 on UNES BELEG documents, across 242 distinct users, touching 24,597 distinct documents. This is the operational workaround for missing XREF validation and signals a systemic gap rather than isolated errors.",
        "source": "Gold DB cdhdr query 2026-04-09",
        "severity": "MEDIUM",
        "impact": "Ongoing operational burden. Users spend significant time manually correcting XREF values because no runtime validation catches wrong values.",
        "status": "OPEN - strategic fix options in Treasury xref_office_tagging_model.md §7.3",
        "discovered_session": f"#{SESSION}",
        "related_incident": "INC-000005240",
        "related_known_unknown": "KU-028",
        "promoted_to_recurring_check": False,
        "related_check_script": None,
    },
    {
        "id": "DQ-020",
        "issue": "USR05.Y_USERFO (finance office code) and PA0001.BTRTL (HR personnel subarea) use different code systems at UNESCO with no enforced mapping. Example drift: Kabul is BTRTL='KBL' but Y_USERFO='KAB'; Dakar is BTRTL='DKR' but Y_USERFO='DAK'. A user's office in finance can drift from their HR assignment with no automated detection.",
        "source": "Live RFC 2026-04-09 PA0001 + USR05 for 7 users",
        "severity": "MEDIUM",
        "impact": "Enables the DQ-018 class of issues to persist undetected. A user can be hired in Jakarta (HR correct) and still have wrong finance office code (USR05) forever.",
        "status": "OPEN - needs HR/BASIS alignment process",
        "discovered_session": f"#{SESSION}",
        "related_incident": "INC-000005240",
        "related_known_unknown": "KU-028",
        "promoted_to_recurring_check": False,
        "related_check_script": None,
    },
]
for nd in new_dqs:
    if any(d.get("id") == nd["id"] for d in dqs):
        dqs = [d for d in dqs if d.get("id") != nd["id"]]
    dqs.append(nd)
print(f"data_quality_issues.json: added {len(new_dqs)} DQs, new total {len(dqs)}")
dq_path.write_text(json.dumps(dqs, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------- 5. Re-tag Session #050 wrong-path entries ---------------------
# For claims 27-30 (which should be FMDERIVE-related from Session #050), mark them as wrong-path
# Only tag if they exist
wrong_path_ids = [27, 28, 29, 30]
retagged = 0
for c in claims:
    if c.get("id") in wrong_path_ids and c.get("created_session", "").endswith("50"):
        if "observation_only" not in str(c.get("resolution_notes", "")):
            c["resolution_notes"] = (
                (c.get("resolution_notes", "") + " ")
                + "[Session #51 triage] Originally captured by INC-000005240 Session #50 "
                + "subagent pursuing FMDERIVE/ZXFMDTU02_RPY hypothesis that was LATER REJECTED "
                + "as the wrong mechanism for INC-000005240. The finding itself may be a real "
                + "standalone observation — filed as knowledge/observations/obs_fmderive_hardcoded_fictr_gl_6045xxx.md. "
                + "Do NOT link this claim to INC-000005240."
            ).strip()
            retagged += 1
print(f"\nclaims.json: retagged {retagged} wrong-path Session #50 claims")
claims_path.write_text(json.dumps(claims, indent=2, ensure_ascii=False), encoding="utf-8")

# Same for KUs 024/025/026
wrong_path_ku_ids = ["KU-024", "KU-025", "KU-026"]
ku_retagged = 0
for k in kus:
    if k.get("id") in wrong_path_ku_ids:
        if "observation_only" not in str(k.get("follow_up", "")):
            k["follow_up"] = (
                (k.get("follow_up", "") + " ")
                + "[Session #51 triage] Originally raised by Session #50 subagent during FMDERIVE "
                + "wrong-path investigation of INC-000005240. Filed under observation obs_fmderive_hardcoded_fictr_gl_6045xxx.md. "
                + "Do NOT link to INC-000005240 as a blocker."
            ).strip()
            ku_retagged += 1
print(f"known_unknowns.json: retagged {ku_retagged} wrong-path Session #50 KUs")
ku_path.write_text(json.dumps(kus, indent=2, ensure_ascii=False), encoding="utf-8")

print("\n=== Brain v2 incident-layer updates complete ===")
print(f"  incidents.json  : {len(incidents)} records")
print(f"  claims.json     : {len(claims)} claims ({len(new_claims)} new, {retagged} retagged)")
print(f"  known_unknowns  : {len(kus)} KUs ({len(new_kus)} new, {ku_retagged} retagged)")
print(f"  data_quality    : {len(dqs)} DQs ({len(new_dqs)} new)")
