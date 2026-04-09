# Session #049 Plan — Code Brain v2: Agent-Optimized Hybrid Rebuild

## Context

The Brain v2 has 52,491 nodes / 113,172 edges but is broken for agent use. Three problems:
1. **Graph broken**: 34 SAP_STANDARD files unparsed, 3,217 duplicate nodes, 3 days stale
2. **No fast lookup**: 65MB JSON — can't query mid-session without loading entire graph
3. **Knowledge at risk**: 60 memory files (34 feedback rules, 11 project state docs) live OUTSIDE the project in `~/.claude/`. Machine change = total knowledge loss.

---

## Detailed Design

### 1. Feedback Rules — Data Model

Each of the 34 feedback rules migrated from `~/.claude/memory/feedback_*.md` into a single JSON array at `brain_v2/agent_rules/feedback_rules.json`:

```json
[
  {
    "id": "feedback_bseg_is_join_not_table",
    "rule": "BSEG is a JOIN via Golden Query, NEVER extract/enrich it",
    "why": "BSEG is not a physical table in P01 — it's a cluster. The Golden Query already joins BSIS+BSAS+BSIK+BSAK+BSID+BSAD into bseg_union VIEW (4.7M rows). Extracting BSEG directly = duplicate data + wrong approach.",
    "how_to_apply": "When someone asks to extract or enrich BSEG, redirect to bseg_union. When building queries, use the Golden Query pattern (bseg_union + BKPF + FMIFIIT + PRPS).",
    "severity": "CRITICAL",
    "created_session": 35,
    "source_file": "feedback_bseg_is_join_not_table.md"
  },
  {
    "id": "feedback_bash_autonomy",
    "rule": "NEVER ask before running bash commands — just run them",
    "why": "User gave explicit instruction: execute autonomously. Asking 'should I run this?' wastes time.",
    "how_to_apply": "When a plan exists, execute all commands without confirmation. Only ask when requirements are ambiguous, never for execution permission.",
    "severity": "HIGH",
    "created_session": 12,
    "source_file": "feedback_bash_autonomy.md"
  }
]
```

**Fields:**
- `id`: unique identifier (matches original filename without .md)
- `rule`: the behavioral rule itself (1 sentence)
- `why`: the reason/evidence behind the rule (what went wrong that caused this)
- `how_to_apply`: when/where this rule activates
- `severity`: CRITICAL (violating causes data loss/errors), HIGH (violating wastes significant time), MEDIUM (preference)
- `created_session`: which session created this rule
- `source_file`: original memory file for traceability

**How I use it at session start:** One `Read` call loads all 34 rules. I scan the JSON array and internalize the rules. If I need a specific rule mid-session (e.g., about BSEG), I already have it in context from session start. If compressed, I `Read` the file again.

### 2. Claims — Data Model

System-level facts with evidence, stored at `brain_v2/claims/claims.json`:

```json
[
  {
    "id": 1,
    "claim": "Travel advance posting requires BUKRS=BUKST for GSBER propagation in LHRTSF01",
    "claim_type": "verified_fact",
    "confidence": "TIER_1",
    "evidence_for": "Source code LHRTSF01.abap line 852: IF epk-bukst = epk-bukrs. Verified from extracted code in Session #048.",
    "evidence_against": null,
    "related_objects": ["LHRTSF01", "PA0001", "PTRV_SCOS", "GGB1"],
    "domain": "Travel",
    "created_session": 48,
    "resolved_session": null,
    "resolution_notes": null,
    "status": "active"
  },
  {
    "id": 2,
    "claim": "FEBEP=0 was wrong — actual count is 223,710 items",
    "claim_type": "superseded",
    "confidence": "TIER_1",
    "evidence_for": "Re-extraction in Session #029 revealed 223K rows. Previous 'FEBEP=0' was artifact of truncated first extraction.",
    "evidence_against": "Original extraction in Session #025 returned 0 rows (FEBEP table, 50K limit, only 104 columns).",
    "related_objects": ["FEBEP", "FEBEP_2024_2026"],
    "domain": "FI",
    "created_session": 25,
    "resolved_session": 29,
    "resolution_notes": "The _2024_2026 suffix table has the real data. Unsuffixed FEBEP was truncated first attempt.",
    "status": "superseded"
  },
  {
    "id": 3,
    "claim": "SAPLYBAPI_SISTER reads 6+ custom tables including YDONOR and YBAPI_EXPENDITURE_DETAILS",
    "claim_type": "hypothesis",
    "confidence": "TIER_3",
    "evidence_for": "D010TAB filtered to YY* shows SAPLYBAPI_SISTER reading YBAPI_EXPENDITURE_DETAILS, YBAPI_GLACCOUNT_DETAILS, YBAPI_GLAC_DETAILS, YBAPI_LINEITEM_BUDET_DETAILS, YBAPI_YFM2_GLACCOUNT_DETAILS, YDONOR. Observed in SE16 screenshot Session #049.",
    "evidence_against": null,
    "related_objects": ["SAPLYBAPI_SISTER", "YDONOR", "YBAPI_EXPENDITURE_DETAILS"],
    "domain": "Integration",
    "created_session": 49,
    "resolved_session": null,
    "resolution_notes": null,
    "status": "active"
  }
]
```

