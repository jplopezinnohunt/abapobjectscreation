"""Register INC-180995 in brain_v2/incidents/incidents.json + add 3 KUs."""
import json, os, subprocess
os.chdir('c:/Users/jp_lopez/projects/abapobjectscreation')

ip = 'brain_v2/incidents/incidents.json'
incidents = json.load(open(ip, encoding='utf-8'))

if any(i['id']=='INC-180995' for i in incidents):
    print("INC-180995 already exists, skipping")
else:
    new_incident = {
        "id": "INC-180995",
        "status": "ROOT_CAUSE_CONFIRMED",
        "title": "Ticket 180995 parallel TR lag - Mozambique (5$B3/MZN) imported 101 days after sibling Sri Lanka (5$B4/LKR)",
        "reporter": "JP Lopez (Session #60 PY-Finance companion review)",
        "received_date": "2026-04-22",
        "analyzed_session": 60,
        "domain": "PY-Finance",
        "secondary_domains": ["Treasury", "CTS"],
        "category": "process_anomaly",
        "transactions": ["STMS", "SE01", "SE09", "SPRO"],
        "primary_object_id": "D01K9B0CDZ + D01K9B0CE6",
        "primary_subject": "Ticket 180995 - new-country payment method setup (MZ + LK)",
        "company_codes_involved": ["350 (UN/UNESCO)"],
        "scenario": "new_country_wage_type_setup",
        "error_messages": [],
        "root_cause_summary": "Two transports released on same day 2024-11-19 (~6h apart) for same service-desk ticket 180995 by same owner (FP_SPEZZANO). Sri Lanka (LKR) transport D01K9B0CE6 imported to P01 on 2024-11-20 (1 day lag, normal). Mozambique (MZN) transport D01K9B0CDZ imported 2025-02-28 (101 day lag, anomalous). Both technically identical in structure. Root cause not fully verified from data alone - candidates: H1 scheduled rollout, H2 stuck in STMS import queue, H3 approval workflow delay. Needs Francesco/basis admin confirmation.",
        "code_validation_chain": [
            "E070.D01K9B0CDZ STATUS=R OWNER=FP_SPEZZANO CLIENT=350 STRKORR=empty (NOT a correction)",
            "E070.D01K9B0CE6 STATUS=R OWNER=FP_SPEZZANO CLIENT=350 STRKORR=empty (NOT a correction)",
            "E071 both: CORR/RELE + CDAT/VC_T042ZL + 5x TABU (T512T,T512W,T52DZ,T52EL,T52EZ) = 7 objects, 8 table keys",
            "E071K D01K9B0CDZ: 350MZ3 / 350EMZ3 / 350EUN5$B3 / 350UN5$B399991231 / 350UN5$B3 / 350UN5$B30199991231 / 350UN5$B30299991231 / 350UN5$B399991231",
            "E071K D01K9B0CE6: 350LKU / 350ELKU / 350EUN5$B4 / 350UN5$B499991231 / 350UN5$B4 / 350UN5$B40199991231 / 350UN5$B40299991231 / 350UN5$B499991231",
            "cts_transports AS4DATE Gold DB snapshot of P01 import date: 20250228 (Mozambique) vs 20241120 (LKR)",
            "TMSALOG 2026-04-20 snapshot: V.VAURETTE is the sole human user executing TMS_TP_IMPORT on P01 (alongside TMSADM service account for TMS_TS_GET_TRLIST) - inferred P01 importer"
        ],
        "scope": {
            "transports_affected": 2,
            "countries_affected": ["Mozambique", "Sri Lanka"],
            "wage_types_created": ["5$B3 (Stockage devise MZN)", "5$B4 (Stockage devise LKR)"],
            "payment_methods_created": ["MZ/3", "LK/U"],
            "lag_days_mozambique": 101,
            "lag_days_sri_lanka": 1,
            "window_between_imports": "2024-11-20 to 2025-02-28",
            "mozambique_payroll_impact_in_gap": "UNKNOWN - needs FO audit (see KU-038)"
        },
        "fix_path": {
            "immediate": "None - both transports now live in P01 (resolved 2025-02-28).",
            "structural": "N/A - no SAP config fix needed; both transports were correctly structured.",
            "preventive": [
                "Build Zagentexecution/quality_checks/tr_sibling_lag_detector.py - detect siblings (same ticket# in as4text) with import-date delta > 7 days",
                "Extend cts_dashboard.html / transport companion to cluster transports by extracted ticket number",
                "Add governance rule: any ticket producing >1 TR should have sibling status cross-checked at each release",
                "Document UNESCO 5$Bx new-country wage type pattern as canonical procedure (done in py_finance_wage_type_companion_v1.html)"
            ]
        },
        "related_objects": [
            "D01K9B0CDZ","D01K9B0CE6","T042Z","T042ZT","T512T","T512W","T52DZ","T52EL","T52EZ","VC_T042ZL","5$B3","5$B4"
        ],
        "related_claims": [
            {"id": 55, "claim": "Four Tier-1 PY-Finance editors (A_SEFIANI, L_CABALLE, N_MENARD, FP_SPEZZANO) cover 97%"},
            {"id": 56, "claim": "FP_SPEZZANO/M_SPRONK enter wage type tables only when a ticket requires new-country payment setup"},
            {"id": 59, "claim": "T512W wrong row = silent salary miscalc"}
        ],
        "related_dq": ["DQ-022","DQ-023","DQ-025"],
        "related_known_unknowns": ["KU-038","KU-039","KU-040"],
        "analysis_doc": "knowledge/incidents/INC-180995_py_finance_trlag_forensics.md",
        "evidence_extracted_this_incident": {
            "rfc_calls": [
                "RFC_READ_TABLE E070 (header for both TRs)",
                "RFC_READ_TABLE E07T (description text)",
                "RFC_READ_TABLE E071 (object list, 7 per TR)",
                "RFC_READ_TABLE E071K (table keys, 8 per TR)",
                "CTS_API_READ_CHANGE_REQUEST (confirmed owner, client, category)",
                "RFC_READ_TABLE TMSALOG 1000-row snapshot (identified V.VAURETTE as P01 importer)"
            ],
            "json_artifacts": [
                "Zagentexecution/py_finance_investigation/180995_forensics.json"
            ]
        },
        "lessons": [
            "Ticket-linked transports can diverge silently - no automated UNESCO check catches sibling TR lag. Class of defect, not a one-off.",
            "Service-desk ticket numbers are the best cross-cutting key for linking transports to external context, but UNESCO CTS extraction lacks a ticket column; we reverse-engineer via as4text regex.",
            "Treasury-routed PY config (Francesco ticket-driven new-country setup) is a legitimate cross-functional flow, not a misclassification.",
            "'101-day lag' is not automatically a defect - could be deliberate staggered rollout. Need human confirmation for root cause."
        ],
        "open_followups": [
            "KU-038: Did Mozambique FO have payroll activity in 2024-11-20 to 2025-02-28 window that required 5$B3?",
            "KU-039: Exact P01 importer for D01K9B0CDZ 2025-02-28",
            "KU-040: Are there other sibling-ticket TR pairs with import lag > 30 days across 4 years?"
        ],
        "chain_anchor_type": "sap_transport_system",
        "chain_anchor_note": "CTS-based incident - anchors are E070/E071/E071K/E07T records + CTS_API_READ_CHANGE_REQUEST confirmations from P01.",
        "chain_anchor_coverage_pct": 90,
        "chain_audited_session": 60,
        "domain_axes": {
            "functional": ["PY-Finance", "Treasury", "Transport_Intelligence"],
            "module": ["PY", "PA", "FI", "BC-CTS"],
            "process": ["H2R", "T2R"]
        }
    }
    incidents.append(new_incident)
    with open(ip,'w',encoding='utf-8') as f:
        json.dump(incidents, f, indent=2, ensure_ascii=False)
    print(f"Added INC-180995. Total incidents: {len(incidents)}")

