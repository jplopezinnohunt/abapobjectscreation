# UNESCO SAP Knowledge Brain — Entity Map

> **Living Document**: This map grows as new programs, tables, filters, and services are analyzed. It connects all discovered SAP objects into a unified, end-to-end knowledge graph organized by **object type** and **business purpose**.

---

## 0. The 5-Level Reverse Engineering Protocol

To enable high-fidelity cloning and technical reconstruction of the UNESCO system, we follow this hierarchical skill progression:

1.  **Level 1: ABAP Objects (The DNA)**: Direct source code extraction (Programs, Classes, BAdIs) using RFC.
2.  **Level 2: Fiori Reverse Engineering (The UI/Service)**: Reconstruction of BSP apps, OData manifests, and service hierarchies.
3.  **Level 3: Configuration Audit (The Logic)**: Extraction of business rules from T-tables (T588M, ZTHRFIOFORM_VISI, YTFM_*).
4.  **Level 4: Master Data Analysis (The Entities)**: Structural audit of Funds, Projects, and Employees. (Filter: **2024+**). (See [Level 4 skill](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/level_4_master_data_skill.md) & [Strategy](file:///c:/Users/jp_lopez/projects/abapobjectscreation/.agents/workflows/sap_configuration_strategy.md))
5.  **Level 5: Transactional Data Audit (The Flow)**: (Future) Monitoring of actual budget/actual postings and financial documents.

---

## 0.1 Domain Analysis Index
- **PSM-FM & PS**: [Initial Structural Analysis](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/psm_initial_analysis.md)
- **HCM**: [HCM Connectivity Map](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/HCM/Fiori%20Apps/hcm_connectivity_map.md)

---

## 1. End-to-End Data Model (Cross-Domain)

This diagram shows how **all discovered objects** connect across business domains. It is organized by layer: Entry Points → Business Logic → Data Sources → External Interfaces.

```mermaid
graph LR
    subgraph ENTRY["🖥️ Entry Points"]
        direction TB
        YFM1["YFM1\nFM Budget Report"]
        FIORI["Fiori App\n(CRP Frontend)"]
        FIORI_HCM["Fiori App\n(Personal Data)"]
        FIORI_ADDR["Fiori App\n(Manage Address)"]
        FIORI_FMLY["Fiori App\n(Family Management)"]
        FIORI_OFFB["Fiori App\n(Offboarding)"]
        FIORI_BENEF["Fiori App\n(Benefit Monitor)"]
        FIORI_BEN_ENR["Fiori App\n(Benefit Enrollment)"]
        RFC_CLIENT["Python MCP Client\n(sap_mcp_server.py)"]
    end

    subgraph LOGIC["🔷 Business Logic Layer"]
        direction TB
        YFM1_BCS_V3["YFM1_BCS_V3\n(Report Wrapper)"]
        YCL_BL["YCL_YFM1_BCS_BL\n(FM Report Logic)"]
        DPC_EXT["ZCL_Z_CRP_SRV\n_DPC_EXT\n(CRP Data Provider)"]
        MPC_EXT["ZCL_Z_CRP_SRV\n_MPC_EXT\n(CRP Model Provider)"]
        HCM_FEEDER["CL_HCMFAB_PERSINFO_FEEDER\n(HR Metadata & Data)"]
        ASR_LOGIC["ZCL_HRFIORI_BIRTH_OF_A_CHILD\n(ASR Workflow logic)"]
        OFFB_LOGIC["ZCL_HR_FIORI_OFFBOARDING_REQ\n(Offboarding Logic)"]
        BENEF_CTRL["ZCL_HR_FIORI_REQUEST\n(Benefit Request Controller)"]
        DMS_MGR["ZCL_HR_DOCUMENT_MANAGER\n(Universal DMS Handler)"]
        EVE_UN["CL_HRPADUN_EVE_ENVIRONMENT\n(UN Entitlement Engine)"]
        CL_SALV["CL_SALV_TABLE\n(ALV Framework)"]
        WF_NORM["ZCL_HRFIORI_PF_COMMON\n(Status Normalization Layer)"]
        UI_VISI["ZTHRFIOFORM_VISI\n(UI Logic Manifest)"]
        UI_METADATA["ZTHRFIORI_UI5PRO\n(Universal UI Metadata)"]
        STEP_CTRL["ZTHRFIORI_STEP\n(Section Controller)"]
    end

    subgraph PAYROLL["💰 UNESCO Payroll Engine"]
        PY_DRIVER["UN Payroll Driver\n(RPCALCx0)"]
        PY_WT_DA["Wage Type 12xx\n(Dependency Allowance)"]
        PY_WT_EG["Wage Type 4xxx\n(EG Reimbursement)"]
    end

    subgraph SERVICES["🌐 OData Services"]
        direction TB
        Z_CRP_SRV["Z_CRP_SRV\n(CRP OData Service)"]
        SRV_PERS["Z_HCMFAB_MYPERSONALDATA_SRV\n(HCM Profile)"]
        SRV_ADDR["Z_HCMFAB_ADDRESS_SRV\n(Manage Address)"]
        SRV_FMLY["ZHCMFAB_MYFAMILYMEMBERS_SRV\n(Family Management)"]
        SRV_ASR["ZHR_PROCESS_AND_FORMS_SRV\n(ASR Actions)"]
        SRV_OFFB["ZHR_OFFBOARD_SRV\n(Offboarding)"]
        SRV_BENEF["ZHR_BENEFITS_REQUESTS_SRV\n(Benefit Monitor)"]
        SRV_BENENR["ZHCMFAB_BEN_ENROLLMENT_SRV\n(Enrollment)"]
    end

    subgraph RFC_BAPI["⚡ RFCs & BAPIs"]
        direction TB
        RFC_READ["RFC_READ_TABLE\n(Generic Table Read)"]
        ARCH_INS["ARCHIV_CONNECTION_INSERT\n(ArchiveLink Link)"]
        ARCH_CRT["ARCHIVOBJECT_CREATE_TABLE\n(ArchiveLink Store)"]
        BAPI_USER["BAPI_USER_GET_DETAIL\n(User Master)"]
        RPY_READ["RPY_PROGRAM_READ\n(Program Source)"]
    end

    subgraph TABLES_STD["📊 Standard SAP Tables"]
        direction TB
        PA0002["PA0002\nPersonal Data"]
        PA0021["PA0021\nFamily Members"]
        T588M["T588M\nScreen Config (HCM)"]
        TOA01["TOA01\nArchiveLink Links"]
        TOAAT["TOAAT\nArchiveLink Metadata"]
        PA0965["PA0965\nEducation Grant"]
        T7UN_EVE["T7UNPAD_EVE\nUN Entitlements"]
    end

    subgraph TABLES_CUSTOM["🏛️ UNESCO Custom Tables"]
        direction TB
        ZBENEF_HDR["zthrfiori_breq\nBenefit Request Header"]
        ZBENEF_EG["zthrfiori_eg_mai\nEducation Grant Items"]
        ZBENEF_RS["zthrfiori_rs_mai\nRental Subsidy Items"]
        ZATTACH["ZTHRFIORI_ATTACH\nFiori DMS Registry"]
        ZTHRFIOFORM_VISI["ZTHRFIOFORM_VISI\nUI Manifest"]
        ZTHRFIORI_UI5PRO["ZTHRFIORI_UI5PRO\nComponent Properties"]
        ZTHRFIORI_STEP["ZTHRFIORI_OFFB_S\nStep Sections"]
        ZTHRFIORI_ATTAC["ZTHRFIORI_ATTAC\nDMS Link"]
    end

    subgraph HCM_BACKBONE["🧬 HCM Shared Backbone"]
        direction TB
        ASR_FW["ASR Framework\n(T5ASRSCENARIOS)"]
        BADI_COMMON["BAdI HCMFAB_B_COMMON\n(On Behalf Of logic)"]
    end

    %% Entry → Logic/Backbone
    FIORI_OFFB -->|consumes| SRV_OFFB
    FIORI_BENEF -->|consumes| SRV_BENEF
    
    %% Shared Backbone Connections
    SRV_PERS & SRV_ADDR & SRV_FMLY & SRV_ASR --> ASR_FW
    
    %% Service → Logic
    SRV_BENEF --> BENEF_CTRL
    SRV_OFFB --> OFFB_LOGIC
    OFFB_LOGIC & BENEF_CTRL --> DMS_MGR
    SRV_PERS & SRV_OFFB & SRV_BENEF --> OBO_BADI

    %% Logic → Tables
    BENEF_CTRL -->|stages in| ZBENEF_HDR
    BENEF_CTRL -->|populates| ZBENEF_EG & ZBENEF_RS
    DMS_MGR -->|links in| ZATTACH
    DMS_MGR -->|streams via| ARCH_CRT
    ARCH_CRT -->|persists in| TOAAT
    ARCH_INS -->|maps to| TOA01
    OBO_BADI -->|governs PERNR access via| PA0001
    OBO_BADI -->|validates Roles via| AGR_USERS
    
    %% Workflow Normalization
    SRV_PERS & SRV_OFFB & SRV_BENEF & SRV_ASR --> WF_NORM
    WF_NORM -->|Maps to| STD_00_06["Standard Status 00-06"]
    
    %% UI Control
    SRV_ASR --> UI_VISI
    UI_VISI -->|governs| FRONTOUT["UI Field State\n(Mandatory/Hidden/Read-Only)"]

    %% Payroll
    subgraph CONTROL["🛡️ Control & Derivation Layer"]
        direction TB
        FMDERIVE["FMDERIVE\n(Posting Derivation)"]
        AVC_DER["AVC Derivation\n(AFMA / AFMT)"]
        FMDERIVE_002["Table FMDERIVE002\n(G/L -> Commit Item)"]
        FMAFMAP["Table FMAFMAP*\n(AA Groups)"]
        SPAUTH["YCL_FM_SPENDING_AUTH\n(Appropriation Control)"]
    end

    %% Logic → Control
    YFM1_BCS_V3 --> SPAUTH
    SRV_CRP --> ODATA
    
    %% Control → Tables
    FMDERIVE --> FMDERIVE_002
    AVC_DER --> FMAFMAP
    SPAUTH --> YTFM_FUND_CPL
    
    %% Connections to existing nodes
    FMDERIVE_002 --> FM_ITEM
    FMAFMAP --> FM_FUND
    YTFM_FUND_CPL --> FM_FUND

```

---

## 2. Object Catalog by Type

### 2.1 Domain Classes (Purpose & Reusability)

| Class | Domain | Package | Purpose | Reuse Potential |
| :--- | :--- | :--- | :--- | :--- |
| `YCL_YFM1_BCS_BL` | FM Reporting | `YB` | Full business logic for YFM1 report: selection, data retrieval, WRTTP grouping, period accumulation, ALV display. | **High** — Methods like `READ_DATA_FROM_DB` and `COMPUTE_TOTAL_AMOUNTS` can be reused for any FM-based report. |
| `ZCL_Z_CRP_SRV_DPC_EXT` | CRP | `ZCRP` | Data Provider Extension for Z_CRP_SRV. Implements CRUD for CRP certificates and budget lines. | **Medium** — CRP-specific, but CRUD patterns are reusable for other OData services. |
| `ZCL_Z_CRP_SRV_MPC_EXT` | CRP | `ZCRP` | Model Provider Extension. Defines OData entity model metadata for CRP. | **Low** — Model-specific. Only reuse as a template for new SEGW services. |
| `CL_SALV_TABLE` | Framework | SAP | Standard SAP ALV framework class. Used by YFM1 for grid display. | **Universal** — Standard SAP class, reusable in any report. |
| `ZCL_HRFIORI_PF_COMMON` | HCM | `ZHR_DEV` | **Normalization Recommendation**: Layer to map ASR/Hybrid statuses to numeric 00-06. | **High** — Critical for cross-app HR reporting. |

### 2.2 OData Services

| Service | Domain | Package | Entities | Status |
| :--- | :--- | :--- | :--- | :--- |
| `Z_CRP_SRV` | CRP | `ZCRP` | `CrpCertificate`, `CrpBudgetLine`, `CrpAttachment` | Active |
| `Z_HCMFAB_MYPERSONALDATA_SRV` | HCM | `HCMFAB` | `PersonalData`, `FieldMetadataSet`, `FormScenario` | Active |
| `ZHR_PROCESS_AND_FORMS_SRV` | HCM | `ZHR_DEV` | `FormScenario`, `Attachment`, `Process` | Active |
| `ZHR_OFFBOARD_SRV` | HCM | `ZHR_DEV` | `Request`, `WorkflowStep`, `Employee` | Active |
| `ZHCMFAB_MYFAMILYMEMBERS_SRV` | HCM | `ZHR_DEV` | `FamilyMember`, `FamilyMemberUN` | Active |
| `ZHR_BENEFITS_REQUESTS_SRV` | HCM | `ZHR_DEV` | `RequestHeader`, `EducationGrant`, `RentalSubsidy` | Active (Draft -> HRA -> HRO) |
| `ZHCMFAB_BEN_ENROLLMENT_SRV` | HCM | `HCMFAB` | `BenefitEnrollmentSet`, `PlanSet` | Enhanced (Z_HCM_FAB_BEN_ENROLL) |



### 2.3 Reports, Programs & BSPs

| Object | Domain | Package | Type | Purpose | Key Class |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `YFM1` | FM | `YB` | Transaction | Aggregated FM budget/commitment reporting | `YCL_YFM1_BCS_BL` |
| `Z_PERS_MAN_EXT` | HCM | `ZHR_DEV` | BSP Application | UNESCO Extension for Fiori Personal Data | `CL_HCMFAB_PERSINFO_FEEDER` |
| `YPS8` | FM/PS | `YE` | Transaction | Integrated FM/PS reporting for non-RB funds | `YCL_YPS8_BCS_BL` |
| `ZHRBENEFREQ` | HCM | `ZHR_DEV` | BSP Application | UNESCO Benefit Request Management | `ZCL_HR_FIORI_REQUEST` |
| `YHR_BEN_ENRL` | HCM | `ZFIORI` | BSP Application | UNESCO Benefit Enrollment | `YCL_HR_BENEF_COMMON` |


### 2.4 RFCs & BAPIs

| Function Module | Type | Domain | Purpose | Used By |
| :--- | :--- | :--- | :--- | :--- |
| `RFC_READ_TABLE` | RFC | Cross-domain | Generic table reader. Reads any SAP transparent table by name. | `sap_mcp_server.py`, `read_t001.py`, `test_sap_connection.py` |
| `BAPI_GL_GETGLACCPERIODBALANCES` | BAPI | FI | Retrieves G/L account period balances. | `sap_client.py` |
| `BAPI_USER_GET_DETAIL` | BAPI | BC | Retrieves user master data details. | `sap_client.py` |
| `RPY_PROGRAM_READ` | RFC | BC/Dev | Reads ABAP program source code remotely. | Discovery protocol (backend analysis) |

### 2.5 HCM Shared Infrastructure (The Backbone)

| Component | Type | Purpose | Impacted Apps |
| :--- | :--- | :--- | :--- |
| `ASR / HCM Processes` | Framework | **Parking Pattern**: Stages data in XML snapshots (`T5ASR*`) before master record update. | All HCM Update Apps |
| `HCMFAB_B_COMMON` | BAdI | **On Behalf Of**: Unified authorization check for managers/admins. | Personal Data, Address, Family |
| `CL_HRPA_UI_CONVERT_*` | Class | **UNESCO Extensions**: Maps `ZZ*` custom fields from Infotypes to OData. | All HCM Apps |

### 2.6 Tables (Standard SAP)

(See [SAP Configuration Reference](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/sap_configuration_reference.md) for detailed business rules)

| Table | Domain | Purpose | Used By | Key Fields |
| :--- | :--- | :--- | :--- | :--- |
| `FMIT` | FM | **FM Totals** — Period-based amounts by Value Type | `YCL_YFM1_BCS_BL`, `YCL_YPS8_BCS_BL` | `FIKRS`, `RFONDS`, `RWRTTP`, `RYEAR`, `HSL01`–`HSL16` |
| `FMFINCODE` | FM | **Fund Master Data** — Fund descriptions and types | `YCL_YFM1_BCS_BL`, `YCL_YPS8_BCS_BL`, `CRP` | `FINCODE`, `FIKRS`, `BEZEICH` |
| `FMCIT` | FM | **Commitment Item Master** — Expenditure categories | `YCL_YFM1_BCS_BL`, `CRP` | `FIPEX`, `FIKRS`, `TEXT1` |
| `FMBDT` | FM | **Budget Entries** — Budget types | `YCL_YFM1_BCS_BL`, `YCL_YPS8_BCS_BL` | `BUDTYPE` |
| `PROJ` | PS | **Project Definition** — High-level project record | `YCL_YPS8_BCS_BL` | `PSPNR`, `PSPID` |
| `PRPS` | PS | **WBS Element** — Project structures and custom donor attributes | `YCL_YPS8_BCS_BL` | `OBJNR`, `POSID`, `PSPHI` |
| `T588M` | HCM | **Infotype Screen Modification** — Controls field visibility/editable state | `CL_HCMFAB_PERSINFO_FEEDER` | `MOLGA`, `INFTY`, `REPID`, `VARIABLE` |
| `T5ASRSCENARIOS` | HCM | **ASR Action Registry** — Maps HR Actions to Workflows | `ZHR_PROCESS_AND_FORMS_SRV` | `SCENARIO`, `SCENARIO_TYPE` |
| `PA0002` | HCM | **Personal Data** — Names, Birth dates | `HCM Fiori` | `PERNR`, `NACHN`, `VORNA` |
| `T001` | FI | **Company Codes** — Legal entities | `CRP`, `sap_mcp_server.py` | `BUKRS`, `BUTXT`, `WAERS` |

### 2.7 Level 4: Master Data Entities (The Pattern Scan)

High-fidelity patterns derived from data created since **2024-01-01** to avoid legacy noise.

| Entity | Table | Key Pattern Discovered | Date Filter Field |
| :--- | :--- | :--- | :--- |
| **Fund** | `FMFINCODE` | `FINCODE` (10 chars) matches `PROJ-PSPID`. | `ERFDAT` |
| **Project** | `PROJ` | `PSPID` is the root for all WBS elements. | `ERDAT` |
| **WBS Element**| `PRPS` | `POSID` contains hierarchical depth (e.g., `505INT0001.2.1.1`). | `ERDAT` |
| **Funds Center**| `FMFCTR` | Responsible unit for budget control. | `ERFDAT` |

### 2.6 Tables (UNESCO Custom)

| Table | Domain | Package | Purpose | Used By | Reuse Potential |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `YTFM_FUND_CPL` | FM | `YB` | Fund AL and Non-IBF (Complementary Authority) | `YCL_FM_SPENDING_AUTH` | **High** — Key for Budget vs Actuals |
| `FMDERIVE002` | FM | `SAP` | G/L to Commitment Item Mapping | `FMDERIVE` | **Internal** — Main Posting Rule |
| `FMAFMAP013500109` | FM | `9HZ00001`| AVC Account Assignment Groups | `FMAVCDERICH` | **Internal** — AVC Control Truth |



### 2.7 Filter Logic

| Filter ID | Field | Config Table | Domain | Discovered In | Reuse Potential |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `WRTTP_FM` | `RWRTTP` | `YTFM_WRTTP_GR` | FM | `YCL_YFM1_BCS_BL` | **High** — Any FM report. Full reference in [Filter Registry](file:///c:/Users/jp_lopez/projects/abapobjectscreation/.agents/skills/unesco_filter_registry/SKILL.md#wrttp_fm--funds-management-value-type-grouping) |

---

## 3. Cross-Domain Data Flow

This shows how data flows **end-to-end** from user interfaces through business logic to database tables, highlighting reuse points.

```mermaid
flowchart TB
    subgraph UI_LAYER["👤 User Interface Layer"]
        SAP_GUI["SAP GUI\n(Transaction YFM1)"]
        FIORI_APP["Fiori / Web App\n(CRP Certificates)"]
        PYTHON_CLIENT["Python MCP Client\n(Automated Access)"]
    end

    subgraph SERVICE_LAYER["🌐 Service Layer"]
        ODATA["Z_CRP_SRV\n(OData Gateway)"]
        RFC_LAYER["RFC/BAPI Layer\n(RFC_READ_TABLE,\nBAPI_GL_*, BAPI_USER_*)"]
    end

    subgraph BL_LAYER["🔷 Business Logic Layer"]
        YFM1_CLASS["YCL_YFM1_BCS_BL\n• SET_SELECTION_VALUES\n• READ_DATA_FROM_DB\n• COMPUTE_TOTAL_AMOUNTS\n• PREPARE_DATA\n• DISPLAY_ALV"]
        CRP_DPC["ZCL_Z_CRP_SRV_DPC_EXT\n• GET_ENTITY\n• CREATE_ENTITY\n• UPDATE_ENTITY"]
    end

    subgraph FILTER_LAYER["🔍 Filter & Config Layer"]
        WRTTP_FILTER["WRTTP_FM Filter\n(Budget/Actual/Commit)"]
        OUTPUT_CONFIG["YTFM_OUTPUT\n(UNESCO Output Codes)"]
    end

    subgraph DATA_LAYER["💾 Data Layer"]
        subgraph FM_DATA["FM Domain"]
            FM_TOTALS["FMIT (Totals)"]
            FM_FUND["FMFINCODE (Funds)"]
            FM_ITEM["FMCIT (Commit Items)"]
            FM_BUD["FMBDT (Budget Entries)"]
        end
        subgraph CRP_DATA["CRP Domain"]
            CRP_HDR["ZCRP_HDR (Certificates)"]
            CRP_ITM["ZCRP_ITM (Budget Lines)"]
        end
        subgraph CORE_DATA["Core/FI Domain"]
            COMPANY["T001 (Company Codes)"]
        end
    end

    %% UI → Service/Logic
    SAP_GUI --> YFM1_CLASS
    FIORI_APP --> ODATA
    PYTHON_CLIENT --> RFC_LAYER

    %% Service → Logic
    ODATA --> CRP_DPC
    RFC_LAYER -->|generic read| FM_TOTALS
    RFC_LAYER -->|generic read| COMPANY

    %% Logic → Filter/Config
    YFM1_CLASS --> WRTTP_FILTER
    YFM1_CLASS --> OUTPUT_CONFIG

    %% Logic → Data
    YFM1_CLASS --> FM_TOTALS
    YFM1_CLASS --> FM_FUND
    YFM1_CLASS --> FM_ITEM
    CRP_DPC --> CRP_HDR
    CRP_DPC --> CRP_ITM
    CRP_DPC -->|validates| COMPANY

    %% Cross-domain links (reuse!)
    CRP_ITM -.->|"🔄 Reuse: Fund & Commit Item"| FM_FUND
    CRP_ITM -.->|"🔄 Reuse: Fund & Commit Item"| FM_ITEM

    %% Filter → Data
    WRTTP_FILTER -->|groups RWRTTP| FM_TOTALS
```

---

## 4. Reuse Opportunities Matrix

> [!TIP]
> This matrix highlights objects that are used across **multiple domains**, making them candidates for shared libraries or services.

| Shared Object | Used by FM | Used by PS | Used by CRP | Used by FI | Used by Agent/MCP | Reuse Action |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `FMFINCODE` (Fund Master) | ✅ | ✅ | ✅ | — | ✅ | **Vital Link** `FINCODE` bridges FM and PS. Create shared OData entity |
| `PROJ` / `PRPS` (WBS) | ✅ (YPS8) | ✅ | — | — | — | `PROJ-PSPID` matches `FMFINCODE-FINCODE`. Use PRPS for donor custom fields (`YYE_DONOR`, `USR02`, etc.) |
| `FMCIT` (Commitment Items) | ✅ | — | ✅ | — | ✅ | **Create shared OData entity** — both domains need item data |
| `T001` (Company Codes) | — | — | ✅ | ✅ | ✅ | Already cross-domain. Candidate for a shared `CompanyCode` entity |
| `RFC_READ_TABLE` | — | — | — | — | ✅ | Universal backend access. Centralized in `sap_mcp_server.py` |
| `WRTTP_FM` (Filter Logic) | ✅ | — | — | — | — | **Any new FM report** should reuse this filter from the [Registry](file:///c:/Users/jp_lopez/projects/abapobjectscreation/.agents/skills/unesco_filter_registry/SKILL.md) |
| `YTFM_OUTPUT` (Output Codes) | ✅ | — | — | — | — | Reuse for any UNESCO Results-Based Budgeting report |

---

## 5. Growth Protocol

When analyzing a **new** SAP object (program, class, service, RFC, table), follow these steps to update this brain:

1. **Identify the object type** → Add it to the corresponding catalog section (2.1–2.7)
2. **Map its connections** → Add edges in the End-to-End Data Model diagram (Section 1)
3. **Check for reuse** → Update the Reuse Matrix (Section 4) if the object touches multiple domains
4. **Register any filters** → Add to the [UNESCO Filter Registry skill](file:///c:/Users/jp_lopez/projects/abapobjectscreation/.agents/skills/unesco_filter_registry/SKILL.md) if filter logic is found
5. **Map Field Connectivity** → Document the flow from UI to DB and Auth in the [HCM Connectivity Map](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/HCM/Fiori Apps/hcm_connectivity_map.md)
6. **Extract Configuration Rules** → Query the relevant T-tables or Manifest tables identified in the [SAP Configuration Reference](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/sap_configuration_reference.md).
7. **Map Fiori Screens & Fields** → Create a blueprint connecting UI sections to OData properties and PA tables in the [Fiori Reverse Engineering Blueprint](file:///c:/Users/jp_lopez/projects/abapobjectscreation/artifacts/fiori_reverse_engineering_blueprint.md)
8. **Cross-reference** → Link back from the object's domain analysis doc to this brain map

> [!IMPORTANT]
> **This is the single source of truth** for understanding what SAP objects exist, what they do, and how they connect. Every new analysis should update this file.
