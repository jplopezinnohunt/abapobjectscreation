# UNESCO SAP Custom Enhancement Registry (Levels 3 & 4)

This document serves as the master registry of custom ABAP enhancements (User-Exits, CMOD Projects, and BAdIs) discovered during the analysis of the UNESCO SAP system (P01).

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
*For app-level connections see individual analysis docs in `knowledge/domains/HCM/Fiori Apps/`*
