# [Fiori Analysis] ZAW_CRP — Certificate Request Process (PSM Domain)
> **Artifact Type**: Fiori App Analysis — Full Stack Blueprint (BSP Layer + OData Service + DB Schema + Business Logic)

---

# PART I: APPLICATION LANDSCAPE

## 1. Functional Overview

The **Certificate Request Process (CRP)** app (`ZAW_CRP`) manages the lifecycle of operational certificates at UNESCO — documents that authorize financial and staff-related activities (e.g. consultancy contracts). The process covers:

1. **Certificate Creation**: Staff creates a CRP with budget allocation and period details.
2. **Budget Check**: System validates Fund/FundsCenter availability before submission.
3. **Approval Workflow**: Certificate moves through multi-step approval chain.
4. **JV Posting**: Approved certificate triggers a Journal Voucher (JV) document in FI.
5. **Allotment**: Final posting creates the allotment commitment in FM.

## 2. Technical Componentry

| Object | Type | Package | Role |
| :--- | :--- | :--- | :--- |
| `ZAW_CRP` | WAPA (BSP App) | `$TMP` | Frontend UI (Fiori-style) |
| `Z_CRP_SRV` | OData Service (IWPR) | `ZCRP` | Backend service project |
| `Z_CRP_SRV_SRV 0001` | IWSV | `ZCRP` | Registered service endpoint |
| `Z_CRP_SRV_MDL 0001` | IWMO | `ZCRP` | OData model definition |
| `ZCL_Z_CRP_SRV_MPC` | ABAP Class | `ZCRP` | Model Provider Class (auto-generated, frozen) |
| `ZCL_Z_CRP_SRV_MPC_EXT` | ABAP Class | `ZCRP` | Model Provider Extension (custom schema ✅) |
| `ZCL_Z_CRP_SRV_DPC` | ABAP Class | `ZCRP` | Data Provider Class (auto-generated, frozen) |
| `ZCL_Z_CRP_SRV_DPC_EXT` | ABAP Class | `ZCRP` | Data Provider Extension (custom logic ✅) |
| `ZCRP_BUDGETLN` | DB Table | `ZCRP` | Budget line items per certificate |
| `ZCRP_APRVL_HIST` | DB Table | `ZCRP` | Approval workflow history |
| `ZCRP_GRADE_CFG` | DB Table | `ZCRP` | Grade/daily rate configuration |
| `Z_CRP_SRV_SRV` | SICF Node | `ZCRP` | HTTP endpoint: `/sap/opu/odata/sap/Z_CRP_SRV` |

> **⚠️ Note on BSP Package**: The BSP app `ZAW_CRP` is currently in `$TMP` (local, not transported). The OData backend objects are properly packaged in `ZCRP`. The frontend needs to be moved to `ZCRP` or a transport request created before it can be released.

---

# PART II: THE ODATA MODEL (FULL SCHEMA)

Confirmed via `z_crp_srv_config.json` and SEGW automation prompt (`2026_03_04_crp_service_layer`).

## 2.1 Entity Types & Entity Sets

| Entity Type | Entity Set | Capabilities | Key Fields |
| :--- | :--- | :--- | :--- |
| `CrpCertificate` | `CrpCertificateSet` | C/R/U (no Delete) | CompanyCode + FiscalYear + CertificateId |
| `CrpBudgetLine` | `CrpBudgetLineSet` | C/R/U/D | CompanyCode + FiscalYear + CertificateId + LineId |
| `CrpAttachment` | `CrpAttachmentSet` | C/R/D (Media Entity) | CertificateId + AttachmentId |
| `CrpApprovalHistory` | `CrpApprovalHistorySet` | R only | HistoryId |
| `CostRate` | `CostRateSet` | R only | Grade + DutyStation + Biennium |

## 2.2 CrpCertificate — Full Property Schema

