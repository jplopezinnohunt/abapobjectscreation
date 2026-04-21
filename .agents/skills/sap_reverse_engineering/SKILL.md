---
name: SAP Backend Reverse Engineering (Code Extraction)
description: Protocol for extracting OData service logic and ABAP method source code directly from SAP via RFC.
domains:
  functional: [*]
  module: [CUSTOM]
  process: []
---

# SAP Backend Reverse Engineering: Python RFC Protocol (Gold Truth)

This protocol defines the **Reverse Engineering via Python RFC Protocol**. It mandates that all Fiori/OData analysis must be performed directly against the SAP Backend using Python RFC automation. 

> [!CAUTION]
> **ABSOLUTE PROHIBITION**: NEVER use the browser for discovering the technical structure of an SAP app. Browsers mislead by showing cached or superficial UI5 metadata. The **Gold Truth** (Auth logic, Data Persistence, Hidden Fields, UNESCO extensions) is only accessible via direct RFC calls to ABAP Logic and Tables.

## 1. Tactical Objective
The goal is to extract the complete technical DNA of an SAP application (OData, Business Logic, DB Schema, Workflows) using the **Python RFC Toolset** to enable high-fidelity React cloning without ever needing a browser session.

## 2. The Python RFC Toolset
Analysis MUST be performed using these specific tools in `Zagentexecution\mcp-backend-server-python\`:
- `query_table.py`: Deep table scanning (TADIR, /UI2/*, T5ASR*, PA*).
- `find_service.py`: OData discovery when metadata is restricted.
- `fetch_bsp.py` / `fetch_bsp_content.py`: Extracting `manifest.json` and UI source from the BSP repo.
- `extract_methods.py`: Bulk extraction of ABAP source code (DPC_EXT, BAdIs, Feeder Classes).
- `read_report.py`: Reading main programs and includes.
- `TRDIR Scan`: If a class `ZCL_FOO` or `YCL_BAR` is not found, query `TRDIR` where `NAME` LIKE `YCL_BAR===============*` to find the Method Includes (`CM***`) or Class Pool (`CP`), then use `read_report.py` or `RPY_PROGRAM_READ`.

## 3. HCM & UNESCO Specialized Protocol (The Refined Standard)

Based on the successful analysis of the **Address Management**, **Offboarding**, and **Personal Management** apps, the following specialized protocol MUST be followed for UNESCO HCM applications:

### Phase A: Entry Point Discovery (The Entry Scan)
- **TADIR Lookup**: Locate `WAPA` (BSP) and `IWSV` (OData) starting with `Z*` or `Y*`.
- **Launchpad Mapping**: Resolve the Semantic Object to its technical BSP name via `/UI2/PB_C_PAGEM`.
- **BSP Deep-Scan**: Use `fetch_bsp.py` to extract `manifest.json`. Identify if the app is a standard extension (`HCMFAB_*`) or a pure custom UNESCO build.

### Phase B: Architecture & Extension Mapping
- **Hierarchy Mapping**: Determine the DPC Inheritance (Standard -> UNESCO `DPC_EXT`). 
- **Gateway Delegate Scan**: Look for specialized logic classes (Feeders/Reactors) like `ZCL_HR_FIORI_OFFBOARDING_REQ`.
- **BAdI Intersection**: 
    - Identify the domain BAdI (e.g., `HCMFAB_B_MYPERSONALDATA`, `HCMFAB_B_MYFAMILYMEMBERS`).
    - Extract the implementing class (e.g., `ZCL_HCMFAB_B_MYFAMILYMEMBERS`).
    - Focus on `ENRICH_*` methods to find hidden UNESCO-specific fields (e.g., UN Regions, Wage Type texts).

### Phase C: Process & Workflow (The "Parking" Scan)
- **ASR Scenario Discovery**: Query `T5ASRSCENARIOS` to find associated UNESCO processes (e.g., `ZHR_BIRTH_CHILD`).
- **Data Staging (Parking Pattern)**: Identify if data is held in ASR buffers or Custom Tables (e.g., `zthrfiori_hreq`) before final PA update.
- **On Behalf Of Check**: Always check BAdI `HCMFAB_B_COMMON` or `CHECK_ON_BEHALF` methods for manager/admin delegation logic.

### Phase D: Persistence & UI Logic
- **Custom Persistence**: Search for `zthrfiori*` tables which often store state independently of Infotypes.
- **Visibility Engine**: Extract logic from methods like `check_wf_step_visibility` to understand dynamic UI behavior (Tabs/Buttons/Fields).
- **Field Blueprint**: Map UI fields to `OData Property` -> `ABAP Struct` -> `DB Table`.

### Phase E: Business Configuration & rule Extraction (The "Engine" Scan)
- **UI Logic Manifests**: Query tables like `ZTHRFIOFORM_VISI` or `T588M`. These tables often drive field visibility, mandatory status, and technical field mapping without changing code.
- **Domain Configuration (T-Tables)**: 
    - **HCM**: `T500P` (Personnel Areas), `T503K` (Employee Subgroups), `T529T` (Action Texts).
    - **FM/FI**: `T001` (Company Codes), `T004` (Chart of Accounts), `T5UT` (Unit Texts).
- **Status & Workflow Maps**: Extract status transition rules from custom tables (e.g., `ZTHRFIORI_BREQ` status codes 00-09).
- **UNESCO Special Filters**: Check `YTFM_WRTTP_GR` and `YTFM_OUTPUT` for RBB (Results Based Budgeting) logic.
- **The "Safety Valve" (Bypass) Scan**: Always check for a check against table **`YXUSER`**. In UNESCO, this table contains a list of IDs (XTYPE='FM' or 'FRTL') that bypass all standard validations and hardware tolerance caps.
- **Fiscal Gate Scan**: Query table **`YFMXCHKP`**. This is a custom UNESCO gate that blocks FM postings independently of FI periods (`OB52`). If `ACTIV = 'X'`, the period is locked.

## 4. The Technical Specification Standard (Fields & Sources)

Every analysis MUST culminate in a technical specification that mirrors the **"Field & Screen Connectivity Matrix"**. This is the only way to ensure the React clone is 100% accurate.

### Mandated Connectivity Matrix Format
For every screen and tab, you MUST document:

| UI Element / Field | OData Property | Backend Source (Gold Truth) | logic / BAdI Trace |
| :--- | :--- | :--- | :--- |
| `[Field Label]` | `[Property_Name]` | `[Table]-[Field]` OR `[Method]` | [Conditions for visibility/editability] |

### Mapping Protocol:
1. **The Origin**: Start with the `MPC_EXT` class to find the technical property names.
2. **The Logic**: Scan the `ENRICH_*` methods in the BAdI (e.g., `ZCL_HCMFAB_B_MYPERSONALDATA`) to see how properties are populated.
3. **The Persistence**: Trace the `DPC_EXT` CRUD-Q methods to find the `SELECT` or `UPDATE` statements targeting `PA*` or `Z*` tables.
4. **The visibility**: Extract logic from `check_wf_step_visibility` or `T588M` table reads to determine when fields are hidden/shown.

## 5. Knowledge Synthesis (The Blueprint)
- **Artifact Creation**: Generate a full **[Fiori App Analysis Blueprint](file:///C:/Users/jp_lopez/.gemini/antigravity/brain/b6d3c018-79ef-48e4-abb5-37af2ca21052/fiori_app_analysis_blueprint.md)**.
- **Field Connectivity Map**: Populate Section 5 of the Blueprint with the matrix defined above.
- **Brain Map Update**: Add the new app, its services, and its persistence links to `entity_brain_map.md`.
- **Final Verification**: Browser use is permitted **ONLY** for final visual confirmation that the React model matches the live UI.

---
*Note: This skill relies on RFC_READ_TABLE and SIW_RFC_READ_REPORT access.*
