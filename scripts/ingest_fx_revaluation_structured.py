# Convert the FX revaluation prose analysis into STRUCTURED brain records
# (incident + claims) so the curation promotes SAPF100/T030H/accounts into brain_state.
import json, io, os
ROOT = r"C:\Users\jp_lopez\projects\abapobjectscreation"
INC = os.path.join(ROOT, "brain_v2", "incidents", "incidents.json")
CLA = os.path.join(ROOT, "brain_v2", "claims", "claims.json")

DOC = "knowledge/domains/Closing_Activities/fx_revaluation_process.md"
RELATED = [
    "SAPF100", "T030H", "OB09", "F.05", "SKB1", "GLT0", "BSEG", "BKPF",
    "0001010574", "0001010571", "0001110574", "0001110571",
    "0001109574", "0001109571", "0001143254", "0001194316",
    "1094316", "1194316",  # Ecobank (the working example)
    "UNES_UNBA", "UNES_DEPOSIT",
]

incidents = json.load(io.open(INC, encoding="utf-8"))
claims = json.load(io.open(CLA, encoding="utf-8"))

# remove prior version if rerun (idempotent)
incidents = [i for i in incidents if i.get("id") != "INC-FXREVAL-OB09"]
claims = [c for c in claims if c.get("id") not in (205, 206, 207, 208)]

new_claims = [
    {"id": 205,
     "claim": "UNESCO revalues bank accounts (F.05/SAPF100) via two valid patterns: self-revaluation (HKONT=LKORR, 277 active accts) or a main+sub-account design (BK main posts its FX balance-sheet adjustment to a paired active S-BK sub, 163 active accts). Ecobank does this correctly: 1094316 -> LKORR 1194316 (active sub).",
     "claim_type": "verified_fact", "confidence": "TIER_1",
     "evidence_for": [{"type": "table_query", "ref": "T030H x SKB1 (P01)", "cite": "944 distinct HKONTs in T030H KTOPL=UNES; 555 self-ref (277 active), 167 sub-account (163 active), 6 point to a closed sub, 200 empty."}],
     "evidence_against": [], "related_objects": RELATED, "domain": "Closing Activities",
     "created_session": 79, "status": "active", "domain_axes": ["FI", "Treasury"]},
    {"id": 206,
     "claim": "ROOT CAUSE of 'Account 1109574 blocked for posting' in F.05: an UNFINISHED bank sub-account migration in OB09. Banco de Chile mains 0001010574 (CLP) and 0001010571 (USD) still point their balance-sheet adjustment (LKORR) to the CLOSED sub 1109574/1109571 instead of the active sub 1110574/1110571. F.05 cannot post to the blocked sub and aborts.",
     "claim_type": "verified_fact", "confidence": "TIER_1",
     "evidence_for": [{"type": "config_screen", "ref": "OB09 / FS00 (P01)", "cite": "OB09 for 1010574: Val.loss/gain 6045011/7045011 (active); Bal.sheet adj 1109574 (XSPEB=X, 'CLOSED S-BK BANCO DE CHILE'). Active sub 1110574 exists (main+100000) but OB09 not repointed."}],
     "evidence_against": [], "related_objects": RELATED, "domain": "Closing Activities",
     "created_session": 79, "status": "active", "domain_axes": ["FI", "Treasury"]},
    {"id": 207,
     "claim": "FIX for the F.05 'blocked for posting' error = repoint OB09 (KDF) for the 2 in-scope accounts to the active sub: 0001010574 -> 1110574, 0001010571 -> 1110571 (matching Ecobank). Do NOT unblock the closed subs (retired on purpose). Only 2 accounts are inside the failing variant ranges (1000000-1099999); other mis-pointed accounts are out of scope.",
     "claim_type": "verified_fact", "confidence": "TIER_1",
     "evidence_for": [{"type": "table_query", "ref": "T030H ranges + GLT0 balances (P01)", "cite": "Of 6 mis-pointed accounts only 1010574/1010571 fall in variant range 1000000-1099999; both carry FX balances (GLT0 FY2026: 164,918 / 20,096 USD)."}],
     "evidence_against": [], "related_objects": RELATED, "domain": "Closing Activities",
     "created_session": 79, "status": "active", "domain_axes": ["FI", "Treasury"]},
    {"id": 208,
     "claim": "F.05/SAPF100 runs interactively at UNESCO with ZERO background jobs; it builds a batch-input session (SM35) processed by SAPF180 to make FBB1 postings. The improvement opportunity is to schedule SM36 jobs (template: SAPF124 clearing already runs daily as JOBBATCH) to remove missed months, timing lag, single-point-of-failure and the absence of a sign-off gate.",
     "claim_type": "verified_fact", "confidence": "TIER_1",
     "evidence_for": [{"type": "table_query", "ref": "BKPF/APQI (P01)", "cite": "0 SAPF100 jobs in TBTCO; FBB1 docs have human USNAM not JOBBATCH; SAPF180/UNES sessions in APQI."}],
     "evidence_against": [], "related_objects": ["SAPF100", "SAPF180", "SAPF124", "F.05", "BKPF"],
     "domain": "Closing Activities", "created_session": 79, "status": "active", "domain_axes": ["FI", "Treasury"]},
]

