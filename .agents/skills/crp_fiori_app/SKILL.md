---
name: CRP Fiori App (Cost Recovery Program)
description: >
  Architecture and implementation guide for the UNESCO CRP (Cost Recovery Program)
  Fiori application. ASR Hybrid model: Z_CRP_SRV OData for CRUD + FM validation,
  ASR framework for approval workflow (Submit→Approve→Post). 19 open implementation
  items spanning DPC_EXT, ASR service, workflow config, and infrastructure.
domains:
  functional: [FI, PSM]
  module: [FI, FM]
  process: [B2R]
---

# CRP Fiori App — Cost Recovery Program

## Purpose

The CRP app manages **UNESCO cost recovery certificates** — the formal process by which
one organizational unit charges another for shared services (staff, consultants, facilities).

**Business flow**: Create Certificate → Add Budget Lines → Simulate JV → Submit for Approval
→ Approve/Reject → Post JV + Allotment → Close

---

## NEVER Do This

> [!CAUTION]
> - **NEVER bypass FM availability check** — every budget line must validate against FM before posting
> - **NEVER post JV/Allotment without workflow approval** — ASR framework enforces this
> - **NEVER hardcode fund codes** — use 10-digit glue rule (PRPS.POSID starts with FINCODE)
> - **NEVER skip SIMULATEJVPOSTING_FI** — this is the real-time FM feedback on screen events
> - **NEVER create the app without understanding the 3 posting streams** — see fi_domain_agent cost recovery section

---

## Architecture: ASR Hybrid Model

```
┌─────────────────────────────────────────────────────────────┐
│                    BSP / UI5 Frontend                        │
│  ZAW_CRP (BSP App — currently in $TMP, needs ZCRP package) │
│  ├── Certificate List → CRPCERTIFICATESET_GET_ENTITYSET     │
│  ├── Certificate Detail → CRPCERTIFICATESET_GET_ENTITY      │
│  ├── Budget Lines → CRPBUDGETLINESET (CRUD)                 │
│  ├── Attachments → CRPATTACHMENTSET (media stream)          │
│  └── Submit → EXECUTE_ACTION(ZPSM_CRP_CERTIFICATE)         │
├─────────────────────────────────────────────────────────────┤
│                    Z_CRP_SRV OData Service                   │
│  ZCL_Z_CRP_SRV_DPC_EXT (DPC Extension)                     │
│  ├── CRUD: Certificate, BudgetLine, Attachment entities      │
│  ├── FM Validation: SIMULATEJVPOSTING_FI (dry-run)          │
│  ├── FI Posting: POSTJV_FI (triggered by WF task)           │
│  └── FM Posting: POSTALLOTMENT_FI (triggered by WF task)    │
├─────────────────────────────────────────────────────────────┤
│                    ASR Framework (Approval)                   │
│  Scenario: ZPSM_CRP_CERTIFICATE (T5ASRSCENARIOS)           │
│  Processor: ZCL_CRP_ASR_PROCESSOR (IF_HRASR00GEN_SERVICE)  │
│  Workflow: WS_ZCRP_CERT (SWDD — Submit→Approve/Reject→Post)│
│  History: T5ASRPROCESSES (native read, replaces custom)     │
└─────────────────────────────────────────────────────────────┘
```

---

## Cost Recovery Posting Schema (from Session #016)

3 streams, each with 2-line JV entries:

| Stream | BUKRS | BLART | DR GL | CR GL | CR FONDS |
|--------|-------|-------|-------|-------|----------|
| STAFF COST RECOVERY | IIEP | JV | 6046013/6046014 | 7034011 | P3638PSF99/638PSF9000 |
| ITF/COST RECOVERY | IIEP | R1 | 6046013/6046014 | 7022020 | 1143PRVxxx |
| Cost Recovery (field) | UNES | R1 | 6046013/6046014 | 7046013 | 633CRP9003 |

