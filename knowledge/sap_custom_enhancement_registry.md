# UNESCO SAP Custom Enhancement Registry (Levels 3 & 4)

This document serves as the master registry of custom ABAP enhancements (User-Exits, CMOD Projects, and BAdIs) discovered during the analysis of the UNESCO SAP system (P01).

> 🖥️ **Living companion (the visual layer):** [`companions/fi_substitutions_custom_code_companion_v1.html`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/companions/fi_substitutions_custom_code_companion_v1.html) — renders this registry as 8 tabs (16-step chain · YRGGBS00 exits · BASU · XREF tagging · BCM/Payment custom code · YXUSER backdoor · tables & incidents). Keep registry ↔ companion aligned (0 contradictions); the `.md` is the source of truth, the `.html` is the snapshot.

## 1. Fund Management (FM) & Posting Derivation

### 1.1 `FMDERIVE` Strategy (Global)
*   **Include**: [`ZXFMDTU02`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/ZXFMDTU02_RPY.abap)
*   **Trigger**: Central Posting/Requisition derivation.
*   **Logic**: 
    - Hardcoded G/L to Fund/FC mappings (e.g., G/L `7042011` force-mapped to `BOC`).
    - Custom business area (`GSBER`) logic for specific fund types (`114`, `115`).
    - Blocking procurement postings for historical funds (`149*`).
*   **Project**: `ZFMACCHK`
*   **Technical Autopsy**: [`posting_derivation_technical_autopsy.md`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/EXTENSIONS/posting_derivation_technical_autopsy.md)

### 1.2 Account Assignment Validation (FM Side)
*   **Logic**: Mandates either a Cost Center or WBS and validates the link between the Fund ID and the WBS Element ID.
*   **Enforcement**: Specific Business Area (GEF, PFF, MBF, OPF) is forced based on the `FMFINCODE-TYPE`.
*   **Technical Autopsy**: [`fm_validation_technical_autopsy.md`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/EXTENSIONS/fm_validation_technical_autopsy.md)

## 2. Project System (PS) & Materials Management (MM)

### 2.1 Project Master Validation
*   **Include**: [`YJWB001`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/YJWB001_RPY.abap) (within `ZXCN1U01`)
*   **Logic**: Validates custom "User Fields" for WBS Elements (`USR00` to `USR04`) against UNESCO-specific verification tables (`YUSR00` - `YUSR04`).
*   **Fields**: Region, Sub-region, Sector, Division, CCAQ Code.

### 2.2 WBS Element Enhancements
*   **Includes**: `YELAM001`, `YELAM003` (within `ZXCN1U21/22`)
*   **Description**: Likely handles the "Allotment" logic for project budget ceiling controls.

### 2.3 PO Release Strategy Bypass (MM)
*   **Include**: [`ZXM06U22`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/ZXM06U22_RPY.abap)
*   **Logic**: 
    - Forced manipulation of **Material Group (`MATKL`)** to 'X' or 'Y' for specific Purchasing Orgs (`UNES`, `ICTP`) and Document Types (`CS`, `205D`, `COMM`, etc.).
    - Purpose: Bypasses standard release checks for specific materials or forces a specific approval path.
    - Integration: Calls `Z_RFC_EXT_DEST_PO_RELEASE` for external workflow triggering.

## 3. Travel Management (TV)

### 3.1 Travel Header & Dependant Checks
*   **Include**: [`ZXTRVU03`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/ZXTRVU03_RPY.abap)
*   **Logic**: Checks for overlapping travel periods and validates "Dependant" mandatory status.

### 3.2 Account Assignment Validation
*   **Include**: [`ZXTRVU05`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/ZXTRVU05_RPY.abap)
*   **Logic**: **Dual Assignment Block**: Prevents specifying both a Cost Center AND a WBS element in a travel request (Message `ZFI:009`).

## 4. BW Data Extraction (BI Integration)

### 4.1 Transactional & Master Data Enrichment
*   **Includes**: [`ZXRSAU01`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/ZXRSAU01_RPY.abap), [`ZXRSAU02`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/ZXRSAU02_RPY.abap)
*   **Logic**: enrichment of FM/PS data sources with **Analytical Posting Dates**, **Donors**, **Sectors**, and **Support Cost (%)**.

## 5. Master Data Enhancements

