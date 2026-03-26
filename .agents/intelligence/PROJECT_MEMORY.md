# PROJECT_MEMORY.md
## UNESCO SAP System Intelligence — Living Project Memory

**Purpose**: The authoritative memory for this project. Updated at the end of every session.
The agent reads this FIRST at the start of every conversation to restore full context.

---

## System Architecture (Non-Negotiable Rules)

```
D01 (Development)  ← code deploy, BSP extract, ADT API — password auth
P01 (Production)   ← data, monitoring, BDC, active users  — SNC/SSO only
```

| System | Host | Port | Auth |
|--------|------|------|------|
| D01 | `HQ-SAP-D01.HQ.INT.UNESCO.ORG` | 80 | Password (HTTP Basic) + SNC (RFC) |
| P01 | `172.16.4.100` | 8000 | **SNC/SSO only — no password** ✅ |

Both systems: Client `350`, User `jp_lopez`, SNC partner `p:CN=D01` / `p:CN=P01`

---

## Three-Pillar Tool Stack

| # | Pillar | Script / Tool | When to Use |
|---|--------|--------------|-------------|
| 1 | **Python RFC** | `pyrfc` + SNC | Table reads, BDC sessions, active users, background jobs, dumps |
| 2 | **ADT REST API** | `sap_adt_client.py` | Read/write/activate ABAP source (classes, programs, BSP, etc.) |
| 3 | **Fiori Tools CLI** | `@sap/create-fiori` (npx) | Fiori app scaffolding, manifest.json, OData metadata reading |

---

## Seven Capability Layers (Feed Each Other)

```
┌─────────────────────────────────────────────────────────────┐
│ L7: Process Intelligence → consumes L2 (event logs) + L5 (CTS)
│ L6: Fiori Development    → consumes L2 (data) + L3 (domain) + L4 (code)
│ L5: Transport Intel      → feeds L4 (what changed) + L3 (config rules)
│ L4: Code Extraction      → feeds L6 (reverse-engineer to rebuild)
│ L3: Validation/Domain    → feeds L2 (what to extract) + L6 (business rules)
│ L2: Data Extraction      → feeds L3 (validate) + L7 (event logs)
│ L1: SAP Connectivity     → enables ALL other layers
└─────────────────────────────────────────────────────────────┘
```

| Layer | Skills | Key Tools | Current State |
|-------|--------|-----------|---------------|
| L1: Connectivity | sap_webgui, sap_native_desktop, sap_debugging_and_healing | pyrfc, SNC/SSO | ✅ Stable |
| L2: Data Extraction | **NEEDS SKILL** | extract_fmifiit_full.py, read_psm_logic.py | ✅ FMIFIIT done, BKPF/BSEG pending |
| L3: Validation | sap_expert_core, unesco_filter_registry | sap_brain.py | ✅ Active |
| L4: Code Extraction | sap_adt_api, sap_reverse_engineering, sap_enhancement_extraction | sap_adt_client.py | ✅ Active |
| L5: Transport Intel | sap_transport_intelligence | cts_dashboard.html | ✅ Active |
| L6: Fiori Dev | sap_fiori_tools, sap_fiori_extension_architecture | Vite + React + UI5 | ✅ Offboarding clone |
| L7: Process Intel | parallel_html_build | process-intelligence.html | ✅ Built |

**Critical cross-layer relationships:**
- L2→L3: FMIFIIT data validates fund/center joins (99.9% FONDS, 100% FISTL match)
- L2→L7: Extracted CTS data → real event logs in process intelligence tool
- L5→L4: Transport analysis reveals what code changed → targets for extraction
- L3→L6: Domain knowledge (UNESCO custom tables, filter logic) → business rules for Fiori apps
- L4→L6: Reverse-engineered OData/BSP code → architecture for replacement apps

---

## Agent Architecture (Anthropic Framework)

**Design Docs**: `AGENT_ARCHITECTURE.md` + `BRAIN_ARCHITECTURE.md` in `.agents/intelligence/`

### Core Principle: Living Knowledge, Not Static Documents
Knowledge, skills, and conclusions are NOT static. Each new analysis refines the brain.
Word docs, expert knowledge, and discovered patterns are SEEDS — the agent must evolve them.

