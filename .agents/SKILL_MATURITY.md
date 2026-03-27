# Skill Maturity Companion
*Baseline: Session #018 | 2026-03-26 | 31 skills evaluated | Updated Session #023 | 2026-03-27 | 36 skills*

---

## Maturity Scale

| Score | Label | Criteria |
|-------|-------|----------|
| 4 | **Production** | SKILL.md complete, triggers/rules clear, references exist, used in real sessions, comprehensive docs |
| 3 | **Functional** | SKILL.md solid, works reliably, may lack polish or edge cases |
| 2 | **Draft** | SKILL.md exists but incomplete, stub-level, needs work |
| 1 | **Stub** | Minimal/no content, placeholder only |

---

## Production (Score 4) — 16 Skills

| Skill | Layer | Capability | Key Metric |
|-------|-------|-----------|------------|
| coordinator | Orchestration | Master routing (B2R/H2R/P2P/T2R/P2D), progressive disclosure, brain query | Routes all 5 UNESCO processes + payment routing |
| sap_expert_core | Knowledge | FI/PSM/ABAP/Workflow/OData senior consultant knowledge | ECC 6.0 proven |
| sap_data_extraction | L2 | RFC extraction pipeline, Gold DB, enrichment patterns | 42 tables, 24M+ rows, 2.5GB |
| sap_class_deployment | L9 | ABAP class creation via RFC/ADT, 6 CCIMP strategies | 16 scripts, CRP OData proven |
| sap_system_monitor | L8 | SM04/SM35/SM37/ST22 operational dashboard | 228 jobs classified |
| sap_webgui | Framework | Playwright automation, Select-Then-Toolbar, 103 experiments | lib/ 8 modules |
| sap_fiori_tools | L6 | Fiori CLI, manifest editing, BSP extraction | App structure + OData |
| sap_reverse_engineering | L4 | OData service logic extraction, 5-phase protocol | HCM specialized |
| sap_adt_api | L4 | ADT REST: 14 object types, CSRF flow, activation | D01 confirmed |
| sap_transport_intelligence | L5 | CTS forensics, risk taxonomy, 100+ object classifications | 7,745 transports |
| psm_domain_agent | Domain | FM/budget, WRTTP filter, golden query, AVC engine | 2M+ rows |
| hcm_domain_agent | Domain | HR lifecycle, Allos, ASR, offboarding Fiori | 89 Allos sessions |
| fi_domain_agent | Domain | GL/BKPF+BSEG, OB28/OBBH, FM-FI bridge, cost recovery | 3-stream posting |
| sap_payment_bcm_agent | L7/FI | F110, BCM, DMEE, FBZP chain, workflow 90000003, SWIFT, payroll refs | 10 co codes, 2 banks, 4 processes — #021+#022+#023 |
| sap_segw | Framework | SEGW OData service creation: 5 workflows, element IDs, Playwright patterns | Merged segw_automation #023 |
| sap_change_audit | L7 | CDHDR/CDPOS 7.8M rows, 100+ TCODE mappings, compliance SQL templates | 4 ready-to-run compliance reports |

---

## Functional (Score 3) — 11 Skills

