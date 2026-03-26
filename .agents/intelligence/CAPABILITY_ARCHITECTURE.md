# UNESCO SAP Intelligence — Capability Architecture
> 7 layers × their skills × cross-layer connections × lessons learned
> Updated: 2026-03-15 (Session #005)
> **Read this alongside PROJECT_MEMORY.md for full context.**

---

## The Fundamental Principle

**Data is the ground truth.** It reflects what actually happened in the system.
By analyzing data — extracting patterns, counting, joining, comparing — you understand **system behavior**.

**Programs define mechanisms.** UNESCO's custom ABAP programs and enhancements
define HOW the system behaves differently from standard SAP. They change behavior
through BADIs, exits, substitutions, and custom logic.

**Reports are the synthesis.** Especially in the PSM domain, reports combine
*multiple elements* — data from several tables, validation rules, substitution
derivations, Z-tables, standard SAP logic — into the **final business solution**.
A single PSM report reveals more about how UNESCO's system works than any
individual table, config, or program in isolation.

```
                    THE DISCOVERY LOOP
  ═══════════════════════════════════════════════════

  DATA (L2)            CODE (L4)           REPORTS (L3+L4)
  ───────────          ───────────         ─────────────────
  What happened        How it's made       How it all combines
  Ground truth         Mechanisms          The synthesis
  Tables, rows         Programs, BADIs     SELECT+WHERE+IF+Z*
  Patterns reveal      Enhancements        = final business solution
  system behavior      change behavior

  Example: FMIFIIT     Example: ENHO       Example: ZFMRP001
  2M rows show         modifies FM         reads FMIFIIT + funds +
  spending reality     posting logic       YTFM_FUND_CPL + applies
                                           validation + substitution
                                           = UNESCO's actual process
```

---

## The Architecture

Each layer builds **specialized expert skills**. Those skills then **connect
across layers** — a skill in one layer consumes outputs from skills in other layers.

```
┌─────────────────────────────────────────────────────────────────────┐
│  L7: PROCESS INTELLIGENCE                                            │
│  L6: FIORI APP DEVELOPMENT                                          │
│  L5: TRANSPORT INTELLIGENCE                                          │
│  L4: CODE & ENHANCEMENT EXTRACTION (programs = mechanisms)           │
│  L3: VALIDATION & SUBSTITUTION (rules + reports = synthesis)         │
│  L2: DATA EXTRACTION (ground truth = reality)                        │
│  L1: SAP CONNECTIVITY & AUTOMATION                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## L1: SAP CONNECTIVITY & AUTOMATION

### Purpose
Reliable, authenticated connections to SAP. The foundation everything else stands on.

### Skills
| Skill | What It Does |
|-------|-------------|
| `sap_webgui` | Browser automation of SAP Web GUI (Playwright) |
| `sap_native_desktop` | win32com automation of SAP Logon thick client |
| `sap_debugging_and_healing` | Self-heal dumps, auth failures, timeouts, lock conflicts |

### Current State
- ✅ P01 (prod) — SNC/SSO, no password, stable RFC via pyrfc
- ✅ D01 (dev) — Password + SNC, both RFC and HTTP/ADT
- ✅ .env config centralized at `mcp-backend-server-python/.env`
- ✅ Two-system rule enforced: D01=code, P01=data

### Lessons Learned (Across Sessions)
| Lesson | Session |
|--------|---------|
| P01 SSO works — no password needed for prod | #001 |
| .env path must be resolved relative to script location, not CWD | #005 |
| SNC partner name is case-sensitive (`p:CN=P01` not `P:CN=P01`) | #001 |
| Connection timeout → check .env first, then network | #005 |
| Always test with RFC_SYSTEM_INFO before starting work | #005 |

### Feeds
→ ALL other layers (L2-L7) — nothing works without connectivity

### Needs Next
- [ ] Fix RFC_SYSTEM_INFO field parsing (health report shows `?`)
- [ ] Document SNC certificate renewal procedure

---

## L2: DATA EXTRACTION

### Purpose
Extract SAP table data via RFC_READ_TABLE into JSON checkpoints → SQLite gold database.

### Skills
| Skill | What It Does |
|-------|-------------|
| **`sap_data_extraction`** | ⚠️ **TO CREATE** — DD03L-first protocol, batching, auto-load SQLite |
| `sap_automated_testing` | Verify OData service generation/activation |

### Current State
- ✅ Gold DB: `p01_gold_master_data.db` — **503 MB, 2,070,523 rows** in main table
- ✅ FMIFIIT extracted: all 7 fund areas × 3 years (2024-2026)
- ✅ PSM master data: funds (64K), centers (764), projects (13K), WBS (58K)
- ✅ Budget/availability summaries: FMBDT (19K), FMAVCT (19K)
- ✅ CTS data loaded: 7,745 transports + 108,290 objects
- ❌ FI data not extracted: BKPF, BSEG (scripts ready)
- ❌ MM data not extracted: EKKO, EKPO, EKBE (scripts ready)
- ❌ CO data not extracted: COOI, COEP, RPSCO (scripts needed)

### Lessons Learned (Session #005 — CRITICAL)
| Lesson | Impact |
|--------|--------|
| **NEVER assume field names** — always DD03L first | Used BELNR instead of FMBELNR, POPER instead of PERIO — caused 0-row extractions |
| **FM tables prefix fields with FM** | FMBELNR, FMBUZEI, not BELNR, BUZEI |
| **RFC TABLE_WITHOUT_DATA = 0 rows**, not an error | Must catch in try/except and continue |
| **Batch by natural key (PERIO), not ROWSKIPS** | ROWSKIPS is fragile and causes SAP server memory issues on large tables |
| **Auto-load to SQLite immediately** | Previous sessions left data in JSON checkpoints — never moved to SQLite |
| **16 SAP periods, not 12** | Special periods 13-16 carry year-end adjustments (period 15 had 2,656 rows) |
| **Delete JSON after SQLite verified** | 977 MB of redundant JSON was cleaned up |
| **Verify with volume_anchors** | Compare extracted counts vs known SAP row counts |

### Field Name Gotchas Registry
| Module | Wrong (assumed) | Correct (DD03L) | Table |
|--------|---------|---------|-------|
| FM | BELNR | FMBELNR | FMIFIIT |
| FM | BUZEI | FMBUZEI | FMIFIIT |
| FM | POPER | PERIO | FMIFIIT |
| FM | HSL | FKBTR | FMIFIIT |
| FM | KSL | TRBTR | FMIFIIT |
| FM | FIPOS | FIPEX | FMIFIIT |
| FM | VALTYPE | WRTTP | FMIFIIT |
| PS | (visible code) | PSPNR (internal) | PROJ/PRPS |
| FI | BELNR ✅ | BELNR | BKPF/BSEG |
| CO | BELNR ✅ | BELNR | COEP |

### Mandatory Extraction Protocol
1. **DD03L first** — `RFC_READ_TABLE` on DD03L with `TABNAME = 'target'`
2. **Test 3 rows** — verify field names work
3. **Volume check** — count rows by key segments
4. **Batch by natural key** — PERIO, BUDAT month, FIKRS, etc.
5. **Handle TABLE_WITHOUT_DATA** — try/except → 0 rows
6. **Checkpoint per batch** — JSON after each period/month
7. **Auto-load to SQLite** — immediately after area/year completes
8. **Verify vs anchors** — compare row counts
9. **Delete JSON** — after SQLite verified

### Feeds
→ L3 (data validates domain knowledge, confirms/contradicts assumptions)
→ L7 (CTS data → event logs for process mining)

### Consumes
← L1 (RFC connection)
← L3 (domain knowledge tells WHAT tables to extract, WHICH filters to apply)

### Needs Next
- [ ] **Create `sap_data_extraction` SKILL.md** (only layer without one)
- [ ] Run BKPF/BSEG overnight extraction
- [ ] Build COOI/COEP/RPSCO extraction scripts
- [ ] Add auto-load to ALL extraction scripts (not just FMIFIIT)

---

## L3: VALIDATION & SUBSTITUTION (Business Rules Brain)

### Purpose
Understand, catalog, and enforce UNESCO's SAP business rules — the validations that CHECK data and the substitutions that DERIVE field values automatically. **This is the central brain.**

### Skills
| Skill | What It Does |
|-------|-------------|
| `sap_expert_core` | Deep SAP FI/CO/FM/PSM/HCM knowledge, config transactions (OB28, OBBH, etc.) |
| `unesco_filter_registry` | UNESCO-specific hardcoded filters and derivation rules found in ABAP programs |
| `sap_configuration_strategy` (workflow) | Systematic config & master data discovery protocol |

### Current State
- ✅ Core SAP expertise codified in `sap_expert_core`
- ✅ UNESCO filter registry started (ZFMRP* programs analyzed)
- ✅ YTFM custom tables extracted (fund-ceiling coupling, value type groups)
- ✅ Volume anchors verified (21/21 fund area counts match)
- ⚠️ Validation rules (OB28) not yet extracted from SAP
- ⚠️ Substitution rules (OBBH/GGB1) not yet extracted
- ⚠️ FMDERIVE derivation strategy not documented

### Lessons Learned
| Lesson | Session |
|--------|---------|
| Fund areas are organizational: UNES, IBE, ICTP, IIEP, UBO, MGIE, UIS | #005 |
| FONDS→funds.FINCODE join is 99.9%, not 100% (4 orphan funds) | #005 |
| FISTL→fund_centers.FICTR is exactly 100% | #005 |
| UNESCO has 16 posting periods (special periods carry real data) | #005 |
| WRTTP (value type) drives budget consumption vs release logic | #005 |
| CTS transport classification needs domain knowledge to assign modules | #004 |
| 3,329/4,168 CTS objects land in "General IMG" — needs better classification | #004 |
| Enhancement code reveals hidden business rules not visible in config | #004 |

### SAP Config Transactions (L3 territory)
| Transaction | Purpose | Status |
|------------|---------|--------|
| OB28 | FI Validations (posting rules) | ❌ Not extracted |
| OBBH | FI Substitutions (field derivation) | ❌ Not extracted |
| GGB0 | Define validations (cross-module) | ❌ Not extracted |
| GGB1 | Define substitutions (cross-module) | ❌ Not extracted |
| FMDERIVE | FM Derivation strategy | ❌ Not extracted |
| SM30/YTFM_* | UNESCO custom config tables | ✅ Extracted (6,434 rows) |

### Feeds
→ L2 (tells WHAT to extract — which tables, filters, periods)
→ L5 (module classification for transport objects)
→ L6 (business rules that Fiori apps must enforce)

### Consumes
← L2 (extracted data validates/contradicts domain assumptions)
← L4 (code extraction reveals hidden rules in enhancements and BADIs)

### Needs Next
- [ ] Extract OB28 validation rules via RFC
- [ ] Extract OBBH/GGB1 substitution rules
- [ ] Document FMDERIVE derivation strategy
- [ ] Investigate 4 orphan FONDS values (in FMIFIIT but not in funds table)
- [ ] Improve CTS module classification (reduce "General IMG" from 80%)

---

## L4: CODE & ENHANCEMENT EXTRACTION

### Purpose
Reverse-engineer ABAP source code, OData services, BSP apps, and composite enhancements from SAP.

### Skills
| Skill | What It Does |
|-------|-------------|
| `sap_adt_api` | Read/write/activate ABAP via ADT REST API (Eclipse/VS Code protocol) |
| `sap_reverse_engineering` | Extract OData logic and method source via RFC |
| `sap_enhancement_extraction` | Extract SE20 composite enhancements, classify by domain |

### Current State
- ✅ ADT client working against D01
- ✅ BSP extraction: ZHROFFBOARDING, YHR_OFFBOARDEMP (full source)
- ✅ Class extraction: 13 HCM classes (DPC/MPC pairs + shared)
- ✅ Enhancement extraction: 11 Fiori-impacting enhancements identified
- ⚠️ OData service $metadata not yet extracted
- ⚠️ Only HCM domain extracted — PSM, FM, FI code not started

### Lessons Learned
| Lesson | Session |
|--------|---------|
| ADT REST API is the preferred method over RFC hacks for source code | #001 |
| Enhancement code reveals business rules invisible in standard config | #003 |
| BSP app extraction gives both UI5 views AND controller logic | #001 |
| ABAP `FROM` clauses auto-detect table dependencies (brain edge READS_TABLE) | #001 |

### Feeds
→ L6 (reverse-engineered code → understand to rebuild)
→ L3 (extracted enhancements reveal hidden validation/substitution logic)

### Consumes
← L5 (transport analysis reveals WHAT changed → targets for extraction)
← L3 (domain context for understanding extracted code)

### Needs Next
- [ ] Extract OData $metadata for ZHRF_OFFBOARD_SRV
- [ ] Extract PSM/FM custom programs (Z*)
- [ ] Cross-reference enhancement registry with Fiori app architecture

---

## L5: TRANSPORT INTELLIGENCE

### Purpose
Analyze CTS transport orders to understand change history, risk, and configuration patterns.

### Skills
| Skill | What It Does |
|-------|-------------|
| `sap_transport_intelligence` | CTS order analysis — anatomy, OBJFUNC, module risk, classification |

### Current State
- ✅ 10-year transport history (7,745 orders, 108,290 objects)
- ✅ CTS dashboard built (cts_dashboard.html)
- ✅ Module classification partial (42 contributors, 4,168 TADIR entries)
- ✅ Config vs Workbench split: 1,420 customizing vs 965 workbench (2022-2024)
- ⚠️ 80% of config objects still in "General IMG" — needs better classification

### Lessons Learned
| Lesson | Session |
|--------|---------|
| TADIR must be queried with OBJECT type filter (same name = different object types) | #004 |
| SOTR/VARX use GUID keys — RFC_READ_TABLE fails with SAPSQL_DATA_LOSS | #004 |
| TABU/TDAT are content types, not structural objects | #004 |
| CTS is config-heavy at UNESCO (60% customizing) | #003 |
| Other/RELE entries inflate CTS activity count — must filter | #003 |

### Feeds
→ L4 (what changed in transports → what code to extract)
→ L3 (config transport content → domain/module classification)
→ L7 (CTS event logs for process mining)

### Consumes
← L1 (RFC to read E070/E071)
← L3 (module classification knowledge)

### Needs Next
- [ ] Improve module classification (reduce General IMG from 80%)
- [ ] Verify total_mods = distinct ORDER count
- [ ] Add SOTR/VARX special handling for TADIR lookup

---

## L6: FIORI APP DEVELOPMENT

### Purpose
Build replacement Fiori apps using React + UI5 Web Components, backed by SAP OData services.

### Skills
| Skill | What It Does |
|-------|-------------|
| `sap_fiori_tools` | VS Code Fiori Tools CLI, manifest.json, page layouts |
| `sap_fiori_extension_architecture` | Discover extension points, BSP/OData protection layers |
| `sap_segw` | Build OData services via SEGW in Web GUI |

### Current State
- ✅ Offboarding clone app scaffolded (React + Vite + UI5 Web Components)
- ✅ Playwright + Vitest testing setup documented
- ✅ Mock vs Live SAP testing pattern established (port 3000=mock, 3001=live)
- ✅ Live SAP proxy tested and working
- ⚠️ PA Mass Update app (PRAA* replacement) not started
- ⚠️ Benefits app not started

### Lessons Learned
| Lesson | Session |
|--------|---------|
| UI5 Web Components use Shadow DOM — need special Playwright selectors | Various |
| MemoryRouter required for Vitest (no browser history in test env) | Various |
| MSW mock handlers must match exact OData $format query params | Various |
| Vite proxy needs correct SAP backend URL with /sap/opu/odata prefix | Various |
| VPN DNS inheritance causes Playwright to fail resolving SAP hostnames | Various |

### Feeds
→ End users (working apps replace BDC/manual processes)

### Consumes
← L2 (data to display in apps)
← L3 (validation/substitution rules to enforce in app logic)
← L4 (reverse-engineered code to understand existing behavior)

### Needs Next
- [ ] Design PRAA* PA Mass Update replacement (PA30 infotype app)
- [ ] Identify target BAPIs (BAPI_EMPLOYEE_ENQUEUE + HR_MAINTAIN_MASTERDATA)
- [ ] Complete Offboarding clone with live data

---

## L7: PROCESS INTELLIGENCE

### Purpose
Signavio-style process mining using SAP event logs — discover, analyze, and
optimize business processes. **When data extraction is complete, this layer
discovers ALL possible end-to-end scenarios — which become test cases for L6.**

### Skills
| Skill | What It Does |
|-------|-------------|
| `parallel_html_build` | Build large HTML/JS tools in parallel parts, join into single file |

### Files & Build Pipeline
```
Location: Zagentexecution/
├── process-intelligence.html           297 KB  ← FINAL OUTPUT (open in browser)
├── _pi_part1_head.html                  34 KB  ← CSS design system
├── _pi_part2_body.html                  21 KB  ← HTML body (7 views)
├── _pi_part3_data.js                     9 KB  ← 6-domain data engine + algorithms
├── _pi_part3b_realdata.js              194 KB  ← Real CTS event log (embedded)
├── _pi_part4_map.js                      9 KB  ← D3.js process map
├── _pi_part5_ui.js                      30 KB  ← Full UI controller
├── _build_cts_eventlog.py                5 KB  ← CTS JSON → event log
├── _build_realdata_js.py                 3 KB  ← event log → embedded JS
└── _join_parts.py                        1 KB  ← 6 parts → final HTML

Rebuild: python _build_cts_eventlog.py → _build_realdata_js.py → _join_parts.py
```

### Current State
- ✅ process-intelligence.html built (297KB, single-file, last modified 2026-03-12)
- ✅ 6 process domains mapped (P2P, O2C, Incident, FM, HR, Travel)
- ✅ 15 SAP data sources registry
- ✅ Real CTS data embedded (2,579 transports, 2022-2024)
- ⚠️ Only CTS domain has real data — others are template/demo
- ⚠️ Other/RELE entries inflate CTS activity count
- ⚠️ Not yet verified in browser after Session #003 build

### Lessons Learned
| Lesson | Session |
|--------|---------|
| DFS topo sort + longest-path for process graph layout (BFS fails on cycles) | #003 |
| Parallel build pipeline proven: split → develop → join | #003 |
| Nested template literals with complex expressions fail silently in HTML | #003 |
| CTS is the richest event log source already available | #003 |

### The Testing Scenario Insight
**When data extraction is complete across all domains (FM, FI, MM, CO), process
discovery will reveal every end-to-end business path that actually exists in the
system.** These discovered paths become:
- **Functional test scenarios** for Fiori apps (L6)
- **Regression test baselines** for config changes
- **Edge case identification** — rare paths the data proves exist
- **Volume profiles** — how many documents flow through each path

```
L2 (all data) → L7 (process discovery) → L6 (test scenarios)
                                        → L3 (validation of rules completeness)
```

### Feeds
→ Decision makers (process optimization insights)
→ **L6 (discovered process paths = end-to-end test scenarios for apps)**
→ L3 (discovered paths validate whether business rules cover all real scenarios)

### Consumes
← L2 (event logs from extracted SAP data — CTS, FMIFIIT, BKPF/BSEG when ready)
← L5 (CTS change management data)

### Needs Next
- [ ] Open process-intelligence.html in browser and verify all 7 views
- [ ] Filter Other/RELE from CTS event log
- [ ] Add FM process domain using real FMIFIIT data (2.07M rows now available!)
- [ ] Design FM event log schema: fund lifecycle (create → budget → commit → actual → close)

---

## UNEXPLORED ELEMENTS (To Evolve)

Four capability areas partially touched but not yet systematized,
plus one critical migration challenge:

### Element A: INTERFACES (In/Out Connections)
**Question:** How is data flowing in and out of SAP — in any form?
| Interface Type | SAP Source | What We Know |
|---------------|-----------|-------------|
| RFC Destinations | RFCDES (SM59) | `bdc_full_inventory.py` queries RFCDES for MSSY/Y1 — found SZORME-RFC, SAS-RFC |
| IDocs | EDIDC/EDIDS | Not explored |
| Web Services/SOAP | SOAMANAGER | Not explored |
| Batch Input (external) | APQI (SM35) | Coupa → SAP via BDC PA30 sessions identified |
| File Interfaces | AL11/CG3Y | Not explored |
| RFC from external | RFCDES type 3 | SZORME-RFC (22 sessions), SAS-RFC (17 sessions) — unknown systems |
**Status:** Partially discovered via BDC analysis. No systematic extraction yet.

### Element B: SYSTEM LOGS & MONITORING
**Question:** What's breaking, what's unusual, what's the system health?
| Log Type | SAP Table/Transaction | Tool |
|----------|----------------------|------|
| Runtime Dumps | ST22/SNAP | `sap_system_monitor.py --report dumps` |
| Active Users | SM04/TH_USER_LIST | `sap_system_monitor.py --report users` |
| Transaction Usage | TSTC/STAD | `sap_system_monitor.py --report transactions` |
| Obsolete Programs | REPOSRC change dates | `sap_system_monitor.py --report obsolete` |
| Security Audit Log | SM20/RSAU_READ | Not explored |
| System Log | SM21/SYSLOG | Not explored |
| Change Documents | CDHDR/CDPOS | Not explored |
**Status:** `sap_system_monitor.py` has 7 reports. Some were run in Session #001. Output location needs verification.

### Element C: BACKGROUND JOBS
**Question:** What's running automatically, how often, and why?
| Aspect | SAP Table/Transaction | Tool |
|--------|----------------------|------|
| Job Definitions | TBTCO/TBTCP (SM37) | `sap_system_monitor.py --report jobs` |
| Job Steps | TBTCP | Partially in monitor |
| Job Scheduling | TBTCS (SM36) | Not explored |
| Job Chains | Process chains | Not explored |
| OBBATCH (109 sessions) | APQI | Identified in BDC analysis |
**Status:** `report_jobs()` exists in monitor. OBBATCH identified as automated BDC. Need systematic extraction of WHAT runs, WHEN, and WHY.

### Element D: WORKFLOWS
**Question:** What SAP Business Workflows exist? What triggers them? Who approves?
| Aspect | SAP Table/Transaction | Status |
|--------|----------------------|--------|
| Workflow Definitions | SWI5/SWDM | Not explored |
| Workflow Instances | SWI1/SWIA | Not explored |
| Workflow Tasks | PFTC/SWDD | Not explored |
| Workflow Events | SWE2 | Not explored |
**Status:** Not explored. Mentioned in process-intelligence.html as data source WF but no real data.

### Element E: BUSINESS PARTNER ARCHITECTURE (ECC → S/4HANA) ⭐ KEY CHALLENGE
**Question:** Where are we in the vendor/customer → Business Partner conversion?

**The BP Challenge:**
In ECC, vendors (LFA1/LFB1/LFBK) and customers (KNA1/KNB1/KNBK) are separate
master data objects. In S/4HANA, they MUST be unified under the **Business Partner**
(BUT000/BUT020/BUT021) concept. This is one of the most complex ECC→S/4 migrations.

**UNESCO's Current State:**
- ✅ **Real Estate domain** implemented (NEW domain to track!)
- ✅ Some client (customer) conversion to BP done
- ❌ Full vendor BP conversion still pending
- ❌ BP conversion strategy not fully documented

**SAP Tables Involved:**
| Table | Content | Direction |
|-------|---------|-----------|
| **BUT000** | BP header (name, type, category) | Target (S/4) |
| **BUT020** | BP addresses | Target (S/4) |
| **BUT021** | BP address usage | Target (S/4) |
| **BUT050/BUT051** | BP relationships | Target (S/4) |
| **BUT100** | BP roles (vendor, customer, employee...) | Target (S/4) |
| **BUPA_IDENT** | BP identification numbers | Target (S/4) |
| LFA1 | Vendor master (general) | Source (ECC) |
| LFB1 | Vendor master (company code) | Source (ECC) |
| LFBK | Vendor bank details | Source (ECC) |
| KNA1 | Customer master (general) | Source (ECC) |
| KNB1 | Customer master (company code) | Source (ECC) |
| KNBK | Customer bank details | Source (ECC) |
| **CVI_CUST_LINK** | Customer ↔ BP mapping | Bridge |
| **CVI_VEND_LINK** | Vendor ↔ BP mapping | Bridge |

**What We Need:**
1. Extract vendor master data (LFA1/LFB1/LFBK) to understand current state
2. Extract customer master data (KNA1/KNB1/KNBK)
3. Extract existing BP data (BUT000 etc.) to see what's already converted
4. Extract CVI link tables to see which vendors/customers already have BPs
5. Understand UNESCO's BP numbering strategy (internal vs external)
6. Map vendor/customer roles to BP role categories
7. Identify duplicates (same entity as both vendor AND customer)

**Status:** Partially implemented (Real Estate done, some clients). Needs deep
research on BP concept, full data extraction, and conversion strategy.

**New Domain:** Real Estate is a **new domain** (not in current domain structure).

### How These Connect to the 7 Layers
```
Interfaces (A)  → L2 (extract interface configs) → L7 (process discovery: who sends what)
Sys Logs (B)    → L2 (extract logs)  → L3 (validate system health) → Pattern Brain (anomalies)
Jobs (C)        → L2 (extract job list) → L7 (process: scheduled vs triggered) → L3 (what do jobs do)
Workflows (D)   → L2 (extract WF data)  → L7 (process: approval chains) → L6 (Fiori task inbox)
BP Arch (E)     → L2 (extract master data) → L3 (validate conversion rules) → L5 (track migration transports)
```

---

## Cross-Layer Connection Summary

```
L1 ──────────→ L2, L3, L4, L5, L6, L7  (connectivity enables all)
L2 ←──→ L3     (data validates rules ↔ rules tell what to extract)
L2 ────→ L7    (extracted tables → event logs for process discovery)
L3 ────→ L5    (domain knowledge classifies transport objects)
L3 ────→ L6    (business rules → app validation logic)
L4 ←──→ L3    (code reveals hidden rules ↔ domain context for code)
L4 ────→ L6    (reverse-engineered code → rebuild as modern apps)
L5 ────→ L4    (transport targets → code extraction priorities)
L5 ────→ L7    (CTS data → process mining event logs)
L7 ────→ L6    (discovered scenarios → end-to-end test cases)
L7 ────→ L3    (discovered paths → validate rule completeness)
```

**Future connections (from unexplored elements):**
```
Interfaces(A) → L7  (external system flows → process maps)
Sys Logs(B)   → L3  (dumps/errors → validate system health)
Jobs(C)       → L7  (scheduled processes → automated paths)
Workflows(D)  → L7  (approval chains → process variants)
Workflows(D)  → L6  (Fiori inbox/approval UIs)
```

**L3 is the most connected layer** — it feeds L2, L5, L6 and is fed by L2, L4, L7.
**L7 closes the loop** — process discovery from data (L2) generates test scenarios for apps (L6).