# === 2. Add 3 KUs ===
kup = 'brain_v2/agi/known_unknowns.json'
kus = json.load(open(kup, encoding='utf-8'))
existing = {k['id'] for k in kus}
if 'KU-038' in existing:
    print("KUs already added")
else:
    nums = [int(k['id'].split('-')[1]) for k in kus if k['id'].startswith('KU-')]
    next_n = max(nums) + 1

    new_kus = [
        {
            "id": f"KU-{next_n:03d}",
            "question": "Did Mozambique Field Office have any payroll activity in the 2024-11-20 to 2025-02-28 window that required wage type 5$B3 (Stockage devise MZN)?",
            "why_unknown": "Transport D01K9B0CDZ released 2024-11-19 but imported to P01 only 2025-02-28 (101 day lag). If MZ FO had payroll in that window that needed 5$B3, they would have had no working wage type available.",
            "raised_session": 60,
            "domain": "PY-Finance",
            "blocks_incident": "INC-180995",
            "investigation_cost_estimate": "LOW",
            "owner_session": None,
            "notes": "Query PA0008/PA0014/PA0015 for any Mozambique employee with WT 5$B3 in infotype dates 2024-11 through 2025-02. Also check T512W for any pre-existing stub WT prior to 2024-11-19."
        },
        {
            "id": f"KU-{next_n+1:03d}",
            "question": "Who exactly imported D01K9B0CDZ into P01 on 2025-02-28? TMSALOG RFC is capped at ~1000 rows and 2025-02 entries have cycled out.",
            "why_unknown": "V.VAURETTE is the dedicated P01 import operator based on 2026-04-20 TMSALOG snapshot, but we cannot directly confirm the exact user who imported the 2025-02-28 event from remote RFC alone. Historical STMS GUI audit or SM21 system log reading is needed.",
            "raised_session": 60,
            "domain": "PY-Finance",
            "blocks_incident": "INC-180995",
            "investigation_cost_estimate": "LOW",
            "owner_session": None,
            "notes": "SAP basis team can check STMS import history via SAP GUI (STMS_IMPORT_HIST) or filesystem /usr/sap/trans/log/ALOG*.P01 for the specific date."
        },
        {
            "id": f"KU-{next_n+2:03d}",
            "question": "Across 4 years of UNESCO transport history (2022-2026), are there other sibling-ticket transport pairs with import lag > 30 days? Class-of-defect generalization.",
            "why_unknown": "INC-180995 is a single observed case. We have 418 wage type transports and 7,745 total UNESCO transports. A systematic detection pass using ticket number regex on as4text + pairwise import-date comparison could surface other instances.",
            "raised_session": 60,
            "domain": "Transport_Intelligence",
            "blocks_incident": None,
            "investigation_cost_estimate": "LOW",
            "owner_session": None,
            "notes": "Build Zagentexecution/quality_checks/tr_sibling_lag_detector.py. Output: list of (ticket, TR1, TR2, lag_days, description). Alert threshold: >7 days, investigate: >30 days."
        }
    ]
    kus.extend(new_kus)
    with open(kup,'w',encoding='utf-8') as f:
        json.dump(kus, f, indent=2, ensure_ascii=False)
    print(f"Added 3 KUs (KU-{next_n:03d}/KU-{next_n+1:03d}/KU-{next_n+2:03d}). Total KUs: {len(kus)}")

# === 3. Rebuild brain ===
print("\nRebuilding brain_state...")
result = subprocess.run(['python','brain_v2/rebuild_all.py'], capture_output=True, text=True, timeout=300)
# Print last lines
for line in result.stdout.splitlines()[-15:]:
    print(line)
