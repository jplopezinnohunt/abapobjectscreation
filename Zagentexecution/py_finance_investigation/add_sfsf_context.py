"""Add SuccessFactors 2026 migration strategic context to HR-Workflows."""
import json, os, subprocess
os.chdir('c:/Users/jp_lopez/projects/abapobjectscreation')

path = 'brain_v2/domains/domains.json'
d = json.load(open(path, encoding='utf-8'))
hr = d['domains']['HR-Workflows']

hr['description'] = "HR Workflows - long-running UNESCO domain covering end-user-facing HR self-service flows: Offboarding, Benefits Enrollment, Family Management, Rental, Education Grant, Secondary Dependent. Built on SAPUI5 Fiori + WebDynpro ABAP + ASR Framework + ZCL_HR_FIORI_* handler classes. Activity 2017-2026. Strategic context: migration to SuccessFactors (SFSF) in progress, target completion 2026. End state = hybrid SFSF + retained UNESCO custom apps. The Core HR Project 2025-2026 burst IS the SFSF integration project."

hr['strategic_context_2026'] = {
    "migration_target": "SuccessFactors (SFSF) integration",
    "target_completion": "2026",
    "end_state": "Hybrid: SFSF handles standard HR flows; some UNESCO custom apps retained",
    "integration_layer": "TBD - BizTalk planned per MEMORY.md (not live), or MuleSoft alternative",
    "project_team_started": "2025-10",
    "project_team_expansion": "GD_SCHELLINC joined 2025-11, N_VIDAL 2026-01, G_SONNET 2026-02",
    "custom_apps_retained_tbd": True,
    "source": "User attestation Session #60 (2026-04-22)"
}

hr['subtopics']['core_hr_project_2025_2026']['description'] = "SuccessFactors integration project 2025-2026. Concentrated development burst starting 2025-10 (80 TRs 2025 + 53 TRs 2026 YTD = 133 TRs on HR Fiori apps by 4-6 editors). Target: end state 2026 = hybrid SFSF + retained UNESCO custom apps. This subtopic IS the SFSF migration project."
hr['subtopics']['core_hr_project_2025_2026']['aliases'] = ['successfactors_migration_2025_2026','sfsf_integration_project']

hr['subtopics']['successfactors_end_state_2026'] = {
    "description": "End state target 2026: SuccessFactors handles standard HR processes; UNESCO retains custom apps for flows SFSF cannot cover (likely Offboarding complexity, Family/Dependent for UN common-system rules, Benefits, Education Grant, Rental).",
    "migration_layer": "BizTalk planned (not live per MEMORY.md) or MuleSoft alternative",
    "status": "in_progress_2025_2026",
    "open_questions": ["Which custom apps survive migration?","Integration architecture?","Cutover plan?","Source of truth for employee data post-cutover?"]
}