### Multi-Agent Architecture (Session #006)
Coordinator → Domain Agent pattern (Anthropic orchestrator-workers):
- **Coordinator** (`.agents/skills/coordinator/SKILL.md`): routes by UNESCO process/domain
- **PSM** (`.agents/skills/psm_domain_agent/SKILL.md`): FM/budget, WRTTP filter, gold DB queries
- **HCM** (`.agents/skills/hcm_domain_agent/SKILL.md`): employee lifecycle, Allos replacement, ASR
- **FI** (`.agents/skills/fi_domain_agent/SKILL.md`): GL, OBBH/YRGGBS00, FM-FI bridge

### 3 Operational Modes
| Mode | Anthropic Pattern | Example |
|------|------------------|---------|
| **Discovery** | Orchestrator-Workers + Evaluator-Optimizer | "Analyze FMIFIIT spending patterns" |
| **Building** | Prompt Chaining + Parallelization | "Extract BKPF/BSEG data" |
| **Monitoring** | Autonomous Agent loop | "Overnight extraction" |

### 4-Layer Brain
| Layer | Technology | Purpose | Status |
|-------|-----------|---------|--------|
| A: Document | SQLite + Markdown + Skills | Facts, procedures, rules | ✅ Active |
| B: Graph | networkx + sap_brain.py | Relationships, impact chains | ✅ **748 nodes / 564 edges** (6 sources) |
| C: Vector | ChromaDB + sentence-transformers | Semantic search across ALL knowledge | ⏳ Planned |
| D: Pattern | pandas + scipy + sklearn | Anomaly detection, clustering, trends | ⏳ Planned |

### Expert Seed Documents (Living Knowledge Sources)
| Document | Size | Content | Location |
|----------|------|---------|----------|
| `doc_reference.txt` | 28 KB | Transport anatomy (603 paragraphs) | mcp-backend-server-python/ |
| `doc_supplement.txt` | 31 KB | Module-specific risks (HR/PSM/PS/Bank/FI) | mcp-backend-server-python/ |
| `YRGGBS00_SOURCE.txt` | 105 KB | Substitution exit — L3 derivation logic | mcp-backend-server-python/ |
| `YPS8_ALL_METHODS.txt` | 76 KB | PSM budget control logic | mcp-backend-server-python/ |

---

## Data Extraction State (Layer 2)

### Gold Database: `p01_gold_master_data.db` — ~2 GB, ~18M+ rows

| Table | SAP Source | Rows | Status |
|-------|-----------|------|--------|
| **cdhdr** | CDHDR | **7,810,913** | ✅ Session #011 (2024-2026, 57 OBJECTCLAS) |
| bsis | BSIS | 2,291,246 | ✅ Session #010 |
| **fmifiit_full** | FMIFIIT | **2,070,523** | ✅ (2024-2026, all 7 areas) |
| bkpf | BKPF | 1,677,531 | ✅ Session #010 |
| bsas | BSAS | 1,480,715 | ✅ Session #010 |
| bsak | BSAK | 739,910 | ✅ Session #010 |
| essr | ESSR | 710,574 | ✅ Session #010 |
| ekbe | EKBE | 482,532 | ✅ Session #010 |
| bsad | BSAD | 211,201 | ✅ Session #010 |
| ekpo | EKPO | 190,927 | ✅ Session #010 |
| rseg | RSEG | 162,539 | ✅ Session #011 |
| rbkp | RBKP | 126,428 | ✅ Session #011 |
| cts_objects | E071 | 108,290 | ✅ |
| ekko | EKKO | 68,861 | ✅ Session #010 |
| funds | FMFCT | 64,799 | ✅ |
| prps | PRPS | 58,516 | ✅ |
| eban | EBAN | 23,160 | ✅ Session #011 |
| fmavct_summary | FMAVCT | 19,111 | ✅ |
| fmbdt_summary | FMBDT | 19,008 | ✅ |
| movements_summary | FMIFIIT(agg) | 18,975 | ✅ |
| proj | PROJ | 13,878 | ✅ |
| bsik | BSIK | 8,015 | ✅ Session #010 |
| cts_transports | E070 | 7,745 | ✅ |
| ytfm_fund_cpl | Custom | 6,368 | ✅ |
| bsid | BSID | 4,677 | ✅ Session #010 |
| tadir_enrichment | TADIR | 4,168 | ✅ |
| fund_centers | FMFCTR | 764 | ✅ |
| cooi | COOI | 0 | ❌ Investigate |
| coep | COEP | 0 | ❌ Investigate |
| rpsco | RPSCO | 0 | ❌ Investigate |

