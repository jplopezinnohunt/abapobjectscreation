# 09 — SEGW Browser Automation Prompt (Z_CRP_SRV)

<aside>
🤖

**Purpose:** Give this prompt to an agent with Playwright/browser control to create the full SEGW OData project in SAP WebGUI.

</aside>

---

## PROMPT START

You are automating the creation of an SAP OData V2 service project using transaction SEGW in SAP WebGUI (browser). The SAP system is ECC 6.0 EhP8. You will control the browser via Playwright to complete every step below.

### PRE-REQUISITES (verify before starting)

1. You must already be logged into SAP WebGUI in the browser
2. Transaction SEGW must be accessible to your user
3. Package ZCRP must exist (check with SE80 if unsure)
4. The following 6 tables must exist: ZCRP_CERT, ZCRP_BUDGETLN, ZCRP_ATTACH, ZCRP_APRVL_HIST, ZCRP_GRADE_CFG, ZCRP_GL_MAP

### IMPORTANT NOTES ABOUT SAP WEBGUI

- SAP WebGUI renders as HTML — use accessibility snapshots and DOM inspection
- Transaction codes are entered in the command field (top-left input, usually `/nSEGW` or `/oSEGW`)
- SAP uses a tree control on the left panel and a detail form on the right
- After every "save" or "generate" action, wait for the status bar message at the bottom
- SEGW uses a split view: left tree = model structure, right = property editor
- Fields are often input elements with SAP-specific IDs — use labels to identify them
- Right-click on tree nodes opens context menus for "Create" operations
- Take a snapshot after every major step to verify state before proceeding

---

## STEP 1: CREATE SEGW PROJECT

1. Navigate to transaction SEGW: type `/nSEGW` in the command field and press Enter
2. Click "Create Project" button (or menu: Project → Create)
3. Fill in the project details:
    - **Project:** `Z_CRP_SRV`
    - **Description:** `CRP Certificate - Cost Recovery to Project`
    - **Package:** `ZCRP`
    - **Project Type:** Service with SAP Annotations (default)
    - **Generation Strategy:** Standard
4. Press Enter or click the green checkmark to confirm
5. If prompted for a transport request, create a new one or select an existing one for package ZCRP
6. **Verify:** The project tree should appear on the left with nodes: Data Model, Service Implementation, Service Maintenance, Runtime Artifacts

---

## STEP 2: CREATE ENTITY TYPES

For each entity type below, right-click on "Entity Types" under "Data Model" in the left tree → "Create".

### Entity Type 1: CrpCertificate

1. Right-click "Entity Types" → Create
2. **Entity Type Name:** `CrpCertificate`
3. Confirm. The entity type node appears in the tree.
4. Expand "CrpCertificate" → click "Properties"
5. Add each property by clicking the "Create" (append row) button in the properties table:

| **Property Name** | **EdmType** | **Key** | **Nullable** | **MaxLength** | **Label** |
| --- | --- | --- | --- | --- | --- |
| CompanyCode | Edm.String | ✓ Yes | No | 4 | Company Code |
| FiscalYear | Edm.String | ✓ Yes | No | 4 | Fiscal Year |
| CertificateId | Edm.String | ✓ Yes | No | 20 | Certificate ID |
| DocumentDate | Edm.DateTime | No | Yes | — | Document Date |
| PostingDate | Edm.DateTime | No | Yes | — | Posting Date |
| HeaderText | Edm.String | No | Yes | 25 | Header Text |
| ReferenceDoc | Edm.String | No | Yes | 16 | Reference |
| Status | Edm.String | No | Yes | 2 | Status |
| PostingPeriod | Edm.String | No | Yes | 2 | Period |
| StaffId | Edm.String | No | Yes | 8 | Staff ID |
| StaffName | Edm.String | No | Yes | 80 | Staff Name |
| Grade | Edm.String | No | Yes | 4 | Grade |
| PostTitle | Edm.String | No | Yes | 40 | Post Title |
| BusinessArea | Edm.String | No | Yes | 4 | Business Area |
| FieldOffice | Edm.String | No | Yes | 40 | Field Office |
| NumberOfWorkingDays | Edm.Int32 | No | Yes | — | Working Days |
| StartDate | Edm.DateTime | No | Yes | — | Start Date |
| EndDate | Edm.DateTime | No | Yes | — | End Date |
| CalculatedAmount | Edm.Decimal | No | Yes | Precision:13, Scale:2 | Amount |
| Currency | Edm.String | No | Yes | 5 | Currency |
| GLAccount | Edm.String | No | Yes | 10 | GL Account |
| DescriptionOfTasks | Edm.String | No | Yes | 0 (unlimited) | Description |
| JVDocNumber | Edm.String | No | Yes | 10 | JV Document # |
| JVFiscalYear | Edm.String | No | Yes | 4 | JV Fiscal Year |
| JVPostedAt | Edm.DateTime | No | Yes | — | JV Posted At |
| CreatorAuthType | Edm.String | No | Yes | 10 | Auth Type |
| CreatedBy | Edm.String | No | Yes | 12 | Created By |
| CreatedAt | Edm.DateTime | No | Yes | — | Created At |
| ChangedBy | Edm.String | No | Yes | 12 | Changed By |
| ChangedAt | Edm.DateTime | No | Yes | — | Changed At |

