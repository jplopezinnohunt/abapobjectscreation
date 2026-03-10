---
description: Fiori App Reverse Engineering Protocol
---

# Fiori App Reverse Engineering Protocol (Python RFC-Only)

This workflow defines the systematic procedure for performing a complete technical reconstruction of an SAP Fiori App using the **Python RFC Protocol**. All discovery and extraction must happen via RFC to ensure data integrity and bypass restricted UI metadata.

## 1. Entry Point Discovery (Launchpad & BSP)
1. **Semantic Object Resolution**: Use `query_table.py` to search `/UI2/PB_C_PAGEM` or `/UI2/TM_CONFIG` using the `Semantic Object-Action` pair.
2. **BSP Identification**: Resolve the Semantic Object to its technical `WAPA` (BSP) name.
3. **BSP manifest Extraction**: Run `fetch_bsp.py` and `fetch_bsp_content.py` on the technical name to extract the `manifest.json`.
4. **Service Mapping**: Identify all OData services (`IWSV` objects) and model names from the manifest.

## 2. Gateway & SEGW Analysis (The "Gold" Layer)
1. **Class Discovery**: Use `query_table.py` on `TADIR` to find the `DPC_EXT` and `MPC_EXT` classes for each identified OData service.
2. **Hierarchy Mapping**: Determine the inheritance path (Standard -> UNESCO Extension).
3. **Redefinition Scanning**: Check table `SEOREDEF` to see which standard methods have been customized by UNESCO.

## 3. ABAP Logic Extraction (Deep Technical Audit)
1. **Source Code Capture**: Run `extract_methods.py` on the `DPC_EXT` class to pull all CRUD-Q logic.
2. **BAdI Delegation Scan**: Identify the specialized domain BAdIs (e.g., `HCMFAB_B_MYPERSONALDATA`) and extract the implementing `Z*` class methods (`ENRICH_*`).
3. **Feeder Class Analysis**: For HCM apps, identify if a "Feeder" class (e.g., `ZCL_HR_FIORI_OFFBOARDING_REQ`) is managing the business logic independently of the DPC.

## 4. Rule & Configuration Extraction (The "Engine" Scan)
1. **Visibility Manifest**: Query `ZTHRFIOFORM_VISI` using the BSP name or OData service to extract dynamic field rules.
2. **HCM Field Config**: Query `T588M` to find screen modification rules for specific infotypes.
3. **Workflow Status Map**: Query custom status tables (e.g., `ZTHRFIORI_BREQ`) to document the state machine of the application.
4. **Domain Constants**: Extract key T-table records (T500P, T001) that define the app's structural context.

## 5. Continuity & Persistence Mapping
1. **The Parking Pattern (ASR/Custom)**: Search for data staging logic in `T5ASRSCENARIOS` or custom `Z*` tables (`zthrfiori*`). Identify the "Draft" vs. "Active" state transitions.
2. **Field Extension Audit**: Identify all `ZZ*` (UNESCO custom) fields and track their conversion logic in Conversion Classes.
3. **On Behalf Of Logic**: Verify authorization checks in BAdI `HCMFAB_B_COMMON` or specific logic methods to support Manager/Admin roles.

## 6. Technical Blueprint Synthesis
1. **Documentation**: Generate the **[Fiori App Analysis Blueprint](file:///C:/Users/jp_lopez/.gemini/antigravity/brain/b6d3c018-79ef-48e4-abb5-37af2ca21052/fiori_app_analysis_blueprint.md)**.
2. **Brain Map Update**: Add the new app, its services, and its persistence links to `entity_brain_map.md`.
3. **React Blueprint**: Standardize the OData payloads and visibility logic (e.g., `check_wf_step_visibility`) for the React clone.

---
> [!IMPORTANT]
> This workflow is **RFC-Only**. Developed through the successful reverse-engineering of UNESCO's Address, Offboarding, and Personal Data applications.