**Confidence tiers (from PPM-brain):**
- `TIER_1`: Certain — verified from source code, Gold DB, or SAP system
- `TIER_2`: High confidence — domain knowledge, expert-verified edges
- `TIER_3`: Moderate — observed in screenshots, session retros, inferred from patterns
- `TIER_4`: Low — single observation, not re-verified
- `TIER_5`: Speculative — hypothesis without direct evidence

**Claim types:**
- `verified_fact`: confirmed true with evidence
- `hypothesis`: believed to be true, awaiting verification
- `superseded`: was believed true, later found wrong — includes resolution_notes explaining what changed

**How I use it:** At session start, I `Read` claims.json. I know what I'm certain about, what I'm uncertain about, and what I got wrong before. Mid-session, if I'm about to act on a TIER_3+ claim, I know to verify first. When I discover something new, I add a claim. When I find something was wrong, I mark it superseded with the correction — so I never repeat the same mistake.

### 3. Text Object Index — Format

Generated at `brain_v2/index/{object_id}.md`, one per analyzed object:

```markdown
# LHRTSF01
**Type:** ABAP_REPORT | **Domain:** Travel | **Layer:** code
**Source:** extracted_code/SAP_STANDARD/LHRTSF01.abap (852 lines)
**Last analyzed:** Session #048

## Dependencies
### Reads Tables
| Table | Confidence | Evidence |
|-------|-----------|----------|
| PA0001 | 1.0 | parsed |
| PTRV_SCOS | 1.0 | parsed |
| T706B1 | 1.0 | parsed |
| CSKS | 0.9 | code_metadata |

### Calls Functions
| FM | Confidence | Evidence |
|----|-----------|----------|
| HR_READ_INFOTYPE | 1.0 | parsed |
| RP_FILL_WAGE_TYPE | 0.95 | domain_knowledge |

### Called By
| Caller | Edge Type | Evidence |
|--------|----------|----------|
| RPRAPA00 | CALLS_FM | parsed |

## Annotations (3)
### [CRITICAL] Line 852 — Intercompany GSBER bug
IF epk-bukst = epk-bukrs — only propagates GSBER for same-company trips.
**Impact:** Any intercompany posting where partner company ≠ sending company gets no business area → posting fails with "business area required."
**Incident:** INC-000006073 | **Session:** #048
**Related:** PA0001.GSBER, PTRV_SCOS.COMP_CODE

### [CONTROL_FLAG] Line 850 — bukst variable
bukst = partner company code from trip header. Controls whether GSBER, KOSTL, PRCTR are propagated.
**Session:** #048

### [SIDE_EFFECT] Line 870 — KOSTL clearing
When bukst ≠ bukrs, KOSTL is also cleared (not just GSBER).
**Impact:** Intercompany trips lose cost center assignment too.
**Session:** #048

## Claims
- **[TIER_1]** Travel advance posting requires BUKRS=BUKST for GSBER propagation (verified #048, source:line 852)
- **[TIER_1]** Three safety nets were broken: BAdI PA0027-02 expired (2021), ZXTRVU05 commented out (2018), GGB1 missing GL 2021011 (verified #048)

## Incidents
- **INC-000006073** — IIEP traveler advance posting failure. ROOT_CAUSED_BY this object.
```

