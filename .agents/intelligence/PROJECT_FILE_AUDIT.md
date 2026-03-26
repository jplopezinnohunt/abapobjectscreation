# UNESCO SAP Intelligence — Complete File Audit
> 100% inventory of every file, every directory, every tool
> Purpose: Ensure nothing valuable was missed in the architecture analysis
> Created: 2026-03-15 (Session #005b)

---

## PROJECT ROOT (`abapobjectscreation/`)

### Intelligence & Documentation (✅ Well-tracked)
| File | Layer | Status | Notes |
|------|-------|--------|-------|
| `.agents/intelligence/` | Meta | ✅ Active | 12 files: SESSION_LOG, PROJECT_MEMORY, PMO_BRAIN, CAPABILITY_ARCHITECTURE, AGENT_ARCHITECTURE, BRAIN_ARCHITECTURE, sap_brain.json, sap_knowledge_graph.html, sap_companion_intelligence.md, vscode_sap_plugin_intelligence.md, README.md |
| `.agents/skills/` | All | ✅ Active | 18 SKILL.md files across L1-L7 |
| `.agents/workflows/` | Meta | ✅ Active | 6 workflows: session_start, session_retro, segw_interview, sap_configuration_strategy, hybrid_orchestration, fiori_app_reverse_engineering |

### Legacy Root Docs ⚠️ PARTIALLY MISSED
| File | Size | Status | Notes |
|------|------|--------|-------|
| `CLAUDE.md` | 9 KB | ⚠️ **OUTDATED** | Original agent instructions from Phase 1 (WebGUI era). Superseded by `.agents/intelligence/` but still referenced by Claude sessions |
| `ROADMAP.md` | 10 KB | ⚠️ **OUTDATED** | Original 10-phase roadmap from 2026-03-04. Now superseded by CAPABILITY_ARCHITECTURE + PMO_BRAIN |
| `RETROSPECTIVE.md` | 7 KB | ⚠️ **VALUABLE** | 103-script Gemini experiment retrospective. Contains hard-won WebGUI lessons. Should be preserved as L1 knowledge |

> **ACTION**: CLAUDE.md and ROADMAP.md should be updated or archived. RETROSPECTIVE.md lessons should feed into `sap_webgui` SKILL.md.

### Root-Level Extraction Scripts ⚠️ MISSED IN ANALYSIS
| File | Size | Status | What It Does |
|------|------|--------|-------------|
| `p01_massive_extractor.py` | 7 KB | ⚠️ **Not tracked** | Mass extraction from P01 — predecessor of current extraction scripts |
| `p01_master_data_sync.py` (v1-v6) | 5-8 KB each | ⚠️ **6 versions!** | Master data sync scripts — evolution trail shows ≥6 iterations |
| `p01_anchor_counts.py` | 4 KB | ⚠️ **Not tracked** | Row count anchors for data verification |
| `p01_proj_prps_sync.py` | 4 KB | ⚠️ **Not tracked** | PS Project/WBS data extraction |
| `p01_ps_transaction_sync.py` | 6 KB | ⚠️ **Not tracked** | PS Transaction data sync |
| `p01_ps_transaction_anchor.py` | 4 KB | ⚠️ **Not tracked** | PS anchor counts |
| `p01_raw_puller.py` | 5 KB | ⚠️ **Not tracked** | Raw table data puller |
| `p01_totals_sync.py` | 5 KB | ⚠️ **Not tracked** | Totals table sync |
| `p01_derivation_sync_task.py` | 5 KB | ⚠️ **Not tracked** | Derivation rules sync |
| `download_cockpit*.py` | 1-2 KB × 5 | ⚠️ **Not tracked** | Cockpit data download variants |
| `download_rpy_derivation.py` | 2 KB | ⚠️ **Not tracked** | RPY derivation rules download |
| `check_db_stats.py` | 1 KB | ⚠️ | SQLite stats checker |
| `check_v3_results.py` | 1 KB | ⚠️ | V3 verification |
| `verify_counts.py` | 3 KB | ⚠️ | Count verification |
| `read_yps8_class.py` | 2 KB | ⚠️ | YPS8 class reader |
| `debug_connection.py` | 1 KB | ⚠️ | Connection debugger |

> **ACTION**: These are the **original L2 extraction layer** — v1 through v6 shows evolution. Extract the protocol patterns into `sap_data_extraction` SKILL.md. Many can be archived/cleaned up but patterns are valuable.

### Root Data Files
| File | Size | Notes |
|------|------|-------|
| `dev_rfc.log` | 66 MB | ❌ Should be gitignored — massive RFC log |
| `massive_extraction.log` | 83 KB | Historical extraction log |
| `counts.log` | 10 KB | Historical row counts |
| Various `sync_*.log` | 1-21 KB | FMAVCT/FMBDT sync logs — **valuable**: shows which PSM tables were extracted |
| `entity_config_example.json` | 3 KB | Entity config schema — SEGW related |
| `z_crp_srv_config.json` | 8 KB | CRP service config |

---

## ZAGENTEXECUTION/ (Main Agent Workspace)

### HTML Tools (✅ + 1 missed)
| Tool | Size | Layer | Status |
|------|------|-------|--------|
| `process-intelligence.html` | 297 KB | L7 | ✅ Tracked |
| `mcp-backend-server-python/cts_dashboard.html` | 2.3 MB | L5 | ✅ Tracked |
| `mcp-backend-server-python/sap_taxonomy_companion.html` | 39 KB | L4 | ⚠️ **NOT TRACKED** — SAP object taxonomy viewer |
| `mcp-backend-server-python/epiuse_companion.html` | 31 KB | L5 | ⚠️ **NOT TRACKED** — EPIUSE data migration analysis tool |

> **ACTION**: sap_taxonomy_companion.html and epiuse_companion.html need to be added to the architecture. Taxonomy companion helps L4 (code understanding), EPIUSE helps L5/data migration.

### Python Scripts by Category

#### Core Infrastructure (L1)
| Script | Size | Purpose |
|--------|------|---------|
| `sap_system_monitor.py` | 32 KB | 7 system monitoring reports |
| `sap_brain.py` | 25 KB | Knowledge graph builder (55 nodes, 66 edges) |
| `sap_adt_client.py` | 33 KB | ADT REST API client |
| `sap_mcp_server.py` | 7 KB | SAP MCP server |
| `sap_utils.py` | 1 KB | Shared utilities |
| `test_sap_connection.py` | 2 KB | Connection tester |
| `extract_sso_and_test_adt.py` | 15 KB | SSO + ADT testing |

#### Data Extraction (L2)
| Script | Size | Purpose | Status |
|--------|------|---------|--------|
| `extract_fmifiit_full.py` | 16 KB | FMIFIIT extraction | ✅ Used |
| `extract_bkpf_bseg_parallel.py` | 14 KB | FI doc headers + line items | ⏳ Ready to run |
| `extract_ekko_ekpo_parallel.py` | 18 KB | MM purchase orders | ⏳ Ready to run |
| `run_overnight_extraction.py` | 13 KB | Orchestrator for overnight batch | ⏳ Ready |
| `extraction_status.py` | 18 KB | Status reporter | ✅ Used |
| `query_table.py` | 3 KB | Generic table query | ✅ Used |
| `read_table_generic.py` | 4 KB | Generic table reader | ✅ Used |
| `batch_tadir_dd02t.py` | 7 KB | TADIR + DD02T batch enrichment | ✅ Used |
| `read_t001.py` | 1 KB | Company code master | ✅ Used |

#### CTS / Transport Intelligence (L5) — 26 scripts!
| Script | Size | Purpose |
|--------|------|---------|
| `cts_extract.py` | 27 KB | Main CTS extractor |
| `cts_extract_batch.py` | 11 KB | Year-batch extraction |
| `cts_analyze.py` | 17 KB | Transport analysis |
| `cts_full_classification.py` | 16 KB | Module classification |
| `cts_object_classification.py` | 9 KB | Object type classification |
| `cts_domain_year_type.py` | 11 KB | Year/domain breakdown |
| `cts_package_breakdown.py` | 7 KB | Package analysis |
| `cts_tadir_enrichment.py` | 8 KB | TADIR enrichment |
| `cts_tadir_fullscan.py` | 7 KB | Full TADIR scan |
| `cts_unique_analysis.py` | 15 KB | Unique object analysis |
| `cts_true_inventory.py` | 6 KB | True inventory builder |
| `cts_upgrade_detect.py` | 7 KB | Upgrade detection |
| `cts_user_year_breakdown.py` | 5 KB | User contribution analysis |
| `cts_rele_analysis.py` | 7 KB | Release analysis |
| `cts_epiuse_analysis.py` | 3 KB | EPIUSE analysis |
| `cts_quick_stats.py` | 2 KB | Quick statistics |
| `cts_probe.py` | 7 KB | CTS probing |
| `cts_probe_other.py` | 3 KB | Other probe |
| `gen_dashboard.py` | 38 KB | Dashboard generator |
| `cts_dashboard_data.py` | 6 KB | Dashboard data builder |
| `cts_package_config_data.py` | 8 KB | Package config |
| `improve_module_classification.py` | 11 KB | Module classification improver |
| `enrich_config_detail.py` | 6 KB | Config detail enrichment |
| `gen_config_detail.py` | 3 KB | Config detail generator |
| Various `patch_*.py` | 1-13 KB × 12 | Dashboard patches |

> The CTS pipeline is the **most mature L5 capability** — 26 scripts + 26 JSON data files + 2.3MB HTML dashboard.

#### Code Extraction & Deployment (L4) — ~50+ scripts
| Category | Scripts | Purpose |
|----------|---------|---------|
| BSP extraction | `extract_bsp_*.py`, `fetch_bsp*.py` | BSP content extraction |
| Enhancement extraction | `extract_composite_enhancements.py` | 11 composite enhancements |
| Class operations | `create_class_*.py`, `deploy_crp_*.py` | Class creation/deployment |
| Method operations | `extract_methods.py`, `download_*_methods.py` | Method code extraction |
| Include handling | `discover_dpc_includes.py`, `find_cm_includes.py` | Include discovery |
| CCIMP writing | `write_ccimp_*.py` × 6, `ccimp_bridge_writer.py` | CCIMP code writing |
| Code reconstruction | `complete_reconstruction.py`, `reconstruct_*.py` | Code reconstruction |
| Deployment | `deploy_*.py` × 4, `activate_and_deploy.py` | SAP deployment |
| Verification | `verify_*.py` × 6, `final_*.py` × 5 | Deployment verification |

#### BDC Analysis (L7/L1)
| Script | Size | Purpose |
|--------|------|---------|
| `bdc_full_inventory.py` | 24 KB | Full BDC session inventory + RFC destinations |
| `bdc_deep_analysis.py` | 35 KB | Deep field-level BDC analysis |
| `bdc_schema_probe.py` | 7 KB | BDC schema detection |
| `decode_numeric_bdc.py` | 15 KB | Numeric BDC field decoder |

### ABAP Source Code Files ⚠️ VALUABLE & PARTIALLY MISSED
| File | Size | Layer | Notes |
|------|------|-------|-------|
| `YRGGBS00_SOURCE.txt` | 105 KB | **L3!** | 🔴 **CRITICAL**: This is the substitution exit source code! Contains UNESCO's custom derivation logic |
| `YFI_ACCOUNT_SUBSTITUTION.txt` | 1 KB | L3 | FI account substitution definition |
| `YCL_FI_ACCOUNT_SUBST_BL_*.txt` × 5 | 1-11 KB | L3 | FI account substitution class — all methods and includes |
| `YCL_FI_ACCOUNT_SUBST_READ_*.txt` × 2 | 68B-1KB | L3 | FI account substitution reader |
| `YCL_YPS8_BCS_BL_*.txt` × 4 | 86B-13KB | L3 | YPS8 BCS class — PSM budget control |
| `YPS8_ALL_METHODS.txt` | 76 KB | L3 | 🔴 **All YPS8 methods** — PSM budget control logic |
| `YPS8_BCS_V2*.txt` × 3 | 0.4-3 KB | L3 | V2 variants |

> **ACTION**: The YRGGBS00 (105KB substitution exit) and YPS8_ALL_METHODS (76KB budget control) are **GOLD for L3**. These should be:1. Indexed in Vector Brain2. Added as nodes in Graph Brain3. Analyzed for validation/substitution rules4. Cross-referenced with FMIFIIT data patterns

### CTS Data Files (26 JSON files, ~150 MB total)
| File | Size | Content |
|------|------|---------|
| `cts_10yr_raw.json` | 32 MB | 10 years of raw transport data |
| `cts_10yr_analyzed.json` | 32 MB | Analyzed transport data |
| `cts_10yr_enriched.json` | 20 MB | Enriched with TADIR |
| `cts_batch_20XX.json` × 10 | 2-5 MB each | Per-year batches |
| `cts_config_detail.json` | 2.3 MB | Config detail for dashboard |
| `cts_sap_packages.json` | 169 KB | SAP package descriptions |
| `cts_unique_objects.json` | 28 KB | Unique objects inventory |
| `tadir_enrichment_checkpoint.json` | 2 MB | TADIR cache |
| `tadir_cache.sqlite` | 375 KB | TADIR SQLite cache |

### SAP MCP Server ⚠️ NOT IN ARCHITECTURE
| File | Size | Purpose |
|------|------|---------|
| `SAP_MCP/sap_server.py` | 5 KB | MCP server exposing SAP RFC |
| `SAP_MCP/sap_client.py` | 2 KB | MCP client for testing |
| `SAP_MCP/config.json` | 174 B | Server config |
| `SAP_MCP/simple_test.py` | 2 KB | Simple test |

> **ACTION**: This is a **half-finished MCP server for SAP RFC**. Could become a real L1 tool — expose RFC_READ_TABLE, BAPI_*, etc. as MCP tools.

### MDK MCP Server ⚠️ NOT IN ARCHITECTURE
| Directory | Size | Purpose |
|-----------|------|---------|
| `mdk-mcp-server/` | 2521 files | SAP Mobile Development Kit MCP server (TypeScript) |

> **ACTION**: This is a cloned open-source SAP MCP server. Could be useful reference for building our own.

### SAP Skills (Open Source) ⚠️ NOT IN ARCHITECTURE
| Directory | Files | Purpose |
|-----------|-------|---------|
| `sap-skills/` (and `skills/extracted_open_source_skills/`) | 766+617 files | Open-source SAP skills for BTP, Datasphere, SAC, etc. |

> **ACTION**: These are reference skills from the community. Not directly used but good reference for our skill design.

---

## EXTRACTED CODE (`extracted_code/`)

30 ABAP class directories containing **812 files** of extracted source code.

Key classes:
| Class | Files | Domain | Purpose |
|-------|-------|--------|---------|
| `CL_HCMFAB_MYPERSONALDA_MPC` | 179 | HCM | My Personal Data model |
| `ZCL_HCMFAB_MYPERSONALDATA` | 115 | HCM | Custom personal data DPC |
| `ZCL_HCMFAB_B_MYFAMILYMEMBERS` | 113 | HCM | Family members DPC |
| `CL_HCMFAB_BEN_ENROLLME_DPC_EXT` | 59 | HCM | Benefits enrollment |
| `CL_HCMFAB_COMMON_DPC_EXT` | 71 | HCM | Common HCM DPC |
| `UNESCO_CUSTOM_LOGIC` | 50 | HCM | UNESCO custom classes |
| `ZCL_ZHRF_OFFBOARD_DPC_EXT` | 22 | HCM | Offboarding OData DPC |

> All HCM domain. No PSM/FM/FI code extracted yet. This is a gap for L4.

---

## EXTRACTED SAP (`extracted_sap/`)

332 files across 3 domains. **HCM only**, structured by:
- `HCM/Fiori_Apps/` → 332 files (Fiori app analysis documents)
- `HCM/Interfaces/` → empty
- `HCM/Reports/` → empty
- `PSM/` → exists but empty
- `_shared/` → exists but empty

> **GAP**: No PSM or FI extracted_sap code. This needs to happen with L4 extraction.

---

## KNOWLEDGE (`knowledge/`)

51 files across 7 domain directories.

| Domain | Files | Key Contents |
|--------|-------|-------------|
| `PSM/` | 22 | Extensions (11), Fiori Apps (3), Reports (2), FM-PS bridge, initial analysis |
| `HCM/` | 8 | Benefits, Fiori Apps, Infotypes, Payroll |
| `FI/` | 1 | FI enhancements analysis |
| `RE-FX/` | 1 | RE-FX enhancements analysis — **confirms Real Estate domain exists** |
| `PS/` | 1 | PS domain |
| `Procurement/` | 1 | Procurement domain |
| `Output/` | 1 | Output domain |

Plus root-level knowledge files:
| File | Size | Purpose |
|------|------|---------|
| `entity_brain_map.md` | 25 KB | Entity relationship map |
| `code_analysis_control_matrix.md` | 5 KB | Analysis control matrix |
| `sap_custom_enhancement_registry.md` | 14 KB | 11 composite enhancements |
| `knowledge_base_index.md` | 3 KB | Knowledge base index |
| `sap_configuration_reference.md` | 4 KB | Config reference |
| `fiori_reverse_engineering_strategy.md` | 3 KB | Fiori RE strategy |
| `level_4_master_data_skill.md` | 2 KB | Master data skill |
| `pmo_tracker.md` | 7 KB | Old PMO tracker (⚠️ superseded by PMO_BRAIN.md) |

---

## DATA EXTRACTION (`sap_data_extraction/`)

| File/Dir | Purpose |
|----------|---------|
| `scripts/` | 7 extraction scripts (FMIFIIT, BKPF/BSEG, EKKO/EKPO, overnight runner) |
| `reports/` | 31 files including CTS data, 3 status reports, 2 HTML tools, 26 CTS JSONs |
| `sqlite/` | **p01_gold_master_data.db (503 MB)** + p01_master_data_v2.db (6 MB legacy) |
| `LIVE_BRAIN.md` | Current data intelligence |
| `SQLITE_CONTENTS.md` | Database schema documentation |

---

## ITEMS MISSED OR UNDERVALUED IN ARCHITECTURE

| # | Item | Location | Importance | Action |
|---|------|----------|-----------|--------|
| 0a | **doc_reference.txt** (28KB) | mcp-backend-server-python/ | 🔴 **CRITICAL SEED** | Transport anatomy (603 paragraphs) — OBJFUNC, PGMID/OBJECT taxonomy, AI agent design patterns. Must become LIVING knowledge in transport skill. |
| 0b | **doc_supplement.txt** (31KB) | mcp-backend-server-python/ | 🔴 **CRITICAL SEED** | Module-specific transport risks (423 paragraphs) — HR payroll schemas, PSM FMDERIVE, PS master data traps, Bank DMEE, FI T001B. SEED for module risk matrix. |
| 1 | **YRGGBS00_SOURCE.txt** (105KB) | mcp-backend-server-python/ | 🔴 **CRITICAL** | Substitution exit source code — THE L3 brain. Must index in Vector Brain. |
| 2 | **YPS8_ALL_METHODS.txt** (76KB) | mcp-backend-server-python/ | 🔴 **CRITICAL** | PSM budget control logic — key L3 knowledge |
| 3 | **YCL_FI_ACCOUNT_SUBST** files | mcp-backend-server-python/ | 🟡 High | FI substitution class — L3 validation rules |
| 4 | **epiuse_companion.html** (31KB) | mcp-backend-server-python/ | 🟡 High | EPIUSE data migration tool — L5/data migration |
| 5 | **sap_taxonomy_companion.html** (39KB) | mcp-backend-server-python/ | 🟡 Medium | SAP object taxonomy — L4 code understanding |
| 6 | **SAP_MCP/ server** | Zagentexecution/ | 🟡 Medium | Half-built MCP server for SAP RFC — could be key L1 tool |
| 7 | **Root p01_*.py scripts** (16 files) | Project root | 🟡 Medium | Original extraction layer — patterns valuable for SKILL |
| 8 | **Duplicate scripts** | mcp-backend-server-python/ vs sap_data_extraction/ | ⚠️ Confusion risk | extract_bkpf, extract_ekko exist in BOTH locations |
| 9 | **ROADMAP.md** (10KB) | Project root | ⚠️ Outdated | Original 10-phase roadmap — superseded by CAPABILITY_ARCHITECTURE |
| 10 | **CLAUDE.md** (9KB) | Project root | ⚠️ Outdated | Original agent instructions — superseded by .agents/ |
| 11 | **pmo_tracker.md** (7KB) | knowledge/ | ⚠️ Outdated | Superseded by PMO_BRAIN.md |
| 12 | **RE-FX domain** | knowledge/domains/RE-FX/ | ✅ Confirmed | Real Estate domain EXISTS — confirms BP architecture Element E |
| 13 | **PSM/EXTENSIONS** (11 files) | knowledge/domains/PSM/ | ✅ Tracked | 11 enhancement analyses |

---

## RECOMMENDATIONS FOR NEXT SESSION

### 1. Immediate (Brain Redesign Prep)
- [ ] Move YRGGBS00_SOURCE.txt and YPS8_ALL_METHODS.txt to `extracted_sap/PSM/` domain
- [ ] Index these in Vector Brain (ChromaDB) as first embeddings
- [ ] Resolve duplicate scripts (mcp-backend-server-python/ vs sap_data_extraction/)
- [ ] Archive or update ROADMAP.md, CLAUDE.md, pmo_tracker.md

### 2. Architecture Updates
- [ ] Add sap_taxonomy_companion.html to CAPABILITY_ARCHITECTURE (L4)
- [ ] Add epiuse_companion.html to CAPABILITY_ARCHITECTURE (L5)
- [ ] Add SAP_MCP server as potential L1 tool
- [ ] Document the root-level p01_*.py scripts in extraction SKILL

### 3. Data Extraction Priorities
- [ ] Run extract_bkpf_bseg_parallel.py (FI docs — ready in sap_data_extraction/scripts/)
- [ ] Run extract_ekko_ekpo_parallel.py (MM POs — ready)
- [ ] Extract PSM source code to fill extracted_sap/PSM/ gap

### 4. Knowledge Gaps
- [ ] extracted_sap/PSM/ is EMPTY — needs L4 code extraction
- [ ] extracted_sap/HCM/Interfaces/ is EMPTY — Element A not started
- [ ] extracted_sap/HCM/Reports/ is EMPTY — L3 report analysis not started
- [ ] No FI domain in extracted_sap/ — needs adding

---

**Total Project Size:**
- **Scripts:** ~300+ Python scripts
- **ABAP Source:** 812+ extracted files (30 classes)
- **Data:** 503 MB SQLite + ~150 MB CTS JSON
- **HTML Tools:** 4 (process-intelligence, cts_dashboard, sap_taxonomy, epiuse_companion)
- **Skills:** 18 SKILL.md files
- **Knowledge:** 51 files across 7 domains
- **Architecture Docs:** 6 files in .agents/intelligence/

**Nothing is lost. Everything has value. The key missed items are the YRGGBS00 substitution exit (105KB of L3 gold) and the YPS8 budget control methods (76KB).**
