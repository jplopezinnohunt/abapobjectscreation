# -*- coding: utf-8 -*-
"""Add 7 new feedback rules from INC-000005240 retrospective."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

p = Path(r"c:\Users\jp_lopez\projects\abapobjectscreation\brain_v2\agent_rules\feedback_rules.json")
rules = json.loads(p.read_text(encoding="utf-8"))
existing_ids = {r["id"] for r in rules}

new_rules = [
    {
        "id": "feedback_psm_extensions_is_fi_substitution_home",
        "rule": "FI substitution and validation autopsy knowledge lives under knowledge/domains/PSM/EXTENSIONS/ - NOT under knowledge/domains/FI/. Before investigating any FI substitution/validation/BTE/exit incident, read finance_validations_and_substitutions_autopsy.md, validation_substitution_matrix.md, validation_substitution_autopsy.md, basu_mod_technical_autopsy.md, and posting_derivation_technical_autopsy.md from that folder.",
        "why": "INC-000005240 lost hours re-deriving YRGGBS00 structure, YXUSER bypass, U904/U915/U917, BASU framework - all of which were already documented in PSM/EXTENSIONS. The docs were misfiled under PSM historically because FI validation was originally extended by the PSM team, but they are the authoritative FI substitution/validation reference.",
        "how_to_apply": "For any incident mentioning substitution, validation, YRGGBS00, GGB0, GGB1, BOOLEXP, GB901, GB922, GB93, GB931, UXR*, U9*, UAEP, UATF, BASU, YTFI_BA_SUBST, YXUSER, or any FI derivation topic: grep knowledge/domains/PSM/EXTENSIONS/ and knowledge/domains/FI/ at the start of the investigation (Step 2 BRAIN LOOKUP). Read every autopsy doc in PSM/EXTENSIONS whose title matches. Document in the incident report which existing docs filled which gaps and which gaps this incident fills.",
        "severity": "HIGH",
        "created_session": "#051",
        "source_file": "feedback_psm_extensions_is_fi_substitution_home.md",
    },
    {
        "id": "feedback_bseg_union_has_no_xref",
        "rule": "The Gold DB view bseg_union does NOT carry BSEG-XREF1 / BSEG-XREF2 / BSEG-XREF3 columns. Never claim XREF is blank or XREF is set to X based on a bseg_union query - those columns do not exist in the view.",
        "why": "INC-000005240 claimed substitution fires only on vendor lines, GL lines have blank XREF based on reading bseg_union. The claim was wrong because bseg_union's schema does not include XREF1/XREF2/XREF3. I was reading an empty value from a non-existent field and misinterpreting it as blank in live data. CDPOS then contradicted the claim.",
        "how_to_apply": "1. PRAGMA table_info(bseg_union) at the start of any XREF-related query to confirm the schema. 2. If the investigation needs XREF values, go directly to live RFC on BSAK / BSAS / BSIS / BSIK / BSAD / BSID (the view's source tables, which DO carry XREF). 3. If the Gold DB must carry XREF values, enrich bseg_union with a targeted re-extraction (KU-028 class). 4. Never cite a bseg_union query result as proof of XREF state.",
        "severity": "HIGH",
        "created_session": "#051",
        "source_file": "feedback_bseg_union_has_no_xref.md",
    },
    {
        "id": "feedback_empirical_over_theoretical_substitution",
        "rule": "For substitution/validation rule behavior, empirical evidence (CDPOS change history, AUGBL trace, live RFC BSAK reads) always beats theoretical inference from BOOLID naming conventions or GB901 BOOLEXP parsing. The GGB framework has multiple configuration layers and some may be inaccessible via RFC_READ_TABLE.",
        "why": "INC-000005240 speculated for hours about whether the UXR1/UXR2 step prerequisite was 3UNESCO#013 (KOART=K) or 3UNESCO#017 (always-true) or an empty prerequisite (always fires). Each hypothesis produced a different prediction about F-53 vs F110 behavior. The answer came from CDPOS on one specific doc (3100003438 line 001 had VALUE_OLD=HQ on the bank GL line) - empirical proof trumped multiple rounds of inference. GB905/GB921 were empty in the RFC probe, confirming the step-prerequisite linking is not in standard tables at UNESCO.",
        "how_to_apply": "1. When investigating a substitution/validation behavior, run the EMPIRICAL test first: CDPOS on one representative document, AUGBL trace for clearing, RFC BSAK for the actual XREF values. 2. Use GB901/GB922/GB93/GB931 content to EXPLAIN the observation, not to PREDICT it. 3. If empirical and theoretical disagree, trust the empirical result - theoretical gaps usually mean the GGB configuration uses a mechanism not in the tables we can see (custom code, BAdI, BTE, or a table that is inaccessible). 4. Before claiming a step does or does not fire, pull at least ONE live document through CDPOS.",
        "severity": "HIGH",
        "created_session": "#051",
        "source_file": "feedback_empirical_over_theoretical_substitution.md",
    },
    {
        "id": "feedback_metadata_vs_real_bseg_lines",
        "rule": "Distinguish REAL business BSEG lines from METADATA / linkage-only BSEG lines when analyzing substitution, XREF, or any line-level financial attribution. BSCHL=27/37 zero-balancing clearing pairs, technical offsets in zero-net clearings, and similar engine-generated linkage records are metadata, not real business events - their XREF/GSBER/KOSTL values are cosmetic.",
        "why": "INC-000005240 initially flagged L_HANGI's 18K FB1K documents as a 1300x blast radius structural risk based on the clearing-pair BSEG lines carrying the clearing user XREF. The claim was correct in the strict sense (the BSEG records do exist with wrong XREF), but overstated because the clearing pair (BSCHL=27/37) is a zero-balancing metadata pattern that has no financial impact - the original invoice line XREF is preserved unchanged. Downstream consumers that correctly filter BSCHL or join via AUGBL to the original open item see the correct attribution.",
        "how_to_apply": "1. When counting affected documents, distinguish BSCHL=25 (real outgoing payment), BSCHL=31 (real vendor credit/invoice), BSCHL=50 (real bank side on F110/F-53) from BSCHL=27/37 (metadata zero-balancing pair for FB1K/SAPF124 clearings). 2. Severity HIGH applies to real lines; severity LOW to metadata. 3. For FB1K zero-balancing clearings, trace through AUGBL to the ORIGINAL invoice line - the invoice XREF is the business-meaningful value, not the clearing pair. 4. Document the distinction explicitly in the incident report so consumers know which numbers matter.",
        "severity": "MEDIUM",
        "created_session": "#051",
        "source_file": "feedback_metadata_vs_real_bseg_lines.md",
    },
    {
        "id": "feedback_no_learning_capture_mid_investigation",
        "rule": "Do NOT update knowledge domain docs, do NOT write feedback rules, do NOT update brain_v2 layers, and do NOT run rebuild_all.py while the investigation is still in flight. All knowledge capture happens at the finalization stage, after the user has confirmed the root cause and conclusions.",
        "why": "On INC-000005240, the main agent tried to write process learnings and update the incident-analyst SKILL mid-investigation, before the conclusions were finalized. The user stopped it with 'you cannot capture learning until we finish'. The reason: premature capture enshrines hypotheses as facts, poisons future queries, and may need to be reverted when the investigation pivots. Only at the end, when all conclusions are confirmed, should knowledge artifacts be written.",
        "how_to_apply": "1. Throughout the investigation, keep learnings as working memory (within the conversation context) only. 2. The incident report (knowledge/incidents/INC-id_slug.md) is the ONE exception - it is the active working document and can be updated continuously. 3. All OTHER artifacts (knowledge/domains/, .agents/skills/, brain_v2/*) are held until the user confirms conclusions. 4. When the user says investigation finished or update everything, execute the full finalization pass: feedback rules -> wrong-path triage -> domain docs -> brain layers -> rebuild. 5. Never rebuild brain_state.json mid-investigation - it is the last step always.",
        "severity": "HIGH",
        "created_session": "#051",
        "source_file": "feedback_no_learning_capture_mid_investigation.md",
    },
    {
        "id": "feedback_extract_ggb_tables_for_substitution_incidents",
        "rule": "For any incident touching FI substitution or validation, extract GB93 (validation header), GB931 (validation steps), GB905 (substitution step header, if present), GB921 (substitution rule header, if present), GB01/GB02/GB02C (Boolean class definitions), GB901 (Boolean expressions), GB922 (substitution values), and T80D (form pool registration) at the START of the investigation. Check Gold DB first; RFC what is missing.",
        "why": "INC-000005240 wasted significant effort speculating about which GB901 BOOLEXP was the prerequisite for which GB922 step because Gold DB only had GB01/GB02C/GB901/GB903/GB922. GB93 (validation header) was pullable via RFC and contained the row VALID=UNES BOOLCLASS=009 - critical context for understanding the UNES validation. GB931 (validation steps) was pullable and contained the full 12-step validation map with CONDID/CHECKID/severity - the most important single piece of evidence for the investigation. GB905/GB921 were empty at UNESCO (step linkage not in standard tables), but that itself is a finding.",
        "how_to_apply": "1. At investigation Step 3 (Gold DB pull), first check which GGB tables are in Gold DB via SELECT name FROM sqlite_master. 2. RFC-extract any missing GGB tables at the start: GB93, GB931, GB905, GB921, T80D. 3. Client-side filter for the relevant VALID or SUBSTID to see the rule set. 4. Cross-reference BOOLID naming convention: prefix 1 name ### X = CONDID, prefix 2 name ### X = CHECKID, prefix 3 name # X = substitution step prerequisite. 5. Document the extracted tables as evidence in the incident report Evidence section.",
        "severity": "HIGH",
        "created_session": "#051",
        "source_file": "feedback_extract_ggb_tables_for_substitution_incidents.md",
    },
    {
        "id": "feedback_read_emails_in_main_agent",
        "rule": "Always read the .eml file directly in the main agent before doing anything else with an incident. Never hand a file path to a subagent and rely on its summary of the content.",
        "why": "INC-000005240 Session #050 handed the .eml path to an incident-analyst subagent. The subagent read the file but produced a wrong intake parsing (mapped reference key to XBLNR/ZUONR/FISTL, HQ to UNESCO fund center). The main agent never saw the email body and had no way to catch the misinterpretation. By the time the user rejected the root cause, 154K tokens had been burned chasing the wrong mechanism.",
        "how_to_apply": "1. When a ticket / email / .eml is handed to you as a file path or attachment, use the Read tool in the main agent immediately. Read the full body, parse the terminology, build the User-term -> SAP-field translation table yourself. 2. Only AFTER you have the terminology nailed down can narrow sub-tasks (e.g., grep YRGGBS00 for XREF2 write sites) be delegated to subagents. 3. The .eml body is the ground truth - never rely on anyone else summary of it, including your own earlier summary.",
        "severity": "HIGH",
        "created_session": "#051",
        "source_file": "feedback_read_emails_in_main_agent.md",
    },
]

added = 0
for nr in new_rules:
    if nr["id"] in existing_ids:
        print(f"SKIP (exists): {nr['id']}")
        continue
    rules.append(nr)
    added += 1
    print(f"ADD: {nr['id']}")

p.write_text(json.dumps(rules, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nTotal rules now: {len(rules)} (added {added})")