### 5.1 Fund Master (`FMMD`)
*   **Includes**: [`ZXFMFUNDU01-04`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/ZXFMFUNDU01_RPY.abap)
*   **Logic**: Integrates the "IBF Management" (Integrated Budget Framework). Uses class `YCL_FM_FUND_IBF_BL` to manage custom fields on the Fund master record.
*   **Technical Autopsy**: [`ibf_metadata_technical_autopsy.md`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/EXTENSIONS/ibf_metadata_technical_autopsy.md)

## 6. Applications & Cockpits
*   **FM Cockpit**: `YFM_COCKPIT` (Manages AVC Rules and Re-initialization).
*   **YFM1 Report**: Aggregate budget/expenditure report (Class `YCL_YFM1_BCS_BL`).
*   **YPS8 Report**: Specialized integrated FM-PS report (Class `YCL_YPS8_BCS_BL`).

## 7. Custom Table Key
*   `YUSR00` - `YUSR04`: Project validation master data.
*   `YFMXCHKP` / `YFMXCHK`: Posting check parameters and windows.
*   `YTFM_WRTTP_GR`: Value type groupings for reporting.
*   `YTFM_FUND_C5`: Strategic (IBF) fund metadata (`ZZIBF`, `ZZOUTPUT`).
*   `YBW_PSCOUNTRY`: ISO-to-UNESCO Country Mapper.

## 8. Finance Validations & Substitutions (GGB0/GGB1)

### 8.1 Central Routine Pool: `YRGGBS00`
*   **Transaction**: `GGB0` (Validation), `GGB1` (Substitution)
*   **Role**: Serves as the global exit container for FI postings.
*   **Key User Exits**:
    - `U910`: Business Area Substitution (calls `YCL_FI_ACCOUNT_SUBST_READ`).
    - `U901/U902`: Bank Type/Payment Currency manipulation.
    - `U911/U912`: Assignment/Reference manipulation for specific institutes.
    - `UXR1/UXR2`: Reference field (XREF1/XREF2) auto-population.
    - `UZLS`: Payment Method force-override.
    - `UGLS`: G/L Account substitution for internal transfers.

### 8.2 Global Validation Logic: `UNES`
*   **Context**: Company Code `UNES`.
*   **Logic**:
    - **GSBER Check**: Restricts Business Area to `GEF`, `MBF`, `OPF`, or `PFF` (Msg `ZFI:015`).
    - **Fund Check**: Blocks postings on specific funds based on fiscal year/BFM requirements (Msg `ZFI:024`).
    - **G/L Account Check**: Validates `HKONT` for specific document types (e.g., `R1` only for certain accounts, Msg `ZFI:021`).
    - **Payment Details**: Mandates "Partner Bank Type" for specific beneficiaries (Msg `ZFI:012`).

### 8.3 Institute-Specific Validations
*   **IBE/IIEP/ICTP/UBO**:
    - Each institute has a dedicated `VALID` ID (e.g., `UBO`, `ICTP`) in `GB93`.
    - **Business Area Enforcement**: 
        - `ICTP` -> Force `PFF`.
        - `IIEP` -> Force `PAR`, `IBA`, or `FEL`.
        - `UBO` -> Force `GEF`, `MBF`, `OPF`, or `PFF`.

## 9. Custom Business Area Substitution (`YFI_BASU_MOD`)

### 9.1 Mechanism: "Hidden" Account Substitution
*   **Transaction**: `YFI_BASU_MOD`
*   **Program**: `YFI_ACCOUNT_SUBSTITUTION`
*   **Backend Class**: `YCL_FI_ACCOUNT_SUBST_BL` (Management), `YCL_FI_ACCOUNT_SUBST_READ` (Runtime).
*   **Primary Table**: `YTFI_BA_SUBST`

### 9.2 Functional Logic
*   **Trigger**: Called from `YRGGBS00` -> `FORM U910`.
*   **Evolution**:
    - **Legacy**: Used table `YBASUBST` for hardcoded 1:1 mapping.
    - **Modern (Post 10/2022)**: Uses `YTFI_BA_SUBST` which supports **Range-based mapping**.
*   **Logic Flow**:
    - Input: `BUKRS`, `BLART` (Doc Type), `HKONT` (GL Account).
    - Lookup 1: Select ranges for `BUKRS` + `BLART`. If `HKONT` in range -> Return `GSBER`.
    - Lookup 2: If fail, select ranges for `BUKRS` + `SPACE` (Global). If `HKONT` in range -> Return `GSBER`.
