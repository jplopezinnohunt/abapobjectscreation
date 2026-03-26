# CLAUDE.md - Instructions for AI Agents

## 🎯 Project Overview

This is an **enterprise SAP automation framework** for automating SAP GUI (Web and Native) transactions using Playwright, with support for direct RFC/BAPI calls when appropriate.

**Core Philosophy:** Generic primitives first, transaction-specific logic second.

## 🏗️ Architecture

### Framework Structure
```
lib/sap-webgui-core/        # Generic SAP WebGUI primitives (DO NOT HARDCODE)
lib/sap-transactions/       # Transaction-specific automation (uses core)
.agents/                    # AI agent behaviors, skills, workflows
Zagentexecution/           # Task execution artifacts
```

**CRITICAL RULE:** Core modules (`lib/sap-webgui-core/`) must NEVER contain transaction-specific logic. They provide generic primitives that work across ALL SAP transactions.

## 📚 Required Reading

Before making changes, read these files in order:

1. **[lib/README.md](lib/README.md)** - Framework documentation
2. **[.agents/rules/sapwebgui_framework_findings.md](.agents/rules/sapwebgui_framework_findings.md)** - 103 experiments consolidated
3. **[.agents/rules/multi_agent_architecture.md](.agents/rules/multi_agent_architecture.md)** - Multi-agent design
4. **[.agents/workflows/hybrid_orchestration.md](.agents/workflows/hybrid_orchestration.md)** - When to use WebGUI vs BAPI

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

## 📋 Task Execution Workflow

1. **User provides requirement** (e.g., "Create OData service")
2. **Evaluate approach:** `.agents/workflows/hybrid_orchestration.md`
3. **Use framework:** Compose transaction module from core primitives
4. **Execute and archive:** Save to `Zagentexecution/tasks/{date}_{task}/`
5. **Document learnings:** Update `.agents/rules/sapwebgui_framework_findings.md` if needed

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

## 📁 File Organization

```
Zagentexecution/tasks/YYYY_MM_DD_{task_name}/
├── task_details.md           # Requirements & context
├── automation_prompt.md      # Generated prompt for automation
├── learning_summary.md       # Findings from this task
├── {script}.js              # Execution scripts
└── {screenshot}.png         # Debug screenshots
```

All scripts must be archived in `Zagentexecution/tasks/` - never leave scripts in project root.

## 🔄 Multi-Agent Workflow

This project uses specialized agents (see `.agents/rules/multi_agent_architecture.md`):

1. **Orchestrator:** Plans and delegates
2. **SME Agents:** SAP domain experts (ABAP, Gateway, FI, etc.)
3. **Execution Workers:**
   - UI Automation (Playwright)
   - Backend (BAPI/RFC)
   - Native Fallback (SAP GUI Scripting)
   - CI/CD (abapGit)

**As an agent, identify your role and stay in scope.**

## 🎯 Success Metrics

When you complete a task, the result should have:
- ✅ Clean code using framework primitives
- ✅ < 20 lines per operation (not counting property data)
- ✅ No hardcoded DOM selectors (use framework locators)
- ✅ Transport handling included
- ✅ Error handling via status bar checks
- ✅ Screenshots for major steps
- ✅ Archived in `Zagentexecution/tasks/`

## 💾 Preserving Knowledge

After completing a task:
1. Update `learning_summary.md` in task folder
2. If you discovered new patterns, update `.agents/rules/sapwebgui_framework_findings.md`
3. If it's a common pattern, consider adding to core framework
4. Document in memory: `~/.claude/projects/{project}/memory/MEMORY.md`

## 🆘 When Stuck

1. Read `lib/README.md` - examples of all patterns
2. Check `Zagentexecution/tasks/2026_03_04_crp_service_layer/` - 103 experiments
3. Look at `learning_summary.md` files in past tasks
4. Check `.agents/skills/` for relevant skills
5. Ask user for clarification (don't guess)

## 🔐 Security

- Never commit credentials to Git
- Use `Zagentexecution/config/` for credentials (gitignored)
- SAP sessions use user's SSO - agent can only do what user is authorized for
- See `.agents/rules/security_guardrails.md`

## 📞 Getting Help

- **User Questions:** Use `AskUserQuestion` tool for clarifications
- **Complex Planning:** Use `EnterPlanMode` for multi-step implementations
- **Codebase Search:** Use `Task` tool with `Explore` agent
- **SAP Transactions:** Check `.agents/skills/` for transaction-specific guidance

---

**Remember:** This framework is the result of 103 experimental scripts. Respect the patterns that were proven to work. Don't reinvent the wheel - use the framework!

Last updated: 2026-03-04

---

## Ecosystem Standards

This project is governed by the **UNESCO SAP Ecosystem Coordinator**.
Classification: **Tier 1 — Skill Project** (builds reusable knowledge)
Publishes: `sap-intelligence`, `sap-gui-automation` skills

**Load before session start:**
- `C:\Users\jp_lopez\projects\ecosystem-coordinator\.knowledge\way-of-working\session-start.md`
- `C:\Users\jp_lopez\projects\ecosystem-coordinator\.knowledge\skills\sap-intelligence\SKILL.md`
- All topic files listed in this project's `memory/MEMORY.md`

**Session end:** Follow `session-end.md` from ecosystem coordinator.
**Propose new patterns to:** `ecosystem-coordinator/ecosystem/priority-actions.md`

## Memory Architecture

This project uses file-based memory with a strict architecture:
- `memory/MEMORY.md` — **Index only** (under 150 lines). Lines after 200 are silently truncated.
- `memory/topic_*.md` — Detail files read at every session start. No size limit.
- `memory/feedback_*.md` — Corrections and preferences.
- `memory/project_*.md` — Project state and decisions.

**Rule:** If you only read MEMORY.md, you are missing most of the project's memory.
Read ALL files it points to.
