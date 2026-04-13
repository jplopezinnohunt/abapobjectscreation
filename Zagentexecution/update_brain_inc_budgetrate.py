"""Idempotent brain updater for INC-BUDGETRATE-EQG (Session #053).

Appends:
  - 5 feedback rules to brain_v2/agent_rules/feedback_rules.json
  - 3 claims    to brain_v2/claims/claims.json
  - 1 incident  to brain_v2/incidents/incidents.json (INC-BUDGETRATE-EQG)
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# 1. RULES
rp = "brain_v2/agent_rules/feedback_rules.json"
rules = json.load(open(rp))
existing_ids = {r["id"] for r in rules}
new_rules = [
    {
        "id": "feedback_br_camp_asymmetry",
        "rule": "When analyzing UNESCO BR custom solution (ENHC ZFIX_EXCHANGERATE), classify enhancements by gate-input source: Camp A (FR-currency anchored: CHECK_CONS, EF_FUND_RESERVATION, FUNDBLOCK), Camp B (posting-currency anchored: PAYCOMMIT, NEW_ITEM, AVC, KBLEW, FI), Camp C (filters: BR_REVALUATION, BR_REVAL_RESFUND, BR_AVC_EXCLUSIONS BAdI), Camp D (auxiliary: FM_BR_POST_FROM_PY_AUTO, BR_BAPI_EMPLOYEE_POST). The asymmetry between Camp A (always BR for EUR FR) and Camp B (skips when posting is non-EUR) is the cross-currency drift bug surface.",
        "why": "Session #053 (INC-BUDGETRATE-EQG): the prior 8-member framing was incomplete. Real composite has 15 members + 1 BAdI. Bug isn't 'gate rejects USD everywhere' - it's gate input source asymmetry. Only Camp B mis-handles cross-currency.",
        "how_to_apply": "When triaging FMAVC005 or any BR-related question, list all 15 composite members + classify into camps before reasoning about behavior. Don't trust prior 8-member docs.",
        "severity": "HIGH",
        "created_session": 53,
        "source_file": "knowledge/domains/PSM/EXTENSIONS/budget_rate_custom_solution.md",
    },
    {
        "id": "feedback_check_landscape_before_root_cause",
        "rule": "Before claiming any custom Z/Y object affects production behavior, query TADIR + REPOSRC against P01 (production) directly via RFC. D01-only or V01-only objects do NOT affect production no matter how interesting their source code looks. Cross-check via: SELECT FROM TADIR WHERE OBJ_NAME=<X> on every system in the landscape (D01/V01/TS1/TS3/P01).",
        "why": "Session #053: I claimed BR_AVC_EXCLUSIONS BAdI was suppressing AVC for MIRO/F110 in production based on D01 source. User caught it: 'I do not see it in TS3'. Cross-check confirmed it lives only in D01+V01, was deactivated 1 day after creation, never transported. Wrong claim wasted user time.",
        "how_to_apply": "For any custom object analysis: (1) confirm presence in P01 first, (2) check ENHLOG for deactivation, (3) check transports in E070/E07T for release status, (4) only THEN claim it affects production behavior.",
        "severity": "CRITICAL",
        "created_session": 53,
        "source_file": "PMO H38",
    },
    {
        "id": "feedback_kble_via_pspro_wrapper",
        "rule": "KBLE / KBLEW (Earmarked Fund consumption history) are cluster tables - RFC_READ_TABLE returns TABLE_WITHOUT_DATA. Use RFC-enabled wrapper: conn.call('/SAPPSPRO/PD_GM_FMR2_READ_KBLE', I_BELNR=<FR_doc>) which returns T_KBLE (consumption events with RBELNR/RBUZEI = consumer FI doc/line) AND T_KBLEW (per-currency split with CURTP=00 transaction currency, CURTP=10 local USD).",
        "why": "Session #053: needed FR<->FI consumption traceability without BSEG.KBLNR. Wrapper found via /SAPPSPRO/ namespace probe. Returns 263 rows for one FR including the RBELNR linkage we couldn't get any other way.",
        "how_to_apply": "For any FR consumption analysis: use wrapper FM, not RFC_READ_TABLE. KBLEW.CURTP=10 gives local-currency (USD) view directly; CURTP=00 gives transaction currency.",
        "severity": "MEDIUM",
        "created_session": 53,
        "source_file": "Zagentexecution/quality_checks/budget_rate_consumption_audit.py",
    },
    {
        "id": "feedback_fmavct_query_pattern",
        "rule": "FMAVCT (BCS AVC totals) is a wide table (>512 bytes per row). RFC_READ_TABLE with FIELDS=[] returns DATA_BUFFER_EXCEEDED. Workaround: pass narrow FIELDS list (max 10-15 columns); split WHERE conditions into multiple OPTIONS entries (single complex boolean WHERE rejected with OPTION_NOT_VALID). Dedup result rows by full-row signature (RVERS/RPMAX often produce duplicates that double-count if summed naively). For AVC available calc: ALLOCTYPE_9='KBFC' = carryforward allotment (UNESCO ledger 9H 2026). HSL01-HSL16 are per-period local-currency values; HSLVT is yearly total.",
        "why": "Session #053: needed AVC budget per fund for 26 funds. First attempts failed with parser errors. Final pattern works reliably: split WHERE + narrow FIELDS + dedup.",
        "how_to_apply": "For any FMAVCT query in a script: (1) use DDIF_FIELDINFO_GET first to confirm column names, (2) pick max 12 fields, (3) split WHERE into multiple OPTIONS lines, (4) dedup by row signature before summing. ALLOCTYPE_9 dimension distinguishes budget vs. consumption rows.",
        "severity": "MEDIUM",
        "created_session": 53,
        "source_file": "Zagentexecution/quality_checks/br_line_level_inconsistency_check.py",
    },
    {
        "id": "feedback_fmioi_carryforward_pairs",
        "rule": "FMIOI WRTTP=81 rows for an Earmarked Fund include: original creation (positive), period-specific consumption reductions (negative), period-016 year-end reversal (positive equal to remaining), period-000 carryforward-IN to next year. Naive sign-sum across all years does NOT equal 'open balance'. For 'open' filter by current GJAHR + signed sum. For 'lifetime consumed' use KBLE/KBLEW (the consumption history), NOT FMIOI. FMIOI rows with ratio=1.0 and tiny amounts ($0.01-0.02) are SAP rounding plugs, NOT cross-currency consumption signatures.",
        "why": "Session #053: misread the AFFECTED 20 lines as 'cross-currency consumption already fired' when they were actually rounding plugs. Also computed wrong open balance from FMIOI by naive subtraction. User caught both errors.",
        "how_to_apply": "Always sample 3 raw FMIOI WRTTP=81 rows for any FR before computing per-line metrics. Identity-ratio rows with sub-cent amounts = rounding plugs, ignore. For consumption history, use KBLEW filtered by CURTP - not FMIOI signed sums.",
        "severity": "MEDIUM",
        "created_session": 53,
        "source_file": "Zagentexecution/quality_checks/br_line_level_inconsistency_check.py",
    },
]
added_rules = 0
for r in new_rules:
    if r["id"] not in existing_ids:
        rules.append(r)
        added_rules += 1
with open(rp, "w", encoding="utf-8") as f:
    json.dump(rules, f, indent=2, ensure_ascii=False)
print(f"feedback_rules: +{added_rules} new (now {len(rules)} total)")

# 2. CLAIMS
cp = "brain_v2/claims/claims.json"
claims = json.load(open(cp))
max_id = max(c["id"] for c in claims)
new_claims_specs = [
    {
        "claim": "UNESCO BR cross-currency drift bug = gate-input asymmetry across the 15-member ZFIX_EXCHANGERATE composite. Camp A (CHECK_CONS / EF_FUND_RESERVATION / FUNDBLOCK) gates on FR's own EUR currency and always fires. Camp B (PAYCOMMIT / NEW_ITEM / AVC / KBLEW / FI) gates on per-row posting currency and silently skips when posting is non-EUR. The two camps thus produce divergent ledger states: FR side at BR (1.09529), consumption side at identity / M-rate. AVC pool drifts fund-by-fund until cover-group hits zero headroom => FMAVC005.",
        "evidence": "Source code: extracted_code/ENHO/ZFIX_EXCHANGERATE/ (15 enhancement files inspected line-by-line in Session #053). Production data: 64 BR-applicable open FR lines in P01 ledger 9H 2026, 35 with non-EUR consumption pool drift documented in Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_lines_FINAL.xlsx.",
        "related": ["YCL_FM_BR_EXCHANGE_RATE_BL","ZFIX_EXCHANGERATE_CHECK_CONS","ZFIX_EXCHANGERATE_AVC","ZFIX_EXCHANGERATE_FI","ZFIX_EXCHANGERATE_KBLEW","ZFIX_EXCHANGERATE_NEW_ITEM","ZFIX_EXCHANGERATE_PAYCOMMIT","ZFIX_EF_FUND_RESERVATION","ZFIX_EXCHANGERATE_FUNDBLOCK","INC-BUDGETRATE-EQG"],
    },
    {
        "claim": "ZFIX_BR_AVC_EXCLUSIONS BAdI is dead code in P01 production. Created by JP_LOPEZ on 2025-05-14 in D01 (transports D01K9B0D4Z + D01K9B0D50, 'BR - AVC Exlclusion MIRO F110'), deactivated next day 2025-05-15 (transports D01K9B0D54 + D01K9B0D55, 'BR Deactivate AVC exclusion'). Exists in D01 + V01 only (TADIR + REPOSRC confirmed). Absent from TS1, TS3, P01. The implementation only places skip logic in BUDGET_FILTER (wrong method) for tcodes MIRO + F110, and POSTING_FILTER is an empty stub. Never affected production AVC behavior.",
        "evidence": "Cross-system TADIR/REPOSRC query Session #053. Transports E070/E07T headers. Source code at extracted_code/ENHO/ZFIX_EXCHANGERATE/AVC_EXCLUSIONS/.",
        "related": ["ZFIX_BR_AVC_EXCLUSIONS","FMAVC_ENTRY_FILTER","IF_EX_FMAVC_ENTRY_FILTER"],
    },
    {
        "claim": "AVC available is a fund/cover-group level metric, not an FR-line-level metric. All FR lines on the same (FONDS, FUNDSCTR, CMMTITEM-rolled-to-control-object) draw from a single shared AVC pool. The pool is calculated as: Available = FMAVCT.allotment - sum(open FMIOI commitments) - sum(FMIFIIT actuals) on the same key. FMAVC005 fires when Available <= 0 + new posting amount > 0. The triggering FR line is incidental; the constraint is the fund pool.",
        "evidence": "FMAVCT structure inspection + Vonthron's case empirical confirmation: fund 3110111021/PAX/TC 2026 has $12,897.80 carryforward allotment exactly matching the 5 carryforward FRs sum => Available = 0 => any USD posting on any of the 5 lines triggers FMAVC005.",
        "related": ["FMAVCT","FMIOI","FMIFIIT","INC-BUDGETRATE-EQG"],
    },
]
added_claims = 0
existing_claim_texts = {c["claim"][:80] for c in claims}
for spec in new_claims_specs:
    if spec["claim"][:80] in existing_claim_texts:
        continue
    max_id += 1
    claims.append({
        "id": max_id,
        "claim": spec["claim"],
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": spec["evidence"],
        "evidence_against": None,
        "related_objects": spec["related"],
        "domain": "PSM",
        "created_session": 53,
        "resolved_session": None,
        "resolution_notes": None,
        "status": "active",
    })
    added_claims += 1
with open(cp, "w", encoding="utf-8") as f:
    json.dump(claims, f, indent=2, ensure_ascii=False)
print(f"claims: +{added_claims} new (now {len(claims)} total, last id={claims[-1]['id']})")

# 3. INCIDENT
ip = "brain_v2/incidents/incidents.json"
incidents = json.load(open(ip))
incidents = [i for i in incidents if i.get("id") != "INC-BUDGETRATE-EQG"]
inc = {
    "id": "INC-BUDGETRATE-EQG",
    "status": "ROOT_CAUSE_CONFIRMED",
    "title": "Budget Rate custom solution allows cross-currency consumption against EUR-reserved FR -> AVC pool drift -> FMAVC005",
    "reporter": "Laetitia Vonthron (adm.cad) -> Christina Lopez-Chemouny -> Yimiao Guo -> Illya Konakov -> Pablo Lopez",
    "received_date": "2026-03-26",
    "analyzed_session": 53,
    "domain": "PSM",
    "secondary_domains": ["FI", "Treasury"],
    "transactions": ["FB60", "MIRO", "F110", "FMX1", "FMX2", "FMN4N", "FMZZ", "FMAVCREINIT"],
    "primary_subject": "FR 3250117351 line 39 (EUR carryforward to 2026, fund 3110111021 / FUNDSCTR PAX / CMMTITEM TC); EqG ticket reimbursement for SG Bivini Mangue",
    "company_codes_involved": ["UNES"],
    "scenario": "cross_currency_consumption_against_BR_FR",
    "incident_type": "defect",
    "error_messages": ["FMAVC005 Annual budget exceeded by 0,87 USD (FM Availability Control) for document item 00002"],
    "root_cause_summary": "15-member ZFIX_EXCHANGERATE composite has gate-input asymmetry: Camp A (FR-anchored: CHECK_CONS, EF_FUND_RESERVATION, FUNDBLOCK) always fires for EUR FRs; Camp B (posting-anchored: PAYCOMMIT, NEW_ITEM, AVC, KBLEW, FI) silently skips when posting currency is not EUR. FR persisted at BR (1.09529); consumption persisted at identity. AVC pool drifts fund-by-fund until cover-group hits zero headroom. Vonthron's fund 3110111021/PAX/TC has $12,897.80 budget exactly matched by $12,897.80 of carryforward FR commitments -> Available=0 -> any new USD posting fires FMAVC005.",
    "code_validation_chain": [
        "extracted_code/CLAS/YCL_FM_BR_EXCHANGE_RATE_BL/CM00A line 8: APPEND 'EUR' to mr_waers (the perimeter line)",
        "extracted_code/CLAS/YCL_FM_BR_EXCHANGE_RATE_BL/CM004: check_conditions exits abap_false if iv_waers NOT IN mr_waers",
        "ZFIX_EXCHANGERATE_CHECK_CONS Enh1 (Camp A): iv_waers = m_r_doc->m_f_kblk-waers (FR header EUR) -> PASS -> recalc -> Enh2 RESTORE original (in-memory only, no persistence)",
        "ZFIX_EXCHANGERATE_NEW_ITEM (Camp B): iv_waers = c_f_fmoi-twaer (USD for USD posting) -> FAIL -> no recalc",
        "ZFIX_EXCHANGERATE_AVC Enh1+3 (Camp B): iv_waers = <ls_fmioi>-twaer / <ls_fmifiit>-twaer per-row -> mixed, USD rows skip",
        "ZFIX_EXCHANGERATE_KBLEW (Camp B): iv_waers = ls_tr_kblew-waers (USD) -> FAIL -> no recalc",
        "ZFIX_EXCHANGERATE_FI (Camp B): iv_waers = <ls_fmifiit>-twaer (USD) -> FAIL -> no recalc + no audit + mt_avc_fund not appended -> fmavc_reinit_on_event handler never registered",
        "FMAVCT(RLDNR=9H,RFIKRS=UNES,RYEAR=2026,RFUND=3110111021,RFUNDSCTR=PAX,RCMMTITEM=TC) ALLOCTYPE_9=KBFC HSL01=12,897.80 USD",
        "Open FR commitments same key: 5 lines (RFPOS 38/39/40/43/45 of FR 3250117351) summing to $12,897.80",
        "Available = 12,897.80 - 12,897.80 = 0 -> FMAVC005 fires on any positive posting",
    ],
    "scope": {
        "br_applicable_open_fr_lines_in_P01_2026": 64,
        "distinct_funds_at_risk": 26,
        "lines_with_AVC_available_zero": [
            "3250117351/00038", "3250117351/00039", "3250117351/00040",
            "3250117351/00043", "3250117351/00045",
            "3260008383/00001", "3260008383/00002", "3260008383/00007",
            "3250117154/00002", "3250118228/00003", "3250118228/00004",
        ],
        "lifetime_USD_bypass_volume_USD": 375011484.95,
        "estimated_drift_exposure_USD": 35734844.40,
        "system_landscape": {
            "D01": "BAdI ZFIX_BR_AVC_EXCLUSIONS exists (DEAD)",
            "V01": "BAdI exists (DEAD)",
            "TS1": "absent",
            "TS3": "absent",
            "P01": "absent",
        },
    },
    "fix_path": {
        "immediate_workaround": "Post the EqG invoice in EUR (validated by Konakov 2026-03-30 'when I try to post the invoice in EUR instead of USD it works fine'). Use XOF->EUR rate at translation date.",
        "preventive_recommended": "Add validation in CL_FM_EF_POSITION->CHECK_CONSUMPTION: IF check_br_is_active() AND m_r_doc->m_f_kblk-waers='EUR' AND m_f_kblp-gsber='GEF' AND fund_type IN mr_fund_type AND consumption_doc-waers <> 'EUR' THEN MESSAGE 'Z_BR_001' TYPE 'E'. Stops drift at user-input layer.",
        "corrective_alternative": "Activate convert_to_currency_2 (Staff logic) in Camp B enhancements to dispatch USD through USD-UNORE -> EUR @ M -> USD @ EURX double-hop. Method exists, complete, only called from IF 1=2 dead branches today.",
        "cleanup": "After preventive validation deploys: one-time FMAVCREINIT on 26 affected funds for 2026 GJAHR ledger 9H to clear accumulated drift.",
        "PMO_items": [
            "H38: Cleanup ZFIX_BR_AVC_EXCLUSIONS dead code from D01+V01",
            "H39 (new): Build preventive validation enhancement",
            "H40 (new): One-time FMAVCREINIT cleanup",
        ],
    },
    "analysis_doc": "knowledge/incidents/INC-BUDGETRATE-EQG_budget_rate_usd_posting.md",
    "executive_brief": "knowledge/incidents/INC-BUDGETRATE-EQG_executive_brief.md",
    "inventory_xlsx": "Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_lines_FINAL.xlsx",
    "trace_evidence": "Zagentexecution/incidents/INC_budget_rate_eq_guinea/dev_w5_trace_TS3.txt + body.txt + image*.png + br_consumption_audit.json",
    "related_objects": [
        "YCL_FM_BR_EXCHANGE_RATE_BL", "ZFIX_EXCHANGERATE",
        "ZFIX_EXCHANGERATE_CHECK_CONS", "ZFIX_EXCHANGERATE_AVC",
        "ZFIX_EXCHANGERATE_FI", "ZFIX_EXCHANGERATE_KBLEW",
        "ZFIX_EXCHANGERATE_NEW_ITEM", "ZFIX_EXCHANGERATE_PAYCOMMIT",
        "ZFIX_EXCHANGERATE_FUNDBLOCK", "ZFIX_EF_FUND_RESERVATION",
        "ZFIX_BR_REVALUATION", "ZFIX_BR_REVAL_RESFUND",
        "ZFIX_BR_AVC_EXCLUSIONS", "ZFIX_FM_BR_POST_FROM_PY_AUTO",
        "ZFIX_BR_BAPI_EMPLOYEE_POST", "CL_FM_EF_POSITION",
        "FMAVCT", "FMIOI", "FMIFIIT", "KBLE", "KBLEW", "KBLK", "KBLP",
        "TCURR", "TVARVC.Y_FM_FIXED_RATE_START", "FMFINCODE",
        "FMFUNDTYPE.ZZFIX_RATE", "/SAPPSPRO/PD_GM_FMR2_READ_KBLE",
    ],
}
incidents.append(inc)
with open(ip, "w", encoding="utf-8") as f:
    json.dump(incidents, f, indent=2, ensure_ascii=False)
print(f"incidents: INC-BUDGETRATE-EQG upserted (now {len(incidents)} total)")
print("\nDone. Brain artifacts updated.")
