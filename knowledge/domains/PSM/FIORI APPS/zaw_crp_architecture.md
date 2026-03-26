# [Architecture] ZAW_CRP — Fiori App Full Design Blueprint
> **Domain**: PSM / Finance · **App Type**: Custom Full-Stack (BSP + SEGW) · **Date**: 2026-03-10

---

# PART I: THE FULL STACK PICTURE

## 1. System Layer Map — Hybrid Dual-Service Architecture

> [!IMPORTANT]
> **Updated 2026-03-10:** CRP uses a **Hybrid model** — the BSP app calls both services. See [`crp_asr_vs_segw_analysis.md`](./crp_asr_vs_segw_analysis.md) for full rationale.

```
┌─────────────────────────────────────────────────────────────┐
│  BROWSER (Fiori Launchpad)                                  │
│  BSP App: ZAW_CRP  [Package: $TMP → must move to ZCRP]     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  List Report Screen (My Certificates)                 │  │
│  │  Object Page Screen (Certificate Detail)              │  │
│  │  Create/Edit Dialog (New Certificate Wizard)          │  │
│  └───────────────────────────────────────────────────────┘  │
│           │ DATA (CRUD)                │ LIFECYCLE (WF)      │
└───────────┼────────────────────────────┼─────────────────────┘
            │                            │
┌───────────▼──────────────┐ ┌───────────▼──────────────────┐
│  Z_CRP_SRV (SEGW)        │ │  ASR Service                 │
│  /sap/opu/odata/sap/     │ │  ZHR_PROCESS_AND_FORMS_SRV   │
│  Z_CRP_SRV/              │ │  (or ZPSM_PROCESS_SRV)       │
│                          │ │                              │
│  CrpCertificateSet       │ │  EXECUTE_ACTION              │
│  CrpBudgetLineSet        │ │  GET_PROCESS_LIST            │
│  CrpAttachmentSet        │ │  GET_PROCESS_INSTANCE        │
│  CostRateSet             │ │  T5ASRSCENARIOS registry     │
│  SIMULATEJVPOSTING_FI    │ │  ZCL_CRP_ASR_PROCESSOR       │
│  POSTJV_FI               │ │  WS_ZCRP_CERT (Workflow)     │
│  POSTALLOTMENT_FI        │ │                              │
│                          │ │  Scenario: ZPSM_CRP_CERT     │
│  ZCL_Z_CRP_SRV_MPC       │ │  T5ASRPROCESSES (lifecycle)  │
│  ZCL_Z_CRP_SRV_MPC_EXT   │ │  T5ASRDATAVAR (XML vault)    │
│  ZCL_Z_CRP_SRV_DPC       │ │                              │
│  ZCL_Z_CRP_SRV_DPC_EXT   │ │                              │
│  └── ZCL_CRP_PROCESS_REQ │ └──────────────────────────────┘
└──────────────────────────┘
            │ ABAP / RFC / BAPI
┌───────────▼──────────────────────────────────────────────────┐
│  PERSISTENCE & INTEGRATION LAYER                             │
│  ┌─────────────────┐ ┌──────────────────┐ ┌─────────────┐   │
│  │ ZCRP_CERT       │ │ ZCRP_BUDGETLN    │ │ ZCRP_GRADE  │   │
│  │ (Draft/Working) │ │ (Lines - FM data)│ │ _CFG        │   │
│  └─────────────────┘ └──────────────────┘ └─────────────┘   │
│  ┌─────────────────┐ ┌──────────────────┐ ┌─────────────┐   │
│  │ T5ASRPROCESSES  │ │ T5ASRDATAVAR     │ │ BKPF/BSEG   │   │
│  │ (WF lifecycle)  │ │ (XML audit vault)│ │ (FI posting)│   │
│  └─────────────────┘ └──────────────────┘ └─────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

**Service responsibility split:**
| Operation | Service |
|:---|:---|
| Create/Edit certificate & lines | `Z_CRP_SRV` |
| FM budget check (on field event) | `Z_CRP_SRV → SIMULATEJVPOSTING_FI` |
| File attachments | `Z_CRP_SRV → CrpAttachment` (Media Entity) |
| Submit for approval | **ASR → `EXECUTE_ACTION`** |
| Approve / Reject | **ASR → WF task decision** |
| Approval history / audit trail | **ASR → `T5ASRPROCESSES` + `T5ASRDATAVAR`** |
| Post JV / Allotment | `Z_CRP_SRV` (called from WF task after approval) |



---

# PART II: SCREEN ARCHITECTURE

## 2. Application Flow (Navigation)

```
Launchpad Tile: "Certificate Requests" (ZAW_CRP)
        │
        ▼
