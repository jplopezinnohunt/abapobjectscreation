# Brain Design Specification v3 — Agent-Optimized Hybrid Architecture
**Version:** 3.0 | **Session:** #049 | **Date:** 2026-04-09
**Status:** ACTIVE — Mandatory reading before any Brain modification

---

## 1. Purpose

The Brain is the AI agent's persistent, queryable, self-correcting memory. It accumulates intelligence across sessions so that every future incident, analysis, and decision benefits from everything learned before.

**It is NOT a dashboard.** It is NOT a documentation system. It is the agent's working memory — optimized for how an LLM actually processes information.

## 2. Design Principles

### 2.1 Agent-Optimized
The agent is a text-based LLM with 1M context window. Design for how it actually works:
- **Text files** = 1 Read call, native understanding. Best for reasoning and context.
- **SQL queries** = 3 steps (write query, Bash tool, parse output). Best for filtering.
- **Graph algorithms** = CLI tool call. Best for impact analysis, dependency tracing.

Each format for what it does best. Never force one format where another is superior.

### 2.2 Portable
ALL irreplaceable knowledge lives inside the project directory, git-tracked. Nothing critical exists only in `~/.claude/memory/` (machine-specific). On a new machine, `git clone` + `python -m brain_v2 build` restores full intelligence.

### 2.3 Compression-Safe
Context compression mid-session destroys any knowledge only in conversation text. Every discovery must be written to a file (annotation, claim, index entry) within the same turn. The agent can always `Read` files to recover after compression.

### 2.4 Can't Lose It
- **Irreplaceable knowledge** (annotations, claims, feedback rules) = git-tracked source JSON files
- **Generated artifacts** (graph, text index, SQLite active DB) = rebuildable from source by running scripts
- Distinction is explicit: if you delete a generated file, run the build. If you delete a source file, knowledge is lost.

## 3. Architecture — Three Layers

```
                    ┌─────────────────────────────────────┐
                    │        AGENT (LLM, 1M context)       │
                    └──────┬──────────┬──────────┬─────────┘
                           │          │          │
                    ┌──────▼──────┐ ┌─▼────────┐ ┌▼──────────┐
                    │ TEXT INDEX   │ │ GRAPH    │ │ SQLite    │
                    │ (Read file) │ │ (CLI)    │ │ (SQL)     │
                    │             │ │          │ │           │
                    │ One .md per │ │ NetworkX │ │ pmo_items │
                    │ analyzed    │ │ 52K nodes│ │ claims    │
                    │ object      │ │ 113K edge│ │ sessions  │
                    │             │ │          │ │ incidents │
                    │ Context     │ │ BFS,     │ │ Filter,   │
                    │ loading     │ │ impact,  │ │ aggregate │
                    │ & reasoning │ │ depends  │ │ & query   │
                    └──────┬──────┘ └─┬────────┘ └┬──────────┘
                           │          │           │
                    ┌──────▼──────────▼───────────▼──────────┐
                    │         SOURCE FILES (git-tracked)       │
                    │                                          │
                    │  annotations.json  — object findings     │
                    │  claims.json       — system facts        │
                    │  feedback_rules.json — agent behavior    │
                    │  knowledge/domains/ — rich domain docs   │
                    │  extracted_code/    — 1,132 ABAP files   │
                    │  PMO_BRAIN.md      — pending work        │
                    └──────────────────────────────────────────┘
```

### Layer 1: brain_state.json — Single-File Session Bootstrap
- **Location:** `brain_v2/brain_state.json`
- **Purpose:** ONE Read call at session start = full intelligence in context
- **Size:** ~28K tokens (2.8% of 1M context)
- **Structure:** Object-centric knowledge graph (NOT flat arrays)
  - `objects`: 102 entities, each with edges/annotations/claims/incidents inline
  - `indexes`: cross-cutting views (by_incident, by_domain, uncertain_claims, superseded_claims)
  - `rules`: 49 agent behavioral rules
  - `claims`: 12 system-level facts with evidence trails
- **Generated from:** Graph + annotations + claims + feedback_rules after each build
- **When to use:** Session start — 1 Read call replaces 50+ file reads
- **Rebuildable:** Yes — `python brain_v2/generate_index.py`
- **Query functions:** `python brain_v2/graph_queries.py <command>` — 8 commands for mid-session reasoning without loading full graph