**Selection criteria for index generation** (not ALL 52K nodes — only analyzed objects):
- Has ≥1 annotation → always indexed
- Referenced in an incident → always indexed
- Has ≥5 edges (hub node) AND is Y*/Z* custom → indexed
- Is an extracted SAP_STANDARD file → indexed
- Is a SAP_TABLE with ≥3 incoming READS_TABLE edges → indexed
- Estimated: 200-500 objects

**How I use it:** When investigating an incident or answering "what do we know about X?", I `Read brain_v2/index/X.md`. One tool call, full context with narrative explanations, directly in my context window. No SQL roundtrip, no graph loading.

### 4. SQLite Active DB — Schema

Generated at `brain_v2/output/brain_v2_active.db`. NOT the source of truth — rebuilt from source files.

```sql
-- PMO items (source: PMO_BRAIN.md)
CREATE TABLE pmo_items (
    id TEXT PRIMARY KEY,            -- H34, G55, B1
    title TEXT NOT NULL,
    priority TEXT NOT NULL,         -- BLOCKING, HIGH, BACKLOG
    category TEXT,                  -- Data, Skill, Brain, Audit, Code, Ecosystem
    status TEXT NOT NULL,           -- OPEN, CLOSED, KILLED, MERGED
    first_raised_session INTEGER,
    closed_session INTEGER,
    closed_reason TEXT,
    notes TEXT
);

-- Claims (source: claims.json — SQL copy for filtering)
CREATE TABLE claims (
    id INTEGER PRIMARY KEY,
    claim TEXT NOT NULL,
    claim_type TEXT NOT NULL,       -- verified_fact, hypothesis, superseded
    confidence TEXT NOT NULL,       -- TIER_1 to TIER_5
    evidence_for TEXT,
    evidence_against TEXT,
    related_objects TEXT,           -- JSON array
    domain TEXT,
    created_session INTEGER,
    resolved_session INTEGER,
    status TEXT DEFAULT 'active'
);

-- Sessions (source: session retro files)
CREATE TABLE sessions (
    session_number INTEGER PRIMARY KEY,
    date TEXT,
    focus TEXT,
    deliverables_count INTEGER DEFAULT 0,
    items_added INTEGER DEFAULT 0,
    items_closed INTEGER DEFAULT 0,
    net INTEGER DEFAULT 0
);

-- Incidents (source: annotations.json incident references)
CREATE TABLE incidents (
    id TEXT PRIMARY KEY,
    description TEXT,
    root_cause_objects TEXT,        -- JSON array
    contributing_objects TEXT,      -- JSON array
    session_discovered INTEGER,
    session_resolved INTEGER,
    status TEXT                     -- OPEN, RESOLVED, MONITORING
);
```

**Why SQL for these 4 tables (not text):**
- PMO: "show me all open HIGH items" = filter query, not reading
- Claims: "show me all TIER_4+ uncertain facts" = filter query
- Sessions: "what's my closure velocity over last 10 sessions?" = aggregation
- Incidents: small table, but joins with claims and annotations

**What's NOT in SQL (and why):**
- Nodes (52K) → graph + text index is better. I don't filter nodes, I traverse them.
- Edges (113K) → graph algorithms (BFS, impact) need NetworkX, not SQL joins
- Annotations (41) → text index includes them with narrative context. SQL strips the WHY.
- Knowledge docs → rich markdown, I reason with the narrative

### 5. CLAUDE.md Alignment — What Changes

**Current CLAUDE.md** has 280+ lines including:
- Framework overview (keep)
- Key learnings / patterns (keep)
- Anti-patterns (keep)
- "Never Do This" section with 30+ `See [feedback_*.md]` references → **CHANGE**

