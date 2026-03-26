"""
append_enhancements_to_app_docs.py
====================================
Appends composite enhancement cross-reference sections to each Fiori app
analysis document, and adds a new HCM section to the custom enhancement
registry.

Run from: c:/Users/jp_lopez/projects/abapobjectscreation
"""

import os

BASE = r"c:\Users\jp_lopez\projects\abapobjectscreation"
HCM_FIORI = os.path.join(BASE, "knowledge", "domains", "HCM", "Fiori Apps")
KNOW = os.path.join(BASE, "knowledge")
ENHO_BASE = os.path.join(BASE, "Zagentexecution", "mcp-backend-server-python",
                          "extracted_code", "ENHO")


# ── family management ─────────────────────────────────────────────────────────
FAMILY_ENH = """

---

## 8. Composite Enhancement Linkage (ENHO Cross-Reference)

> [!IMPORTANT]
> Auto-generated from SE20 Composite Enhancement extraction (2026-03-12).
> Extracted source: `extracted_code/ENHO/ZHR_FIORI_0021/`

### ZHR_FIORI_0021 — IT0021 Family Member UI Field Control
- **Enhancement Type**: Classic Enhancement Point (`=E` include)
- **Interface**: `IF_HRPA_UI_CONVERT_STANDARD` (Infotype UI conversion)
- **Package**: `ZFIORI` | **Transport**: `D01K9B0ENM` | **Last changed**: `G_SONNET` 2026-02-23

| Field | Name | Rule | Impact on Fiori UI |
|---|---|---|---|
| `GOVAST` | Government-Assisted | Always INVISIBLE | Never shown to user |
| `SPEMP` | Special Employment | Always INVISIBLE | Never shown to user |
| `ERBNR` | Inheritance Number | Always INVISIBLE | Never shown to user |
| `WAERS` | Currency | READ_ONLY | Only when FAMSA='14' (Child) or '2' (Spouse) |

**End-to-End Chain**:
```
PA0021 (IT0021)
  --> IF_HRPA_UI_CONVERT_STANDARD (SAP Standard)
        --> ZHR_FIORI_0021 (UNESCO Enhancement: field visibility override)
              --> ZHCMFAB_MYFAMILYMEMBERS_SRV (OData)
                    --> FamilyMemberSet entity
                          --> Fiori Family Members App (Z_FMLY_MAN_EXT / BSP)
```
"""

# ── personal data ─────────────────────────────────────────────────────────────
PERSONAL_ENH = """

---

## 12. Composite Enhancement Linkage (ENHO Cross-Reference)

> [!IMPORTANT]
> Auto-generated from SE20 Composite Enhancement extraction (2026-03-12).
> Extracted source: `extracted_code/ENHO/`

### ZHR_PERS_DATA — Personal Data BAdI Container
- **Enhancement**: `ZHR_PERS_DATA` (ENHC, package: `ZFIORI`, no stand-alone source)
- **Implements**: `HCMFAB_B_MYPERSONALDATA` BAdI (UNESCO implementation class: `ZCL_HCMFAB_B_MYPERSONALDATA`)
- **Status**: Container-only ENHC — logic lives in linked BAdI class

### YCL_HRPA_UI_CONVERT_0002_UN — Infotype 0002 Field Conversion (Personal Data)
- **Enhancement**: `YCL_HRPA_UI_CONVERT_0002_UN` (ENHC, composite)
- **Interface**: `CL_HRPA_UI_CONVERT_*` UNESCO override for IT0002
- **Impact**: Controls visibility/editability of PA0002 fields in Fiori

**End-to-End Chain**:
```
PA0002 (IT0002 Personal Data fields: VORNA, NACHN, GBDAT, ...)
  --> CL_HRPA_UI_CONVERT_<INFTY> (SAP standard UI conversion)
        --> YCL_HRPA_UI_CONVERT_0002_UN (UNESCO override — field attributes)
              --> Z_HCMFAB_MYPERSONALDATA_SRV (OData)
                    --> PersonalDataSet entity
                          --> Fiori My Personal Data App (Z_PERS_MAN_EXT / BSP)
```

### ZCL_HCMFAB_ASR_PROCESS — ASR Process Configuration (Admin Employees)
- **Enhancement / Class**: `ZCL_HCMFAB_ASR_PROCESS` (Package: `ZFIORI`)
- **Interface implemented**: `IF_HCMFAB_ASR_PROCESS_CONFG~GET_ADMIN_EMPLOYEES`
- **Extracted**: 13 CM method includes — richest ENHO (35 files total)
- **Key Logic** (CM006 method — `GET_ADMIN_EMPLOYEES`):
  - Checks current user against `AGR_USERS` for roles `YSF:HR:HRA*` / `YSF:HR:HRO*`
  - If HR Admin role found: returns ALL active employees (PA0000 STAT2='3') as admins
  - If no role: resolves employee via `BAPI_USR01DOHR_GETEMPLOYEE(sy-uname)`
  - Joins PA0001 (position/org unit) + T528T (position texts in sy-langu)
- **Business Meaning**: Drives who appears as a delegatable HR Admin in the Start ASR Process UI
- **Code**: `extracted_code/ENHO/ZCL_HCMFAB_ASR_PROCESS/ZCL_HCMFAB_ASR_PROCESS========CM006.abap`
"""

