# [Architecture Decision] ZAW_CRP: ASR Workflow vs Custom SEGW Service

> **Domain**: PSM / Finance · **Decision Date**: 2026-03-10

> [!IMPORTANT]
> **ASR is a co-primary architecture option — do not discard it.** The initial objection about 1:N budget lines in XML was incorrect. XML was designed for hierarchical header+position data. The only remaining real blockers are FM real-time validation and domain ownership, both of which have clear mitigations.

---

## 1. Summary of the Decision

The CRP app was built using a **Custom SEGW OData service** (`Z_CRP_SRV`). However, during architecture analysis we explored whether the **ASR (HCM Processes & Forms) framework** could handle the CRP process instead. This document captures the full reasoning so the ASR route is not lost.

> [!IMPORTANT]
> This is **NOT** a closed decision. The ASR approach was assessed as architecturally viable for a future-generation or simplified CRP variant. The current SEGW approach was chosen for pragmatic, near-term delivery reasons — not because ASR is fundamentally wrong for this use case.

---

## 2. Understanding the Two Options

### Option A: Custom SEGW OData Service (Current Implementation)
The CRP app owns its full OData stack:
- **MPC_EXT** defines the schema: `CrpCertificate`, `CrpBudgetLine`, `CrpAttachment`, `CrpApprovalHistory`, `CostRate`.
- **DPC_EXT** implements all CRUD-Q methods + Function Imports (`SubmitForApproval`, `PostJV`, `PostAllotment`).
- **Custom DB Tables**: `ZCRP_CERT`, `ZCRP_BUDGETLN`, `ZCRP_APRVL_HIST`, `ZCRP_GRADE_CFG`.
- Approval state machine is fully custom: STATUS field + `ZCRP_APRVL_HIST`.
- Workflow trigger happens inside `SubmitForApproval` function import (calls `SAP_WAPI_START_WORKFLOW`).

### Option B: ASR Workflow Route (Evaluated but Not Implemented)
The CRP process would be registered as **ASR Scenarios** in `T5ASRSCENARIOS` and exposed via the existing `ZHR_PROCESS_AND_FORMS_SRV` OData service.

Architecture under this model:
- **No new OData entities** for the certificate header — the payload is a `service_datasets` name-value bag sent via `EXECUTE_ACTION`.
- **Logic Class** (e.g., `ZCL_CRP_ASR_PROCESSOR`) implements `IF_HRASR00GEN_SERVICE~DO_OPERATIONS`.
- **ASR Buffer** (`T5ASRDATAVAR` / XML snapshots) serves as the staging/parking layer instead of `ZCRP_CERT`.
- **`T5ASRPROCESSES`** tracks the GUID / lifecycle of each request.
- JV posting and FM allotment would be triggered **inside the workflow task** after approval, not as OData Function Imports.

---

## 3. The CRP Process — How it Maps to ASR

The CRP lifecycle maps naturally to the ASR paradigm:

| CRP Step | ASR Equivalent |
| :--- | :--- |
| Create Draft | `EXECUTE_ACTION` → parks data in `T5ASRDATAVAR` XML blob |
| Submit for Approval | Status transition in ASR process; triggers WF task for approver |
| Approver reviews | WF task reads XML snapshot from ASR buffer via `GET_REQUEST_FORM_DATA` |
| Approved → Post JV | WF final step calls FM inside `DO_OPERATIONS` or a WF task |
| Rejected → Revise | ASR reopen flow; XML snapshot retained in vault |
| Audit Trail | `T5ASRDATAVAR` ledger — immutable, available even after deletion |

The **Approval History** (`ZCRP_APRVL_HIST`) is essentially what `T5ASRPROCESSES` does natively in ASR.

---

## 4. Head-to-Head Comparison

