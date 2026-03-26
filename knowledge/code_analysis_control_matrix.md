# UNESCO SAP Code Analysis Control Matrix

This table tracks the analysis status, functional domain, and technical purpose of all custom ABAP objects extracted from the P01 system.

| Object Name | Functional Domain | Technical Type | Analysis Status | Purpose / Business Rule |
| :--- | :--- | :--- | :--- | :--- |
| [`YCL_YPS8_BCS_BL`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/PS_PROJECTS/) | **PS** (Projects) | Class (Bridge) | ✅ Complete | **The Project-Fund Glue**: Link between WBS & FM Budget. |
| [`YCL_SAP_TO_WORD`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/TECH_INTEGRATION/) | **TECH** (Framework) | Class (Integration) | ✅ Complete | Framework for generating Word docs from SAP data. |
| [`ZXFMDTU02`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMDTU02_RPY.abap) | **FM** (Budgeting) | Include (Derivation) | ✅ Complete | FMDERIVE: Hardcoded GL-to-Fund/FC mapping. |
| [`ZXFMYU22`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMYU22_RPY.abap) | **FM** (Budgeting) | Include (Validation) | ✅ Complete | Mandatory logic for Fund -> WBS/CC links. |
| [`ZXFMCU09`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMCU09_RPY.abap) | **FM** (Budgeting) | Include (FR Header) | ✅ Complete | Historical "Dollar Constant" currency & date checks. |
| [`ZXFMCU10`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMCU10_RPY.abap) | **FM** (Budgeting) | Include (FR Header) | ✅ Complete | Validates `XBLNR` (Reference) field for dots and date format. |
| [`ZXFMCU12`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMCU12_RPY.abap) | **FM** (Budgeting) | Include (Exch Rate) | ✅ Complete | Exchange rate warnings for EUR trans on FMX1. |
| [`ZXFMCU17`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMCU17_RPY.abap) | **FM** (Budgeting) | Include (FR Limits) | ✅ Complete | Forces 2% / 2000 USD tolerance max for FMX1/2. |
| [`ZXFMFUNDU04`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_MASTER_DATA/ZXFMFUNDU04_RPY.abap) | **FM** (Master Data) | Include (Fund) | ✅ Complete | IBF: Validates Biennium dates vs Fund validity. |
| [`ZXFMFUNDI01`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_MASTER_DATA/ZXFMFUNDI01_RPY.abap) | **FM** (Master Data) | PAI Module | ✅ Complete | UI logic for IBF C/5 Workplan assignment. |
| [`ZXFMYU41`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMYU41_RPY.abap) | **FM** (Global) | Include (AVC) | ✅ Complete | Forces AVC activation for Batch/WF jobs. |
| [`ZXTRVU05`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/TV_TRAVEL/ZXTRVU05_RPY.abap) | **TV** (Travel) | Include (Validation) | ✅ Complete | Blocks dual assignment of CC + WBS in TV. |
| [`ZXM06U22`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/MM_PROCUREMENT/ZXM06U22_RPY.abap) | **MM** (Procurement) | Include (Release) | ✅ Complete | Bypasses PO release via MATKL manipulation. |
| [`YJWB001`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/PS_PROJECTS/YJWB001_RPY.abap) | **PS** (Projects) | Include (WBS) | ✅ Complete | Validates custom User Fields (Sector, Region). |
| [`ZXRSAU01`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/BI_REPORTING/ZXRSAU01_RPY.abap) | **BI/BW** (Reporting) | Include (Extraction) | ✅ Complete | Logic for "Real" Posting Dates and USD calc. |
| [`ZXFMDTU01`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMDTU01_RPY.abap) | **FM** (Budgeting) | Include (Derivation) | ✅ Complete | Placeholder for FMDERIVE logic. |

## 🔗 Related Components (Secondary Discovery)
- **`YXUSER`**: Custom table mentioned in `ZXFMCU17` for granting "FRTL" (Funds Reservation Tolerance Limit) exceptions.
- **`YCL_FM_FUND_IBF_BL`**: Business Logic class for IBF; core controller for `ZXFMFUND*` objects.
- **`ZFI:009`**: Universal error/warning message class used across several validation includes.
- **`BKPF-HWAE2`**: Secondary local currency (USD) relied upon by extraction logic.
