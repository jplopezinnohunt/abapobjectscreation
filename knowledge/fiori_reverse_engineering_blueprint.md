# Fiori Reverse Engineering Blueprint: UNESCO HCM Applications

This blueprint provides a functional and technical mapping of the Fiori screens, sections, and fields discovered through deep reverse engineering of the SAP backend OData services and ABAP logic.

---

## 1. Application: My Personal Data (ESS)
**Fiori App/Action**: `yhr_pers_man-display`  
**OData Service**: `Z_HCMFAB_MYPERSONALDATA_SRV`

### Screen View: Personal Information & Profile
This view is the main landing page for Employee Self-Service personal data management.

| Section | Field (UI Label) | OData Property | Backend Source (Structure -> Table) | Service Call |
| :--- | :--- | :--- | :--- | :--- |
| **Personal Info** | First Name | `FirstName` | `HCMT_BSP_PA_XX_R0002-FIRST_NAME` -> `PA0002-VORNA` | `PersonalDataSet` (GET) |
| | Last Name | `LastName` | `HCMT_BSP_PA_XX_R0002-LAST_NAME` -> `PA0002-NACHN` | `PersonalDataSet` (GET) |
| | Birth Date | `BirthDate` | `HCMT_BSP_PA_XX_R0002-BIRTH_DATE` -> `PA0002-GBDAT` | `PersonalDataSet` (GET) |
| | Gender | `Gender` | `HCMT_BSP_PA_XX_R0002-GENDER` -> `PA0002-GESCH` | `PersonalDataSet` (GET) |
| **UNESCO Custom** | Regional Group | `Zzreggr` | `HCMT_BSP_PA_XX_R0002-ZZREGGR` -> `PA0002-ZZREGGR` | `PersonalDataSet` (GET) |
| **Field Metadata** | Visibility/Edit | (Dynamic) | **T588M** (Screen Modification Table) Logic | `FieldMetadataSet` (GET) |

- **UNESCO Custom Tables**: `[Z* Tables]`
- **Headless Property Mapping**: Use `ZTHRFIORI_UI5PRO` to map `FIELD` tags to `PROPERTY` (01=Visible, 04=Hidden).
- **Conversion Classes**: `[CL_HRPA_UI_CONVERT_*]` (Logic for ZZ-field mapping)

---

## 2. Application: HR Offboarding (Custom)
**Fiori App/Action**: `yhrappoffboardingemp-display`  
**OData Service**: `ZHRF_OFFBOARD_SRV`

### Screen View: Offboarding Request Overview
This is a task-heavy dashboard showing the separation process.

| Section | Field (UI Label) | OData Property | Backend Source (Structure -> Table) | Service Call |
| :--- | :--- | :--- | :--- | :--- |
| **Request Header** | Initiator ID | `CreatorPernr` | `zthrfiori_hreq-creator_pernr` | `RequestSet` (GET) |
| | Initiator Name | `CreatorLname` | `zthrfiori_hreq-creator_lname` | `RequestSet` (GET) |
| | Request GUID | `Guid` | `zthrfiori_hreq-guid` (Primary Key) | `RequestSet` (GET) |
| **Separation** | Effective Date | `EffectiveDate` | `zthrfiori_hreq-effective_date` | `RequestSet` (GET) |
| | Reason | `Reason` | `zthrfiori_hreq-reason` -> Domain `ZD_HRFIORI_REASON` | `RequestSet` (GET) |
| **Process Tracker** | Request Init | `RequestInit` | `zthrfiori_hreq-request_init` (Flag) | `RequestSet` (GET) |
| | Travel Clearance | `Travel` | `zthrfiori_hreq-travel` (Flag) | `RequestSet` (GET) |
| | Shipment Detail | `Shipment` | `zthrfiori_hreq-shipment` (Flag) | `RequestSet` (GET) |
| | Salary Suspense | `SalarySuspense` | `zthrfiori_hreq-salary_suspense` (Flag) | `RequestSet` (GET) |
| | Process Closed | `Closed` | `zthrfiori_hreq-closed` (Flag) | `RequestSet` (GET) |
| **Status Logic** | Step Visibility | (Dynamic) | `ZCL_ZHRF_OFFBOARD_DPC_EXT->WORKFLOWSTEPSET_GET_ENTITYSET` | `WorkflowStepSet` |

---

## 3. Implementation Patterns for Cloning

### 3.1 Metadata-Driven Visibility (HCM Pattern)
Both apps use a "Metadata Hub" architecture. For every UI section, the frontend first calls the `FieldMetadataSet` or `WorkflowStepVisibilitySet`.
*   **Source of Logic**: The logic is not in the UI code but in the ABAP DPC class (`if_visible`, `if_editable`).
*   **Clone Tip**: In React, do not hardcode field visibility. Fetch the metadata entity first and map it to the component state.

### 3.2 Action Redirection (UNESCO Pattern)
For sensitive updates (Marriage, Birth, Offboarding Save):
*   - `OData Models`: [List of services from manifest.json]
   - `Custom Routing`: [Note any overrides]
- **Headless UI Metadata**:
  - `Registry Table`: `ZTHRFIORI_UI5PRO` (Standard for UNESCO React Clones)
  - `Step Controller`: `ZTHRFIORI_STEP` or `ZTHRFIORI_OFFB_S`
  - `Metadata Key`: `REQUEST_TYPE` code (e.g., 01, 02, BEN, OFFB)
*   **Trigger**: It calls a custom ASR class (e.g., `ZCL_HRFIORI_BIRTH_OF_A_CHILD`) which starts a **workflow** (`SAP_WAPI_START_WORKFLOW`).
*   **Persistence**: Data remains in "draft" mode in ASR buffers or Custom UNESCO tables (`zthrfiori_*`) until the workflow reaches final approval.

### 3.3 Authorization Checks
Before showing any section, the backend performs checks on:
*   **P_PERNR**: For ESS (can I see my own records?)
*   **P_ORGIN**: For MSS/Admin (can I see this employee's separation record?)
*   **S_SERVICE**: Standard check for OData service execution.
