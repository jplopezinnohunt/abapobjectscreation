"""Correct HR-Workflows domain with historical + Core HR Project 2025-2026 split."""
import json, os, subprocess
os.chdir('c:/Users/jp_lopez/projects/abapobjectscreation')

path = 'brain_v2/domains/domains.json'
d = json.load(open(path, encoding='utf-8'))

# Rewrite HR-Workflows with correct scope
d['domains']['HR-Workflows'] = {
    "axis": "functional",
    "description": "HR Workflows - long-running UNESCO domain covering end-user-facing HR self-service flows: Offboarding, Benefits Enrollment, Family Management (Change/Family Sister), Rental, Education Grant, Secondary Dependent. Built on SAPUI5 Fiori + WebDynpro ABAP + ASR Framework + ZCL_HR_FIORI_* handler classes. Activity observed continuously 2017-2026.",
    "parent_domain": "HCM",
    "knowledge_doc_path": "knowledge/domains/HR-Workflows/",
    "knowledge_docs": [
        "knowledge/domains/HR-Workflows/README.md",
        "knowledge/domains/HR-Workflows/staff_rejected_flow.md"
    ],
    "companions": [],
    "skills": [],
    "subtopics": {
        "staff_rejected_flow": {
            "description": "STAFF REJECT at Step 01 -> STAFF_REJECTED status -> creator revises + RESUBMITs (fresh Step 01) or cancels. NOT a pop.",
            "doc": "knowledge/domains/HR-Workflows/staff_rejected_flow.md",
            "transitions": ["APPROVE -> Step 02", "REJECT -> STAFF_REJECTED", "CANCEL -> CANCELLED"]
        },
        "return_step01_impossible": {
            "description": "Any RETURN attempt at Step 01 is impossible. UI doesn't offer the button. Handler has nothing to pop.",
            "doc": "knowledge/domains/HR-Workflows/staff_rejected_flow.md",
            "type": "UI_enforced_invariant"
        },
        "fiori_apps": {
            "description": "SAPUI5 self-service apps for HR workflows (long-running)",
            "apps": ["YHR_BEN_ENRL (Benefits Enrollment)","HRFIORI_OFFBOARDING","HRFIORI_CHANGE_SISTER","HRFIORI_FAMILY_SISTER","HR_FIORI_RENTAL","HR_FIORI_EDUCATION_GRANT","SECONDARY_DEPENDENT"]
        },
        "asr_framework": {
            "description": "SAP standard ASR HR forms framework, redefined with UNESCO behavior",
            "classes": ["CL_HCMFAB_*","CL_HRASR00GEN_SERVICE implementations","ZCL_HR_FIORI_* redefines"],
            "ref": "knowledge/domains/HCM/asr_framework_deep_dive.md"
        },
        "webdynpro_legacy": {
            "description": "Legacy WebDynpro ABAP components still maintained in parallel with Fiori",
            "object_types": ["WDYC", "WDYV"]
        },
        "core_hr_project_2025_2026": {
            "description": "Concentrated development burst starting 2025-10, with new editors joining the long-running HR-Workflows domain. 80 transports in 2025 (Oct-Dec) + 53 YTD 2026 (Jan-Mar) = 133 TRs on HR Fiori apps by 4-6 editors. Time-bound project overlay on top of the permanent HR-Workflows domain.",
            "start_date": "2025-10-29",
            "latest_activity": "2026-03-11",
            "new_editors_joined": {
                "S_IGUENINNI (Said Iguenini)": "40 HR-Fiori TRs, first 2025-10-29, latest 2026-02-12",
                "GD_SCHELLINC": "16 HR-Fiori TRs, first 2025-11-18, latest 2026-03-05",
                "N_VIDAL": "6 HR-Fiori TRs, first 2026-01-19, latest 2026-03-10",
                "G_SONNET": "6 HR-Fiori TRs, first 2026-02-24, latest 2026-03-10"
            },
            "returning_editors": {
                "N_MENARD": "Historical primary maintainer (158 TRs 2022-2026), continues through project"
            },
            "cross_domain_note": "S_IGUENINNI's 95 total transports 2025-2026 include both HR-Fiori (~40) and non-HR content (~55 larger bundles with ABAP methods, data elements, web apps). The 8 that include PSCC/PCYC objects were previously classified as PY-Finance collateral - they belong here in HR-Workflows / Core HR Project, not in PY-Finance."
        }
    },
    "objects": [
        "ZCL_HR_FIORI_OFFBOARDING_REQ","ZCL_ZHRF_OFFBOARD_DPC_EXT","ZCL_HRFIORI_CHANGE_SISTER","ZCL_HRFIORI_FAMILY_SISTER","ZCL_ZHR_BENEFITS_REQUE_DPC_EXT","ZCL_HR_FIORI_RENTAL","ZCL_HR_FIORI_EDUCATION_GRANT","ZCL_SECONDARY_DEPENDENT","YHR_BEN_ENRL","ZE_HRFIORI_OFFBOARDING_DOC_TX","ZE_HRFIORI_OFFBOARDING_LINK_TX","ZE_HRFIORI_OFFBOARDING_STEP_TX","CL_HCMFAB_SERVICE_FORM_PROC","CL_HRASR00GEN_SERVICE"
    ],
    "claims_ids": [60,61,62,63],
    "rules_ids": [],
    "incidents": [],
    "known_unknowns": ["KU-039","KU-040","KU-041"],
    "data_quality_open": [],
    "owner_role": "UNESCO HR Workflow Developer Team",
    "tier_1_editors_historical": ["N_MENARD"],
    "tier_1_editors_current_project": ["N_MENARD","S_IGUENINNI","GD_SCHELLINC","N_VIDAL","G_SONNET"],
    "primary_editors_stats_historical": {
        "N_MENARD": {
            "hr_fiori_trs_4yr_window": 158,
            "first": "2022-05-02",
            "latest": "2026-03-11",
            "role": "Primary HR-Workflows maintainer (permanent)"
        }
    },
    "primary_editors_stats_core_hr_project_2025_2026": {
        "S_IGUENINNI": {"hr_fiori_trs": 40, "total_trs": 95, "first": "2025-10-29", "latest": "2026-02-12"},
        "GD_SCHELLINC": {"hr_fiori_trs": 16, "first": "2025-11-18", "latest": "2026-03-05"},
        "N_VIDAL": {"hr_fiori_trs": 6, "first": "2026-01-19", "latest": "2026-03-10"},
        "G_SONNET": {"hr_fiori_trs": 6, "first": "2026-02-24", "latest": "2026-03-10"}
    },
    "transport_stats_full_history": {
        "2017": 15, "2018": 15, "2019": 33, "2020": 49, "2021": 74,
        "2022": 86, "2023": 21, "2024": 34, "2025": 80, "2026_ytd": 53
    },
    "coverage_pct": 50,
    "last_session_touched": 60,
    "primary_modules": ["HCM","PD","UI5","WDY"],
    "primary_processes": ["H2R"],
    "established_session": 60
}