- FIPEX 11 = staff costs, FIPEX 13 = consultants
- UNES: GSBER PFF (debit) → OPF (credit)
- 633CRP9003 = shared CRP pool (87 field offices)
- IIEP: Charge divisions (TEC/KMM/TRA/RND) → ADM receives revenue

See `project_cost_recovery_analysis.md` for full detail.

---

## 19 Open Implementation Items

### Data Layer — Z_CRP_SRV DPC_EXT (Items 1-9)

| # | Method | Purpose | Status |
|---|--------|---------|--------|
| 1 | `CRPCERTIFICATESET_GET_ENTITYSET` | List certificates with Status/Date filter | 🔴 Pending |
| 2 | `CRPCERTIFICATESET_GET_ENTITY` | Single certificate read | 🔴 Pending |
| 3 | `CRPCERTIFICATESET_CREATE_ENTITY` | Draft creation → `ZCRP_CERT` table | 🔴 Pending |
| 4 | `CRPCERTIFICATESET_UPDATE_ENTITY` | Edit in Draft state only | 🔴 Pending |
| 5 | `CRPBUDGETLINESET_*` | Full CRUD with FM availability check per line | 🔴 Pending |
| 6 | `CRPATTACHMENTSET_*` | Create/read/delete media stream | 🔴 Pending |
| 7 | `SIMULATEJVPOSTING_FI` | FI dry-run BAPI — real-time FM feedback on screen | 🔴 Pending |
| 8 | `POSTJV_FI` | FI JV creation (triggered by WF task after approval) | 🔴 Pending |
| 9 | `POSTALLOTMENT_FI` | FM allotment commitment (triggered by WF task) | 🔴 Pending |

### ASR Service Layer (Items 10-12)

| # | Task | Purpose | Status |
|---|------|---------|--------|
| 10 | Register `ZPSM_CRP_CERTIFICATE` in `T5ASRSCENARIOS` | ASR scenario registration | 🔴 Pending |
| 11 | Create `ZCL_CRP_ASR_PROCESSOR` implementing `IF_HRASR00GEN_SERVICE` | Approval processor class | 🔴 Pending |
| 12 | Configure `WS_ZCRP_CERT` in SWDD | Workflow: Submit → Approve/Reject → Post | 🔴 Pending |

### Deprecations — Move to ASR (Items 13-14)

| # | Old Endpoint | Replacement | Status |
|---|-------------|-------------|--------|
| 13 | ~~SUBMITFORAPPROVAL_FI~~ | `EXECUTE_ACTION` on ASR scenario | 🟡 Design done |
| 14 | ~~CRPAPPROVALHISTORYSET~~ | `T5ASRPROCESSES` native read | 🟡 Design done |

### Infrastructure (Items 15-19)

| # | Task | Purpose | Status |
|---|------|---------|--------|
| 15 | Move `ZAW_CRP` BSP from `$TMP` to `ZCRP` package | Transportability | 🔴 Pending |
| 16 | Wire Submit button → `EXECUTE_ACTION(ZPSM_CRP_CERTIFICATE)` | ASR integration | 🔴 Pending |
| 17 | Wire budget line events → `SIMULATEJVPOSTING_FI` | Real-time FM feedback | 🔴 Pending |
| 18 | Confirm/create `ZCRP_CERT` and `ZCRP_GL_MAP` tables | Data model | 🔴 Pending |
| 19 | Authorization: `S_SERVICE` for `Z_CRP_SRV` + custom `Z_CRP_ACT` | Security | 🔴 Pending |

---

## Key Design Decisions

### 1. ASR vs Custom Approval
**Decision**: Use ASR (Approval Service Requestor) framework, NOT custom approval endpoints.
**Why**: ASR provides audit trail (T5ASRPROCESSES), standard workflow integration (SWDD),
and substitution rules out of the box. Custom approval = reinventing the wheel.

