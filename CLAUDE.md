# CLAUDE.md - Instructions for AI Agents

## 🌐 Ecosystem — this is 1 of 4 interconnected projects (auto-awareness of the other 3)
Each owns its system's data; the others consume it **read-only** (rule **ADR-007 / BROADCAST-005**):
- **abapobjectscreation** (THIS) — **SAP source of truth** (SAP golden DB + brain + 28 skills). Consumed by `unesco-sap-brain` + `FINCLOSSING`.
- **unesco-sap-brain** — strategic SAP-redesign analysis + tools (consumes my SAP golden).
- **FINCLOSSING** — financial closing ABAP (consumes my brain + golden + skills).
- **unescore20-PPM-brain** — Salesforce / Core Planner (PPM) source (consumed by the SAP brain).

My cross-project edges: `ecosystem_link.md` + `refs_external.json`. Directory: `ecosystem-coordinator/ecosystem/data-capability-registry.md`. Rule: ADR-007 / BROADCAST-005.

## ⛔ ABAP CHANGE DISCIPLINE — mandatory before ANY ABAP write/deploy (BROADCAST-007)

Born from **INC-CLASS-LOSS (2026-06-12)** — a session corrupted real `N_MENARD` classes on D01 by writing
in-place via direct ADT with **no transport, no review, on objects we don't own**. The universal rule now lives
at `ecosystem-coordinator/.knowledge/way-of-working/sap-abap-change-discipline.md` (origin: CRP `unescrp` S-119).
**Spine (ranked):** (0) probe landscape read-only first → **(1) a RELEASED transport is the unit of change — D01
is DEV, not "the deploy"** → (2) no QAS ⇒ escalate as THE structural risk → (3) ATC via REST as the pre-release
gate (replace home-made checks) → (4) 4-eyes = JP approves the release (mandatory for AI code) → (5) abapGit/git
mirror + abaplint (channel is secondary to the released transport). **Hard rules:** own `Z*/Y*` objects only,
**never peer-team objects**; recover via Transport-of-Copies (`TMSCSYS` same-domain + "Overwrite Originals"),
**never ADT write**; don't reinvent the pipeline (`erpl-adt`/`abap-adt-api`). The two ADT write clients are
kill-switched (`ALLOW_D01_WRITES=1`) — the real fix is this process, then retire the blunt block.
**THE gated write path now exists (ported from CRP): `Zagentexecution/abap_deploy/deploy_object.py`** —
own-objects-only (manifest) + TADIR/SEOCLASS pre-flight + PRE-readback + hard diff-gate (HALT on deletions) +
W-5 operator guard + concurrent-writer guard + POST-readback byte-verify; `verify_mirror.py` keeps the git
mirror 0-diff; the `process-guardian` agent HALTs a close that deployed without that evidence. **Use it — NEVER
the legacy ad-hoc `deploy_*`/`reconstruct_*`/`force_*`/`direct_insert_*` scripts.** Transport RELEASE + ATC-REST
= POINT B (deferred). Related:
[[feedback_never_modify_standard_objects]] · [[feedback_new_objects_only_in_d01_never_p01]] ·
[[feedback_abapgit_is_the_standard_when_installed]].

## ⛔ STOP — THE OPERATING MODEL ALREADY EXISTS (read before proposing anything)