**Design principle (Session #049, cross-project):**
Agent thinks in ONE dense file, not 50 scattered files. 50 files = 50 tool calls = human thinking. 1 file = 1 tool call = agent thinking. The PPM-brain confirmed: per-object index files are human pattern. Object-centric JSON with cross-cutting indexes is agent pattern. Scales with context window growth.

### Layer 2: NetworkX Graph — Algorithms & Traversal
- **Location:** `brain_v2/output/brain_v2_graph.json` (65MB)
- **Purpose:** Graph algorithms that SQL and text can't do
- **Algorithms:** BFS impact analysis with risk decay, dependency tracing, shortest path, community detection, structural similarity, gap analysis
- **When to use:** "If we change X, what breaks?" — `python -m brain_v2 impact X`
- **Rebuildable:** Yes — `python -m brain_v2 build`

### Layer 3: SQLite Active DB — Filtering & Aggregation
- **Location:** `brain_v2/output/brain_v2_active.db`
- **Purpose:** Structured queries that need filtering (not reasoning)
- **Tables:** pmo_items, claims, sessions, incidents (4 tables only)
- **When to use:** "Show me all open HIGH PMO items" — SQL query
- **NOT source of truth:** Generated from source files (claims.json, PMO_BRAIN.md, retros)
- **Rebuildable:** Yes — `python -m brain_v2 active-db`

### Design Correction: Agent Thinking vs Human Thinking (Session #049 feedback)

| Human thinking | Agent thinking |
|---|---|
| 50 entity index files (one per object) | 1 brain_state.json (everything in ONE file) |
| Session start: read 44 files (44 tool calls) | Session start: read 1 file (1 tool call) |
| "Organize into folders" | "Give me everything, I'll scan in context" |
| Pretty markdown per entity | Dense JSON, machine-parseable |
| File size matters | Tool call count matters — 5000 lines costs same as 50 |

My bottleneck is tool calls, not file size. 1M context fits ~85K tokens of brain state (8.5%). ONE Read call.

### What's NOT in each layer (and why)
| Data | NOT in brain_state.json | NOT in SQL | NOT in Graph |
|------|------------------|-----------|-------------|
| 52K nodes | Only ~100 important ones loaded | Don't filter nodes, traverse them | IN graph (native) |
| 113K edges | Only ~1,300 important ones loaded | BFS needs NetworkX, not JOINs | IN graph (native) |
| Annotations | IN brain_state.json | SQL strips the WHY | Merged into node metadata |
| Claims | IN brain_state.json | IN SQL (for filtering) | Not a graph concept |
| PMO items | Not needed at start | IN SQL (for filtering) | Not a graph concept |
| Knowledge docs | Too long, use on-demand | Not tabular | As KNOWLEDGE_DOC nodes |

## 4. Data Models

### 4.1 Feedback Rules (`brain_v2/agent_rules/feedback_rules.json`)
**Git-tracked, irreplaceable. Source of truth for agent behavioral rules.**

```json
{
  "id": "feedback_bseg_is_join_not_table",
  "rule": "BSEG is a JOIN via Golden Query, NEVER extract/enrich it",
  "why": "Reason and evidence that created this rule",
  "how_to_apply": "When and where the agent should apply this",
  "severity": "CRITICAL | HIGH | MEDIUM",
  "created_session": 35,
  "source_file": "feedback_bseg_is_join_not_table.md"
}
```

### 4.2 Claims (`brain_v2/claims/claims.json`)
**Git-tracked, irreplaceable. System-level facts with evidence trails.**

```json
{
  "id": 1,
  "claim": "What we believe",
  "claim_type": "verified_fact | hypothesis | superseded",
  "confidence": "TIER_1 | TIER_2 | TIER_3 | TIER_4 | TIER_5",
  "evidence_for": "What supports this",
  "evidence_against": "What contradicts it (null if none)",
  "related_objects": ["object_ids"],
  "domain": "FI | HCM | Travel | PSM | Integration",
  "created_session": 48,
  "resolved_session": null,
  "resolution_notes": null,
  "status": "active | superseded | confirmed"
}
```

**Confidence tiers:**
- TIER_1: Certain — verified from source code, Gold DB, or SAP system
- TIER_2: High — domain knowledge, expert-verified edges
- TIER_3: Moderate — screenshots, session retros, inferred from patterns
- TIER_4: Low — single observation, not re-verified
- TIER_5: Speculative — hypothesis without direct evidence

### 4.3 Annotations (`brain_v2/annotations/annotations.json`)
**Git-tracked, irreplaceable. Object-level code findings.**

```json
{
  "LHRTSF01": {
    "annotations": [
      {
        "tag": "CRITICAL",
        "finding": "IF epk-bukst = epk-bukrs — only propagates GSBER for same-company",
        "impact": "Intercompany trips get no business area",
        "line": 852,
        "session": "#048",
        "incident": "INC-000006073",
        "field": "GSBER",
        "related": ["PA0001.GSBER", "PTRV_SCOS.COMP_CODE"]
      }
    ]
  }
}
```

### 4.4 Text Object Index (`brain_v2/index/{id}.md`)
**Rebuildable. One file per analyzed object.**

Selection criteria (not all 52K nodes):
- Has >=1 annotation
- Referenced in an incident
- Has >=5 edges AND is Y*/Z* custom
- Is an extracted SAP_STANDARD file
- Is a SAP_TABLE with >=3 incoming READS_TABLE edges
- Estimated: 200-500 objects

Format: See Section 11 (Appendix A).

### 4.5 SQLite Active DB (`brain_v2/output/brain_v2_active.db`)
**Rebuildable. For filtering queries only.**

4 tables: `pmo_items`, `claims`, `sessions`, `incidents`. See Section 12 (Appendix B) for full schema.

## 5. Build Pipeline

```
python -m brain_v2 build
  Phase 1: Code Parser         → extracted_code/ + extracted_sap/ (incl. SAP_STANDARD/)
  Phase 2: Config/Transport    → Gold DB tables, deduped nodes
  Phase 3: Processes           → UNESCO E2E process definitions
  Phase 4: Knowledge docs      → knowledge/domains/, skills/, retros
  Phase 5: Domain knowledge    → Expert-verified behavioral edges
  Phase 6: Annotations         → Materializes metadata edges + incidents

python -m brain_v2 index       → Generates text index from graph + annotations + claims
python -m brain_v2 active-db   → Generates SQLite from claims.json + PMO + retros
```

## 6. Memory Alignment — CLAUDE.md and feedback_rules.json

### Problem (pre-v3)
CLAUDE.md summarized rules, `~/.claude/memory/` had details. 30+ cross-references between them. They drifted apart. Memory was machine-specific.

### Solution (v3)
- **CLAUDE.md** = stable overview (architecture, patterns, anti-patterns). Changes rarely.
- **feedback_rules.json** = detailed behavioral rules. Grows every session. Git-tracked in project.
- **No duplication.** CLAUDE.md references `brain_v2/agent_rules/`, doesn't restate rules.
- **Session start:** Agent reads CLAUDE.md (overview) + feedback_rules.json (detail) = 2 calls, complete picture.

## 7. Portability Matrix

| Knowledge | Source of truth | Git? | On new machine |
|---|---|---|---|
| 34 feedback rules | brain_v2/agent_rules/feedback_rules.json | YES | Preserved |
| Object annotations | brain_v2/annotations/annotations.json | YES | Preserved |
| System claims | brain_v2/claims/claims.json | YES | Preserved |
| Domain knowledge | knowledge/domains/ | YES | Preserved |
| Extracted code | extracted_code/ + extracted_sap/ | YES | Preserved |
| PMO items | .agents/intelligence/PMO_BRAIN.md | YES | Preserved |
| Text object index | brain_v2/index/ | YES | Rebuildable |
| Graph (52K nodes) | brain_v2/output/ | .gitignore | Rebuild: `build` |
| Active DB | brain_v2/output/ | .gitignore | Rebuild: `active-db` |
| Gold DB (5.3GB) | Zagentexecution/.../sqlite/ | .gitignore | Re-extract from SAP |
| ~/.claude/memory/ | CACHE (not source of truth) | NO | Regenerate from project |

## 8. Design Evolution — Why Hybrid

### v1 (Session #007): Progressive disclosure
73K nodes, 3-level access (summary/focus/full). JSON-only. Write-only brain — nobody queried it.

### v2 (Sessions #039-042): Impact analysis
52K nodes, 113K edges. NetworkX + CLI. Impact/depends/similar/gaps queries operational. Still JSON-first, no agent-optimized access.

### v3 (Session #049): Agent-optimized hybrid
Three critical challenges reshaped the approach:

1. **D010TAB has 200M+ rows** — Bulk extraction abandoned. On-demand WBCROSSGT queries for specific objects when needed.
2. **"Is SQL better for you?"** — Honest evaluation: text for reasoning, graph for algorithms, SQL only for filtering. Hybrid wins.
3. **60 memory files outside project** — Machine change = total knowledge loss. Migrated into git-tracked project files.

### Why NOT pure SQL (PPM-brain pattern)
The PPM-brain uses SQL for 417 entities. Our brain has 52K nodes and 113K edges. At this scale:
- Text index is faster for object lookup (1 Read vs 3-step SQL roundtrip)
- Graph algorithms (BFS, impact) can't be expressed as SQL JOINs
- Annotations need narrative context — SQL strips the WHY
- SQL IS better for filtering PMO items and claims — so we use it there

## 9. Future Enrichment Path

Designed but NOT implemented in v3:

- **WBCROSSGT on-demand**: Agent detects gap → queries WBCROSSGT via RFC for specific Y*/Z* object → inserts edges into graph + updates index. Targeted, not bulk.
- **Cross-brain queries**: PPM-brain agent queries our `claims` table via SQL. Schema is compatible.
- **Historical annotation deep review**: 200+ annotations from 48 session retros.
- **Session learning propagation**: Every session close annotates objects analyzed → claims updated → index regenerated.

## 10. Rules for Modifying the Brain

1. **Read this spec first.** Every session that touches brain_v2/ must read this document.
2. **Source files are irreplaceable.** Never delete annotations.json, claims.json, or feedback_rules.json without explicit user approval.
3. **Generated files are disposable.** Graph, index, active DB can be rebuilt. Don't panic if they're missing.
4. **New ingestors go in brain_v2/ingestors/.** Follow the pattern: `ingest_X(brain, project_root)`.
5. **New edge types go in brain_v2/core/schema.py.** Include: name, weight, direction, category.
6. **New claims go in claims.json.** Include: evidence_for, confidence tier, related_objects.
7. **New annotations go in annotations.json.** Include: tag, finding, session, impact.
8. **After any change, rebuild:** `python -m brain_v2 build && python -m brain_v2 index`

---

## 11. Appendix A — Text Object Index Format

```markdown
# {OBJECT_NAME}
**Type:** {type} | **Domain:** {domain} | **Layer:** {layer}
**Source:** {file_path} ({line_count} lines)
**Last analyzed:** Session #{session}

## Dependencies
### Reads Tables
| Table | Confidence | Evidence |
|-------|-----------|----------|

### Calls Functions
| FM | Confidence | Evidence |
|----|-----------|----------|

### Called By
| Caller | Edge Type | Evidence |
|--------|----------|----------|

## Annotations ({count})
### [{TAG}] Line {N} — {title}
{finding}
**Impact:** {impact}
**Incident:** {incident_id} | **Session:** #{session}

## Claims
- **[{TIER}]** {claim} (verified #{session})

## Incidents
- **{incident_id}** — {description}. {edge_type} this object.
```

## 12. Appendix B — SQLite Active DB Schema

```sql
CREATE TABLE pmo_items (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    priority TEXT NOT NULL,
    category TEXT,
    status TEXT NOT NULL,
    first_raised_session INTEGER,
    closed_session INTEGER,
    closed_reason TEXT,
    notes TEXT
);

CREATE TABLE claims (
    id INTEGER PRIMARY KEY,
    claim TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    confidence TEXT NOT NULL,
    evidence_for TEXT,
    evidence_against TEXT,
    related_objects TEXT,
    domain TEXT,
    created_session INTEGER,
    resolved_session INTEGER,
    status TEXT DEFAULT 'active'
);

CREATE TABLE sessions (
    session_number INTEGER PRIMARY KEY,
    date TEXT,
    focus TEXT,
    deliverables_count INTEGER DEFAULT 0,
    items_added INTEGER DEFAULT 0,
    items_closed INTEGER DEFAULT 0,
    net INTEGER DEFAULT 0
);

CREATE TABLE incidents (
    id TEXT PRIMARY KEY,
    description TEXT,
    root_cause_objects TEXT,
    contributing_objects TEXT,
    session_discovered INTEGER,
    session_resolved INTEGER,
    status TEXT
);
```