┌───────────────────────────────────────┐
│  SCREEN 1: LIST REPORT                │
│  "My Certificate Requests"            │
│  ┌────────────────────────────┐       │
│  │ Filter Bar:                │       │
│  │  Status | Fiscal Year      │       │
│  │  Date Range | Staff        │       │
│  └────────────────────────────┘       │
│  ┌────────────────────────────┐       │
│  │ Table:                     │       │
│  │  CertID | Staff | Status   │       │
│  │  Amount  | Fund  | Date    │       │
│  └────────────────────────────┘       │
│  [+ New Certificate]                  │
└──────────────┬──────────┬─────────────┘
               │ Click    │ Click "New"
               ▼          ▼
┌────────────────┐  ┌───────────────────────────┐
│ SCREEN 2:      │  │  SCREEN 3: CREATE WIZARD  │
│ OBJECT PAGE    │  │  Step 1: Header Data      │
│ Certificate    │  │  Step 2: Budget Lines     │
│ Detail         │  │  Step 3: Attachments      │
│                │  │  Step 4: Review & Submit  │
│ [Tabs below]   │  └───────────────────────────┘
└────────────────┘
```

## 3. Screen 2: Object Page — Tab Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER BLOCK                                                │
│ Certificate: CRP-2024-001 | Staff: J.DUPONT | Status: ●    │
│ Amount: USD 5,000 | Fund: 06000 | Period: 01/2024          │
├─────────────────────────────────────────────────────────────┤
│ [General Info] [Budget Lines] [Attachments] [History]       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ TAB: General Info                                           │
│  Company Code | Fiscal Year  | Reference Doc               │
│  Start Date   | End Date     | Working Days (calculated)   │
│  Grade        | Post Title   | Field Office                │
│  GL Account   | Description of Tasks                       │
│                                                             │
│ TAB: Budget Lines                                          │
│  [Table] Fund | FundsCenter | CommItem | WBS | Amount      │
│  [+ Add Line] [Delete Line]                                 │
│  Budget Available: ✅ / ❌                                  │
│                                                             │
│ TAB: Attachments                                            │
│  [Upload] | FileName | Category | Size | UploadedBy        │
│                                                             │
│ TAB: Approval History                                       │
│  Timeline: Step | Actor | Decision | Comment | Date        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ ACTION TOOLBAR (State-driven — see §5)                      │
│ [Submit] [Simulate JV] [Post JV] [Post Allotment] [Cancel] │
└─────────────────────────────────────────────────────────────┘
```

---

# PART III: DATA FLOW ARCHITECTURE

## 4. End-to-End Field Connectivity Matrix

