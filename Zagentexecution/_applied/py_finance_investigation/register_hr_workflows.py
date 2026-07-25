"""Register HR-Workflows domain + claims about STAFF REJECT flow + reclassify Said."""
import json, os, subprocess
os.chdir('c:/Users/jp_lopez/projects/abapobjectscreation')

# === 1. Add HR-Workflows domain ===
path = 'brain_v2/domains/domains.json'
d = json.load(open(path, encoding='utf-8'))

if 'HR-Workflows' in d['domains']:
    print("HR-Workflows already exists - updating")
else:
    print("Creating HR-Workflows domain")

d['domains']['HR-Workflows'] = {
    "axis": "functional",
    "description": "HR Workflows - end-user-facing HR self-service flows at UNESCO: Offboarding, Benefits Enrollment, Family Management, Rental, Education Grant, Secondary Dependent. Built on SAPUI5 Fiori + WebDynpro ABAP + ASR Framework. Primary maintainer: S_IGUENINNI (Said Iguenini).",
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
            "description": "Any RETURN attempt at Step 01 is impossible. UI doesn't offer the button. Handler has nothing to pop (no previous step on stack).",
            "doc": "knowledge/domains/HR-Workflows/staff_rejected_flow.md",
            "type": "UI_enforced_invariant"
        },
        "fiori_apps": {
            "description": "SAPUI5 self-service apps for HR workflows",
            "apps": ["YHR_BEN_ENRL (Benefits Enrollment)","HRFIORI_OFFBOARDING","HRFIORI_CHANGE_SISTER","HRFIORI_FAMILY_SISTER","HR_FIORI_RENTAL","HR_FIORI_EDUCATION_GRANT","SECONDARY_DEPENDENT"]
        },
        "asr_framework": {
            "description": "SAP standard Adobe Service Request HR forms framework, redefined with UNESCO-specific behavior",
            "classes": ["CL_HCMFAB_*","CL_HRASR00GEN_SERVICE implementations","ZCL_HR_FIORI_* redefines"],
            "ref": "knowledge/domains/HCM/asr_framework_deep_dive.md"
        },
        "webdynpro_legacy": {
            "description": "Legacy WebDynpro ABAP components still maintained in parallel with Fiori",
            "object_types": ["WDYC", "WDYV"]
        }
    },
    "objects": [
        "ZCL_HR_FIORI_OFFBOARDING_REQ",
        "ZCL_ZHRF_OFFBOARD_DPC_EXT",
        "ZCL_HRFIORI_CHANGE_SISTER",
        "ZCL_HRFIORI_FAMILY_SISTER",
        "ZCL_ZHR_BENEFITS_REQUE_DPC_EXT",
        "ZCL_HR_FIORI_RENTAL",
        "ZCL_HR_FIORI_EDUCATION_GRANT",
        "ZCL_SECONDARY_DEPENDENT",
        "YHR_BEN_ENRL",
        "ZE_HRFIORI_OFFBOARDING_DOC_TX",
        "ZE_HRFIORI_OFFBOARDING_LINK_TX",
        "ZE_HRFIORI_OFFBOARDING_STEP_TX"
    ],
    "claims_ids": [],
    "rules_ids": [],
    "incidents": [],
    "known_unknowns": [],
    "data_quality_open": [],
    "owner_role": "UNESCO HR Workflow Developer (Said Iguenini lead)",
    "tier_1_editors": ["S_IGUENINNI"],
    "primary_editors_stats": {
        "S_IGUENINNI": {
            "transports_4yr": 95,
            "object_hits": 3921,
            "avg_objects_per_transport": 41,
            "documented_pct": 0,
            "with_py_collateral": 8
        }
    },
    "coverage_pct": 45,
    "last_session_touched": 60,
    "primary_modules": ["HCM","PD","UI5","WDY"],
    "primary_processes": ["H2R"],
    "established_session": 60
}

# Update HCM to include new child
hcm = d['domains']['HCM']
if 'child_domains' not in hcm: hcm['child_domains'] = []
if 'HR-Workflows' not in hcm['child_domains']:
    hcm['child_domains'].append('HR-Workflows')

# Remove S_IGUENINNI from PY-Finance tier_3 - he's actually HR-Workflows, not PY
if 'PY-Finance' in d['domains']:
    py = d['domains']['PY-Finance']
    if 'tier_3_editors' in py and 'S_IGUENINNI' in py['tier_3_editors']:
        py['tier_3_editors'].remove('S_IGUENINNI')
        py['note_on_siguenini'] = "S_IGUENINNI reclassified to HR-Workflows domain (Session #60). His 8 PY-collateral transports were dev bundles, not wage type config. See HR-Workflows domain."

