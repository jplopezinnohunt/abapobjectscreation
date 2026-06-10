# N_MENARD Object Inventory — Full D01 Scan

**Scan date:** 2026-06-10 (session #081)
**System:** HQ-SAP-D01, client 350 — READ-ONLY (RFC_READ_TABLE on TADIR/TFDIR + texts; ADT GET for deep reads)
**Method:** `TADIR WHERE DEVCLASS = 'YHR_PA_WF'` + `TADIR WHERE AUTHOR = 'N_MENARD'` + `TFDIR PNAME = SAPL<fugr>`
**Scripts:** `Zagentexecution/tasks/2026_06_10_nmenard_inventory/` (scan + this generator). Raw data: `nmenard_inventory.json`.

---

## Headline numbers

- Package `YHR_PA_WF`: **740 TADIR objects** (32 object types).
- N_MENARD authored **3463 objects** across **32 packages** on D01.
- The HR-WF framework is NOT contained in one package: `YCL_HR_WF_MAIL_FACTORY`, `YCL_WF_UTILITIES`,
  `YTHRWF_NOTIF` live in **`YHR_OM_WF`**; `YCL_CA_UTILITIES` in **`YBC`**; `YCL_HRWF_MAIN_LX` and
  `YCL_HRWF_OPERATION` in **`ZHR_DEV`**. Package `YHR_PA_WF` itself has 740 objects but only 135 are
  TADIR-authored by N_MENARD (the rest were created by colleagues/generators inside his package).

### Package composition (YHR_PA_WF)

| Object type | Count | Meaning |
|---|---|---|
| TABL | 193 | Tables + structures (DDIC) |
| DTEL | 105 | Data elements |
| TTYP | 68 | Table types |
| CLAS | 41 | ABAP classes |
| TRAN | 40 | Transactions |
| FUGR | 37 | Function groups |
| CUS0 | 33 | IMG activities |
| CUS1 | 33 | IMG transactions |
| TOBJ | 33 | View-maintenance objects |
| VIEW | 21 | Maintenance views |
| PDTS | 18 | Workflow standard tasks |
| DOMA | 16 | Domains |
| PROG | 16 | Programs/includes |
| INTF | 11 | Interfaces |
| PDWS | 9 | Workflow templates |
| SICF | 9 | ICF services (WDA) |
| WDYA | 9 | Web Dynpro applications |
| WDYN | 9 | Web Dynpro components |
| SFPF | 8 | Adobe forms |
| SMIM | 7 | MIME objects |
| SFPI | 6 | Adobe form interfaces |
| NROB | 3 | Number range objects |
| SUSH | 3 | Auth switch |
| XSLT | 3 | XSLT transformations |
| SOBJ | 2 | BOR object types |
| DEVC | 1 | Package itself |
| ICFA | 1 | ICF alias |
| MSAG | 1 | Message class |
| PDAC | 1 | Workflow rule (AC) |
| SHI3 | 1 | IMG structure |
| SOTR | 1 | OTR texts |
| TYPE | 1 | Type group |

---

## 1. Classes (CLAS) — 41 in package

| Class | Description | Deep-read | Pattern notes |
|---|---|---|---|
| `YCL_HRWF_ACTORS` | HR WF actors | YES (v1, S-63/S-72) | Abstract base — actor determination |
| `YCL_HRWF_ACTORS_I1` | HR WF actors for Interns contract management | YES (v1, S-63/S-72) |  |
| `YCL_HRWF_ACTORS_LX` | HR WF Actors for PA LWOP workflow | YES (v1, S-63/S-72) |  |
| `YCL_HRWF_ACTORS_S1` | HR WF Actors for PA Separation workflow | YES (v1, S-63/S-72) |  |
| `YCL_HRWF_FACTORY` | Factory class for HR WF | YES (v1, S-63/S-72) | Factory/singleton (Pattern 1) |
| `YCL_HRWF_INTERN_GOS` | WF interns: update agreement name in GOS |  |  |
| `YCL_HRWF_MAIN` | HR WF Main class | YES (v1, S-63/S-72) | Abstract base — main algorithm |
| `YCL_HRWF_MAIN_I1` | HR WF main class for interns contract management | YES (v1, S-63/S-72) |  |
| `YCL_HRWF_MAIN_PX` | HR WF main class for PA SPA | YES (v1, S-63/S-72) |  |
| `YCL_HRWF_MAIN_S1` | HR WF main class for PA separation | YES (v1, S-63/S-72) |  |
| `YCL_HRWF_REPORT_2_BL` | Class report WF PA |  | Business-logic class behind report (report->class split) |
| `YCL_HR_INTERNSHIP` | Class for Workflow Evaluation |  |  |
| `YCL_HR_INT_WF_ASSIST` | Assistance Class WD Internship |  | Web Dynpro assistance class |
| `YCL_HR_PA_WF_ASSIST` | Assistance Class for PA Workflow |  | Web Dynpro assistance class |
| `YCL_HR_PDF_ADM_DETAILS` | Create PDF Administrative Details |  | PDF generation class |
| `YCL_HR_WF_MAIL_GENERATOR_PA_I1` | Mail generator for WF PA interns |  | Mail GENERATOR family — one per WF type (S1/I1/LX/PX) |
| `YCL_HR_WF_MAIL_GENERATOR_PA_LX` | Mail generator for WF PA LWOP |  | Mail GENERATOR family — one per WF type (S1/I1/LX/PX) |
| `YCL_HR_WF_MAIL_GENERATOR_PA_PX` | Mail generator for WF PA SPA |  | Mail GENERATOR family — one per WF type (S1/I1/LX/PX) |
| `YCL_HR_WF_MAIL_GENERATOR_PA_S1` | Mail generator for WF PA separation | YES (s081) — per-WF-type mail data provider | Mail GENERATOR family — one per WF type (S1/I1/LX/PX) |
| `YCL_HR_WF_MAIL_LX_STAFF` | LWOP WF : send email with PDF to Staff |  | Mail family |
| `YCL_HR_WF_MAIL_PA_I1_AGR_ACT` | WF mail action for interns contract management |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_I1_AO_ACT` | WF mail action for interns contract management |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_I1_AO_INFO` | WF mail action for interns contract management |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_I1_BUD_ACT` | WF mail action for interns contract management |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_I1_CANCEL` | WF mail action for interns contract management |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_I1_DELETE` | Mail to delete intern |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_I1_HRM_ACT` | WF mail action for interns contract management |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_I1_HRM_INFO` | WF mail action for interns contract management |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_I1_INI_ACT` | WF mail action for interns contract management |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_LX_ACTION` | WF mail action for LWOP |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_LX_FINAL` | WF final mail for LWOP |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_PX_ACTION` | WF mail action for SPA |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_PX_FINAL` | WF mail action for SPA |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_PX_INIT` | WF mail action for SPA - initialization |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_S1_ACTION` | WF mail action for separation | YES (s081) — per-event mail class (FINAL leaf) | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_S1_CHECK` | WF mail checkout for separation |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_S1_FINAL` | WF mail final for separation |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_PA_STAFF` | PA WF : send email with PDF to Staff |  | Mail ACTION family — one class per notification event |
| `YCL_HR_WF_MAIL_S1_STAFF` | Staff norification for separation |  | Mail family |
| `YCL_TO_DEL` |  |  | Dead object kept in package (anti-pattern: delete instead) |
| `YCX_HRWF` | Exception class for HR Workflow | YES (v1, S-63/S-72) | Domain exception class (Pattern 4) |

Out-of-package framework classes (sibling packages):

| Class | Package | Description | Deep-read |
|---|---|---|---|
| `YCL_HR_WF_MAIL_FACTORY` | YHR_OM_WF | Factory class for notification classes | YES (v1, S-63/S-72) |
| `YCL_HR_WF_MAIL_GENERATOR` | YHR_OM_WF | Mail generator for HR workflows | YES (s081) — mail engine base class (template method) — package YHR_OM_WF |
| `YCL_WF_UTILITIES` | YHR_OM_WF | Utilities class for WF | YES (v1, S-63/S-72) |
| `YCL_CA_UTILITIES` | YBC | Cross Application utilities | YES (v1, S-63/S-72) |
| `YCL_HRWF_MAIN_LX` | ZHR_DEV | HR WF main class for PA LWOP | YES (v1, S-63/S-72) |
| `YCL_HRWF_OPERATION` | ZHR_DEV | HR Workflow operation | YES (v1, S-63/S-72) |

## 2. Interfaces (INTF) — 11

| Interface | Description | Deep-read | Notes |
|---|---|---|---|
| `YIF_HRWF_ACTORS` | Interface for HR WF Actors | YES (v1, S-63/S-72) |  |
| `YIF_HRWF_MAIN` | Interface for WF main part | YES (v1, S-63/S-72) |  |
| `ZIWCI_DOC_DISPLAY` |  |  | Generated WDA component interface (ZIWCI* = SAP-generated, not a style reference) |
| `ZIWCI_PAWF_EVALUATION` |  |  | Generated WDA component interface (ZIWCI* = SAP-generated, not a style reference) |
| `ZIWCI_PAWF_INT_AGREE` |  |  | Generated WDA component interface (ZIWCI* = SAP-generated, not a style reference) |
| `ZIWCI_PAWF_INT_AGREE_INITIAL` |  |  | Generated WDA component interface (ZIWCI* = SAP-generated, not a style reference) |
| `ZIWCI_PAWF_INT_HP` |  |  | Generated WDA component interface (ZIWCI* = SAP-generated, not a style reference) |
| `ZIWCI_PAWF_LWOP` |  |  | Generated WDA component interface (ZIWCI* = SAP-generated, not a style reference) |
| `ZIWCI_PAWF_MAIN` |  |  | Generated WDA component interface (ZIWCI* = SAP-generated, not a style reference) |
| `ZIWCI_PAWF_SEPARATION` |  |  | Generated WDA component interface (ZIWCI* = SAP-generated, not a style reference) |
| `ZIWCI_PAWF_SPA` |  |  | Generated WDA component interface (ZIWCI* = SAP-generated, not a style reference) |

## 3. Function groups (FUGR) — 37 in package, with their FMs

Most FUGRs here are **view-maintenance groups** (generated by SE54 for the YV*/YT* maintenance views —
2 generated FMs each, TABLEPROC_/TABLEFRAME_). The hand-written ones are `YHRPAWF1` and `YHR_WF_EVENT`.

| Function group | Description | FMs | FM names |
|---|---|---|---|
| `YHRPAWF1` | Functon Group PA WF | 9 | `Y_HRPAWF_EVENT_RULES_PA0000`, `Y_HRPAWF_NEXT_ACTOR`, `Y_HRPAWF_POWL_INTERN_AGREEMENT`, `Y_HRPAWF_POWL_INTERN_EVAL`, `Y_HRPAWF_POWL_LWOP`, `Y_HRPAWF_POWL_SEPARATION`, `Y_HRPAWF_POWL_SPA`, `Y_HR_PAWF_FILL_REQUEST`, `Y_HR_PAWF_MANAGE_LETTER` |
| `YHR_WF_EVENT` | HR Workflows event | 1 | `Y_HR_SWW_NOTIF_P_END_F` |
| `YTHRINTWF_ATG` | Extended Table Maintenance (Generated) | 2 | `TABLEFRAME_YTHRINTWF_ATG`, `TABLEPROC_YTHRINTWF_ATG` |
| `YTHRINTWF_ATT` | Extended Table Maintenance (Generated) | 2 | `TABLEFRAME_YTHRINTWF_ATT`, `TABLEPROC_YTHRINTWF_ATT` |
| `YTHRINTWF_TYPE` | Extended Table Maintenance (Generated) | 2 | `TABLEFRAME_YTHRINTWF_TYPE`, `TABLEPROC_YTHRINTWF_TYPE` |
| `YTHRINT_DS` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YVHRINT_DS`, `VIEWPROC_YVHRINT_DS` |
| `YTHRINT_FS` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YVHRINT_FS`, `VIEWPROC_YVHRINT_FS` |
| `YTHRINT_S` | Extended Table Maintenance (Generated) | 2 | `TABLEFRAME_YTHRINT_S`, `TABLEPROC_YTHRINT_S` |
| `YTHRPAWF_ABP_M` | Extended Table Maintenance (Generated) | 2 | `TABLEFRAME_YTHRPAWF_ABP_M`, `TABLEPROC_YTHRPAWF_ABP_M` |
| `YTHRPAWF_ATT` | Extended Table Maintenance (Generated) | 2 | `TABLEFRAME_YTHRPAWF_ATT`, `TABLEPROC_YTHRPAWF_ATT` |
| `YTHRPAWF_FWD` | Extended Table Maintenance (Generated) | 2 | `TABLEFRAME_YTHRPAWF_FWD`, `TABLEPROC_YTHRPAWF_FWD` |
| `YTHRPDF_TEXT` | Extended Table Maintenance (Generated) | 2 | `TABLEFRAME_YTHRPDF_TEXT`, `TABLEPROC_YTHRPDF_TEXT` |
| `YTHRWF_ACT_TY` | Maintenance table YTHRWF_ACT_TY | 2 | `TABLEFRAME_YTHRWF_ACT_TY`, `TABLEPROC_YTHRWF_ACT_TY` |
| `YTHRWF_STEP` | Dialog maintenance for table YTHRWF_STEP | 2 | `TABLEFRAME_YTHRWF_STEP`, `TABLEPROC_YTHRWF_STEP` |
| `YTHRWF_SUBSTEP` | Dialog maintenance for YTHRWF_SUBSTEP | 2 | `TABLEFRAME_YTHRWF_SUBSTEP`, `TABLEPROC_YTHRWF_SUBSTEP` |
| `YTHRWF_TYPE` | Extended Table Maintenance (Generated) | 2 | `TABLEFRAME_YTHRWF_TYPE`, `TABLEPROC_YTHRWF_TYPE` |
| `YTHR_PAF_PDF` | Extended Table Maintenance (Generated) | 2 | `TABLEFRAME_YTHR_PAF_PDF`, `TABLEPROC_YTHR_PAF_PDF` |
| `YTHR_SPA_GRADE` | Extended Table Maintenance (Generated) | 2 | `TABLEFRAME_YTHR_SPA_GRADE`, `TABLEPROC_YTHR_SPA_GRADE` |
| `YV5UB1` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YV5UB1`, `VIEWPROC_YV5UB1` |
| `YV5UBE` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YV5UBE`, `VIEWPROC_YV5UBE` |
| `YVHRPAWF_ACTION` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YVHRPAWF_ACTION`, `VIEWPROC_YVHRPAWF_ACTION` |
| `YVHRPAWF_AP` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YVHRPAWF_AP`, `VIEWPROC_YVHRPAWF_AP` |
| `YVHRPAWF_ATTC` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YVHRPAWF_ATTC`, `VIEWPROC_YVHRPAWF_ATTC` |
| `YVHRPAWF_ATTW` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YVHRPAWF_ATTW`, `VIEWPROC_YVHRPAWF_ATTW` |
| `YVHRPAWF_GD1` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YVHRPAWF_GD1`, `VIEWPROC_YVHRPAWF_GD1` |
| `YVHRPAWF_GD2` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YVHRPAWF_GD2`, `VIEWPROC_YVHRPAWF_GD2` |
| `YVHRPAWF_ROM` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YVHRPAWF_ROM`, `VIEWPROC_YVHRPAWF_ROM` |
| `YVHRPAWF_WT` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YVHRPAWF_WT`, `VIEWPROC_YVHRPAWF_WT` |
| `YVHRWF_ACT_DEF` | Maintenance view for YVHRWF_ACT_DEF | 2 | `VIEWFRAME_YVHRWF_ACT_DEF`, `VIEWPROC_YVHRWF_ACT_DEF` |
| `YVHRWF_ACT_IDENT` | Manage WF actor type identification | 2 | `VIEWFRAME_YVHRWF_ACT_IDENT`, `VIEWPROC_YVHRWF_ACT_IDENT` |
| `YVHRWF_STEP_ACT` | Maintenance view for YVHRWF_STEP_ACT | 2 | `VIEWFRAME_YVHRWF_STEP_ACT`, `VIEWPROC_YVHRWF_STEP_ACT` |
| `YVHR_AGENCY_T` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YVHR_AGENCY_T`, `VIEWPROC_YVHR_AGENCY_T` |
| `YV_T7UNPAD_PFST` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YV_T7UNPAD_PFST`, `VIEWPROC_YV_T7UNPAD_PFST` |
| `YV_T7UNPAD_PFUN` | Extended Table Maintenance (Generated) | 2 | `VIEWFRAME_YV_T7UNPAD_PFUN`, `VIEWPROC_YV_T7UNPAD_PFUN` |
| `Y_HR_SPA` | Function group for PAWF SPA | 1 | `Y_HRPAWF_SPA` |
| `Y_HR_SWLOP` | Function group WF SWLOP | 1 | `Y_HRPAWF_SWLOP_2001` |
| `ZE_MTH_SERV` |  | 2 | `TABLEFRAME_ZE_MTH_SERV`, `TABLEPROC_ZE_MTH_SERV` |

### YHRPAWF1 function modules (the hand-written WF group)

| FM | Description | Deep-read |
|---|---|---|
| `Y_HRPAWF_EVENT_RULES_PA0000` | Event Creation Rules - Table PA0000 (Employee Actions) | YES (s081) — SAP-contract FM (WF event rule) |
| `Y_HRPAWF_NEXT_ACTOR` | Determine next actor for PA Workflow | YES (v1, S-63/S-72) |
| `Y_HRPAWF_POWL_INTERN_AGREEMENT` | OM WF Call Webdynpro Application from Work Item Position |  |
| `Y_HRPAWF_POWL_INTERN_EVAL` | OM WF Call Webdynpro Application from Work Item Position |  |
| `Y_HRPAWF_POWL_LWOP` | PA WF Call Webdynpro Application from Work Item LWOP |  |
| `Y_HRPAWF_POWL_SEPARATION` | OM WF Call Webdynpro Application from Work Item Position |  |
| `Y_HRPAWF_POWL_SPA` | PA WF Call Webdynpro Application from Work Item SPA |  |
| `Y_HR_PAWF_FILL_REQUEST` | Fill request for offboarding FIORI dashboard | YES (s081) — bridge FM (WF -> Fiori dashboard via singleton class) |
| `Y_HR_PAWF_MANAGE_LETTER` | Manage letter in content server for FIORI apps |  |

## 4. Programs (PROG) — 16

| Program | Description | Deep-read | Notes |
|---|---|---|---|
| `YBC_DOCX_TO_PDF_FOR_SHORTCUT` | Convert word document into pdf file |  |  |
| `YBC_DOCX_TO_PDF_SLWOP` | Convert word document into pdf file |  |  |
| `YHR_PA_WF_ATTACHMENT_MANAGE` | Manage PA WF attachments |  |  |
| `YHR_PA_WF_LETTER_TO_FIORI` | Set WF letter to FIORI apps |  |  |
| `YHR_TO_DEL` |  |  | Dead object kept in package |
| `YHR_USER_INTERN` | Maintain intern's user |  |  |
| `YHR_WF_EVAL_START_USER` | Start WF Evaluation / Send notification (maintain user) |  |  |
| `YHR_WF_INTERN_SEPARATION` | Create separation measeure for Intern |  |  |
| `YHR_WF_PA_LIST_1` | Reporting Workflow Personnel Administration | YES (s081) — report-as-thin-shell + _BL class pattern | Main WF reporting program |
| `YHR_WF_PA_LIST_1_DATA` | Include YHR_WF_PA_LIST_1_DATA | YES (s081) — DATA include of the 3-file report split | DATA include of YHR_WF_PA_LIST_1 |
| `YHR_WF_PA_LIST_1_SEL` | Include YHR_WF_PA_LIST_1_SEL | YES (s081) — SELECTION-SCREEN include (events + F4 idioms) | SELECTION-SCREEN include of YHR_WF_PA_LIST_1 |
| `YHR_WF_SEP_TOOL` | WF Separation : Complete WF when personnel is left |  |  |
| `YHR_WF_UPDATE_INTERNS_GOS` | Update designation of interns agreement in GOS |  |  |
| `YIMGPAWF` | IMG PA Workflow |  | IMG structure program |
| `YRBUS1065` | Program for object type YBUS1065 : EmployeeUnesco |  | BOR program for YBUS1065 |
| `YRBUS2065` |  |  | BOR program for YBUS2065 |

## 5. BOR objects (SOBJ) + Workflow templates/tasks

| Object | Type | Notes |
|---|---|---|
| `YBUS1065` | SOBJ (BOR object type) | Deep-read v1 (YBUS1065 = EmployeeUnesco) |
| `YBUS2065` | SOBJ (BOR object type) |  |
| 9 workflow templates | PDWS | 98100013, 98100016, 98100017, 98100018, 98100019, 98100020, 98100021, 98100022, 98100023 |
| 18 standard tasks | PDTS | 98100055, 98100056, 98100057, 98100058, 98100059, 98100060, 98100061, 98100062, 98100063, 98100064, 98100065, 98100066, 98100070, 98100071, 98100072, 98100073, 98100074, 98100075 |

## 6. DDIC — Tables and structures (TABL) — 193

Naming families (the structure prefix IS the convention):

- `YTHRWF_*` — WF engine catalog tables (type/step/actor) — the core covered in style guide §12
- `YTHRPAWF_*` — PA-WF specific config + temp-save tables
- `YTHRINT*` — Internship WF tables
- `YSHRWF_*` / `YSHR_*` — structures (`YS` prefix = structure, not table)
- `YSHR_DD_*` — Web Dynpro dropdown structures (one per dropdown)
- `YSHR_WD_*` — Web Dynpro context node structures (one per infotype/view)
- `ZSHR_JSON_*` — SuccessFactors JSON interface structures

| Table/structure | Description | Deep-read |
|---|---|---|
| `T9SCT_T` |  |  |
| `YAAGENCY_T` | Long code for Agency |  |
| `YSHRPDF_TEXT` | Element text for PDF + text |  |
| `YSHRWF_ACTORS` | HR WF actors |  |
| `YSHRWF_ACTOR_TYPE` | HR WF actor type |  |
| `YSHRWF_STEPS` | HR Wf steps |  |
| `YSHRWF_USER_DATA` | HR WF user data |  |
| `YSHR_ADM_DETAILS` | Data for Administrative Details |  |
| `YSHR_ADM_DETAILS_LINE` | Structure form Administrative details |  |
| `YSHR_ADM_DET_DEP` | Administrative details : dependents |  |
| `YSHR_ADM_DET_HEAD_FOOT` | Administrative details header and footer |  |
| `YSHR_ATTES_SAL_ST2` |  |  |
| `YSHR_DATA_NAME` | Data for HR name |  |
| `YSHR_DD_AGENCY` | Dropdown Agency |  |
| `YSHR_DD_BCOVR` | Drop down PA WF BCOVR Benefit Insurance Option |  |
| `YSHR_DD_BOPTI` | Drop down PA WF BOPTI Benefit Health Plan Option |  |
| `YSHR_DD_BPLAN` | Drop down PA WF BPLAN Benefit plan |  |
| `YSHR_DD_DEPCV` | Drop down PA WF DEPCV Benefit dependent coverage |  |
| `YSHR_DD_INT_ATTTY` | WD Dropdown Attachmen type for Internship |  |
| `YSHR_DD_INT_BTRTL` | WD Dropdown Personnel Sub Area |  |
| `YSHR_DD_INT_DSTAT` | Dropdown Duty Station |  |
| `YSHR_DD_INT_FULLNAME` | Dropdown Intership, FullName |  |
| `YSHR_DD_INT_ITYPE` | Dropown Internship Type |  |
| `YSHR_DD_INT_NATIO` | WD Dropfown Nationality |  |
| `YSHR_DD_INT_OBJID` | Dropdown OJID |  |
| `YSHR_DD_INT_ORGEH` | Dropdown ORGEH |  |
| `YSHR_DD_INT_SCHKZ` | Drop down work schedule |  |
| `YSHR_DD_LAND1` | Drop down country (code + text in STRING) |  |
| `YSHR_DD_LGART` | Drop down PA WF LGART |  |
| `YSHR_DD_MASSG` | Drop down PA WF MASSG |  |
| `YSHR_DD_MASSN` | Drop down PA WF MASSN |  |
| `YSHR_DD_PFSCH` | Drop down PA WF PSFTA (Pension Fund Scheme) |  |
| `YSHR_DD_PFSTA` | Drop down PA WF PSFTA (Pension Fund Status Indicator) |  |
| `YSHR_DD_PLTYP` | Drop down PA WF PLTYP Benefit plan type |  |
| `YSHR_DD_SECT` | Dropdown Sector + text |  |
| `YSHR_DD_STEP` | WF PA Dropdown STEP |  |
| `YSHR_DD_TRFGR` | WD structure for DropDown Grade (TRFGR) |  |
| `YSHR_DD_TRFST` | Structure Dropdown Level (step) : TRFST |  |
| `YSHR_DD_WFTYPE` | Dropdown WF PA Workflo type |  |
| `YSHR_EVAL_HEADER` | Internship Evaluation - header data |  |
| `YSHR_EVAL_INTERN` | Evluation for Internship (Intern or Supervisor) |  |
| `YSHR_IF_INT_CONTRACT` | Structure interface PDF Agreement Internship |  |
| `YSHR_INT_AGREE_PDF` | Structure for PDF Internship Agreement |  |
| `YSHR_INT_AGR_DATA` | Data for PDF internship agreement |  |
| `YSHR_INT_AGR_DATA_V2` | Data for PDF internship Agreement (V2) |  |
| `YSHR_INT_COMPLETION_PDF` | Interface for PDF internship completion certificate |  |
| `YSHR_INT_SF` | Structure for SF candidates |  |
| `YSHR_INT_SF_FILE` | Structure for file FROM Success Factors |  |
| `YSHR_MODEL` | WF PA id Model |  |
| `YSHR_PAF_PDF` | Text displayed on PAF SPA or LWOP |  |
| `YSHR_PA_DRAFT` | Structure for Draft WF PA |  |
| `YSHR_PDF_PAF` | Informations to display on  PAF PDF |  |
| `YSHR_PDF_PAF_LINE` | Line PDF PAF |  |
| `YSHR_R_ASTXT` | Range ASTXT (Internship Status text) |  |
| `YSHR_R_ITYPET` | Range ASTXT (Internship type text) |  |
| `YSHR_SPA_PAF` | Informations to display on SPA PAF PDF |  |
| `YSHR_SPA_PAF_LINE` | Line PDF SPA PAF |  |
| `YSHR_WD_0000` | PA WF : Structure for infotype 0000 |  |
| `YSHR_WD_0001` | PA WF : Structure for infotype 0001 |  |
| `YSHR_WD_0002` | PA WF : Structure for node Identity |  |
| `YSHR_WD_0006` | PA WF Structure for Address |  |
| `YSHR_WD_0008` | PA WF : Structure for infotype 0008 |  |
| `YSHR_WD_0015` | PA WF : structure for infotype 0015 |  |
| `YSHR_WD_0016` | PA WF : Structure for infotype Contract |  |
| `YSHR_WD_0041` | WF PA : Structure for dates infotypes 0041 |  |
| `YSHR_WD_0105_MAIL` | PA WF Mail |  |
| `YSHR_WD_0167` | PA WF : Structure for node Health Plans |  |
| `YSHR_WD_0168` | PA WF : Structure for node Insurance Plans |  |
| `YSHR_WD_0168_PLTYP` | Repeat structure for WD table 0168 |  |
| `YSHR_WD_0168_SELEC` | Repeat structure for selected dependents |  |
| `YSHR_WD_0351` | WF PA : Structure Infotype Home Country |  |
| `YSHR_WD_0395` | PA WF : Structure for infotype 0395 |  |
| `YSHR_WD_0961` | PA WF : Structure for infotype 0961 |  |
| `YSHR_WD_ATTTY` | PA WF attachment type |  |
| `YSHR_WD_ATT_MENU` | OM WF Attributes for button OM WF |  |
| `YSHR_WD_DEPENDANT` |  |  |
| `YSHR_WD_DEPENDENT` | WF PA : dependant |  |
| `YSHR_WD_EVALSCALE` | WD Internship Scale |  |
| `YSHR_WD_EVALT` | WD Internship evaluation with text |  |
| `YSHR_WD_EVALV` | WD Internship evaluation with value |  |
| `YSHR_WD_INTERAGENCY` | WD LWOP Inter-Agency |  |
| `YSHR_WD_INT_ATTACH` | WD Structure Attachment for Internship |  |
| `YSHR_WD_INT_CONTRACT` | WD Internship Agreement, Contrat Data |  |
| `YSHR_WD_INT_FILE` | Structure for Attachment |  |
| `YSHR_WD_INT_KEY` | Data key WD Intership Management |  |
| `YSHR_WD_INT_MGV` | Strcutre WD Internship My Global View |  |
| `YSHR_WD_INT_PERSDATA` | WD Internship Agreement, Personal Data |  |
| `YSHR_WD_INT_SELEC` | Structure WD HP Internship |  |
| `YSHR_WD_INT_UIEATTR` | Structure WD Internship UI Attributes |  |
| `YSHR_WD_INT_UIESTATE` | Structure WD Internship UI Attributes |  |
| `YSHR_WD_LWOP` | PA WF Leave Wihtout Pay Key Field |  |
| `YSHR_WD_LWOP_LETTER` | PA WF : Letter separation |  |
| `YSHR_WD_LWOP_UIEATTR` | Structure WD Separation UI Attributes |  |
| `YSHR_WD_LWOP_UIESTATE` | Structure WD Separation UI Attributes state |  |
| `YSHR_WD_MSG` | WF Strcture for message |  |
| `YSHR_WD_PA_CUR_POS` | WD PA  current position |  |
| `YSHR_WD_PA_DATA_OM` | PA WF : data from OM |  |
| `YSHR_WD_PA_DRAFT` | WF PA WDA : Draft table (with text) |  |
| `YSHR_WD_PA_POS` | WF WD PA position (with grades) |  |
| `YSHR_WD_PA_SPA` | WD WF Fields Special Post Allowance |  |
| `YSHR_WD_POST_PA` | PA WF : Structure for data linked to position |  |
| `YSHR_WD_RETURN_RIGHTS` | Structure LWOP : Return Right |  |
| `YSHR_WD_SEPARATION` | PA WF Separation Key Field |  |
| `YSHR_WD_SEP_LETTER` | PA WF : Letter separation |  |
| `YSHR_WD_SEP_LETTER1` | PA WF : Letter separation Input field WD |  |
| `YSHR_WD_SEP_LETTER2` | PA WF : Letter separation display field WD |  |
| `YSHR_WD_SEP_UIEATTR` | Structure WD Separation UI Attributes |  |
| `YSHR_WD_SEP_UIESTATE` | Structure WD Separation UI Attributes |  |
| `YSHR_WD_SIG_LETTER` | WF PA : for dropdown user Tile LastName Firstname / PERNR |  |
| `YSHR_WD_SPA` | PA WF Special Post Allowance Key Field |  |
| `YSHR_WD_SPA_CUR_POS` |  |  |
| `YSHR_WD_SPA_UIEATTR` | Structure WD SPA UI Attributes |  |
| `YSHR_WD_SPA_UIESTATE` | Structure WD SPA UI State (required) |  |
| `YSHR_WD_STATE_MENU` | OM WF Attributes for menu PA WF |  |
| `YSHR_WFTYPE_RANGE` | Structure for workflow type range |  |
| `YSHR_WF_HIS_WFSTEP` | PA WF Step Historic |  |
| `YSHR_WF_REPORT_2` | Workflow report PA |  |
| `YSHR_WF_STEP_LAST_NEXT` | Structure for container WF OM |  |
| `YSHR_XML_LWOP` | Field for XML LWOP Letter |  |
| `YSHR_XML_SEP` | Field for XML Separation Letter |  |
| `YT5UB1` | Benefit plan type used in WF LWOP |  |
| `YT5UBE` | Benefit Health Plan Option used in WD LWOP |  |
| `YTHRINTWF_ATG` | Grouping Attachment type Internship |  |
| `YTHRINTWF_ATGT` | Grouping Text Attachment type Internship |  |
| `YTHRINTWF_ATT` | Internship WF Attachment Type |  |
| `YTHRINTWF_ATTT` | Internship WF Attachment Type text |  |
| `YTHRINTWF_TYPE` | Internship Type |  |
| `YTHRINTWF_TYPET` | Internship Type text |  |
| `YTHRINT_ATTACH` | WF Internship Agreement - Attachment |  |
| `YTHRINT_DRAFT` | WF Internship Agreement - DRAFT |  |
| `YTHRINT_DS` | Determine Status of Internship Agreement |  |
| `YTHRINT_FS` | Internship : Status / Functions |  |
| `YTHRINT_S` | Status for internship agreement |  |
| `YTHRINT_S_T` | Status for internship agreement |  |
| `YTHRINT_T1` | WF Internship Agreement - TMP data Identity - Address |  |
| `YTHRINT_T2` | WF Internship Agreement - TMP data Agreement |  |
| `YTHRINT_T3` | WF Internship Agreement - TMP data cost distribution |  |
| `YTHRPAWF_ABP_M` | Assistant BFM/PAY mail according initial of the staff's name |  |
| `YTHRPAWF_ACTION` | PA WF : Action (0000) by WF type |  |
| `YTHRPAWF_AP` | WF PA Additional Payment by WF Type |  |
| `YTHRPAWF_ATT` | PA WF Attachment Type |  |
| `YTHRPAWF_ATTACH` | Attachment for Workflow PA |  |
| `YTHRPAWF_ATTC` | PA WF Attachment Type required |  |
| `YTHRPAWF_ATTT` | Attachement Type (Text) |  |
| `YTHRPAWF_ATTW` | PA WF Attachment Type used by Workflow Type |  |
| `YTHRPAWF_DRAFT` | Save draft PA WF |  |
| `YTHRPAWF_FWD` | PA WF List of field in WD view |  |
| `YTHRPAWF_FWDT` | PA WF Field in WD view - text |  |
| `YTHRPAWF_GD1` | Generation of document PA, model - chrono and conditions |  |
| `YTHRPAWF_GD2` | Generation of document PA LWOP conditions for model |  |
| `YTHRPAWF_MSERV` | PA WF Separation : Month / Yeayr of service |  |
| `YTHRPAWF_ROM` | PA WF  : Field Read Only |  |
| `YTHRPAWF_TMP1` | WF Separation Save (temporary) info Letter |  |
| `YTHRPAWF_TMP2` | WF Separation Save (temporary) info Payment Deduction |  |
| `YTHRPAWF_TMP3` | WF SPA Save (temporary) data Special Position |  |
| `YTHRPAWF_TMP4` | WF LWOP Save (temporary) data |  |
| `YTHRPAWF_WT` | PA WF Wage Type included in Amount |  |
| `YTHRPDF_TEXT` | Text element for PDF |  |
| `YTHRPDF_TEXT_T` | Element de texte pour PDF |  |
| `YTHRWF_ACT_DEF` | HR WF Actor Identification | YES (v1, S-63/S-72) |
| `YTHRWF_ACT_IDENT` | Actor type identification parameters |  |
| `YTHRWF_ACT_TY` | HR WF Actor type |  |
| `YTHRWF_ACT_TYT` | HR WF Actor type designation |  |
| `YTHRWF_STEP` | Workflow steps | YES (v1, S-63/S-72) |
| `YTHRWF_STEPT` | Workflow steps designation | YES (v1, S-63/S-72) |
| `YTHRWF_STEP_ACT` | HR WF Acotrs per step | YES (s081) — step-actor assignment table (DDIF_FIELDINFO_GET) |
| `YTHRWF_SUBSTEP` | HR WF substep |  |
| `YTHRWF_SUBSTEPT` | HR WF substep designation |  |
| `YTHRWF_TYPE` | Workflow type | YES (v1, S-63/S-72) |
| `YTHRWF_TYPET` | Workflow type text |  |
| `YTHR_PAF_PDF` | Text used on PAF PDF SPA - LWOP |  |
| `YTHR_SPA_GRADE` | Post authorized grade for a personnel grade |  |
| `YWFRR` | Structure WF LWOP for feature |  |
| `ZAT7UNPAD_PFST` |  |  |
| `ZAT7UNPAD_PFUN` |  |  |
| `ZSHR_JSON_CAND` |  |  |
| `ZSHR_JSON_DATA` |  |  |
| `ZSHR_JSON_FILE` |  |  |
| `ZSHR_JSON_FILE_INDEX_CAND` |  |  |
| `ZSHR_JSON_INT_HIRED` |  |  |
| `ZSHR_JSON_JOBREQ` |  |  |
| `ZSHR_JSON_JOBREQLOC` |  |  |
| `ZSHR_JSON_META_ATTACH` |  |  |
| `ZSHR_JSON_META_GENDER` |  |  |
| `ZSHR_JSON_META_NATIO` |  |  |
| `ZSHR_JSON_META_STATUS` |  |  |
| `ZSHR_JSON_RES_ATTACH` |  |  |
| `ZSHR_JSON_RES_GENDER` |  |  |
| `ZSHR_JSON_RES_INDEX_CAND` |  |  |
| `ZSHR_JSON_RES_JOB_REQ_LOCALE` |  |  |
| `ZSHR_JSON_RES_LOCALE` |  |  |
| `ZSHR_JSON_RES_NATIO` |  |  |
| `ZSHR_JSON_RES_PA_INDEX_CAND` |  |  |

## 7. DDIC — Maintenance views (VIEW) — 21

| View | Description |
|---|---|
| `YV5UB1` | Generated Table for View |
| `YV5UBE` | Generated Table for View |
| `YVDB_DSCC` | Generated Table for View |
| `YVHRINT_DS` | Generated Table for View |
| `YVHRINT_FS` | Generated Table for View |
| `YVHRPAWF_ACTION` | Generated Table for View |
| `YVHRPAWF_AP` | Generated Table for View |
| `YVHRPAWF_ATTC` | Generated Table for View |
| `YVHRPAWF_ATTW` | Generated Table for View |
| `YVHRPAWF_GD1` | Generated Table for View |
| `YVHRPAWF_GD2` | Generated Table for View |
| `YVHRPAWF_ROM` | Generated Table for View |
| `YVHRPAWF_WT` | Generated Table for View |
| `YVHRWF_ACT_DEF` | Generated Table for View |
| `YVHRWF_ACT_IDENT` | Generated Table for View |
| `YVHRWF_STEP_ACT` | Generated Table for View |
| `YVHR_AGENCY_T` | Generated Table for View |
| `YV_T7UNPAD_PFST` | Generated Table for View |
| `YV_T7UNPAD_PFUN` | Generated Table for View |
| `ZT7UNPAD_PFST` |  |
| `ZV_T7UNPAD_PFUN` |  |

## 8. DDIC — Data elements / Domains / Table types

- **105 data elements** (`YE_*` pattern dominates)
- **16 domains**
- **68 table types** (`YT*`/`YTT*` pattern)

<details><summary>Full DTEL list</summary>

| Data element | Description |
|---|---|
| `YEHR_LGCODE` | Long code for UN agency |
| `YE_AMTTY` | Amount type |
| `YE_DEPNR` | Number of dependents |
| `YE_GRST` | Grade and Step |
| `YE_HRINT_AGRST` | Status for internship agreement |
| `YE_HRINT_AGRTY` | Type of agreement |
| `YE_HRINT_ASTXT` | Text status of agreement internship |
| `YE_HRINT_BUTTON` | WD Column Button |
| `YE_HRINT_EPOQ` | Past, Ongoing, Future |
| `YE_HRINT_EVALS` | With Supervisor's evaluation |
| `YE_HRINT_SHORT` | Internship period < 1 month |
| `YE_HRSF_EC_LAND1` | External code Sucess Factor for country |
| `YE_HRWF_ABAP_DET` | ABAP determination |
| `YE_HRWF_ABAP_ID` | ID linked to ABAP method |
| `YE_HRWF_ACTOR_CASE` | Actor case |
| `YE_HRWF_ACTOR_CLASS` | HR WF Actor Class |
| `YE_HRWF_ACTOR_TYPE` | Actor type |
| `YE_HRWF_CURRENT_AOS` | Current Actor or Step |
| `YE_HRWF_FIXED` | Model fixed - no dynamic data |
| `YE_HRWF_FOLDER` | Folder for workflow documents |
| `YE_HRWF_GO_TO_ACT_DEF` | Go to actor determination table |
| `YE_HRWF_INITIATOR` | Workflow initiator |
| `YE_HRWF_MAIN_CLASS` | HR WF Main Class |
| `YE_HRWF_ORG_DEPTH` | Org unit depth |
| `YE_HRWF_RRIGHT` | LWOP Return Rights (Generic or Specific) |
| `YE_HRWF_SEARCH_SEQUENCE` | Search sequence |
| `YE_HRWF_STEP` | Workflow step |
| `YE_HRWF_STEP_SEQ` | WF step sequence |
| `YE_HRWF_SUBSTEP` | HR WF substep |
| `YE_HRWF_TYPE` | HR WF : Type of Workflow |
| `YE_HRWF_WHOOU` | Population of org unit |
| `YE_HR_GRPAT_TXT` | Text group Attachment type |
| `YE_HR_HOMLC` | Home leave credits |
| `YE_HR_IATRF` | Inter Agency : Type of transfer |
| `YE_HR_IDTEXT` | Id text element for PDF |
| `YE_HR_INIT_AGREE` | Initiator WF Internship Agreement |
| `YE_HR_INTWF_ATTSH` | Attachment short text |
| `YE_HR_INTWF_ATTTY` | Attachment Type for Internship Agreement |
| `YE_HR_INTWF_ATTXT` | Text Attachment type |
| `YE_HR_INTWF_GRPAT` | Grouping Attachement type Internship |
| `YE_HR_ITYPE` | Internship Type |
| `YE_HR_ITYPET` | Text Type of Internship |
| `YE_HR_LHLRD` | Last home leave return date |
| `YE_HR_POST_GRADE_FROM` | Post grade from |
| `YE_HR_POST_GRADE_TO` | Post grade to |
| `YE_HR_SECT_TXT` | Text Sector |
| `YE_IDENT` | Identity :  Last Name First Name |
| `YE_INITLETTER` | Initial letter |
| `YE_LIPNR` | Number of Life Insurance Plans |
| `YE_MANAGER_NAME` | Manager's name |
| `YE_MBFCTBNR` | Number of contributions MBF |
| `YE_POS_SHST` | Position number (SHORT) and Title (STEXT) |
| `YE_TUTOR_NAME` | Supervisor's name |
| `YE_YEAR_SERV` | Number of Year of service |
| `ZE01_FIRST_UN` |  |
| `ZE06_DUTY` |  |
| `ZE19_RETIR` |  |
| `ZE20_CATEGORY` |  |
| `ZEAN_MENS2` |  |
| `ZEPAWF_ATTSH` |  |
| `ZEPAWF_ATTTX` |  |
| `ZEPAWF_ATTTY` |  |
| `ZEPAWF_WSTEP` |  |
| `ZEU6_DS` |  |
| `ZEUSEWD` |  |
| `ZE_ABOPO` |  |
| `ZE_AMT_BAL` |  |
| `ZE_AMT_DIS` |  |
| `ZE_AMT_DIS_USD` |  |
| `ZE_AMT_LEAVE` |  |
| `ZE_AMT_NOT` |  |
| `ZE_AMT_OVER` |  |
| `ZE_AMT_TERM` |  |
| `ZE_AUSEP` |  |
| `ZE_CTRIB` |  |
| `ZE_DAY_LEAVE` |  |
| `ZE_DTFOR` |  |
| `ZE_DTPCT` |  |
| `ZE_DUCON` |  |
| `ZE_FULLNAME` |  |
| `ZE_GESCHTXT` |  |
| `ZE_IDENT` |  |
| `ZE_IDTXT` |  |
| `ZE_INDMD` |  |
| `ZE_LANGU` |  |
| `ZE_LETDT` |  |
| `ZE_LETRF` |  |
| `ZE_LTOYEAR` |  |
| `ZE_MODELWORD` |  |
| `ZE_MTH_NOTICE` |  |
| `ZE_MTH_SERV` |  |
| `ZE_NUATTPA` |  |
| `ZE_PAYDED` |  |
| `ZE_PLADE` |  |
| `ZE_PLADS` |  |
| `ZE_SHIHG` |  |
| `ZE_SHIPE` |  |
| `ZE_TOTAIR` |  |
| `ZE_TOTLS_FT` |  |
| `ZE_TOTLS_NFT` |  |
| `ZE_TXTPAF` |  |
| `ZE_TXTPAFEN` |  |
| `ZE_TXTPAFFR` |  |
| `ZE_USED_LWOP` |  |
| `ZE_USED_SPA` |  |

</details>

<details><summary>Full DOMA / TTYP lists</summary>

Domains: `YD_AMTTY`, `YD_HRINT_AGRTY`, `YD_HRINT_EPOQ`, `YD_HRWF_ACTOR_TYPE`, `YD_HRWF_ORG_DEPTH`, `YD_HRWF_RRIGHT`, `YD_HRWF_STEP`, `YD_HRWF_SUBSTEP`, `YD_HRWF_TYPE`, `YD_HRWF_WHOOU`, `YD_IATRF`, `ZD_CTRIB`, `ZD_MTH_NOTICE`, `ZD_PAYDED`, `ZD_TOTLS_FT`, `ZE_LANGU`

Table types: `YTTHRINT_ATTACH`, `YTTHRPAWF_ATTACH`, `YTTHRPDF_TEXT`, `YTTHRWF_ACTORS`, `YTTHRWF_ACTOR_TYPE`, `YTTHRWF_STEPS`, `YTTHR_ADM_DETAILS`, `YTTHR_ADM_DET_DEP`, `YTTHR_DD_AGENCY`, `YTTHR_DD_BCOVR`, `YTTHR_DD_BOPTI`, `YTTHR_DD_BPLAN`, `YTTHR_DD_DEPCV`, `YTTHR_DD_INT_ATTTY`, `YTTHR_DD_INT_BTRTL`, `YTTHR_DD_INT_DSTAT`, `YTTHR_DD_INT_FULLNAME`, `YTTHR_DD_INT_ITYPE`, `YTTHR_DD_INT_NATIO`, `YTTHR_DD_INT_OBJID`, `YTTHR_DD_INT_ORGEH`, `YTTHR_DD_INT_SCHKZ`, `YTTHR_DD_LAND1`, `YTTHR_DD_LGART`, `YTTHR_DD_MASSG`, `YTTHR_DD_MASSN`, `YTTHR_DD_PFSCH`, `YTTHR_DD_PFSTA`, `YTTHR_DD_PLTYP`, `YTTHR_DD_SECT`, `YTTHR_DD_STEP`, `YTTHR_DD_TRFGR`, `YTTHR_DD_TRFST`, `YTTHR_DD_WFTYPE`, `YTTHR_EVAL_INTERN`, `YTTHR_INT_AGREE_PDF`, `YTTHR_INT_EVALT`, `YTTHR_INT_EVALV`, `YTTHR_INT_GRPAT`, `YTTHR_INT_SF`, `YTTHR_MODEL`, `YTTHR_PAF_PDF`, `YTTHR_PDF_PAF`, `YTTHR_SPA_PAF`, `YTTHR_WD_0015`, `YTTHR_WD_0168`, `YTTHR_WD_ATTTY`, `YTTHR_WD_DEPENDENT`, `YTTHR_WD_EVALSCALE`, `YTTHR_WD_INT_ATTACH`, `YTTHR_WD_INT_FILE`, `YTTHR_WD_INT_MGV`, `YTTHR_WD_MSG`, `YTTHR_WD_PA_DRAFT`, `YTTHR_WFTYPE_RANGE`, `YTTHR_WF_HIS_WFSTEP`, `YTTHR_WF_REPORT_2`, `YTTHR_XML_LWOP`, `YTTHR_XML_SEP`, `YTTSHR_INT_SF_FILE`, `YTTYHRINT_T3`, `ZTTHR_JSON_META_ATTACH`, `ZTTHR_JSON_META_GENDER`, `ZTTHR_JSON_META_NATIO`, `ZTTHR_JSON_RES_ATTACH`, `ZTTHR_JSON_RES_LOCALE`, `ZTTHR_JSON_RES_NATIO`, `ZTTHR_JSON_RES_PA_INDEX_CAND`

</details>

## 9. UI + integration layer

| Type | Objects |
|---|---|
| WDYN (Web Dynpro components) | `ZDOC_DISPLAY`, `ZPAWF_EVALUATION`, `ZPAWF_INT_AGREE`, `ZPAWF_INT_AGREE_INITIAL`, `ZPAWF_INT_HP`, `ZPAWF_LWOP`, `ZPAWF_MAIN`, `ZPAWF_SEPARATION`, `ZPAWF_SPA` |
| WDYA (Web Dynpro applications) | `ZDOC_DISPLAY`, `ZPAWF_EVALUATION`, `ZPAWF_INT_AGREE`, `ZPAWF_INT_AGREE_INITIAL`, `ZPAWF_INT_HP`, `ZPAWF_LWOP`, `ZPAWF_SEPARATION`, `ZPAWF_SPA`, `ZPAWF__MAIN` |
| SICF (ICF services (WDA)) | `D0135024       BPXI9KP2BASOTAFYZA1IQQI7C`, `D0135025       BPXI9KP2BASOTAFYZA1IQQI7C`, `D0135032       BPXI9KP2BASOTAFYZA1IQQI7C`, `ZDOC_DISPLAY   BPXI9KP2BASOTAFYZA1IQQI7C`, `ZPAWF_INT_AGREEBPXI9KP2BASOTAFYZA1IQQI7C`, `ZPAWF_INT_HP   BPXI9KP2BASOTAFYZA1IQQI7C`, `ZPAWF_LWOP     BPXI9KP2BASOTAFYZA1IQQI7C`, `ZPAWF_SPA      BPXI9KP2BASOTAFYZA1IQQI7C`, `ZPAWF__MAIN    BPXI9KP2BASOTAFYZA1IQQI7C` |
| SFPF (Adobe forms) | `YHRINT_AGREEMENT3`, `YHRINT_AGREEMENT_V2_EN`, `YHRINT_CERTIFICATE`, `YHRINT_CERTIFICATE2`, `YHRINT_EVALUATION`, `YHRPA_ADM_DETAIL`, `YHRPA_PAF`, `YHRPA_PAF_SAVE_120125` |
| SFPI (Adobe form interfaces) | `YHRINT_IF_AGREEMENT`, `YHRINT_IF_AGREEMENT_V2`, `YHRINT_IF_CERTFICATE`, `YHRINT_IF_EVALUATION`, `YHR_IF_ADM_DETAILS`, `YHR_IF_PAF` |
| TRAN (Transactions) | `YHRWF_REP2`, `YHRWF_UPLOAD_LETTER`, `YHR_USER_INTERN`, `YHR_WF_SEP_TOOL`, `YIMGPAWF`, `YPAWF_LETTER_PDF`, `YSWLOP_LETTER_PDF`, `Y_D01_47000054`, `Y_D01_47000055`, `Y_D01_47000056`, `Y_D01_47000057`, `Y_D01_47000058`, `Y_D01_47000059`, `Y_D01_47000060`, `Y_D01_47000061`, `Y_D01_47000062`, `Y_D01_47000067`, `Y_D01_47000068`, `Y_D01_47000076`, `Y_D01_47000077`, `Y_D01_47000078`, `Y_D01_47000093`, `Y_D01_47000094`, `Y_D01_47000095`, `Y_D01_47000096`, `Y_D01_47000097`, `Y_D01_47000098`, `Y_D01_47000099`, `Y_D01_47000156`, `Y_D01_47000157`, `Y_D01_47000158`, `Y_D01_47000159`, `Y_D01_47000160`, `Y_D01_47000161`, `Y_D01_47000162`, `Y_D01_47000165`, `Y_D01_47000169`, `Y_D01_47000171`, `Y_D01_47000172`, `Y_D01_47000173` |
| XSLT (XSLT transformations) | `YTR_LWOP_01`, `YTR_SEPARATION_01`, `YTR_WD_FORMATTEXT_TO_ADOBE` |
| NROB (Number range objects) | `YCONT_INT`, `YLWOP`, `YSEP` |
| MSAG (Message class) | `YWF_PA` |

## 10. N_MENARD beyond YHR_PA_WF — sibling packages

`TADIR WHERE AUTHOR = N_MENARD` returns 3463 objects. Distribution:

| Package | Objects | Role |
|---|---|---|
| `ZHR_DEV` | 809 | Older HR dev package — holds YCL_HRWF_MAIN_LX + YCL_HRWF_OPERATION |
| `$TMP` | 568 | Local objects (not transported) |
| `YA` | 548 | Cross-application Y objects |
| `YBC` | 329 | Basis/cross-app tools — holds YCL_CA_UTILITIES, Excel/BTCI/mail-auth tools |
| `ZHRDEV` | 324 | Older HR dev package |
| `YHR_OM_WF` | 195 | OM workflow framework (sibling of PA WF) — holds YCL_HR_WF_MAIL_FACTORY, YCL_WF_UTILITIES, YTHRWF_NOTIF |
| `YHR_PA_WF` | 135 | THIS package (PA workflow framework) |
| `YB` | 120 | Y basis objects |
| `/SDF/FDQ_API` | 111 | SAP support tool (not his design) |
| `YP` | 47 | HR/payroll objects |
| `ZTECH` | 46 | Technical sandbox |
| `ZHR_EVE` | 45 | HR events |
| `YV` | 36 | — |
| `YE` | 35 | — |
| `YL` | 32 | — |
| `YU` | 16 | — |
| `ZPM` | 12 |  |
| `YHR_CORE_MANAGER` | 10 | Core Manager interface |
| `ZRE_POSTINGS` | 9 |  |
| `YA_FEX` | 7 |  |
| `ZHRBENEFITS_FIORI` | 5 | Benefits Fiori |
| `ZHRPA` | 5 |  |
| `ZRE_WORKFLOW` | 4 |  |
| `ZRE_INVOICE` | 3 |  |
| `PBUN` | 3 |  |
| `ZRE_CONTRACT` | 2 |  |
| `PAOC_MSS` | 2 |  |
| `YT` | 1 | — |
| `ZBC` | 1 |  |
| `PC_WTI` | 1 |  |
| `BF_BANK` | 1 |  |
| `ZHR_INFOTYPE_EXTENSION` | 1 |  |

---

## 11. Deep-read log

**Prior (style guide v1, CRP S-63/S-72): 18 reference files** — see README.md of the style guide.
Note: the file named `YTHRWF_EVAL_PATH` in the v1 reference set has **no TADIR object of that name on D01**
(closest: eval-path logic lives in `YCL_WF_UTILITIES=>GET_OBJECTS_WITH_EVAL_PATH`). Flagged as naming drift.

**This session (s081) — new deep-reads via ADT GET (read-only):**

| Object | Type | Why chosen |
|---|---|---|
| `YCL_HR_WF_MAIL_GENERATOR` |  | mail engine base class (template method) — package YHR_OM_WF |
| `YCL_HR_WF_MAIL_GENERATOR_PA_S1` |  | per-WF-type mail data provider |
| `YCL_HR_WF_MAIL_PA_S1_ACTION` |  | per-event mail class (FINAL leaf) |
| `YHR_WF_PA_LIST_1` |  | report-as-thin-shell + _BL class pattern |
| `YHR_WF_PA_LIST_1_DATA` |  | DATA include of the 3-file report split |
| `YHR_WF_PA_LIST_1_SEL` |  | SELECTION-SCREEN include (events + F4 idioms) |
| `Y_HRPAWF_EVENT_RULES_PA0000` |  | SAP-contract FM (WF event rule) |
| `Y_HR_PAWF_FILL_REQUEST` |  | bridge FM (WF -> Fiori dashboard via singleton class) |
| `YTHRWF_STEP_ACT` |  | step-actor assignment table (DDIF_FIELDINFO_GET) |

**Golden locations** (code and objects are data too):

- Sources (canonical, brain-ingested): `extracted_code/HCM/YHR_PA_WF/` — 8 .abap + table-structure JSON.
- Object catalog (Gold DB, D01 provenance): `d01_tadir_yhr_pa_wf` (740), `d01_tadir_nmenard` (3,463),
  `d01_tfdir_nmenard_fugr` (297 FMs) in `p01_gold_master_data.db`.
- Raw session artifact: `Zagentexecution/tasks/2026_06_10_nmenard_inventory/` (scan JSON + readback).

## 12. Style-guide impact

See `UNESCO-ABAP-STYLE-GUIDE.md` — "Extended patterns (from full D01 scan)" subsections appended in s081.