| UI Field | OData Property | ABAP Field | DB Table | Logic |
| :--- | :--- | :--- | :--- | :--- |
| **Company Code** | `CompanyCode` | `BUKRS` | `ZCRP_CERT` | Defaulted from user settings |
| **Fiscal Year** | `FiscalYear` | `GJAHR` | `ZCRP_CERT` | Derived from posting date |
| **Certificate ID** | `CertificateId` | `CERTIFICATE_ID` | `ZCRP_CERT` | Generated on CREATE |
| **Status** | `Status` | `STATUS` | `ZCRP_CERT` | State machine §5 |
| **Staff ID** | `StaffId` | `STAFF_ID` | `ZCRP_CERT` | Auto: `PA0105` lookup |
| **Staff Name** | `StaffName` | `STAFF_NAME` | `ZCRP_CERT` | Auto: `PA0002` lookup |
| **Grade** | `Grade` | `GRADE` | `ZCRP_CERT` | Auto: `PA0001-STELL` |
| **Post Title** | `PostTitle` | `POST_TITLE` | `ZCRP_CERT` | Auto: `PA0001-PLANS` |
| **Start/End Date** | `StartDate`/`EndDate` | `BEGDA`/`ENDDA` | `ZCRP_CERT` | User input |
| **Working Days** | `NumberOfWorkingDays` | `NUM_WORK_DAYS` | `ZCRP_CERT` | Calculated: ENDDA-BEGDA |
| **Amount** | `CalculatedAmount` | `CALC_AMOUNT` | `ZCRP_CERT` | Days × Rate (from ZCRP_GRADE_CFG) |
| **GL Account** | `GlAccount` | `GL_ACCOUNT` | `ZCRP_CERT` | Lookup via ZCRP_GL_MAP or config |
| **JV Doc Number** | `JvBelnr` | `JV_BELNR` | `ZCRP_CERT` | Written by `PostJV` |
| **Fund (line)** | `Fonds` | `FONDS` | `ZCRP_BUDGETLN` | User input, FM native field |
| **Funds Center** | `Fictr` | `FICTR` | `ZCRP_BUDGETLN` | User input |
| **Commitment Item** | `Fipex` | `FIPEX` | `ZCRP_BUDGETLN` | User input, Conv: FIPEX |
| **WBS Element** | `WbsElement` | `WBS_ELEMENT` | `ZCRP_BUDGETLN` | User input, Conv: ABPSN |
| **Budget Available** | `BudgetAvailable` | `BUDGET_AVAILABLE` | `ZCRP_BUDGETLN` | Calculated: FM availability call |
| **Decision** | `Decision` | `DECISION` | `ZCRP_APRVL_HIST` | APPROVE / REJECT |
| **Comment** | `Apcomment` | `APCOMMENT` | `ZCRP_APRVL_HIST` | Free text |

---

# PART IV: OData CALL MAP (What the UI calls and when)

## 5. READ Operations

```
Screen 1 Load → GET CrpCertificateSet?$filter=CreatedBy eq 'JDUPONT'
                         &$expand=ToBudgetLines
                         &$orderby=CreatedAt desc

Screen 2 Load → GET CrpCertificateSet(Bukrs='UC01',Gjahr='2024',CertificateId='CRP-2024-001')
                         ?$expand=ToBudgetLines,ToAttachments,ToApprovalHistory

Rate Lookup   → GET CostRateSet?$filter=Grade eq 'P3'
```

## 6. WRITE Operations

```
Create Draft  → POST CrpCertificateSet
                     Body: {Bukrs, Gjahr, StaffId, Grade, StartDate, EndDate, Description...}
                     DPC: Resolves staff from SY-UNAME, generates CertificateId, Status='01'

Add Budget Ln → POST CrpBudgetLineSet
                     Body: {Bukrs, Gjahr, CertificateId, LineId, Fonds, Fictr, Amount...}

Upload File   → PUT CrpAttachmentSet
                     Content-Type: multipart (binary stream — media entity)

Submit        → POST /SubmitForApproval?CertificateId='CRP-2024-001'
                     DPC: Status 01→02, writes ZCRP_APRVL_HIST row, triggers WF

Simulate JV  → POST /SimulateJVPosting?CertificateId='CRP-2024-001'
                     DPC: FI BAPI simulation, returns JVSimulationResult

Post JV       → POST /PostJV?CertificateId='CRP-2024-001'&PostingDate='...'
                     DPC: BAPI_ACC_DOCUMENT_POST, writes JV_BELNR back to ZCRP_CERT

Post Allotment→ POST /PostAllotment?CertificateId='CRP-2024-001'
                     DPC: FM BAPI, Status→09 (terminal)
```

---

# PART V: STATE MACHINE & ACTION VISIBILITY

## 7. Status Lifecycle

