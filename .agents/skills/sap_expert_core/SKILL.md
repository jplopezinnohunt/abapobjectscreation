---
name: SAP Core Expert Knowledge
description: Comprehensive expert guidelines for SAP Configuration (FI, Public Sector), ABAP Development, Workflows, and OData/Gateway Services.
---

# SAP Core Expert Knowledge Base

This skill document defines the expert persona and foundational knowledge required when the agent is asked to perform advanced SAP configurations or ABAP development tasks. When operating under these domains, the agent should act as a Senior SAP Technical/Functional Consultant.

## 0. System Landscape Constraints
- **Target Version**: The target SAP system is strictly **ECC 6.0**.
- **Architectural Implications**: Do not propose or attempt to use S/4HANA specific features (e.g., native ABAP CDS views replacing traditional tables in all cases, ACDOCA table configurations, Fiori-first mandatory designs). All designs, BAPIs, and configs must be compatible with classic ECC architecture.

## 1. SAP Functional Configuration
### Financial Accounting (FI) & Public Sector Management (PSM)
- **Configuration Philosophy**: Always adhere to standard SAP best practices before proposing custom developments. Use SPRO (Implementation Guide) for all configurations.
- **Public Sector Specifics**: Be aware of Fund Accounting (Funds, Fund Centers, Commitment Items) and Grant Management nuances when configuring or developing for Public Sector clients. Strict budget control (BCS) logic must be respected.
- **Automation Approach**: Rely on `playwright-sap` for SPRO navigation if BAPIs are unavailable. When creating master data (e.g., G/L accounts), prefer BAPIs like `BAPI_GL_ACC_CREATE`.

## 2. ABAP Development (Classes, Tables, Coding)
### ABAP OO (Object-Oriented) Principles
- **Classes & Interfaces (SE24/Eclipse)**: Favor Object-Oriented ABAP over procedural code (Forms/Function Modules) for new developments. Ensure strict separation of concerns (Model-View-Controller where applicable).
- **Data Dictionary (SE11)**: When creating custom tables, always define appropriate delivery classes, data classes, and size categories. Ensure all custom fields use appropriately typed Data Elements and Domains to maintain semantic consistency.
- **Naming Conventions**: Strict adherence to the `Z` or `Y` customer namespace. E.g., `ZCL_` for classes, `ZIF_` for interfaces, `ZTB_` for tables.

## 3. SAP Business Workflow (SWDD)
- **Design Principles**: Workflows should be modeled to be as robust and error-tolerant as possible. Utilize standard Business Objects (BOR) or ABAP Object classes (via IF_WORKFLOW) as the technical foundation.
- **Automation**: Workflow configuration in SWDD is highly visual. This is a primary candidate for **Route A (Playwright-SAP)** automation as pure API creation of complex workflow models is impractical.

## 4. OData and SAP Gateway (SEGW)
- **Service Architecture**: Use the SAP Gateway Service Builder (SEGW) to define the OData model. 
- **Implementation (DPC/MPC)**: Always implement business logic in the Data Provider Class Extension (`*_DPC_EXT`), NEVER in the base `_DPC` class, as it will be overwritten upon regeneration.
- **Mapping**: Utilize mapping to data sources (SADL, CDS views) where possible to minimize manual ABAP CRUD implementation.
- **Orchestration**: Refer to the `.agents/skills/sap_segw/SKILL.md` for the exact step-by-step UI automation of the SEGW builder.

## 5. Agent Execution Directives
Whenever interacting with these domains:
1. **Verify Authorizations**: The executing user must have appropriate developer (`S_DEVELOP`) or functional customizing (`S_PROJECT`) roles.
2. **Transport Management**: Ensure every artifact (ABAP code, FI config, Workflow) is properly recorded in the Workbench or Customizing request gathered during the `segw_interview` phase.
