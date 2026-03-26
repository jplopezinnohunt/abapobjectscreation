# UNESCO SAP Project — PMO Activity Tracker

> **Living Document**: Updated at the end of each work session. Covers both technical analysis (reverse engineering) and development deliverables (React clone / Fiori extension).

Last Updated: 2026-03-26 | Session #017: Full project audit + protocol redesign

---

## 🟢 Workstream 1: HCM Fiori App Reverse Engineering

### Completed
| App | Status | Key Artifact |
| :--- | :--- | :--- |
| Personal Data (`Z_PERS_MAN_EXT`) | ✅ Done | `hcm_connectivity_map.md` |
| Address Management | ✅ Done | `entity_brain_map.md` |
| Family Management | ✅ Done | `entity_brain_map.md` |
| Offboarding (`ZHROFFBOARDING`) | ✅ Done (v2) | `fiori_app_analysis_offboarding_v2.md` |
| Benefit Monitor (`ZHRBENEFREQ`) | ✅ Done (v2) | `fiori_app_analysis_benefit_monitor_v2.md` |
| Benefit Enrollment (`YHR_BEN_ENRL`) | ✅ Done | `fiori_app_analysis_blueprint_benefits.md` |

### In Progress
| App | Status | Next Step |
| :--- | :--- | :--- |
| Extension Map (all apps) | 🔄 In progress | Complete two-layer map for Personal Data, Family, Address |

### Pending
| Item | Priority | Notes |
| :--- | :--- | :--- |
| Education Grant deep dive (Claims vs Advances logic) | 🔴 High | EGPYT flag, ZTHR_EG_ADVANCE / ZTHR_EG_CLAIM reconciliation |
| CRP App (`Z_CRP_SRV`) deep dive completion | 🟡 Medium | 19 open items — see `crp_management.md` Part IX |

---

## 🔵 Workstream 2: PSM / Finance Domain Analysis

