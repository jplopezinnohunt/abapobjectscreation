---
name: Web SAP GUI Automation
description: Best practices and guidelines for automating SAP GUI for HTML
domains:
  functional: [*]
  module: [*]
  process: []
---

# Web SAP GUI Automation

## Overview
SAP GUI for HTML (Web SAP GUI) maps SAP screen elements to HTML dynamically. This means standard web automation techniques might be fragile and require special care.

## ⛔ CRITICAL: NEVER USE `browser_subagent` FOR SAP TASKS ⛔
**This is a hard, non-negotiable rule. Violating it is the #1 failure mode.**

- **NEVER** call the `browser_subagent` tool for any SAP interaction.
- `browser_subagent` opens a **fresh, unauthenticated browser** at `localhost` — it has **no SAP session**, **no client certificate**, and cannot reach `hq-sap-d01.hq.int.unesco.org`.
- **ALWAYS** interact with SAP by writing a Node.js script and running it via `run_command`:
  ```
  node <script>.js
  ```
- **ALL** Playwright scripts MUST connect to the existing, pre-authenticated Chrome test browser via CDP:
  ```javascript
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  ```
- The correct SAP URL is: `https://hq-sap-d01.hq.int.unesco.org/sap/bc/gui/sap/its/webgui?sap-client=350`
- **NEVER** navigate to `localhost` or open any URL other than the correct SAP server above.
- The Chrome test browser is launched separately via `00_launch_browser.js` with `--remote-debugging-port=9222` and a persistent profile in `playwright_data/`. This is the ONLY browser that should be used.

## Core Process Rules
### 1. Pre-Development Interview
Before starting any significant Web SAP GUI task, you MUST execute the interview checklist defined in `.agents/workflows/segw_interview.md`.

### 2. Hybrid Orchestration Evaluation
Evaluate the task using `.agents/workflows/hybrid_orchestration.md`. If the task involves massive pure data manipulation, consider if a BAPI approach is better than Web GUI automation.

## Best Practices
1. **Playwright-SAP Locators**: Standard Playwright selectors fail easily in SAP. ALWAYS use the `playwright-sap` module and its native locators (like `getByRoleUI5`, `locateSID`) whenever possible.
2. **Iframes**: Web SAP GUI relies heavily on iframes. Always ensure your Playwright script has switched contexts to the correct iframe before interacting.
3. **Execution Wait States**: Leverage `playwright-sap`'s built-in wait logic to handle SAP's complex UI rendering cycles rather than hardcoded sleeps.
4. **Tool-Assisted Debugging**: When writing scripts, use these browser extensions:
   *   **SAP UI5 Inspector**: To inspect the true UI5 control hierarchy and data bindings.
   *   **SelectorsHub**: For older, non-UI5 classic web GUI screens to generate precise XPath/CSS.

## Playwright Script Generation & Execution
Do not guess complex DOM paths. Use specialized tools to generate the UI code:
1. **Playwright-SAP Smarter Codegen**: ALWAYS use the augmented `playwright-sap` recorder instead of writing raw clicks by hand when capturing long workflows. It will generate stable `getByRoleUI5` calls.
2. **Context Selection**: Start scripts by identifying and focusing on the main content iframe.
3. **Locator Hierarchy**: 
   *   Primary: `playwright-sap` extensions (`locateSID`, `getByRoleUI5`).
   *   Secondary: Stable Text definitions.
   *   Last Resort: CSS/XPath (verified via SelectorsHub).

---

## Método trasladado desde CLAUDE.md (s107)

> Estas secciones vivían en `CLAUDE.md` y se cargaban en CADA sesión, se usaran o no.
> La doctrina de Claude Code manda el conocimiento de dominio a un skill, que carga
> bajo demanda. Contenido íntegro, sin recortar.

## 🎓 Key Learnings (DO NOT IGNORE)

### 1. The Select-Then-Toolbar Pattern
```javascript
// ✅ CORRECT - Most reliable (proven in 103 experiments)
await tree.selectNode(['Entity Types']);
await toolbar.clickCreate();

// ❌ WRONG - Right-click menus are unreliable
await tree.rightClick(['Entity Types']);
await menu.selectMenuItem('Create');
```

### 2. Text Locators Are More Stable Than IDs
```javascript
// ✅ CORRECT
frame.locator('span, td').filter({ hasText: /^Entity Types$/ })

// ❌ WRONG - IDs change between sessions
frame.locator('#tree#C111#3#ni')
```