| Skill | Layer | Capability | Gap to Production |
|-------|-------|-----------|-------------------|
| sap_job_intelligence | L8 | SM37 deep analysis, 228 programs/18 domains | Needs failure correlation patterns |
| sap_interface_intelligence | L8 | 239 RFC destinations, 19 systems, 19.4K IDocs | Needs IDoc error analysis |
| sap_bdc_intelligence | L10 | SM35 forensics, Allos vs Y1 payroll | Needs replay automation |
| sap_enhancement_extraction | L4 | SE20 composite mining, BAdI discovery | Needs cross-domain impact matrix |
| sap_process_mining | L7 | pm4py engine, 8 CLI commands, 848K P2P events | Needs OCEL multi-object |
| sap_payment_e2e | L7/FI | Payment lifecycle mining: 1.4M events, 550K cases, cycle times | REGUH/REGUP partially extracted; FEBEP=0 |
| sap_transport_companion | L5 | HTML companion generation from RFC transport extract | Proven on 2 transports (#019); needs wider use |
| sap_company_code_copy | FI | EC01 copy protocol, 41-task checklist, NR gaps, FBZP chain | STEM still broken (B9); awaiting fix validation |
| skill_creator | Meta | 33-skill hierarchy, creation protocol, maturity rubric | Needs live creation walkthrough example |
| unesco_filter_registry | Cross | WRTTP_FM, BLART_FI, BCM_RULE filters documented | Needs GL account filter, CO object filter |
| sap_debugging_and_healing | Framework | Triple Threat (ST22+SU53+SM21) + RFC/Playwright real patterns | End-to-end autonomous loop not yet tested |
| crp_fiori_app | L6 | CRP architecture, ASR hybrid, 3-stream posting | 19 open implementation items |
| sap_fiori_extension_architecture | L6 | Fiori extension discovery, BAdI vs ENHO vs clone | Needs real extension examples |

---

## Draft (Score 2) — 4 Skills

| Skill | Capability | What's Missing |
|-------|-----------|----------------|
| sap_native_desktop | SAP GUI Scripting via win32com | Not heavily tested, no real examples |
| sap_automated_testing | OData HTTP validation | Only HTTP 200 checks, no GUI tests |
| abapgit_integration | abapGit commit workflow | Not fully automated |
| parallel_html_build | Part-based HTML generation | Niche, vis.js specific |

---

## Stub (Score 1) — 2 Skills

| Skill | Status | Action Needed |
|-------|--------|---------------|
| notion_integration | Notion MCP placeholder | Build real extraction examples |
| ~~segw_automation~~ | ~~Deprecated #023~~ | ~~Merged into sap_segw~~ |

---

## Consolidation Opportunities

| Action | Skills | Rationale |
|--------|--------|-----------|
| ~~**Merge** sap_segw + segw_automation~~ | ~~Done #023~~ | ~~Merged, segw_automation deprecated~~ |
| **Promote** | sap_job_intelligence → Production | Add failure correlation, nearly there |
| **Promote** | sap_process_mining → Production | Add OCEL, nearly there |
| **Promote** | sap_payment_e2e → Production | Needs REGUH/REGUP full extraction + FEBEP clarification |
| **Deprecate or Flesh Out** | notion_integration | Either build it or remove the stub |
| **Deprecate or Flesh Out** | sap_native_desktop | Rarely used, WebGUI covers most cases |

---

## Coverage Map

```
UNESCO Process → Skills Coverage

B2R (Budget-to-Report):
  [4] psm_domain_agent → [4] fi_domain_agent → [4] sap_data_extraction
  [4] sap_change_audit → [3] sap_process_mining

H2R (Hire-to-Retire):
  [4] hcm_domain_agent → [3] sap_bdc_intelligence → [4] sap_reverse_engineering
  [3] sap_fiori_extension_architecture

P2P (Procure-to-Pay):
  [4] fi_domain_agent → [3] sap_process_mining → [4] sap_data_extraction
  [4] sap_change_audit

Payment (P2P sub-process):
  [4] sap_payment_bcm_agent → [3] sap_payment_e2e → [3] sap_company_code_copy

T2R (Travel-to-Claim):
  [4] psm_domain_agent → [4] fi_domain_agent
  (gap: no dedicated travel skill)

P2D (Project-to-Close):
  [4] psm_domain_agent → [4] fi_domain_agent
  (gap: no dedicated PS skill)

Cross-Cutting:
  [4] coordinator, sap_expert_core, sap_transport_intelligence
  [4] sap_adt_api, sap_class_deployment, sap_system_monitor
  [4] sap_segw (merged), [3] sap_job_intelligence, sap_interface_intelligence
  [3] skill_creator, unesco_filter_registry, sap_debugging_and_healing
```

---

## Metrics Summary

| Metric | Value |
|--------|-------|
| Total Skills | 36 (+5 new: sap_payment_bcm_agent, sap_payment_e2e, sap_transport_companion, sap_company_code_copy; segw_automation deprecated) |
| Production-Ready | 16 (44%) |
| Functional | 13 (36%) |
| Draft | 4 (11%) |
| Stub | 2 (6%) — segw_automation deprecated, notion_integration placeholder |
| UNESCO Processes Covered | 5/5 (T2R and P2D have gaps; Payment sub-process now 3-skill chain) |
| Layers Covered | 10/10 |
| Consolidation Done | sap_segw + segw_automation merged (#023) |
| Next Consolidation | sap_process_mining + sap_payment_e2e (same pm4py engine) |

---

*Next review: After 5 sessions or when 3+ skills change maturity level*

---

## AI Diligence Statement

| Field | Value |
|-------|-------|
| AI Role | Read all 31 SKILL.md files, scored maturity on 4-point scale, identified gaps and consolidation opportunities |
| Model | Claude Opus 4.6 (1M context) via Claude Code CLI |
| Human Role | JP Lopez directed the evaluation as part of BROADCAST-001, will validate scores against real usage |
| Verification | Scores based on SKILL.md content analysis [INFERRED]. Count of 13 Production skills [VERIFIED]. Coverage map cross-referenced against UNESCO 5-process model [VERIFIED]. Session usage not cross-checked [GAP]. |
| Accountability | JP Lopez maintains full responsibility |