**After this session:**
```markdown
## Agent Behavioral Rules
This project has 34+ feedback rules accumulated over 48 sessions.
**Authoritative source:** `brain_v2/agent_rules/feedback_rules.json`
At session start: Read CLAUDE.md (overview) + feedback_rules.json (detail).
Do NOT duplicate rules between files. If a rule exists in feedback_rules.json,
CLAUDE.md should reference it, not restate it.
```

The current "Never Do This" section with 30 individual `See [feedback_*.md]` links → replaced by one reference to `feedback_rules.json`. CLAUDE.md stays concise and stable. Rules grow in the JSON file.

### 6. Build Pipeline — Order of Operations

```
python -m brain_v2 build          # Phase 2: fix + rebuild graph
  ├── Phase 1: Code Parser        → parses extracted_code/ + extracted_sap/ 
  │                                  (NOW includes SAP_STANDARD/)
  ├── Phase 2: Config/Transport    → deduped nodes (CLASS: prefix only)
  │   /Integration/Schema/Jobs
  ├── Phase 3: Processes
  ├── Phase 4: Knowledge docs
  ├── Phase 5: Domain knowledge
  └── Phase 6: Annotations         → materializes metadata edges + incidents

python -m brain_v2 index          # Phase 3a: generate text index
  ├── Select important objects     → annotations + incidents + hubs + Y*/Z*
  ├── For each: gather edges,      → reads, writes, callers, callees
  │   annotations, claims
  └── Write brain_v2/index/{id}.md → one file per object

python -m brain_v2 active-db      # Phase 3c: generate SQLite
  ├── Parse PMO_BRAIN.md           → pmo_items table
  ├── Load claims.json             → claims table  
  ├── Parse session retros         → sessions table
  └── Extract incidents from       → incidents table
      annotations.json
```

### 7. Migration Strategy — Memory to Project

**One-time migration** (`brain_v2/migrate_memory.py`):

```
Step 1: Read ~/.claude/.../memory/feedback_*.md (34 files)
  → Parse frontmatter + content
  → Extract: rule, why, how_to_apply from markdown body
  → Write brain_v2/agent_rules/feedback_rules.json

Step 2: Read ~/.claude/.../memory/project_*.md (11 files)  
  → For each: check if knowledge/ already has equivalent content
  → If NOT in project → copy to knowledge/domains/ or brain_v2/claims/
  → If already in project → mark memory file as "cache only"

Step 3: Update CLAUDE.md
  → Replace 30+ "See [feedback_*.md]" lines with single reference
  → Add "Agent Behavioral Rules" section pointing to feedback_rules.json

Step 4: Keep ~/.claude/memory/ files intact (cache for fast session start)
  → But project files are now authoritative
  → If conflict: project file wins
```

### 8. Seeding Strategy — Initial Claims

First build generates ~200 claims from existing knowledge:

| Source | Claim Type | Confidence | Count (est.) |
|--------|-----------|-----------|--------------|
| Annotations with tag=CRITICAL | verified_fact | TIER_1 | ~10 |
| Code parser edges (confidence=1.0) | verified_fact | TIER_1 | ~50 |
| Domain knowledge edges (confidence=0.95) | verified_fact | TIER_2 | ~40 |
| Metadata-materialized edges (confidence=0.9) | verified_fact | TIER_2 | ~60 |
| Key session retro discoveries | hypothesis | TIER_3 | ~40 |
| **Total** | | | **~200** |