| Property | EDM Type | Key | MaxLen | Label | Backend Source (Design) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CompanyCode` | Edm.String | ✅ | 4 | Company Code | `T001-BUKRS` |
| `FiscalYear` | Edm.String | ✅ | 4 | Fiscal Year | `ZCRP_CERT-GJAHR` |
| `CertificateId` | Edm.String | ✅ | 20 | Certificate ID | `ZCRP_CERT-CERT_ID` |
| `DocumentDate` | Edm.DateTime | | — | Document Date | `ZCRP_CERT-BLDAT` |
| `PostingDate` | Edm.DateTime | | — | Posting Date | `ZCRP_CERT-BUDAT` |
| `HeaderText` | Edm.String | | 25 | Header Text | `ZCRP_CERT-BKTXT` |
| `ReferenceDoc` | Edm.String | | 16 | Reference | `ZCRP_CERT-XBLNR` |
| `Status` | Edm.String | | 2 | Status | State machine (see §IV) |
| `PostingPeriod` | Edm.String | | 2 | Period | `ZCRP_CERT-MONAT` |
| `StaffId` | Edm.String | | 8 | Staff ID | `PA0001-PERNR` |
| `StaffName` | Edm.String | | 80 | Staff Name | `PA0002-VORNA`+`NACHN` |
| `Grade` | Edm.String | | 4 | Grade | `PA0001-STELL` |
| `PostTitle` | Edm.String | | 40 | Post Title | `PA0001-PLANS` |
| `BusinessArea` | Edm.String | | 4 | Business Area | `ZCRP_CERT-GSBER` |
| `FieldOffice` | Edm.String | | 40 | Field Office | `ZCRP_CERT-FIELD_OFF` |
| `NumberOfWorkingDays` | Edm.Int32 | | — | Working Days | Calculated from Start/End |
| `StartDate` | Edm.DateTime | | — | Start Date | `ZCRP_CERT-BEGDA` |
| `EndDate` | Edm.DateTime | | — | End Date | `ZCRP_CERT-ENDDA` |
| `CalculatedAmount` | Edm.Decimal | | P:13 S:2 | Amount | Days × DailyRate |
| `Currency` | Edm.String | | 5 | Currency | `T001-WAERS` |
| `GLAccount` | Edm.String | | 10 | GL Account | `ZCRP_CERT-HKONT` |
| `DescriptionOfTasks` | Edm.String | | 0 | Description | `ZCRP_CERT-DESCR` |
| `JVDocNumber` | Edm.String | | 10 | JV Document # | `BKPF-BELNR` (after posting) |
| `JVFiscalYear` | Edm.String | | 4 | JV Fiscal Year | `BKPF-GJAHR` |
| `JVPostedAt` | Edm.DateTime | | — | JV Posted At | `BKPF-CPUDT` |
| `CreatorAuthType` | Edm.String | | 10 | Auth Type | Role-based |
| `CreatedBy` | Edm.String | | 12 | Created By | `SY-UNAME` |
| `CreatedAt` | Edm.DateTime | | — | Created At | `SY-DATUM`+`SY-UZEIT` |
| `ChangedBy` | Edm.String | | 12 | Changed By | `SY-UNAME` |
| `ChangedAt` | Edm.DateTime | | — | Changed At | `SY-DATUM`+`SY-UZEIT` |

## 2.3 CrpBudgetLine — FM Integration

| Property | EDM Type | Key | MaxLen | FM Relevance |
| :--- | :--- | :--- | :--- | :--- |
| `CompanyCode` | Edm.String | ✅ | 4 | Links to `T001` |
| `FiscalYear` | Edm.String | ✅ | 4 | FM fiscal year |
| `CertificateId` | Edm.String | ✅ | 20 | FK to header |
| `LineId` | Edm.String | ✅ | 3 | Line number (001, 002…) |
| `Fund` | Edm.String | | 10 | **FM Fund** (`FMFUNDD-FINCC`) |
| `FundsCenter` | Edm.String | | 16 | **FM Funds Center** (`FMFCTR`) |
| `CommitmentItem` | Edm.String | | 24 | **FM Commitment Item** |
| `BusinessArea` | Edm.String | | 4 | `GSBER` |
| `WBSElement` | Edm.String | | 24 | **PS WBS** (10-digit Fund rule!) |
| `CRPCode` | Edm.String | | 20 | Internal reference code |
| `Amount` | Edm.Decimal | | P:13 S:2 | Posting amount |
| `Currency` | Edm.String | | 5 | Line currency |
| `BudgetAvailable` | Edm.String | | 1 | `X` = funds confirmed |

## 2.4 CrpAttachment (Media Entity)

Marked as **Media Entity** in SEGW (`m:HasStream="true"`). Binary content handled via `Edm.Stream`. Metadata properties: `FileName`, `MimeType`, `FileSize`, `Category`, `UploadedBy`, `UploadedAt`.

## 2.5 CrpApprovalHistory & CostRate (Read-Only)

- **`CrpApprovalHistory`** → persisted in `ZCRP_APRVL_HIST` (confirmed in TADIR).
- **`CostRate`** → driven by `ZCRP_GRADE_CFG` (Grade + DutyStation + Biennium → DailyRate). This is the rate lookup table for amount calculation.

---

# PART III: ASSOCIATIONS & NAVIGATION PROPERTIES

```
CrpCertificate (1)
├── ToBudgetLines    → CrpBudgetLine (M)     [FK: CompanyCode+FiscalYear+CertificateId]
├── ToAttachments    → CrpAttachment (M)     [FK: CertificateId]
└── ToApprovalHistory → CrpApprovalHistory (M) [FK: CertificateId]
```

---

# PART IV: FUNCTION IMPORTS (Actions)

These are the **state-changing operations** — the heart of the CRP business logic:

| Function Import | HTTP | Returns | Purpose |
| :--- | :--- | :--- | :--- |
| `SubmitForApproval` | POST | `CrpCertificate` (1) | Transitions certificate from Draft → Pending |
| `SimulateJVPosting` | POST | `JVSimulationResult` | Dry-run of FI JV document — validates before posting |
| `PostJV` | POST | `JVPostingResult` | Creates the actual FI Journal Voucher |
| `PostAllotment` | POST | `AllotmentResult` | Posts the FM allotment commitment |

### Complex Types Returned by Function Imports

**`JVSimulationResult`**: `Success (Boolean)`, `DocumentNumber (String/10)`, `Messages (String)`
**`JVPostingResult`**: `Success (Boolean)`, `DocumentNumber (String/10)`, `FiscalYear (String/4)`, `Messages (String)`
**`AllotmentResult`**: `Success (Boolean)`, `AllotmentId (String/20)`, `Messages (String)`

---

# PART V: APPROVAL WORKFLOW STATE MACHINE

Based on functional design (code not yet implemented in DPC_EXT):

| Status Code | Status Text | Trigger | Allowed Next States |
| :--- | :--- | :--- | :--- |
| `01` | Draft | Creation | `02` |
| `02` | Submitted (Pending) | `SubmitForApproval` | `03`, `05` |
| `03` | Approved | Approver decision | `04` |
| `04` | JV Posted | `PostJV` | `05` (allotment) |
| `05` | Rejected | Approver decision | `01` (revise) |
| `09` | Allotment Posted | `PostAllotment` | — (terminal) |

---

# PART VI: DATABASE SCHEMA — CONFIRMED FROM LIVE MPC SOURCE

All field names below are the **exact ABAP names** extracted from `ZCL_Z_CRP_SRV_MPC` via RFC (2026-03-10). These are the authoritative names for all SELECT/INSERT statements in DPC_EXT.

## ZCRP_CERT — Certificate Header
*Bound via: `lo_entity_type->bind_structure( 'ZCRP_CERT' )`*

| OData Property | ABAP Field | Type | Key | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `CompanyCode` | `BUKRS` | CHAR(4) | ✅ | |
| `FiscalYear` | `GJAHR` | NUMC(4) | ✅ | Conv: GJAHR |
| `CertificateId` | `CERTIFICATE_ID` | CHAR(20) | ✅ | |
| `DocumentDate` | `BLDAT` | DATS | | |
| `PostingDate` | `BUDAT` | DATS | | |
| `HeaderText` | `BKTXT` | CHAR(25) | | |
| `ReferenceDoc` | `XBLNR` | CHAR(16) | | |
| `Status` | `STATUS` | CHAR(2) | | State machine |
| `PostingPeriod` | `MONAT` | NUMC(2) | | |
| `StaffId` | `STAFF_ID` | NUMC(8) | | PERNR |
| `StaffName` | `STAFF_NAME` | CHAR(80) | | |
| `Grade` | `GRADE` | CHAR(4) | | |
| `PostTitle` | `POST_TITLE` | CHAR(40) | | |
| `BusinessArea` | `GSBER` | CHAR(4) | | |
| `FieldOffice` | `FIELD_OFFICE` | CHAR(40) | | |
| `NumberOfWorkingDays` | `NUM_WORK_DAYS` | INT4 | | Calculated |
| `StartDate` | `BEGDA` | DATS | | |
| `EndDate` | `ENDDA` | DATS | | |
| `CalculatedAmount` | `CALC_AMOUNT` | DEC(13,2) | | Days × Rate |
| `Currency` | `CURRENCY` | CUKY(5) | | |
| `GlAccount` | `GL_ACCOUNT` | CHAR(10) | | Conv: ALPHA |
| `Description` | `DESCRIPTION` | STRG | | |
| `JvBelnr` | `JV_BELNR` | CHAR(10) | | Conv: ALPHA — filled after PostJV |
| `JvGjahr` | `JV_GJAHR` | NUMC(4) | | Conv: GJAHR |
| `JvPostedAt` | `JV_POSTED_AT` | TIMESTAMP | | |
| `CreatorAuthType` | `CREATOR_AUTH_TYPE` | CHAR(10) | | |
| `CreatedBy` | `CREATED_BY` | CHAR(12) | | SY-UNAME |
| `CreatedAt` | `CREATED_AT` | TIMESTAMP | | |
| `ChangedBy` | `CHANGED_BY` | CHAR(12) | | |
| `ChangedAt` | `CHANGED_AT` | TIMESTAMP | | |

## ZCRP_BUDGETLN — Budget Lines
*Bound via: `lo_entity_type->bind_structure( 'ZCRP_BUDGETLN' )`*
> **Critical**: Uses SAP-native FM field names (FONDS, FICTR, FIPEX) — not display aliases.

| OData Property | ABAP Field | Type | Key | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `CompanyCode` | `BUKRS` | CHAR(4) | ✅ | |
| `FiscalYear` | `GJAHR` | NUMC(4) | ✅ | Conv: GJAHR |
| `CertificateId` | `CERTIFICATE_ID` | CHAR(20) | ✅ | FK to ZCRP_CERT |
| `LineId` | `LINE_ID` | CHAR(3) | ✅ | 001, 002… |
| `Fonds` | `FONDS` | CHAR(10) | | FM Fund |
| `Fictr` | `FICTR` | CHAR(16) | | FM Funds Center |
| `Fipex` | `FIPEX` | CHAR(24) | | Commitment Item — Conv: FIPEX |
| `Gsber` | `GSBER` | CHAR(4) | | Business Area |
| `WbsElement` | `WBS_ELEMENT` | CHAR(24) | | Conv: ABPSN |
| `CrpCode` | `CRP_CODE` | CHAR(20) | | |
| `Amount` | `AMOUNT` | DEC(13,2) | | |
| `Currency` | `CURRENCY` | CUKY(5) | | |
| `BudgetAvailable` | `BUDGET_AVAILABLE` | CHAR(1) | | `X` = confirmed |

## ZCRP_APRVL_HIST — Approval History
*Bound via: `lo_entity_type->bind_structure( 'ZCRP_APRVL_HIST' )`*
> **Note**: Key is BUKRS+GJAHR+HIST_SEQ+CERTIFICATE_ID (4-part key, not just HistoryId as designed).

| OData Property | ABAP Field | Type | Key | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `Bukrs` | `BUKRS` | CHAR(4) | ✅ | |
| `Gjahr` | `GJAHR` | NUMC(4) | ✅ | Conv: GJAHR |
| `HistSeq` | `HIST_SEQ` | CHAR(10) | ✅ | Sequence number |
| `CertificateId` | `CERTIFICATE_ID` | CHAR(20) | ✅ | |
| `StepName` | `STEP_NAME` | CHAR(40) | | |
| `ActorId` | `ACTOR_ID` | NUMC(8) | | PERNR of approver |
| `ActorName` | `ACTOR_NAME` | CHAR(80) | | |
| `Decision` | `DECISION` | CHAR(10) | | APPROVE/REJECT |
| `Apcomment` | `APCOMMENT` | CHAR(255) | | |
| `DecisionAt` | `DECISION_AT` | TIMESTAMP | | |

## ZCRP_GRADE_CFG — Cost Rate Configuration (CostRate entity)
*Bound via: `lo_entity_type->bind_structure( 'ZCRP_GRADE_CFG' )`*
> **Note**: Actual schema differs from config JSON — has Grade+Category+Description only (3 fields confirmed).

| OData Property | ABAP Field | Type | Key | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `Grade` | `GRADE` | CHAR(10) | ✅ | |
| `Category` | `CATEGORY` | CHAR(10) | | |
| `Description` | `DESCRIPTION` | CHAR(40) | | |

> ⚠️ **Design Gap**: The config JSON specified DailyRate+DutyStation+Biennium on CostRate, but the live MPC only exposes Grade+Category+Description from ZCRP_GRADE_CFG. The rate calculation logic must be inside the DPC_EXT method, not a simple table lookup.

---

# PART VII: BACKEND IMPLEMENTATION STATUS

| Layer | Object | Status |
| :--- | :--- | :--- |
| **SEGW Project** | `Z_CRP_SRV` | ✅ Created & registered (IWSV confirmed) |
| **MPC** | `ZCL_Z_CRP_SRV_MPC` | ✅ Auto-generated (frozen — do not edit) |
| **MPC_EXT** | `ZCL_Z_CRP_SRV_MPC_EXT` | ✅ Generated — schema customization target |
| **DPC** | `ZCL_Z_CRP_SRV_DPC` | ✅ Auto-generated (frozen — do not edit) |
| **DPC_EXT** | `ZCL_Z_CRP_SRV_DPC_EXT` | ⚠️ **Only MAC stub exists** — CRUD-Q logic NOT yet implemented |
| **ICF Node** | `Z_CRP_SRV_SRV` | ✅ Registered in SICF |
| **BSP Frontend** | `ZAW_CRP` | ⚠️ In `$TMP` — not transported, UI logic unverified |
| **DB Tables** | `ZCRP_BUDGETLN`, `ZCRP_APRVL_HIST`, `ZCRP_GRADE_CFG` | ✅ Confirmed live |

**Bottom line**: The OData shell (`$metadata`) is operational, but the **DPC_EXT has no implemented methods** — every CRUD-Q call currently falls through to the auto-generated empty base class. All business logic (reads, writes, function imports) must still be coded.

---

# PART VIII: DOMAIN INTERSECTIONS

| Domain | Integration Point | Object |
| :--- | :--- | :--- |
| **FI (Finance)** | JV Document creation (`PostJV`) | `BKPF`/`BSEG`, BAPI_ACC_DOCUMENT_POST |
| **FM (Fund Management)** | Budget availability check, allotment posting | `FMFCTR`, `FMEDCO`, BAPI_FUNDSCOMMIT_* |
| **PS (Project System)** | WBS Element on budget line | `PRPS`, 10-digit Fund-WBS matching rule |
| **HCM (HR)** | Staff ID lookup, grade/post title | `PA0001`, `PA0002` |
| **DMS (Documents)** | Certificate attachments | GOS / ArchiveLink |
| **YFMXCHKP** | Fiscal period gate | Blocks FM postings when `ACTIV = 'X'` |
| **YXUSER** | Bypass list | Users exempt from FM validation rules |

---

# PART IX: REVERSE ENGINEERING GAPS & NEXT STEPS

> [!IMPORTANT]
> **Architecture decision updated (2026-03-10):** The CRP approval lifecycle will use the **ASR Hybrid model**. `Z_CRP_SRV` continues to handle all data editing (CRUD, FM check, JV/Allotment posting). The ASR framework handles Submit, Approve/Reject, process lifecycle, and audit trail. See full analysis: [`crp_asr_vs_segw_analysis.md`](./crp_asr_vs_segw_analysis.md).

## Open items for complete implementation:

### Z_CRP_SRV — DPC_EXT (data layer — unchanged architecture)
1. `CRPCERTIFICATESET_GET_ENTITYSET` — list with Status/Date filter
2. `CRPCERTIFICATESET_GET_ENTITY` — single read
3. `CRPCERTIFICATESET_CREATE_ENTITY` — draft creation → `ZCRP_CERT`
4. `CRPCERTIFICATESET_UPDATE_ENTITY` — edit in Draft state
5. `CRPBUDGETLINESET_*` — full CRUD with FM availability check per line
6. `CRPATTACHMENTSET_*` — create/read/delete media stream
7. `SIMULATEJVPOSTING_FI` — FI dry-run BAPI (used for FM check on screen event)
8. `POSTJV_FI` — FI JV creation (triggered by WF task after approval)
9. `POSTALLOTMENT_FI` — FM allotment commitment (triggered by WF task)

### ASR Service — New (approval lifecycle)
10. Register scenario `ZPSM_CRP_CERTIFICATE` in `T5ASRSCENARIOS`
11. Create `ZCL_CRP_ASR_PROCESSOR` implementing `IF_HRASR00GEN_SERVICE`
12. Configure Workflow `WS_ZCRP_CERT` in SWDD (Submit → Approve/Reject → Post)

### `Z_CRP_SRV` — Removes (move to ASR)
13. ~~`SUBMITFORAPPROVAL_FI`~~ → replaced by `EXECUTE_ACTION` on ASR
14. ~~`CRPAPPROVALHISTORYSET`~~ → replaced by `T5ASRPROCESSES` native read

### App & Transport
15. BSP Package — Move `ZAW_CRP` from `$TMP` to `ZCRP` and transport
16. Wire Submit button → `EXECUTE_ACTION(ZPSM_CRP_CERTIFICATE)`
17. Wire budget line events → `SIMULATEJVPOSTING_FI` for real-time FM feedback
18. Confirm/create `ZCRP_CERT` and `ZCRP_GL_MAP` tables
19. Authorization — `S_SERVICE` for `Z_CRP_SRV` + custom `Z_CRP_ACT` object

---

*Sources: RFC/TADIR queries (D01 system, 2026-03-10), `z_crp_srv_config.json`, `automation_prompt.md` (task 2026_03_04_crp_service_layer), ASR analysis (2026-03-10).*

