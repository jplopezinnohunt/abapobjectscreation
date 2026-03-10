---
description: SAP Configuration & Master Data Discovery Strategy (Levels 3 & 4)
---

# SAP Configuration & Master Data Discovery Strategy

This document defines the systematic protocol for performing **SAP Configuration Audits** (Level 3) and **Master Data Pattern Discovery** (Level 4). This strategy ensures we extract business rules and structural "DNA" without exhaustive code analysis.

## 1. Entry Point: The Manifest Scan (Level 3)

Before reading any ABAP code, always scan for **Logic Manifests**. These are tables that drive the "Engine" of the application via configuration.

1.  **Fiori/Web Manifests**: Query `ZTHRFIOFORM_VISI` or `/UI2/*` tables to extract UI rules (visibility, mandatory fields).
2.  **Logic Groupings**: Query custom UNESCO tables (e.g., `YTFM_WRTTP_GR`).
3.  **Standard Screen Mods**: Query `T588M` (HCM) or `T5UT` (Unit Texts) for standard SAP configuration blocks.

### 3. Reporting as a Model Source
Since custom reports (`YFM1`, `YPS8`) reflect the intended business model:
1.  Analyze their selection screens for mandatory filters.
2.  Identify the `WRTTP` (Value Type) grouping logic in `YTFM_WRTTP_GR`.
3.  Use the report output columns as the specification for the React OData model.

## 2. Structural Audit: Master Data Patterns (Level 4)

Discover the "Structure of Truth" for system entities.

1.  **Date-Filtered Sampling**: **MANDATORY** - Always filter by `Date >= 2024-01-01` (`ERFDAT` or `ERDAT`) to avoid 20+ years of legacy noise.
2.  **Relationship Mapping**: Identify how IDs bridge across domains:
    *   `Project-PSPID` (10 chars) ↔ `Fund-FINCODE` (10 chars).
    *   `WBS-POSID` ↔ Hierarchy Prefix.
3.  **Metadata Enrichment**: Identify all `ZZ*` (UNESCO Custom) fields in master tables (`FMFINCODE`, `PROJ`, `PRPS`, `PA*`).
- **Level 4: Master Data Reconstruction**
    - Query **P01** for recently created Funds (`FMFINCODE`) and Fund Centers (`FMFCTR`).
    - **Filter**: `ERFDAT >= '20240101'` to capture current patterns.
    - **Custom Table Scan**: Identify `YTFM_*` tables (e.g., `YTFM_FUND_CPL`, `YTFM_INT_PROJS`) that bridge entities.
    - **Pattern Discovery**: Link Fund IDs to Project Definition IDs (`PSPID`).

## 3. Remote RFC Read Protocol (D01 ↔ P01)

If the Development system (D01) lacks representative data for a specific module:

1.  **System Selection**: Use `sap_utils.py` with `system_id='P01'`.
2.  **Target Tables**: Focus on T-tables (Configuration) and Master Data only. 
3.  **Goal**: Identify "Golden Patterns" from the Production environment to ensure the React clone matches the final business reality.

## 4. Documentation & Brain Map Update

1.  **Register Tables**: Add any newly discovered T-tables to the **[SAP Configuration Reference](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/sap_configuration_reference.md)**.
2.  **Map Connections**: Update the **[Entity Brain Map](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/entity_brain_map.md)** to include the discovered master data links.
3.  **Initial Analysis**: Save findings into the corresponding `knowledge/domains/[MODULE]` folder.

---
> [!IMPORTANT]
> **Level 5 (Transactional Data)** should only be performed once Levels 3 and 4 are stabilized for a given module. We are currently focusing on the **Definition** and **Configuration** of the system.