### Key Finding: PBC Dominates CDHDR (~90%)
- FMRESERV = 82% of CDHDR (6.4M of 7.8M) — driven by PBC budget engine
- F_DERAKHSHAN = 80% of FMRESERV (5.14M) — RFC/BAPI from PBC, no TCODE
- HIPER = 10% — ZPBC_PERIOD_CLS_EXEC (period close), January spikes (carryforward)
- For non-FM analysis, filter out OBJECTCLAS='FMRESERV'

### SAP Field Name Gotchas (NEVER assume — always DD03L first)

| Module | Wrong | Correct | Table |
|--------|-------|---------|-------|
| FM | BELNR | FMBELNR | FMIFIIT |
| FM | BUZEI | FMBUZEI | FMIFIIT |
| FM | POPER | PERIO | FMIFIIT |
| FM | HSL | FKBTR | FMIFIIT |
| FM | KSL | TRBTR | FMIFIIT |
| PS | (visible) | PSPNR (internal) | PROJ/PRPS |
| FI | BELNR ✅ | BELNR | BKPF/BSEG |

### Extraction Protocol (MANDATORY)
1. **DD03L first** — get actual fields
2. **Test 3 rows** — verify connectivity
3. **Batch by natural key** — not ROWSKIPS
4. **Handle TABLE_WITHOUT_DATA** — = 0 rows
5. **Auto-load to SQLite** — immediately after extraction
6. **Verify vs anchors** — compare row counts
7. **Delete JSON after verification** — no redundant data

---

## Key Scripts

### Data Extraction (in `sap_data_extraction/scripts/`)

| Script | Purpose | State |
|--------|---------|-------|
| `extract_fmifiit_full.py` | FMIFIIT 2024-2026, auto-loads SQLite | ✅ DONE |
| `extract_bkpf_bseg_parallel.py` | BKPF + BSEG by month | Ready |
| `extract_ekko_ekpo_parallel.py` | EKKO/EKPO/EKBE/ESSR/ESLL | Ready |
| `run_overnight_extraction.py` | Orchestrator (max 2 SAP connections) | Ready |
| `read_psm_logic.py` | PSM master data → SQLite | ✅ DONE |

### Code Tools (in `mcp-backend-server-python/`)

| Script | Purpose | Default System |
|--------|---------|---------------|
| `sap_adt_client.py` | Full ADT client — read/write ABAP | D01 |
| `extract_bsp_via_adt.py` | Download BSP/UI5 apps | D01 |
| `sap_system_monitor.py` | 7-report P01 dashboard | P01 |
| `bdc_full_inventory.py` | Full BDC session analysis | P01 |
| `sap_brain.py` | Knowledge graph builder | both |

---

## Domain Folder Structure

```
extracted_sap/
├── HCM/
│   ├── Fiori_Apps/
│   │   ├── Offboarding/
│   │   │   ├── bsp/        ← BSP_ZHROFFBOARDING, BSP_YHR_OFFBOARDEMP ✅
│   │   │   ├── services/   ← OData services (to extract)
│   │   │   └── classes/    ← ZCL_ZHRF_OFFBOARD_* ✅
│   │   ├── Benefits/
│   │   │   └── classes/    ← ZCL_ZHR_BENEFITS_* ✅
│   │   └── _shared/
│   │       └── classes/    ← ZCL_HR_FIORI_* ✅
│   ├── Reports/
│   └── Interfaces/
├── PSM/
└── _shared/
```

---

## What Has Been Extracted (Confirmed Working)

### HCM / Offboarding
- **BSP_ZHROFFBOARDING** — Manager-facing offboarding app (full source)
- **BSP_YHR_OFFBOARDEMP** — Employee-facing offboarding app (full source)
- **ZCL_ZHRF_OFFBOARD_DPC_EXT** — OData data provider class
- **ZCL_ZHRF_OFFBOARD_MPC / MPC_EXT** — OData model provider class
- **ZCL_ZHRF_OFFBOARDIN_01_DPC_EXT** — Second DPC variant