| Dimension | Custom SEGW (current) | ASR Workflow (evaluated) |
| :--- | :--- | :--- |
| **Budget Lines (1:N)** | ✅ Full entity CRUD via `CrpBudgetLineSet` | ✅ **Feasible** — XML supports repeating node groups (e.g., `<BudgetLines><Line seq="1"><FONDS>...</FONDS>...</Line></BudgetLines>`). Logic class parses the array. |
| **FM Integration** | ✅ Real-time BAPI check per line on save | ❌ Budget check deferred to WF execution; no real-time feedback |
| **Attachments** | ✅ Media Entity with GOS (`CrpAttachment`) | ⚠️ Possible via GOS attachment on ASR process, but not native to scenarios |
| **UI Flexibility** | ✅ Full control over entity shapes / $expand / $filter | ✅ Fields change in UI without touching OData metadata |
| **Workflow** | ⚠️ Must call `SAP_WAPI_START_WORKFLOW` manually | ✅ Native — WF is the framework's spine |
| **Approval History** | ⚠️ Must maintain `ZCRP_APRVL_HIST` manually | ✅ `T5ASRPROCESSES` + `T5ASRDATAVAR` provides this out of the box |
| **Audit / Staging** | ⚠️ STATUS field only — no XML snapshot of previous states | ✅ Every intermediate state is captured as immutable XML |
| **Zero-new-OData** | ❌ New service required | ✅ Reuse `ZHR_PROCESS_AND_FORMS_SRV` |
| **FI JV Posting** | ✅ Triggered via Function Import (user-initiated) | ⚠️ Triggered inside WF task (background, not user-controlled) |
| **Dev Effort (now)** | ⚠️ Large: all DPC_EXT methods must be written | ✅ Smaller footprint: one logic class + config |
| **Maintenance** | ⚠️ OData schema changes require regen cycle | ✅ Field changes are metadata-only |
| **Pattern fit** | ✅ Matches PSM/Finance patterns (relational data) | ✅ Matches HCM patterns (approvals + staging) |

---

## 5. Critical Insight: ASR CRUD Is Already Built Into SAP Core

> [!IMPORTANT]
> The standard CRUD operations that the CRP app needs are **already provided by the ASR framework's native OData service** — they do not need to be coded. This is the decisive advantage over Custom SEGW.

| What CRP Needs | SEGW Approach | ASR Core (already exists) |
| :--- | :--- | :--- |
| List all my certificates | `CRPCERTIFICATESET_GET_ENTITYSET` (must code) | `GET_PROCESS_LIST` — built-in, returns all parked requests for user |
| Read one certificate | `CRPCERTIFICATESET_GET_ENTITY` (must code) | `GET_PROCESS_INSTANCE` — reads XML blob from `T5ASRDATAVAR` |
| Create draft | `CRPCERTIFICATESET_CREATE_ENTITY` (must code) | `EXECUTE_ACTION` — parks data into `T5ASRDATAVAR` as XML |
| Edit draft | `CRPCERTIFICATESET_UPDATE_ENTITY` (must code) | `EXECUTE_ACTION` (same endpoint, different operation code) |
| Status tracking | Custom STATUS field + state machine (must code) | `T5ASRPROCESSES` — framework manages lifecycle natively |
| Audit history | `ZCRP_APRVL_HIST` table (must code + maintain) | `T5ASRDATAVAR` — immutable XML snapshots, framework-managed |
| WF trigger | `SAP_WAPI_START_WORKFLOW` call in DPC_EXT (must code) | Native — WF fires from `DO_OPERATIONS` via framework |
| Budget validation | Call in DPC_EXT per-entity method (must code) | Call inside `DO_OPERATIONS` on screen action — same effort |

**The ONLY custom artifact needed in ASR is one ABAP class** implementing `IF_HRASR00GEN_SERVICE~DO_OPERATIONS`. Scenario registration is pure configuration in `T5ASRSCENARIOS` (customizing, no coding). Compare this to Custom SEGW which requires coding **11+ DPC_EXT methods** (see `crp_management.md` Part IX).

---

## 6. Why ASR Was Not Chosen for V1 (Pragmatic Reasons Only)


1. ~~**Budget Lines cannot be represented in XML.**~~ **NOT a blocker.** XML is a hierarchical format by design — a `<CRP>` root with `<Header>` + `<Positions><Line seq="1">...` children is exactly what XML does natively. The `T5ASRDATAVAR` vault stores arbitrary XML blobs. The logic class `DO_OPERATIONS` iterates `<Line>` nodes exactly as a table loop. HCM already does this for multi-dependent scenarios in `ZHR_BIRTH_CHILD`. **This objection is withdrawn.**

2. **FM validation can be done on screen action, not only in WF.** The `BAPI_FUNDSAVAIL_CHECK` call does not need to run per-keystroke. It can fire when the user clicks a dedicated **"Check Budget"** button or on the Submit action itself — a synchronous call that returns immediate on-screen feedback. The result (`BudgetAvailable = X / ' '`) is then embedded in the XML payload before parking in `T5ASRDATAVAR`. If the check fails, the park/WF trigger is simply blocked at that point. A second check in the WF execution step acts as a safety net (FM availability can change between submission and approval). This is a **design consideration, not a fundamental ASR blocker**.

