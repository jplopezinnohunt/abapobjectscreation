# UNESCO SAP — Project Brain + PMO Brain
> Two brains, one project. Updated every session. Read alongside `PROJECT_MEMORY.md`.

---

## PROJECT BRAIN — What We Built

### The System (as of 2026-03-26)

```
UNESCO SAP Intelligence Toolkit — 10 Capability Layers, 31 Skills
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

Governance: .agents/GOVERNANCE.md + SKILL_MATURITY.md (31 skills scored)
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

### What the Brain Knows (73,381 nodes — Session #007)
- **64,766 FUNDs** + 710 FUND_CENTERs + 7 FUND_AREAs (with aggregate metadata)
- **7,745 TRANSPORTs** (full CTS inventory)
- **59 Code objects**: 2 BSP Apps, 13 Classes, 44 Tables, App Areas, Domains
- **45 KNOWLEDGE_DOC nodes**: cross-referenced to classes and tables
- **23 SKILL nodes**: L1-L7 + Meta layer + sap_data_extraction (new)
- **10 DOCUMENT nodes**: expert seeds (YRGGBS00, doc_reference, FI substitution sources)
- **5 PROCESS nodes**: B2R, H2R, P2P, T2R, P2D — UNESCO core processes
- **8 JOINS_VIA edges**: table-to-table foreign keys (FMIFIIT→FMFCT, FMIFIIT→BKPF, etc.)
- **3-level access**: L1 BRAIN_SUMMARY.md, L2 `--focus`, L3 full JSON

### Multi-Agent Architecture (Session #006)
- **Coordinator**: `.agents/skills/coordinator/SKILL.md` — routes by process type, knows entity model
- **PSM Domain Agent**: `.agents/skills/psm_domain_agent/SKILL.md` — FM/budget specialist
- **HCM Domain Agent**: `.agents/skills/hcm_domain_agent/SKILL.md` — HR/employee lifecycle
- **FI Domain Agent**: `.agents/skills/fi_domain_agent/SKILL.md` — GL/validation/substitution

---

## PMO BRAIN — Tasks, Ideas, Backlog

### 🔴 Critical — Next Session

| # | Task | Owner | Notes |
|---|------|-------|-------|
| 1 | ~~**Extract FMIFIIT full**~~ | ~~agent~~ | ✅ DONE — 2,070,523 rows in SQLite (2026-03-15) |
| 2 | ~~**Brain redesign — Living Knowledge Engine**~~ | ~~agent~~ | ✅ DONE — 748 nodes/564 edges, 6 sources, 4 domain agents (2026-03-15) |
| 3 | ~~**Create `sap_data_extraction` SKILL.md**~~ | ~~agent~~ | ✅ DONE — `.agents/skills/sap_data_extraction/SKILL.md` (2026-03-15 #007) |
| 4 | ~~**Consolidate 3 SQLite DB copies**~~ | ~~agent~~ | ✅ DONE — 4 stale copies deleted, single canonical path (2026-03-15 #007) |
| 5 | ~~**Run overnight FI/MM extraction**~~ | ~~agent~~ | ✅ DONE — Session #010: BKPF(1.67M)+6 BS* tables(6.41M)+EKKO/EKPO/EKBE/ESSR(1.45M) |
| 6 | **Extract COOI, COEP, RPSCO** — CO cost data | agent | ~1.6M rows total, needs extraction scripts |
| 8 | ~~**CDHDR extraction**~~ | ~~agent~~ | ✅ DONE — Session #011: 7,810,913 rows (57 OBJECTCLAS, 2024-2026) |
| 9 | ~~**P2P complement: EBAN+RBKP+RSEG**~~ | ~~agent~~ | ✅ DONE — Session #011: 312K rows loaded |
| 10 | **ESLL extraction** | agent | Last missing P2P table |
| 11 | **B2R: FMIOI+FMBH+FMBL** | agent | Returned 0 rows — investigate date field/filters |
| 12 | **BSEG UNION view** | agent | CREATE VIEW over 6 Celonis tables in SQLite |
| 7 | **Design Fiori replacement for PRAA*** — PA30 infotype update app | agent+user | BAPI: `BAPI_EMPLOYEE_ENQUEUE + HR_MAINTAIN_MASTERDATA` |

### 🟡 High Priority — Soon

| # | Task | Notes |
|---|------|-------|
| 6 | Extract Benefits BSP app | Find BSP name from `ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT` manifest |
| 7 | Run P01 transaction usage report | `--report transactions --system P01` |
| 8 | Run P01 obsolete programs report | Old programs not changed in 2+ years |
| 9 | P01 runtime dumps report | `--report dumps --system P01` — what's breaking in prod? |
| 10 | **Document Coupa integration** with ICT/Coupa team | COUPA* sessions doing PA30 BDC — needs proper BAPI endpoint |
| 11 | Populate HCM/Reports folder | Extract Z-reports in HCM namespace |

### 🟢 Backlog — Ideas + Future

| # | Idea | Description |
|---|------|-------------|
| 12 | **Fiori PA Mass Update App** | Replace all PRAA* BDC with one Fiori app (135 sessions/quarter) |
| 13 | **Coupa → SAP API Interface** | Replace COUPA* BDC with REST/BAPI endpoint (12 sessions/quarter) |
| 14 | **PSM domain extraction** | Start extracting PSM (Public Sector) objects |
| 15 | **Brain auto-refresh workflow** | `--build` after every extraction automatically |
| 16 | **Service node enrichment** | Add parsed `$metadata` as SERVICE node in brain |
| 17 | **P01 user activity map** | USR02 + active session → who uses what |
| 18 | **Notion PMO sync** | Write PMO Brain to Notion database via MCP |
| 19 | **abapGit integration** | List all repos, link to brain nodes |
| 20 | **CTS transport analysis** | Which transports reference HCM objects? |
| 21 | **Architecture HTML companion** | Rich HTML with embedded graph |
| 22 | **Catch live BDC field data** | Run `bdc_deep_analysis.py --state E` when ERROR sessions appear |
| 23 | **BDC Trigger Analysis (RISK)** | For each BDC session type: identify WHAT triggers it (user action? scheduled job? external system? Allos button?). BDC is a fragile technology — SAP could deprecate it. Understanding the triggering process is needed before any replacement decision. Priority: SZORME-RFC, SAS-RFC, COUPA*, then PRAA*. |
| 24 | **CTS Dashboard — Improve module classification** | 3,329/4,168 objects land in "General IMG" — improve obj_type → module mapping to give them proper domains (FI, MM, SD, etc.) |
| 25 | **CTS Dashboard — total_mods verification** | Confirm total_mods = distinct transport ORDER count, not E071 row count. Cross-check against E070 |
| 26 | **CTS Dashboard — topbar KPI sync** | "28 Contributors" is hardcoded separately from DATA.top_users.length — sync these |
| 27 | **CTS Dashboard — TADIR cache enrichment** | SOTR/VARX types skipped (GUID keys break RFC_READ_TABLE) — add special handling to get their packages |
| 28 | **Business Partner Conversion** ⭐ | ECC→S/4HANA: Extract vendor (LFA1/LFB1) + customer (KNA1/KNB1) + existing BP (BUT000) + CVI link tables. Map conversion state. Real Estate domain already done, some clients done, vendors pending. |
| 29 | **Real Estate domain** | New domain discovered — add to domain structure (extracted_sap/RE/). Extract related objects. |
| 30 | **sap_data_extraction SKILL.md** | Create the missing Layer 2 skill — DD03L-first protocol, TABLE_WITHOUT_DATA, auto-load SQLite |
| 31 | **sap_bp_conversion SKILL.md** | Future skill for BP migration strategy — BP concept, CVI sync, role mapping, duplicate detection |
| 32 | **Vector Brain (ChromaDB)** | Install ChromaDB + sentence-transformers, index ABAP code + skills + field descriptions |
| 33 | **Pattern Brain (Algorithms)** | Build anomaly detection, fund clustering, spending network analysis on FMIFIIT data |
| 34 | **Index YRGGBS00 + YPS8** ⭐ | Move YRGGBS00_SOURCE.txt (105KB substitution exit) + YPS8_ALL_METHODS.txt (76KB budget control) to extracted_sap/PSM/ and index in Vector Brain |
| 35 | **Transport Living Knowledge** ⭐ | doc_reference.txt + doc_supplement.txt are SEEDS — evolve them with each new transport analysis. Agent must learn from every session. |
| 36 | **HTML tools integration** | Add sap_taxonomy_companion.html (L4) + epiuse_companion.html (L5) to CAPABILITY_ARCHITECTURE |
| 37 | **SAP MCP Server build** | SAP_MCP/ has a half-built MCP server for RFC — could expose RFC_READ_TABLE, BAPI_* as MCP tools for L1 |
| 38 | **Duplicate script cleanup** | extract_bkpf, extract_ekko exist in BOTH mcp-backend-server-python/ AND sap_data_extraction/scripts/ — resolve |
| 39 | **Archive legacy root docs** | ROADMAP.md (outdated), CLAUDE.md (outdated), pmo_tracker.md (superseded by PMO_BRAIN) — archive or update |
| 40 | **Merge sap_segw + segw_automation** | Consolidation candidate from SKILL_MATURITY.md review |
| 41 | **Build T2R skill** | Travel-to-Claim has no dedicated skill — coverage gap |
| 42 | **Build P2D skill** | Project-to-Close has no dedicated skill — coverage gap |
| 43 | **Cross-reference maturity vs SESSION_LOG** | Verify Production skills were actually used in sessions |

---

## SESSION LOG

### Session 2026-03-12 — TOP SESSION

**Duration**: ~70 min
**Systems touched**: D01 (dev), P01 (prod)

**Completed:**
- ✅ Fixed sap_system_monitor.py — 7 reports working
- ✅ Added `--system P01/D01` routing — monitor defaults to P01
- ✅ P01 SSO confirmed working (SNC, no password)
- ✅ BDC report from P01 — 500 sessions, found Allos patterns
- ✅ Two-system architecture encoded everywhere (`.env`, scripts, skill)
- ✅ Domain folder structure: `extracted_sap/HCM/PSM/_shared`
- ✅ Moved all extractions into domain structure
- ✅ `sap_brain.py` — knowledge graph builder (55 nodes, 66 edges)
- ✅ Project Brain + PMO Brain created
- ✅ `skill_creator/SKILL.md` — Anthropic framework for skill quality
- ✅ `PROJECT_MEMORY.md` — session memory anchor
- ✅ `.agents/intelligence/` — organized document hub

---

### Session 2026-03-12 — BDC Deep Dive (~10:16–10:50)

**Duration**: ~35 min
**Systems touched**: P01 (prod only)

**Completed:**
- ✅ `bdc_deep_analysis.py` — forensic BDC tool (APQD, PROGID decode)
- ✅ `bdc_full_inventory.py` — ALL sessions, no limit, full decode
- ✅ `bdc_schema_probe.py` + `decode_numeric_bdc.py` — investigation tools
- ✅ Separated high-level monitor (`sap_system_monitor.py`) from deep analysis tools
- ✅ Cracked numeric sessions: `MSSY1` = SAP Y1 payroll system → `PC00_M99_CIPE`
- ✅ Confirmed `TRIP_MODIFY` (1,180) = real users + ALE, NOT Allos
- ✅ Identified true Allos target: 135 PRAA* sessions via `BBATCH` service user
- ✅ **New discovery**: `COUPA*` sessions = Coupa procurement → SAP HR via BDC (PA30)
- ✅ **New discovery**: `SZORME-RFC` (22) + `SAS-RFC` (17) = external RFC integrations

**Key insight of the session:**
> BDC sessions in SAP have multiple origins. Not everything is Allos.
> `TRIP_MODIFY` = users. Numeric sessions = payroll system. `PRAA*` = Allos.
> PROGID is the logical system name, not the ABAP program name.
> APQD is purged after success — always work from ERROR sessions for live field data.

**Pending**: SZORME-RFC + SAS-RFC identification, OData service extraction, Fiori PRAA* replacement design.

---

### Session 2026-03-12 — Process Intelligence Tool (~13:00–18:35) ⭐

**Duration**: ~5.5 hours

**Completed:**
- ✅ `process-intelligence.html` — 297KB single-file Signavio-inspired process mining tool
- ✅ 6 process domains with SAP table mapping: P2P · O2C · Incident · **FM** · **HR** · **Travel**
- ✅ 15 SAP data sources registry (CTS · BDC · FI · FM · CO · HR · Travel · Syslog · SM37 · SM20 · ENHO · WF)
- ✅ CO/PSM objects: **Cost Center** (CSKS/COSP) · **Internal Order** (AUFK) · **WBS** (PROJ/PRPS)
- ✅ **Real CTS data embedded**: 2,579 transports (2022–2024), 400-case sample, actual change_cat activities
- ✅ `_build_cts_eventlog.py` + `_build_realdata_js.py` — reusable data pipeline
- ✅ `parallel_html_build/SKILL.md` — formalized the parallel build skill
- ✅ Fixed D3 process map layout (BFS bug → DFS topo sort + longest-path)
- ✅ Configuration & Enhancements group: CTS · BDC · CDHDR · ENHO · Workflows

**Key discovery of session:**
> UNESCO SAP is **Config-heavy**: 1,420 Customizing vs 965 Workbench transports.
> CTS data is the richest process mining source we already have extracted.
> `Other/RELE` entries inflate activity count — must filter in next pass.

**Pending**: Browser verification, filter RELE entries, OData service extraction.

---



1. **Every session**: Read `PROJECT_MEMORY.md` + this PMO Brain first
2. **Every session**: Pick 1 🔴 Critical + 1-2 🟡 High Priority tasks
3. **Every session end**: Update this file with completed items + new ideas
4. **Brain rule**: After any extraction → run `sap_brain.py --build --html`
5. **Skill rule**: After discovering a new pattern 3x → create a skill for it
6. **P01 rule**: All monitoring data from P01 only. Never use D01 data for decision-making.
