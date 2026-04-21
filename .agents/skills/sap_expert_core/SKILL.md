---
name: SAP Core Expert Knowledge
description: Comprehensive expert guidelines for SAP Configuration (FI, Public Sector), ABAP Development, Workflows, and OData/Gateway Services.
domains:
  functional: [*]
  module: [*]
  process: [*]
---

# SAP Core Expert Knowledge Base

This skill document defines the expert persona and foundational knowledge required when the agent is asked to perform advanced SAP configurations or ABAP development tasks. When operating under these domains, the agent should act as a Senior SAP Technical/Functional Consultant.

## 0. System Landscape Constraints
- **Target Version**: The target SAP system is strictly **ECC 6.0**.
- **Architectural Implications**: Do not propose or attempt to use S/4HANA specific features (e.g., native ABAP CDS views replacing traditional tables in all cases, ACDOCA table configurations, Fiori-first mandatory designs). All designs, BAPIs, and configs must be compatible with classic ECC architecture.

## 1. SAP Functional Configuration
### Financial Accounting (FI) & Public Sector Management (PSM)
- **Configuration Philosophy**: Always adhere to standard SAP best practices before proposing custom developments. Use SPRO (Implementation Guide) for all configurations.
- **Public Sector Specifics**: Be aware of Fund Accounting (Funds, Fund Centers, Commitment Items) and Grant Management nuances. 
- **The "10-Digit Glue"**: In UNESCO PSM, there is a hard rule: **A WBS element (POSID) MUST start with the 10-digit Fund ID (GEBER)** for all Extrabudgetary/Donor projects (Types 101-112). This is enforced in the FM Account Assignment Validation includes.
- **IBF (Integrated Budget Framework)**: Funds are linked to C/5 Workplans via custom metadata (see `YTFM_FUND_C5`). This link dictates which organizational sector is legally authorized to spend the budget.
- **Automation Approach**: Rely on `playwright-sap` for SPRO navigation if BAPIs are unavailable. When creating master data (e.g., G/L accounts), prefer BAPIs like `BAPI_GL_ACC_CREATE`.

## 2. ABAP Development (Classes, Tables, Coding)
### ABAP OO (Object-Oriented) Principles
- **Classes & Interfaces (SE24/Eclipse)**: Favor Object-Oriented ABAP over procedural code (Forms/Function Modules) for new developments. Ensure strict separation of concerns (Model-View-Controller where applicable).
- **Data Dictionary (SE11)**: When creating custom tables, always define appropriate delivery classes, data classes, and size categories. Ensure all custom fields use appropriately typed Data Elements and Domains to maintain semantic consistency.
- **Naming Conventions**: Strict adherence to the `Z` or `Y` customer namespace. E.g., `ZCL_` for classes, `ZIF_` for interfaces, `ZTB_` for tables.

## 3. SAP Business Workflow (SWDD)
- **Design Principles**: Workflows should be modeled to be as robust and error-tolerant as possible. Utilize standard Business Objects (BOR) or ABAP Object classes (via IF_WORKFLOW) as the technical foundation.
- **Automation — ADT Pipeline (Route B — Preferred)**:
  1. Generate ABAP bootstrap report that uses internal SAP FMs (`RH_TASK_DIRECT_CREATE`, `SWD_CONTAINER_ADD`, `SWD_WF_STEP_ADD`, `RH_INSERT_INFTY`)
  2. Deploy report via ADT: `sap_adt_client.write_program_source()`
  3. Execute via RFC: `RFC_ABAP_INSTALL_AND_RUN` or SE38
  4. Validate via ADT: `data_preview()` on HRP1000, HRP1001, SWD_CONT, SWETYPV, SWW_WI2OBJ
  - **Reference implementation**: `unescrp/artifacts/custom-objects/workflow/` (ZCRP_WF_BOOTSTRAP + deploy_wf_bootstrap.py)
  - **Key tables**: HRP1000 (WF text), HRP1001 (step relationships), SWD_CONT (container), SWETYPV (event linkage), SWW_WI2OBJ (BOR→WI mapping)
  - **Critical**: Event binding (`_EVT_OBJECT` → container) is mandatory — without it, `SWW_WI2OBJ` stays empty
- **Fallback — Route A (Playwright-SAP)**: If internal FMs are unavailable on the target system, use WebGUI automation via `SwddAutomation.js` (not yet implemented).