### Completed
| Item | Status | Artifact |
| :--- | :--- | :--- |
| YFM1 Report Analysis | ✅ Done | `knowledge/domains/PSM/` |
| YPS8 Report Analysis | ✅ Done | `knowledge/domains/PSM/` |
| Finance Validations & Substitutions | ✅ Done | `finance_validations_and_substitutions_autopsy.md` |
| PSM Synthesis & Conclusions | ✅ Done | `psm_synthesis_final_conclusion.md` |
| PSM Posting Logic Audit (BA/YTFI_BA_SUBST/YXUSER) | ✅ Done (#010) | `basu_mod_technical_autopsy.md` |
| Cost Recovery Analysis (3 streams, 4,211 docs) | ✅ Done (#016) | `project_cost_recovery_analysis.md` |
| Golden Query (bseg_union+BKPF+FMIFIIT+PRPS) | ✅ Done (#016) | `project_golden_query.md` |
| BSIS/BSAS enrichment (+13 fields, 3.7M rows) | ✅ Done (#016) | `enrich_bsis_bsas_fields.py` |
| FMIFIIT OBJNRZ enrichment (2025 only, 976K rows) | ✅ Done (#016) | `enrich_fmifiit_objnrz.py` |

### Pending
| Item | Priority | Notes |
| :--- | :--- | :--- |
| FMIFIIT OBJNRZ enrichment for 2024+2026 | 🔴 High | Script proven on 2025, just needs re-run |
| BSEG PROJK extraction (declustered in P01) | 🔴 High | Alternative WBS source, no MANDT in WHERE |
| CRP Management deep dive (19 DPC items) | 🟡 Medium | See `crp_management.md` Part IX |
| WBS / Project linkage analysis (PRPS → FMFINCODE) | 🟡 Medium | Cross-domain reuse candidate |

---

## 🟠 Workstream 3: Architecture & Framework Documentation

### Completed
| Item | Status | Artifact |
| :--- | :--- | :--- |
| Entity Brain Map | ✅ Active | `knowledge/entity_brain_map.md` |
| SAP Configuration Reference | ✅ Active | `knowledge/sap_configuration_reference.md` |
| UNESCO Unified Fiori Design System | ✅ Done | `unesco_unified_fiori_design_system.md` |
| Standard Fiori Extension Guide | ✅ Done | `standard_fiori_extension_guide.md` |
| UNESCO Filter Registry Skill | ✅ Done | `.agents/skills/unesco_filter_registry/` |
| Fiori Extension Architecture Skill | ✅ Done | `.agents/skills/sap_fiori_extension_architecture/SKILL.md` |
| Session Open/Close checklists (CRP-style) | ✅ Done (#017) | `.agents/workflows/session_start.md` + `session_retro.md` |

### Pending
| Item | Priority | Notes |
| :--- | :--- | :--- |
| Two-layer extension map for all HCM apps | 🔴 High | Blocks Fiori replacement design |
| Knowledge Base Index update | 🟡 Medium | Stale since Session #009 |
| Update 10 skills with Session #016 discoveries | ✅ Done (#017) | All 10 updated |
| Create 3 new skills (change_audit, process_mining, crp_app) | ✅ Done (#017) | 28→31 skills |

---

## 🔴 Open Questions & Blockers

| # | Question / Blocker | Raised | Status |
| :--- | :--- | :--- | :--- |
| 1 | `O2PAGCON` returns `TABLE_WITHOUT_DATA` — cannot read `manifest.json` via RFC | 2026-03 | 🔴 Open |
| 2 | `ZTHRFIORI_STEP` table not available in RFC_READ_TABLE | 2026-03 | 🔴 Open |
| 3 | `CL_HCMFAB_BEN_ENROLLME_DPC_EXT` method listing fails | 2026-03 | ✅ Worked around (TRDIR) |
| 4 | `YHR_BEN_ENRL` — Adaptation Project or standalone? | 2026-03 | 🟡 To investigate |
| 5 | B2R extraction (FMIOI/FMBH/FMBL) returned 0 rows | 2026-03 | 🔴 Blocks B2R mining |
| 6 | SES gap — ESSR↔ESLL JOIN = 0 events (PACKNO mismatch?) | 2026-03 | 🔴 Blocks P2P SES |
| 7 | BSEG declustered but BSEG UNION view not yet in SQLite | 2026-03 | 🟡 Script ready |

---

## 📋 Backlog

- [ ] Map `ZTHRFIORI_UI5PRO` vs `ZTHRFIOFORM_VISI` — same or layered?
- [ ] Document `ASR Feeder` class pattern for Personal Data
- [ ] Validate BAdI `HCMFAB_B_MYFAMILYMEMBERS` implementation
- [ ] Run `/segw_interview` protocol for new OData service creation
- [ ] Review Knowledge Base Index and confirm all analyses indexed
- [ ] Extract YCL_HRPA_UI_CONVERT_0002_UN and YCL_HRPA_UI_CONVERT_0006_UN
- [ ] Document Coupa integration (COUPA* sessions doing PA30 BDC)
- [ ] Populate HCM/Reports folder (Z-reports in HCM namespace)

---

## 🟣 Workstream 4: P01 Production Intelligence & Monitoring

> Uses P01 (SNC/SSO only — confirmed working).

### Completed
| Item | Status | Artifact |
| :--- | :--- | :--- |
| `sap_system_monitor.py` — 7 reports | ✅ Done (#011) | `sap_system_monitor.py` |
| P01 SSO confirmed (SNC, no password) | ✅ Done (#011) | `.env` |
| BDC P01 analysis — `PRAAUNESC_SC` (89x) = Allos #1 | ✅ Done (#011) | BDC intelligence |
| Two-system architecture rule (D01=dev, P01=prod) | ✅ Done (#011) | Encoded everywhere |
| Job intelligence — 228 programs, 18 domains | ✅ Done (#014) | `sap_job_intelligence` |
| Interface intelligence — 239 RFC, 19 systems, 19.4K IDocs | ✅ Done (#014) | `sap_interface_intelligence` |
| Connectivity diagram (19 systems mapped) | ✅ Done (#014) | `connectivity_diagram.html` |

### Pending
| Item | Priority | Notes |
| :--- | :--- | :--- |
| Fix `RFC_SYSTEM_INFO` parsing — shows `?` | 🔴 High | Raw response dump needed |
| Analyze `PRAAUNESC_SC` via APQD → BAPI identification | 🔴 High | #1 Allos replacement target |
| P01 transaction usage report | 🟡 Medium | `--report transactions` |
| P01 obsolete programs | 🟡 Medium | `--report obsolete` |
| P01 runtime dumps | 🟡 Medium | `--report dumps` |
| Job source code extraction (top custom programs) | 🟡 Medium | ZFI_SWIFT_UPLOAD_BCM, YFI_COUPA_POSTING_FILE |

---

## 🟢 Workstream 5: Knowledge Brain & Data Extraction

### Completed
| Item | Status | Artifact |
| :--- | :--- | :--- |
| Brain — 73,877 nodes, 65,873 edges (8 sources) | ✅ Done (#014) | `sap_brain.py` |
| Progressive disclosure L1/L2/L3 | ✅ Done (#007) | `BRAIN_SUMMARY.md` |
| SQLite Gold DB — 42 tables, 24M+ rows, ~2.5GB | ✅ Done (#016) | `p01_gold_master_data.db` |
| BKPF (1.67M) + BSEG_UNION view (4.7M) | ✅ Done (#012) | Gold DB |
| EKKO + EKPO (procurement) | ✅ Done (#012) | Gold DB |
| CDHDR (7.8M) + CDPOS | ✅ Done (#011) | Gold DB |
| P2P complement (EBAN 26K, RBKP 210K, RSEG 77K) | ✅ Done (#011) | Gold DB |
| BSIS/BSAS enrichment (+13 fields) | ✅ Done (#016) | `enrich_bsis_bsas_fields.py` |
| Model routing (Opus/Sonnet/Haiku) | ✅ Done (#007) | `coordinator/SKILL.md` |
| 8 dashboards built | ✅ Done (#014) | Various locations |

### Pending
| Item | Priority | Notes |
| :--- | :--- | :--- |
| FMIFIIT OBJNRZ enrichment 2024+2026 | 🔴 High | Script proven on 2025 |
| BSEG PROJK extraction (declustered) | 🔴 High | No MANDT in WHERE |
| BSEG UNION view in SQLite | 🟡 Medium | CREATE VIEW (6 tables) |
| EKBE timestamp enrichment (BUDAT) | 🟡 Medium | Currently GJAHR proxy |
| ESLL extraction (last P2P table) | 🟡 Medium | Blocked by SES gap |
| Extract OData services (ZHR_OFFBOARD_SRV, ZHR_BENEFITS_REQUESTS_SRV) | 🟡 Medium | ADT API ready |
| Extract Benefits BSP | 🟡 Medium | BSP name from DPC manifest |
| COEP/COOI/JEST/RPSCO investigation | 🟢 Low | Empty — extract or remove |

---

## 🔵 Workstream 6: Process Discovery & Mining

### Completed
| Item | Status | Artifact |
| :--- | :--- | :--- |
| pm4py v2.7.20 installed | ✅ Done (#009) | pip package |
| `sap_process_discovery.py` — 8 CLI commands | ✅ Done (#009) | Core engine |
| CTS mining (DFG, variants, conformance) | ✅ Done (#009) | `process_discovery_output/cts_*.json` |
| FM/FMIFIIT mining (2M events, 616K cases) | ✅ Done (#009) | `fm_process_patterns.json` |
| CDHDR extractor + activity mapping (60+ rules) | ✅ Done (#009) | `extract_cdhdr.py` + `cdhdr_activity_mapping.py` |
| P2P process mining (848K events, 193K cases) | ✅ Done (#014) | `p2p_process_mining.html` |

### Pending
| Item | Priority | Notes |
| :--- | :--- | :--- |
| Fix B2R extraction (FMIOI/FMBH/FMBL = 0 rows) | 🔴 High | Debug date filters — BLOCKS B2R mining |
| OCEL multi-object P2P (pm4py 2.0) | 🟡 Medium | Object types: PO, Invoice, Vendor, Material |
| Brain integration (PROCESS_VARIANT/BOTTLENECK nodes) | 🟡 Medium | New node types for sap_brain.py |
| CDHDR activity mining (7.8M rows loaded) | 🟡 Medium | Mapping ready, execution pending |
| BRAIN_SUMMARY rebuild | 🟡 Medium | After brain integration |

---

## 🔧 Workstream 7: Skill & Protocol Maintenance (NEW — #017)

### Completed
| Item | Status | Artifact |
| :--- | :--- | :--- |
| Full project audit (87+ items catalogued) | ✅ Done (#017) | `session_017_retro.md` |
| Session Open/Close checklists (CRP-style) | ✅ Done (#017) | `.agents/workflows/` |
| PMO tracker updated (was 6 sessions stale) | ✅ Done (#017) | This file |

### Pending
| Item | Priority | Notes |
| :--- | :--- | :--- |
| Update 10 skills with #016 discoveries | ✅ Done (#017) | All 10 updated |
| Create `sap_change_audit` skill | ✅ Done (#017) | CDHDR/CDPOS mining |
| Create `sap_process_mining` skill | ✅ Done (#017) | pm4py 8 CLI commands |
| Create `crp_fiori_app` skill | ✅ Done (#017) | ASR+WF+DPC 19 items |
| Backfill retros for sessions #012-#016 | 🟢 Low | Knowledge gap but diminishing returns |