Examples of auto-generated claims:
- From code parser: "YCL_IDFI_CGI_DMEE_FR reads BKPF, BSEG, PA0001" (TIER_1, evidence: parsed)
- From domain knowledge: "FPAYP-XREF3 feeds DMEE tree PurposeCode" (TIER_2, evidence: domain_knowledge, Session #039)
- From annotation: "LHRTSF01 line 852 causes intercompany GSBER failure" (TIER_1, evidence: annotation + source code)
- From retro: "FEBEP=0 was wrong, real count 223K" (superseded, resolved Session #029)

### 9. Design Rationale — Why Hybrid, Not Pure SQL

**The evolution of this design (within this session):**

We started with the PMO assumption: "extract D010TAB/WBCROSS/D010INC from SAP → rebuild Brain." During planning, three critical challenges reshaped the approach:

**Challenge 1: D010TAB has 200M+ rows.**
Original plan was full extraction. User correctly pointed out this is mapping 100% of SAP, which we never do. Even filtered to Y*/Z*, these tables can be queried on-demand via WBCROSSGT when investigating a specific object — no need to bulk extract.

**Challenge 2: "Is SQL actually better for you?"**
The PPM-brain uses SQL (417 entities, 3,451 claims). We have 52K nodes, 113K edges. I evaluated honestly:
- I'm a text-based LLM. Reading a markdown file = 1 tool call, native understanding.
- Querying SQL = 3 steps (write query → Bash tool → parse text output).
- Graph algorithms (BFS impact analysis) need NetworkX, not SQL JOINs.
- BUT: filtering ("show me all open HIGH PMO items") IS better in SQL.

**Result: hybrid** — text for reasoning (object index), graph for algorithms (impact/depends), SQL only for filtering (PMO, claims, sessions).

**Challenge 3: "60 memory files are outside the project."**
34 feedback rules + 11 project docs live in `~/.claude/memory/` — machine-specific, not git-tracked. Move to a new machine = lose 48 sessions of accumulated behavioral intelligence. The agent becomes generic again.

**Result: migrate irreplaceable knowledge INTO the project** — `feedback_rules.json` (git-tracked, portable), claims.json (git-tracked, portable). Memory files become a cache, not the source of truth.

### 10. Memory ↔ CLAUDE.md Alignment — The Problem and Solution

**The problem today:**

```
CLAUDE.md (280 lines)                    ~/.claude/memory/ (60 files)
├── "Never Do This" section              ├── feedback_bseg_is_join_not_table.md
│   └── "See feedback_bseg_*.md" ──────→│   └── Full rule + why + how to apply
│   └── "See feedback_efficiency.md" ──→│   └── Full rule + why + how to apply
│   └── ... (30+ references)            │   └── ...
│                                        │
├── Key Learnings (summary)              ├── project_golden_query.md
│   └── Brief mention of patterns        │   └── Detailed query patterns
│                                        │
├── Memory Architecture section          ├── MEMORY.md (index to all 60 files)
│   └── "Read ALL topic files"           │
└── ─── PARTIAL OVERLAP ───             └── ─── MACHINE-SPECIFIC ───
```

**Problems:**
1. **Duplication**: CLAUDE.md summarizes rules that memory files detail → they drift apart
2. **Fragility**: CLAUDE.md says "See feedback_X.md" → if memory is missing (new machine), link is broken
3. **Conflict**: CLAUDE.md might say one thing, memory file might say another (no reconciliation)
4. **Loading overhead**: Agent must read CLAUDE.md + MEMORY.md + 60 individual files = 62 Read calls at session start

**The solution:**

```
CLAUDE.md (stable overview, ~200 lines)    brain_v2/agent_rules/ (IN project)
├── Architecture + patterns                 ├── feedback_rules.json
├── Anti-patterns                           │   └── ALL 34 rules with why + how
├── Transaction workflow                    │       (SINGLE FILE, one Read call)
├── "Agent Behavioral Rules:                │
│    See brain_v2/agent_rules/" ──────────→│
│    (one reference, not 30+)              │
└── Ecosystem standards                    │
                                            │
brain_v2/claims/ (IN project)              brain_v2/annotations/ (IN project)
├── claims.json                            ├── annotations.json
│   └── System facts + evidence            │   └── Object-level findings
│   └── Superseded = lessons learned       │   └── Incident links
```

**After alignment:**
- CLAUDE.md is **stable** — only changes when architecture changes (rarely)
- `feedback_rules.json` **grows** — every session can add rules
- NO duplication — CLAUDE.md references, doesn't restate
- **2 Read calls** at session start (CLAUDE.md + feedback_rules.json) instead of 62
- **Portable** — everything is inside the project, git-tracked
- **No conflict** — single source of truth per knowledge type

### 11. How the Three Layers Work Together

**Scenario: New incident comes in — "Payment to vendor X failed"**

```
Step 1: Agent reads text index for context
  Read brain_v2/index/FBZP.md         → payment config, known issues
  Read brain_v2/index/T042I.md        → payment methods, bank selection
  → Agent now has domain context in one turn

Step 2: Agent runs graph algorithm for impact
  $ python -m brain_v2 impact T042I    → BFS with risk decay
  → Shows: T042I → FBZP → T012K → HOUSE_BANK:UBA01 → BCM_RULE:dual_control
  → Agent now knows the full impact chain

Step 3: Agent queries SQL for operational context  
  $ sqlite3 brain_v2_active.db "SELECT * FROM claims WHERE domain='FI' 
    AND confidence IN ('TIER_3','TIER_4','TIER_5')"
  → Shows uncertain facts in FI domain that might be relevant
  
  $ sqlite3 brain_v2_active.db "SELECT * FROM incidents WHERE status='OPEN'"
  → Shows if there are related open incidents

Step 4: Agent discovers something new → persists immediately
  → Adds annotation to annotations.json (object-level finding)
  → Adds claim to claims.json (system-level fact)
  → Both are git-tracked, survive compression AND machine changes
```

**Each layer serves a different cognitive need:**
- **Text index** = context loading (understand the domain)
- **Graph + CLI** = reasoning (trace relationships, find impact)
- **SQLite** = filtering (find specific items by criteria)
- **Source JSON files** = persistence (survive everything)

## Design Principles

### 1. It's for ME (the agent)
I'm text-based with 1M context. Text files = 1 Read call. SQL = 3 steps (write query → Bash → parse output). Graph algorithms (BFS, impact) = CLI tool. Each format for what it does best.

### 2. Portable — no machine dependency
ALL knowledge inside the project directory, git-tracked. Nothing critical in `~/.claude/` only.

### 3. Can't lose it
Irreplaceable knowledge (annotations, claims, feedback rules, project state) = git-tracked source files. Generated artifacts (graph, index, active DB) = rebuildable from source by running scripts.

## Knowledge Architecture (after this session)

```
project/                                    
├── brain_v2/
│   ├── annotations/
│   │   └── annotations.json               # Object findings (IRREPLACEABLE, git)
│   ├── claims/
│   │   └── claims.json                    # System facts with evidence (IRREPLACEABLE, git)
│   ├── agent_rules/
│   │   └── feedback_rules.json            # ALL 34 feedback rules (IRREPLACEABLE, git)
│   │                                       # Migrated FROM ~/.claude/memory/feedback_*.md
│   ├── index/                             # Text object index (REBUILDABLE)
│   │   ├── LHRTSF01.md                    # One file per analyzed object
│   │   └── ...                            # ~200-500 objects
│   ├── output/                            # Generated artifacts (.gitignore, REBUILDABLE)
│   │   ├── brain_v2_graph.json            # NetworkX graph (65MB)
│   │   ├── brain_v2_active.db             # SQLite: pmo, claims, sessions, incidents
│   │   └── brain_v2_index.db              # SQLite index (fast lookups)
│   ├── ingestors/                         # Build scripts (git)
│   ├── queries/                           # Graph algorithms (git)
│   ├── core/                              # Schema + graph engine (git)
│   ├── generate_index.py                  # Text index builder (git)
│   ├── build_active_db.py                 # SQLite builder (git)
│   ├── seed_pmo.py                        # PMO migration script (git)
│   ├── migrate_memory.py                  # One-time: ~/.claude/memory/ → project (git)
│   └── cli.py                             # CLI entry point (git)
│
├── knowledge/domains/                     # Rich domain docs (IRREPLACEABLE, git)
├── extracted_code/                        # 970 ABAP files (IRREPLACEABLE, git)
├── extracted_sap/                         # 162 BSP/UI5 files (IRREPLACEABLE, git)
├── .agents/intelligence/PMO_BRAIN.md      # Pending work (IRREPLACEABLE, git)
└── .agents/rules/                         # Framework rules (git)
```

### Portability matrix

| Knowledge | Source of truth | Git? | On new machine |
|---|---|---|---|
| 34 feedback rules | `brain_v2/agent_rules/feedback_rules.json` | YES | Preserved |
| 11 project state docs | `knowledge/` + PMO_BRAIN.md | YES | Preserved |
| Object annotations (41) | `brain_v2/annotations/annotations.json` | YES | Preserved |
| System claims (~200) | `brain_v2/claims/claims.json` | YES | Preserved |
| Text object index | `brain_v2/index/` | YES | Rebuildable |
| Graph (52K nodes) | `brain_v2/output/` | .gitignore | Rebuild: `python -m brain_v2 build` |
| Active DB (pmo, claims) | `brain_v2/output/` | .gitignore | Rebuild: `python -m brain_v2 active-db` |
| Gold DB (5.3GB) | `Zagentexecution/.../sqlite/` | .gitignore | Re-extract from SAP |
| `~/.claude/memory/` | CACHE only (not source of truth) | NO | Regenerate from project |

### What happens on a new machine?
1. Clone the project → all git-tracked knowledge is there
2. Run `python -m brain_v2 build` → rebuilds graph from extracted code + Gold DB
3. Run `python -m brain_v2 active-db` → rebuilds SQLite from graph + claims.json + PMO
4. Run `python -m brain_v2 index` → rebuilds text index from graph + annotations
5. Agent reads CLAUDE.md + `brain_v2/agent_rules/feedback_rules.json` → behavioral rules restored
6. (Optional) Re-extract Gold DB from SAP if needed

## Approach: 5 Phases

### Phase 0: Save Brain Design Specification (permanent reference)

Before any code changes, persist the design as a durable document at `Brain_Architecture/brain_design_specification_v3.md`.

This is NOT the session plan — it's the **architectural reference** for how the Brain works, why it's hybrid, and how to extend it. Lives in git, survives across sessions and machines.

**Contents:**
- Design principles (agent-optimized, portable, compression-safe)
- Architecture diagram (3 layers: text index + graph + SQL)
- Data models (feedback_rules.json, claims.json, annotations.json, object index format)
- Build pipeline (6 ingestor phases + index + active-db)
- Memory alignment strategy (CLAUDE.md ↔ feedback_rules.json)
- Portability matrix (what's git-tracked, what's rebuildable)
- Evolution rationale (pure SQL → hybrid, and why)
- Future enrichment path (on-demand WBCROSSGT, cross-brain)

**Why v3:** v1 was the original brain (Session #007, progressive disclosure). v2 was Brain v2 (Session #039-042, 52K nodes, impact analysis). v3 is the agent-optimized hybrid (Session #049).

**Mandatory reading rule:** Any session that modifies the Brain (ingestors, schema, annotations, claims, index) MUST read this spec first. Same principle as `lib/README.md` for the SAP framework. This will be added to CLAUDE.md's "Required Reading" section.

### Phase 1: Migrate memory into project (portability fix)

**1a. Migrate 34 feedback rules** (`brain_v2/migrate_memory.py`)
- Read all `~/.claude/.../memory/feedback_*.md` files
- Parse frontmatter (name, description, type) + content
- Write to `brain_v2/agent_rules/feedback_rules.json`:
  ```json
  [
    {
      "id": "feedback_bseg_is_join_not_table",
      "rule": "BSEG is a JOIN via Golden Query, NEVER extract/enrich it",
      "why": "BSEG is not a physical table — it's a cluster...",
      "how_to_apply": "Use bseg_union VIEW instead",
      "created_session": "#035"
    },
    ...
  ]
  ```
- Also keep `~/.claude/memory/` as cache (fast session start loading) — but project file is authoritative

**1b. Verify project state docs exist in project**
- Cross-check 11 `project_*.md` memory files against `knowledge/` docs
- Any knowledge ONLY in memory → copy into `knowledge/` or `brain_v2/claims/`

**1c. Align CLAUDE.md with project-internal rules**
- Today: CLAUDE.md has a summary of rules, memory has details → they drift
- Fix: CLAUDE.md references `brain_v2/agent_rules/feedback_rules.json` as the authoritative source
- CLAUDE.md keeps the overview (architecture, patterns, anti-patterns) — stable, rarely changes
- `feedback_rules.json` keeps the detailed behavioral rules — grows every session
- NO duplication: if a rule is in feedback_rules.json, CLAUDE.md just says "See agent_rules"
- At session start: agent reads CLAUDE.md (overview) + feedback_rules.json (detail) = complete picture, zero conflict

### Phase 2: Fix the graph plumbing

**2a. Fix code_ingestor** — parse 34 SAP_STANDARD files as ABAP_REPORT nodes
**2b. Fix transport_ingestor** — dedup CLASS: vs ABAP_CLASS: nodes
**2c. Rebuild**: `python -m brain_v2 build`

### Phase 3: Build agent access layers

**3a. Text Object Index** (`brain_v2/generate_index.py`)
- One markdown file per analyzed object (~200-500 objects)
- Contains: type, domain, reads/writes, callers, annotations, claims
- I Read these directly — 1 tool call, full context, narrative reasoning

**3b. Claims source file** (`brain_v2/claims/claims.json`)
- Git-tracked, portable, irreplaceable
- Seeded from: annotations (CRITICAL→TIER_1), domain knowledge edges (→TIER_2), session discoveries (→TIER_3)

**3c. SQLite Active DB** (`brain_v2/build_active_db.py`)
- Generated FROM source files (claims.json, PMO_BRAIN.md, session retros)
- 4 tables: pmo_items, claims, sessions, incidents
- For filtering queries only — not source of truth

### Phase 4: Validate

1. `Read brain_v2/index/LHRTSF01.md` → full object context in one call
2. `python -m brain_v2 impact LFA1` → multi-hop chain via graph algorithm
3. `Read brain_v2/agent_rules/feedback_rules.json` → all 34 rules portable
4. SQL: `SELECT * FROM pmo_items WHERE status='OPEN'` → PMO queryable
5. On simulated "new machine": can rebuild everything from git clone + `build`

## Files to Create/Modify

| File | Type | Change |
|------|------|--------|
| `Brain_Architecture/brain_design_specification_v3.md` | NEW | Permanent design spec — architecture, rationale, data models, portability |
| `brain_v2/migrate_memory.py` | NEW | Migrate ~/.claude/memory/ feedback rules → project |
| `brain_v2/agent_rules/feedback_rules.json` | NEW | All 34 feedback rules (git-tracked, portable) |
| `brain_v2/claims/claims.json` | NEW | System-level facts with evidence (git-tracked) |
| `brain_v2/generate_index.py` | NEW | Text object index generator |
| `brain_v2/build_active_db.py` | NEW | SQLite active DB builder (4 tables) |
| `brain_v2/seed_pmo.py` | NEW | PMO_BRAIN.md → SQL migration |
| `brain_v2/ingestors/code_ingestor.py` | MODIFY | Parse SAP_STANDARD files |
| `brain_v2/ingestors/transport_ingestor.py` | MODIFY | Node deduplication |
| `brain_v2/cli.py` | MODIFY | Add `index`, `active-db`, `migrate-memory` commands |

## Future Enrichment (NOT this session)
- WBCROSSGT on-demand queries for specific objects
- Cross-brain SQL queries (PPM↔SAP)
- Historical annotation deep review (200+ annotations from 48 retros)

## Out of Scope
- NO bulk SAP extraction (WBCROSSGT = 200M+ rows)
- NO new code extraction — 1,132 files on disk are the source
- Nodes/edges NOT in SQLite — graph + text index serve this better

## Success Criteria
- [ ] `brain_design_specification_v3.md` saved as permanent reference (Phase 0)
- [ ] `brain_v2/agent_rules/feedback_rules.json` has 34 rules (portable)
- [ ] `brain_v2 build` completes, LHRTSF01 has edges
- [ ] `brain_v2/index/` has 200+ readable object files
- [ ] `brain_v2/output/brain_v2_active.db` has pmo_items, claims, sessions
- [ ] Duplicate CLASS:/ABAP_CLASS: nodes merged
- [ ] All irreplaceable knowledge is git-tracked inside the project