with open(path,'w',encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
print("HR-Workflows updated with SFSF 2026 migration context")

cp = 'brain_v2/claims/claims.json'
claims = json.load(open(cp, encoding='utf-8'))
next_id = max(c['id'] for c in claims) + 1
new_claim = {
    "id": next_id,
    "claim": "UNESCO HR-Workflows domain is being migrated to SuccessFactors (SFSF) with target completion 2026. The end state is hybrid: SFSF handles standard HR processes; UNESCO retains some custom apps (likely Offboarding, Family/Dependent, Benefits, Education Grant, Rental) for UN common-system rules SFSF cannot cover. The Core HR Project 2025-2026 burst (N_MENARD + 4 new editors from 2025-10 onward, 133 HR-Fiori transports) is the SFSF integration project itself.",
    "claim_type": "strategic_context",
    "confidence": "TIER_2",
    "evidence_for": [
        {
            "type": "user_attestation",
            "ref": "Session #60 user message 2026-04-22",
            "cite": "User: HR workflows have a long process that we need to know and track. This ends this year integrated to SuccessFactors and using some custom apps too.",
            "added_session": 60
        },
        {
            "type": "data_correlation",
            "ref": "Gold DB + MEMORY.md",
            "cite": "Core HR Project burst starts 2025-10 with 4 new editors. MEMORY.md notes 'BizTalk | SuccessFactors EC (planned, not live)'. Timing + editor cohort consistent with SFSF integration project start.",
            "added_session": 60
        }
    ],
    "evidence_against": None,
    "related_objects": ["YHR_BEN_ENRL","ZCL_HR_FIORI_OFFBOARDING_REQ","ZCL_HRFIORI_CHANGE_SISTER","BizTalk_SFSF_EC"],
    "domain": "HR-Workflows",
    "created_session": 60,
    "resolved_session": None,
    "resolution_notes": None,
    "status": "active",
    "needs_validation": [
        "which specific custom apps are retained vs migrated",
        "integration architecture (BizTalk vs MuleSoft vs direct SFSF API)",
        "cutover plan",
        "employee data source of truth post-migration"
    ],
    "domain_axes": {
        "functional": ["HR-Workflows","HCM","Integration"],
        "module": ["HCM","PD","UI5","SFSF"],
        "process": ["H2R"]
    }
}
claims.append(new_claim)
with open(cp,'w',encoding='utf-8') as f:
    json.dump(claims, f, indent=2, ensure_ascii=False)
print(f"Added claim #{next_id} (SFSF migration 2026). Total claims: {len(claims)}")

kup = 'brain_v2/agi/known_unknowns.json'
kus = json.load(open(kup, encoding='utf-8'))
nums = [int(k['id'].split('-')[1]) for k in kus if k['id'].startswith('KU-')]
next_n = max(nums) + 1
new_kus = [
    {
        "id": f"KU-{next_n:03d}",
        "question": "Which specific UNESCO HR custom apps will be retained (kept on SAP) vs migrated to SuccessFactors by end of 2026? Candidates: Offboarding, Family/Change Sister, Benefits Enrollment, Rental, Education Grant, Secondary Dependent.",
        "why_unknown": "User indicated hybrid end state but did not specify which apps survive. Critical for technical debt planning.",
        "raised_session": 60,
        "domain": "HR-Workflows",
        "blocks_incident": None,
        "investigation_cost_estimate": "LOW",
        "owner_session": None,
        "notes": "Ask N_MENARD or HR project lead. Check recent transport descriptions for SFSF-related keywords."
    },
    {
        "id": f"KU-{next_n+1:03d}",
        "question": "What is the integration architecture for SuccessFactors migration at UNESCO? BizTalk (per MEMORY.md plan), MuleSoft, direct SFSF API, or a mix?",
        "why_unknown": "MEMORY.md says BizTalk planned not live. No confirmation that this is the chosen path.",
        "raised_session": 60,
        "domain": "Integration",
        "blocks_incident": None,
        "investigation_cost_estimate": "LOW",
        "owner_session": None,
        "notes": "Check with integration architect. Look for BizTalk/MuleSoft workbench entries in recent transports."
    },
    {
        "id": f"KU-{next_n+2:03d}",
        "question": "Post-SFSF cutover, what is the source of truth for employee master data? SFSF, SAP PA0* infotypes, or both with replication?",
        "why_unknown": "Affects every downstream domain that reads employee data: payroll PY-Finance, Travel, Benefits, Rental, access control.",
        "raised_session": 60,
        "domain": "HR-Workflows",
        "blocks_incident": None,
        "investigation_cost_estimate": "MEDIUM",
        "owner_session": None,
        "notes": "Typical SFSF pattern: PA0* remains source for payroll, SFSF source for talent; replication via BizTalk per infotype."
    }
]
kus.extend(new_kus)
with open(kup,'w',encoding='utf-8') as f:
    json.dump(kus, f, indent=2, ensure_ascii=False)
print(f"Added 3 KUs (KU-{next_n:03d}/KU-{next_n+1:03d}/KU-{next_n+2:03d}). Total KUs: {len(kus)}")

print("\nRebuilding brain_state...")
result = subprocess.run(['python','brain_v2/rebuild_all.py'], capture_output=True, text=True, timeout=300)
for line in result.stdout.splitlines()[-8:]:
    print(line)
