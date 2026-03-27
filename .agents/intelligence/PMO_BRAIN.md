# UNESCO SAP — Project Brain + PMO Brain
> Two brains, one project. Updated every session. Read alongside `PROJECT_MEMORY.md`.
> **Last reconciled**: Session #022 (2026-03-27) — Companion v4 + Brain SOURCE 9 + payment_full_landscape.md

---

## PROJECT BRAIN — What We Built

### The System (as of 2026-03-26)

```
UNESCO SAP Intelligence Toolkit — 10 Capability Layers, 33 Skills
├── L1: SAP Connectivity      → pyrfc + SNC/SSO (D01 dev / P01 prod)
├── L2: Data Extraction       → ~2.5GB gold SQLite DB, 24M+ rows, 42 tables
├── L3: Validation/Domain     → sap_brain.py (73.9K nodes, 3-level access), 4 domain agents + coordinator
├── L4: Code Extraction       → ADT API, BSP/OData/Enhancement extraction
├── L5: Transport Intel       → CTS dashboard, 7,745 transports analyzed
├── L6: Fiori Development     → Offboarding clone (React+UI5 Web Components)
├── L7: Process Intelligence  → process-intelligence.html + pm4py (848K P2P events)
├── L8: System Monitoring     → sap_system_monitor.py (SM04/SM35/SM37/ST22)
├── L9: Class Deployment      → 16 scripts (create, deploy, verify ABAP classes)
└── L10: BDC Intelligence     → bdc_full_inventory.py (Allos/Y1 payroll forensics)

Governance: .agents/GOVERNANCE.md + SKILL_MATURITY.md (33 skills scored)
Maturity: 13 Production (42%) | 10 Functional (32%) | 4 Draft | 4 Stub

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
| B1 | **FMIFIIT OBJNRZ enrichment 2024+2026** | #016 | Golden Query WBS coverage | Script proven on 2025 (976K rows). Just re-run for 2024+2026 |
| B2 | **BSEG PROJK extraction** | #016 | WBS for non-FM documents | BSEG declustered in P01. No MANDT in WHERE. Direct RFC_READ_TABLE |
| B3 | **CO tables: COOI, COEP, RPSCO** | #005 | Entire CO cost layer missing | ~1.6M rows total. No extraction script yet |
| B4 | **B2R tables: FMIOI+FMBH+FMBL verification** | #009 | B2R lifecycle mining | Returned 0 rows initially (date filter bug). Extracted in #013 but verify data quality |
| B5 | **SES gap: ESSR↔ESLL PACKNO mismatch** | #011 | P2P service receipts | ESLL extracted (2.9M in #013) but JOIN=0 events. Debug join keys |
| B6 | **EKBE BUDAT enrichment** | #018 | P2P temporal precision | Currently GJAHR proxy. Need real posting dates |
| B7 | **CDHDR process mining** | #011 | Audit trail analysis | 7.8M rows extracted but NEVER processed with pm4py |
| B8 | **P2P bottleneck/temporal analysis** | #009 | P2P insights | 848K event log built but no time analysis run |
| B9 | **Fix STEM FBZP chain** | #019 | Company code unusable for payments | T042C+T042I missing. House bank CBE01 question |
| B10 | **Update 10 stale skills** | #017 | Agents using outdated instructions | See #017 retro for full gap list |

### 🟡 HIGH — Next available session

| # | Task | First raised | Category | Notes |
|---|------|-------------|----------|-------|
| ~~H1~~ | ~~Create `sap_payment_e2e` skill~~ | ~~#019~~ | ~~Skill~~ | ~~Done #021~~ |
| H2 | **Create `sap_process_mining` skill** | #017 | Skill | pm4py engine exists but has no SKILL.md |
| H3 | **Create `sap_change_audit` skill** | #017 | Skill | CDHDR/CDPOS mining pattern — no skill |
| H4 | **BSEG UNION view in SQLite** | #011 | Data | CREATE VIEW over 6 Celonis tables (BSIS+BSAS+BSIK+BSAK+BSID+BSAD) |
| H5 | **Merge sap_segw + segw_automation** | #018 | Skill | Duplicate skills for same domain |
| H6 | **Brain integration of P2P** | #009 | Brain | PROCESS_VARIANT/BOTTLENECK/ANOMALY nodes |
| H7 | **Design Fiori replacement for PRAA*** | #005 | App | PA30 infotype update app. BAPI: BAPI_EMPLOYEE_ENQUEUE + HR_MAINTAIN_MASTERDATA |
| H8 | **P01 transaction usage report** | #005b | Monitoring | `--report transactions --system P01` |
| H9 | **P01 runtime dumps report** | #005b | Monitoring | `--report dumps --system P01` — what's breaking in prod? |
| H10 | **Document Coupa integration** | #002 | Analysis | COUPA* sessions doing PA30 BDC — needs proper BAPI endpoint |
| H11 | **Extract Benefits BSP app** | #005b | Code | Find BSP name from `ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT` manifest |
| H12 | **Populate HCM/Reports folder** | #005b | Code | Extract Z-reports in HCM namespace |
| H13 | **BCM dual-control gap remediation** | #021 | Audit | UNES: 1,557 same-user batches (CRUSR=CHUSR). UBO: 284. Potential audit finding. Needs root cause analysis. |
| H14 | **Extract YWFI package source from D01** | #021 | Code | Z_GET_CERTIF_OFFICER_UNESDIR, Z_WF_GET_CERTIFYING_OFFICER etc. D01 HTTP blocked via VPN — needs on-site or VPN route |
| ~~H15~~ | ~~Read Blueprint BCM pages 21-47~~ | ~~#021~~ | ~~Knowledge~~ | ~~Done #022 — Full 21 SAP Notes, Delegation of Authority table, grouping rules, XML char handling all extracted~~ |

### 🟢 BACKLOG — When blocking/high are clear

#### Process Mining & Analytics
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G1 | **OCEL 2.0 multi-object** | #009 | Cross-process Fund→PO→Invoice in single event log |
| G2 | **CTS conformance deep dive** | #009 | Which transports deviate? (100% conformant found — may need more data) |
| G3 | **Pattern Brain (Algorithms)** | #005b | Anomaly detection, fund clustering, spending network on FMIFIIT |
| G4 | **process-intelligence.html: filter RELE entries** | #003 | Other/RELE inflates activity count |
| G5 | **process-intelligence.html: browser verification** | #003 | Never verified in browser |

#### Skills & Governance
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G6 | **Build T2R skill** | #018 | Travel-to-Claim — no dedicated skill |
| G7 | **Build P2D skill** | #018 | Project-to-Close — no dedicated skill |
| G8 | **Create `crp_fiori_app` skill** | #017 | CRP 19 open items |
| G9 | **Publish `sap-intelligence` SKILL.md** to ecosystem | ecosystem | 33 local skills, ecosystem doesn't know them |
| G10 | **Promote Transport Companion pattern** | ecosystem | Proven in #019, not yet ecosystem-level |
| G11 | **Promote Company Code Copy checklist** | ecosystem | 41-task protocol, proven in #019 |
| G12 | **Cross-reference maturity vs SESSION_LOG** | #018 | Verify "Production" skills were actually used |

#### Data Extraction (non-blocking)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G13 | **Job source code extraction** | #018 | 228 programs catalogued, code not extracted |
| G14 | **BP Conversion extraction** | #005b | LFA1/KNA1/BUT000/CVI links — S/4HANA readiness |
| G15 | **PSM domain code extraction** | #005b | extracted_sap/PSM/ is empty |
| G16 | **Real Estate domain extraction** | #005b | New domain discovered — extracted_sap/RE/ |

#### CTS Dashboard Fixes
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G17 | **Improve module classification** | #004 | 3,329/4,168 in "General IMG" — needs better mapping |
| G18 | **total_mods verification** | #004 | Confirm = distinct transport ORDER count |
| G19 | **topbar KPI sync** | #004 | "28 Contributors" hardcoded vs DATA.top_users.length |
| G20 | **TADIR cache enrichment** | #004 | SOTR/VARX types skipped (GUID keys) |

#### Infrastructure
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G21 | **Vector Brain (ChromaDB)** | #005b | Index ABAP code + skills + field descriptions |
| G22 | **SAP MCP Server build** | #005b | Half-built in SAP_MCP/ — expose RFC_READ_TABLE as MCP tool |
| G23 | **Duplicate script cleanup** | #005b | extract_* in mcp-backend-server-python/ AND sap_data_extraction/scripts/ |
| G24 | **Index YRGGBS00 + YPS8** | #005b | Move to extracted_sap/PSM/ and index |
| G25 | **Archive legacy root docs** | #005b | ROADMAP.md, pmo_tracker.md superseded |
| G26 | **Brain auto-refresh workflow** | #006 | `--build` after every extraction automatically |
| G27 | **Notion PMO sync** | #006 | Write PMO Brain to Notion database via MCP |

#### Future Ideas
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G28 | **Fiori PA Mass Update App** | #002 | Replace PRAA* BDC (135 sessions/quarter) |
| G29 | **Coupa → SAP API Interface** | #002 | Replace COUPA* BDC (12 sessions/quarter) |
| G30 | **BDC Trigger Analysis (RISK)** | #002 | Map what triggers each BDC type — needed before replacement |
| G31 | **P01 user activity map** | #006 | USR02 + active session → who uses what |
| G32 | **Service node enrichment** | #006 | Add $metadata as SERVICE node in brain |
| G33 | **Transport Living Knowledge** | #005b | doc_reference + doc_supplement as evolving seeds |
| G34 | **abapGit integration** | #006 | List all repos, link to brain nodes |
| G35 | **Catch live BDC field data** | #002 | `bdc_deep_analysis.py --state E` for ERROR sessions |
| G36 | **sap_bp_conversion SKILL.md** | #005b | Future skill for BP migration strategy |

#### Ecosystem-Level
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G37 | **Rescue Vendor MDM** | ecosystem | 98 days stalled |
| G38 | **ADR-004: Testing as Skill or Project?** | ecosystem | Architecture decision pending |
| G39 | **Promote BSP React patterns** | ecosystem | To `.knowledge/skills/sap-fiori-react/SKILL.md` |
| G40 | **Score UNESCO SAP Brain on 10 dimensions** | ecosystem | Gap analysis |

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
