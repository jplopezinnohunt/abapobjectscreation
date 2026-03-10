# UNESCO NGO-Specific Infotypes & Data Extraction Protocol

UNESCO, as an International Organization (NGO-like structure), uses a combination of standard SAP HCM infotypes and highly customized "UNESCO fields" to manage its diverse workforce across various global regions.

## 1. Infotype Registry: Application Coverage

| Application | Infotype | Purpose | UNESCO Custom Fields / Notes |
| :--- | :--- | :--- | :--- |
| **Personal Data (ESS)** | `0002` | Personal Data | `ZZREGGR` (UNESCO Regional Grouping). |
| | `0021` | Family/Dependents | Custom UNESCO education attendance checks. |
| | `0006` | Addresses | Integration with UN Global Address standards. |
| **Birth of a Child** | `0378` | Request Status | Acts as a "Ticket" or "Workflow Header" infotype. |
| **Offboarding** | `0016` | Contract Details | Controls separation reasons and contract types. |
| | `0001` | Org Assignment | Used to determine the 'Approving Officer' for separation. |

---

## 2. Data Extraction Protocol (The "How")

### 2.1 The Decoupled Reader Pattern
UNESCO follows the **Decoupled HRPA Framework**. Data is rarely read via `SELECT * FROM PA0002`. Instead, it uses the **Feeder-to-XSS Adapter** path:

1.  **UI Request**: Fiori requests a certain "Version ID" (e.g., `02` for France, `99` for Int'l).
2.  **Mapping**: Table `T588UICONVCLAS` maps the Infotype/Version to a **Conversion Class** (e.g., `CL_HRPA_UI_CONVERT_0002_XX`).
3.  **Extraction**: The class uses `mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_all_data`.
4.  **Transformation**: The method `OUTPUT_CONVERSION` in the conversion class maps technical PA fields into the UI-friendly OData structure.

### 2.2 Custom Business Logic Injection (UNESCO BAdIs)
To avoid modifying standard SAP code, UNESCO injects NGO-specific rules using:
- **`HCMFAB_B_PERSINFO_CONFIG`**: Overrides field visibility (e.g., "Hide field X if staff is Regular Budget").
- **`HCMFAB_B_MYPERSONALDATA`**: Enriches data before it reaches the UI.

---

## 3. Custom Code Porting for UNESCO

### 3.2 The "Parking" Pattern (HCM-as-Finance-Posting)
Just like a Finance Posting Workflow (where a document is **Parked** in `VBKPF` before hitting the General Ledger), UNESCO HCM Fiori apps use a **Staging Pattern**:
- **Variation A: Standard ASR Staging** (e.g., Birth, Marriage): Data is held in the standard ASR buffer.
- **Variation B: Custom Table Staging** (e.g., Offboarding): Data is held in UNESCO custom tables like `zthrfiori_hreq`.
- **The Trigger**: The app calls `SAP_WAPI_START_WORKFLOW`. The data (whether in ASR or Custom Tables) acts like a **Parked Document**.
- **The "Posting" (Commit)**: The actual update to the employee's record (`HR_INFOTYPE_OPERATION`) only happens *after* the workflow is fully approved in the background.

### 3.3 Audit Trail and "Deep Recovery"
For auditors requiring an end-to-end view of a workflow:
- **Digital Ledger**: Every request is captured as an **XML Snapshot** in the ASR Data Container.
- **Recovery Method**: Using `ZCL_HRFIORI_PF_COMMON=>GET_REQUEST_FORM_DATA`, the system can reconstruct the exact state of the form at any step of the workflow, even if the data was never "Posted" to master tables.
- **Workflow Logs**: The system joins the **Process GUID** with the Workflow Log (`SWWIADESC`) to show who approved what and when.

### 3.4 PDF Attachments & Evidence
UNESCO requires evidence for sensitive actions (e.g., Birth Certificates):
- **Staging**: PDFs are uploaded via the OData Service and held in the **ASR Buffer** / Case Management container.
- **Verification**: Method `CHECK_ATTACHMENT` ensures the document is present before the workflow can be "Parked" or "Posted".
- **Audit Link**: The PDF is logically linked to the Finance-equivalent "Parked Document" via ArchiveLink.

### 3.5 Strategic ASR Monitoring & Custom RF Screens
Beyond simple tracking, the **ASR Process List** acts as a dynamic router for the UNESCO HR Portal. Monitoring these "Parked" items allows auditors and managers to ensure process integrity.

#### A. Universal Monitoring Logic (The "Smart Inbox")
The backend utility `FILTER_PROCESS_LIST` identifies the category of request (RF) and its state:
- **Campaign-Driven**: Special processes like `ZHR_DEP_REVIEW` (Dependent Review) are only "Postable" during windows defined in table `zthrfiori_dep_dl`.
- **Logic-Driven**: If an auditor or manager sees a `ZHR_CHANGE_CHILD` process, the UI can dynamically load a different "RF Screen" context than it would for a `ZHR_SPSE_UN` (Spouse) request.
- **Persistence Layers**:
    - `zthrfiori_hreq`: Monitors Offboarding request headers.
    - `zthrfiori_reqsta`: Tracks the granular 12-step progress/checklists.
    - `zthrfiori_dep_dl`: Manages deadlines for NGO-specific global campaigns.

#### B. Dynamic UI Routing in React (Special Screens)
When porting the monitoring dashboard, we leverage the **ProcessID** to swap UI layouts based on the "Request Type" (RF):

| Process ID (RF Type) | Special UI Requirement | Data Source for Auditor |
| :--- | :--- | :--- |
| `ZHR_CHANGE_CHILD` | Age Validation Banner (if > 18) | `ZCL_HRFIORI_BIRTH_OF_A_CHILD` |
| `ZHR_DEP_REVIEW` | Campaign Deadline Countdown | `zthrfiori_dep_dl` |
| `ZHROFFBOARD` | 12-Step Progress Stepper | `zthrfiori_reqsta` |

#### C. Custom Monitoring Dashboard Strategy
To build a high-performance monitoring screen for UNESCO:
1.  **Fetch the Process List**: Call the OData service to get all active processes for the logged-in user or auditor scope.
2.  **Contextual Rendering**: Map the `ProcessID` to a predefined set of React "Cards" that highlight the NGO-specific fields (e.g., Regional Group).
3.  **Deep-Dive Recovery**: If an auditor clicks a "Pending" item, use the `PROCESS_GUID` to call the **Recovery Engine** (`GET_REQUEST_FORM_DATA`) and display the "Parked" XML values without ever modifying the employee's standard profile.

> [!IMPORTANT]
> **React Porting Tip**: To keep UNESCO rules intact, do NOT write direct DB update logic in the new frontend. Instead, call the OData Actions of the `ZHR_PROCESS_AND_FORMS_SRV` service, which acts as the "Logical Gatekeeper" for all UNESCO HR actions.

---

## 4. NGO-Specific Field Discovery Protocol
If you encounter a field in Fiori that is not in the standard `PA` table definition:
1.  Search for the field name in **`DD03L`** with `TABNAME = 'HCMT_BSP_PA_XX_Rxxxx'`.
2.  Check the **Conversion Class** found in `T588UICONVCLAS`.
3.  Look for "UNESCO" comments in the code or `ZZ` field prefixes.
4.  If the field is calculated, it will be in the `OUTPUT_CONVERSION` method of the conversion class.
