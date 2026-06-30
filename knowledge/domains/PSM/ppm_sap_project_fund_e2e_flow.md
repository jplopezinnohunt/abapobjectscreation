---
name: E2E Flow — PPM/Salesforce → SAP project + fund creation (as the integration does it)
description: The end-to-end flow exactly as Salesforce/Core Planner (PPM) creates a project + its fund in SAP via MuleSoft — trigger, ordered inbound FM calls (BAPI_PROJECT_MAINTAIN, Y_BAPI_WBS_*, Y_FMKU_0050_CREATE_WITH_COMMIT, Y_BAPI_FUND_C5_ASSIGNMENT), the FINCODE=PSPID link, the disponible, and the financials sync back. Grounded in system_operating_model_rfc.md (RFC+job process discovery 2026-06-21) + unescore20-PPM-brain (other side).
type: project
domain: PSM / Project_System / Integration
evidence_tier: TIER_1
cross_links:
  - knowledge/system_operating_model_rfc.md
  - knowledge/domains/PSM/ps_project_replication_and_ki235.md
  - knowledge/domains/PSM/cost_recovery_avc_disponible_model.md
  - knowledge/domains/PSM/fund_management_sync_playbook.md
---

# E2E Flow — PPM/Salesforce → SAP (project + fund), as the integration does it

**Master of record = PPM (Salesforce / Core Planner).** SAP RECEIVES projects + funds; it does NOT originate
them. The transport is **MuleSoft** (a "synctrigger" background-job fleet — 17 distinct flows; visible in
TBTCO job discovery). SAP then serves financials back OUT to PPM. (Source: system_operating_model_rfc.md.)

```mermaid
flowchart TD
    subgraph PPM["PPM — Salesforce / Core Planner (MASTER)"]
      WP["Workplan / project defined + approved\n(outputs, sector, division, region, country, donor,\nfund type, funding, C/5 biennium)"]
    end
    WP -->|approve → sync trigger| MS["MuleSoft\n(synctrigger job fleet, 17 flows)\ndest: MULESOFT_PROD / MULESOFT_P01_IDOC"]

    subgraph SAP["SAP (D01/P01) — RECEIVES (inbound, in order)"]
      direction TB
      S1["1 · Project def + WBS structure\nBAPI_PROJECT_MAINTAIN\n(PSPID, profile, CO area, resp/appl,\nWBS hierarchy from C/5 outputs, BELKZ/PLAKZ=X, Release)"]
      S2["2 · WBS texts + custom fields\nY_BAPI_WBS_TEXT_MAINTAIN +\nY_BAPI_WBS_CUS_FIELD_UPDATE\n(USR00-04 = region/country/sector/division/CCAQ,\ndonor/source/exec/beneficiary)"]
      S3["3 · Fund create\nY_FMKU_0050_CREATE_WITH_COMMIT\n(FM_FUND_CREATE_RFC)\nFINCODE = PSPID  ·  type from YPS_FM_TYPE  ·  validity"]
      S4["4 · Fund → C/5 biennium assign\nY_BAPI_FUND_C5_ASSIGNMENT\n(YTFM_FUND_C5: fund × C5_ID × output)"]
      S5["5 · Budget / disponible (cost recovery)\nENTR / VALTYPE=B1 / BUDTYPE=3000\nat control address (e.g. FC NAI + TC)\n→ project becomes spendable (AVC)"]
      S1 --> S2 --> S3 --> S4 --> S5
    end
    MS -->|inbound write| S1

    SAP -->|financials sync OUT| MSO["MuleSoft (read flows)"]
    MSO -->|Y_BAPI_WBS_FINANCIAL_DATA_1\nY_BAPI_YPS8| PPM
```

## Step detail (the exact contract)

| # | Step | FM (inbound MuleSoft→SAP) | Key data |
|---|------|---------------------------|----------|
| 1 | Project + WBS structure | **`BAPI_PROJECT_MAINTAIN`** | PSPID, PROJECT_PROFILE, COMP_CODE/CONTROLLING_AREA/BUS_AREA, RESPONSIBLE_NO (TCJ04), APPLICANT_NO (TCJ05); WBS w/ `WBS_ACCOUNT_ASSIGNMENT_ELEMENT=X`+`WBS_PLANNING_ELEMENT=X`; hierarchy via `I_WBS_HIERARCHIE_TABLE`; then Release (REL). REFNUMBER = per-data-table row index. |
| 2 | WBS texts + custom fields | `Y_BAPI_WBS_TEXT_MAINTAIN`, `Y_BAPI_WBS_CUS_FIELD_UPDATE` | USR00=REGION, USR01=COUNTRY, USR02=SECTOR, USR03=DIVISION, USR04≈CCAQ; YYE_DONOR, YYE_TYP_SOU (source), YYE_EXEC, YYE_BENEF1 (sister/beneficiary). |
| 3 | Fund create | **`Y_FMKU_0050_CREATE_WITH_COMMIT`** (→ FM_FUND_CREATE_RFC) | **FINCODE = PSPID** (the 10-digit link); fund TYPE via YPS_FM_TYPE correlation; DATAB/DATBIS from workplan validity. |
| 4 | Fund → C/5 biennium | **`Y_BAPI_FUND_C5_ASSIGNMENT`** | Writes YTFM_FUND_C5 (FIKRS, FINCODE, C5_ID e.g. 43=2026-27, FM_OUTPUT). |
| 5 | Disponible (cost recovery) | budget entry (ENTR / VALTYPE B1 / BUDTYPE 3000) | At the control address (fund center e.g. NAI + commitment item TC); makes the project spendable under AVC (RIB). See cost_recovery_avc_disponible_model.md. |
| ← | Financials back to PPM | `Y_BAPI_WBS_FINANCIAL_DATA_1`, `Y_BAPI_YPS8` | SAP returns project financials (budget/commitment/actual) to PPM for monitoring. |

## Invariants
- **FINCODE = PSPID** (project ⇔ fund, 10-digit naming link). When a project is created a matching fund is provisioned.
- **PPM is master**; never create projects/funds standalone in SAP for production — they must originate in PPM.
- WBS hierarchy IS created via `BAPI_PROJECT_MAINTAIN` (MuleSoft does it daily) → nesting is achievable via the
  BAPI; reproduce the `I_WBS_HIERARCHIE_TABLE` payload MuleSoft sends.

## How our manual D01 replica maps to this flow
Steps 1–4 = the FM master sync + project/WBS create we ran (`fund_*`, `ps_project_sync.py`); step 5 = the
disponible we posted (`budget_assign_entr.py`). Replicating a project for a TEST = run this same flow for one
PSPID. For the canonical/automated path, drive `BAPI_PROJECT_MAINTAIN` with the MuleSoft payload shape (incl.
the hierarchy table) rather than hand-building.

## Open (to make it byte-exact)
Capture the actual MuleSoft request payloads (SOAMANAGER logical ports / the unescore20-PPM-brain integration
artifacts) to lock the exact field mapping + the `I_WBS_HIERARCHIE_TABLE` population for nested WBS.