### 3. Keyboard Navigation > Mouse for Trees
```javascript
// ✅ CORRECT
await node.click();                      // Focus
await page.keyboard.press('ArrowRight'); // Expand

// ⚠️ Less reliable
await expandIcon.click();
```

### 4. Always Handle Transport Requests
Transport popups appear asynchronously after saves/creates. ALWAYS check:
```javascript
await session.save();
await session.handleTransportRequest(); // Don't skip this!
```

### 5. BAPIs vs WebGUI Decision Tree
- **Use WebGUI:** Visual builders (SEGW, SWDD), screen configuration
- **Use BAPI/RFC:** Mass data operations, standard business objects
- **Use Hybrid:** Complex workflows (UI for setup, BAPI for data)

See: `.agents/workflows/hybrid_orchestration.md`

## 🚀 Adding a New Transaction

Example: Automating SE11 (Data Dictionary)

### Step 1: Create Transaction Module
```javascript
// lib/sap-transactions/Se11Automation.js
const { SapTree, SapToolbar, SapPopup, SapSession } = require('../sap-webgui-core');

class Se11Automation {
    constructor(connection) {
        this.tree = new SapTree(connection.frame, connection.page);
        this.toolbar = new SapToolbar(connection.frame, connection.page, 'C110'); // SE11 prefix
        this.popup = new SapPopup(connection.frame, connection.page);
        this.session = new SapSession(connection.frame, connection.page);
    }

    async createTable(tableName, fields) {
        // Use generic primitives - NO custom tree navigation!
        await this.session.ensureChangeMode();
        await this.tree.selectNode(['Dictionary Objects', 'Database Tables']);
        await this.toolbar.clickCreate();
        await this.popup.fillFirst(tableName);
        await this.popup.confirm();

        // Add fields using keyboard navigation
        for (const field of fields) {
            await this._addField(field);
        }

        await this.session.save();
    }
}
```

### Step 2: Document Toolbar Prefixes
If the transaction uses a different toolbar prefix, document it in the transaction class.

### Step 3: Write Test
```javascript
// test_se11.js
const { SapConnection } = require('./lib/sap-webgui-core');
const Se11Automation = require('./lib/sap-transactions/Se11Automation');

const conn = await SapConnection.connect();
const se11 = new Se11Automation(conn);
await se11.createTable('ZTESTTABLE', fields);
```

## 🔧 Modifying Core Modules

**⚠️ RARELY NEEDED - Core modules are stable.**

Only modify core modules if:
1. SAP changes its HTML structure (`.urPW` class, tree patterns, etc.)
2. Chrome CDP API changes
3. Adding a truly generic primitive (e.g., table handling)

**Never modify core for transaction-specific needs!**

## 🛠️ Debugging Failed Automation

When a script fails:

1. **Check Status Bar:** `await session.getStatusBarMessage()`
2. **Take Screenshot:** `await conn.screenshot('debug')`
3. **List Toolbar Buttons:** `await toolbar.listButtons()` (shows all available buttons)
4. **Verify Tree State:** `await tree.getActiveNode()`
5. **Check for Popup:** `await popup.isVisible()`

Don't guess - use the framework's debugging methods.

## 🚫 Anti-Patterns (DON'T DO THIS)

### ❌ Hardcoding Tree Navigation
```javascript
// WRONG - Transaction-specific in core module
class SapTree {
    async navigateToSegwEntity() { // NO! Too specific!
        await this.selectNode(['Z_CRP_SRV', 'Data Model', 'Entity Types']);
    }
}
```

### ❌ Skipping Framework and Writing Raw Playwright
```javascript
// WRONG - Bypassing framework
const entityTypes = page.locator('#tree#C111#3#ni');
await entityTypes.click({ button: 'right' });
// Use tree.selectNode() instead!
```

### ❌ Using browser_subagent for SAP
```javascript
// WRONG - browser_subagent has no SAP session
await browser_subagent.execute('click button');
// Use SapConnection.connect() instead!
```

### ❌ Mixing Generic and Specific Logic
```javascript
// WRONG - SEGW logic in core toolbar class
class SapToolbar {
    async createSegwEntity(name) { // NO! Too specific!
        await this.clickButton(0);
        // This belongs in SegwAutomation class
    }
}
```

## 🎯 Success Metrics

When you complete a task, the result should have:
- ✅ Clean code using framework primitives
- ✅ < 20 lines per operation (not counting property data)
- ✅ No hardcoded DOM selectors (use framework locators)
- ✅ Transport handling included
- ✅ Error handling via status bar checks
- ✅ Screenshots for major steps
- ✅ Archived in `Zagentexecution/tasks/`

