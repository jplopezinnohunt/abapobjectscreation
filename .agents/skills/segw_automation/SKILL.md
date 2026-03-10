# SEGW OData Service Construction Skill

This skill provides a standardized workflow for automating the SAP Gateway Service Builder (SEGW) using Playwright.

## Core Concepts

- **Transaction**: `SEGW`
- **Navigation**: Always use the command field `/nSEGW` to ensure a clean start.
- **Tree Interaction**: SEGW relies on a left-hand tree. Nodes like "Data Model" and "Entity Types" must be expanded via double-click or keyboard navigation.
- **Popups**: SAP WebGUI popups are often `div` elements with class `.urPW`. Input fields inside popups should be focused explicitly before typing.

## Key Element IDs (SEGW)
- **Main Toolbar (C109)**:
    - `C109_btn0`: Create (Context-sensitive).
    - `C109_btn3`: Display/Change toggle.
    - `C109_btn6`: Generate Runtime Objects.
    - `C109_btn5`: Check Consistency.
- **Project Tree (C111)**:
    - `Entity Types`: `tree#C111#3#ni`
    - `Associations`: `tree#C111#4#ni`
    - `Entity Sets`: `tree#C111#5#ni`

## Automated Workflow: Project Management

### 1. Check/Open Project
- **Goal**: Determine if project `[PROJECT_ID]` exists and open it.
- **Steps**:
    1. Click the "Open Project" (Folder icon, title "Open Project").
    2. Type project name in the popup.
    3. Press Enter.
    4. Verify success by looking for "Data Model" in the tree.

### 2. Create Project (if not exists)
- **Goal**: Create `[PROJECT_ID]` if opening fails.
- **Steps**:
    1. Click "Create Project" (Paper icon).
    2. Fill: Project, Description, Attributes.
    3. Confirm (Enter).
    4. Handle the Package Selection popup (e.g., enter `$TMP` and click "Local Object").

## Automated Workflow: Entity Creation

### 1. Create Entity Type
- **Steps**:
    1. Right-click the "Entity Types" node in the tree.
    2. Select the "Create" menu item.
    3. Enter Entity Name in the popup.
    4. Uncheck "Create Related Entity Set" (unless required).
    5. Confirm.

### 2.2 Define Entity Properties
After creating the entity type, expand it and click **Properties**.
**Pattern:**
- Click **"Append Row"** or **"Insert Row"** icon in the properties table (id pattern usually includes `tbl` or `btn[5]` in the sub-toolbar).
- **Batch Entry:** Enter properties in batches. Tab navigation is preferred over direct ID clicks for efficiency.
- **Key Checkbox:** Key properties must be explicitly checked.
- **Nullable:** Non-key properties must have Nullable checked.

### 2.3 Handle Media Entities (CrpAttachment)
- When creating `CrpAttachment`, check the **"Media"** checkbox in the initial popup.
- Do NOT add a binary content property (Edm.Stream is handled by SEGW).

### 2.4 Service Creation & Maintenance
- **Transaction:** `/n/IWFND/MAINT_SERVICE`
- **Pattern:**
    - Click **"Add Service"**.
    - System Alias: `LOCAL`.
    - Search for project `Z_CRP_SRV`.
    - Select and click **"Add Selected Services"**.

### 2.5 Runtime Objects Generation
- Click **"Generate"** (Cog icon, `id~="btn[11]"`).
- Wait for status bar message: `"Model and service implementation generated"`.

### 2.6 Association Mapping
- Right-click **"Associations"** -> Create.
- Principal Entity: `CrpCertificate` (1).
- Dependent Entity: `CrpBudgetLine` (M).
- **Referential Constraint:** Maps headers to items (e.g., CertificateId).

---

## 4. Troubleshooting Dynamic Elements
- **Context Menus:** Use `ArrowDown` + `Enter` if right-click menus are not directly targetable.
- **Grid IDs:** In SAP WebGUI, grid cells have IDs like `M1:46:::1:0` (Row:Col). ROW indices change as you insert rows.
- **Status Bar:** Always verify the status bar text (ID `stbar-msg-txt`) before moving to the next script.

---
## Best Practices for Automation

- **Wait for Status Bar**: After every major action, wait for the status bar (`.urStatusbar`) to update or clear.
- **CDP Connection**: Always use `chromium.connectOverCDP('http://localhost:9222')` to interact with the user's active logged-in session.
- **Frame Targeting**: Targeted elements are usually inside an `iframe` with a name starting with `itsframe1_`.