with open(path,'w',encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
print(f"HR-Workflows domain corrected with long-running + Core HR Project 2025-2026 structure")

# Correct claim 62 (the Said-as-primary claim) and add claim 63 for N_MENARD
cp = 'brain_v2/claims/claims.json'
claims = json.load(open(cp, encoding='utf-8'))
for c in claims:
    if c['id'] == 62:
        c['claim'] = "S_IGUENINNI (Said Iguenini) joined the UNESCO HR-Workflows team in 2025-10 as part of the Core HR Project 2025-2026. His 95 transports (first 2025-10-29, latest 2026-02-12) are large development release bundles (avg 41 objects, 3921 total object hits) maintaining HR Fiori apps. He is NOT a long-running HR-Workflows primary editor - that role belongs historically to N_MENARD (158 TRs from 2022-05-02 across 4 years). Said is a Core HR Project 2025-2026 team member, not the HR-Workflows domain lead."
        c['evidence_for'].append({
            "type": "data_query",
            "ref": "Gold DB cts_transports year distribution for S_IGUENINNI",
            "cite": "Year breakdown: 2022=0, 2023=0, 2024=0, 2025=75, 2026=20 (YTD). First transport 2025-10-29, latest 2026-02-12. Zero activity pre-2025. Compare N_MENARD: 158 HR-Fiori TRs spanning 2022-05-02 to 2026-03-11 (continuous).",
            "added_session": 60
        })
        print("Claim #62 corrected")

next_id = max(c['id'] for c in claims) + 1
new_claim = {
    "id": next_id,
    "claim": "N_MENARD is the long-running primary maintainer of UNESCO HR-Workflows domain: 158 HR-Fiori transports from 2022-05-02 to 2026-03-11 (continuous across all 4 years). He is the only editor who has maintained HR-Workflows content every year 2022-2026 without interruption. The Core HR Project 2025-2026 added 4 new editors around him: S_IGUENINNI (Oct 2025), GD_SCHELLINC (Nov 2025), N_VIDAL (Jan 2026), G_SONNET (Feb 2026).",
    "claim_type": "verified_fact",
    "confidence": "TIER_1",
    "evidence_for": [
        {
            "type": "data_query",
            "ref": "Gold DB cts_transports + cts_objects filtered to HR Fiori object patterns",
            "cite": "N_MENARD HR-Fiori TR counts: 2022=43, 2023=20, 2024=34, 2025=47, 2026=14 (YTD). Total 158, first 2022-05-02 (D01K9B0968Q era), latest 2026-03-11. No other editor has continuous yearly activity.",
            "added_session": 60
        }
    ],
    "evidence_against": None,
    "related_objects": ["ZCL_HR_FIORI_OFFBOARDING_REQ","ZCL_HRFIORI_CHANGE_SISTER","YHR_BEN_ENRL"],
    "domain": "HR-Workflows",
    "created_session": 60,
    "resolved_session": None,
    "resolution_notes": None,
    "status": "active",
    "domain_axes": {
        "functional": ["HR-Workflows","HCM"],
        "module": ["HCM","PD","UI5","WDY"],
        "process": ["H2R"]
    }
}
claims.append(new_claim)
with open(cp,'w',encoding='utf-8') as f:
    json.dump(claims, f, indent=2, ensure_ascii=False)
print(f"Added claim #{next_id} for N_MENARD. Total claims: {len(claims)}")

# Rebuild brain
print("\nRebuilding brain_state...")
result = subprocess.run(['python','brain_v2/rebuild_all.py'], capture_output=True, text=True, timeout=300)
for line in result.stdout.splitlines()[-10:]:
    print(line)