### 2. JV Posting via Workflow Task
**Decision**: POSTJV_FI and POSTALLOTMENT_FI are triggered by WF task completion, NOT by UI button.
**Why**: Ensures posting only happens AFTER approval. UI cannot bypass workflow.

### 3. SIMULATEJVPOSTING_FI on Budget Line Events
**Decision**: Real-time FM availability check fires on every budget line add/change.
**Why**: Users need immediate feedback if budget is exceeded, not at submit time.

### 4. Z_CRP_SRV keeps CRUD, ASR handles lifecycle
**Decision**: OData service handles data operations. ASR handles state transitions.
**Why**: Clean separation — CRUD is stateless, approval is stateful.

---

## Custom Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `ZCRP_CERT` | Certificate master | CERT_ID, STATUS, BUKRS, FONDS, FISTL, AMOUNT, CREATED_BY, CREATED_AT |
| `ZCRP_GL_MAP` | GL account mapping per stream | STREAM, BUKRS, DR_HKONT, CR_HKONT, DR_FONDS, CR_FONDS |

**Status**: 🔴 Tables need to be confirmed/created in D01.

---

## BAPIs Used

| BAPI | Purpose | Called By |
|------|---------|----------|
| `BAPI_ACC_DOCUMENT_POST` | Create JV document | POSTJV_FI (DPC method) |
| `BAPI_ACC_DOCUMENT_CHECK` | Simulate JV (dry-run) | SIMULATEJVPOSTING_FI |
| `FMRP_BUDGET_POST` or FM BAPI | Post FM allotment | POSTALLOTMENT_FI |
| `BAPI_TRANSACTION_COMMIT` | Commit after posting | All posting methods |

---

## Integration Points

- **FI Domain**: Golden Query validates posting against GL (see `fi_domain_agent`)
- **PSM Domain**: FMIFIIT OBJNRZ links posted docs to WBS elements (see `psm_domain_agent`)
- **Class Deployment**: DPC_EXT class via `sap_class_deployment` skill
- **ADT API**: Source code write/activate via `sap_adt_api` skill
- **WebGUI**: SEGW service generation via `segw_automation` skill
- **Process Mining**: CRP lifecycle events feed pm4py (see `sap_process_mining`)

---

## Known Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `BAPI_ACC_DOCUMENT_CHECK returns errors` | Invalid GL/fund combination | Check ZCRP_GL_MAP mapping matches actual chart of accounts |
| `ASR scenario not found` | T5ASRSCENARIOS not registered | Run Item #10 first |
| `Workflow doesn't trigger` | WS_ZCRP_CERT not activated in SWDD | Activate workflow + event linkage |
| `FM availability check fails` | Budget exhausted | Expected behavior — show user the remaining budget |
| `$TMP package can't transport` | BSP still in temporary package | Item #15: move to ZCRP package |

---

## Deployment Order

```
Phase 1: Data Model
  #18 → Create ZCRP_CERT + ZCRP_GL_MAP tables
  #15 → Move BSP from $TMP to ZCRP package

Phase 2: OData CRUD
  #1-6 → DPC_EXT methods (Certificate + BudgetLine + Attachment)
  #7 → SIMULATEJVPOSTING_FI (dry-run)

Phase 3: ASR + Workflow
  #10 → Register ASR scenario
  #11 → Create ASR processor class
  #12 → Configure SWDD workflow
  #13-14 → Deprecate old approval endpoints

Phase 4: Integration
  #16-17 → Wire UI buttons to ASR + FM simulation
  #8-9 → Posting methods (triggered by WF)
  #19 → Authorization config
```

---

## You Know It Worked When

1. Certificate CRUD works via OData `$metadata` test
2. Budget line add triggers FM simulation and shows remaining budget
3. Submit fires ASR workflow (visible in SWIA)
4. Approval triggers JV + Allotment posting (visible in BKPF + FMIFIIT)
5. Full cycle: Create → Lines → Submit → Approve → Posted → shows in Golden Query
