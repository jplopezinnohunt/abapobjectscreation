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

## 🧠 MANDATORY FIRST ACTION — Load Brain State

**EVERY session, before ANY other action, read this ONE file:**

```
brain_v2/brain_state.json
```

This single file contains (Session #050 — 12 layers):
- **Layer 1**: 136 analyzed objects with inline edges, annotations, claims, incidents
- **Layer 2**: Cross-cutting indexes (by_incident — now enriched with status/doc/root_cause/fix, by_domain, uncertain_claims, superseded_claims)
- **Layer 3**: 58 feedback rules (agent behavioral DNA)
- **Layer 4**: 26 claims with evidence tier
- **Layer 6**: 23 known_unknowns
- **Layer 7**: 6 falsification predictions pending test
- **Layer 8**: 15 superseded claims (anti-regression)
- **Layer 9**: User questions (parked + answered)
- **Layer 10**: Data quality issues (8 open)
- **Layer 11**: First-class **incidents** (full root cause + fix path + analysis_doc inline) — added Session #050
- **Layer 12**: **blind_spots** — names the brain talks about but does not classify as first-class objects (currently 20, all flavor MISSING) — added Session #050
- `_coverage` — pct_classified metric (75.6%)
- **~52K tokens (5.3% of context)**

One Read call = full project intelligence. This REPLACES the old 50+ file session-start ceremony. NEVER skip this. If context compresses, re-read it.

### Mandatory traversal order (rule `feedback_brain_first_then_grep`)

When the user mentions an incident ID, transaction, or domain:
1. **`brain_state.incidents`** → if ID matches, READ `incidents[id].analysis_doc` immediately
2. **`brain_state.indexes.by_incident[id]`** → status, root_cause_summary, related_objects, doc
3. **`brain_state.objects[X]`** for each related object → annotations, claims, knowledge_docs
4. **`brain_state.blind_spots`** → if any related object is here, EXTRACT before continuing
5. **`brain_state.data_quality`** + **`known_unknowns`** + **`rules`**
6. **Only THEN** grep `knowledge/` as a fallback

The brain is useless if you don't traverse it. Globbing for an incident file when the brain has the link is the failure mode this rule prevents.

For mid-session queries without loading the full graph: `python brain_v2/graph_queries.py <command>`

## 📚 Required Reading (after brain_state.json)

1. **[lib/README.md](lib/README.md)** - Framework documentation
2. **[.agents/rules/sapwebgui_framework_findings.md](.agents/rules/sapwebgui_framework_findings.md)** - 103 experiments consolidated
3. **[.agents/rules/multi_agent_architecture.md](.agents/rules/multi_agent_architecture.md)** - Multi-agent design
4. **[.agents/workflows/hybrid_orchestration.md](.agents/workflows/hybrid_orchestration.md)** - When to use WebGUI vs BAPI
5. **[Brain_Architecture/brain_design_specification_v3.md](Brain_Architecture/brain_design_specification_v3.md)** - Brain v3 hybrid architecture (MANDATORY before any brain_v2/ changes)

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

## 📐 Companion & Report Quality Rules

1. **Cross-reference rule:** When updating ANY artifact (report, companion, skill), grep for the entity name (HBKID, table name, etc.) across ALL companions and reports. Fix every stale reference — not just the file you're editing.
2. **Gold DB before "not accessible":** Before claiming a table is not readable via RFC, check the Gold DB first (`SELECT name FROM sqlite_master WHERE type='table'`). The Gold DB has 68+ tables already extracted.
3. **Key validation:** Never infer SAP key construction from naming patterns. Always verify against actual data (read 3 rows from the table).
4. **Companion standard:** Every section needs: what is it, why it matters, who uses it, what happens if it's wrong, real examples with real data. A table without explanation is not documentation.
5. **No pending on closed reports:** If all transports are released, the report is CLOSED. No "pending" language.
6. **CLI tools accept arguments:** Scripts that check/compare specific entities (bank, transport, GL) must accept CLI arguments — never hardcode the entity and require file edits to change it.

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

## Agent Knowledge Architecture (v3 — Session #049, Layers 11+12 added Session #050)

This project uses a **hybrid knowledge architecture** optimized for AI agent use.
Full specification: `Brain_Architecture/brain_design_specification_v3.md`

### Source of Truth (git-tracked, portable, irreplaceable)
- `brain_v2/agent_rules/feedback_rules.json` — **58 behavioral rules** (severity-classified, with why + how_to_apply). Read at every session start.
- `brain_v2/annotations/annotations.json` — Object-level findings from code analysis
- `brain_v2/claims/claims.json` — System-level facts with evidence trails and confidence tiers
- `brain_v2/incidents/incidents.json` — **First-class incident records** (added Session #050). Status, root cause, fix path, related objects, analysis_doc inline. Source for `brain_state.incidents`. Every incident processed via the `incident-analyst` subagent appends here.
- `knowledge/domains/` — Rich domain documentation (15 domains)
- `knowledge/incidents/` — **Canonical location for incident analysis docs** (added Session #050). All `INC-<id>_<slug>.md` files live here, NOT in domain folders.
- `.agents/intelligence/PMO_BRAIN.md` — Pending work tracker
- `.agents/skills/sap_incident_analyst/SKILL.md` — **Incident processing 7-step protocol** (added Session #050)
- `.claude/agents/incident-analyst.md` — **Dedicated subagent for incidents** (added Session #050)
- `Zagentexecution/quality_checks/` — **Recurring data quality checks** (added Session #050). Class-of-defect detectors promoted from incidents.

### Generated Artifacts (rebuildable)
- `brain_v2/index/` — Text object index (one .md per analyzed object). Rebuild: `python -m brain_v2 index`
- `brain_v2/output/brain_v2_graph.json` — NetworkX graph (53K nodes). Rebuild: `python -m brain_v2 build`
- `brain_v2/output/brain_v2_active.db` — SQLite (PMO, claims, sessions). Rebuild: `python -m brain_v2 active-db`
- `brain_v2/brain_state.json` — 12-layer agent state. Rebuild: `python brain_v2/rebuild_all.py`

### Session Start (2 reads, complete picture)
1. Read this CLAUDE.md (overview)
2. Read `brain_v2/brain_state.json` (full intelligence — 12 layers)

### Brain v3 governance (rules learned Session #050)
- `feedback_brain_first_then_grep` — CRITICAL. Traverse brain_state.incidents → by_incident → objects[X].knowledge_docs → blind_spots BEFORE any glob/grep.
- `feedback_blind_spots_are_first_class` — HIGH. At session start, log `_coverage.pct_classified` and triage `blind_spots`. Don't let brain coverage decay.
- `feedback_force_include_referenced_names` — HIGH. Any object referenced from annotations/claims/incidents is force-included in objects[]. Never let names we talk about fall out of the brain.

### Incident processing
When the user passes a support incident: invoke the `incident-analyst` subagent (or follow the `sap_incident_analyst` skill manually). The 7-step protocol is: PARSE → BRAIN LOOKUP → GOLD DB PULL → CODE TRACE → ROOT CAUSE → CLASS GENERALIZATION → BRAIN ANNOTATION. Output: `knowledge/incidents/INC-<id>_<slug>.md` + first-class record in `brain_v2/incidents/incidents.json`.

### Session close — Phase 4b: Capture SAP Learnings (Session #050)
Every session that touches SAP must explicitly answer: "What did we learn about SAP itself this session that the next agent needs to know?" See `.agents/workflows/session_close_protocol.md` Phase 4b for the mandatory checklist. Empty section in retro = explicit "N/A" with one-sentence justification. Silent omission is a Phase 4b failure.

### Legacy Memory (~/.claude/memory/)
The `~/.claude/` memory files are a **cache**, not the source of truth. The authoritative knowledge lives in the project files above. If memory and project conflict, project wins.