### HCM / Benefits
- **ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT** — Family members Fiori DPC
- **ZCL_ZHR_BENEFITS_REQUE_DPC_EXT / MPC_EXT** — Benefits request classes

### HCM / Shared
- **ZCL_HR_FIORI_OFFBOARDING_REQ** — Shared offboarding logic
- **ZCL_HR_FIORI_BENEFITS** — Shared benefits logic
- **ZCL_HR_FIORI_BADCOMMON** — Common BAD utilities
- **ZCL_HR_FIORI_RENTAL** — Rental allowance logic
- **ZCL_HR_FIORI_REQUEST** — Request base class

### PSM / Data Extraction (Session #005 — 2026-03-15)
- **FMIFIIT** — 2,070,523 FM/FI integration documents (2024-2026, 7 fund areas) ✅
- **FMFCT** — 64,799 fund masters ✅
- **FMFCTR** — 764 fund centers ✅
- **PROJ** — 13,878 project definitions ✅
- **PRPS** — 58,516 WBS elements ✅
- **FMBDT** — 19,008 budget summaries ✅
- **FMAVCT** — 19,111 availability control summaries ✅
- **YTFM_FUND_CPL** — 6,368 UNESCO fund-ceiling couplings ✅
- **YTFM_WRTTP_GR** — 66 UNESCO value type groups ✅
- **E070/E071** — 7,745 transports + 108,290 transport objects ✅

---

## System Monitor — P01 Findings (2026-03-12)

### P01 Object Counts
| Type | P01 | D01 | Delta |
|------|-----|-----|-------|
| PROG | 826 | 1000 | 174 not promoted |
| CLAS | 142 | 266 | 124 in dev only |
| WAPA | **0** | 13 | **No Fiori in prod** |

### BDC Complete Intelligence (90-day full inventory — Session #002)

#### Session Types by Origin

| Origin | Sessions | Meaning |
|--------|:--------:|---------|
| **Travel module (TRIP_MODIFY)** | **1,180** | Real users + ALE. NOT Allos. DO NOT REPLACE. |
| **Allos PRAA* (PA30/PA40)** | **135** | ← Replacement Target #1 (BBATCH service account) |
| **Payroll posting (MSSY1/Y1)** | hundreds | Standard SAP payroll-to-FI. NOT Allos. Keep. |
| Coupa integration (COUPA*) | 12 | Procurement system → HR BDC. Replace with BAPI. |
| SZORME-RFC | 22 | Unknown external system. Investigate. |
| SAS-RFC | 17 | SAS analytics or other system. Investigate. |
| FM/Support Cost | 13 | Finance batch — replace with FMBB BAPI |
| HR batch (HUNUPSR0) | 11 | Standard SAP HR mass update |

#### Creator Map
| Creator | Sessions | Role |
|---------|:--------:|------|
| `COLLOCA` | 195 | Primary Allos operator |
| `BBATCH` | 135 | Allos service account (automated) |
| `GAMA-BERNA` | 64 | Payroll admin + Allos |
| Travel users (BOUQUET, ZELDINA…) | 280+ | Regular travel expense users |
| `SZORME-RFC` | 22 | External RFC system |
| `SAS-RFC` | 17 | External RFC system |
| `EARLE`, `NOBLET`, `MEKONNEN` | 44 | Payroll posting admins |

#### Key Technical Facts (APQI/APQD)
- **APQD is PURGED** after successful processing (QSTATE=S/F). Only ERROR sessions have live APQD.
- **PROGID=`MSSY1`** = SAP logical system Y1 = HCM payroll backend (not a program name).
- **Numeric session names** = `[PERNR][PayrollArea][RunID]` (e.g., `10155259V901`)
- **PERNR 10155259** confirmed = real UNESCO employee in PA0001 ✅
- **APQI fixed-width parser** requires exact field widths — use `parse_fixed()` from `bdc_full_inventory.py`

