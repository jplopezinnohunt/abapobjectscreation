---
name: ABAP SEGW OData Services
description: >
  Complete skill for creating and automating SAP Gateway OData services via SEGW.
  Covers: interview protocol, Playwright automation patterns, element IDs, entity/property/association
  creation, service registration, transport handling. Consolidated from sap_segw + segw_automation.
domains:
  functional: [*]
  module: [*]
  process: []
---

# ABAP SEGW — OData Service Construction

## NEVER Do This

> [!CAUTION]
> - **NEVER use right-click context menus** — use Select-Then-Toolbar pattern (proven in 103 experiments)
> - **NEVER use hardcoded tree node IDs** (e.g., `#tree#C111#3#ni`) — IDs change between sessions. Use text locators.
> - **NEVER skip transport request handling** — popups appear asynchronously after save/create. Always call `session.handleTransportRequest()`.
> - **NEVER use `browser_subagent`** — no SAP session. Use `lib/sap-webgui-core/` framework via `SegwAutomation.js`.

---

## Pre-Development Protocol

Before ANY SEGW task:
1. Execute interview checklist in `.agents/workflows/segw_interview.md`
2. Gather: SAP URL, auth method, project name, dev package, transport request
3. Evaluate Web GUI vs BAPI via `.agents/workflows/hybrid_orchestration.md`
   - **SEGW creation** = always Route A (Web GUI) — no BAPI equivalent for visual builder

---

## Core Process (5 Steps)

1. **SEGW** — Launch Gateway Service Builder
2. **Create/Open Project** — Assign to package (`$TMP` for local, custom for transport)
3. **Data Model** — Import DDIC structures or define entities/properties manually
4. **Generate Runtime** — Click "Generate Runtime Objects" → creates DPC + MPC classes
5. **Register Service** — `/IWFND/MAINT_SERVICE` → Add Service → System Alias LOCAL

---

## Playwright Automation Patterns

### Connection & Frame
```javascript
const browser = await chromium.connectOverCDP('http://localhost:9222');
const frame = page.frameLocator('iframe[name^="itsframe1_"]').first();
```

### Select-Then-Toolbar (PROVEN PATTERN — use always)
```javascript
// ✅ CORRECT
await tree.selectNode(['Entity Types']);
await toolbar.clickCreate();     // Button activates after selection

// ❌ WRONG — right-click menus are unreliable
await entityTypesNode.click({ button: 'right' });
```

### Text Locators Over IDs
```javascript
// ✅ CORRECT — stable across sessions
frame.locator('span, td').filter({ hasText: /^Entity Types$/ })

// ❌ WRONG — IDs change
frame.locator('#tree#C111#3#ni')
```

---

## Key Element IDs (SEGW — C109/C111 prefix)

**Main Toolbar (C109)**:
| ID | Action |
|----|--------|
| `C109_btn0` | Create (context-sensitive) |
| `C109_btn3` | Display/Change toggle |
| `C109_btn5` | Check Consistency |
| `C109_btn6` | Generate Runtime Objects |
| `id~="btn[11]"` | Generate (alternative locator) |

**Project Tree (C111) — use text locators, not these IDs**:
| Node | Text Locator (preferred) |
|------|--------------------------|
| Entity Types | `span, td` filter `hasText: /^Entity Types$/` |
| Associations | `span, td` filter `hasText: /^Associations$/` |
| Entity Sets | `span, td` filter `hasText: /^Entity Sets$/` |

**Status Bar**: `#stbar-msg-txt` or `.urStatusbar`
**Popup inputs**: `.urPW input` (focus explicitly before typing)

---

## Workflow: Project Management

### Open Existing Project
1. Click "Open Project" (folder icon)
2. Type project name in popup
3. Press Enter → verify "Data Model" appears in tree

### Create New Project
1. Click "Create Project" (paper icon)
2. Fill: Project name, Description, Attributes
3. Confirm → Handle Package Selection popup
   - Enter `$TMP` + click "Local Object" (dev only)
   - Enter transport package for proper dev objects

---

## Workflow: Entity Creation

### 1. Create Entity Type
```javascript
await tree.selectNode(['Project', 'Data Model', 'Entity Types']);
await toolbar.clickCreate();
// Fill popup: Entity Name
// Uncheck "Create Related Entity Set" unless needed
await popup.confirm();
await session.handleTransportRequest();
```

### 2. Define Properties
- Select entity → click "Properties" tab
- Click "Append Row" / "Insert Row" icon (sub-toolbar)
- Tab navigation preferred over direct ID clicks (grid IDs change with row inserts)
- **Key fields**: check "Key" checkbox explicitly
- **Non-key fields**: check "Nullable" checkbox

### 3. Media Entities (e.g., CrpAttachment)
- When creating: check **"Media"** checkbox in creation popup
- Do NOT add binary content property — Edm.Stream is handled by SEGW automatically

### 4. Associations
- Select Associations node → toolbar Create
- Principal Entity: 1-side (e.g., CrpCertificate)
- Dependent Entity: M-side (e.g., CrpBudgetLine)
- Set Referential Constraint: map header key → item foreign key

### 5. Generate Runtime Objects
```javascript
await toolbar.clickButton('Generate');  // or C109_btn6
// Wait for: "Model and service implementation generated" in status bar
await expect(page.locator('#stbar-msg-txt'))
    .toContainText('generated', { timeout: 30000 });
```

---

## Workflow: Service Registration

**Transaction**: `/n/IWFND/MAINT_SERVICE`
1. Click "Add Service"
2. System Alias: `LOCAL`
3. Search for your project (e.g., `Z_CRP_SRV`)
4. Select → click "Add Selected Services"
5. Confirm transport

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Context menu doesn't open | JavaScript timing | Use `ArrowDown` + `Enter` instead of right-click |
| Grid ID targeting fails | Row indices shift on insert | Use relative position or tab navigation |
| Status bar empty after action | SAP async processing | `await page.waitForSelector('#stbar-msg-txt:not(:empty)')` |
| Transport popup missed | Async appearance | `await session.handleTransportRequest()` after every save |
| Tree node not found | ID changed | Switch to text locator: `filter({ hasText: /^NodeName$/ })` |

---

## Integration Points

- `lib/sap-webgui-core/` — Framework: `SapTree`, `SapToolbar`, `SapPopup`, `SapSession`
- `lib/sap-transactions/SegwAutomation.js` — SEGW-specific transaction class
- `.agents/workflows/segw_interview.md` — Pre-task interview protocol
- `.agents/workflows/hybrid_orchestration.md` — When to use GUI vs BAPI
- `Zagentexecution/tasks/2026_03_04_crp_service_layer/` — 103 experiments, full learning archive

---

## You Know It Worked When

1. Project opens with Data Model tree visible
2. Entity type created with properties (Key + Nullable correctly set)
3. Generate → status bar shows "generated"
4. Service appears in `/IWFND/MAINT_SERVICE`
5. `$metadata` endpoint returns your entity types
