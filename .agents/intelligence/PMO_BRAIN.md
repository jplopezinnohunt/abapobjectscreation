# UNESCO SAP — Project Brain + PMO Brain
> Two brains, one project. Updated every session. Read alongside `PROJECT_MEMORY.md`.
> **Last reconciled**: Session #054 (2026-04-14) — **Formalization audit + Core Principles bootstrap.** User-driven audit revealed 13 of 16 session #053 commitments were never formalized in PMO. Response: 3 Core Principles established (CP-001 Knowledge over velocity, CP-002 Preserve first, CP-003 Precision evidence facts) as constitutional layer 0 of brain_state.json. 4 new operational rules (86 total: retro_to_pmo_bridge CRITICAL, never_drop_columns HIGH, sample_before_aggregating + explicit_aggregation_filter MEDIUM). H42 schema migration executed: claims.evidence_for/against str → list[typed]. 11 new H-items (H41-H51). H36 refreshed (20→71 blind_spots). See `brain_v2/core_principles/core_principles.json` + `knowledge/session_retros/session_054_retro.md`.
> **Session #050** prior: Brain v3 validation + incident methodology bootstrap. 12 deliverables. H35 closed. 7 new feedback rules (58 total). 2 new brain layers (incidents=11, blind_spots=12). Brain coverage metric introduced: 75.6%. Object count 102→136 via force-include. New skill `sap_incident_analyst` + subagent `incident-analyst`. New session-close Phase 4b (Capture SAP Learnings).
> Session #049 prior: Brain v3 hybrid rebuild + portability + AGI self-awareness. 16 deliverables.
> Session #048 prior: INC-000006073 RCA + Travel/BusinessPartner domain creation. 14 deliverables.
> Session #042 prior: Brain v2 Explorer + Bank consolidation. 10 deliverables.
> **Current count**: 0 Blocking | **14** High (4 pre-054 + H41-H51 except H42 closed = 10 new) | **32** Backlog = **46 total** (Session #054: 1 closed (H42 done in-session), 10 high added (H41,H43-H51), 1 refreshed (H36→H50 successor). Net +10 reflects formalization debt repayment.)
> **Reward function**: items_shipped - items_added > 0 per session. Net-zero is failure.
> **Growth paradigm**: Skills grow, never consolidate. Memory grows, no line limit. Knowledge is routed via `skill_coordinator`, never compressed.

---

## PROJECT BRAIN — What We Built

### The System (as of 2026-03-26)

```
UNESCO SAP Intelligence Toolkit — 10 Capability Layers, 38 Skills
├── L1: SAP Connectivity      → pyrfc + SNC/SSO (D01 dev / P01 prod)
├── L2: Data Extraction       → ~2.5GB gold SQLite DB, 24M+ rows, 68 tables
├── L3: Validation/Domain     → sap_brain.py (73.9K nodes, 3-level access), 4 domain agents + coordinator
├── L4: Code Extraction       → ADT API, BSP/OData/Enhancement extraction
├── L5: Transport Intel       → CTS dashboard, 7,745 transports analyzed
├── L6: Fiori Development     → Offboarding clone (React+UI5 Web Components)
├── L7: Process Intelligence  → process-intelligence.html + pm4py (848K P2P events)
├── L8: System Monitoring     → sap_system_monitor.py (SM04/SM35/SM37/ST22)
├── L9: Class Deployment      → 16 scripts (create, deploy, verify ABAP classes)
├── L10: BDC Intelligence     → bdc_full_inventory.py (Allos/Y1 payroll forensics)
└── L11: Integration Intel    → 38 systems, 334 RFC FMs, 7 UNESCO .NET apps mapped

Governance: .agents/GOVERNANCE.md + SKILL_MATURITY.md (38 skills scored)
Companions: 15 HTML (landing page + 14 domain companions)

Each layer FEEDS the others:
  L2→L3 (data validates domain), L5→L4 (transports→code targets),
  L3→L6 (domain rules→app logic), L4→L6 (code→rebuild),
  L2→L7 (event logs), L5→L7 (CTS data)
```

### Key Intelligence Discovered

| Finding | Impact |
|---------|--------|
| P01 SSO works, no password needed | All prod monitoring is passwordless |
| `PRAAUNESC_SC` BDC — 89 sessions by `_COLLOCA` | #1 Allos replacement target |
| `OBBATCH` — 109 automated sessions | Background automation via BDC |
| 0 Fiori apps in P01 (13 in D01) | None have reached production yet |
| 826 programs in P01 vs 1000 in D01 | 174 dev objects not promoted |
| 33 tables discovered via code analysis | Auto brain edge `READS_TABLE` |
| PBC generates ~90% of CDHDR volume | Filter OBJECTCLAS='FMRESERV' for non-FM analysis |
| BSEG declustered in P01 | Can read PROJK directly via RFC_READ_TABLE (no MANDT in WHERE) |
| FMIFIIT.KNBUZEI = BSIS.BUZEI | Perfect 1:1 line-level FM↔FI join |
| FMIFIIT.OBJNRZ = PRPS.OBJNR | Proper WBS element recovery (85.9% coverage for 2025) |

### What the Brain Knows (73,877 nodes — Session #014)
- **64,766 FUNDs** + 710 FUND_CENTERs + 7 FUND_AREAs (with aggregate metadata)
- **7,745 TRANSPORTs** (full CTS inventory)
- **59 Code objects**: 2 BSP Apps, 13 Classes, 44 Tables, App Areas, Domains
- **45 KNOWLEDGE_DOC nodes**: cross-referenced to classes and tables
- **23 SKILL nodes**: L1-L7 + Meta layer + sap_data_extraction
- **10 DOCUMENT nodes**: expert seeds (YRGGBS00, doc_reference, FI substitution sources)
- **5 PROCESS nodes**: B2R, H2R, P2P, T2R, P2D — UNESCO core processes
- **8 JOINS_VIA edges**: table-to-table foreign keys
- **3-level access**: L1 BRAIN_SUMMARY.md, L2 `--focus`, L3 full JSON

### Multi-Agent Architecture (Session #006)
- **Coordinator**: `.agents/skills/coordinator/SKILL.md` — routes by process type
- **PSM Domain Agent**: `.agents/skills/psm_domain_agent/SKILL.md` — FM/budget
- **HCM Domain Agent**: `.agents/skills/hcm_domain_agent/SKILL.md` — HR/employee lifecycle
- **FI Domain Agent**: `.agents/skills/fi_domain_agent/SKILL.md` — GL/validation/substitution

---

## PMO BRAIN — Single Source of Truth for ALL Pending Work

> **RULE**: Every pending item lives HERE. SESSION_LOG entries point here, not the reverse.
> **RECONCILIATION**: At session close, EVERY new pending item must be added here.
> Items completed mid-session get ~~struck through~~ with session # and date.

### 🔴 BLOCKING — Cannot progress without these

| # | Task | First raised | Blocks | Notes |
|---|------|-------------|--------|-------|
| ~~B1~~ | ~~FMIFIIT OBJNRZ enrichment 2024+2026~~ | ~~#016~~ | ~~Golden Query WBS coverage~~ | ~~Done #028: 2024 (16 periods, 27 min) + 2026 (3 periods, 4 min). All years now enriched.~~ |
| ~~B2~~ | ~~BSEG PROJK extraction~~ | ~~#016~~ | ~~WBS for ~9.5% non-FM docs~~ | ~~Closed #035: BSEG is not a table — it's a JOIN (bseg_union VIEW). Golden Query covers 85.9% WBS via FMIFIIT.OBJNRZ→PRPS. Remaining 9.5% = clearing lines without FM match, marginal value. Resolved by design.~~ |
| ~~B3~~ | ~~CO tables: COOI, COEP, RPSCO~~ | ~~#005~~ | ~~Entire CO cost layer missing~~ | ~~Done #035: 3,451,708 rows (COOI 773K + COEP 2.55M + RPSCO 127K). DD03L-verified fields. Period-by-period extraction for VPN resilience. Gold DB loaded. Anchor estimate was 1.6M — actual 2x larger.~~ |
| ~~B4~~ | ~~B2R tables: FMIOI+FMBH+FMBL verification~~ | ~~#009~~ | ~~B2R lifecycle mining~~ | ~~Done — verified #028: FMIOI=1.8M, FMBH=287K, FMBL=319K rows~~ |
| ~~B5~~ | ~~SES gap: ESSR↔ESLL PACKNO mismatch~~ | ~~#011~~ | ~~P2P service receipts~~ | ~~Done — verified #028: 707K PACKNO matched (99.99% of ESSR)~~ |
| ~~B6~~ | ~~EKBE BUDAT enrichment~~ | ~~#018~~ | ~~P2P temporal precision~~ | ~~Done #028: 363K rows enriched (BUDAT+BLDAT+BEWTP+MENGE+DMBTR+WRBTR+WAERS). 2024=161K, 2025=175K, 2026=27K. MEINS auth-restricted. GJAHR=0000 (119K delivery notes) skipped.~~ |
| ~~B7~~ | ~~CDHDR process mining~~ | ~~#011~~ | ~~Audit trail analysis~~ | ~~Done — verified #028: cdhdr_activity_mapping.py exists with pm4py integration~~ |
| ~~B8~~ | ~~P2P bottleneck/temporal analysis~~ | ~~#009~~ | ~~P2P insights~~ | ~~Done — verified #028: p2p_process_mining.py + HTML dashboard built~~ |
| ~~B9~~ | ~~Fix STEM FBZP chain~~ | ~~#019~~ | ~~N/A~~ | ~~Closed #028: STEM not in T001. 9 real co codes (IBE,ICBA,ICTP,IIEP,MGIE,UBO,UIL,UIS,UNES) all configured~~ |
| ~~B10~~ | ~~Update remaining stale skills~~ | ~~#017~~ | ~~Agents using outdated instructions~~ | ~~KILLED #036: subsumed by `SKILLS_CONSOLIDATION_PLAN.md` (38→6 archetypes). The 3 stale skills (sap_native_desktop, sap_automated_testing, sap_enhancement_extraction) will be absorbed or deleted during consolidation, not individually "updated". Item was ceremonial maintenance, not strategic work.~~ |

### 🟡 HIGH — Next available session

| # | Task | First raised | Category | Notes |
|---|------|-------------|----------|-------|
| ~~H1~~ | ~~Create `sap_payment_e2e` skill~~ | ~~#019~~ | ~~Skill~~ | ~~Done #021~~ |
| ~~H2~~ | ~~Create `sap_process_mining` skill~~ | ~~#017~~ | ~~Skill~~ | ~~Done — SKILL.md exists, Functional (3). OCEL pending as G1~~ |
| ~~H3~~ | ~~Create `sap_change_audit` skill~~ | ~~#017~~ | ~~Skill~~ | ~~Done — SKILL.md exists, Functional (3). Compliance template → added #023~~ |
| ~~H4~~ | ~~BSEG UNION view in SQLite~~ | ~~#011~~ | ~~Data~~ | ~~Done — bseg_union VIEW exists, 4.7M rows (BSIS+BSAS+BSIK+BSAK+BSID+BSAD). Verified #023~~ |
| ~~H5~~ | ~~Merge sap_segw + segw_automation~~ | ~~#018~~ | ~~Skill~~ | ~~Done #023 — sap_segw now comprehensive (5 workflows, element IDs, full troubleshooting). segw_automation redirects.~~ |
| ~~H6~~ | ~~Brain integration of P2P~~ | ~~#009~~ | ~~Brain~~ | ~~KILLED #036: brain is write-only. 73K nodes built, zero decisions routed through it. Adding PROCESS_VARIANT nodes is more write, not more value. Resurrect only if a decision needs graph traversal that SQL can't do.~~ |
| ~~H7~~ | ~~Design Fiori replacement for PRAA*~~ | ~~#005~~ | ~~App~~ | ~~Moved to backlog #036 as G54 (was deprioritized #028 but never actually moved)~~ |
| ~~H8~~ | ~~P01 transaction usage report~~ | ~~#005b~~ | ~~Monitoring~~ | ~~Done — verified #028: sap_system_monitor.py --report transactions works~~ |
| ~~H9~~ | ~~P01 runtime dumps report~~ | ~~#005b~~ | ~~Monitoring~~ | ~~Done — verified #028: sap_system_monitor.py --report dumps works~~ |
| ~~H10~~ | ~~Document Coupa integration~~ | ~~#002~~ | ~~Analysis~~ | ~~KILLED #036: SUPERSEDED. `integration_map_complete.md` (#035) documented COUPA dual-channel (file + BDC). `project_coupa_file_integration.md` memory exists. This item was already done but never closed.~~ |
| ~~H11~~ | ~~**Extract Benefits BSP + HCM Z-reports (merged H11+H12)**~~ | ~~#005b (merged #036)~~ | ~~Code~~ | ~~**Done #038** via RFC (not ADT — avoided the .env password dependency). 4 HCMFAB MYFAMILY classes extracted: `ZCL_ZHCMFAB_MYFAMILYME_DPC` + `_DPC_EXT` + `_MPC` + `_MPC_EXT`. 7 BSP apps discovered in ZFIORI package: YHR_BEN_ENRL (Benefits Enrollment), YHR_EDURENT_APV, YHR_OFFBOARDEMP, YHR_OFFBRD, ZHRBENEFREQ, ZHREDURENTALADM, Z_HCMPROCES_EXT. 222 HCM namespace Z-reports discovered, 12 extracted as sample (including ZZHRPAF02 186KB, ZHRAUTOSTEP, ZNHR_LOAD_PAYSCALE_GROUPS). Channel: `READ REPORT` via `RFC_ABAP_INSTALL_AND_RUN` over SNC/SSO — same channel as H29.~~ |
| ~~H12~~ | ~~Populate HCM/Reports folder~~ | ~~#005b~~ | ~~Code~~ | ~~MERGED into H11 #036.~~ |
| ~~H13~~ | ~~**BCM dual-control gap remediation**~~ | ~~#021/#027~~ | ~~Audit~~ | ~~**Done #037 — Deliverable 1 shipped.** Monitor script `Zagentexecution/bcm_dual_control_monitor.py`, HTML companion `bcm_dual_control_audit.html`, executive summary `knowledge/domains/BCM/h13_executive_summary.md`. Reframe: automation debt, not fraud. 3,359 same-user batches in scope / $656M exposure. Top 2 = C_LOPEZ + I_MARQUAND (94.7% / 92.9% self-approval) — HQ treasury manual Wednesday cycle, no 3rd operator. F_DERAKHSHAN reclassified (74% dual-controlled). +1,366 drift since #027 (15 sessions of inaction cost). Paths 2–5 (carve-out, role split, workflow mod, automation) spawn as H13a/b/c/d in next review.~~ |
| ~~H14~~ | ~~**Extract YWFI package source from D01**~~ | ~~#021~~ | ~~Code~~ | ~~**Done #038** via RFC (TADIR query DEVCLASS='YWFI' → 37 objects). Full extraction: classes, programs, FUGRs with method includes. Key find: `ZWF_GET_CERTIFYING_OFFICER` (NOT `Z_WF_GET_CERTIFYING_OFFICER` as PMO said — wrong underscore) is a FUGR with 5 includes (TOP+UXX+U01+U02+U03, 7KB of logic). Other extracted FUGRs: `ZFI_PAYREL_EMAIL`, `Z_WF_FI_EVENT_PAYMENT_METH`, `Z_WF_FI_EXCLUDE_NOTIF`, `Z_WF_FI_GET_CLASSIC_VALID`. Programs: `YBSEG_REL`, `ZNOTREJECT`. Output: `extracted_code/YWFI/`.~~ |
| ~~H16~~ | ~~Investigate 229 PAYROLL IBC17 (Failed) BCM batches~~ | ~~#026~~ | ~~Audit~~ | ~~Closed #028: ALL 2,056 IBC17 failures are 2021-2022 (BCM activation outage Jul21-Dec22). Zero failures in 2024-2026. Root cause: BCM activated mid-2021, misconfigured for 15 months, fixed Oct-Dec 2022. Out of data scope.~~ |
| ~~H17~~ | ~~Rebuild payment event log: model all 4 clearing streams~~ | ~~#026/#027~~ | ~~Analytics~~ | ~~Done #028: 4-stream model implemented. 1,848,699 events / 550,993 cases. Stream 2 (OP field office): 274,863 events. Stream 3 (AB netting): 138,378 events. Stream 4 (Tier 3 OP): 82 events. Dashboard + CSV rebuilt. Brain rebuilt (73,922 nodes).~~ |
| ~~H18~~ | ~~**SEPA `<Purp><Cd>` PurposeCode source identification**~~ | ~~#026~~ | ~~Code~~ | ~~**Done #039 (CONFIRMED from P01).** The PurposeCode comes from **`FPAYP-XREF3`**, read by DMEE tree `/CGI_XML_CT_UNESCO` node `Purp > Cd` (N_9662041050), post-processed by BAdI `FI_CGI_DMEE_EXIT_W_BADI`. Proprietary fallback from `FPAYP-STRFR`. Not a static literal — runtime field mapping. 13 UNESCO DMEE trees analyzed (8,308 nodes in P01). D01 vs P01 comparison: 12/13 trees identical, only `/CGI_XML_CT_UNESCO_1` diverges (9 address nodes differ — minor). ABAP classes `YCL_IDFI_CGI_DMEE_FR/FALLBACK/UTIL` are BAdI implementations receiving tree values, not containing them. PMO class names `_AE`/`_BH` never existed. Findings: `knowledge/domains/Payment/h18_dmee_tree_findings.md`. Comparison CSV: `h18_dmee_d01_vs_p01_comparison.csv`. Probe script: `h18_dmee_tree_probe.py`.~~ |
| ~~H19~~ | ~~**Bank recon aging investigation**~~ | ~~#028~~ | ~~Audit~~ | ~~**Closed #042.** Already fully investigated #029: 199K items on 10xxxxx = permanent ledger (by design). Real unreconciled = 2,737 on 11xxxxx (0.6% gap). No further action needed — finding documented in `bank_statement_ebs_architecture.md`.~~ |
| ~~H20~~ | ~~BSAS AUGBL re-enrichment for bank statements~~ | ~~#028~~ | ~~Data~~ | ~~Done #030: 553,781 items enriched with AUGBL+AUGDT (100% fill rate). Year 2024=247K, 2025=267K, 2026=49K. Clearing chain now fully traceable.~~ |
| ~~H21~~ | ~~**Bank recon amounts: currency conversion**~~ | ~~#028~~ | ~~Analytics~~ | ~~**Done #042.** CURRENCY_USD_RATES table (203 currencies from TCURR type M) + FEBEP_USD view created in Gold DB. Real USD total: **$16.8B** (not $13.9B — conversion increased total). UZS=$6.2B (37% from 1.3% items), USD=$5.8B, EUR=$2.7B. Weak currencies (UZS/IRR/LBP) inflate, don't deflate. Falsified hypothesis that DMBTR was inflated.~~ |
| ~~H22~~ | ~~**FEBEP full fields extraction**~~ | ~~#029~~ | ~~Data~~ | ~~**Closed #042 — DATA WAS ALREADY COMPLETE.** PMO was stale 12 sessions. `FEBEP_2024_2026` table has 223,710 rows with 27 fields, ALL months present (2024-01 through 2026-03). The unsuffixed `FEBEP` (50K rows, 104 cols) was the truncated first attempt — the real data lives in the `_2024_2026` table. "Missing months" claim was wrong.~~ |
| ~~H23~~ | ~~**FEBKO full fields extraction**~~ | ~~#029~~ | ~~Data~~ | ~~**Closed #042 — DATA WAS ALREADY COMPLETE.** PMO said "Missing HBKID" but `FEBKO_2024_2026` has 31,416 rows with 62 fields INCLUDING HBKID (0% null). The unsuffixed `FEBKO` (50K rows, 8 cols) was the truncated first attempt. Same pattern as H22 — always check `_2024_2026` suffix.~~ |
| ~~H24~~ | ~~FEBRE extraction (Note-to-payee / Tag 86 text)~~ | ~~#029~~ | ~~Data~~ | ~~Done #030: 964,055 rows (KUKEY-filtered 2024-2026). 211K match FEBEP. Tag 86 analysis completed: 102I root cause = ACH returns (BELNR=*). Search string effectiveness validated.~~ |
| ~~**H34**~~ | ~~**Code Brain v2: SAP cross-reference extraction + annotation framework + incident linking**~~ | ~~**#048**~~ | ~~**Brain**~~ | ~~**Done #049 — pivoted from extraction to architecture rewrite.** D010TAB/WBCROSS = 200M+ rows, never bulk extract. Built Brain v3 hybrid instead: object-centric `brain_v2/brain_state.json` (4.2% of context, 10 AGI layers, 1 Read = full intelligence). 50 feedback rules migrated from `~/.claude/memory/` (portable). 26 claims (15 superseded for anti-regression). 19 known_unknowns + 16 data quality issues mined from 48 retros. Single-command rebuild via `rebuild_all.py`. SessionStart hook in `.claude/settings.json`. AGI score 41/100→90/100. See `Brain_Architecture/brain_design_specification_v3.md` and `session_049_retro.md`.~~ |
| ~~**H35**~~ | ~~**Validate Brain v3 in real session work**~~ | ~~#049~~ | ~~Brain~~ | ~~**Done #050.** Brain v3 used for the entire session including a self-evaluation that produced 12 deliverables. FALS-003 falsified (I globbed before reading the brain link) — fix shipped: `feedback_brain_first_then_grep` rule + Layer 11 (incidents) + Layer 12 (blind_spots) + `_coverage` metric + force-include. Object count 102→136. AGI score 90→101 (added Failure-mode visibility criterion).~~ |
| **H36** | **Triage brain blind_spots — superseded by H50** | #050 | Brain | Original scope #050: 20 blind_spots. Session #054 audit: count grew to **71** (all MISSING flavor). Coverage dropped 75.6% → 64.3%. H36 is preserved as history anchor; **H50 supersedes with updated scope**. H36 action list remains valid for the first 20: extract PA0027, ZCL_IDFI_CGI_DMEE_FR, ZCL_IM_TRIP_POST_FI_CM006; model GB901/GB922 from Gold DB; drop pseudo-refs (LHRTSF01:852, inst_fund_ba_wbs_cc, GB901:2IIEP###001). |
| **H37** | **Process next incident with new infrastructure** | #050 | Workflow | User will pass next incident in Session #051. Invoke `incident-analyst` subagent (`.claude/agents/incident-analyst.md`) and follow the 7-step `sap_incident_analyst` skill protocol. Output: `knowledge/incidents/INC-<id>_<slug>.md` + first-class record in `brain_v2/incidents/incidents.json`. Resolves FALS-005 (does the workflow reproduce INC-000006073-quality output on a fresh case?). |
| **H38** | **Cleanup `ZFIX_BR_AVC_EXCLUSIONS` landscape inconsistency** | #053 | Code/Cleanup | Discovered Session #053 during INC-BUDGETRATE-EQG analysis. BAdI implementation of `FMAVC_ENTRY_FILTER` exists in **D01 + V01 only**; absent in TS1, TS3, P01. Created 2025-05-14 by JP_LOPEZ (transports D01K9B0D4Z + D50, "BR - AVC Exlclusion MIRO F110"), **deactivated next day 2025-05-15** (transports D01K9B0D54 + D55, "BR Deactivate AVC exclusion"). Never promoted beyond V01. Class `ZFIX_BR_AVC_EXCLUSIONS` (CCDEF/CCIMP/CM001/CM002/CO/CU/CI/CP/CT) is dead code. **Action**: delete from D01+V01 (release transport through chain). **Lesson**: tcode-blacklist mute on AVC was the wrong direction; cross-currency drift must be fixed at the persistence layer or via preventive validation (H39), not the AVC filter. |
| **H39** | **Build preventive validation for cross-currency consumption against EUR BR FRs** | #053 | Code | Per business agreement (Session #053 close). Implementation: new BAdI implementation on `CL_FM_EF_POSITION->CHECK_CONSUMPTION`. Logic: IF `check_br_is_active() = abap_true` AND `m_r_doc->m_f_kblk-waers='EUR'` AND `m_f_kblp-gsber='GEF'` AND `fund_type IN mr_fund_type` AND `consumption_doc-waers <> 'EUR'` THEN MESSAGE 'Z_BR_001' TYPE 'E' "Cannot consume in &1 against EUR Budget Rate Fund Reservation &2/&3. Please post in EUR." Test coverage: FB60/FB65/FB70/MIRO/F110 in TS3 with all 64 listed at-risk FR lines from `Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_lines_FINAL.xlsx`. Coordinate with H38 (delete dead BAdI first). |
| **H40** | **One-time FMAVCREINIT cleanup of 26 affected funds for 2026 / ledger 9H** | #053 | Operations | After H39 deploys to production. Run `RFFMAVC_REINIT` for FIKRS=UNES, GJAHR=2026, ALDNR=9H, FUND IN (26-fund list from incident INC-BUDGETRATE-EQG.scope). Clears accumulated AVC pool drift. Verify each fund's Available USD post-reinit. List of funds: 3110111021, 3110111061, 3210151021, 3210621061, 3210631031, 3230311021, 3230311031, 3230321041, 3230411011, 3230411081, 3230511011, 3230711051, 3230833081, 3230836011, 3230851011, 3240211011, 3310511011, 3310611021, 3310611041, 3310611051, 3310611071, 3310714011, 3320111011, A110111041, A230211011, A230542041. Add a recurring schedule? TBD with treasury — reinit is heavy. |
| **H41** | **Promote 11 PERNRs from blind_spots to first-class person objects** | #054 | Brain/Meta | Discovered session #054 audit of retro #053 formalization gap. Brain carries 11 PERNR-shaped blind_spots (all numeric 8-digit): 10050037, 10067156, 10069500, 10092400, 10097358, 10098989, 10105832, 10107946, 10136066, 10150918, 10567156. These are referenced by BCM workflow annotations + INC-000006313 (VOFFAL add) + ghost PERNR 10567156 (dq_ghost_pernr_bcm_oesttveit RESOLVED). Promotion: for each PERNR, create a first-class object in `brain_state.objects[]` with type=PERSON, fields={pernr, name (from PA0001), BCM_roles, active_rules, related_incidents, HR_status}. Data source: Gold DB PA0001 + OOCU_RESP extraction. Supersedes the "low priority next session" deferred item from #053 retro. |
| **H42** | **Migrate claims.evidence_for/against from str to structured list (DONE session #054)** | #054 | Brain/Schema | **Done session #054.** Schema `evidence_for` and `evidence_against` migrated from `str` to `list[{type, ref, cite, added_session, migrated_from_legacy}]`. 46 claims migrated. Legacy text preserved verbatim in new fields `evidence_legacy_text_for` + `evidence_legacy_text_against` (CP-001). Types inferred automatically: 24 empirical, 11 production_data, 8 source_code, 3 config. `build_active_db.py` patched to json.dumps() the list and add `evidence_count_for/against` columns (CP-003: claims with count<2 are suspect). Backup: `brain_v2/claims/claims.json.pre_session054_backup`. Enables queries: "claims with only empirical evidence", "claims missing source-code anchors", etc. |
| **H43** | **Register 4 missing objects from session #053 (FMAVCT, KBLEW, CL_FM_EF_POSITION, /SAPPSPRO/PD_GM_FMR2_READ_KBLE)** | #054 | PSM/Brain | Session #053 retro §11 committed to registering these as first-class brain objects — never done. All 4 confirmed in `brain_state.blind_spots`. Required fields: type (TABLE/CLASS/FUNCTION_MODULE), domain (PSM), annotations with Session #053 findings (FMAVCT wide-table query pattern, KBLEW cluster wrapper, CL_FM_EF_POSITION→CHECK_CONSUMPTION as H39 fix target). Source data: retro §6 "Tables/data sources discovered" + §7 "Custom code/class architecture". |
| **H44** | **Build `sap_fm_avc_intelligence` skill (AVC = core PSM)** | #054 | PSM/Skill | Availability Control is the foundation of PSM at UNESCO. Skill must encapsulate: FMAVCT wide-table extraction pattern (narrow FIELDS, split OPTIONS), cluster-table access via `/SAPPSPRO/PD_GM_FMR2_READ_KBLE`, fund-level vs FR-line-level metric distinction, Camp A/B/C enhancement asymmetry classification for BR composites, EURX rate type handling, FMIOI WRTTP=81 carryforward pair interpretation (CP-003: sample before aggregating), FMAVCT dedup by RVERS/RPMAX. Source references: retro #053 + `knowledge/domains/PSM/EXTENSIONS/budget_rate_custom_solution.md` + `Zagentexecution/quality_checks/budget_rate_consumption_audit.py`. Deliverable: `.agents/skills/sap_fm_avc_intelligence/SKILL.md` + MATURITY entry. Upgraded from "consider" (retro §13) to HIGH based on domain criticality. |
| **H45** | **Deploy AL_JONATHAN SU3 Y_USERFO fix (DQ-018)** | #054 | FI/Config | Single-user fix for INC-000005240 class. User Anthony Jonathan (Jakarta Field Unit) has USR05 parameter Y_USERFO='HQ', should be 'JAK'. Every F-53/FBZ2 posting carries wrong XREF office tag. Blocked by **KU-027** (verify YFO_CODES contains FOCOD='JAK' before SU3 update). Action: (1) extract YFO_CODES table from P01; (2) confirm JAK entry; (3) update USR05 for AL_JONATHAN via SU3; (4) verify next F-53 posting carries XREF1/XREF2='JAK'. Dependency on H48 (understand substitution mechanics before deploying). |
| **H46** | **Systemic XREF drift strategic fix (DQ-019)** | #054 | FI/Strategy | 21,754 manual post-posting XREF edits in Q1 2026 (FBL3N/FBL1N/FB02/FBL5N on UNES documents). Strategic options documented in `knowledge/domains/Treasury/xref_office_tagging_model.md §7.3`. Decision needed between: (a) preventive substitution fix (code in YRGGBS00), (b) opt-in SU3-based user param model, (c) periodic reconciliation + auto-correction job, (d) tolerate as known manual tax. Must select one, write implementation plan, coordinate with Treasury. Scope: production-wide, affects all 9 company codes. Blocked by H48 (understand WHY substitution fires asymmetrically). |
| **H47** | **HR/BASIS alignment process for USR05.Y_USERFO ↔ PA0001.WERKS/BTRTL (DQ-020)** | #054 | HCM×BASIS | Organizational process gap: USR05 (finance office code, SU3) and PA0001 (HR personnel area/subarea) use different code systems at UNESCO with no enforced sync. A user's finance office can drift silently from their HR assignment. Not a technical bug — a missing process. Action: propose HR→BASIS alert mechanism when PA0001.WERKS/BTRTL changes; periodic diff report (SAP job); policy for mandatory SU3 update on HR transfer. Owner: HR + BASIS collab. Cross-domain item. |
| **H48** | **Investigate KU-030/031/032: YRGGBS00 substitution mechanics** | #054 | FI/Investigation | 3 open known_unknowns that block H45/H46: KU-030 (why is `IF bseg_xref1 = space` guard commented out in YRGGBS00_SOURCE.txt:998?), KU-031 (where is substitution step-to-prerequisite linkage stored? GB905/GB921 empty via RFC_READ_TABLE), KU-032 (why does F110 substitution fire on vendor line but NOT on bank GL line, while F-53 fires on both?). Investigation plan: version history of YRGGBS00 (who removed the guard and when), alternative tables for prerequisite storage (GB01/GGB1 via RFC), empirical trace of F110 vs F-53 via ST05 in TS3. Deliverable: resolve 3 KUs + update knowledge/incidents/INC-000005240_xref_office_substitution.md. |
| **H49** | **Test FALS-001 to FALS-006 predictions** | #054 | Brain/Meta | 6 falsification predictions pending test (layer 7 brain_state). Split by testability: **Testable now** (session #054): FALS-001 (brain_state.json size < growth threshold), FALS-002 (one-Read faster than multi-file), FALS-003 (knowledge_docs links reduce grep), FALS-005 (incident-analyst subagent matches INC-000006073 quality — test on INC-BUDGETRATE-EQG + INC-000006313 + INC-000005240). **Longer horizon**: FALS-004 (50 rules enough? — need 10 sessions of delta), FALS-006 (DQ-001 recurring check finds 5+ more vendor drift — need full fmifiit scan). Action: write `brain_v2/agi/falsification_test_session054.py` that evaluates each against current state + updates `falsification_log.json` with verdict PASSED/FALSIFIED/DEFERRED. |
| **H50** | **Triage 71 brain_spots (supersedes H36)** | #054 | Brain/Meta | Coverage 64.3% (71 MISSING, 0 GHOST, 0 PSEUDO). Classification target per CP-001: every blind_spot must have flavor + disposition (PROMOTE, MODEL_FROM_DATA, PSEUDO_REF_DROP, DEFER). Breakdown: 11 PERNRs (→ H41 PROMOTE as PERSON), 4 session #053 objects (→ H43 PROMOTE), ~56 remaining (SAP table refs like BSEG.XREF1, CL_* classes, DMEE trees, FM FMs). Target: coverage ≥ 80% post-triage. Script: `brain_v2/triage_blind_spots.py` classifies each via pattern matching + annotations lookup. Output: add `disposition` + `rationale` fields to each blind_spot. |
| ~~**H51**~~ | ~~**Audit + backfill traceability gaps in existing brain (6/6 DONE session #054)**~~ | ~~#054~~ | ~~Brain/Meta~~ | ~~**Closed #054.** All 6 sub-steps done: (1) 15/15 superseded claims linked, (2) 4/4 incidents annotated with chain_anchor_type (all 100% coverage), (3) annotation finding audit — 88 annotations, only 3 <80 chars, all 3 complete-concise (not truncated), 0 expansion needed, (4) 21/21 data_quality enriched, (5) 34/34 known_unknowns enriched, (6) 86/86 feedback rules tagged with derives_from_core_principle. Audit methodology validated CP-003 precision principle: empirical verification replaced assumption of truncation. Nothing further to do.~~ |
| H25 | **T028A + T028E extraction (account symbol definitions)** | #029 | Config | T028A = symbol-to-GL mapping (BANK→10xxxxx, BANK_SUB→11xxxxx). T028E = posting key definitions. Validates the account symbol configuration. **Zombie age 19. Kill if not done by #055.** |
| H26 | **T012K UKONT re-extraction** | #029 | Config | T012K missing UKONT field (sub-bank GL paired with bank GL). Need to re-extract with all fields to validate 10xxx↔11xxx pairing. **Zombie age 19. Kill if not done by #055.** |
| ~~**H33**~~ | ~~**Brain v2: Absorb ALL text into graph — zero dead text**~~ | ~~**#040**~~ | ~~**Brain**~~ | ~~**Done #040.** `knowledge_ingestor.py` shipped: 113 KNOWLEDGE_DOC nodes + 40 SKILL nodes + 19 COMPANION nodes + 1,177 reference edges (DOCUMENTED_IN/SKILLED_IN/DISCOVERED_IN). Covers knowledge/domains/ (44 docs), .agents/skills/ (40 skills), session retros (34), intelligence docs, HTML companions (19). Enforced by preflight check S5 (no static artifacts when brain exists). Principle: if it has relationships, it's a node.~~ |
| ~~**H30**~~ | ~~**Brain v2 Phase 1: Behavioral edges from code**~~ | ~~**#039**~~ | ~~**Brain**~~ | ~~**Done #040.** 1,251 code nodes + 671 behavioral edges from 1,142 ABAP files. Parser: 6 regex patterns (SELECT, CALL FUNCTION, INSERT/MODIFY, INHERITING FROM, INTERFACES, BAdI naming). Multi-class flat directory grouping (DMEE pattern). Recursive scanner handles 5-level nesting after project reorganization.~~ |
| ~~**H31**~~ | ~~**Brain v2 Phase 2: Config + Integration + Transport edges**~~ | ~~**#039**~~ | ~~**Brain**~~ | ~~**Done #040.** 50,798 nodes + 111,048 edges from 7 ingestors. Config (T042A, DMEE trees, BCM, house banks), Transports (7,745 + 46K objects → 108K edges), Integration (239 RFC dests, 3,073 RFC-enabled FMs, 7 .NET apps, IDocs), SQLite schema (83 tables + 18 proven joins), Jobs (227 programs), Processes (5 E2E, 30 steps). Build time: 45s.~~ |
| ~~**H32**~~ | ~~**Brain v2 Phase 3: Process overlay + Query engine + CLI**~~ | ~~**#039**~~ | ~~**Brain**~~ | ~~**Done #040.** 4 query types operational: impact analysis (BFS with risk decay), dependency tracing (reverse BFS), structural similarity (Jaccard), gap analysis (2,931 findings on first run). CLI: `python -m brain_v2 build\|stats\|impact\|depends\|similar\|gaps\|search\|critical\|path`. Validated: HR_READ_INFOTYPE impact → 9 affected objects, ZCL_HR_FIORI_EDUCATION_GRANT depends → 26 dependencies.~~ |
| ~~H29~~ | ~~**Update 510 SKAT text differences P01→D01**~~ | ~~#034~~ | ~~Data Sync~~ | ~~**Done #038**: real scope was **1,690 rows multi-language** (not 510 English-only from #034 note). 1,511 UPDATEs (518 E + 500 F + 493 P) + 179 INSERTs (87 F + 92 P). Pattern: SELECT SINGLE + UPDATE FROM ls (avoids 72-char ABAP truncation bug). 141 batches, ok=1690 ko=0, gap=0 verified. Log: `knowledge/domains/FI/h29_skat_sync_log.md`. Side-fix: `rfc_helpers.py` RECONNECTABLE_ERRORS extended with RFC_CLOSED/broken/WSAE* patterns after mid-flight crash at batch 31.~~ |
| ~~H27~~ | ~~TCURR/TCURF extraction (exchange rates)~~ | ~~#029~~ | ~~Analytics~~ | ~~Done #030: TCURR 54,993 rates + TCURF 2,614 factors loaded. Ready for H21 currency conversion.~~ |
| ~~H28~~ | ~~Bank Statement EBS Companion HTML~~ | ~~#029~~ | ~~Viz~~ | ~~Done #030: `bank_statement_ebs_companion.html` — 10 tabs (Overview, E2E Chain, Config Tiers, Posting Rules, Algorithms, GL Structure, BA Determination, Production Reality, Interactive Map, Glossary). Includes production analysis: 97% outgoing clearing, 46.5% incoming, 85.7% algo 015. SVG network diagram.~~ |
| ~~H15~~ | ~~Read Blueprint BCM pages 21-47~~ | ~~#021~~ | ~~Knowledge~~ | ~~Done #022 — Full 21 SAP Notes, Delegation of Authority table, grouping rules, XML char handling all extracted~~ |

### 🟢 BACKLOG — When blocking/high are clear

> **Session #036 Purge**: 31 zombie items (>10 sessions old, no movement) killed with explicit reason.
> Kill criteria: (a) speculative, (b) ceremony not decision-enabling, (c) superseded, (d) nice-to-have masquerading as work.
> Pre-purge: 52 items. Post-purge: 21 items. Survivors have a deadline or a hard business tie-in.

#### Process Mining & Analytics
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G1~~ | ~~OCEL 2.0 multi-object~~ | ~~#009~~ | ~~KILLED #036: speculative. Current pm4py mining is not queried by any decision. Adding OCEL = adding ceremony.~~ |
| ~~G2~~ | ~~CTS conformance deep dive~~ | ~~#009~~ | ~~KILLED #036: found 100% conformant. No value in deeper analysis.~~ |
| ~~G3~~ | ~~Pattern Brain (Algorithms)~~ | ~~#005b~~ | ~~KILLED #036: speculative "anomaly detection" with no target metric.~~ |
| ~~G4~~ | ~~process-intelligence.html filter RELE~~ | ~~#003~~ | ~~KILLED #036: minor cosmetic on a dashboard nobody uses.~~ |
| ~~G5~~ | ~~process-intelligence.html browser verify~~ | ~~#003~~ | ~~KILLED #036: same dashboard, same lack of demand.~~ |

#### Skills & Governance
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G6~~ | ~~Build T2R skill~~ | ~~#018~~ | ~~KILLED #036: YAGNI. No Travel-to-Claim work in session backlog. Build when demanded.~~ |
| ~~G7~~ | ~~Build P2D skill~~ | ~~#018~~ | ~~KILLED #036: YAGNI. Same as G6.~~ |
| ~~G8~~ | ~~Create crp_fiori_app skill~~ | ~~#017~~ | ~~KILLED #036: speculative. CRP has 19 items but none active.~~ |
| G9 | **Publish `sap-intelligence` SKILL.md** to ecosystem | ecosystem | Survives — governance obligation to ecosystem coordinator |
| G10 | **Promote Transport Companion pattern** | ecosystem | Survives — ecosystem obligation |
| G11 | **Promote Company Code Copy checklist** | ecosystem | Survives — ecosystem obligation |
| ~~G12~~ | ~~Cross-reference maturity vs SESSION_LOG~~ | ~~#018~~ | ~~KILLED #036: audit ceremony. `session_preflight.py` Check 8 now enforces skill count automatically.~~ |

#### Data Extraction (non-blocking)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G13~~ | ~~Job source code extraction~~ | ~~#018~~ | ~~KILLED #036: 228 programs already catalogued. Source extraction is speculative until a specific program needs it.~~ |
| ~~G14~~ | ~~BP Conversion extraction~~ | ~~#005b~~ | ~~KILLED #036: S/4HANA readiness is not a 2026 goal. Resurrect when migration is actually planned.~~ |
| ~~G15~~ | ~~PSM domain code extraction~~ | ~~#005b~~ | ~~KILLED #036: extracted_sap/PSM/ empty = no concrete need, only completionism.~~ |
| ~~G16~~ | ~~Real Estate domain extraction~~ | ~~#005b~~ | ~~KILLED #036: new domain discovery ≠ requirement. No RE work in pipeline.~~ |

#### CTS Dashboard Fixes
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G17~~ | ~~Improve module classification~~ | ~~#004~~ | ~~KILLED #036: 3,329/4,168 in "General IMG" — cosmetic. Dashboard works.~~ |
| ~~G18~~ | ~~total_mods verification~~ | ~~#004~~ | ~~KILLED #036: trivial QA on a working dashboard.~~ |
| ~~G19~~ | ~~topbar KPI sync~~ | ~~#004~~ | ~~KILLED #036: hardcoded value vs data mismatch — 5 min fix if ever demanded, not a PMO item.~~ |
| ~~G20~~ | ~~TADIR cache enrichment~~ | ~~#004~~ | ~~KILLED #036: SOTR/VARX skipped — no user-facing impact.~~ |

#### Infrastructure
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G21~~ | ~~Vector Brain (ChromaDB)~~ | ~~#005b~~ | ~~KILLED #036: speculative. 30 sessions without a use case. Current keyword grep works.~~ |
| ~~G22~~ | ~~**SAP MCP Server build**~~ | ~~#005b~~ | ~~**KILLED #037**: MCP server already exists and is operational at `Zagentexecution/mcp-backend-server-python/sap_mcp_server.py`. Done-but-never-closed pattern (same as H10 in #036). Zombie for 30 sessions because no one struck it. Verified via file existence.~~ |
| ~~G23~~ | ~~Duplicate script cleanup~~ | ~~#005b~~ | ~~KILLED #036: hygiene, not strategic. Do during a refactor, not as a PMO item.~~ |
| ~~G24~~ | ~~Index YRGGBS00 + YPS8~~ | ~~#005b~~ | ~~KILLED #036: indexing ceremony. Nobody queries this index.~~ |
| ~~G25~~ | ~~Archive legacy root docs~~ | ~~#005b~~ | ~~Done #023~~ |
| ~~G26~~ | ~~Brain auto-refresh workflow~~ | ~~#006~~ | ~~KILLED #036: see G1/H6 — brain is write-only. Auto-refresh = more writes, not more value.~~ |
| ~~G27~~ | ~~Notion PMO sync~~ | ~~#006~~ | ~~KILLED #036: nice-to-have integration. PMO_BRAIN.md is the source of truth; duplication adds sync cost.~~ |

#### Integration & Connectivity (Session #032)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G37 | **Build Basis Monitoring HTML companion** | #032 | Script `sap_system_monitor.py` ready, needs companion. SM04/SM37/SM35/ST22. |
| G38 | **Update system_inventory.html with .NET apps** | #032 | 7 UNESCO .NET apps discovered but only in connectivity diagram, not inventory page |
| G39 | **Add RFC API Surface tab to rfc_analysis.html** | #032 | 334 RFC-enabled FMs by domain. Data in tfdir_custom table. |
| G40 | **Investigate TULIP + UNESDIR 93% job failures** | #032 | YHR_MANAGER_FROM_TULIP_UPDATE (14/15 failed), YHR_CREATE_MAIL_FROM_UNESDIR (28/30 failed) |
| ~~G41~~ | ~~Verify SuccessFactors EC migration status~~ | ~~#032~~ | ~~Closed #035: SF EC IS ACTIVE. ECPAO_OM_OBJECT_EXTRACTION (43 parallel jobs, 1,290 runs) + ECPAO_EMPL_EXTRACTION (3 jobs, 51 runs). Massive OM+Employee extraction to EC Payroll. Not "planned" — live in production.~~ |
| G42 | **Build FI Support Agent skill** | #032 | Orchestrates fi_maintenance + payment_bcm + bank_statement + brain + Gold DB to resolve tickets |
| G43 | **Confirm SAPBC/us0033 is decommissioned** | #032 | Legacy Business Connector. No jobs/code/IDocs. Check SM59 connection test. |
| G44 | **Extend `sap_master_data_sync` to CC/PC/FA** | #034 | Cost centers (CSKS/CSKT), profit centers (CEPC/CEPCT), functional areas (TFKB/TFKBT), fund centers (FMFCTR/FMFCTRT). Same 4-step pattern. |
| G45 | **Update connectivity diagram with file-based integration tier** | #035 | 5 tiers: SWIFT/banks (7K runs), COUPA (348), SuccessFactors EC (1,340), TULIP/UNESDIR (45), Data Hub/BW (30+). New integration vector. |
| G46 | **Update `sap_interface_intelligence` skill with file-based vector** | #035 | Add TBTCO/TBTCP job analysis as integration discovery method. Current skill only covers RFC destinations + IDocs. |
| G47 | **Investigate Data Hub target system** | #035 | YFM_OUTPUT_INDIRECT_COSTS_DH + YHR_ORG_UNIT_COUNT_DH + YFM_STAFF_COST_DISTRIBUT_DH — "DH" suffix = Data Hub. What system is this? |

#### Future Ideas
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G28 | **Fiori PA Mass Update App** | #002 | Survives — consolidates PRAA* BDC (135/quarter) + absorbs G54. Real business op value. **Rejustified #037**: age 33 sessions but real consolidation value confirmed. Deadline: ship scoping doc (not app) in 5 sessions or KILL. Needs coupling with HR roadmap, not H13. |
| ~~G29~~ | ~~Coupa → SAP API Interface~~ | ~~#002~~ | ~~KILLED #036: speculative. COUPA file + BDC integration is working (integration_map_complete.md). No business push to replace.~~ |
| ~~G30~~ | ~~BDC Trigger Analysis (RISK)~~ | ~~#002~~ | ~~KILLED #036: "risk analysis for a hypothetical replacement". No replacement in flight.~~ |
| ~~G31~~ | ~~P01 user activity map~~ | ~~#006~~ | ~~KILLED #036: nice-to-have. Not tied to any decision.~~ |
| ~~G32~~ | ~~Service node enrichment~~ | ~~#006~~ | ~~KILLED #036: brain ceremony.~~ |
| ~~G33~~ | ~~Transport Living Knowledge~~ | ~~#005b~~ | ~~KILLED #036: speculative "evolving seeds" concept.~~ |
| ~~G34~~ | ~~abapGit integration~~ | ~~#006~~ | ~~KILLED #036: 29 sessions dormant. No abapGit workflow in use.~~ |
| ~~G35~~ | ~~Catch live BDC field data~~ | ~~#002~~ | ~~KILLED #036: requires live SAP + SM35 access + a failing session — too many preconditions for nonzero value.~~ |
| ~~G36~~ | ~~sap_bp_conversion SKILL.md~~ | ~~#005b~~ | ~~KILLED #036: future skill for future migration. YAGNI.~~ |
| G55 | **BP Conversion Readiness: research SAP vendor→BP migration strategies** | #048 | **RESURRECTED from G14+G36 — now justified by INC-000006073.** Wrong KTOKK caused production failure. 21 BP tables now in Gold DB (2.5M rows). Research SAP help (help.sap.com/docs/SAP_S4HANA_ON-PREMISE vendor-customer-integration), SAP blogs, conversion strategies. Analyze UNESCO data: KTOKK distribution, CVI_VEND_LINK gaps (0 rows = no BP↔vendor mapping yet), BUT000 vs LFA1 coverage (559 BP vs 316K vendors = <1% converted). Output: `knowledge/domains/BusinessPartner/bp_conversion_readiness.md` |
| G56 | **Travel domain discovery: KTOKK anomalies + GGB1 coverage gaps across all company codes** | #048 | Cross LFB1.AKONT with GB901/GB922 to find every GL with vendors but no substitution rule — systematic INC-000006073 prevention. Also: KTOKK vs PERSG cross-check to find more wrong vendor account groups. |
| G57 | **Ingest Travel + BP domain into Brain v2 (48 + BP edges)** | #048 | 69 ABAP files + 21 Gold DB tables + relationship definitions in `travel_brain_edges.md`. Run `sap_brain.py --ingest-domain Travel` and `--ingest-domain BusinessPartner`. |
| G58 | **Extract PTRV_SCOS + PTRV_SHDR with ALL fields** | #048 | Current extraction has 8/35 and 11/25 fields. Re-extract with DDIF pattern for full trip cost assignment data. |
| G59 | **Build automated annotation prompts mid-session** | #049 | AGI layers (known_unknowns, falsification, data_quality) decay without enforcement. Need a hook or workflow that prompts agent to populate them when discoveries happen. Currently relies on agent discipline. |
| G60 | **Validate `/hooks` reload + SessionStart hook fires** | #049 | Created `.claude/settings.json` SessionStart hook in #049. Watcher wasn't watching `.claude/` at session start, so hook needs `/hooks` open or restart to activate. Verify it actually fires next session. |

#### Ecosystem-Level
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G48 | **Rescue Vendor MDM** | ecosystem | 98 days stalled |
| G49 | **ADR-004: Testing as Skill or Project?** | ecosystem | Architecture decision pending |
| G50 | **Promote BSP React patterns** | ecosystem | To `.knowledge/skills/sap-fiori-react/SKILL.md` |
| G51 | **Score UNESCO SAP Brain on 10 dimensions** | ecosystem | Gap analysis |

#### Added Session #036 (2026-04-05)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G52 | **Integration map companion HTML** | #035 retro | Build interactive visual from integration_map_complete.md (37 flows, 8 channels, 18+ systems) |
| G53 | **Investigate 10 integration open questions** | #035 retro | Exchange rate source (Q1), Data Hub identity (Q2), LSMW origin (Q3), Core Mgr bidirectional (Q4), COUPA/SWIFT file paths (Q5), BOC purpose (Q6), AWS security (Q7), Vendor export target (Q8), UNJSPF payload (Q9), TULIP/UNESDIR 93% failure (Q10) |
| ~~G54~~ | ~~Design Fiori replacement for PRAA*~~ | ~~#005 (moved from H7 #036)~~ | ~~MERGED into G28 #036: PRAA replacement is the same concept as "Fiori PA Mass Update App". Two items, one idea.~~ |

#### Added Session #036 (2026-04-05) — Infrastructure for AGI-discipline
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G55~~ | ~~Skills Consolidation Execution (38→6 archetypes)~~ | ~~#036~~ | ~~KILLED #036 by user: knowledge loss unacceptable. Skills are memory, merging is lossy compression. See `.agents/SKILLS_CONSOLIDATION_PLAN.md` (REJECTED). Alternative: individual deletion of truly-dormant skills only if they've been dormant 30+ sessions AND contain no unique knowledge.~~ |
| G56 | **Nightly SAP health check (`sap_health_check.py`)** | #036 | Auto-generated invariant queries over Gold DB (FM-FI balance, BCM dual-control delta, open item aging). Converts platform from archive to monitor. |
| ~~G57~~ | ~~Convert 10 more feedback rules to executable checks~~ | ~~#036~~ | ~~KILLED #036 (user decision): same growth paradigm as skills and memory. Feedback files are part of memory — they GROW, never consolidate. Converting to executable checks is optional for high-frequency rules, not a reduction target. `session_preflight.py` Check 9 updated to track health, not count.~~ |
| ~~G58~~ | ~~**Route H13 BCM finding into `sap_payment_bcm_agent` SKILL.md**~~ | ~~#036~~ | ~~Done #037 via skill_coordinator — new "Dual-Control Audit" section at `sap_payment_bcm_agent/SKILL.md` with SQL query, reproducible findings, CUR_STS vs STATUS guidance, user pattern signatures, remediation paths, invocation triggers. ~90 lines substantive content. First real invocation of skill_coordinator's routing protocol.~~ |
| ~~G59~~ | ~~**Route file-based integration vector into `sap_interface_intelligence`**~~ | ~~#036~~ | ~~Done #037 via skill_coordinator — new "File-Based Integration Vector" section at `sap_interface_intelligence/SKILL.md` with pattern signature, detection method, channel matrix (RFC/IDoc/HTTP/DB/Transport/File), COUPA reference, invocation triggers. ~60 lines. 9 systems identified, full per-system enumeration deferred to #038+.~~ |

#### Added Session #039 (2026-04-06)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G61~~ | ~~**Brain v2: fix impact query direction + v1 migration (73K fund nodes)**~~ | ~~#039~~ | ~~**Done #041.** Impact direction model corrected: ROUTES_TO_BANK→bidirectional, forward/backward traversal working. FPAYP.XREF3→32 objects. v1 migration deferred (fund nodes are taxonomic, low value for impact analysis). Domain knowledge ingestor covers BAdI param tables.~~ |
| ~~G62~~ | ~~**Brain v2: ingest DMEE→FPAYP.XREF3 edge from h18_dmee_tree_nodes.csv**~~ | ~~#039~~ | ~~**Done #041.** Domain knowledge ingestor creates DMEE class→FPAYP/REGUH/T042Z edges (88 edges). USES_DMEE_TREE edges (36) from T042A bank routing (SOG*→/CGI_XML_CT_UNESCO). Full chain: FPAYP.XREF3→class→DMEE→paymethod→bank verified.~~ |
| G63 | **Formalize Discovery Patterns as ecosystem skill** | #039 | Independent of Brain v2. 6 proven patterns (Payment E2E, P2P, Integration, Bank Recon, Code+BAdI tracing, Transport Impact). Create `.agents/skills/discovery_patterns/SKILL.md` + promote to ecosystem-coordinator as `enterprise-discovery` skill. |
| G64 | **Brain v2: self-improvement research track** | #039 | **Phase 4 (after H32).** Investigate real self-improving KG models (Graphiti temporal, Agentic-KGR co-evolution, ARC Prize refinement). Spec: Section A.7 (3 validated loops) + A.8 (platform absorption). |

#### Added Session #038 (2026-04-05)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G60~~ | ~~**User-operated monitor bundle: BCM dual-control + Basis (SM04/SM37/SM35/ST22)**~~ | ~~#038~~ | ~~**Done #038 (added + shipped same session).** Location: `Zagentexecution/my_monitors/run_my_monitors.py` + `my_monitors_dashboard.html` (8.9 KB, 2 tabs: BCM + Basis) + `README.md`. On-demand launcher over Gold DB (no cron, no SMTP, no infra). Tab 1 surfaces H13 finding (3,359 same-user batches, Wednesday cycle, top-2 ops). Tab 2 surfaces TBTCO job health + TFDIR_CUSTOM FM inventory + ICFSERVICE count. User's "el monitor puede ser mío junto a Basis" idea from Block 4.~~ |

#### Added Session #050 (2026-04-09)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G65 | **Run vendor_master_integrity_check.py against full master + remediation report** | #050 | Resolves FALS-006 + KU-020. Run the script with default threshold + a looser rank-based pass. Produce a per-(KTOKK,BUKRS) outlier list. Cross-check with GGB1 coverage. Estimate full exposure across the 316K vendor master. Promote findings to BusinessPartner README and PMO if scope is >10 vendors. |
| G66 | **PA0027 subtype 02 expiration scan across employee master** | #050 | INC-000006073 root cause included a BAdI safety net that silently fails when PA0027-02 record is expired (Katja's expired 2021-01-31). Build a recurring check that lists all employees whose latest PA0027-02 record's ENDDA is in the past. The BAdI then never fires for them — they are exposed to the same intercompany trip failure. Promote to `Zagentexecution/quality_checks/pa0027_subtype_02_expiration_check.py`. |
| G67 | **TADIR-wide brain coverage metric** | #050 | Resolves KU-023. The current `_coverage.pct_classified = 75.6%` only measures the closed loop (objects the brain has TALKED about). The open loop is unmeasured: how many `Y*/Z*` objects exist in TADIR vs how many are in `brain_state.objects`? Build a one-shot script that queries TADIR via RFC, joins with `brain_state.objects` keys, and reports per-domain coverage. |

---

## COMPLETED (Archive)

Items completed across all 19 sessions — kept for audit trail.

| # | Task | Completed | Session |
|---|------|-----------|---------|
| ~~1~~ | Extract FMIFIIT full | 2026-03-15 | #005 |
| ~~2~~ | Brain redesign — Living Knowledge Engine | 2026-03-15 | #006 |
| ~~3~~ | Create `sap_data_extraction` SKILL.md | 2026-03-15 | #007 |
| ~~4~~ | Consolidate 3 SQLite DB copies | 2026-03-15 | #007 |
| ~~5~~ | Run overnight FI/MM extraction | 2026-03-16 | #010 |
| ~~6~~ | CDHDR extraction (7.8M rows) | 2026-03-16 | #011 |
| ~~7~~ | P2P complement: EBAN+RBKP+RSEG | 2026-03-16 | #011 |
| ~~8~~ | ESLL extraction (2.9M rows) | 2026-03-19 | #013 |
| ~~9~~ | FMIOI extraction (1.8M rows) | 2026-03-19 | #013 |
| ~~10~~ | Jobs intelligence (228 programs) | 2026-03-19 | #014 |
| ~~11~~ | Interface intelligence (239 RFC dests) | 2026-03-19 | #014 |
| ~~12~~ | P2P event log (848K events) | 2026-03-19 | #014 |
| ~~13~~ | Connectivity diagram | 2026-03-19 | #014 |
| ~~14~~ | Brain 73.9K nodes (8 sources) | 2026-03-19 | #014 |
| ~~15~~ | Cost recovery analysis | 2026-03-26 | #016 |
| ~~16~~ | Golden Query built | 2026-03-26 | #016 |
| ~~17~~ | BSIS/BSAS 13-field enrichment | 2026-03-26 | #016 |
| ~~18~~ | FMIFIIT OBJNRZ 2025 only | 2026-03-26 | #016 |
| ~~19~~ | GOVERNANCE.md + SKILL_MATURITY.md | 2026-03-26 | #018 |
| ~~20~~ | 1,002-file commit | 2026-03-26 | #018 |
| ~~21~~ | Transport companion D01K9B0CBF | 2026-03-26 | #019 |
| ~~22~~ | sap_transport_companion skill | 2026-03-26 | #019 |
| ~~23~~ | sap_company_code_copy skill | 2026-03-26 | #019 |
| ~~24~~ | sap_payment_bcm_agent skill (728 lines, 13 PDFs) | 2026-03-27 | #021 |
| ~~25~~ | sap_payment_e2e skill (process mining results) | 2026-03-27 | #021 |
| ~~26~~ | Payment BCM companion HTML (664KB) | 2026-03-27 | #021 |
| ~~27~~ | Payment process mining HTML (694KB, 1.4M events) | 2026-03-27 | #021 |
| ~~28~~ | Gold DB +9 tables (BNK_BATCH_HEADER/ITEM, REGUH, PAYR, T042*, T012*, T001) | 2026-03-27 | #021 |
| ~~29~~ | PMO audit: 11 items closed (B1,B4-B9,H8,H9,H16,H17) | 2026-03-31 | #028 |
| ~~30~~ | FMIFIIT OBJNRZ enrichment 2024+2026 (all years complete) | 2026-03-31 | #028 |
| ~~31~~ | EKBE BUDAT+6 fields enrichment (363K rows, 2-pass) | 2026-03-31 | #028 |
| ~~32~~ | 4-stream payment event log (1.85M events, 550K cases) | 2026-03-31 | #028 |
| ~~33~~ | Bank recon process discovery (239K docs, 91.2% auto) | 2026-03-31 | #028 |
| ~~34~~ | Companion v8 (14 tabs: +Deep Analysis, +Bank Recon, 794KB) | 2026-03-31 | #028 |
| ~~35~~ | Brain 73,935 nodes (+10 Source 9: streams, findings, bank recon) | 2026-03-31 | #028 |
| ~~36~~ | BSAS AUGBL enrichment (553K items, 100% fill) | 2026-03-31 | #030 |
| ~~37~~ | TCURR (55K) + TCURF (2.6K) exchange rates extracted | 2026-03-31 | #030 |
| ~~38~~ | Bank Statement EBS Companion v1 (10 tabs, production analysis) | 2026-03-31 | #030 |
| ~~39~~ | FEBEP re-extracted 27 fields (133K rows, E2E chain analysis) | 2026-03-31 | #030 |
| ~~40~~ | GL + Cost Element P01→D01 sync (880 records, 6 tables, gap=0) | 2026-04-03 | #034 |
| ~~41~~ | `sap_master_data_sync` skill created (#38) | 2026-04-03 | #034 |
| ~~42~~ | CO tables extracted: COOI 773K + COEP 2.55M + RPSCO 127K = 3.45M rows | 2026-04-04 | #035 |

---

## SESSION CLOSE PROTOCOL — Mandatory Reconciliation

> **This is the #1 rule that prevents pending items from getting lost.**

At the END of every session, the agent MUST:

1. **List all new pending items** discovered during the session
2. **Add each one** to the appropriate section above (B/H/G) with session # in "First raised"
3. **Strike through** any items completed during the session
4. **Verify count**: `pending_before + new_pending - completed = pending_after`
5. **Update SESSION_LOG.md** with: "PMO reconciled: +N new, -N completed, N total pending"
6. **Update MEMORY.md** pending count (just the number, not the list — list lives HERE)

**If you skip this, items get lost. This happened between sessions #009 and #020 (11 sessions without reconciliation).**

---

## Operating Rules

1. **Every session**: Read this PMO Brain FIRST — it's the single source of truth
2. **Every session**: Pick 1 🔴 Blocking + 1-2 🟡 High Priority tasks
3. **Every session end**: MANDATORY reconciliation (see protocol above)
4. **Brain rule**: After any extraction → run `sap_brain.py --build --html`
5. **Skill rule**: After discovering a new pattern 3x → create a skill for it
6. **P01 rule**: All monitoring data from P01 only. Never use D01 data for decision-making