3. ~~**Domain ownership risk.**~~ **NOT a blocker.** ASR ("HCM Processes & Forms") is misleadingly named — it is a **generic SAP framework** for any domain that needs form-based data collection, parking, approval workflow, and audit trails. UNESCO uses it heavily in HCM, but SAP designed it domain-agnostic. A PSM scenario `ZPSM_CRP_CERTIFICATE` in `T5ASRSCENARIOS` is structurally identical to an HCM scenario. No coupling, no shared transport risk. **This objection is withdrawn.**

4. **Sprint delivery pressure.** Custom SEGW mirrors patterns the team already knows. Introducing ASR for PSM is a new pattern with a learning curve.

---

## 6. Why ASR Is Now a Stronger Option (Revised)

> [!IMPORTANT]
> With budget lines confirmed viable in XML, the ASR objections reduce to **only 2 real blockers** (FM real-time check + domain ownership), both of which have mitigations. The ASR / Hybrid route should be treated as **co-equal** to the current SEGW-only approach.

1. **Budget lines: CONFIRMED VIABLE in ASR XML.** Repeating `<BudgetLine>` nodes can be parsed in `DO_OPERATIONS`. No blocker here.

2. **Audit trail is a major ASR advantage.** The current SEGW `STATUS` field records the final state only. `T5ASRDATAVAR` records **every intermediate XML snapshot** — what data looked like at submission, what the approver saw, what was revised. This is a material difference for UNESCO's audit requirements.

3. **Workflow complexity future-proofing.** If UNESCO adds parallel approval, delegation, or SLA escalation, ASR's native WF integration is significantly lighter than maintaining `SAP_WAPI_*` calls in DPC_EXT.

4. **CRP Lite variant.** For field offices that only need to notify Finance (no FM validation), a pure ASR scenario with no relational entity is ideal.

---

## 7. Hybrid Architecture (Best of Both Worlds)

A hybrid model is fully feasible:

```
Browser (ZAW_CRP)
    │
    ├── CRUD Operations (Lines, Attachments) ──►  Z_CRP_SRV (Custom SEGW)
    │                                             ZCL_Z_CRP_SRV_DPC_EXT
    │                                             ZCRP_CERT / ZCRP_BUDGETLN
    │
    └── Submit / Approve Actions ──────────────►  ZHR_PROCESS_AND_FORMS_SRV (ASR)
                                                  ZCL_CRP_ASR_PROCESSOR
                                                  T5ASRPROCESSES (audit log)
                                                  SAP Workflow (WS98100032 or custom)
```

**How it works:**
1. The SEGW service handles all CRUD (draft creation, line editing, attachments).
2. When the user clicks **Submit**, the BSP app calls **`EXECUTE_ACTION`** on the ASR service, passing only the `CertificateId` as a key.
3. The ASR logic class reads the `ZCRP_CERT` record, takes an XML snapshot into `T5ASRDATAVAR` (creating the audit trail), and fires the SAP Workflow.
4. The Workflow task's approval/rejection is handled natively by ASR.
5. On approval, the WF task calls back a function module/method that executes `PostJV` + `PostAllotment` logic.

**Benefits of Hybrid:**
- Real-time FM validation preserved (SEGW handles data entry).
- Native audit trail for the submission/approval lifecycle (ASR).
- No encoding of budget lines into name-value pairs.
- Separation of concerns: Finance edits → SEGW; HR-like approval → ASR.

---

## 8. Pros & Cons by Option — and Why We Select

### Option A: Pure Custom SEGW
| | |
|:---|:---|
| ✅ **Pro** | Team already knows the pattern — fastest V1 delivery |
| ✅ **Pro** | Full OData entity control: `$filter`, `$expand`, `$orderby` on any field |
| ✅ **Pro** | FM availability check fires per-line in real time as user types |
| ⚠️ **Pro** | Attachments via `CrpAttachment` Media Entity (HasStream=true) — full control of stream, works with GOS/ArchiveLink |
| ❌ **Con** | Must hand-code 11+ DPC_EXT methods — large codebase to build and maintain |
| ❌ **Con** | No built-in audit snapshot — `STATUS` field only captures current state, not history |
| ❌ **Con** | WF trigger requires manual `SAP_WAPI_START_WORKFLOW` call — tightly coupled to this app |
| ❌ **Con** | **Each new Finance workflow requires a new full SEGW project from scratch** — not reusable |
| ❌ **Con** | Transport footprint is large: MPC/DPC classes, SEGW project, ICF node, DB tables |

---