# ── address management ────────────────────────────────────────────────────────
ADDRESS_ENH = """

---

## 6. Composite Enhancement Linkage (ENHO Cross-Reference)

> [!IMPORTANT]
> Auto-generated from SE20 Composite Enhancement extraction (2026-03-12).

### YCL_HRPA_UI_CONVERT_0006_UN — Infotype 0006 (Address) Field Conversion
- **Enhancement**: `YCL_HRPA_UI_CONVERT_0006_UN` (ENHC, composite)
- **Interface**: `CL_HRPA_UI_CONVERT_*` UNESCO override for IT0006 (Address)
- **Impact**: Controls which PA0006 address fields are visible/editable/mandatory
- **Directly linked to**: `YCL_IM_PERSINFOUI_0006` (referenced in Section PART I.2)

**End-to-End Chain**:
```
PA0006 (IT0006 Address fields: STRAS, ORT01, ZZUNREG, ...)
  --> YCL_IM_PERSINFOUI_0006 (BAdI impl: field attribute override for IT0006)
        --> YCL_HRPA_UI_CONVERT_0006_UN (Composite Enhancement: UN-specific UI field conversion)
              --> Z_HCMFAB_ADDRESS_SRV (OData)
                    --> AddressSet entity
                          --> Fiori Manage Address App
```

**Note on ZZUNREG**: The UNESCO custom field `ZZUNREG` (UN Region) passes through this enhancement chain.
It is set as visible/mandatory for permanent addresses (SUBTY=1) and hidden for others.
"""

# ── ASR / offboarding ─────────────────────────────────────────────────────────
ASR_SECTION = """

---

## [Additional] Composite Enhancement Linkage — ASR & Workflow

> [!IMPORTANT]
> Auto-generated from SE20 Composite Enhancement extraction (2026-03-12).

### ZENH_PAWF_INT_AGREE — Internship Agreement Workflow Enhancement
- **Enhancement**: `ZENH_PAWF_INT_AGREE` (ENHC, package: `ZHR_DEV`)
- **Domain**: HCM/Workflow — PA Workflow for internship agreement
- **Impact on this app**: May affect Fiori Inbox items and ASR scenario routing
- **Status**: Container-only ENHC — TRDIR has no direct includes

### ZCL_HCMFAB_ASR_PROCESS — ASR Process Configuration
- **Enhancement / Class**: `ZCL_HCMFAB_ASR_PROCESS` (13 CM methods extracted)
- **Implements**: `IF_HCMFAB_ASR_PROCESS_CONFG` (process configurator interface)
- **Impact on this app**: Controls admin employee list for "Start Process on Behalf"
- **Key finding**: HR Admin role check via `AGR_USERS` (YSF:HR:HRA* / YSF:HR:HRO*)
- **Code**: `extracted_code/ENHO/ZCL_HCMFAB_ASR_PROCESS/`

### ZCOMP_ENH_SF — SuccessFactors Integration Enhancement
- **Enhancement**: `ZCOMP_ENH_SF` (ENHC, package: `ZHR_DEV`)
- **Impact**: May affect OData payload routing to BTP/iFlow for SF sync
- **Status**: Container-only ENHC — logic lives in linked SF integration classes
"""

# ── enhancement registry — HCM section ───────────────────────────────────────
HCM_REGISTRY = """

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
"""


def append(filepath, content):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(content)
    print(f"Appended -> {os.path.basename(filepath)}")


if __name__ == "__main__":
    append(os.path.join(HCM_FIORI, "hcm_family_management_analysis.md"), FAMILY_ENH)
    append(os.path.join(HCM_FIORI, "hcm_personal_data_analysis.md"), PERSONAL_ENH)
    append(os.path.join(HCM_FIORI, "hcm_address_management_analysis.md"), ADDRESS_ENH)
    append(os.path.join(HCM_FIORI, "hr_offboarding_analysis.md"), ASR_SECTION)
    append(os.path.join(KNOW, "sap_custom_enhancement_registry.md"), HCM_REGISTRY)
    print("\nAll app analysis docs updated.")
    print("Enhancement registry updated with HCM section (Section 12).")