```
[01] DRAFT
  ├── User can: Edit header, Add/Delete budget lines, Upload attachments
  ├── Toolbar: [Submit ✅] [Delete ✅]
  │
  ▼  SubmitForApproval
[02] SUBMITTED (Pending Approval)
  ├── User can: View only
  ├── Approver can: Approve → [03] / Reject → [05]
  ├── Toolbar: [Simulate JV ✅] (approver only)
  │
  ├──[05] REJECTED → User can revise → back to [01]
  │
  ▼  Approve decision
[03] APPROVED
  ├── Finance officer can: Post JV
  ├── Toolbar: [Simulate JV ✅] [Post JV ✅]
  │
  ▼  PostJV
[04] JV POSTED
  ├── JV_BELNR + JV_GJAHR filled in ZCRP_CERT
  ├── Toolbar: [Post Allotment ✅]
  │
  ▼  PostAllotment
[09] ALLOTMENT POSTED (Terminal)
  ├── Read only
  ├── Toolbar: [View JV Document ↗]
```

## 8. Button Visibility Logic (DPC_EXT must enforce — not just UI)

| Button | Visible when | Additional backend check |
| :--- | :--- | :--- |
| **Submit** | Status = `01` | User is creator |
| **Simulate JV** | Status = `02` or `03` | User has finance role |
| **Post JV** | Status = `03` | User has `Z_CRP_ACT` ACTVT=`POST` |
| **Post Allotment** | Status = `04` | Same as Post JV |
| **Edit (header)** | Status = `01` | User is creator |
| **Add Budget Line** | Status = `01` | User is creator |
| **Delete** | Status = `01` | User is creator |

> ⚠️ The DPC_EXT must **always re-validate** status on WRITE — never trust the UI to only show the right buttons.

---

# PART VI: AUTHORIZATION MODEL

## 9. Authorization Objects Required

| Object | Field | Value | Purpose |
| :--- | :--- | :--- | :--- |
| `S_SERVICE` | `SRV_NAME` | `Z_CRP_SRV` | OData service execution |
| `S_SERVICE` | `SRV_TYPE` | `HT` | HTTP handler type |
| `Z_CRP_ACT` *(new)* | `ACTVT` | `01`=Create, `03`=Display | Basic access |
| `Z_CRP_ACT` | `STATUS` | `02`,`03`,`04` | FI/FM transition permissions |
| `P_PERNR` | `AUTHC` | `R` | Staff self-lookup |

## 10. Role Architecture

| Role | Can Do | STATUS gate |
| :--- | :--- | :--- |
| **Requestor** | Create, Edit (Draft), Submit | ≤ 02 |
| **Approver** | View all, Approve/Reject, Simulate JV | ≤ 03 |
| **Finance Officer** | Post JV, Post Allotment | 03, 04 |
| **Read Only** | View all, no actions | — |

---

# PART VII: ERROR HANDLING

## 11. Standard Error Pattern (from HCM apps)

| Scenario | Backend response | UI behavior |
| :--- | :--- | :--- |
| Budget not available | `E/ZCRP/001: No budget for Fund &1` | Inline error on budget line row |
| Status conflict (wrong state for action) | `E/ZCRP/002: Action not allowed for status &1` | Toast / dialog with status explanation |
| FM period locked (YFMXCHKP) | `E/ZCRP/003: FM posting period &1/&2 is closed` | Blocking dialog, no retry |
| JV simulation fails | `E/ZCRP/004: Simulation error: &1` | Dialog with full BAPIRET2 message |
| Missing required budget line | `E/ZCRP/005: At least one budget line required` | Highlight Budget Lines tab |
| PERNR not found for user | `E/ZCRP/006: User &1 not linked to a personnel number` | Blocking error on create |
| Attachment too large | Client-side | Warn before upload (max size check) |

---

# PART VIII: INTEGRATION PATTERNS (FROM HCM KNOWLEDGE BASE)

## 12. Staff Resolution (reused from Personal Data app)

