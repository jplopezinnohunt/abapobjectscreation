# SAP Configuration & Business Rule Reference

This document catalogs key SAP configuration (T-tables) and UNESCO custom rule tables discovered during reverse engineering. It provides the "Logic Rosetta Stone" for understanding system behavior without reading ABAP code.

## 1. UI & Field Visibility Rules

| Table | Domain | Purpose | Key Fields | Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| `ZTHRFIOFORM_VISI` | HCM / Cross | **UI Manifest**: Rules for field visibility per app/step. | `ACTION`, `FIELDNAME`, `VISIBILITY` | Mandatory/Hidden/Read-Only toggles. |
| `T588M` | HCM | **Infotype Screen Mod**: Standard SAP field control. | `INFTY`, `REPID`, `VARIA` | Controls which IT fields are required for specific countries/groups. |
| `ZCL_HR_DOCUMENT_MANAGER` | HCM | **DMS Routing**: Not a table, but uses BAdIs to route attachments. | N/A | Configuration of which fields require attachments. |

## 2. Organizational Structures (Context)

| Table | Domain | Purpose | Key Fields |
| :--- | :--- | :--- | :--- |
| `T001` | FI | Company Codes (Legal Entities) | `BUKRS`, `WAERS` |
| `T500P` | HCM | Personnel Areas (Locations/Offices) | `WERKS`, `NAME1` |
| `T503K` | HCM | Employee Subgroups (Staff Categories) | `PERSK`, `PTEXT` |
| `T522N` | HCM | Name Formats | `CNTY`, `FORMAT` |

## 3. Workflow & Business States

| Table | Domain | Purpose | Interpretation |
| :--- | :--- | :--- | :--- |
| `ZTHRFIORI_BREQ` | HCM | Benefit Request Statuses | `00` (Draft), `01` (Submitted), `05` (Approved), `09` (Rejected). |
| `T5ASRSCENARIOS` | HCM | ASR Process Registry | Links Fiori Buttons to Backend Workflow Scenarios. |
| SWWWIHEAD | Tech | Workflow Runtime Header | Current status of an active approval process. |

## 4. Public Sector Management (PSM-FM) Accounting

| Table | Domain | Purpose | Key Fields | Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| `FM01` | FM | **FM Area** | `FIKRS`, `WAERS`, `PERIV` | Highest mapping level for Funds Management. Defines currency and fiscal year. |
| `FMFINCODE` | FM | **Fund** | `FINCODE`, `FIKRS`, `DATAB`, `DATBI` | Core budget unit. Bridges to PS via ID matching. |
| `FMFCTR` | FM | **Funds Center** | `FICTR`, `FIKRS` | Responsible unit for budget control. |
| `FMCIT` | FM | **Commitment Item** | `FIPEX`, `FIKRS` | Expense/Revenue category. |
| `T001A` | FM / FI | **FI Area Assignment** | `BUKRS`, `FIKRS` | Maps Company Codes to FM Areas. |
| `YTFM_WRTTP_GR`| FM | **Value Type Groups** | `WRTTP_GRP`, `WRTTP` | UNESCO-specific grouping for Actual vs Budget vs Commitment. |

## 5. Project System (PS) Accounting & Control

| Table | Domain | Purpose | Key Fields | Integration |
| :--- | :--- | :--- | :--- | :--- |
| `PROJ` | PS | **Project Definition** | `PSPID`, `POST1`, `VERNR` | Project header. `PSPID` usually matches Fund `FINCODE`. |
| `PRPS` | PS | **WBS Element** | `OBJNR`, `POSID`, `PSPHI` | Work breakdown node. Captures accounting/donor data. |
| `PRHI` | PS | **WBS Hierarchy** | `POSNR`, `UP`, `DOWN` | Defines the tree structure of the Project. |
| `TCJ1` | PS | **Project Types** | `PROTY`, `PROTXT` | Categorizes Projects (e.g., RB vs Non-RB). |
| `TCJ04` | PS | **Status Profile** | `STSMA` | Controls allowed business transactions per project state. |

## 6. Financial & Budgeting Rules (UNESCO Custom)

| Table | Domain | Purpose | Logic Link |
| :--- | :--- | :--- | :--- |
| `YTFM_WRTTP_GR` | FM | Value Type Grouping | Maps `RWRTTP` (SAP) to UNESCO concepts (Budget, Actual, Commit). |
| `YTFM_OUTPUT` | FM | Output Codes | Mapping of FM/PS data to Results-Based Budgeting codes. |
| `FMFINCODE` | FM | Fund Master | Bridges Finance to Projects via `FINCODE`. |

---
> [!TIP]
> Use `query_table.py` to extract contents of these tables when starting the analysis of a new application.
