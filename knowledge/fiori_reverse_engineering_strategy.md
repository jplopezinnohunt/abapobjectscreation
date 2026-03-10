# Fiori & HR Apps Reverse Engineering Strategy

This document serves as the living technical strategy for performing end-to-end analysis of SAP Fiori Applications, specializing in complex HR ESS/MSS scenarios.

## 1. Tactical Objective
The goal is to extract enough technical metadata from the SAP Backend (via RFC) and BSP layer to enable the creation of a high-fidelity React clone that mirrors SAP business rules without relying on the SAP UI5 runtime.

## 2. Extraction methodology (End-to-End)

### Phase A: Entry Point Discovery
- **Launchpad Analysis**: Identify Semantic Object & Action.
- **TADIR Lookup**: Locate the `WAPA` (BSP) and `IWSV` (OData) objects.
- **Package Context**: Identify the `DEVCLASS` (ABAP Package) to find companion services and shared frameworks (e.g., `ZHRBENEFITS_FIORI`).

### Phase B: Business Logic Extraction (The "Gold" Layer)
- **MPC Analysis**: Map OData entities to ABAP structures via Model Provider code.
- **DPC Redefinition Scanning**: Use `SEOREDEF` to find methods like `GET_ENTITYSET` that contain the actual logic.
- **Method Include Extraction**: Use the automated RFC include scanner to pull method source code into local `.abap` files.
- **Domain Class Analysis**: Identify core engine classes (e.g., `ZCL_HR_FIORI_OFFBOARDING_REQ`) called by the OData layer.

### Phase C: Workflow & Persistence Mapping
- **Custom Table Scanning**: Identify the state-machine tables (`Z*`) that track process steps.
- **Visibility Rules**: Extract logic that determines which steps/fields are visible based on HR parameters (Effective Date, Pernr, Contract Type).
- **On-Behalf Context**: Map the `CHECK_ON_BEHALF` authorization gates to determine who can edit for whom.
- **Service Orchestration**: Map dependencies between the main app and common services (Common, Approval, Generic Request services).
- **State Merging**: Document how the UI merges "Master Data" (PA*) with "Parked Data" (ASR/XML) for a unified user view.

## 3. Knowledge Management
- **Domain Analysis**: Results are saved in `knowledge/domains/<DOMAIN>/Fiori Apps/<app_name>_analysis.md`.
- **Entity Brain Map**: Update the global entity map with discovered relationships between HR tables and OData entities.
- **Filtering Registry**: Log any hardcoded logic or session filters discovered in the ABAP code.

## 4. Continuity & Updates
- This strategy is updated after every successful app analysis to incorporate new discovery patterns (e.g., handling deep-nested HR workflows).
- The corresponding **Skill** in `.agents/skills/sap_reverse_engineering` implements the technical automation for this strategy.