```abap
" Step 1: Resolve SY-UNAME → PERNR (from PA0105, same as HCM apps)
SELECT SINGLE pernr INTO lv_pernr
  FROM pa0105
  WHERE subty = '0001'
  AND   usrid = sy-uname
  AND   endda >= sy-datum.

" Step 2: Read PA0001 for Grade / PostTitle
SELECT SINGLE stell plans INTO (lv_grade, lv_post_title)
  FROM pa0001
  WHERE pernr = lv_pernr
  AND   endda >= sy-datum.
```

## 13. FM Availability Check (on budget line save)

```abap
" Called from CRPBUDGETLINESET_CREATE_ENTITY
CALL FUNCTION 'BAPI_FUNDSAVAIL_CHECK'
  EXPORTING
    fm_area        = lv_fikrs
    fund           = ls_line-fonds
    funds_center   = ls_line-fictr
    commitment_item= ls_line-fipex
    fiscal_year    = ls_line-gjahr
    amount         = ls_line-amount
    currency       = ls_line-currency
  IMPORTING
    available      = lv_available.

ls_line-budget_available = lv_available. " 'X' or ' '
```

## 14. FI Journal Voucher Posting (Function Import: PostJV)

```abap
" Called from POSTJV_FI in DPC_EXT
" 1. Read all budget lines for the certificate
" 2. Build BAPI accounting document
CALL FUNCTION 'BAPI_ACC_DOCUMENT_POST'
  EXPORTING
    documentheader = ls_header  " BLDAT, BUDAT, BUKRS, BKTXT
  TABLES
    accountgl      = lt_gl_lines " One per ZCRP_BUDGETLN row
    return         = lt_return.

" 3. Check lt_return for errors
" 4. On success: COMMIT WORK + update ZCRP_CERT-JV_BELNR, STATUS='04'
```

---

# PART IX: ARCHITECTURE DECISIONS SUMMARY

| Decision | Choice | Rationale |
| :--- | :--- | :--- |
| **Framework** | Custom SEGW (not ASR) | Relational 1:N data (lines) requires real entity CRUD — see full analysis below |
| **Logic class** | Dedicated `ZCL_CRP_PROCESS_REQ` | Mirrors Offboarding pattern — DPC_EXT stays thin |
| **Staging** | `ZCRP_CERT` with STATUS field | Same pattern as `zthrfiori_hreq` in HCM |
| **Staff resolution** | `PA0105` lookup | Proven pattern from HCM Personal Data app |
| **Budget check** | Real-time on line save | FM availability BAPI per line |
| **Attachments** | GOS/Media Entity | Proven in HCM apps, `CrpAttachment` marked HasStream |
| **Approval history** | Custom `ZCRP_APRVL_HIST` | Simple audit log — ASR covers this natively but adds overhead |
| **FI Posting** | `BAPI_ACC_DOCUMENT_POST` | Standard FI BAPI, UNESCO-wide standard |
| **FM Posting** | FM allotment BAPI | After JV, commits funds reservation |
| **Open item** | `ZCRP_GRADE_CFG` rate logic | Only 3 fields confirmed live — rate calc TBD |

> ⚠️ **The ASR Workflow option was evaluated and is NOT discarded.** A detailed head-to-head analysis including hybrid architecture options is documented in:  
> 📄 [`crp_asr_vs_segw_analysis.md`](./crp_asr_vs_segw_analysis.md)
>
> **Key takeaway**: ASR is architecturally viable and becomes the better choice if: (a) budget lines are simplified, (b) the approval workflow grows complex, or (c) a Hybrid model (SEGW for CRUD + ASR for Submit/Approve) is adopted in V2.
>
> **Implementation guard**: Do NOT hardcode `SAP_WAPI_START_WORKFLOW` directly in DPC_EXT. Delegate to `ZCL_CRP_PROCESS_REQ->SUBMIT_FOR_APPROVAL()` to keep the door open for switching to ASR-based triggering later.

---

*Sources: ZCL_Z_CRP_SRV_MPC source (RFC, 2026-03-10), z_crp_srv_config.json, automation_prompt.md, HCM app analyses (Offboarding + Personal Data).*