*   **Key Significance**: This tool allows non-ABAPers to manage complex Business Area derivation rules without modifying the GGB1 transport-locked configuration.

## 10. Master Registry of Persistence Tables (FI Extensions)
*   `YTFI_BA_SUBST`: Modern Business Area substitution ranges.
*   `YBASUBST`: Legacy Business Area substitution (Static).
*   `GB901 / GB922`: Standard SAP tables storing Boolean logic for validations.
*   `T80D`: Formpool registry (Links `FI` area to `YRGGBS00`).

---
## 11. PSM/PS Force-Mapping Logic (The "Brain" Connections)

This section documents the hardwired logical links between different account assignment objects discovered in `YRGGBS00`. These rules enforce system-wide consistency for PSM (Public Sector) and PS (Project System) postings.

### 11.1 The "Technical Fund" Force-Mapping Pattern
Triggered primarily for Asset postings and specific expenditures (Exits `UAEP`, `UATF`, `NSAI`).

| Company Code | Condition (Business Area) | Resulting Fund (`GEBER`) | Resulting FC (`FISTL`) | Resulting CC (`KOSTL`) | PS Impact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UNES** | `GEF` | `GEF` | `UNESCO` | `111023` | **FORCE CLEAR WBS** |
| **UNES** | `OPF` | `OPF` | `UNESCO` | `131023` | **FORCE CLEAR WBS** |
| **UNES** | `PFF` | `PFF` | `UNESCO` | `121023` | **FORCE CLEAR WBS** |
| **IBE** | (Any) | `PFF` | `IBE` | `ADM` | **FORCE CLEAR WBS** |
| **IIEP** | `PAR` | `PAR` | `IIEP` | `ADM` | **FORCE CLEAR WBS** |
| **ICTP** | (Any) | `ICTP` | `ICTP` | (Derived) | (No Clear) |

### 11.2 Payment-to-Business-Area Linkage
Exit `U904` creates a dependency between payment metadata and financial reporting segments.

*   **Payment Supp. `PF`** -> Mandatory Business Area **`PFF`**.
*   **Payment Supp. `OP`** -> Mandatory Business Area **`OPF`**.
*   **Payment Supp. `GE`** -> Mandatory Business Area **`GEF`**.

### 11.3 Account-to-Fund Isolation
Specific funds are "locked" to certain G/L accounts via validations:
*   **Fund `185GEF0012`**: Postings are permitted ONLY on G/L **`6043011`**.
*   **Legacy Funds (`149*`)**: Heavily restricted or blocked for new procurement.

### 11.4 Cross-Module Conflict Resolution
*   **PS-PSM Bypass**: In Asset technical postings (`UATF`, `NSAI`), the system **automatically clears the WBS Element (`PROJK`)**. This ensures that the technical fund derivation (which is mandatory for financial integrity) is not blocked by a "Project-vs-Fund" validation error in the standard FM-PS check.

### 11.5 The "Master Emergency Exit" (`YXUSER`)
A critical table called **`YXUSER`** allows specified users (Batch IDs or Administrators) to **bypass** the most restrictive substitutions and validations.
*   **Effect**: If a user is registered in this table with the correct `XTYPE` (e.g., `AA` for Assets), the system will **NOT** clear the WBS element or force-map the Fund. 
*   **Significance**: This is the "Open Door" used for automated interfaces and high-level adjustments that must bypass the standard guardrails.

---
**Related Technical Autopsies**: 
- [Finance Validations & Substitutions Autopsy](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md)
- [Business Area Substitution Framework (BASU)](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/EXTENSIONS/basu_mod_technical_autopsy.md)
- [Validation & Substitution Matrix](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/EXTENSIONS/validation_substitution_matrix.md)


---

## 12. HCM Fiori Enhancements (SE20 Composite — Extracted 2026-03-12)

### 12.1 Overview
27 composite enhancement implementations discovered in SE20. 11 directly impact Fiori apps.
Full extraction: `Zagentexecution/mcp-backend-server-python/extracted_code/ENHO/`
Master report: `extracted_code/ENHO/_COMPOSITE_ENH_REPORT.json`

### 12.2 High-Priority Fiori Enhancements

