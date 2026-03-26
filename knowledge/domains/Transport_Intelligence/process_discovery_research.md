# Process Discovery Research — Tools, Repos & Integration Plan

Source: Session #008 research (2026-03-15)

## Conclusion

Process discovery is NOT a layer — it's a **transversal engine** that feeds ALL layers. The HTML dashboard is just one output. The real value is **discovered patterns** (flows, bottlenecks, anomalies, conformance gaps) that become nodes in the brain, signals in transport intelligence, and actionable insights for domain agents.

Current state: we have data (2M+ FMIFIIT, 7,745 transports, 500+ BDC sessions) but almost zero algorithms. Only rule-based classification and counting. No real mining.

## Repos Investigated — What to Copy

### 1. pm4py (process-intelligence-solutions/pm4py)
**Verdict: INSTALL AND USE DIRECTLY**

- 26 discovery algorithms: DFG, Inductive Miner, Heuristic Miner, Alpha, ILP, Genetic, OCEL-specific
- Works directly with pandas DataFrames — no conversion needed
- OCEL 2.0 support: object-centric event logs (Fund+PO+Invoice in same event)
- HTML visualization WITHOUT graphviz system binary (uses GraphvizJS in browser)
- Conformance checking: token-based replay + alignment-based
- Performance DFG: time annotations on edges for bottleneck detection
- Temporal profile: expected vs actual timing between activity pairs
- `pip install pm4py` pulls in: networkx, scipy, matplotlib, lxml, tqdm

**Key API:**
```python
import pm4py
# DFG
dfg, sa, ea = pm4py.discover_dfg(df, case_id_key='case_id', activity_key='activity', timestamp_key='timestamp')
# Inductive Miner → Petri Net
net, im, fm = pm4py.discover_petri_net_inductive(df, ...)
# Conformance
fitness = pm4py.fitness_token_based_replay(df, net, im, fm, ...)
# Performance bottlenecks
perf_dfg, sa, ea = pm4py.discover_performance_dfg(df, ..., perf_aggregation_key='mean')
# OCEL
ocel = OCEL(events=events_df, objects=objects_df, relations=relations_df)
ocdfg = pm4py.discover_ocdfg(ocel)
```

### 2. Javert899/sap-extractor (RWTH Aachen — van der Aalst's group)
**Verdict: COPY MAPPING TABLES AND PATTERNS**

Best source for SAP process mining. Key assets to copy:

**CDHDR/CDPOS field→activity mapping** (100+ rules):
- OBJECTCLAS='EINKBELEG', TCODE='ME21N' → "Create Purchase Order"
- OBJECTCLAS='EINKBELEG', TCODE='ME29N' → "Release Purchase Order"
- PROCSTAT field value '5' → "Release completed"
- KEY + EKKO + chngind='I' → "Update Purchase Order"

**P2P table join pattern** (NetworkX directed graph):
```
EBAN (PR) → EKKO (PO header) → EKPO (PO item) → EKBE (PO history)
  ↓ VGABE='1'                    ↓ VGABE='2'
Goods Receipt                  Invoice Receipt
  ↓                              ↓
RBKP/RSEG (Invoice Verification)
  ↓
BKPF/BSEG (FI posting)
  ↓
BSAK (Cleared vendor items = Payment)
```

**Event log schema**: `event_timestamp`, `event_activity`, `event_USERNAME`, `event_node` (table_docnumber), `RELATED_DOCUMENTS`

### 3. RWTH oc-process-discovery (marcoheinisch)
**Verdict: COPY OCEL CONSTRUCTION PATTERN**

- Uses pyrfc + RFC_READ_TABLE (same as us)
- DataFrame→OCEL transformation pattern reusable
- VBTYP 40+ document type dictionary (SD doc flow types)
- Only extracts 3000 rows (no pagination) — we do this better
- OCEL 1.0 only — we should use OCEL 2.0 (pm4py supports it)
- CDPOS defined but never actually used — we should use it

**Key paper**: Berti, Park, Rafiei, van der Aalst — "An Event Data Extraction Approach from SAP ERP for Process Mining" (2022). Classifies SAP tables into 5 types:
1. **Flow** tables (VBFA) — document chains
2. **Transaction** tables (RBKP, BKPF) — financial records
3. **Change** tables (CDHDR/CDPOS) — audit trail
4. **Record** tables (EKKO, EBAN) — business documents
5. **Detail** tables (EKPO, BSEG) — line items

### 4. abaplint (larshp/abaplint)
**Verdict: INSTALL FOR CODE ANALYSIS**