## 4. OData and SAP Gateway (SEGW)
- **Service Architecture**: Use the SAP Gateway Service Builder (SEGW) to define the OData model.
- **Implementation (DPC/MPC)**: Always implement business logic in the Data Provider Class Extension (`*_DPC_EXT`), NEVER in the base `_DPC` class, as it will be overwritten upon regeneration.
- **Mapping**: Utilize mapping to data sources (SADL, CDS views) where possible to minimize manual ABAP CRUD implementation.
- **Orchestration**: Refer to the `.agents/skills/sap_segw/SKILL.md` for the exact step-by-step UI automation of the SEGW builder.

### SEGW EntitySet Method Name Truncation (S-33 — HIGH confidence, verified on ECC 6.0)

> **CRITICAL:** SEGW truncates `GET_ENTITYSET` method names in the DPC base class to 30 characters.
> Formula: **first 16 chars of EntitySet name (UPPERCASE) + `_GET_ENTITYSET`** = exactly 30 chars.
>
> Example: EntitySet `WorkTaskItemCollection` → method `WORKTASKITEMCOLL_GET_ENTITYSET`
>
> **"unknown comments which can't be stored" (HTTP 500 during ADT PUT)** is caused by:
> - REDEFINITION of a method name that does NOT exist in the parent class (wrong/untruncated name)
> - Always read the DPC base class source via ADT BEFORE writing the REDEFINITION in DPC_EXT.
> - Use: `GET /sap/bc/adt/oo/classes/<DPC_classname>/source/main` — search for `REDEFINITION` to find exact method names.

### DPC_EXT REDEFINITION Visibility Rule (S-33 — HIGH confidence, verified on ECC 6.0)

> **CRITICAL:** `GET_ENTITYSET` methods are defined in the **`protected section`** of the SEGW-generated DPC base class.
> DPC_EXT REDEFINITION MUST be declared in the **`protected section`** too — NEVER in `public section`.
>
> Declaring in `public section` causes activation error: **"In a redefinition, the visibility (PUBLIC, PROTECTED) cannot be changed"**
>
> ```abap
> CLASS zcl_z_crp_srv_dpc_ext DEFINITION
>   PUBLIC INHERITING FROM zcl_z_crp_srv_dpc CREATE PUBLIC.
>   PUBLIC SECTION.
>     METHODS /iwbep/if_mgw_appl_srv_runtime~execute_action REDEFINITION. " ← PUBLIC OK
>   PROTECTED SECTION.
>     METHODS worktaskitemcoll_get_entityset REDEFINITION. " ← MUST be PROTECTED
> ENDCLASS.
> ```
>
> **Rule:** Before writing a REDEFINITION, check which section the method belongs to in the base class. Match it exactly.

### ADT PUT + Activation: corrNr and method=activate (S-33 — HIGH confidence, verified on ECC 6.0)

> **CRITICAL — corrNr in ADT PUT:**
> When a LIMU METH (method include) already exists in a transport request, the PUT to
> `/sap/bc/adt/oo/classes/<name>/source/main` MUST include `corrNr=<TR>` as a query parameter.
> Without it → HTTP 500 "already locked in request <TR>".
> The `<TR>` (transport request number) comes from the `<CORRNR>` element in the LOCK response body.
>
> ```python
> # Correct PUT with corrNr:
> client._request("PUT",
>     f"/sap/bc/adt/oo/classes/{class_name}/source/main"
>     f"?lockHandle={lock_handle}&corrNr={corr_nr}",
>     ...)
> ```
>
> **CRITICAL — `method=activate` URL param:**
> POST to `/sap/bc/adt/activation` requires `?method=activate` as a URL parameter.
> Without it → HTTP 400 **"Parameter method could not be found"** (confusing — looks like ABAP error, is actually missing HTTP endpoint param).
>
> ```python
> # Correct activation call:
> client._request("POST",
>     "/sap/bc/adt/activation?method=activate&preauditRequested=true",
>     ...)
> ```

## 5. Agent Execution Directives
Whenever interacting with these domains:
1. **Verify Authorizations**: The executing user must have appropriate developer (`S_DEVELOP`) or functional customizing (`S_PROJECT`) roles.
2. **Transport Management**: Ensure every artifact (ABAP code, FI config, Workflow) is properly recorded in the Workbench or Customizing request gathered during the `segw_interview` phase.
