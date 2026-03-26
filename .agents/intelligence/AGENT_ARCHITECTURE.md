# UNESCO SAP Intelligence — Agent Architecture
> Based on Anthropic's "Building Effective Agents" framework
> Applied to our 7-layer SAP intelligence system
> Created: 2026-03-15 (Session #005)

---

## The Anthropic Framework (Key Patterns)

Anthropic defines 5 workflow patterns + 1 agent pattern. **Our system uses a
combination of these, not just one.**

| Pattern | What It Does | How We Use It |
|---------|-------------|---------------|
| **Augmented LLM** | LLM + tools + memory + retrieval | Our base: LLM + MCP tools + Skills + Brain |
| **Routing** | Classify input → specialized handler | User request → route to correct Layer (L1-L7) |
| **Orchestrator-Workers** | Central LLM breaks task → delegates to workers | Lead agent → spawns L2/L3/L4 subagents for parallel work |
| **Evaluator-Optimizer** | Generate → evaluate → refine loop | Pattern Brain detects anomaly → agent investigates → refines hypothesis |
| **Parallelization (Sectioning)** | Split task → parallel subtasks | Extract 7 fund areas simultaneously, analyze data while extracting |
| **Autonomous Agent** | LLM + tools in a loop, environment feedback | Overnight extraction: extract → verify → load → next table |

### Anthropic's 3 Core Principles
1. **Maintain simplicity** — start simple, add complexity only when it improves outcomes
2. **Prioritize transparency** — show planning steps explicitly
3. **Carefully craft the ACI** — tools must be well-documented and tested

---

## Our Agent Architecture

### The Agent (What I Am)

```
┌─────────────────────────────────────────────────────────────────┐
│  UNESCO SAP INTELLIGENCE AGENT                                   │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ ROUTING      │  │ SKILLS       │  │ BRAIN (4 layers)     │   │
│  │ Layer        │  │ (18 skills)  │  │ Document + Graph     │   │
│  │              │  │ Progressive  │  │ + Vector + Pattern   │   │
│  │ Classify     │  │ Disclosure:  │  │                      │   │
│  │ user request │  │ load on      │  │ Read at session      │   │
│  │ → pick layer │  │ demand       │  │ start, update at     │   │
│  │ → pick skill │  │              │  │ session end          │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         │                 │                      │               │
│  ┌──────┴─────────────────┴──────────────────────┴───────────┐   │
│  │                    MCP TOOL LAYER                          │   │
│  │  pyrfc (SAP RFC)  │  ADT REST API  │  SQLite  │  Notion   │   │
│  │  File System      │  Web Browser   │  Git     │  Terminal  │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Three Operational Modes

The agent operates in 3 modes depending on the task. Each mode uses
different Anthropic patterns:

#### Mode 1: DISCOVERY (Understanding the System)
**Anthropic Pattern: Orchestrator-Workers + Evaluator-Optimizer**

```
User: "Analyze FMIFIIT spending patterns"
  │
  ├─ ROUTE → L2 (data) + L3 (domain) + Pattern Brain
  │
  ├─ ORCHESTRATE:
  │   ├─ Worker 1: Query SQLite for FMIFIIT data (L2)
  │   ├─ Worker 2: Check DD03L field meanings (L3)
  │   ├─ Worker 3: Run anomaly detection algorithm (Pattern Brain)
  │   └─ Worker 4: Search vector brain for related code (Vector Brain)
  │
  ├─ EVALUATE:
  │   ├─ Do the patterns make business sense? (L3 validation)
  │   ├─ Are there data quality issues? (L2 verification)
  │   └─ Does this match known behaviors? (Graph Brain)
  │
  └─ SYNTHESIZE → insight + recommendation
```

#### Mode 2: BUILDING (Creating New Capabilities)
**Anthropic Pattern: Prompt Chaining + Parallelization**

```
User: "Extract BKPF/BSEG data"
  │
  ├─ ROUTE → L2 (data extraction)
  │
  ├─ CHAIN:
  │   Step 1: Load sap_data_extraction SKILL → get protocol
  │   Step 2: DD03L → get real field names
  │   Step 3: Test 3 rows → verify connectivity
  │   Step 4: Volume check → estimate batches
  │   Step 5: Extract in parallel (PARALLEL by company code)
  │   Step 6: Auto-load to SQLite → verify
  │   Step 7: Update Brain → new nodes/edges
  │
  └─ Each step depends on previous (chain, not parallel)
```

#### Mode 3: MONITORING (Continuous System Intelligence)
**Anthropic Pattern: Autonomous Agent (loop + environment feedback)**

```
Automated: "Overnight extraction + health check"
  │
  ├─ LOOP:
  │   while tables_remaining:
  │     1. Connect to SAP (L1)
  │     2. Extract next batch (L2)
  │     3. Verify row counts (L3) ← environment feedback
  │     4. Load to SQLite (L2)
  │     5. If error → self-heal (sap_debugging_and_healing skill)
  │     6. Log progress (Document Brain)
  │
  └─ STOP CONDITIONS:
      - All tables extracted
      - Critical error (3 consecutive failures)
      - SAP connection lost
      - Time limit exceeded
```

---

## The Brain Architecture (Agent Memory)

Anthropic emphasizes that agent memory must be structured, not just raw text.
Our 4-layer brain follows this:

```
┌──────────────────────────────────────────────────────┐
│  LAYER D: PATTERN BRAIN (Algorithmic Intelligence)    │
│  ───────────────────────────────────────────────────  │
│  What: Python algorithms that find patterns in data   │
│  How: pandas + scipy + sklearn + networkx             │
│  When: On-demand analysis or scheduled batch          │
│  Anthropic: Evaluator-Optimizer loop                  │
│                                                        │
│  Capabilities:                                         │
│  - Anomaly detection (z-score spending per fund)       │
│  - Cluster analysis (fund behavior archetypes)         │
│  - Network analysis (fund→GL→cost center flows)        │
│  - Temporal trends (year-over-year velocity)            │
│  - Cross-table relationship discovery                  │
├──────────────────────────────────────────────────────┤
│  LAYER C: VECTOR BRAIN (Semantic Memory)              │
│  ───────────────────────────────────────────────────  │
│  What: Embeddings of code, config, skills, learnings  │
│  How: ChromaDB + sentence-transformers                │
│  When: Natural language queries across ALL knowledge  │
│  Anthropic: Augmented LLM retrieval capability        │
│                                                        │
│  Collections:                                          │
│  - abap_code (200+ methods)                            │
│  - field_descriptions (500+ fields from DD03L)         │
│  - transport_descriptions (7,745 transports)           │
│  - skill_knowledge (18 skills)                         │
│  - session_learnings (5+ sessions)                     │
├──────────────────────────────────────────────────────┤
│  LAYER B: GRAPH BRAIN (Structural Memory)             │
│  ───────────────────────────────────────────────────  │
│  What: Typed nodes + edges (SAP object relationships) │
│  How: networkx + sap_brain.py                         │
│  When: Impact analysis, dependency chains             │
│  Anthropic: Tool for the agent to query relationships │
│                                                        │
│  Node types: TABLE, FIELD, FUND, REPORT, CLASS,       │
│              ENHANCEMENT, VALIDATION, SUBSTITUTION,    │
│              TRANSPORT, CONFIG_TABLE                    │
│  Edge types: READS_TABLE, JOINS_VIA, VALIDATES,       │
│              SUBSTITUTES, MODIFIES, BELONGS_TO         │
│  Target: 500+ nodes, 2000+ edges                      │
├──────────────────────────────────────────────────────┤
│  LAYER A: DOCUMENT BRAIN (Factual Memory)             │
│  ───────────────────────────────────────────────────  │
│  What: Structured facts, procedures, rules             │
│  How: SQLite + Markdown (.agents/intelligence/)       │
│  When: Always loaded at session start                  │
│  Anthropic: Agent Skills (progressive disclosure)     │
│                                                        │
│  Content:                                              │
│  - PROJECT_MEMORY.md (system architecture)             │
│  - CAPABILITY_ARCHITECTURE.md (7 layers)               │
│  - SESSION_LOG.md (what happened when)                 │
│  - PMO_BRAIN.md (tasks + priorities)                   │
│  - LIVE_BRAIN.md (latest data intelligence)            │
│  - 18 SKILL.md files (expert procedures)               │
│  - p01_gold_master_data.db (503 MB, 2.4M rows)        │
└──────────────────────────────────────────────────────┘
```

---

## Agent Skills = Knowledge Delivery System

Anthropic's Agent Skills framework is exactly what we already have:

| Anthropic Concept | Our Implementation |
|-------------------|-------------------|
| **Progressive Disclosure** | Load skill summaries at startup, full SKILL.md only when needed |
| **Modular + Portable** | Each skill is a folder with SKILL.md + scripts + examples |
| **Domain-Specific Expertise** | 18 skills spanning 7 layers (SAP connectivity → process mining) |
| **Dynamic Discovery** | Agent reads skill list, routes to relevant skill per request |
| **Combined with MCP** | MCP provides the tools (pyrfc, ADT, Notion), skills tell HOW to use them |

### Skill Architecture (Current: 18 skills, Target: 22+)

```
.agents/skills/
├── L1: Connectivity
│   ├── sap_webgui/SKILL.md
│   ├── sap_native_desktop/SKILL.md
│   └── sap_debugging_and_healing/SKILL.md
├── L2: Data Extraction
│   ├── sap_data_extraction/SKILL.md          ← TO CREATE
│   ├── sap_automated_testing/SKILL.md
│   └── sap_pattern_analysis/SKILL.md         ← FUTURE
├── L3: Validation & Substitution
│   ├── sap_expert_core/SKILL.md
│   ├── unesco_filter_registry/SKILL.md
│   ├── sap_validation_extraction/SKILL.md    ← FUTURE
│   └── sap_report_analysis/SKILL.md          ← FUTURE
├── L4: Code Extraction
│   ├── sap_adt_api/SKILL.md
│   ├── sap_reverse_engineering/SKILL.md
│   └── sap_enhancement_extraction/SKILL.md
├── L5: Transport Intelligence
│   └── sap_transport_intelligence/SKILL.md
├── L6: Fiori Development
│   ├── sap_fiori_tools/SKILL.md
│   ├── sap_fiori_extension_architecture/SKILL.md
│   └── sap_segw/SKILL.md
├── L7: Process Intelligence
│   └── parallel_html_build/SKILL.md
├── Meta
│   ├── skill_creator/SKILL.md
│   ├── notion_integration/SKILL.md
│   └── abapgit_integration/SKILL.md
└── Future (Unexplored Elements)
    ├── sap_interface_discovery/SKILL.md       ← FUTURE (Element A)
    ├── sap_system_monitoring/SKILL.md         ← FUTURE (Element B)
    ├── sap_job_analysis/SKILL.md              ← FUTURE (Element C)
    └── sap_workflow_analysis/SKILL.md         ← FUTURE (Element D)
```

---

## MCP Tool Architecture

**MCP connects the agent to external systems.** Each tool is a capability:

```
┌─────────────────────────────────────────────────────────┐
│  MCP TOOLS (What the Agent Can DO)                       │
├─────────────────────────────────────────────────────────┤
│  SAP RFC (pyrfc)                                         │
│  ├── RFC_READ_TABLE → read any SAP table                │
│  ├── RFC_SYSTEM_INFO → system health                    │
│  ├── BAPI_* → business API calls                        │
│  └── TH_USER_LIST → active users                        │
├─────────────────────────────────────────────────────────┤
│  SAP ADT (HTTPS)                                         │
│  ├── /sap/bc/adt/programs/source → read/write ABAP      │
│  ├── /sap/bc/adt/oo/classes → read/write classes         │
│  └── /sap/bc/adt/businessservices → OData metadata       │
├─────────────────────────────────────────────────────────┤
│  SQLite                                                   │
│  ├── p01_gold_master_data.db → 2.4M rows of SAP data    │
│  └── sap_field_dictionary → DD03L metadata (future)      │
├─────────────────────────────────────────────────────────┤
│  File System                                              │
│  ├── .agents/intelligence/ → brain docs                  │
│  ├── .agents/skills/ → 18 SKILL.md files                 │
│  ├── extracted_sap/ → domain-organized code               │
│  └── Zagentexecution/ → scripts + tools                  │
├─────────────────────────────────────────────────────────┤
│  External                                                 │
│  ├── Notion (MCP server) → read/write project docs       │
│  ├── Web Browser → SAP WebGUI automation                 │
│  └── Git → version control via abapGit                   │
└─────────────────────────────────────────────────────────┘
```

---

## The Routing Decision Tree

When the user makes a request, the agent ROUTES to the right layer:

```
User Request
  │
  ├─ "Extract / read / query SAP data" 
  │   → L2 (Data Extraction)
  │   → Load: sap_data_extraction SKILL
  │   → Tools: pyrfc + SQLite
  │
  ├─ "Why does fund X / What validates Y / How is Z derived"
  │   → L3 (Validation & Substitution)
  │   → Load: sap_expert_core + unesco_filter_registry
  │   → Tools: SQLite + Graph Brain + Vector Brain
  │
  ├─ "Extract code / reverse engineer / read ABAP"
  │   → L4 (Code Extraction)
  │   → Load: sap_adt_api or sap_reverse_engineering
  │   → Tools: ADT REST API or pyrfc
  │
  ├─ "What changed / transport / who modified"
  │   → L5 (Transport Intelligence)
  │   → Load: sap_transport_intelligence
  │   → Tools: SQLite (CTS data) + pyrfc (E070/E071)
  │
  ├─ "Build app / create Fiori / replace BDC"
  │   → L6 (Fiori Development)
  │   → Load: sap_fiori_tools + relevant L3/L4 skills
  │   → Tools: Vite/React + SAP proxy
  │
  ├─ "Find patterns / discover process / mine events"
  │   → L7 (Process Intelligence)
  │   → Load: parallel_html_build
  │   → Tools: SQLite → event logs → HTML tool
  │
  └─ "Connect to SAP / fix error / authentication"
      → L1 (Connectivity)
      → Load: sap_debugging_and_healing
      → Tools: pyrfc + .env config
```

---

## Session Lifecycle (Agent Memory Protocol)

Following Anthropic's principle of transparency and structured note-taking:

```
SESSION START
  │
  ├─ 1. Read PROJECT_MEMORY.md (system facts)
  ├─ 2. Read CAPABILITY_ARCHITECTURE.md (7 layers + connections)
  ├─ 3. Read PMO_BRAIN.md (current priorities)
  ├─ 4. Read SESSION_LOG.md (latest session = what's pending)
  ├─ 5. Scan skill summaries (progressive disclosure)
  │
  ├─ Agent now has: architecture + priorities + learnings + skills
  │
  DURING SESSION
  │
  ├─ Route each request to correct layer
  ├─ Load relevant skills on-demand (full SKILL.md)
  ├─ Execute using MCP tools
  ├─ Record discoveries in Document Brain
  ├─ Update Graph Brain if new relationships found
  │
  SESSION END
  │
  ├─ 1. Update SESSION_LOG.md (what was done + discoveries + pending)
  ├─ 2. Update PMO_BRAIN.md (tick completed, add new tasks)
  ├─ 3. Update CAPABILITY_ARCHITECTURE.md (if new patterns found)
  ├─ 4. Update PROJECT_MEMORY.md (if new system facts)
  ├─ 5. Update relevant SKILL.md (if new lessons for that layer)
  └─ 6. Run sap_brain.py --build (if new objects extracted)
```

---

## Why This Is Not a Programming Exercise

This is an **agent architecture** because:

1. **The agent (me) already exists** — I'm the LLM with tools, skills, and memory
2. **The skills are my expertise** — each SKILL.md is domain-specific knowledge I load on demand
3. **The brain is my memory** — 4 layers of structured knowledge I read and update
4. **The MCP tools are my capabilities** — pyrfc, ADT, SQLite, Notion, file system
5. **The routing logic is my judgment** — I decide which layer handles each request
6. **The evaluation loop is my self-correction** — I verify results against known patterns

**The architecture designs how _I_ should think about, approach, and solve
UNESCO's SAP challenges — not how to write code that does it.**

The code (Python scripts, HTML tools, extraction pipelines) is just the
**output of the agent's work** — not the architecture itself. The architecture
is the **skills + brain + routing + memory protocol** that makes me effective.