new_incident = {
    "id": "INC-FXREVAL-OB09",
    "status": "ROOT_CAUSE_CONFIRMED",
    "title": "F.05 FX revaluation: 'Account 1109574 blocked for posting' (Banco de Chile)",
    "reporter": "Treasury (via session screenshot)",
    "received_date": "2026-06-07",
    "analyzed_session": 78,
    "domain": "Closing Activities",
    "secondary_domains": ["Treasury", "FI"],
    "transactions": ["F.05", "OB09", "FS00", "FS10N"],
    "primary_object_id": "0001109574",
    "primary_subject": "FX revaluation balance-sheet adjustment account blocked",
    "company_codes_involved": ["UNES"],
    "scenario": "F.05/SAPF100 (variant UNES_UNBA) revalues active CLP/USD Banco de Chile bank accounts. It posts the FX balance-sheet adjustment to the account configured in OB09/T030H (LKORR). That account is the CLOSED sub 1109574/1109571, blocked for posting.",
    "error_messages": ["Account 1109574 UNES is blocked for posting"],
    "root_cause_summary": "Unfinished bank sub-account migration. The Banco de Chile sub was retired (old 1109574 closed -> new 1110574 created) but OB09 was never repointed; the active main still points its LKORR adjustment to the closed sub. Two conditions needed for the runtime error: (1) OB09 points to a blocked sub AND (2) the main carries an FX balance to revalue.",
    "code_validation_chain": "F.05 -> SAPF100 -> T030H (KDF account determination) -> LKORR=1109574 -> SKB1.XSPEB='X' -> post aborts.",
    "scope": "2 accounts in the failing variant range (1010574 CLP, 1010571 USD); 4 more share the defect but are out of variant scope.",
    "fix_path": "OB09/KDF: repoint 0001010574 -> 1110574 and 0001010571 -> 1110571 (active subs, like Ecobank 1094316->1194316). Do NOT unblock the closed subs. Confirm migration target with Treasury.",
    "related_objects": RELATED,
    "related_claims": [
        {"id": 205, "claim": "Two valid revaluation patterns: self-ref vs main+sub-account (Ecobank correct)."},
        {"id": 206, "claim": "Root cause = unfinished OB09 sub-account migration (main -> closed sub)."},
        {"id": 207, "claim": "Fix = repoint OB09 to the active sub for the 2 in-scope accounts."},
        {"id": 208, "claim": "F.05 runs interactively with 0 jobs; SM36 automation is the bigger opportunity."},
    ],
    "related_dq": [],
    "related_known_unknowns": ["KU-CA-001 (confirm migration target 1110574/1110571)", "KU-CA-002 (confirm _UNBA valuation mode)"],
    "analysis_doc": DOC,
    "evidence_extracted_this_incident": "T030H config, SKB1 block flags, T012K house-bank map, GLT0 balances, OB09/FS00 screens, variant ranges, BKPF/BSIS execution.",
    "lessons": "Closing-account migrations must repoint OB09 (house-bank closure Step 4). Balance source = GLT0/FAGLFLEXT, not BSIS sums. Currency from SKAT name, not SKB1.WAERS.",
    "open_followups": ["Repoint OB09 (2 entries)", "Fix Citibank/Ecobank mis-mappings in same pass", "Schedule SM36 jobs for SAPF100"],
    "chain_anchor_type": "config_table",
    "chain_anchor_note": "Anchored on T030H/OB09 account determination.",
    "chain_anchor_coverage_pct": 95,
    "chain_audited_session": 78,
    "domain_axes": ["FI", "Treasury"],
}

incidents.append(new_incident)
claims.extend(new_claims)

json.dump(incidents, io.open(INC, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(claims, io.open(CLA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"Added incident INC-FXREVAL-OB09 + claims 205-208.")
print(f"  incidents now: {len(incidents)} | claims now: {len(claims)}")
print(f"  related_objects force-included: {len(RELATED)} names incl. SAPF100, T030H, OB09, accounts")