| Enhancement | Package | Domain | Fiori App / Service | Code Status |
|---|---|---|---|---|
| `ZCL_HCMFAB_ASR_PROCESS` | ZFIORI | HCM/ASR | `ZHR_PROCESS_AND_FORMS_SRV` | **35 files extracted** (CM001-CM00D) |
| `ZHR_FIORI_0021` | ZFIORI | HCM/Family | `ZHCMFAB_MYFAMILYMEMBERS_SRV` | 1 E-include extracted (44 lines) |
| `ZHR_PERS_DATA` | ZFIORI | HCM/Personal Data | `Z_HCMFAB_MYPERSONALDATA_SRV` | Container-only (BAdI) |
| `YCL_HRPA_UI_CONVERT_0002_UN` | (TBC) | HCM/PA IT0002 | `Z_HCMFAB_MYPERSONALDATA_SRV` | Container-only |
| `YCL_HRPA_UI_CONVERT_0006_UN` | (TBC) | HCM/PA IT0006 | `Z_HCMFAB_ADDRESS_SRV` | Container-only |
| `YENH_INFOTYPE` | (TBC) | HCM/Infotypes | PA26/PA30 Fiori | Container-only |
| `YHR_ENH_HRFIORI` | ZHRBENEFITS_FIORI | HCM/Fiori | Generic Benefits Fiori | Container-only |
| `YHR_ENH_HRCOREPLUS` | ZHR_DEV | HCM/HR Core+ | HR Foundation Fiori | Container-only |
| `ZCOMP_ENH_SF` | ZHR_DEV | HCM/SF | OData/BTP iFlow | Container-only |
| `ZENH_PAWF_INT_AGREE` | ZHR_DEV | HCM/WF | Fiori Inbox/ASR | Container-only |
| `ZHR_PENSION` | ZHR_DEV | HCM/Payroll | HR Data Fiori | Container-only |

### 12.3 ZHR_FIORI_0021 — Key Finding (IT0021 Field Visibility)
Enhancement Point on `IF_HRPA_UI_CONVERT_STANDARD` that hides:
- `GOVAST` (Government-Assisted), `SPEMP` (Special Employment), `ERBNR` (Inheritance No.) — always hidden
- `WAERS` (Currency) — read-only when `FAMSA = '14'` (Child) or `'2'` (Spouse)

