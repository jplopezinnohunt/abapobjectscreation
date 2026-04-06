# BRAIN V2: Universal Knowledge Graph + Impact Analysis Engine

> Supersedes: BRAIN_ARCHITECTURE.md (Session #005)
> Created: 2026-04-05 | Revised: 2026-04-06 (Session #039 design review)
> Status: Architecture Design — APPROVED for execution
> Problem Statement: The brain has 73,968 nodes but 98.4% are taxonomic (HAS_FUND, BELONGS_TO). Impact analysis requires behavioral edges (CALLS, READS_FIELD, CONFIGURES, TRIGGERS) that don't exist yet.

## Design Principles (Session #039 Review)

These principles were refined through debate during the design review. They are NON-NEGOTIABLE.

### 1. Living Organism, Not Static Snapshot
The brain grows every session. Data, model, and reasoning all evolve. No edge is ever deleted — superseded edges get `valid_until` timestamps (Graphiti temporal pattern). The brain remembers what was true and when.

### 2. Companions Are Knowledge Checkpoints
Each companion HTML is a snapshot of the brain's understanding at a point in time. When regenerated, the diff between v(N) and v(N+1) IS the evolution of thought. Companions carry `brain_checkpoint` metadata: version, brain_hash, session, date, node/edge counts. Old versions are git-tagged before overwrite.

### 3. Continuous Enrichment Loop (Celonis PI Graph Pattern)
Every session close triggers `brain_v2 --ingest-session N`. Retro findings → new edges with `evidence="session_NNN"`. The brain grows without manual intervention.

### 4. Confidence Decay
Edges discovered long ago and never revalidated lose confidence: -0.05 per 10 sessions without revalidation. `--stale` query surfaces edges below threshold. `--refresh NODE_ID` triggers RFC re-extraction for on-demand validation.

### 5. Model Self-Evolution (Agentic GraphRAG Pattern)
The brain_spec.yaml is append-only and versionable. When a session discovers a new relationship type, the agent adds it to the spec, writes a parser, and runs incremental build. No rewrite. No migration. The brain proposes its own schema extensions; human approves.

### 6. OCEL 2.0 for Process Mining
Process events are object-centric (pm4py OCEL support). Events link to graph objects (tables, tcodes), not just sequences. This enables "which objects does this process step touch?" queries.

### 7. Self-Improvement of Reasoning — 3 Validated Loops

The brain improves HOW it thinks, not just WHAT it knows. Three loops, all validated in market/research:

**A. Critique Loop (Self-Check per Query)**
Every query result passes through a self-check: missing edges flagged, low-confidence paths highlighted, unreachable nodes surfaced. The brain says "here's my answer AND here's what I don't know." Implementation: `query.py` returns `{result, gaps_found, low_confidence_paths}`.

**B. Co-Evolutionary Loop ([Agentic-KGR, arxiv 2510.09156](https://arxiv.org/abs/2510.09156))**
The LLM and the knowledge graph improve each other through multi-round interaction. Each session Claude reads the brain → discovers gaps → fills them → brain improves → next session Claude reasons better. +33.3 points over traditional RL in knowledge graph extraction benchmarks. Implementation: `session_ingestor.py` reads session retro, extracts "gaps identified" → creates `NEEDS_INVESTIGATION` edges on nodes with missing dependencies.

**C. Refinement Loop (ARC Prize 2025 Pattern — [arcprize.org](https://arcprize.org/blog/arc-prize-2025-results-analysis))**
Edge weights adjust based on usage feedback. When a user follows an impact path the brain suggested → that path's edges get +0.1 weight. When a brain suggestion is ignored or rejected → edges get -0.05. Over 10+ sessions, the brain's traversal priorities align with what actually matters. Implementation: `cli.py --feedback QUERY_ID useful|not_useful` adjusts weights.

```yaml
# In brain_spec.yaml:
reasoning_evolution:
  critique_loop:
    trigger: "every query"
    output: "gaps_found list appended to query result"
  co_evolution:
    trigger: "session close"  
    input: "session retro gaps"
    output: "NEEDS_INVESTIGATION edges on gap nodes"
  refinement_signal:
    trigger: "user feedback on query"
    adjustment: "+0.1 weight on useful paths, -0.05 on ignored paths"
    decay_floor: 0.3  # edges never drop below 0.3 weight
```

### 8. Platform Absorption — The Brain Evolves When the Ecosystem Evolves

The brain's reasoning improves NOT by rewriting code, but by absorbing new platform capabilities via standard interfaces:

**A. MCP as Brain Interface (available now)**
The brain exposes itself as an MCP server. When Claude (or any MCP-compatible agent) queries impact/dependency/gaps, it uses the standard MCP protocol. When Anthropic improves Claude's reasoning, the brain benefits automatically — the same MCP interface, better model behind it. Reference: [Anthropic Knowledge Graph Memory MCP Server](https://www.pulsemcp.com/servers/modelcontextprotocol-knowledge-graph-memory), [Neo4j MCP integration](https://neo4j.com/developer/genai-ecosystem/model-context-protocol-mcp/).

**B. Agent Skills as Brain-Invokable Expertise (available now)**
Anthropic launched [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) as an open standard. Our 38 skills ARE Agent Skills. The brain should invoke the right skill when a query needs domain expertise: `--impact FPAYP.XREF3` → brain traverses graph → invokes `sap_payment_bcm_agent` skill for expert interpretation of the payment chain.

**C. Agent Teams as Critique Infrastructure (experimental, v2.1.32)**
[Agent Teams](https://code.claude.com/docs/en/agent-teams) enable multi-agent coordination. The critique loop (Principle 7A) is implemented as a separate agent — not a function in the same process. One agent queries, another critiques, a third fills gaps. Each has its own context window and can reason independently.

**D. Model Upgrades = Free Reasoning Upgrades**
When Anthropic releases Claude 5 / Opus 5 / any new model, the brain doesn't change. The new model queries the same MCP server, reads the same graph, invokes the same skills — but reasons BETTER about them. The brain's "self-improvement of thinking" is partially outsourced to model evolution. Our job is to keep the interfaces standard so we absorb upgrades automatically.

```yaml
# In brain_spec.yaml:
platform_integration:
  mcp_server:
    protocol: "MCP 1.0"
    endpoints: ["brain://impact", "brain://depends-on", "brain://gaps", "brain://similar-to"]
    status: "phase_4_implementation"
  agent_skills:
    invokable_skills: 38  # from .agents/skills/
    invocation_trigger: "query domain matches skill domain"
  agent_teams:
    critique_agent: "separate Claude instance reviews query results"
    status: "experimental"
  model_absorption:
    principle: "standard interfaces → new model = better reasoning for free"
```

### 9. Ecosystem Replicability
The brain_spec.yaml is domain-agnostic. SAP UNESCO is the first instance. The template promotes to ecosystem-coordinator as `enterprise-brain` skill. Other projects instantiate with their own parsers (React, TypeScript, Salesforce) but the same graph engine, query engine, and companion pattern.

### Sources (Validated Market Patterns)
- [Graphiti — Real-Time Temporal Knowledge Graphs](https://github.com/getzep/graphiti) + [Paper](https://arxiv.org/abs/2501.13956)
- [Agentic GraphRAG — Neo4j](https://neo4j.com/nodes-ai/agenda/agentic-graphrag-autonomous-knowledge-graph-construction-and-adaptive-retrieval/)
- [Celonis Process Intelligence Graph](https://www.celonis.com/platform/process-intelligence-graph)
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [Stardog Agentic AI + KG](https://www.stardog.com/agentic-ai-knowledge-graph/)

---

## Executive Summary

### The Dual Paradigm (NON-NEGOTIABLE)

Brain v2 serves **two equally important purposes**. Neither is secondary.

**1. "What exists and how it works"** — The living map of the system. Who reads what table, who calls what function module, what config activates what code, how a payment flows end-to-end from invoice to bank file. This is the foundation for:
- **Understanding the system** — A new consultant can ask "show me everything involved in the payment process" and get the complete dependency chain in seconds
- **Planning tests** — Before testing a transport, know exactly which objects, tables, and processes are involved
- **Preparing migrations** — S/4HANA readiness: which custom code reads which tables, which FMs are exposed to external systems, which BAdIs are implemented
- **Onboarding and documentation** — The graph IS the living documentation, always current because it's parsed from real code and config

**2. "What happens if you change something"** — Impact analysis. This comes FREE on top of the existence map because the same edges that say "YCL_IDFI_CGI_DMEE_FR reads FPAYP.XREF3" also answer "if you touch FPAYP.XREF3, YCL_IDFI_CGI_DMEE_FR breaks". The existence graph IS the impact graph — they are the same data structure.

**These two are inseparable.** The graph of existence is the graph of impact. Every edge that describes "how it works" simultaneously describes "what breaks if you change it." This is why the brain must be built BEFORE continuing to evaluate more information — the new model will generate new conclusions from existing data simply by revealing connections that were previously invisible.

---

Brain v1 answered "what exists" as a flat taxonomy (HAS_FUND, BELONGS_TO). Brain v2 adds **behavioral edges** (CALLS_FM, READS_FIELD, CONFIGURES_FORMAT) that make both paradigms operational.

The core insight: UNESCO's SAP landscape is already 90% extracted into local data. The missing piece is not more data -- it is the **edges between existing data**. We have 896 ABAP files with parseable SELECT/CALL FUNCTION statements. We have 68 SQLite tables with foreign key relationships. We have config tables (T042Z, DMEE, FBZP chain) that define runtime behavior. We have process mining event logs that define execution paths. None of this is connected.

Brain v2 builds those connections. The result is an engine that can answer:

**Paradigm 1 — Existence & Function:**
- "What does the payment process depend on end-to-end?" (dependency tracing)
- "Show me everything similar to this DMEE exit" (similarity search)
- "What config exists but is never executed?" (gap analysis)
- "Which external systems call which function modules?" (integration map)

**Paradigm 2 — Change Impact:**
- "If I change FPAYP.XREF3, what breaks?" (impact analysis)
- "If I deactivate this DMEE tree, which company codes lose payment capability?" (config impact)
- "If I modify this BAdI, which processes are affected?" (code impact)

**Paradigm 3 — Discovery (emergent from the graph itself):**
The brain doesn't just answer questions — it **discovers use cases** by revealing connections nobody asked about. When you connect code → config → process → integration, patterns emerge that were invisible in isolation:
- "This RFC-enabled FM is called by SISTER AND by a background job AND by a transport — it's a convergence point nobody documented"
- "These 3 DMEE trees share the same BAdI exit but serve different banks — a change to the exit class affects all 3 banking channels simultaneously"
- "This substitution rule feeds a field that 4 different processes read — it's a hidden single point of failure"
- "These 12 custom reports all read the same 3 tables but are maintained by different teams — they're candidates for consolidation"

Discovery is not a query you run — it's what happens when the graph exists. Gap analysis, community detection, centrality scoring, and orphan identification all produce findings that no one asked for but everyone needs. **The graph generates its own backlog of investigation targets.** This is why the brain must be built before continuing to evaluate information — every new edge potentially reveals a discovery that changes priorities.

### What Market Leaders Do (And What We Borrow)

| Tool | Core Idea We Borrow | How It Maps |
|------|---------------------|-------------|
| **Panaya** | Change impact analysis via code dependency graph | Section A: CALLS/READS_FIELD edges from parsed ABAP |
| **Tricentis LiveCompare** | Object-level regression risk scoring | Section C: impact radius calculation per node |
| **LeanIX** | Application portfolio + dependency mapping | Section A: SYSTEM, APPLICATION, INTERFACE nodes + CALLS_SYSTEM edges |
| **Celonis** | Object-centric process mining (OCEL 2.0) | Section B.3: Process events linked to graph objects |
| **ServiceNow CMDB** | Configuration items + relationship types + impact rules | Section A: CONFIG_ITEM pattern with typed relationships |
| **Neo4j** | Property graph with Cypher traversal | Section D: Why we use NetworkX over Neo4j for this scale |
| **SAP Signavio** | Process model + mining convergence | Section B.3: BPMN-like process overlay on data graph |
| **SNP/Datavard** | System analysis for transformations | Section C.4: Gap analysis (configured-but-unused) |
| **Rev-Trac** | Transport dependency chains | Already have this in CTS data; Section B.2 adds edges |

---

## A. Unified Knowledge Graph Schema

### A.1 Design Philosophy: The CMDB Pattern

ServiceNow's CMDB succeeds because every entity is a Configuration Item (CI) with typed relationships. We adopt this pattern: every SAP artifact is a node with a canonical type, and every dependency is an edge with a semantic type. The graph is a property graph (nodes and edges carry arbitrary key-value metadata).

**Scale target:** ~80,000 nodes (mostly existing), ~200,000 edges (mostly new behavioral edges). This is comfortably within NetworkX's in-memory capacity on any modern machine.

### A.2 Node Types (30 types, 6 categories)

#### Category 1: Code Objects (from `extracted_code/` + `extracted_sap/`)

| Type | Description | Source | Est. Count | Example |
|------|------------|--------|-----------|---------|
| `ABAP_CLASS` | OO class (ZCL_*, YCL_*, CL_*) | extracted_code/ dirs | ~30 | `YCL_IDFI_CGI_DMEE_FR` |
| `ABAP_METHOD` | Individual method within a class | .abap files | ~500 | `YCL_IDFI_CGI_DMEE_FR::IF_EX_FI_CGI_DMEE_EXIT_W~FORMAT_FIELD` |
| `FUNCTION_MODULE` | RFC-enabled or internal FM | TFDIR_CUSTOM (3,073 rows) | ~3,073 | `Z_RFC_READ_FUND_CENTER` |
| `ABAP_REPORT` | Z/Y reports + includes | extracted_code/UNESCO_CUSTOM_LOGIC | ~200 | `YRGGBS00` |
| `ENHANCEMENT` | BAdI implementation or user exit | extracted_code/FM_BUDGETING/*.abap | ~50 | `ZXFMCU09_RPY` |
| `BSP_APP` | Fiori/UI5 BSP application | extracted_sap/*/Fiori_Apps/*/bsp | 7 | `ZHCM_OFFBOARDING` |
| `ODATA_SERVICE` | Gateway OData service | Known list + /IWBEP tables | ~10 | `Z_CRP_SRV` |
| `PACKAGE` | ABAP dev package (DEVC) | cts_objects PGMID=R3TR/OBJECT=DEVC | ~100 | `YWFI` |

#### Category 2: Data Objects (from Gold DB schema)

| Type | Description | Source | Est. Count | Example |
|------|------------|--------|-----------|---------|
| `SAP_TABLE` | Database table or view | Gold DB sqlite_master + DD03L | ~68 | `FMIFIIT` |
| `TABLE_FIELD` | Individual field within a table | PRAGMA table_info() on Gold DB | ~2,000 | `FMIFIIT.XREF3` |
| `DOMAIN_VALUE` | Fixed domain value that controls logic | T042Z.DTFOR, T042A.ZLSCH | ~500 | `DTFOR=/CGI_XML_CT_UNESCO` |

#### Category 3: Configuration Objects (from Gold DB config tables)

| Type | Description | Source | Est. Count | Example |
|------|------------|--------|-----------|---------|
| `DMEE_TREE` | Payment medium format definition | T042Z.DTFOR | ~20 | `/CGI_XML_CT_UNESCO` |
| `PAYMENT_METHOD` | Payment method per company code | T042A | ~76 | `UNES-T (wire transfer)` |
| `BCM_RULE` | BCM batch grouping rule | BNK_BATCH_HEADER | ~15 | `PAYROLL` |
| `HOUSE_BANK` | Bank master for payments | T012/T012K | ~211 | `SOG01` |
| `VALIDATION_RULE` | OB28/FMDERIVE validation | To be extracted | ~50 | `OB28#015 (max amount)` |
| `SUBSTITUTION_RULE` | OBBH/GGB1 substitution | To be extracted | ~30 | `OBBH: PRCTR from FISTL` |
| `NUMBER_RANGE` | NROB number range object | cts_objects | ~20 | `FI_DOC_NUM` |
| `JOB_DEFINITION` | Background job schedule | TBTCO+TBTCP | ~228 | `RFEBKA00 (bank stmt import)` |

#### Category 4: Organizational / Master Data

| Type | Description | Source | Est. Count | Example |
|------|------------|--------|-----------|---------|
| `COMPANY_CODE` | Organizational unit | T001 | 10 | `UNES` |
| `FUND` | Budget fund | funds table | 64,766 | `AAFRA2023` |
| `FUND_AREA` | FM area | funds.FIKRS distinct | 7 | `UNES` |
| `FUND_CENTER` | Responsible unit | fund_centers | 710 | `ADM` |
| `GL_ACCOUNT` | General ledger account | P01_SKA1 | ~2,491 | `40010000` |
| `COST_ELEMENT` | CO cost element | P01_CSKA | ~535 | `641000` |

#### Category 5: Integration / Infrastructure

| Type | Description | Source | Est. Count | Example |
|------|------------|--------|-----------|---------|
| `SAP_SYSTEM` | SAP system instance | RFCDES distinct systems | ~38 | `P01`, `D01`, `Y1` |
| `EXTERNAL_SYSTEM` | Non-SAP system | Integration map | ~15 | `SISTER`, `COUPA`, `SocGen` |
| `RFC_DESTINATION` | SM59 RFC connection | rfcdes (239 rows) | ~239 | `P01CLNT350` |
| `ICF_SERVICE` | HTTP endpoint in SAP | icfservice (6,477 rows) | ~100 (active) | `/sap/opu/odata` |
| `IDOC_TYPE` | IDoc message type | edidc distinct | ~50 | `PROJECT02` |

#### Category 6: Process / Transport / Knowledge

| Type | Description | Source | Est. Count | Example |
|------|------------|--------|-----------|---------|
| `PROCESS` | End-to-end business process | Coordinator skill | ~15 | `P2P`, `Payment_E2E` |
| `PROCESS_STEP` | Individual step in a process | Process mining event logs | ~100 | `PR Created`, `GR Posted` |
| `TRANSPORT` | CTS transport order | cts_transports (7,745) | 7,745 | `D01K9B0CBF` |
| `SKILL` | Agent skill document | .agents/skills/ | ~38 | `sap_payment_bcm_agent` |
| `KNOWLEDGE_DOC` | Domain analysis document | knowledge/**/*.md | ~51 | `payment_architecture` |

**Total estimated nodes: ~80,000** (current 73,968 + ~6,000 new code/config/field nodes)

### A.3 Edge Types (45 types, 8 categories)

This is where Brain v2 fundamentally differs from v1. Each edge type carries semantic meaning for impact analysis.

#### Category 1: Code Dependency Edges (parsed from ABAP source)

| Edge Type | From -> To | How Detected | Impact Direction | Est. Count |
|-----------|-----------|-------------|-----------------|-----------|
| `CALLS_FM` | Method/Report -> Function_Module | `CALL FUNCTION 'name'` in source | Forward: caller breaks if FM signature changes | ~2,000 |
| `READS_TABLE` | Method/Report -> SAP_Table | `SELECT * FROM table` in source | Forward: code breaks if table structure changes | ~500 |
| `WRITES_TABLE` | Method/Report -> SAP_Table | `INSERT INTO table`, `MODIFY table`, `UPDATE table` | Forward: data consumers break if write logic changes | ~200 |
| `READS_FIELD` | Method/Report -> Table_Field | `SELECT field FROM table` or `wa-field` usage | Precise field-level impact | ~3,000 |
| `IMPLEMENTS_BADI` | Class -> Enhancement | `CLASS ... DEFINITION ... FOR ... EXIT` pattern | Backward: BAdI framework calls implementor | ~30 |
| `INHERITS_FROM` | Class -> Class | `INHERITING FROM superclass` | Bidirectional: super changes break sub | ~20 |
| `IMPLEMENTS_INTF` | Class -> Interface | `INTERFACES if_name` | Contract: interface changes break all implementors | ~40 |
| `RAISES_EVENT` | Method -> Event_Name | `RAISE EVENT` in source | Forward: event consumers affected | ~20 |
| `BELONGS_TO_PACKAGE` | Code_Object -> Package | TADIR DEVCLASS | Organizational grouping | ~3,000 |

#### Category 2: Configuration Dependency Edges (from Gold DB tables)

| Edge Type | From -> To | Source Table | Impact Meaning | Est. Count |
|-----------|-----------|-------------|----------------|-----------|
| `USES_DMEE_TREE` | Company_Code+Payment_Method -> DMEE_Tree | T042Z: ZBUKR+ZLSCH -> DTFOR | Changing DMEE tree changes payment file format for those co-codes | ~40 |
| `ROUTES_TO_BANK` | Payment_Method -> House_Bank | T042A: ZLSCH -> HBKID+HKTID | Changing routing changes which bank receives payments | ~76 |
| `PROCESSES_VIA_BCM` | Payment_Method -> BCM_Rule | BNK_BATCH_HEADER rule assignment | Changing BCM rule changes approval workflow | ~15 |
| `CONFIGURES_FORMAT` | DMEE_Tree -> ABAP_Class | T042Z.DTFOR -> BAdI exit class | Changing format tree changes which exit code runs | ~20 |
| `VALIDATES_FIELD` | Validation_Rule -> Table_Field | OB28 config (to be extracted) | Changing validation blocks/allows postings | ~100 |
| `SUBSTITUTES_FIELD` | Substitution_Rule -> Table_Field | OBBH/GGB1 config (to be extracted) | Changing substitution changes derived field values | ~60 |
| `CONTROLS_POSTING_PERIOD` | Config -> Company_Code | T001B equivalent | Changing period control blocks/allows postings | ~10 |
| `ASSIGNS_NUMBER_RANGE` | Number_Range -> Company_Code+Doc_Type | NRIV config | Changing NR resets counters (CRITICAL) | ~30 |

#### Category 3: Data Join Edges (from proven SQL relationships)

| Edge Type | From -> To | Join Key | Purpose | Est. Count |
|-----------|-----------|---------|---------|-----------|
| `JOINS_VIA` | SAP_Table -> SAP_Table | FK specification | Data model navigation | ~30 |
| `FIELD_MAPS_TO` | Table_Field -> Table_Field | e.g., FMIFIIT.KNBELNR -> BKPF.BELNR | Precise join field mapping | ~60 |

The full join map (from SKILL.md and Golden Query):
```
FMIFIIT.FONDS     -> funds.FINCODE          (fund master lookup)
FMIFIIT.FISTL     -> fund_centers.FICTR      (fund center master)
FMIFIIT.KNBELNR   -> BKPF.BELNR             (FM-to-FI bridge)
FMIFIIT.KNGJAHR   -> BKPF.GJAHR             (FM-to-FI bridge)
FMIFIIT.BUKRS     -> BKPF.BUKRS             (FM-to-FI bridge)
FMIFIIT.KNBUZEI   -> bseg_union.BUZEI       (line-level bridge)
FMIFIIT.OBJNRZ    -> PRPS.OBJNR             (WBS element link)
PRPS.PSPHI         -> PROJ.PSPNR             (WBS -> Project)
EKKO.EBELN         -> EKPO.EBELN             (PO header -> item)
EKPO.EBELN+EBELP   -> EKBE.EBELN+EBELP      (PO item -> history)
EKPO.EBELN+EBELP   -> ESSR.EBELN+EBELP      (PO item -> entry sheet)
ESSR.PACKNO         -> ESLL.PACKNO           (entry sheet -> lines)
RBKP.BELNR+GJAHR   -> RSEG.BELNR+GJAHR      (invoice header -> item)
cts_objects.TRKORR  -> cts_transports.TRKORR (CTS object -> transport)
TBTCO.JOBNAME+JOBCOUNT -> TBTCP.JOBNAME+JOBCOUNT (job -> steps)
REGUH.ZBUKR+VBLNR  -> BKPF.BUKRS+BELNR      (payment -> FI doc)
T042A.ZBUKR+ZLSCH   -> T042Z.ZBUKR+ZLSCH     (pay method -> DMEE tree)
```

#### Category 4: Integration Edges (from RFCDES, EDIDC, TFDIR_CUSTOM)

| Edge Type | From -> To | Source | Impact Meaning | Est. Count |
|-----------|-----------|--------|----------------|-----------|
| `CALLS_SYSTEM` | RFC_Destination -> SAP_System | rfcdes.RFCSYSID | Changing dest breaks integration | ~239 |
| `EXPOSES_FM` | SAP_System -> Function_Module | TFDIR_CUSTOM (RFC-enabled=334) | External callers break if FM changes | ~334 |
| `SENDS_IDOC` | SAP_System -> IDOC_Type -> External_System | edidc SNDPRT/RCVPRT | IDoc format change breaks receiver | ~50 |
| `CALLS_VIA_RFC` | External_System -> Function_Module | .NET app inventory (334 FMs) | App breaks if FM interface changes | ~239 |
| `SERVES_HTTP` | SAP_System -> ICF_Service | icfservice (active) | Deactivating service breaks consumers | ~100 |

#### Category 5: Process Edges (from process mining event logs)

| Edge Type | From -> To | Source | Purpose | Est. Count |
|-----------|-----------|--------|---------|-----------|
| `PROCESS_CONTAINS` | Process -> Process_Step | Process mining definitions | Process composition | ~100 |
| `STEP_FOLLOWS` | Process_Step -> Process_Step | Event log sequence analysis | Process flow (DFG) | ~200 |
| `STEP_READS` | Process_Step -> SAP_Table | Event-to-table mapping | Which tables matter at each step | ~150 |
| `STEP_USES_TCODE` | Process_Step -> Transaction_Code | BKPF.TCODE from event log | Which transactions drive each step | ~50 |

#### Category 6: Transport Edges (from cts_transports + cts_objects)

| Edge Type | From -> To | Source | Impact Meaning | Est. Count |
|-----------|-----------|--------|----------------|-----------|
| `TRANSPORTS` | Transport -> Code_Object | E071 PGMID+OBJECT+OBJ_NAME | What objects travel together | ~108,290 |
| `MODIFIES_CONFIG` | Transport -> Config_Object | E071 OBJECT=TABU + E071K | Config changes in this transport | ~10,000 |
| `CO_TRANSPORTED_WITH` | Code_Object -> Code_Object | Same transport, different objects | Co-change coupling | ~50,000 |

#### Category 7: Knowledge Edges (existing, enhanced)

| Edge Type | From -> To | Source | Purpose | Est. Count |
|-----------|-----------|--------|---------|-----------|
| `DOCUMENTED_IN` | Any_Node -> Knowledge_Doc | Regex match in .md files | Documentation traceability | ~200 |
| `SKILLED_IN` | Skill -> Any_Node | Skill SKILL.md references | Which skill covers what | ~200 |
| `DISCOVERED_IN` | Any_Node -> Session | Session log references | Provenance tracking | ~500 |

#### Category 8: Organizational Edges (existing, kept)

| Edge Type | From -> To | Source | Purpose | Est. Count |
|-----------|-----------|--------|---------|-----------|
| `BELONGS_TO` | Fund -> Fund_Area | funds.FIKRS | Organizational hierarchy | 64,799 |
| `HAS_FUND_CENTER` | Fund_Area -> Fund_Center | fund_centers.FIKRS | Org hierarchy | ~710 |
| `POSTS_TO_GL` | Fund -> GL_Account | FMIFIIT.HKONT (aggregated) | Spending patterns | ~5,000 |

**Total estimated edges: ~200,000+** (current 65,977 + ~140,000 new behavioral edges)

### A.4 Property Model

Every node carries:
```python
{
    "id":       str,        # Unique identifier (e.g., "CLASS:YCL_IDFI_CGI_DMEE_FR")
    "type":     str,        # From A.2 taxonomy
    "name":     str,        # Human-readable name
    "domain":   str,        # Business domain (FI, PSM, HCM, MM, CTS, BASIS, ...)
    "layer":    str,        # "code" | "config" | "data" | "process" | "integration" | "org"
    "source":   str,        # Where this node came from (extraction pipeline ID)
    "metadata": dict,       # Type-specific properties (see below)
    "tags":     list[str],  # Searchable tags
    "added":    str,        # ISO date when first added
    "updated":  str,        # ISO date of last metadata update
}
```

Type-specific metadata examples:

```python
# ABAP_CLASS
{"package": "YWFI", "super_class": "CL_SOME_BASE", "interfaces": ["IF_EX_FI_CGI_DMEE_EXIT_W"],
 "method_count": 12, "line_count": 850, "tables_read": ["FPAYP", "REGUH", "T042Z"],
 "fms_called": ["RFC_READ_TABLE"], "is_badi_impl": True, "badi_name": "FI_CGI_DMEE_EXIT_W_BADI"}

# DMEE_TREE
{"format_id": "/CGI_XML_CT_UNESCO", "company_codes": ["UNES", "IIEP", "UBO"],
 "payment_methods": ["T", "U", "V"], "exit_class": "YCL_IDFI_CGI_DMEE_FR",
 "output_format": "XML", "bank": "SocGen/CGI"}

# FUNCTION_MODULE
{"fugr": "ZFGR_RFC_FUND", "rfc_enabled": True, "calling_apps": ["SISTER", "HR_Workflow"],
 "parameters_in": ["IV_FUND", "IV_FIKRS"], "parameters_out": ["ET_DATA"],
 "tables_read": ["FMFCT", "FMIFIIT"], "app_domain": "Financial_Reporting"}

# PROCESS_STEP
{"process": "Payment_E2E", "step_order": 5, "activity_name": "BCM Batch Created",
 "avg_duration_hours": 2.3, "tables_involved": ["BNK_BATCH_HEADER", "REGUH"],
 "tcodes": ["BNK_MONI"], "volume_2025": 21800}
```

Every edge carries (Graphiti temporal model + confidence decay):
```python
{
    "from":           str,      # Source node ID
    "to":             str,      # Target node ID
    "type":           str,      # From A.3 taxonomy
    "label":          str,      # Human-readable description
    "weight":         float,    # Strength/importance (1.0 = default)
    "evidence":       str,      # How discovered ("parsed", "config", "mined", "manual", "session_NNN")
    "confidence":     float,    # 0.0-1.0 (parsed=1.0, regex=0.7, manual=0.9) — DECAYS over time
    # Temporal facts (Graphiti pattern)
    "valid_from":     str,      # ISO date — when this edge became true
    "valid_until":    str|None, # ISO date — when superseded (None = still valid)
    "superseded_by":  str|None, # Edge ID that replaced this one (None = current)
    # Provenance
    "discovered_in":  str,      # Session number where first found (e.g., "039")
    "last_validated":str,      # Session number of last revalidation
}
```

### A.5 The Impact Direction Model

Borrowing from Panaya's approach: every edge type has a defined **impact direction** that determines how change propagation works.

```
FORWARD:  Change in source breaks target
          Code CALLS_FM function -> changing FM signature breaks caller
          
BACKWARD: Change in target affects source
          Class IMPLEMENTS_BADI -> changing BAdI definition affects implementor
          
BIDIRECTIONAL: Changes in either direction propagate
          Class INHERITS_FROM superclass -> changes either way cause issues
          
NONE: Informational only, no impact propagation
          DOCUMENTED_IN -> no runtime impact
```

| Edge Type | Impact Direction | Risk Weight |
|-----------|-----------------|-------------|
| `CALLS_FM` | FORWARD | 0.8 |
| `READS_TABLE` | FORWARD | 0.6 |
| `WRITES_TABLE` | FORWARD | 0.9 |
| `READS_FIELD` | FORWARD | 0.7 |
| `IMPLEMENTS_BADI` | BACKWARD | 0.9 |
| `INHERITS_FROM` | BIDIRECTIONAL | 0.8 |
| `USES_DMEE_TREE` | FORWARD | 0.95 |
| `ROUTES_TO_BANK` | FORWARD | 0.95 |
| `CONFIGURES_FORMAT` | FORWARD | 0.9 |
| `EXPOSES_FM` | BACKWARD | 0.85 |
| `CALLS_VIA_RFC` | FORWARD | 0.85 |
| `TRANSPORTS` | FORWARD | 0.7 |
| `DOCUMENTED_IN` | NONE | 0.0 |

---

## B. Data Ingestion Pipeline

### B.1 Source 1: Code Objects -> Graph (ABAP Parser)

**Input:** 896 .abap files in `extracted_code/` + files in `extracted_sap/`

**Parser strategy:** Regex-based static analysis of ABAP source. Not a full compiler -- we extract the 5 patterns that account for 90% of dependencies.

```python
# brain_v2/parsers/abap_parser.py

import re
from pathlib import Path

class ABAPDependencyParser:
    """Extract dependencies from ABAP source code files."""
    
    # Pattern 1: SELECT statements -> READS_TABLE + READS_FIELD
    RE_SELECT = re.compile(
        r'SELECT\s+(SINGLE\s+)?'
        r'(?P<fields>[\w\s,*~]+?)\s+'
        r'FROM\s+(?P<table>\w+)',
        re.IGNORECASE | re.DOTALL
    )
    
    # Pattern 2: CALL FUNCTION -> CALLS_FM
    RE_CALL_FM = re.compile(
        r"CALL\s+FUNCTION\s+'(?P<fm_name>[A-Z0-9_/]+)'",
        re.IGNORECASE
    )
    
    # Pattern 3: INSERT/MODIFY/UPDATE/DELETE -> WRITES_TABLE
    RE_WRITE = re.compile(
        r'(?:INSERT|MODIFY|UPDATE|DELETE)\s+(?:FROM\s+)?(?P<table>[A-Z]\w{2,30})\b',
        re.IGNORECASE
    )
    
    # Pattern 4: CLASS ... INHERITING FROM -> INHERITS_FROM
    RE_INHERITS = re.compile(
        r'CLASS\s+\w+\s+DEFINITION.*?INHERITING\s+FROM\s+(?P<super>\w+)',
        re.IGNORECASE | re.DOTALL
    )
    
    # Pattern 5: INTERFACES -> IMPLEMENTS_INTF
    RE_INTERFACE = re.compile(
        r'INTERFACES\s+(?P<intf>[A-Z]\w+)',
        re.IGNORECASE
    )
    
    # Pattern 6: Known BAdI implementation classes (naming convention)
    RE_BADI_IMPL = re.compile(
        r'CLASS\s+(?P<cls>[YZ]CL_IM_\w+)\s+DEFINITION',
        re.IGNORECASE
    )
    
    def parse_file(self, filepath: Path) -> dict:
        """Parse a single ABAP file and return all dependencies."""
        source = filepath.read_text(encoding='utf-8', errors='replace')
        
        return {
            'tables_read':  self._extract_tables_read(source),
            'fields_read':  self._extract_fields_read(source),
            'fms_called':   [m.group('fm_name') for m in self.RE_CALL_FM.finditer(source)],
            'tables_written': [m.group('table') for m in self.RE_WRITE.finditer(source)
                              if m.group('table').upper() not in ABAP_KEYWORDS],
            'inherits':     [m.group('super') for m in self.RE_INHERITS.finditer(source)],
            'interfaces':   [m.group('intf') for m in self.RE_INTERFACE.finditer(source)],
            'is_badi_impl': bool(self.RE_BADI_IMPL.search(source)),
        }
    
    def parse_class_directory(self, class_dir: Path) -> dict:
        """Parse all methods of an ABAP class."""
        all_deps = {
            'tables_read': set(), 'fields_read': set(), 'fms_called': set(),
            'tables_written': set(), 'inherits': set(), 'interfaces': set(),
            'is_badi_impl': False, 'methods': {},
        }
        
        for abap_file in sorted(class_dir.glob('*.abap')):
            method_name = abap_file.stem
            deps = self.parse_file(abap_file)
            all_deps['methods'][method_name] = deps
            
            for key in ['tables_read', 'fms_called', 'tables_written',
                        'inherits', 'interfaces']:
                all_deps[key].update(deps[key])
            for table, fields in deps['fields_read']:
                all_deps['fields_read'].add((table, tuple(fields)))
            if deps['is_badi_impl']:
                all_deps['is_badi_impl'] = True
        
        # Convert sets to sorted lists for JSON serialization
        for key in ['tables_read', 'fms_called', 'tables_written',
                    'inherits', 'interfaces']:
            all_deps[key] = sorted(all_deps[key])
        all_deps['fields_read'] = sorted(all_deps['fields_read'])
        
        return all_deps

ABAP_KEYWORDS = {
    'INTO', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'TABLE', 'APPENDING',
    'CORRESPONDING', 'FIELDS', 'OF', 'UP', 'TO', 'ROWS', 'ORDER', 'BY',
    'GROUP', 'HAVING', 'FOR', 'ALL', 'ENTRIES', 'IN', 'INNER', 'LEFT',
    'RIGHT', 'OUTER', 'JOIN', 'ON', 'AS', 'SINGLE', 'DISTINCT',
}
```

**Concrete output for DMEE example:**
```
Parsing: extracted_code/DMEE/YCL_IDFI_CGI_DMEE_FR_CCIMP.abap
  -> READS_TABLE: FPAYP, REGUH, T042Z, T012, T012K, PAYR
  -> READS_FIELD: FPAYP.XREF3, REGUH.VBLNR, REGUH.LIFNR, T042Z.DTFOR
  -> CALLS_FM: FI_CGI_DMEE_GET_PAYEE_DATA, CONVERSION_EXIT_ALPHA_OUTPUT
  -> IMPLEMENTS_BADI: True (FI_CGI_DMEE_EXIT_W_BADI implied by naming)

Resulting edges:
  YCL_IDFI_CGI_DMEE_FR --READS_TABLE--> FPAYP
  YCL_IDFI_CGI_DMEE_FR --READS_TABLE--> REGUH
  YCL_IDFI_CGI_DMEE_FR --READS_FIELD--> FPAYP.XREF3
  YCL_IDFI_CGI_DMEE_FR --CALLS_FM--> FI_CGI_DMEE_GET_PAYEE_DATA
  YCL_IDFI_CGI_DMEE_FR --IMPLEMENTS_BADI--> FI_CGI_DMEE_EXIT_W_BADI
```

**Files to parse (by priority):**

| Directory | Files | Priority | Domain |
|-----------|-------|----------|--------|
| `extracted_code/DMEE/` | 25 | P1 | FI/Payment |
| `extracted_code/YWFI/` | ~20 | P1 | FI/Workflow |
| `extracted_code/UNESCO_CUSTOM_LOGIC/` | ~100+ | P1 | Cross-domain |
| `extracted_code/ZCL_*/` (30 dirs) | ~500 | P2 | HCM/PSM |
| `extracted_code/CL_HCMFAB_*/` | ~200 | P3 | HCM |

### B.2 Source 2: Configuration -> Graph

**Input:** Gold DB config tables already extracted.

```python
# brain_v2/ingestors/config_ingestor.py

def ingest_payment_config(brain, db_path):
    """Build config graph from payment tables."""
    conn = sqlite3.connect(db_path)
    
    # ── T042Z: DMEE Tree Assignments ──
    # Each row: company code + payment method -> DMEE format tree
    rows = conn.execute("""
        SELECT ZBUKR, ZLSCH, DTFOR, DMESSION, DMESSION2
        FROM T042Z WHERE DTFOR IS NOT NULL AND DTFOR != ''
    """).fetchall()
    
    for zbukr, zlsch, dtfor, sess1, sess2 in rows:
        # DMEE tree node
        tree_id = f"DMEE:{dtfor}"
        brain.add_node(tree_id, "DMEE_TREE", dtfor,
                       domain="FI", layer="config",
                       metadata={"format": dtfor})
        
        # Payment method node (per company code)
        pm_id = f"PAYMETHOD:{zbukr}:{zlsch}"
        brain.add_node(pm_id, "PAYMENT_METHOD", f"{zbukr}-{zlsch}",
                       domain="FI", layer="config",
                       metadata={"bukrs": zbukr, "zlsch": zlsch})
        
        # Edge: payment method USES this DMEE tree
        brain.add_edge(pm_id, tree_id, "USES_DMEE_TREE",
                       label=f"{zbukr}/{zlsch} -> {dtfor}",
                       evidence="config", confidence=1.0)
    
    # ── T042A: Payment Method -> House Bank Routing ──
    rows = conn.execute("""
        SELECT ZBUKR, ZLSCH, HBKID, HKTID, RWBTR, XKURA
        FROM T042A
    """).fetchall()
    
    for zbukr, zlsch, hbkid, hktid, rwbtr, xkura in rows:
        pm_id = f"PAYMETHOD:{zbukr}:{zlsch}"
        bank_id = f"HOUSEBANK:{zbukr}:{hbkid}"
        
        brain.add_node(bank_id, "HOUSE_BANK", f"{zbukr}/{hbkid}",
                       domain="FI", layer="config",
                       metadata={"bukrs": zbukr, "hbkid": hbkid, "hktid": hktid or ""})
        
        brain.add_edge(pm_id, bank_id, "ROUTES_TO_BANK",
                       label=f"{zlsch} -> {hbkid}/{hktid}",
                       evidence="config", confidence=1.0)
    
    # ── DMEE Tree -> BAdI Exit Class ──
    # This is the critical link: which ABAP class processes each DMEE tree
    # Known mappings from extracted code analysis:
    DMEE_EXIT_MAP = {
        "/CGI_XML_CT_UNESCO":    "YCL_IDFI_CGI_DMEE_FR",
        "/CGI_XML_CT_UNESCO_FB": "YCL_IDFI_CGI_DMEE_FALLBACK",
        # UTIL variant for non-CGI countries:
        "*":                     "YCL_IDFI_CGI_DMEE_UTIL",
    }
    
    for dtfor, cls_name in DMEE_EXIT_MAP.items():
        tree_id = f"DMEE:{dtfor}"
        cls_id = f"CLASS:{cls_name}"
        if tree_id in brain.nodes:
            brain.add_edge(tree_id, cls_id, "CONFIGURES_FORMAT",
                           label=f"DMEE {dtfor} processed by {cls_name}",
                           evidence="manual", confidence=0.9)
    
    # ── BCM Rules from BNK_BATCH_HEADER ──
    rows = conn.execute("""
        SELECT GROUPING_RULE, COUNT(*) as cnt
        FROM BNK_BATCH_HEADER
        WHERE GROUPING_RULE IS NOT NULL AND GROUPING_RULE != ''
        GROUP BY GROUPING_RULE
    """).fetchall()
    
    for rule, cnt in rows:
        rule_id = f"BCM:{rule}"
        brain.add_node(rule_id, "BCM_RULE", rule,
                       domain="FI", layer="config",
                       metadata={"batch_count": cnt})
    
    conn.close()


def ingest_transport_objects(brain, db_path):
    """Link transports to the objects they carry."""
    conn = sqlite3.connect(db_path)
    
    rows = conn.execute("""
        SELECT TRKORR, PGMID, OBJECT, OBJ_NAME, OBJFUNC
        FROM cts_objects
        WHERE OBJ_NAME IS NOT NULL AND OBJ_NAME != ''
    """).fetchall()
    
    object_type_map = {
        'PROG': 'ABAP_REPORT', 'CLAS': 'ABAP_CLASS', 'FUGR': 'FUNCTION_MODULE',
        'TABL': 'SAP_TABLE', 'TABU': 'SAP_TABLE', 'TRAN': 'TRANSACTION',
        'DEVC': 'PACKAGE', 'DTEL': 'DATA_ELEMENT', 'DOMA': 'DOMAIN_OBJECT',
        'ENHO': 'ENHANCEMENT', 'NROB': 'NUMBER_RANGE', 'SICF': 'ICF_SERVICE',
    }
    
    for trkorr, pgmid, obj_type, obj_name, objfunc in rows:
        tr_id = f"TR_{trkorr}"
        
        # Map CTS object type to our graph node type
        node_type = object_type_map.get(obj_type, 'CODE_OBJECT')
        obj_id = f"{node_type}:{obj_name}" if node_type != 'CODE_OBJECT' else f"OBJ:{obj_type}:{obj_name}"
        
        # Ensure object node exists
        if obj_id not in brain.nodes:
            brain.add_node(obj_id, node_type, obj_name,
                           domain="CTS", layer="code",
                           metadata={"pgmid": pgmid, "object_type": obj_type})
        
        # Edge: transport carries this object
        brain.add_edge(tr_id, obj_id, "TRANSPORTS",
                       label=f"{objfunc or 'overwrite'}: {pgmid}/{obj_type}/{obj_name}",
                       evidence="config", confidence=1.0,
                       weight=1.2 if objfunc == 'D' else 1.0)  # Delete = higher risk
    
    conn.close()


def ingest_job_intelligence(brain, db_path):
    """Link background jobs to the programs they execute and tables they touch."""
    conn = sqlite3.connect(db_path)
    
    # Job programs with classification
    rows = conn.execute("""
        SELECT DISTINCT t.PROGNAME, COUNT(DISTINCT c.JOBNAME) as job_count,
               COUNT(*) as exec_count
        FROM tbtcp t
        JOIN tbtco c ON t.JOBNAME = c.JOBNAME AND t.JOBCOUNT = c.JOBCOUNT
        WHERE t.PROGNAME IS NOT NULL AND t.PROGNAME != ''
        GROUP BY t.PROGNAME
        ORDER BY exec_count DESC
    """).fetchall()
    
    for progname, job_count, exec_count in rows:
        prog_id = f"JOB_PROG:{progname}"
        brain.add_node(prog_id, "JOB_DEFINITION", progname,
                       domain="BASIS", layer="process",
                       metadata={"job_count": job_count, "exec_count": exec_count})
        
        # Link to known ABAP reports if they exist in extracted code
        report_id = f"ABAP_REPORT:{progname}"
        if report_id in brain.nodes:
            brain.add_edge(prog_id, report_id, "RUNS_PROGRAM",
                           evidence="config", confidence=1.0)
    
    conn.close()
```

### B.3 Source 3: Process Mining -> Graph

**Input:** Existing process mining scripts + event logs.

The key insight from Celonis's OCEL 2.0 model: process events are not just sequences -- they touch objects. Each event in a P2P process reads/writes specific SAP tables. We overlay this on the graph.

```python
# brain_v2/ingestors/process_ingestor.py

# UNESCO's proven processes with their table footprints
PROCESS_DEFINITIONS = {
    "P2P": {
        "name": "Procure to Pay",
        "steps": [
            {"name": "PR Created",       "tables": ["EBAN"],                    "tcodes": ["ME51N"]},
            {"name": "PR Released",       "tables": ["EBAN"],                    "tcodes": ["ME54N"]},
            {"name": "PO Created",        "tables": ["EKKO", "EKPO"],           "tcodes": ["ME21N"]},
            {"name": "PO Released",       "tables": ["EKKO"],                    "tcodes": ["ME29N"]},
            {"name": "GR Posted",         "tables": ["EKBE", "BKPF"],           "tcodes": ["MIGO"]},
            {"name": "SES Created",       "tables": ["ESSR", "ESLL"],           "tcodes": ["ML81N"]},
            {"name": "SES Released",      "tables": ["ESSR"],                    "tcodes": ["ML81N"]},
            {"name": "Invoice Posted",    "tables": ["RBKP", "RSEG", "BKPF"],  "tcodes": ["MIRO"]},
            {"name": "Invoice Verified",  "tables": ["RBKP"],                    "tcodes": ["MRBR"]},
            {"name": "Payment Run",       "tables": ["REGUH", "T042A"],         "tcodes": ["F110"]},
        ],
        "volume": {"events": 848000, "source": "p2p_process_mining.py"},
    },
    "Payment_E2E": {
        "name": "Payment End-to-End",
        "steps": [
            {"name": "Invoice Received",  "tables": ["RBKP", "BKPF"],          "tcodes": ["MIRO", "FB60"]},
            {"name": "Payment Proposal",  "tables": ["REGUH"],                   "tcodes": ["F110"]},
            {"name": "Payment Execution", "tables": ["REGUH", "BKPF", "PAYR"], "tcodes": ["F110"]},
            {"name": "BCM Batch Created", "tables": ["BNK_BATCH_HEADER"],       "tcodes": ["BNK_MONI"]},
            {"name": "BCM Approved",      "tables": ["BNK_BATCH_HEADER"],       "tcodes": ["BNK_MONI"]},
            {"name": "Bank File Sent",    "tables": ["BNK_BATCH_ITEM"],         "tcodes": ["BNK_MONI"]},
            {"name": "Bank Confirmed",    "tables": ["FEBEP"],                   "tcodes": ["FF_5"]},
        ],
        "volume": {"events": 1400000, "cases": 550000, "source": "payment_event_log.csv"},
    },
    "Bank_Statement": {
        "name": "Bank Statement Processing",
        "steps": [
            {"name": "Statement Imported", "tables": ["FEBKO"],                  "tcodes": ["FF_5"]},
            {"name": "Items Posted",       "tables": ["FEBEP", "BKPF"],         "tcodes": ["FEBAN"]},
            {"name": "Items Cleared",      "tables": ["FEBEP"],                  "tcodes": ["FEBAN"]},
            {"name": "Reconciled",         "tables": ["FEBRE"],                  "tcodes": ["FEBAN"]},
        ],
        "volume": {"events": 263000, "source": "bank_statement_ebs_companion.html"},
    },
}


def ingest_processes(brain):
    """Create process and step nodes with table/tcode linkages."""
    for proc_id, proc_def in PROCESS_DEFINITIONS.items():
        # Process node
        p_node_id = f"PROCESS:{proc_id}"
        brain.add_node(p_node_id, "PROCESS", proc_def["name"],
                       domain="FI" if "Payment" in proc_id or "Bank" in proc_id else "MM",
                       layer="process",
                       metadata=proc_def.get("volume", {}))
        
        prev_step_id = None
        for i, step in enumerate(proc_def["steps"]):
            step_id = f"STEP:{proc_id}:{step['name'].replace(' ', '_')}"
            brain.add_node(step_id, "PROCESS_STEP", step["name"],
                           domain="FI" if "Payment" in proc_id else "MM",
                           layer="process",
                           metadata={"order": i, "tcodes": step["tcodes"]})
            
            # Process contains step
            brain.add_edge(p_node_id, step_id, "PROCESS_CONTAINS",
                           evidence="mined", confidence=0.95)
            
            # Step sequence
            if prev_step_id:
                brain.add_edge(prev_step_id, step_id, "STEP_FOLLOWS",
                               evidence="mined", confidence=0.9)
            prev_step_id = step_id
            
            # Step -> tables
            for table in step["tables"]:
                tbl_id = f"SAP_TABLE:{table}"
                if tbl_id not in brain.nodes:
                    brain.add_node(tbl_id, "SAP_TABLE", table,
                                   domain="DATA_MODEL", layer="data")
                brain.add_edge(step_id, tbl_id, "STEP_READS",
                               evidence="mined", confidence=0.85)
```

### B.4 Source 4: Integration Map -> Graph

**Input:** RFCDES (239 rows), EDIDC (19K rows), TFDIR_CUSTOM (3,073 rows), ICFSERVICE (6,477 rows)

```python
# brain_v2/ingestors/integration_ingestor.py

# Known .NET application -> FM mappings (from Session #032 discovery)
DOTNET_APP_FM_MAP = {
    "SISTER":       {"fm_count": 47, "domain": "Financial_Reporting", "fms_known": [
                        "Z_RFC_READ_FUND_DATA", "Z_RFC_BUDGET_TRANSFER"]},
    "HR_Workflow":   {"fm_count": 87, "domain": "HCM", "fms_known": [
                        "Z_HR_GET_EMPLOYEE", "Z_HR_CREATE_INFOTYPE"]},
    "CMT":           {"fm_count": 44, "domain": "MM", "fms_known": [
                        "Z_RFC_VENDOR_CREATE", "Z_RFC_VENDOR_CHANGE"]},
    "UBO_Field":     {"fm_count": 15, "domain": "FI", "fms_known": [
                        "Z_RFC_FI_POST", "Z_RFC_FM_COMMITMENT"]},
    "Travel":        {"fm_count": 21, "domain": "Travel", "fms_known": [
                        "Z_RFC_TRIP_CREATE", "Z_RFC_DSA_RATES"]},
    "Mouv":          {"fm_count": 12, "domain": "AM", "fms_known": [
                        "Z_RFC_ASSET_TRANSFER"]},
    "Procurement":   {"fm_count": 13, "domain": "MM", "fms_known": [
                        "Z_RFC_PO_RELEASE", "Z_RFC_GR_POST"]},
}


def ingest_integration(brain, db_path):
    """Build integration edges from RFC destinations, IDocs, and .NET apps."""
    conn = sqlite3.connect(db_path)
    
    # ── RFC Destinations -> SAP Systems ──
    rows = conn.execute("""
        SELECT RFCDEST, RFCTYPE, RFCHOST, RFCSYSID, RFCCLIENT, RFCSNC
        FROM rfcdes
        WHERE RFCDEST IS NOT NULL
    """).fetchall()
    
    systems = set()
    for dest, rfctype, host, sysid, client, snc in rows:
        dest_id = f"RFC:{dest}"
        brain.add_node(dest_id, "RFC_DESTINATION", dest,
                       domain="BASIS", layer="integration",
                       metadata={"type": rfctype or "", "host": host or "",
                                "sysid": sysid or "", "client": client or "",
                                "snc": snc or ""})
        
        if sysid and sysid.strip():
            sys_id = f"SYSTEM:{sysid.strip()}"
            if sys_id not in brain.nodes:
                brain.add_node(sys_id, "SAP_SYSTEM", sysid.strip(),
                               domain="BASIS", layer="integration")
                systems.add(sysid.strip())
            brain.add_edge(dest_id, sys_id, "CALLS_SYSTEM",
                           evidence="config", confidence=1.0)
    
    # ── .NET Applications -> FMs ──
    for app_name, app_info in DOTNET_APP_FM_MAP.items():
        app_id = f"EXTERNAL:{app_name}"
        brain.add_node(app_id, "EXTERNAL_SYSTEM", app_name,
                       domain=app_info["domain"], layer="integration",
                       metadata={"fm_count": app_info["fm_count"],
                                "protocol": ".NET RFC"})
        
        for fm_name in app_info.get("fms_known", []):
            fm_id = f"FM:{fm_name}"
            if fm_id not in brain.nodes:
                brain.add_node(fm_id, "FUNCTION_MODULE", fm_name,
                               domain=app_info["domain"], layer="code",
                               metadata={"rfc_enabled": True})
            brain.add_edge(app_id, fm_id, "CALLS_VIA_RFC",
                           evidence="manual", confidence=0.8)
    
    # ── RFC-Enabled FMs from TFDIR_CUSTOM ──
    try:
        rows = conn.execute("""
            SELECT FUNCNAME, PNAME
            FROM tfdir_custom
            WHERE FUNCNAME LIKE 'Z%' OR FUNCNAME LIKE 'Y%'
        """).fetchall()
        
        for funcname, pname in rows:
            fm_id = f"FM:{funcname}"
            if fm_id not in brain.nodes:
                brain.add_node(fm_id, "FUNCTION_MODULE", funcname,
                               domain="CUSTOM", layer="code",
                               metadata={"fugr": pname or ""})
            # Mark as externally callable
            brain.nodes[fm_id]["metadata"]["rfc_enabled"] = True
    except Exception:
        pass
    
    conn.close()
```

### B.5 Incremental Update Protocol

Critical: the brain must support incremental updates, not full rebuilds.

```python
# brain_v2/core/incremental.py

class IncrementalBrain:
    """Wraps SAPBrain with change tracking for incremental updates."""
    
    def __init__(self, brain):
        self.brain = brain
        self.changelog = []  # [{action, entity_type, entity_id, timestamp}]
    
    def update_from_source(self, source_name, ingest_fn, *args):
        """Run an ingest function and track what changed."""
        before_nodes = set(self.brain.nodes.keys())
        before_edges = len(self.brain.edges)
        
        ingest_fn(self.brain, *args)
        
        after_nodes = set(self.brain.nodes.keys())
        new_nodes = after_nodes - before_nodes
        new_edges = len(self.brain.edges) - before_edges
        
        entry = {
            "source": source_name,
            "timestamp": datetime.now().isoformat(),
            "new_nodes": len(new_nodes),
            "new_edges": new_edges,
            "sample_nodes": sorted(new_nodes)[:10],
        }
        self.changelog.append(entry)
        return entry
    
    def diff_since(self, since_date: str) -> dict:
        """Return all changes since a given date."""
        return [e for e in self.changelog if e["timestamp"] >= since_date]
```

**Update triggers:**
1. New ABAP code extracted -> re-run parser on new files only
2. New table extracted to Gold DB -> add table/field nodes + join edges
3. New transport imported -> add transport + object edges
4. Config table updated -> re-ingest that config source only
5. Session close -> save brain + changelog

---

## C. Query Engine

### C.1 Impact Analysis: "What breaks if I change X?"

This is the core value proposition. It implements a forward/backward graph traversal with risk accumulation, similar to Panaya's approach.

```python
# brain_v2/queries/impact.py

from collections import deque

IMPACT_DIRECTION = {
    "CALLS_FM":           "forward",
    "READS_TABLE":        "forward",
    "WRITES_TABLE":       "forward",
    "READS_FIELD":        "forward",
    "IMPLEMENTS_BADI":    "backward",
    "INHERITS_FROM":      "bidirectional",
    "IMPLEMENTS_INTF":    "backward",
    "USES_DMEE_TREE":     "forward",
    "ROUTES_TO_BANK":     "forward",
    "CONFIGURES_FORMAT":  "forward",
    "VALIDATES_FIELD":    "forward",
    "SUBSTITUTES_FIELD":  "forward",
    "EXPOSES_FM":         "backward",
    "CALLS_VIA_RFC":      "forward",
    "TRANSPORTS":         "forward",
    "STEP_READS":         "forward",
    "STEP_FOLLOWS":       "forward",
    "RUNS_PROGRAM":       "forward",
}

RISK_WEIGHTS = {
    "WRITES_TABLE":      0.95,  # Highest: data corruption risk
    "USES_DMEE_TREE":    0.95,  # Bank file format change
    "ROUTES_TO_BANK":    0.95,  # Payment routing change
    "IMPLEMENTS_BADI":   0.9,
    "CONFIGURES_FORMAT": 0.9,
    "CALLS_FM":          0.8,
    "EXPOSES_FM":        0.85,
    "CALLS_VIA_RFC":     0.85,
    "INHERITS_FROM":     0.8,
    "READS_FIELD":       0.7,
    "READS_TABLE":       0.6,
    "TRANSPORTS":        0.7,
    "VALIDATES_FIELD":   0.75,
    "SUBSTITUTES_FIELD": 0.75,
}


def impact_analysis(brain, start_node_id, max_depth=4, min_risk=0.1):
    """
    Traverse the graph from a starting node, following impact-propagating edges.
    Returns all affected nodes with cumulative risk scores.
    
    Uses BFS with risk decay: each hop multiplies the risk by the edge weight.
    At depth 4, a 0.8-weight chain gives 0.8^4 = 0.41 risk -- still significant.
    """
    
    # Build adjacency lists for fast traversal
    outgoing = {}  # node_id -> [(target, edge_type, weight)]
    incoming = {}  # node_id -> [(source, edge_type, weight)]
    
    for edge in brain.edges:
        etype = edge["type"]
        direction = IMPACT_DIRECTION.get(etype)
        if not direction:
            continue
        
        weight = RISK_WEIGHTS.get(etype, 0.5)
        
        if direction in ("forward", "bidirectional"):
            outgoing.setdefault(edge["from"], []).append(
                (edge["to"], etype, weight))
        if direction in ("backward", "bidirectional"):
            incoming.setdefault(edge["to"], []).append(
                (edge["from"], etype, weight))
    
    # BFS with risk accumulation
    affected = {}  # node_id -> {risk, depth, path}
    queue = deque([(start_node_id, 1.0, 0, [start_node_id])])
    visited = {start_node_id}
    
    while queue:
        node_id, cumulative_risk, depth, path = queue.popleft()
        
        if depth >= max_depth:
            continue
        
        # Follow outgoing edges (forward impact)
        for target, etype, weight in outgoing.get(node_id, []):
            new_risk = cumulative_risk * weight
            if new_risk < min_risk:
                continue
            if target not in visited or (target in affected and new_risk > affected[target]["risk"]):
                visited.add(target)
                affected[target] = {
                    "node": brain.nodes.get(target, {}),
                    "risk": round(new_risk, 3),
                    "depth": depth + 1,
                    "path": path + [target],
                    "edge_type": etype,
                }
                queue.append((target, new_risk, depth + 1, path + [target]))
        
        # Follow incoming edges (backward impact)
        for source, etype, weight in incoming.get(node_id, []):
            new_risk = cumulative_risk * weight
            if new_risk < min_risk:
                continue
            if source not in visited or (source in affected and new_risk > affected[source]["risk"]):
                visited.add(source)
                affected[source] = {
                    "node": brain.nodes.get(source, {}),
                    "risk": round(new_risk, 3),
                    "depth": depth + 1,
                    "path": path + [source],
                    "edge_type": etype,
                }
                queue.append((source, new_risk, depth + 1, path + [source]))
    
    # Sort by risk descending
    results = sorted(affected.values(), key=lambda x: -x["risk"])
    
    return {
        "start_node": start_node_id,
        "total_affected": len(results),
        "max_risk": results[0]["risk"] if results else 0,
        "affected": results,
        "summary": _summarize_impact(results, brain),
    }


def _summarize_impact(results, brain):
    """Generate human-readable impact summary."""
    by_type = {}
    by_domain = {}
    critical = []
    
    for r in results:
        node = r["node"]
        ntype = node.get("type", "unknown")
        domain = node.get("domain", "unknown")
        
        by_type[ntype] = by_type.get(ntype, 0) + 1
        by_domain[domain] = by_domain.get(domain, 0) + 1
        
        if r["risk"] >= 0.7:
            critical.append(f"  [{r['risk']:.0%}] {node.get('name', '?')} ({ntype})")
    
    lines = [f"Impact radius: {len(results)} objects affected"]
    lines.append(f"By type: {dict(sorted(by_type.items(), key=lambda x: -x[1]))}")
    lines.append(f"By domain: {dict(sorted(by_domain.items(), key=lambda x: -x[1]))}")
    if critical:
        lines.append(f"CRITICAL (>=70% risk):")
        lines.extend(critical[:20])
    
    return "\n".join(lines)
```

**Example query: "What does changing FPAYP.XREF3 affect?"**

```
> brain.impact_analysis("TABLE_FIELD:FPAYP.XREF3")

Impact radius: 14 objects affected
By type: {'ABAP_CLASS': 3, 'DMEE_TREE': 2, 'PAYMENT_METHOD': 6, 'HOUSE_BANK': 2, 'EXTERNAL_SYSTEM': 1}
By domain: {'FI': 12, 'BASIS': 2}
CRITICAL (>=70% risk):
  [90%] YCL_IDFI_CGI_DMEE_FR (ABAP_CLASS)        -- READS_FIELD
  [86%] /CGI_XML_CT_UNESCO (DMEE_TREE)             -- CONFIGURES_FORMAT -> class
  [81%] UNES-T (PAYMENT_METHOD)                     -- USES_DMEE_TREE -> tree
  [77%] SOG01 (HOUSE_BANK)                          -- ROUTES_TO_BANK
  [73%] SocGen/CGI (EXTERNAL_SYSTEM)               -- bank receives changed XML
```

### C.2 Dependency Tracing: "What does process Y depend on?"

```python
# brain_v2/queries/dependency.py

def dependency_tree(brain, node_id, max_depth=5):
    """
    Build a complete dependency tree for a node.
    Unlike impact analysis (forward), this traces BACKWARD:
    "What does this node need to function?"
    """
    dependencies = {}
    queue = deque([(node_id, 0)])
    visited = {node_id}
    
    # Build reverse adjacency (what does X depend on?)
    depends_on = {}
    for edge in brain.edges:
        etype = edge["type"]
        # Dependency direction is opposite of impact direction
        if etype in ("READS_TABLE", "READS_FIELD", "CALLS_FM", "USES_DMEE_TREE",
                     "ROUTES_TO_BANK", "STEP_READS", "CALLS_VIA_RFC", "RUNS_PROGRAM"):
            depends_on.setdefault(edge["from"], []).append(
                (edge["to"], etype))
        elif etype in ("IMPLEMENTS_BADI", "INHERITS_FROM", "CONFIGURES_FORMAT"):
            depends_on.setdefault(edge["to"], []).append(
                (edge["from"], etype))
    
    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue
        
        for dep_id, edge_type in depends_on.get(current, []):
            if dep_id not in visited:
                visited.add(dep_id)
                dependencies[dep_id] = {
                    "node": brain.nodes.get(dep_id, {}),
                    "depth": depth + 1,
                    "via": edge_type,
                    "depended_by": current,
                }
                queue.append((dep_id, depth + 1))
    
    return {
        "root": node_id,
        "total_dependencies": len(dependencies),
        "dependencies": sorted(dependencies.values(), key=lambda x: x["depth"]),
    }
```

**Example: "What does the Payment_E2E process depend on?"**

```
> brain.dependency_tree("PROCESS:Payment_E2E")

Total dependencies: 47
Depth 1 (process steps): Invoice Received, Payment Proposal, Payment Execution, 
                          BCM Batch Created, BCM Approved, Bank File Sent, Bank Confirmed
Depth 2 (tables):        RBKP, BKPF, REGUH, BNK_BATCH_HEADER, BNK_BATCH_ITEM, 
                          FEBEP, PAYR, T042A
Depth 3 (config):        DMEE:/CGI_XML_CT_UNESCO, BCM:PAYROLL, BCM:UNES_AP_ST,
                          HOUSEBANK:UNES:SOG01, PAYMETHOD:UNES:T
Depth 4 (code):          YCL_IDFI_CGI_DMEE_FR, YCL_IDFI_CGI_DMEE_UTIL,
                          FI_CGI_DMEE_EXIT_W_BADI
Depth 5 (fields):        FPAYP.XREF3, REGUH.VBLNR, REGUH.LIFNR, T042Z.DTFOR
```

### C.3 Similarity Search: "What's similar to X?"

This uses lightweight structural similarity (graph-based) for nodes that share many neighbors, plus optional vector embeddings for semantic similarity of code.

```python
# brain_v2/queries/similarity.py

def structural_similarity(brain, node_id, top_n=10):
    """
    Find nodes that share the most neighbors (Jaccard similarity).
    Works without embeddings -- pure graph structure.
    """
    # Get neighbors of target node
    target_neighbors = set()
    for edge in brain.edges:
        if edge["from"] == node_id:
            target_neighbors.add(edge["to"])
        elif edge["to"] == node_id:
            target_neighbors.add(edge["from"])
    
    if not target_neighbors:
        return []
    
    # Compare with all other nodes of same type
    target_type = brain.nodes.get(node_id, {}).get("type")
    scores = []
    
    for nid, node in brain.nodes.items():
        if nid == node_id or node.get("type") != target_type:
            continue
        
        node_neighbors = set()
        for edge in brain.edges:
            if edge["from"] == nid:
                node_neighbors.add(edge["to"])
            elif edge["to"] == nid:
                node_neighbors.add(edge["from"])
        
        if not node_neighbors:
            continue
        
        # Jaccard similarity
        intersection = len(target_neighbors & node_neighbors)
        union = len(target_neighbors | node_neighbors)
        score = intersection / union if union > 0 else 0
        
        if score > 0:
            scores.append({
                "node_id": nid,
                "name": node.get("name", ""),
                "similarity": round(score, 3),
                "shared_neighbors": sorted(target_neighbors & node_neighbors)[:5],
            })
    
    return sorted(scores, key=lambda x: -x["similarity"])[:top_n]
```

### C.4 Gap Analysis: "What's configured but never used?"

```python
# brain_v2/queries/gap.py

def find_gaps(brain):
    """
    Identify configuration objects with no runtime consumers,
    and code objects with no configuration linkage.
    """
    gaps = {"configured_but_unused": [], "used_but_undocumented": [],
            "orphan_integrations": [], "dead_code": []}
    
    # Nodes with outgoing edges
    has_consumers = set()
    for edge in brain.edges:
        has_consumers.add(edge["to"])
    
    # Config objects nobody reads
    for nid, node in brain.nodes.items():
        if node["type"] in ("DMEE_TREE", "BCM_RULE", "PAYMENT_METHOD",
                            "VALIDATION_RULE", "SUBSTITUTION_RULE"):
            if nid not in has_consumers:
                gaps["configured_but_unused"].append({
                    "node": nid,
                    "type": node["type"],
                    "name": node["name"],
                    "concern": "Config exists but no code/process references it",
                })
    
    # Code objects with no DOCUMENTED_IN edge
    for nid, node in brain.nodes.items():
        if node["type"] in ("ABAP_CLASS", "FUNCTION_MODULE", "ABAP_REPORT"):
            documented = any(
                e["from"] == nid and e["type"] == "DOCUMENTED_IN"
                for e in brain.edges
            ) or any(
                e["to"] == nid and e["type"] == "DOCUMENTED_IN"
                for e in brain.edges
            )
            if not documented:
                gaps["used_but_undocumented"].append({
                    "node": nid,
                    "type": node["type"],
                    "name": node["name"],
                })
    
    # RFC destinations that nothing calls
    for nid, node in brain.nodes.items():
        if node["type"] == "RFC_DESTINATION":
            used = any(e["from"] == nid or e["to"] == nid
                      for e in brain.edges
                      if e["type"] != "CALLS_SYSTEM")
            if not used:
                gaps["orphan_integrations"].append({
                    "node": nid,
                    "name": node["name"],
                    "concern": "RFC destination exists but no code/process uses it",
                })
    
    # Function modules not called by anything
    for nid, node in brain.nodes.items():
        if node["type"] == "FUNCTION_MODULE":
            called = any(e["to"] == nid and e["type"] in ("CALLS_FM", "CALLS_VIA_RFC")
                        for e in brain.edges)
            if not called and node.get("metadata", {}).get("rfc_enabled"):
                gaps["dead_code"].append({
                    "node": nid,
                    "name": node["name"],
                    "concern": "RFC-enabled FM but no known caller",
                })
    
    return gaps
```

### C.5 Query Interface for Claude Code

All queries are exposed via a single CLI entry point:

```python
# brain_v2/cli.py

"""
Usage:
    python brain_v2/cli.py impact FIELD:FPAYP.XREF3
    python brain_v2/cli.py depends PROCESS:Payment_E2E
    python brain_v2/cli.py similar CLASS:YCL_IDFI_CGI_DMEE_FR
    python brain_v2/cli.py gaps
    python brain_v2/cli.py stats
    python brain_v2/cli.py build          # Full rebuild
    python brain_v2/cli.py update code    # Incremental: re-parse code only
    python brain_v2/cli.py update config  # Incremental: re-ingest config only
    python brain_v2/cli.py search "payment format exit"  # Full-text search
"""
```

---

## D. Technology Choice

### D.1 Graph Engine: NetworkX (not Neo4j)

| Factor | Neo4j | NetworkX | Decision |
|--------|-------|----------|----------|
| Scale | Billions of nodes | Millions of nodes | 80K nodes + 200K edges = trivially small for NetworkX |
| Setup | Java server, Docker, port conflicts | `pip install networkx` | No server needed |
| Querying | Cypher (powerful but separate language) | Python native (dict traversal) | Direct integration with Claude Code |
| Persistence | Built-in | JSON file + SQLite | Already have both |
| Visualization | Neo4j Browser | vis.js HTML (proven pattern) | Already building HTML companions |
| Learning curve | New tool for all agents | Already used in sap_brain.py | Zero migration cost |
| Memory | ~2GB for server | ~200MB for 80K nodes in RAM | Fits easily |

**Decision: NetworkX + JSON persistence.** Neo4j adds operational complexity (Java, ports, Docker) for zero benefit at this scale. If the graph ever exceeds 1M nodes (unlikely for a single SAP system), we can migrate to Neo4j using the same node/edge model.

The existing `sap_brain.py` already uses a custom graph class with dict-based nodes and list-based edges. Brain v2 wraps this with NetworkX for algorithms (shortest path, centrality, community detection) while keeping the same JSON serialization.

```python
# brain_v2/core/graph.py

import networkx as nx

class BrainGraph:
    """Thin wrapper around NetworkX DiGraph with our property model."""
    
    def __init__(self):
        self.G = nx.DiGraph()
    
    def add_node(self, node_id, **properties):
        self.G.add_node(node_id, **properties)
    
    def add_edge(self, from_id, to_id, **properties):
        self.G.add_edge(from_id, to_id, **properties)
    
    def impact_radius(self, node_id, max_depth=4):
        """BFS with risk decay."""
        # Uses NetworkX's built-in BFS with custom traversal
        return nx.single_source_shortest_path_length(self.G, node_id, cutoff=max_depth)
    
    def critical_nodes(self, top_n=20):
        """Nodes with highest betweenness centrality = most critical for system integrity."""
        # Sample subgraph for performance (skip FUND nodes, they dominate)
        subgraph = self.G.subgraph(
            [n for n, d in self.G.nodes(data=True) if d.get("type") != "FUND"]
        )
        centrality = nx.betweenness_centrality(subgraph, k=min(500, len(subgraph)))
        return sorted(centrality.items(), key=lambda x: -x[1])[:top_n]
    
    def shortest_impact_path(self, from_id, to_id):
        """Find the shortest dependency chain between two nodes."""
        try:
            path = nx.shortest_path(self.G, from_id, to_id)
            edges = []
            for i in range(len(path)-1):
                edge_data = self.G.edges[path[i], path[i+1]]
                edges.append({"from": path[i], "to": path[i+1], **edge_data})
            return {"path": path, "length": len(path)-1, "edges": edges}
        except nx.NetworkXNoPath:
            return {"path": [], "length": -1, "message": "No path exists"}
    
    def community_detection(self):
        """Find clusters of tightly-connected objects (Louvain method)."""
        undirected = self.G.to_undirected()
        # Filter out FUND nodes (they'd dominate any community)
        filtered = undirected.subgraph(
            [n for n, d in undirected.nodes(data=True) if d.get("type") != "FUND"]
        )
        communities = nx.community.louvain_communities(filtered)
        return communities
    
    def save(self, filepath):
        """Serialize to JSON (same format as sap_brain.py for backward compat)."""
        data = {
            "meta": {
                "built": datetime.now().isoformat(),
                "nodes": self.G.number_of_nodes(),
                "edges": self.G.number_of_edges(),
                "version": "2.0",
            },
            "nodes": [{"id": n, **d} for n, d in self.G.nodes(data=True)],
            "edges": [{"from": u, "to": v, **d} for u, v, d in self.G.edges(data=True)],
        }
        Path(filepath).write_text(json.dumps(data, indent=2, ensure_ascii=False),
                                   encoding="utf-8")
    
    @classmethod
    def load(cls, filepath):
        """Load from JSON."""
        brain = cls()
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        for n in data.get("nodes", []):
            nid = n.pop("id")
            brain.G.add_node(nid, **n)
        for e in data.get("edges", []):
            brain.G.add_edge(e["from"], e["to"],
                            **{k: v for k, v in e.items() if k not in ("from", "to")})
        return brain
```

### D.2 Persistence: Dual-Store (JSON + SQLite)

```
brain_v2/
  brain_graph.json        # Full graph (NetworkX serialized) — ~50MB estimated
  brain_index.db          # SQLite index for fast lookups without loading full graph
```

The SQLite index enables fast queries without loading the entire graph into memory:

```sql
-- brain_index.db

CREATE TABLE nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    domain TEXT,
    layer TEXT,
    metadata_json TEXT     -- JSON blob for type-specific properties
);

CREATE TABLE edges (
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    type TEXT NOT NULL,
    label TEXT,
    weight REAL DEFAULT 1.0,
    evidence TEXT,
    confidence REAL DEFAULT 1.0,
    PRIMARY KEY (from_id, to_id, type)
);

CREATE INDEX idx_edges_from ON edges(from_id);
CREATE INDEX idx_edges_to ON edges(to_id);
CREATE INDEX idx_edges_type ON edges(type);
CREATE INDEX idx_nodes_type ON nodes(type);
CREATE INDEX idx_nodes_domain ON nodes(domain);

-- Fast impact query: "what nodes connect to X?"
-- SELECT * FROM edges WHERE from_id = ? OR to_id = ?
```

### D.3 Vector Embeddings: Optional Enhancement

Embeddings add value for two specific use cases:
1. **Code similarity**: "Find ABAP methods that do similar things to this one"
2. **Natural language queries**: "Show me everything related to payment file formats"

**Technology:** `sentence-transformers` with `all-MiniLM-L6-v2` (already proposed in v1 architecture). Stored in ChromaDB (local, no server).

**When to add:** Phase 3. The graph-based queries (impact, dependency, gap) deliver 80% of the value without embeddings. Add embeddings only when users request natural language search or code similarity.

```python
# brain_v2/optional/embeddings.py (Phase 3)

# Collections to embed:
# 1. ABAP method source code (~500 methods, ~50 tokens avg)
# 2. Skill knowledge sections (~200 sections)
# 3. Knowledge doc paragraphs (~1000 paragraphs)
# 4. Node descriptions (all 80K nodes, metadata.name + metadata.tags)
```

### D.4 MCP Integration

The brain exposes itself to Claude Code via the existing MCP server pattern:

```python
# Extension to sap_mcp_server.py

@mcp.tool()
def brain_impact(node_id: str, max_depth: int = 4) -> str:
    """Analyze what breaks if a given SAP object changes."""
    brain = BrainGraph.load(BRAIN_V2_PATH)
    result = impact_analysis(brain, node_id, max_depth)
    return json.dumps(result, indent=2)

@mcp.tool()
def brain_depends(node_id: str) -> str:
    """Show complete dependency tree for an object or process."""
    brain = BrainGraph.load(BRAIN_V2_PATH)
    result = dependency_tree(brain, node_id)
    return json.dumps(result, indent=2)

@mcp.tool()
def brain_search(query: str) -> str:
    """Search the brain for nodes matching a query."""
    brain = BrainGraph.load(BRAIN_V2_PATH)
    # First: exact match on ID/name
    # Second: substring match on name/tags
    # Third (if embeddings available): semantic search
    ...
```

---

## E. Implementation Plan

### Phase 1: Behavioral Edges from Code (Effort: 1 session)

**Goal:** Parse all 896 ABAP files and create ~5,000 behavioral edges.

**Prerequisites:** None -- all data exists locally.

**Steps:**
1. Create `brain_v2/` directory structure
2. Implement `ABAPDependencyParser` (patterns 1-6 from B.1)
3. Parse `extracted_code/DMEE/` (25 files) -- validate edges manually
4. Parse `extracted_code/YWFI/` (~20 files)
5. Parse `extracted_code/UNESCO_CUSTOM_LOGIC/` (~100 files)
6. Parse all `extracted_code/ZCL_*/` and `extracted_code/CL_*/` (~750 files)
7. Generate initial edge report: tables read, FMs called, BAdIs implemented
8. Create nodes for every referenced table/FM that doesn't exist yet
9. Save as brain_v2_graph.json

**Expected output:**
- ~500 code object nodes (classes, methods, reports, enhancements)
- ~3,000 READS_TABLE/READS_FIELD edges
- ~2,000 CALLS_FM edges
- ~50 IMPLEMENTS_BADI edges
- ~20 INHERITS_FROM edges

**Validation:** Manually verify the DMEE payment chain:
```
YCL_IDFI_CGI_DMEE_FR --READS_TABLE--> FPAYP
YCL_IDFI_CGI_DMEE_FR --READS_FIELD--> FPAYP.XREF3
YCL_IDFI_CGI_DMEE_FR --CALLS_FM--> FI_CGI_DMEE_GET_PAYEE_DATA
```

### Phase 2: Configuration + Integration Edges (Effort: 1 session)

**Goal:** Link config tables to code and integration map to functions.

**Prerequisites:** Phase 1 complete (so code nodes exist to link to).

**Steps:**
1. Implement `ingest_payment_config()` from B.2 (T042Z, T042A, BCM, house banks)
2. Implement `ingest_transport_objects()` from B.2 (108K cts_objects -> code nodes)
3. Implement `ingest_integration()` from B.4 (RFCDES, TFDIR_CUSTOM, .NET apps)
4. Implement `ingest_job_intelligence()` from B.2 (TBTCO/TBTCP -> programs)
5. Add table-field nodes from Gold DB PRAGMA table_info()
6. Add FIELD_MAPS_TO edges from the known join map (Section A.3 Category 3)
7. Implement CO_TRANSPORTED_WITH edges (objects in same transport)

**Expected output:**
- ~500 config nodes (DMEE trees, payment methods, house banks, BCM rules)
- ~2,000 config edges (USES_DMEE_TREE, ROUTES_TO_BANK, etc.)
- ~108,290 TRANSPORTS edges (transport -> object)
- ~50,000 CO_TRANSPORTED_WITH edges (co-change coupling)
- ~500 integration edges (CALLS_SYSTEM, EXPOSES_FM, CALLS_VIA_RFC)

**Validation:** Verify the complete payment chain:
```
PAYMETHOD:UNES:T --USES_DMEE_TREE--> DMEE:/CGI_XML_CT_UNESCO
DMEE:/CGI_XML_CT_UNESCO --CONFIGURES_FORMAT--> CLASS:YCL_IDFI_CGI_DMEE_FR
CLASS:YCL_IDFI_CGI_DMEE_FR --READS_FIELD--> FPAYP.XREF3
CLASS:YCL_IDFI_CGI_DMEE_FR --CALLS_FM--> FI_CGI_DMEE_GET_PAYEE_DATA
PAYMETHOD:UNES:T --ROUTES_TO_BANK--> HOUSEBANK:UNES:SOG01
```

### Phase 3: Process Overlay + Query Engine (Effort: 1-2 sessions)

**Goal:** Add process mining data as graph overlay and implement all query types.

**Prerequisites:** Phases 1-2 complete.

**Steps:**
1. Implement process ingestor from B.3 (P2P, Payment_E2E, Bank_Statement)
2. Implement impact analysis query (C.1)
3. Implement dependency tracing query (C.2)
4. Implement structural similarity query (C.3)
5. Implement gap analysis query (C.4)
6. Build CLI interface (C.5)
7. Generate impact analysis HTML companion (interactive visualization)
8. (Optional) Add vector embeddings for code similarity

**Expected output:**
- ~15 process nodes, ~100 step nodes
- ~500 STEP_READS, STEP_FOLLOWS, PROCESS_CONTAINS edges
- 4 working query types accessible via CLI
- HTML companion showing impact analysis results visually

**Validation:** Run the full impact query from the problem statement:
```
> python brain_v2/cli.py impact "TABLE_FIELD:FPAYP.XREF3"

Impact radius: 14 objects
[90%] YCL_IDFI_CGI_DMEE_FR (reads this field)
[86%] /CGI_XML_CT_UNESCO (DMEE tree using this class)
[81%] UNES-T wire transfer (payment method using this tree)
[81%] IIEP-T wire transfer
[81%] UBO-T wire transfer
[77%] SOG01 (house bank receiving the output)
[73%] SocGen/CGI (external bank)
[70%] Payment_E2E process (step: Bank File Sent)
```

### Phase 4: Continuous Evolution (Ongoing)

After the initial 3 phases:
- Every new code extraction automatically triggers ABAP parser
- Every new table extraction adds nodes + field nodes + join edges
- Every session close updates the brain with new findings
- The changelog tracks what changed when, enabling "what's new since last week?"

---

## F. File Layout

```
brain_v2/
  __init__.py
  cli.py                           # Main entry point
  core/
    graph.py                       # BrainGraph (NetworkX wrapper)
    incremental.py                 # Change tracking
    schema.py                      # Node/edge type definitions + validation
  parsers/
    abap_parser.py                 # ABAP source -> dependency edges
  ingestors/
    code_ingestor.py               # extracted_code/ -> graph
    config_ingestor.py             # Gold DB config tables -> graph
    integration_ingestor.py        # RFCDES/TFDIR/EDIDC -> graph
    process_ingestor.py            # Process mining -> graph
    transport_ingestor.py          # CTS objects -> graph
    sqlite_ingestor.py             # Gold DB master data -> graph
  queries/
    impact.py                      # Impact analysis (C.1)
    dependency.py                  # Dependency tracing (C.2)
    similarity.py                  # Structural + semantic similarity (C.3)
    gap.py                         # Gap analysis (C.4)
  optional/
    embeddings.py                  # ChromaDB vector store (Phase 3+)
  output/
    brain_v2_graph.json            # Serialized graph
    brain_v2_index.db              # SQLite index
    brain_v2_changelog.json        # What changed when
```

This directory lives at: `c:\Users\jp_lopez\projects\abapobjectscreation\brain_v2\`

---

## G. Migration from Brain v1

Brain v1 (`sap_brain.py` -> `sap_brain.json`) continues to work. Brain v2 is a separate system that:

1. **Reads v1's JSON** as one of its sources (preserving all 73K nodes)
2. **Adds behavioral edges** that v1 doesn't have
3. **Replaces v1's build function** with the modular ingestor pipeline
4. **Keeps v1's HTML visualization** working (same node/edge JSON schema)

The migration path:
- Phase 1-2: v2 runs alongside v1. Both produce separate JSON files.
- Phase 3: v2 becomes the primary brain. v1's build function is deprecated.
- v1's JSON file is kept as a backup but no longer updated.

No data is lost. The v2 JSON is a strict superset of v1's JSON.

---

## H. Success Metrics

| Metric | Brain v1 | Brain v2 Target | How Measured |
|--------|----------|----------------|-------------|
| Node types | 20 | 30 | schema.py type count |
| Edge types | 14 | 45 | schema.py type count |
| Behavioral edges (non-taxonomic) | 150 (~0.2%) | 50,000+ (~25%) | Count edges excluding HAS_FUND/BELONGS_TO |
| Impact query accuracy | N/A | 80% precision on manual validation set | 10 known impact chains validated |
| Query response time | N/A | <5 seconds for any query | Measured on 80K node graph |
| Code coverage (% of extracted files parsed) | ~5% | 100% | Parser run against all 896 files |
| Config coverage (% of config tables graphed) | 0% | 100% of extracted config tables | T042*, BNK_*, T012*, etc. |

---

## I. What This Enables (Business Value)

### For SAP Basis / Technical Architects
- **Before transport import:** "Show me everything this transport touches and what it might break"
- **Before config change:** "If I change this DMEE tree, which company codes, payment methods, and banks are affected?"
- **System cleanup:** "Show me RFC destinations that nothing calls, ICF services nobody uses"

### For Functional Consultants
- **Process understanding:** "What's the complete dependency chain for the P2P process?"
- **Cross-module impact:** "If I change this FM derivation rule, which FI postings are affected?"
- **Knowledge gap:** "What parts of the payment process have no documentation?"

### For Management / PMO
- **Risk assessment:** "What are the 20 most critical objects in our system? (highest betweenness centrality)"
- **Change planning:** "What's the blast radius of this project?" (aggregate impact across all transports)
- **Integration audit:** "How many external systems depend on our custom FMs?"

### For AI Agents (Claude Code)
- **Autonomous reasoning:** Agent can self-answer "what would this change affect?" before executing
- **Skill routing:** Graph structure tells coordinator which skill/domain to invoke
- **Evidence-based answers:** Every claim can be traced to a specific node/edge with provenance

---

> This architecture is designed to be built entirely from data that already exists in this project. No new SAP extractions are required for Phases 1-3. The implementation effort is estimated at 3-4 sessions.