#### Allos Target: PRAA* Sessions → Transaction PA30/PA40
```
PRAAUNESC_SC    89  PA30/PA40  BAPI: BAPI_EMPLOYEE_ENQUEUE + HR_MAINTAIN_MASTERDATA
PRAAUNESU_ST    19  PA30       BAPI: BAPI_EMPLOYEE_ENQUEUE + HR_INFOTYPE_OPERATION
PRAAUNESU_SC    13  PA30       same
PRAAUBOU_SC      2  PA30       same
COUPA0000272+   12  PA30       Coupa system → needs REST/BAPI interface
```

---

## What Still Needs To Be Done

### Immediate Next Extractions
- [ ] Extract OData services (`ZHRF_OFFBOARD_SRV`, etc.) → `HCM/Fiori_Apps/Offboarding/services/`
- [ ] Extract Benefits BSP app → `HCM/Fiori_Apps/Benefits/bsp/`
- [ ] Extract Reports from `HCM/Reports/` (PSM not started at all)

### Brain Enrichment
- [ ] Add P01 monitoring data to brain (BDC sessions as RELATED_BDC edges)
- [ ] Add ADT-discovered services as SERVICE nodes
- [ ] Run `--build` after each extraction to grow the graph

### Custom App Development (Allos Replacement)
- [ ] Design `PRAAUNESC_SC` replacement Fiori app (PA data entry)
- [ ] Identify target BAPI for PA infotype updates (PA30/BAPI_EMPLOYEE_ENQUEUE)

---

## Memory Strategy

**After every session, update this file with:**
1. New extractions completed → add to "What Has Been Extracted"
2. New P01 monitoring findings → update System Monitor section
3. New BDC patterns discovered → update Allos section
4. New capabilities added → update Key Scripts table

**At session start:**
1. READ this file first
2. READ `.agents/intelligence/sap_companion_intelligence.md` for full detail
3. Check `sap_brain.json` for current node count

---

*Last updated: 2026-03-16 | Session #011: CDHDR 7.8M rows + P2P complete + PBC dominance discovery*

---

## Process Intelligence Tool (Session #003 — 2026-03-12)

**File**: `Zagentexecution/process-intelligence.html` (297KB, single-file)

### What It Does
Signavio-inspired process mining tool. Reads SAP data sources, mines event logs, renders DFG process maps, variants, KPIs, conformance checking, and AI insights.

### Process Domains Covered
| Domain | SAP Sources | BRS Score |
|--------|------------|-----------|
| Purchase to Pay | EKKO/EKPO/MIGO/MIRO | 72% |
| Order to Cash | VBAK/VBAP/VBRK | 88% |
| Incident Mgmt | SM37/SWEL/SWI2 | 65% |
| **Fund Management** | FMFCTRT/FMIFIIT/FMBUBA | 79% |
| **HR Hire-to-Retire** | PA0000/PA0001/T529A | 82% |
| **Travel & Expense** | PTRV_HEAD/PTRV_SCOS | 71% |
| **CTS Change Mgmt** | E070/E071 — **REAL DATA** ✅ | 78% |

### CO Object Mapping (PSM Integration)
```
Fund Center   ←→  Cost Center (CSKS, CSKT, COSP)
Grant         ←→  WBS Element (PROJ, PRPS, PRTE, RPSCO)
Budget Line   ←→  Internal Order (AUFK, AUFKV, COEP)
```
These three CO objects together give the complete PSM spending process picture.

### Real CTS Data Extracted (D01 System)
- **2,579 transports** — 2022/2023/2024
- **By type**: Customizing 1,420 · Workbench 965 · Transport-of-copies 194
- **Top real categories**: Config/ViewData (257) · METH (248) · TABU (231) · Code/Program (131)
- ⚠️ **Filter `Other/RELE`** (1,162) — these are release link objects, not real process activities

### Build Pipeline (to refresh with new data)
```bash
python _build_cts_eventlog.py    # extracts CTS → event log JSON
python _build_realdata_js.py     # embeds JSON as JS constant
python _join_parts.py            # joins 6 parts → process-intelligence.html
```

### Critical Algorithm Note
**DFS topo sort + longest-path layering** must be used for process graph layout. BFS fails on cycle-containing event logs (all nodes land at layer 0).