### 12.4 ZCL_HCMFAB_ASR_PROCESS — Key Finding (Admin Employee Logic)
Implements `GET_ADMIN_EMPLOYEES` on `IF_HCMFAB_ASR_PROCESS_CONFG`:
- Checks `AGR_USERS` for roles `YSF:HR:HRA*` / `YSF:HR:HRO*`
- HR Admin: returns all active employees (PA0000.STAT2='3') as admin pool
- Non-Admin: resolves via `BAPI_USR01DOHR_GETEMPLOYEE(SY-UNAME)`
- Source: [CM006](file:///c:/Users/jp_lopez/projects/abapobjectscreation/Zagentexecution/mcp-backend-server-python/extracted_code/ENHO/ZCL_HCMFAB_ASR_PROCESS/ZCL_HCMFAB_ASR_PROCESS========CM006.abap)

### 12.5 Container-Only Enhancements — Next Extraction Steps
These enhancements are ENHC wrappers with no direct source includes.
Their logic lives in BAdI implementation classes to be extracted:

| Enhancement | Linked BAdI / Class to Extract |
|---|---|
| `ZHR_PERS_DATA` | `ZCL_HCMFAB_B_MYPERSONALDATA` (HCMFAB_B_MYPERSONALDATA) |
| `YHR_ENH_HRFIORI` | Classes in package `ZHRBENEFITS_FIORI` |
| `YHR_ENH_HRCOREPLUS` | Classes for HR Core+ integration |
| `ZCOMP_ENH_SF` | SuccessFactors interface classes in `ZHR_DEV` |
| `YENH_INFOTYPE` | Infotype screen exit classes |

---

## 13. Payment / BCM Workflow Custom Code (Treasury — Extracted live P01, 2026-06-19)

> **Why this section exists:** the BCM-signature analysis surfaced custom ABAP in workflow steps that
> previously lived ONLY in the Treasury design doc + Golden DB, never in this master registry. Promoted here
> 2026-06-20 to close that gap (cross-reference rule). Authoritative detail + flow:
> [`bcm_signatory_change_solution_design.md` §3b](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/Treasury/bcm_signatory_change_solution_design.md).

**Scope note — what is NOT custom:** the **signatory/agent selection is 100% standard SAP**
(`BNK_API_GET_REL_ACTORS` → `RH_GET_ACTORS`, criteria in IT1218). The custom code below lives in a *separate*
gate — **FI "Release for Payment"** workflow `WS90000003` (document-level, BEFORE F110) — and in the BCM batch
**reject** path. It blocks/reverses *documents*; it does NOT decide *who signs*.

### 13.1 FI Release-for-Payment custom tasks — `WS90000003` (4 tasks, D_CROUZET, 2010)
Source: Golden DB `bcm_workflow_custom_task`. BOR methods live on custom subtype **`YBSEG`** (PARENT `BSEG`,
program [`YBSEG_REL`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/Treasury/code/YBSEG_REL.abap), author A_AHOUNOU).

| Task | BOR method | Name | Effect |
| :--- | :--- | :--- | :--- |
| **TS90000012** | **`BSEG.ZCREATEPAYMENTBLOCKWF`** | Set Block Payment to W | **Raw `UPDATE bseg / UPDATE bsik SET zlspr='W'`** (Workflow payment block) |
| TS90000011 | `SYSTEM.GENERICINSTANTIATE` | Create instance ZBSEG | Instantiate custom BOR `YBSEG` |
| TS90000010 | `SYSTEM.GENERICINSTANTIATE` | ZGETGOSNOTE | Get a GOS note/attachment |
| TS90000008 | `BSEG.CHANGE` | Change Document Line | Change a doc line item |

> ⚠️ **RISK — direct DB write, not a BAPI.** `ZCREATEPAYMENTBLOCKWF` sets `ZLSPR='W'` via raw SQL `UPDATE`:
> **no change documents, no authority check, no enqueue**, BSEG/BSIK updated separately (desync risk),
> `COMMIT WORK` inside a BOR method. "Who set/removed this block and when?" has an **empty audit trail**.
> Should use the standard Release-for-Payment block / a supported change API. (Same class of finding as the
> `YBASUBST` "hidden substitution" — custom config bypassing the standard guardrail.)

### 13.2 BCM batch reject BAdI — the only custom code in the signing path
Source: Golden DB `bcm_badi_impl` (1 of 3 impls is custom).

| BAdI | Impl class | Method | Effect |
| :--- | :--- | :--- | :--- |
| `BNK_BADI_ORIG_PAYMT_CHG` | [`Z_CL_BNK_BADI_PAYMT_CHG`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/Treasury/code/Z_CL_BNK_BADI_PAYMT_CHG.abap) | `IF_EX_BNK_ORIG_PAYMT_CHG~ON_REJECT` | On batch/payment reject → auto-reverse the F110 payment (`J_1B_FBRA_POSTING_AUFRUFEN`, FBRA+FB08 reason `01`) + log SLG1/FBPM (SAP note 1333640) |

### 13.3 Payment-release email notification (FUGR, package YWFI)
`ZFI_PAYREL_EMAIL` — includes [`LZFI_PAYREL_EMAILU01`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/FI/YWFI/FUGR/ZFI_PAYREL_EMAIL/LZFI_PAYREL_EMAILU01.abap) / `U02`. Email notification for the payment-release gate. *(Logic depth: TBC — extracted, not yet autopsied.)*

### 13.4 Persistence / where this is queryable
*   Golden DB (structured): `bcm_workflow_custom_task` · `bcm_badi_impl` · `bcm_release_activity_fm` (standard FMs).
*   Source code: `knowledge/domains/Treasury/code/` (YBSEG_REL, Z_CL_BNK_BADI_PAYMT_CHG) + `extracted_code/FI/YWFI/`.
*   Companion: `companions/bcm_signatory_companion.html`.

---
*For app-level connections see individual analysis docs in `knowledge/domains/HCM/Fiori Apps/`*

---

## 14. FM/BCS Availability Control Custom Code (PSM — Extracted live P01, 2026-06-23)

### 14.1 `ZRFC_FRESERVATION_CREATE` — Funds Reservation via BDC (ANTI-PATTERN)

*   **Object type**: Function Module (Z-namespace, RFC-enabled)
*   **Purpose**: Creates FM funds reservations (earmarked funds, transaction FMX1) via RFC call from external systems.
*   **Anti-pattern (G_CONFORMANCE)**: Implemented as `CALL TRANSACTION USING t_bdc` with OKCODEs `/00`, `EPF23`, `=SAVE` — a fragile batch-input of screen FMX1. The clean standard data-driven API `FMFR_CREATE_FROM_DATA` (with `I_FLG_CHECKONLY` for AVC check without commit) exists and was NOT used.
*   **Evidence**: Source code extracted via RPY_FUNCTIONMODULE_READ_NEW on P01 (s091). Claim #258.
*   **Improvement candidate**: Replace BDC with `FMFR_CREATE_FROM_DATA`. `I_FLG_CHECKONLY=X` enables AVC pre-check without posting — enables "will this reservation block?" queries without side effects.
*   **Related**: `FI_PSO_EARMARKED_FUNDS2_CREATE` (another standard FM in chain), `FMX1` (BDC target), `BAPI_0050_CREATE` (budget entry BAPI — NOT reservation), `BAPI_0051_GET_TOTALS` (budget totals only — NOT AVC consumption).
*   **Cross-links**: Claim #258 (structural defect), rule `feedback_mode_e_bdc_is_network_coupling_risk`, `knowledge/domains/PSM/avc_availability_model.md#reservation-bapi-landscape`.

---
*AVC model documentation: `knowledge/domains/PSM/avc_availability_model.md` (committed 92f1004). AVC claims #253-#259 in brain_v2/claims/claims.json.*

---

## 15. DMEE Structured-Address Custom Code (Payment/Treasury — extensively analyzed s#062-s#-2026-07-01, never in this registry until now)

> **Why this section exists:** the V001 structured-address redesign for CGI/CITI/SEPA payment media has been
> analyzed across many sessions (claims #62-115, #179-186, #267, #285, #308-311) and has 2 companions
> (`BCM_StructuredAddressChange.html`, `payment_bcm_companion.html`) — but the underlying CUSTOM CODE that
> implements it was never itself registered here. Promoted 2026-07-01 (steward pass) to close that gap.

### 15.1 `YCL_IDFI_CGI_DMEE_FALLBACK_CM001` — CGI Cdtr name-overflow BAdI (Pattern A)

*   **Object type**: Class implementing BAdI `FI_CGI` (method `GET_CREDIT`), exit `FI_CGI_DMEE_EXIT_W_BADI`.
*   **Purpose**: SocGen-mandated overflow guard — if the DMEE-tree-populated `Cdtr` name overflows the field,
    prepend/patch the value (Pattern A). NOT a legacy hack — bank-mandated (claim #96, TIER_1, verified against
    the SocGen document).
*   **Scope of what it actually touches**: address assembly for Dbtr/Cdtr/UltmtCdtr on the CGI tree is mostly
    SAP-standard (`FI_PAYMEDIUM_DMEE_CGI_05` Event 05 populates `FPAYHX-REF01/REF02` buffers from ADRC); this
    class only patches the Cdtr name-overflow case. Confirmed still the only UNESCO-owned address-related BAdI
    code to preserve (claim #186).
*   **Evidence**: `knowledge/domains/Payment/dmee_formats_model_comparison.md` §8; claims #96, #186, #308.

### 15.2 `Y_FI_DMEE_ADR` — SEPA custom DMEE exit family (`/SEPA_CT_UNES`)

*   **Object type**: Custom exit function(s) bound as `MP_EXIT_FUNC` on `/SEPA_CT_UNES` DMEE tree nodes
    (model `FPM_SEPA`). Unlike CGI/CITI, SEPA has NO Event-05 standard buffer population — this custom exit is
    the only address-population mechanism (reads `T001`→`ADRC` directly for the paying company Dbtr fields).
*   **Per-party status (verified s-2026-07-01, D01 V001 fresh extract)**: Dbtr = structured via this exit;
    Cdtr = structured via `FPAYH`-Z* direct fields (no exit, missing `CtrySubDvsn`); UltmtDbtr/UltmtCdtr =
    Nm-only (by design, ISO 20022/EPC scheme has no PstlAdr slot for on-behalf-of parties on ultimate parties —
    see claim #311, `KNOWN_UNKNOWN`: not yet confirmed against the actual EPC/SocGen IG document).
*   **Evidence**: `knowledge/domains/Payment/dmee_sepa_v001_compare_table.md`; `dmee_formats_model_comparison.md`;
    claims #113, #311.

### 15.3 CITIPMW V3 exits — CITI structured-address (`/CITI/XML/UNESCO/DC_V3_01`)

*   **Object type**: SAP-partner-delivered exit family `CITIPMW/V3_*` (Event-05 FM
    `/CITIPMW/V3_PAYMEDIUM_DMEE_05` pre-populates `FPAYHX_FREF` for Dbtr; separate exits read vendor-master
    `ADRC` directly for Cdtr, gated by `UBISO`).
*   **Coverage (verified)**: Dbtr 4/4 structured tags across 2 PstlAdr node variants (primary +
    alt-mode/PstlAdrMor); Cdtr 2 conditional nodes by `UBISO`; UltmtCdtr 2 nodes (structured, works in
    production, Serbia example); UltmtDbtr = 0 (Nm-only by design, user-confirmed 2026-06-17). CITI's
    **CdtrAgt** (`N_5135503450`) is structured (StrtNm/TwnNm/CtrySubDvsn via `FPAYH`-ZB* fields) but lacks
    PstCd/BldgNb — no bank-master source for either (claim #309).
*   **Evidence**: `dump_citi_cdtr_subtrees.py` (Zagentexecution/mcp-backend-server-python/); claims #99, #101,
    #113, #309.

### 15.4 CGI tree (`/CGI_XML_CT_UNESCO`) — 4/4 party structured-address inventory

*   **Object type**: DMEE tree, model `FPM_CGI` (shared with CITI). The ONLY live production CGI tree — its
    twin `/CGI_XML_CT_UNESCO_1` is a DEAD orphan (0 P01 media ever, not in T042Z routing; claim #285).
*   **Full 4-party PstlAdr inventory (D01 V001, verified s-2026-07-01)**: Dbtr, UltmtDbtr (transaction-level
    node only — `PmtInf/UltmtDbtr` stays Nm+Id), Cdtr, UltmtCdtr are ALL structured (claim #308). **CdtrAgt is
    the one gap**: unstructured (2 `AdrLine` nodes only). CITI's CdtrAgt is the correct mirror template
    (claim #309); the refined, LOW-priority change definition (ADD StrtNm/TwnNm/CtrySubDvsn, REMOVE the 2
    AdrLine nodes, do NOT add PstCd/BldgNb — no bank-master source) supersedes the original
    `v001_change_matrix.csv` rows 22-23 (claim #310, TIER_1).
*   **Evidence**: `Zagentexecution/output/dmee_CGI_XML_CT_UNESCO_d01.csv`; claims #285, #308, #309, #310.

### 15.5 `ZSAPFPAYM_REPLAY` — DMEE replay/test tool (deployed D01)

*   **Object type**: Executable ABAP report (TRDIR, author JP_LOPEZ, created 2026-06-15), a copy of SAPFPAYM
    that replays a DFPAYG payment run to regenerate the DMEE output file with ROLLBACK (no status mutation).
    Needs `PM_GRPNO` as input. Confirmed still deployed and runnable as of s-2026-07-01.
*   **Purpose**: Test/validate DMEE tree changes (CGI/CITI/SEPA) against real historical payment media without
    posting side-effects. 5 CGI test cases identified in D01, replay-ready (TC-1..TC-5, see claim #312).
*   **Evidence**: `extracted_code/FI/SAPFPAYM/ZSAPFPAYM_REPLAY/ZSAPFPAYM_REPLAY.abap`;
    `reference_zsapfpaym_replay_and_citi_ubiso.md`; claim #312.

### 15.6 Persistence / where this is queryable

*   Claims: brain_v2/claims/claims.json #62-115, #179-186, #267, #285, #308-312.
*   Source docs: `knowledge/domains/Payment/dmee_formats_model_comparison.md`,
    `dmee_sepa_v001_compare_table.md`, `v001_change_matrix.csv`, `v001_dbtr_fix_2026-05-07.md`,
    `dmee_retrofit_procedure.md`, `dmee_versioning_procedure.md`.
*   Companions: `companions/BCM_StructuredAddressChange.html` (+ source fragments in
    `companions/bcm_structured_address_src/`), `companions/payment_bcm_companion.html`.
*   **KNOWN STALE REFERENCE (flagged, not yet fixed):** `companions/bcm_structured_address_src/tabs/22_matrix.html`
    rows 22-23 still show the original CGI CdtrAgt `PstCd<-ZBPST` / `BldgNb<-ZBSTR[60-75]` field-source plan,
    which claim #310 supersedes (no bank-master source exists for either field). Do not port this correction
    into the fragment until the in-progress fragment/HTML reconciliation (companion drift fix, rule #168)
    completes — fixing it mid-reconciliation risks colliding with that pending merge.
