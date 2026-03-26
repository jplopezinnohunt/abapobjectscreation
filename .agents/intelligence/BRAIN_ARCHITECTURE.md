# UNESCO SAP Intelligence — Brain Architecture Design
> How to structure knowledge so the system can REASON, not just store.
> Created: 2026-03-15 (Session #005)

---

## ⭐ FOUNDATIONAL PRINCIPLE: Living Knowledge, Not Static Documents

**Knowledge is NOT static. Skills are NOT static. Conclusions are NOT static.**

The brain must be designed as a **continuously learning system**:

```
STATIC APPROACH (wrong):               LIVING APPROACH (correct):
┌──────────────────────┐               ┌──────────────────────┐
│ Read Word doc once   │               │ Seed with Word doc   │
│ Store as reference   │               │ Analyze first TR     │ → refine
│ Never update         │               │ Analyze 100th TR     │ → refine
│ Same conclusions     │               │ New pattern found    │ → update rules
│ forever              │               │ Exception discovered │ → add edge case
└──────────────────────┘               │ Cross-domain link    │ → new insight
                                       │ Every session        │ → smarter
                                       └──────────────────────┘
```

### Example: Transport Intelligence Skill
The user shared 2 expert Word documents (~1,000 paragraphs) on how to read
and interpret SAP transport orders. These documents contain:
- OBJFUNC semantics, PGMID/OBJECT taxonomy, module-specific risk rules
- Pre-import checklists, artifact detection, number range warnings
- HR payroll PCR risks, PSM FMDERIVE rules, FI T001B dangers

**Static approach:** Store in SKILL.md → reference forever → knowledge never grows.

**Living approach:**
1. SKILL.md contains the initial expert rules (seed knowledge)
2. Each transport analyzed by the agent **feeds back** into the brain:
   - New T030 pattern? → Update FI risk matrix in Graph Brain
   - Found DMEE + T042Z combo? → Add cross-module edge
   - UNESCO-specific custom object type? → Extend the taxonomy
3. Pattern Brain algorithms detect **new patterns** across 7,745 transports:
   - Which users transport the riskiest objects?
   - Which modules have the most OBJFUNC='D' deletions?
   - Are there seasonal patterns (month-end, year-end burst)?
4. Vector Brain enables **semantic search** across all transport knowledge:
   - "Show me transports similar to this one"
   - "What risks do FMDERIVE transports carry?"
5. The skill EVOLVES with each session — new rules, new exceptions, new insights

### How This Applies to ALL Brain Layers
| Layer | Static (wrong) | Living (correct) |
|-------|----------------|-------------------|
| **Document Brain** | Store Word docs once | Update rules with every new finding |
| **Graph Brain** | Fixed node types | Add new node types when discovered |
| **Vector Brain** | One-time index | Re-index when new code/config extracted |
| **Pattern Brain** | Run algorithms once | Run after every new data load, compare to history |
| **Skills** | Write SKILL.md once | Append lessons learned per session |

### The Learning Feedback Loop
```
USER shares expert knowledge (Word docs, conversations)
    ↓
SEED the brain (initial rules, taxonomy, risk matrix)
    ↓
AGENT works (analyzes transports, extracts data, builds code)
    ↓
DISCOVERIES feed back ←───────────────────────────────┐
    ↓                                                   │
UPDATE brain layers (new nodes, edges, embeddings)      │
    ↓                                                   │
PATTERN BRAIN detects trends across all data            │
    ↓                                                   │
NEW INSIGHTS → update SKILL.md → agent gets smarter ───┘
```

### Existing Expert Documents (Seeds for Living Knowledge)
| Document | Size | Location | What It Seeds |
|----------|------|----------|---------------|
| `doc_reference.txt` | 28 KB | mcp-backend-server-python/ | Transport anatomy, OBJFUNC, object types, AI design patterns |
| `doc_supplement.txt` | 31 KB | mcp-backend-server-python/ | HR/PSM/PS/Bank/FI module-specific transport risks |
| `YRGGBS00_SOURCE.txt` | 105 KB | mcp-backend-server-python/ | Substitution exit — L3 derivation rules |
| `YPS8_ALL_METHODS.txt` | 76 KB | mcp-backend-server-python/ | PSM budget control logic — L3 |
| `YCL_FI_ACCOUNT_SUBST_BL_METHODS.txt` | 11 KB | mcp-backend-server-python/ | FI account substitution methods — L3 |

---

## The Problem

We have data, code, config, transports — but they're in **silos**:

```
SQLite (tabular)     Skills (markdown)     sap_brain.py (graph)
  2.4M rows            18 SKILL.md           55 nodes
  structured           procedural            structural
  answers "what"       answers "how"         answers "what connects"
  
  ❌ Can't search by meaning (semantic)
  ❌ Can't detect anomalies automatically
  ❌ Can't trace end-to-end: fund → program → rule → transport
  ❌ Can't answer "why did spending spike in period 10?"
```

---

## The Solution: 4-Layer Brain

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER D: PATTERN BRAIN (Python Algorithms)                  │
│  Anomaly detection, trend analysis, clustering, forecasting  │
│  Input: all three lower layers                               │
│  Output: insights, alerts, recommendations                   │
├─────────────────────────────────────────────────────────────┤
│  LAYER C: VECTOR BRAIN (Semantic Search)                     │
│  ChromaDB / FAISS embeddings                                 │
│  Input: ABAP code, config, field descriptions, skills        │
│  Output: "find similar logic", "what relates to X?"          │
├─────────────────────────────────────────────────────────────┤
│  LAYER B: GRAPH BRAIN (Relationships)                        │
│  Expanded sap_brain.py — nodes + edges + weights             │
│  Input: extracted code, data joins, config dependencies      │
│  Output: impact analysis, dependency chains, critical paths  │
├─────────────────────────────────────────────────────────────┤
│  LAYER A: DOCUMENT BRAIN (Structured Knowledge)              │
│  SQLite + Markdown + Skills                                  │
│  Input: raw SAP data, session learnings, protocols           │
│  Output: queryable facts, procedures, rules                  │
└─────────────────────────────────────────────────────────────┘
```

---

## LAYER A: DOCUMENT BRAIN (What We Have — Enhance)

### Current
- SQLite gold DB (503 MB, 2.4M rows)
- 18 SKILL.md files
- SESSION_LOG, PROJECT_MEMORY, PMO_BRAIN, CAPABILITY_ARCHITECTURE
- LIVE_BRAIN.md, SQLITE_CONTENTS.md

### What to Add
| Addition | Purpose |
|----------|---------|
| **SAP Field Dictionary** | DD03L metadata for every extracted table — field name, type, length, description, domain |
| **Business Rule Catalog** | Extracted OB28 validations + OBBH substitutions in structured format |
| **Report Registry** | Every Z-report in PSM domain: which tables it reads, which rules it applies, what it produces |
| **Enhancement Registry** | Already started — link each ENHO to which fields/tables/rules it modifies |

### Implementation
```python
# New SQLite table: sap_field_dictionary
# Populated via RFC_READ_TABLE on DD03L for each extracted table
CREATE TABLE sap_field_dictionary (
    tabname   TEXT,    -- e.g. FMIFIIT
    fieldname TEXT,    -- e.g. FMBELNR
    position  INTEGER, -- field position
    datatype  TEXT,    -- CHAR, NUMC, CURR, etc.
    leng      INTEGER, -- field length
    decimals  INTEGER,
    keyflag   TEXT,    -- X = key field
    rollname  TEXT,    -- data element
    ddtext    TEXT,    -- field description (from DD04T)
    domname   TEXT,    -- domain
    PRIMARY KEY (tabname, fieldname)
);
-- ~500 rows (75 fields × ~7 tables)
-- This prevents the "wrong field name" problem FOREVER
```

---

## LAYER B: GRAPH BRAIN (Expand sap_brain.py)

### Current: 55 nodes, 66 edges (code objects only)

### Target: ~500+ nodes, ~2000+ edges (code + data + config + transports)

### New Node Types
| Node Type | Source | Example | Count |
|-----------|--------|---------|-------|
| TABLE | DD03L/extracted | FMIFIIT, BKPF, FMFCT | ~30 |
| FIELD | DD03L | FMIFIIT.FMBELNR, FMIFIIT.FONDS | ~200 |
| FUND_AREA | funds table | UNES, IBE, ICTP... | 7 |
| FUND | funds table | AAFRA2023, 125GEF0000 | top 100 |
| FUND_CENTER | fund_centers | CAP, ADM, OPS... | 50 |
| VALIDATION | OB28 | "Fund X → only GL account Y" | ~20 |
| SUBSTITUTION | OBBH/GGB1 | "Derive PRCTR from FISTL" | ~20 |
| REPORT | TADIR PROG | ZFMRP001, ZFMRP002... | ~50 |
| ENHANCEMENT | ENHO | ZHCM_OFFBOARD_EXIT... | 11 |
| TRANSPORT | E070 | D01K9B01A5 | top 100 |
| CONFIG_TABLE | YTFM_* | YTFM_FUND_CPL rules | ~10 |

### New Edge Types
| Edge Type | From → To | Meaning |
|-----------|-----------|---------|
| READS_TABLE | Report → Table | Report uses this table in SELECT |
| JOINS_VIA | Table.Field → Table.Field | Data join relationship |
| VALIDATES | Validation → Field | This rule checks this field |
| SUBSTITUTES | Substitution → Field | This rule derives this field |
| MODIFIES | Enhancement → Report/Class | Enhancement changes behavior |
| TRANSPORTS | Transport → Object | Transport moves this object |
| BELONGS_TO | Fund → Fund_Area | Organizational hierarchy |
| POSTS_TO | Fund → GL Account | Spending relationship |
| FILTERED_BY | Report → Config_Table | Report uses this Z-table for filtering |

### Implementation
```python
# Extend sap_brain.py with data-driven node generation
def build_data_graph(db_path):
    """Generate graph nodes from SQLite data patterns."""
    db = sqlite3.connect(db_path)
    
    # Table → Table joins (discovered from extracted data)
    joins = [
        ("FMIFIIT", "FONDS", "FMFCT", "FINCODE", "JOINS_VIA"),
        ("FMIFIIT", "FISTL", "FMFCTR", "FICTR", "JOINS_VIA"),
        ("FMIFIIT", "KNBELNR", "BKPF", "BELNR", "JOINS_VIA"),
        ("PRPS", "PSPHI", "PROJ", "PSPNR", "JOINS_VIA"),
    ]
    
    # Fund areas as organizational nodes
    for area in db.execute("SELECT DISTINCT FIKRS FROM fmifiit_full"):
        add_node("FUND_AREA", area[0])
    
    # Top funds by transaction volume
    for row in db.execute("""
        SELECT FONDS, COUNT(*) as cnt 
        FROM fmifiit_full 
        GROUP BY FONDS ORDER BY cnt DESC LIMIT 100
    """):
        add_node("FUND", row[0])
        add_edge(row[0], "BELONGS_TO", get_fund_area(row[0]))
```

---

## LAYER C: VECTOR BRAIN (Semantic Search)

### Purpose
Enable natural language queries across ALL knowledge:
- "Find programs that filter by fund area"
- "What logic is similar to the offboarding validation?"
- "Which enhancements affect FM posting?"

### Technology
```
ChromaDB (local, no server needed)
  + sentence-transformers (all-MiniLM-L6-v2 for code)
  + Optional: CodeBERT for ABAP-specific embeddings
```

### What to Embed
| Collection | Content | Estimated Docs | Chunk Size |
|-----------|---------|---------------|------------|
| `abap_code` | ABAP source from extracted_sap/ | ~200 methods | per method |
| `abap_reports` | PSM/FM Z-report source code | ~50 programs | per subroutine |
| `skill_knowledge` | SKILL.md files | 18 skills | per section |
| `session_learnings` | SESSION_LOG entries | ~20 entries | per discovery |
| `field_descriptions` | DD03L+DD04T field descriptions | ~500 fields | per field |
| `transport_descriptions` | E070 as4text transport descriptions | 7,745 | per transport |
| `enhancement_logic` | ENHO extracted code | 11 enhancements | per exit method |
| `config_rules` | Validation/Substitution definitions | ~40 rules | per rule |
| `report_analysis` | Report → table → rule mappings | ~50 reports | per report |

### Implementation
```python
# brain/vector_brain.py
import chromadb
from sentence_transformers import SentenceTransformer

class VectorBrain:
    def __init__(self, persist_dir="brain/vector_store"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def index_abap_code(self, source_dir):
        """Index all extracted ABAP source code."""
        collection = self.client.get_or_create_collection("abap_code")
        for filepath in glob.glob(f"{source_dir}/**/*.abap", recursive=True):
            methods = parse_abap_methods(filepath)
            for method in methods:
                embedding = self.model.encode(method['source'])
                collection.add(
                    ids=[f"{filepath}:{method['name']}"],
                    embeddings=[embedding.tolist()],
                    documents=[method['source']],
                    metadatas=[{
                        "class": method.get('class',''),
                        "tables_read": ','.join(method.get('tables',[])),
                        "domain": method.get('domain',''),
                    }]
                )
    
    def search(self, query, collection_name="abap_code", n=5):
        """Semantic search across indexed knowledge."""
        collection = self.client.get_collection(collection_name)
        results = collection.query(
            query_embeddings=[self.model.encode(query).tolist()],
            n_results=n
        )
        return results
    
    # Usage:
    # brain = VectorBrain()
    # brain.search("fund area validation logic")
    # brain.search("profit center derivation from fund center")
    # brain.search("offboarding step approval workflow")
```

---

## LAYER D: PATTERN BRAIN (Python Algorithms)

### Purpose
Automatically analyze extracted data to discover patterns, anomalies, trends,
and behavioral insights that humans would miss.

### Algorithm Categories

#### D1: Anomaly Detection (Spending Patterns)
```python
# Find unusual spending per fund/period
from scipy import stats
import pandas as pd

def detect_spending_anomalies(db_path, year='2025', zscore_threshold=3.0):
    """Flag funds with unusual spending in any period."""
    db = sqlite3.connect(db_path)
    df = pd.read_sql("""
        SELECT FONDS, PERIO, COUNT(*) as doc_count,
               SUM(CAST(REPLACE(FKBTR,'-','') AS REAL)) as abs_amount
        FROM fmifiit_full
        WHERE FIKRS='UNES' AND GJAHR=?
        GROUP BY FONDS, PERIO
    """, db, params=[year])
    
    # Z-score per fund across periods
    anomalies = []
    for fund in df['FONDS'].unique():
        fund_data = df[df['FONDS']==fund]
        if len(fund_data) >= 3:  # need enough periods
            z = stats.zscore(fund_data['abs_amount'])
            for i, score in enumerate(z):
                if abs(score) > zscore_threshold:
                    anomalies.append({
                        'fund': fund,
                        'period': fund_data.iloc[i]['PERIO'],
                        'amount': fund_data.iloc[i]['abs_amount'],
                        'zscore': score,
                        'type': 'spike' if score > 0 else 'drop'
                    })
    return pd.DataFrame(anomalies).sort_values('zscore', ascending=False)
```

#### D2: Posting Pattern Clustering
```python
# Cluster funds by posting behavior (which GL accounts, which periods)
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def cluster_fund_behaviors(db_path, n_clusters=8):
    """Group funds by similar posting patterns."""
    db = sqlite3.connect(db_path)
    # Feature matrix: each fund × 16 periods (doc count per period)
    df = pd.read_sql("""
        SELECT FONDS, PERIO, COUNT(*) as cnt
        FROM fmifiit_full 
        WHERE FIKRS='UNES' AND GJAHR='2025'
        GROUP BY FONDS, PERIO
    """, db)
    pivot = df.pivot(index='FONDS', columns='PERIO', values='cnt').fillna(0)
    
    scaler = StandardScaler()
    X = scaler.fit_transform(pivot)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    pivot['cluster'] = kmeans.fit_predict(X)
    
    # Each cluster = a behavioral archetype
    # "steady monthly spenders" vs "year-end burst" vs "quarterly batch"
    return pivot
```

#### D3: Network Analysis (Fund Flow)
```python
# Build a network: Fund → GL Account → Cost Center
import networkx as nx

def build_spending_network(db_path, year='2025'):
    """Create a directed graph of money flow."""
    db = sqlite3.connect(db_path)
    G = nx.DiGraph()
    
    # Fund → GL Account edges (weighted by doc count)
    for row in db.execute("""
        SELECT FONDS, HKONT, COUNT(*) as weight
        FROM fmifiit_full
        WHERE FIKRS='UNES' AND GJAHR=? AND HKONT!=''
        GROUP BY FONDS, HKONT
    """, [year]):
        G.add_edge(f"FUND:{row[0]}", f"GL:{row[1]}", weight=row[2])
    
    # Fund → Fund Center edges
    for row in db.execute("""
        SELECT FONDS, FISTL, COUNT(*) as weight
        FROM fmifiit_full
        WHERE FIKRS='UNES' AND GJAHR=? AND FISTL!=''
        GROUP BY FONDS, FISTL
    """, [year]):
        G.add_edge(f"FUND:{row[0]}", f"FC:{row[1]}", weight=row[2])
    
    # Key metrics
    print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    
    # Central nodes = most connected funds/accounts
    centrality = nx.degree_centrality(G)
    top = sorted(centrality.items(), key=lambda x: -x[1])[:20]
    
    return G, top
```

#### D4: Temporal Trend Analysis
```python
def spending_velocity(db_path, fund, years=['2024','2025','2026']):
    """Compare spending velocity across years for a fund."""
    db = sqlite3.connect(db_path)
    result = {}
    for year in years:
        df = pd.read_sql("""
            SELECT PERIO, COUNT(*) as docs,
                   SUM(CAST(REPLACE(FKBTR,'-','') AS REAL)) as amount
            FROM fmifiit_full
            WHERE FONDS=? AND GJAHR=?
            GROUP BY PERIO ORDER BY PERIO
        """, db, params=[fund, year])
        df['cumulative'] = df['amount'].cumsum()
        result[year] = df
    return result
    # Compare: is 2025 spending faster than 2024?
    # Alert if cumulative at period 6 exceeds full-year 2024
```

#### D5: Cross-Table Pattern Discovery
```python
def discover_data_relationships(db_path):
    """Find unexpected correlations between tables."""
    db = sqlite3.connect(db_path)
    
    # Funds in FMIFIIT but NOT in funds master
    orphans = db.execute("""
        SELECT DISTINCT f.FONDS 
        FROM fmifiit_full f
        LEFT JOIN funds fd ON f.FIKRS=fd.FIKRS AND f.FONDS=fd.FINCODE
        WHERE fd.FINCODE IS NULL AND f.FONDS!=''
    """).fetchall()
    
    # WBS elements posting to unexpected fund areas
    # Grants with spending but no budget allocation
    # Fund centers with transactions but no master record
    
    return {'orphan_funds': orphans}
```

---

## EXPERT SKILLS TO ADD (Per Layer)

| Layer | New Skill | Purpose | Priority |
|-------|-----------|---------|----------|
| L2 | `sap_data_extraction` | DD03L-first protocol, RFC_READ_TABLE patterns, auto-load SQLite | 🔴 Critical |
| L2+D | `sap_pattern_analysis` | Python algorithms for anomaly detection, clustering, network analysis on extracted data | 🟡 High |
| L3 | `sap_validation_extraction` | Programmatically extract OB28, OBBH, GGB0/1, FMDERIVE rules from SAP via RFC | 🟡 High |
| L3 | `sap_report_analysis` | Reverse-engineer Z-reports to understand which tables + rules + filters they combine | 🟡 High |
| Cross | `sap_vector_intelligence` | ChromaDB setup, embedding strategy, semantic search across all knowledge | 🟢 Backlog |

---

## IMPLEMENTATION ROADMAP

### Phase 1: Foundation ✅ DONE (Session #006 — 2026-03-15)
```
✅ Brain redesigned: 5 sources, 18 node types, 17 edge types
✅ 739 nodes (was 55), 524 edges (was 66) — 13x growth
✅ Sources: code objects + SQLite (502MB) + knowledge docs + skills + expert seeds
✅ Funds (300), Fund Areas (7), Fund Centers (100), Transports (200) now in graph
✅ Knowledge docs (45) and Skills (18) cross-referenced to code objects
✅ HTML visualization regenerated with 17-color type legend
Remaining from Phase 1:
  - Create sap_data_extraction SKILL.md
  - sap_field_dictionary in SQLite (DD03L for all tables)
  - Run BKPF/BSEG extraction
  - First pattern analysis script (anomaly detection on FMIFIIT)
```

### Phase 2: Graph Expansion (Sessions 7-8)
```
5. Add JOINS_VIA edges from verified data relationships (FMIFIIT.FONDS → funds.FINCODE)
6. Extract OB28/OBBH validation/substitution rules → VALIDATION/SUBSTITUTION nodes
7. Build report registry (which Z-reports read which tables)
8. Ingest tadir_enrichment table → enrich CLASS/REPORT nodes with transport history
```

### Phase 3: Vector Brain (Sessions 9-10)
```
9. Install ChromaDB + sentence-transformers
10. Index extracted ABAP code, skills, session learnings
11. Index field descriptions from DD03L/DD04T
12. Build semantic search CLI: `python brain/vector_brain.py --search "fund validation"`
```

### Phase 4: Pattern Intelligence (Sessions 11+)
```
13. Full anomaly detection pipeline on FMIFIIT
14. Fund behavior clustering
15. Spending network analysis (fund → GL → cost center)
16. Temporal trend comparison (year-over-year velocity)
17. Cross-table relationship discovery
18. Report → rule → table impact chain
```

---

## TECHNOLOGY STACK

| Component | Technology | Why |
|-----------|-----------|-----|
| Document Brain | SQLite + Markdown | Already in place, proven |
| Graph Brain | networkx + sap_brain.py | Python native, no server needed |
| Vector Brain | ChromaDB (persistent local) | No server, pip install, SQL-like API |
| Embeddings | sentence-transformers (MiniLM) | Small model, runs on CPU, good for code |
| Pattern Analysis | pandas + scipy + sklearn | Standard data science stack |
| Visualization | plotly or matplotlib → HTML | Single-file output, sharable |

### Dependencies to Install
```bash
pip install chromadb sentence-transformers networkx scipy scikit-learn pandas plotly
```
All run locally. No external APIs. No cloud. Everything stays on the machine.

---

## THE END STATE

When all 4 brain layers are active:

```
USER: "Why did fund AAFRA2023 spike in period 10?"

PATTERN BRAIN (D):
  → Anomaly detected: AAFRA2023 period 10 has z-score 4.2 (spike)
  → Cluster: this fund is in the "year-end adjustment" group

VECTOR BRAIN (C):
  → Similar patterns found in funds AAFRA2022, BBFRA2023
  → Related ABAP code: ZFMRP_YEAREND_ADJUST uses FMIFIIT + YTFM_FUND_CPL

GRAPH BRAIN (B):
  → AAFRA2023 posts to GL accounts 400100, 400200 (via HKONT)
  → These GL accounts → validation rule OB28#015 (max amount check)
  → Transport D01K9C02A1 modified this validation 2025-09-15

DOCUMENT BRAIN (A):
  → Fund AAFRA2023 type=100, created 2023-12-11 by C_LEROY
  → YTFM_FUND_CPL: NONIBF=X (non-institutional budget fund)
  → Session #005: FMIFIIT period 10 had 80,366 rows (vs avg 70K)

SYNTHESIS: Period 10 spike caused by year-end adjustments in a
non-IBF fund, following the same pattern as AAFRA2022. The validation
rule OB28#015 was relaxed in transport D01K9C02A1 in September,
allowing larger postings through.
```

**That's what the brain should do — not just store, but REASON.**