with open(path,'w',encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
print(f"HR-Workflows registered. Total domains: {len(d['domains'])}")

# === 2. Add claims ===
cp = 'brain_v2/claims/claims.json'
claims = json.load(open(cp, encoding='utf-8'))
next_id = max(c['id'] for c in claims) + 1

new_claims = [
    {
        "id": next_id,
        "claim": "HR-Workflows domain at UNESCO: STAFF REJECT at Step 01 transitions the request to STAFF_REJECTED status. The creator then revises and RESUBMITs (which creates a fresh Step 01 iteration, not a pop/resume of the rejected workflow) OR cancels. This is NOT a stack-pop operation.",
        "claim_type": "business_rule",
        "confidence": "TIER_2",
        "evidence_for": [
            {
                "type": "user_attestation",
                "ref": "Session #60 user business description 2026-04-22",
                "cite": "User: 'STAFF REJECT Step 01 -> STAFF_REJECTED status. Creator revises + RESUBMITs (back to Step 01 fresh) OR cancels. NOT a pop.'",
                "added_session": 60
            }
        ],
        "evidence_against": None,
        "related_objects": ["ZCL_HR_FIORI_OFFBOARDING_REQ","ZCL_ZHRF_OFFBOARD_DPC_EXT","ZCL_HRFIORI_CHANGE_SISTER","ZCL_ZHR_BENEFITS_REQUE_DPC_EXT"],
        "domain": "HR-Workflows",
        "created_session": 60,
        "resolved_session": None,
        "resolution_notes": None,
        "status": "active",
        "needs_validation": ["source code confirmation via handler classes", "which class.method handles the REJECT transition", "which container is created on RESUBMIT"],
        "domain_axes": {
            "functional": ["HR-Workflows","HCM"],
            "module": ["HCM","PD","UI5"],
            "process": ["H2R"]
        }
    },
    {
        "id": next_id+1,
        "claim": "At Step 01 of any UNESCO HR Workflow, a RETURN action is impossible by design. The Fiori/WebDynpro UI does not render the RETURN button when current_step=01, and if the handler were somehow invoked programmatically it would have nothing to pop (there is no previous approver). This is a UI-enforced invariant, not a runtime guard.",
        "claim_type": "business_rule",
        "confidence": "TIER_2",
        "evidence_for": [
            {
                "type": "user_attestation",
                "ref": "Session #60 user business description 2026-04-22",
                "cite": "User: 'Any RETURN attempt at Step 01 - Impossible - UI doesn't offer the button. Handler has nothing to pop.'",
                "added_session": 60
            }
        ],
        "evidence_against": None,
        "related_objects": ["ZCL_HR_FIORI_OFFBOARDING_REQ","ZCL_ZHRF_OFFBOARD_DPC_EXT"],
        "domain": "HR-Workflows",
        "created_session": 60,
        "resolved_session": None,
        "resolution_notes": None,
        "status": "active",
        "needs_validation": ["find the UI5 controller that hides the RETURN button at Step 01", "confirm the handler class has a defensive guard"],
        "domain_axes": {
            "functional": ["HR-Workflows","HCM"],
            "module": ["HCM","PD","UI5","WDY"],
            "process": ["H2R"]
        }
    },
    {
        "id": next_id+2,
        "claim": "S_IGUENINNI (Said Iguenini) is the primary UNESCO HR Workflow developer, not a PY-Finance config editor. His 95 transports over 4 years (2022-2026) are large development release bundles (average 41 objects each, 3921 total object hits) maintaining Fiori apps (YHR_BEN_ENRL, Offboarding, Family Sister, Benefits, Rental, Education Grant) and WebDynpro legacy. The 8 transports that include PSCC/PCYC schemas are HR-Workflows bundles where PY objects are shipped as collateral, not intentional wage type configuration. He belongs in the HR-Workflows domain, not PY-Finance Tier-3.",
        "claim_type": "verified_fact",
        "confidence": "TIER_1",
        "evidence_for": [
            {
                "type": "data_query",
                "ref": "Gold DB cts_transports + cts_objects for as4user=S_IGUENINNI",
                "cite": "95 transports, 3921 object hits, 0/95 with E07T description. Sample D01K9B0E7W 2025-12-04 obj_count=78 contains Fiori WAPP/YHR_BEN_ENRL + 26 i18n files + methods + DPC_EXT redefines. Raw data in Zagentexecution/py_finance_investigation/fp_ms_si_categorized.json.",
                "added_session": 60
            },
            {
                "type": "user_correction",
                "ref": "Session #60 user message 2026-04-22",
                "cite": "User created HR-Workflows domain specifically for this editor's work. Classification reassigned from PY-Finance Tier-3 (collateral) to HR-Workflows Tier-1 (primary maintainer).",
                "added_session": 60
            }
        ],
        "evidence_against": None,
        "related_objects": ["YHR_BEN_ENRL","ZCL_HR_FIORI_OFFBOARDING_REQ","ZCL_HRFIORI_CHANGE_SISTER","ZCL_ZHRF_OFFBOARD_DPC_EXT"],
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
]
claims.extend(new_claims)
with open(cp,'w',encoding='utf-8') as f:
    json.dump(claims, f, indent=2, ensure_ascii=False)
print(f"Added 3 claims (IDs {next_id}-{next_id+2}). Total claims: {len(claims)}")

# === 3. Add KUs for validation ===
kup = 'brain_v2/agi/known_unknowns.json'
kus = json.load(open(kup, encoding='utf-8'))
nums = [int(k['id'].split('-')[1]) for k in kus if k['id'].startswith('KU-')]
next_n = max(nums) + 1
new_kus = [
    {
        "id": f"KU-{next_n:03d}",
        "question": "Which exact class.method in the UNESCO HR Fiori stack handles the STAFF REJECT at Step 01 transition to STAFF_REJECTED status?",
        "why_unknown": "Claim #60 is TIER_2 (user-attested). Needs source-code anchor to move to TIER_1. Candidates: ZCL_HR_FIORI_OFFBOARDING_REQ, ZCL_ZHRF_OFFBOARD_DPC_EXT, ZCL_HRFIORI_CHANGE_SISTER, ZCL_ZHR_BENEFITS_REQUE_DPC_EXT.",
        "raised_session": 60,
        "domain": "HR-Workflows",
        "blocks_incident": None,
        "investigation_cost_estimate": "LOW",
        "owner_session": None,
        "notes": "Grep extracted_code/ for 'STAFF_REJECTED' string. Should resolve in one pass."
    },
    {
        "id": f"KU-{next_n+1:03d}",
        "question": "Which UI5 controller conditionally hides the RETURN button at Step 01? Is the visibility bound to current_step directly or to a backend metadata field?",
        "why_unknown": "Claim #61 is TIER_2 (user-attested). Need to anchor to the controller.js that enforces the invariant.",
        "raised_session": 60,
        "domain": "HR-Workflows",
        "blocks_incident": None,
        "investigation_cost_estimate": "LOW",
        "owner_session": None,
        "notes": "Check WAPP/YHR_BEN_ENRL/CONTROLLER/*.CONTROLLER.JS for button visibility binding. May be centralized in a parent view or in i18n-driven metadata."
    },
    {
        "id": f"KU-{next_n+2:03d}",
        "question": "When a request is RESUBMITTED after STAFF REJECT, is a new workflow container (SWWWIHEAD) created or is the rejected one reused? Audit-trail implication.",
        "why_unknown": "Claim #60 states 'fresh Step 01' but doesn't specify at the workflow-container level. For audit trails and incident reconstruction, we need to know if the history of the rejected workflow is preserved separately or overwritten.",
        "raised_session": 60,
        "domain": "HR-Workflows",
        "blocks_incident": None,
        "investigation_cost_estimate": "LOW",
        "owner_session": None,
        "notes": "Query SWWWIHEAD/SWW_CONTOB for a known rejected-then-resubmitted request. Compare WI_ID before and after resubmit."
    }
]
kus.extend(new_kus)
with open(kup,'w',encoding='utf-8') as f:
    json.dump(kus, f, indent=2, ensure_ascii=False)
print(f"Added 3 KUs (KU-{next_n:03d}/KU-{next_n+1:03d}/KU-{next_n+2:03d}). Total KUs: {len(kus)}")

# === 4. Rebuild brain ===
print("\nRebuilding brain_state...")
result = subprocess.run(['python','brain_v2/rebuild_all.py'], capture_output=True, text=True, timeout=300)
for line in result.stdout.splitlines()[-10:]:
    print(line)