### Option B: Hybrid (SEGW Data Entry + ASR Approval Leg)
| | |
|:---|:---|
| ✅ **Pro** | FM validation per-line via SEGW call — real-time feedback preserved |
| ✅ **Pro** | ASR provides native WF routing, approval history, and XML audit vault for the submit/approve phase |
| ✅ **Pro** | Separation of concerns: Edit = OData; Approve = ASR |
| ✅ **Pro** | ASR approval leg is domain-agnostic and **reusable for future Finance workflows** |
| ✅ **Pro** | Attachments on SEGW side via `CrpAttachment` Media Entity; WF task reads same GOS object |
| ⚠️ **Con** | Two backend systems must be kept in sync (SEGW data + ASR process GUID) |
| ⚠️ **Con** | Higher initial design complexity — two patterns running in parallel |
| ⚠️ **Con** | Requires the team to learn ASR for the approval leg |

---

### Option C: Pure ASR
| | |
|:---|:---|
| ✅ **Pro** | **Smallest codebase** — one logic class (`DO_OPERATIONS`), scenario config only |
| ✅ **Pro** | Framework handles all CRUD natively (`GET_PROCESS_LIST`, `GET_PROCESS_INSTANCE`, `EXECUTE_ACTION`) |
| ✅ **Pro** | Full audit trail: every intermediate XML snapshot stored in `T5ASRDATAVAR` automatically |
| ✅ **Pro** | Native WF integration — no `SAP_WAPI_*` calls needed in custom code |
| ✅ **Pro** | **Maximum future-proofing**: any new Finance/PSM workflow is a new Scenario ID + logic class — zero new OData infrastructure |
| ✅ **Pro** | Domain-agnostic — PSM, HCM, or any domain can register scenarios independently |
| ✅ **Pro** | **Attachments via GOS on process instance** — ASR process (`HRASR00_PROCESS` + GUID) is a standard GOS object. HCM apps already attach documents this way. Same proven pattern, zero new infrastructure. |
| ✅ **Pro** | **FM validation UX fully preserved via UI events** — the check can be wired to any UI event (field blur, row step change, explicit button) as a direct OData call. The UI framework is agnostic to whether the backend is SEGW or ASR. |
| ⚠️ **Con** | XML parsing for budget lines requires custom iteration in `DO_OPERATIONS` — one-time effort |
| ⚠️ **Con** | New pattern for the team — learning curve on scenario configuration and `IF_HRASR00GEN_SERVICE` |

---

### Why We Select: **Pure ASR (target) / Hybrid (pragmatic V1.5)**

> **The decisive argument: future workflow extensibility.**
>
> If we build CRP in Custom SEGW, every future Finance workflow (travel requests, purchase requisition approvals, budget amendments) requires a full new SEGW project — MPC, DPC, ICF node, DB tables, 11+ methods. Each one is a standalone island.
>
> If we build on ASR, **every future workflow is just a new Scenario ID + one logic class**. The infrastructure (OData service, process list UI, audit vault, WF engine) already exists and is shared. This is the standard SAP extensibility model for form-based approval workflows.

| Criterion | Pure SEGW | Hybrid | **Pure ASR** |
| :--- | :---: | :---: | :---: |
| Delivery speed (fresh start) | ❌ Slowest (11+ methods) | ⚠️ Medium | ✅ **Fastest** (1 class + config) |
| Delivery speed (CRP V1 — already in SEGW) | ✅ Continue existing | ⚠️ Refactor needed | ⚠️ Rework needed |
| Codebase size | ❌ Large | ⚠️ Medium | ✅ Minimal |
| Audit trail | ❌ None | ✅ For WF leg | ✅ Full |
| Future workflow reuse | ❌ None | ✅ WF leg | ✅ **Full platform** |
| FM validation UX | ✅ Per-line | ✅ Per-line | ✅ **Per-line via UI event** |
| **Attachments** | ⚠️ Media Entity (custom code) | ✅ Media Entity + GOS | ✅ GOS on process GUID (proven in HCM) |
| WF complexity support | ❌ Manual | ✅ Native | ✅ Native |
| **Recommended** | ⚠️ Complete V1 as-is | ✅ V2 target | ✅ **All future workflows** |



> [!IMPORTANT]
> Do NOT hard-code the `SubmitForApproval` function import to call `SAP_WAPI_START_WORKFLOW` directly in DPC_EXT.  
> Instead, delegate to `ZCL_CRP_PROCESS_REQ->SUBMIT_FOR_APPROVAL()`.  
> This keeps the door open to **replacing the WF triggering mechanism** (e.g., switching to ASR-based triggering in V2 without touching the OData layer).

---

*Sources: `zaw_crp_architecture.md` (Part IX decisions), `crp_management.md` (full schema), `asr_framework_deep_dive.md`, HCM app analyses (Personal Data, Family Management, Address Management). Reconstructed from architectural conversations, 2026-03-10.*