<aside>
⚠️

**IMPORTANT:** For each key property (yellow rows), make sure the "Is Key" checkbox is checked. For non-key properties, make sure "Nullable" is checked.

</aside>

1. Save (Ctrl+S)

### Entity Type 2: CrpBudgetLine

1. Right-click "Entity Types" → Create
2. **Entity Type Name:** `CrpBudgetLine`
3. Expand → Properties. Add:

| **Property Name** | **EdmType** | **Key** | **Nullable** | **MaxLength** | **Label** |
| --- | --- | --- | --- | --- | --- |
| CompanyCode | Edm.String | ✓ Yes | No | 4 | Company Code |
| FiscalYear | Edm.String | ✓ Yes | No | 4 | Fiscal Year |
| CertificateId | Edm.String | ✓ Yes | No | 20 | Certificate ID |
| LineId | Edm.String | ✓ Yes | No | 3 | Line Item |
| Fund | Edm.String | No | Yes | 10 | Fund |
| FundsCenter | Edm.String | No | Yes | 16 | Funds Center |
| CommitmentItem | Edm.String | No | Yes | 24 | Commitment Item |
| BusinessArea | Edm.String | No | Yes | 4 | Business Area |
| WBSElement | Edm.String | No | Yes | 24 | WBS Element |
| CRPCode | Edm.String | No | Yes | 20 | CRP Code |
| Amount | Edm.Decimal | No | Yes | Precision:13, Scale:2 | Amount |
| Currency | Edm.String | No | Yes | 5 | Currency |
| BudgetAvailable | Edm.String | No | Yes | 1 | Budget Available |
1. Save

### Entity Type 3: CrpAttachment

1. Right-click "Entity Types" → Create
2. **Entity Type Name:** `CrpAttachment`
3. Check **"Media"** checkbox (this entity has binary stream content)
4. Expand → Properties. Add:

| **Property Name** | **EdmType** | **Key** | **Nullable** | **MaxLength** | **Label** |
| --- | --- | --- | --- | --- | --- |
| CertificateId | Edm.String | ✓ Yes | No | 20 | Certificate ID |
| AttachmentId | Edm.String | ✓ Yes | No | 3 | Attachment ID |
| FileName | Edm.String | No | Yes | 128 | File Name |
| MimeType | Edm.String | No | Yes | 128 | MIME Type |
| FileSize | Edm.Int32 | No | Yes | — | File Size |
| Category | Edm.String | No | Yes | 20 | Category |
| UploadedBy | Edm.String | No | Yes | 12 | Uploaded By |
| UploadedAt | Edm.DateTime | No | Yes | — | Uploaded At |

<aside>
📝

**NOTE:** Do NOT add a Content/Binary property — SEGW handles media content via the Edm.Stream convention automatically when Media is checked.

</aside>

1. Save

### Entity Type 4: CrpApprovalHistory

1. Right-click "Entity Types" → Create
2. **Entity Type Name:** `CrpApprovalHistory`
3. Expand → Properties. Add:

| **Property Name** | **EdmType** | **Key** | **Nullable** | **MaxLength** | **Label** |
| --- | --- | --- | --- | --- | --- |
| HistoryId | Edm.String | ✓ Yes | No | 10 | History ID |
| CertificateId | Edm.String | No | Yes | 20 | Certificate ID |
| StepName | Edm.String | No | Yes | 40 | Step Name |
| ActorId | Edm.String | No | Yes | 8 | Actor ID |
| ActorName | Edm.String | No | Yes | 80 | Actor Name |
| Decision | Edm.String | No | Yes | 10 | Decision |
| Comment | Edm.String | No | Yes | 0 | Comment |
| DecisionAt | Edm.DateTime | No | Yes | — | Decision At |
1. Save

### Entity Type 5: CostRate

1. Right-click "Entity Types" → Create
2. **Entity Type Name:** `CostRate`
3. Expand → Properties. Add:

| **Property Name** | **EdmType** | **Key** | **Nullable** | **MaxLength** | **Label** |
| --- | --- | --- | --- | --- | --- |
| Grade | Edm.String | ✓ Yes | No | 4 | Grade |
| DutyStation | Edm.String | ✓ Yes | No | 40 | Duty Station |
| Biennium | Edm.String | ✓ Yes | No | 10 | Biennium |
| DailyRate | Edm.Decimal | No | Yes | Precision:13, Scale:2 | Daily Rate |
| Currency | Edm.String | No | Yes | 5 | Currency |
1. Save

---

## STEP 3: CREATE ENTITY SETS

For each entity type, create a corresponding Entity Set. Right-click "Entity Sets" under "Data Model" → Create.

| **Entity Set Name** | **Entity Type** | **Addressable** | **Creatable** | **Updatable** | **Deletable** |
| --- | --- | --- | --- | --- | --- |
| CrpCertificateSet | CrpCertificate | ✓ | ✓ | ✓ | ✗ |
| CrpBudgetLineSet | CrpBudgetLine | ✓ | ✓ | ✓ | ✓ |
| CrpAttachmentSet | CrpAttachment | ✓ | ✓ | ✗ | ✓ |
| CrpApprovalHistorySet | CrpApprovalHistory | ✓ | ✗ | ✗ | ✗ |
| CostRateSet | CostRate | ✓ | ✗ | ✗ | ✗ |

For CrpApprovalHistorySet and CostRateSet (gray rows): uncheck Creatable, Updatable, and Deletable (read-only entities).

Save after each.

---

## STEP 4: CREATE ASSOCIATIONS & NAVIGATION PROPERTIES

Right-click "Associations" under "Data Model" → Create.

### Association 1: CrpCert_To_BudgetLines

- **Name:** `CrpCert_To_BudgetLines`
- **Principal Entity Type:** `CrpCertificate`
- **Principal Cardinality:** `1`
- **Dependent Entity Type:** `CrpBudgetLine`
- **Dependent Cardinality:** `M` (many)
- **Referential Constraint (FK mapping):**
    - CrpCertificate.CompanyCode → CrpBudgetLine.CompanyCode
    - CrpCertificate.FiscalYear → CrpBudgetLine.FiscalYear
    - CrpCertificate.CertificateId → CrpBudgetLine.CertificateId
- **Navigation Property on CrpCertificate:** `ToBudgetLines`

### Association 2: CrpCert_To_Attachments

- **Name:** `CrpCert_To_Attachments`
- **Principal Entity Type:** `CrpCertificate`
- **Principal Cardinality:** `1`
- **Dependent Entity Type:** `CrpAttachment`
- **Dependent Cardinality:** `M`
- **Referential Constraint:**
    - CrpCertificate.CertificateId → CrpAttachment.CertificateId
- **Navigation Property on CrpCertificate:** `ToAttachments`

### Association 3: CrpCert_To_ApprovalHistory

- **Name:** `CrpCert_To_ApprovalHistory`
- **Principal Entity Type:** `CrpCertificate`
- **Principal Cardinality:** `1`
- **Dependent Entity Type:** `CrpApprovalHistory`
- **Dependent Cardinality:** `M`
- **Referential Constraint:**
    - CrpCertificate.CertificateId → CrpApprovalHistory.CertificateId
- **Navigation Property on CrpCertificate:** `ToApprovalHistory`

After creating each association, also create the corresponding **Association Set** (SEGW may auto-create these — verify under "Association Sets" node).

Save after all associations are created.

---

## STEP 5: CREATE FUNCTION IMPORTS

<aside>
📝

**Create the Complex Types FIRST** (under "Complex Types" node), then create the Function Imports that reference them.

</aside>

### Complex Types

Right-click "Complex Types" under "Data Model" → Create.

**JVSimulationResult:**

| **Property** | **EdmType** | **Label** |
| --- | --- | --- |
| Success | Edm.Boolean | Success |
| DocumentNumber | Edm.String (10) | Document Number |
| Messages | Edm.String (0) | Messages |

**JVPostingResult:**

| **Property** | **EdmType** | **Label** |
| --- | --- | --- |
| Success | Edm.Boolean | Success |
| DocumentNumber | Edm.String (10) | Document Number |
| FiscalYear | Edm.String (4) | Fiscal Year |
| Messages | Edm.String (0) | Messages |

**AllotmentResult:**

| **Property** | **EdmType** | **Label** |
| --- | --- | --- |
| Success | Edm.Boolean | Success |
| AllotmentId | Edm.String (20) | Allotment ID |
| Messages | Edm.String (0) | Messages |