This project HAS a built, persisted **Capability Model** (Session #079). **DO NOT re-invent it, do not
propose a "new framework", do not redesign `brain_state.json`'s schema.** It is already there:

- **`brain_v2/capability_model/capability_model.json`** — the operating model: every domain × **10 capability
  dimensions** (S_STANDARD_REF · A_PROCESS · B_CODE · C_CONFIG · D_DATA · E_AUTH · F_INTERFACE_FILE ·
  G_CONFORMANCE · H_IMPROVE · R_S4_READINESS). A domain = **AS-DESIGNED (standard SAP) + AS-RUN (ours)**;
  G = the delta = the product. It is **Layer 15** of `brain_state.json` (`brain_state.capability_model`).
- Companions of the model: `s4_readiness_model.json` (fractal S/4 sub-scorecard) · `execution_backlog.json`
  (9 EXT + AN + RES tasks, what to extract + what to look for) · `applied_models.json` (which model applied
  to which domain) · `maturity.json` (model maturity, **measured**) · dashboard `companions/model_maturity_dashboard.html`.
- **Verified research base:** `brain_v2/research/` — 7 CLOSED deep-researches, `sources_index.json` (157 urls
  already read — dedupe against it), `findings_registry.json` (verified + refuted; never re-assert refuted).
- The plan is **generated from the matrix**: `python brain_v2/graph_queries.py capability_gaps`.
- Full spec: `knowledge/capability_model.md` · `capability_model_execution_plan.md`. Way-of-working rule:
  `feedback_capability_model_is_the_operating_model` (#149).

If you have NOT loaded `brain_state.capability_model`, you do not know the project state — load it, do not
rebuild from scratch. (This block exists because a parallel session re-invented the model after skipping the
brain read — s079.)

## 🏛️ CORE PRINCIPLES (constitutional — session #054)

Before any work, the agent operates under three **Core Principles** that govern HOW it decides, stores, and compresses. Every feedback rule derives from one of these. Full definitions in `brain_v2/core_principles/core_principles.json`. Loaded as Layer 0 of `brain_state.json`.

### CP-001 — Knowledge over velocity
**Never sacrifice traceability or knowledge for velocity.** Velocity ≠ knowledge. Losing traceability is irreversible; being slow is reversible. Terseness in conversation ≠ terseness in brain — the brain always preserves; the conversation can be short because the brain is behind.

### CP-002 — Preserve first, context is cheap
**With 1M context (Opus 4.6), size is no longer a constraint.** The real bottleneck is findability, solved with structure, not compression. Lossy compression only at query-time, never at storage-time. Structure lossless > prose when entities are repeatable; prose > structure when there is causal reasoning.

### CP-003 — Precision, evidence, facts
**Every decision, claim or recommendation must be anchored in maximum precision + verifiable evidence + checkable facts.** Opinion without evidence ≠ analysis. Approximation without measuring ≠ precision. Exact numbers, citable sources (path:line), explicit tiers (TIER_1/2/3).

These three override any other behavior. Violating a CP is higher-severity than violating a feedback_rule.

---

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

## 🧠 MANDATORY FIRST ACTION — Load Brain (TIERED, s079)

**EVERY session, before ANY other action, read the LEAN INDEX first (~800 tokens, not the 400K full brain):**

```
brain_v2/BRAIN_INDEX.md   ← read THIS first (lean L1 bootstrap)
```

### ⛔ STEP 2 — THE MOMENT A TOPIC/DOMAIN IS NAMED, RUN THE DOMAIN LOAD (s100, rule #181)

The index orients you; it does **not** make you competent on a topic. **As soon as the user names a
subject** (DMEE, PPC, AVC, EBS, a transaction, an incident area) — before proposing, diagnosing or
answering anything — run:

```
python brain_v2/load_domain.py <topic>      # e.g. dmee · "purpose of payment" · Payment_BCM
```

It resolves the topic to its domains and emits ONE ordered payload — domain docs + companions
(prose-extracted) + claims + incidents + annotations + feedback rules + extracted-code objects +
Gold DB tables + capability-model rows — chunked into `part_NN.md`. **READ ALL THE PARTS, IN ORDER.**
It prints a PERIPHERAL list too: what merely mentions the topic, named and not loaded, so nothing is
silently dropped.

**Do NOT wait to be asked.** This exists because between the 4KB index and the 400K brain there was
nothing, so every session re-discovered its own corpus by grepping and the user had to demand it.
Measured on DMEE: 40 domain docs + 20 companions + 165 claims + 11 incidents = ~667K tokens of
existing knowledge that a `graph_queries` drill never surfaces. Grepping is NOT loading.

Then **DRILL on demand** via `python brain_v2/graph_queries.py <cmd>` (capability_gaps, capability <dom>,
domain <name>, incident <id>, what_reads <table>, stats). Read the **full `brain_v2/brain_state.json`
ONLY when you need depth** the index doesn't give. This is tiered loading — Anthropic's own endorsed
"hybrid: small index up front + just-in-time drill-down" pattern (verified, research wwrqcozf1), which
avoids context rot. The full brain is PRESERVED (CP-002); it's just not loaded wholesale every session.

The full `brain_state.json` contains (Session #079 — **16 layers**, L0–L15):
- **Layer 0**: core_principles (CP-001/002/003)
- **Layer 1**: 742 analyzed objects with inline edges, annotations, claims, incidents
- **Layer 2**: Cross-cutting indexes (by_incident — enriched with status/doc/root_cause/fix, by_domain, uncertain_claims, superseded_claims)
- **Layer 3**: **151 feedback rules** (agent behavioral DNA)
- **Layer 4**: claims with evidence tier (+ machine-verification status, Layer-3 trust)
- **Layer 6**: known_unknowns · **Layer 7**: falsification predictions · **Layer 8**: superseded claims (anti-regression)
- **Layer 9**: User questions · **Layer 10**: Data quality issues
- **Layer 11**: First-class **incidents** (root cause + fix path + analysis_doc inline)
- **Layer 12**: **blind_spots** (0 — 100% coverage)
- **Layer 13**: **interactions** · **Layer 14**: **domains_layer** (3-axis: functional/module/process + process_map)
- **Layer 15**: **capability_model** — THE operating model (domain × 10 capabilities; see STOP block at top). Includes s4_readiness_submodel + execution_backlog + maturity. **← added Session #079**
- `_coverage` — pct_classified metric (**100% as of Session #079** — 0 blind spots; curation now SYNTHESIZES a queryable object for any referenced name with no graph node)
- **~357K tokens (~35% of context as of Session #079)** — grew when coverage hit 100%. The full curated graph is correct to PRESERVE (CP-002); the open decision is **tiered loading** (lean L1 index at bootstrap, drill via `graph_queries.py`). See `memory/feedback_knowledge_becomes_useful_via_structured_records.md`. Do NOT shrink the brain to save tokens — solve with structure, not lossy compression.

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
- `.agents/skills/sap_incident_analyst/SKILL.md` — **Support processing: Step-0 triage + Track A (diagnosis, 10 steps) + Track B (operational action, B1–B9)** (added #050, two-track since #099)
- `.claude/agents/incident-analyst.md` — subagent definition, kept as a **prompt template to read**; do NOT invoke it for the protocol (corrected #051)
- `Zagentexecution/quality_checks/incident_record_coverage_check.py` — **gate: every incident doc has a first-class record** (added #099, after 3 incidents were found invisible to the brain)
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

### Making knowledge queryable (Session #079)
Prose `.md` does NOT promote SAP objects into `brain_state.objects`. To make a name (SAPF100, OB09, an account) reachable, add **structured records** (incident + claims with the name in `related_objects`). The curation now **synthesizes** a queryable object for any referenced name with no graph node (`synthesize_object_from_records` in `build_brain_state.py`) — so blind spots → 0, coverage → 100%. Structural code edges (reads/calls/exits) still require the object's source to be a PARSED node. Full rule: `memory/feedback_knowledge_becomes_useful_via_structured_records.md`.

### Support processing — TWO TRACKS, one intake (updated Session #099)

**The MAIN agent executes. Do NOT delegate the protocol to the `incident-analyst` subagent** — that
was corrected in Session #051 after the subagent chased the wrong mechanism on INC-000005240 and
burned 154K tokens. The subagent definition is a prompt template to read, not an agent to invoke;
use subagents only for narrow mechanical sub-tasks (a grep, a list of rows).

**Step 0 is always TRIAGE** (`feedback_support_intake_triage_before_anything`, CRITICAL):
- **TRACK A — DIAGNOSIS** (the unknown is *why*): PARSE → BRAIN LOOKUP → GOLD DB PULL → CODE TRACE →
  PROCESS UNDERSTANDING → ROOT CAUSE → CLASS GENERALIZATION → BRAIN ANNOTATION → user gate → rebuild.
  Output: 13-section doc. Examples: INC-000006073, INC-000005240.
- **TRACK B — OPERATIONAL ACTION** (what to do is known; doing it correctly is the work):
  B1 authority of record → B2 precedent → B3 target-selection mechanism → B4 pre-change live read →
  B5 change spec → B6 execution *by an authorized human* (the agent never writes P01) →
  B7 post-change readback → B8 **drift sweep of the whole population** → B9 close gate + promotion.
  Output: 10-section doc, execution status first. Examples: INC-000006313, INC-000011781.

**Track B's three hard rules:** the authorizing letter/carton is the spec, never the requester's note
(INC-000011781: the note said "add Renata", the letters also said delete Martin). The ticket is the
*occasion* to sweep the population, not the scope (that sweep found 18 months of over-authorization
nobody asked about). And by the **2nd occurrence** of a scenario you owe a procedure doc + a recurring
check, or the cost per ticket never falls.

**Both tracks:** output `knowledge/incidents/INC-<id>_<slug>.md` **AND** a first-class record in
`brain_v2/incidents/incidents.json`. A doc without a record is invisible to BRAIN LOOKUP — gate it
with `python Zagentexecution/quality_checks/incident_record_coverage_check.py` (exit 0 = clean)
before closing. Full protocol: `.agents/skills/sap_incident_analyst/SKILL.md`.

### Session close — Phase 4b: Capture SAP Learnings (Session #050)
Every session that touches SAP must explicitly answer: "What did we learn about SAP itself this session that the next agent needs to know?" See `.agents/workflows/session_close_protocol.md` Phase 4b for the mandatory checklist. Empty section in retro = explicit "N/A" with one-sentence justification. Silent omission is a Phase 4b failure.

### Legacy Memory (~/.claude/memory/)
The `~/.claude/` memory files are a **cache**, not the source of truth. The authoritative knowledge lives in the project files above. If memory and project conflict, project wins.