- Complete ABAP parser in TypeScript — 5-stage: lexer → statements → structures → file info → semantic
- 178 rules, 128 work on single files (our extracted .abap files)
- Key rules: `db_operation_in_loop`, `check_subrc`, `dangerous_statement`, `method_length`, `nesting`, `commented_code`, `unused_variables`, `call_transaction_authority_check`
- `npm install -g @abaplint/cli`
- Can run programmatically via `@abaplint/core` for AST extraction (call graphs, table refs)

### 5. Celonis Extraction Reference
**Verdict: USE AS TABLE CHECKLIST**

Tables Celonis extracts (our pyrfc can do the same):

**P2P**: EBAN, EKKO, EKPO, EKPA, EKET, EKBE, RBKP, RSEG, BKPF, BSEG, MSEG, CDHDR, CDPOS, LFA1, T024, T161T, T001
**O2C**: VBAK, VBAP, VBEP, VBFA, VBUK, VBUP, LIKP, LIPS, VBRK, VBRP, BKPF, BSAD, BSID, CDHDR, CDPOS, KNA1

Celonis deploys ABAP transport `/CELONIS/DATA_EXTRACTION` with RFC FM and background jobs. We replicate with pyrfc without needing their transport.

### 6. abapOpenChecks + code-pal-for-abap-cloud
**Verdict: NOT USABLE** — both require in-system ATC/SCI runtime. abaplint IS the outside-SAP evolution of abapOpenChecks.

### 7. aws-lambda-sap-odp-extractor
**Verdict: DELTA PATTERN USEFUL, REST ARCHIVED**

Archived repo. Uses OData/HTTP to SAP ODP layer (needs NW 7.5+). The **delta state machine pattern** (InitLoading→InitLoaded→DeltaLoading tracked in DynamoDB/SQLite) is worth copying for incremental extraction.

## Key Gaps in Our Codebase

| Gap | What's Missing | How to Fill |
|-----|---------------|-------------|
| **CDHDR/CDPOS** | Zero references — biggest audit gap | Extract via pyrfc, use sap-extractor mappings |
| **SWEL** (Workflow events) | Completely unexplored | Extract SWI1/SWEL tables |
| **Real algorithms** | Only counting/classification | pm4py: DFG, Inductive, Heuristic, Conformance |
| **OCEL** | No multi-object event logs | pm4py OCEL 2.0 for B2R/P2P |
| **Code quality analysis** | Manual reading only | abaplint on extracted .abap files |
| **Temporal analysis** | No timing patterns | pm4py temporal profile + performance DFG |

## Consolidated Implementation Plan

### Phase 1 — Quick Wins (existing data)
1. `pip install pm4py`
2. Build `sap_process_discovery.py` with DFG/Inductive/Conformance commands
3. Run on CTS event log (7,745 transports → DFG, variants, bottlenecks)
4. Run on FMIFIIT (2M rows → fund lifecycle: commit→obligation→expenditure)
5. Output: JSON patterns for brain integration

### Phase 2 — CDHDR/CDPOS Extraction
1. Build `extract_cdhdr.py` (pyrfc to D01)
2. Copy sap-extractor's activity mapping (100+ rules)
3. Target: EINKBELEG, VERKBELEG, LIEFERUNG, MATERIAL, BANF, FM objects
4. Store in SQLite gold DB

### Phase 3 — UNESCO Process Mining
1. B2R event log: FONDS as case ID, WRTTP-mapped activities
2. P2P event log: EBELN as case ID (after EKKO/EKPO extraction)
3. OCEL 2.0 for cross-process view (Fund+PO+Invoice+Payment)
4. Conformance checking vs expected UNESCO processes

### Phase 4 — Brain Integration + Code Analysis
1. New brain node types: PROCESS_PATTERN, BOTTLENECK, ANOMALY, CONFORMANCE_GAP
2. SOURCE 7 in sap_brain.py: process discovery patterns
3. abaplint on extracted_code/ and extracted_sap/
4. CODE_QUALITY nodes in brain

## Cross-Layer Impact

| Layer | What Process Discovery Adds |
|-------|---------------------------|
| L3 (Brain) | PROCESS_PATTERN, BOTTLENECK, ANOMALY nodes from mining |
| L5 (Transport Intel) | Conformance: does this transport follow normal promotion flow? |
| L7 (Process Intel) | Real DFG/Petri nets for B2R, P2P, H2R from actual data |
| Domain Agents | "Fund X deviates from normal B2R pattern" — actionable insight |
| Code Analysis | abaplint AST + quality rules on 59 extracted code objects |
| Data Extraction | CDHDR/CDPOS adds config change audit trail to gold DB |