### Function Imports

Right-click "Function Imports" under "Data Model" → Create.

**SubmitForApproval:**

- **Name:** `SubmitForApproval`
- **HTTP Method:** `POST`
- **Return Type Entity Set:** `CrpCertificateSet`
- **Return Cardinality:** `1`
- **Parameter:** CertificateId (Edm.String, Mode: In, Nullable: No)

**SimulateJVPosting:**

- **Name:** `SimulateJVPosting`
- **HTTP Method:** `POST`
- **Return Type:** `JVSimulationResult` (complex type)
- **Return Cardinality:** `1`
- **Parameter:** CertificateId (Edm.String, Mode: In, Nullable: No)

**PostJV:**

- **Name:** `PostJV`
- **HTTP Method:** `POST`
- **Return Type:** `JVPostingResult` (complex type)
- **Return Cardinality:** `1`
- **Parameters:**
    - CertificateId (Edm.String, Mode: In, Nullable: No)
    - PostingDate (Edm.DateTime, Mode: In, Nullable: No)

**PostAllotment:**

- **Name:** `PostAllotment`
- **HTTP Method:** `POST`
- **Return Type:** `AllotmentResult` (complex type)
- **Return Cardinality:** `1`
- **Parameter:** CertificateId (Edm.String, Mode: In, Nullable: No)

Save after all function imports.

---

## STEP 6: GENERATE RUNTIME OBJECTS

1. Click the **"Generate Runtime Objects"** button in the toolbar (gear/cog icon, or menu: Edit → Generate Runtime Objects)
2. A dialog appears showing the classes that will be generated:
    - **Model Provider Class (MPC):** `ZCL_Z_CRP_SRV_MPC`
    - **Model Provider Extension (MPC_EXT):** `ZCL_Z_CRP_SRV_MPC_EXT`
    - **Data Provider Class (DPC):** `ZCL_Z_CRP_SRV_DPC`
    - **Data Provider Extension (DPC_EXT):** `ZCL_Z_CRP_SRV_DPC_EXT`
3. Confirm the generation
4. If prompted for a transport request, select the same one from Step 1
5. **Wait** for the green "Model and service implementation generated" status bar message
6. **Verify:** Expand "Runtime Artifacts" in the tree — you should see all 4 classes listed

---

## STEP 7: REGISTER THE SERVICE

1. Navigate to transaction `/n/IWFND/MAINT_SERVICE`
2. Click "Add Service" button
3. In the search:
    - **System Alias:** `LOCAL` (or the appropriate alias)
    - **Technical Service Name:** search for `Z_CRP_SRV`
4. Select `Z_CRP_SRV` from the results
5. Click "Add Selected Services"
6. Fill in:
    - **Package:** `ZCRP`
    - Transport request if prompted
7. Confirm
8. **Verify:** The service should appear in the catalog. Test it:
    - Click on the service → "Call Browser" or "ICF Nodes" → "Test"
    - The $metadata URL should return XML with all 5 entity types and 4 function imports

---

## VERIFICATION CHECKLIST

After all steps, verify the following in the `$metadata` XML:

- [ ]  5 EntityType elements: CrpCertificate, CrpBudgetLine, CrpAttachment, CrpApprovalHistory, CostRate
- [ ]  5 EntitySet elements with correct names
- [ ]  3 Association elements with correct FK mappings
- [ ]  3 NavigationProperty on CrpCertificate: ToBudgetLines, ToAttachments, ToApprovalHistory
- [ ]  4 FunctionImport elements: SubmitForApproval, SimulateJVPosting, PostJV, PostAllotment
- [ ]  3 ComplexType elements: JVSimulationResult, JVPostingResult, AllotmentResult
- [ ]  CrpAttachment has `m:HasStream="true"` (media entity)
- [ ]  Key properties are marked as Key in the metadata
- [ ]  Service is reachable at: `/sap/opu/odata/sap/Z_CRP_SRV/$metadata`

---

## ERROR RECOVERY

- **"Object already exists"**: If the project partially exists, open it instead of creating. Delete incomplete entity types and recreate.
- **Transport prompt**: Always select or create a transport in package ZCRP.
- **Generation fails**: Check that all entity types have at least one key property. Check that all associations reference valid property names (case-sensitive).
- **Timeout in WebGUI**: SAP WebGUI sessions expire. If the page becomes unresponsive, navigate to the WebGUI base URL and re-enter `/nSEGW`, then reopen project Z_CRP_SRV.
- **Status bar shows errors (red)**: Take a screenshot, read the error message, and diagnose. Common issues: duplicate names, missing key properties, invalid EdmType.
