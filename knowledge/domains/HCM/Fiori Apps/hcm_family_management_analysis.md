# Fiori App Analysis: Family Members Management (YHR_FMLY_MAN)

## 1. Application Identity
- **App Title**: Family Members Management
- **Semantic Object**: `YHR_FMLY_MAN`
- **Action**: `display`
- **Launchpad Technical ID**: `Z_FMLY_MAN_EXT` (UNESCO Extension)
- **UNESCO Business Domain**: HCM [HR]

## 2. Front-End Entry Points (BSP Layer)
- **Primary BSP**: `HCMFAB_MYFAMILYMEMBERS` (Standard)
- **Extension BSP**: `Z_FMLY_MAN_EXT`
- **Key UX Patterns**: Master-Detail with IconTabBar (Tabs).
- **Manifest Discovery**:
  - `OData Models`: `Z_HCMFAB_MYFAMILYMEMBERS_SRV` (Standard foundation)
  - `Extension Service`: `ZHCMFAB_MYFAMILYMEMBERS_SRV` (UNESCO specialized)

## 3. The Gold Layer (OData & Gateway)
- **Standard Service**: `HCMFAB_MYFAMILYMEMBERS_SRV`
- **UNESCO Extension Service**: `ZHCMFAB_MYFAMILYMEMBERS_SRV`
- **DPC Extension Class**: `ZCL_Z_HCMFAB_MYFAMILYM_DPC_EXT`
- **MPC Extension Class**: `ZCL_Z_HCMFAB_MYFAMILYM_MPC_EXT`

### Entity Model Mapping
| Entity Set | Backend Structure | Key Fields | Purpose |
| :--- | :--- | :--- | :--- |
| `FamilyMemberSet` | `PA0021` | `PERNR`, `SUBTY`, `OBJPS` | Standard family relationships (Spouse, Child, etc.) |
| `FamilyMemberUNSet` | Custom Structure | `PERNR`, `LGART` | UNESCO-specific financial benefits for dependents |

---

## 4. Backend Logic & UNESCO Extensions
- **Core BAdI**: `HCMFAB_B_MYFAMILYMEMBERS`
- **UNESCO Implementation**: `ZHCMFAB_B_MYFAMILYMEMBERS`
- **Implementing Class**: `ZCL_HCMFAB_B_MYFAMILYMEMBERS`

### Logic Trace (Methods Analysis)
| Method | Impact | Discovered Logic |
| :--- | :--- | :--- |
| `ENRICH_FAMILYMEMBERUN` | Benefits Info | Injects UNESCO-specific Wage Type texts (`lgtxt`) from `T512T` for `molga = 'UN'`. |
| `ENRICH_FAMILYMEMBER` | Relationship Logic | Likely handles the "Education Attendance" check logic for children over 18. |
| `CHECK_ON_BEHALF` | Authorization | (Inherited from `HCMFAB_B_COMMON`) Validates if manager/admin is acting on behalf of staff. |

---

## 5. Persistence & Field Connectivity
- **Standard Tables**: `PA0021` (Family Members/Dependents), `PA0002` (Personal Data).
- **UNESCO Configuration**: `T512T` (Wage Type Texts for UN Molga).
- **Field Mappings**:
  - `Education Status` -> `I0021_EDUAT` (IT0021)
  - `UNESCO Wage Type` -> `LGART` (IT0021 or custom staging)

---

## 6. Workflow & State Management
- **Transaction Pattern**: **ASR (HCM Processes and Forms)**.
- **ASR Scenarios**: 
    - `ZHR_BIRTH_CHILD`: Triggered for new child registration.
    - `ZHR_ADOPTION`: Triggered for adoption.
    - `ZHR_CHANGE_CHILD`: Triggered for updates to existing dependent data.
- **Workflow Classes**: `ZCL_FMLY_SPSE_UN`, `ZCL_HRFIORI_BIRTH_OF_A_CHILD`.

---

## 7. React Synthesis (Blueprint for Frontend)
- **Primary API Endpoint**: `/sap/opu/odata/sap/ZHCMFAB_MYFAMILYMEMBERS_SRV/`
- **Tabs/Sections Representation**:
    1. **General Information**: Standard `PA0021` fields.
    2. **UNESCO Specifics**: Benefit Wage Types and Education Status.
    3. **Attachments**: Handled via ASR GOS or custom `DOCUMENTTOUPLOAD` entity.
- **Visibility Rules**:
    - **Education Tab**: Only visible/mandatory if `Age >= 18` (Logic in `ZCL_HRFIORI_BIRTH_OF_A_CHILD`).
    - **Allowances Section**: Powered by `FamilyMemberUNSet` properties.

---
> [!NOTE]
> This app heavily relies on the ASR framework for data staging. Master records (`PA0021`) are only updated AFTER the workflow approval.


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
