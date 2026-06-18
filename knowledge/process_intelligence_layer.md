---
name: Process Intelligence Layer (L7) — commercial-grade architecture
description: The first-class Process Intelligence layer. Operationalizes process mining (van der Aalst) over SAP ECC into a commercial product. Core = deterministic, auditable mining (pm4py, OCEL 2.0); the brain IS the Process Intelligence Graph; Claude is the agentic reasoning/action layer. Re-evaluated against Signavio/Celonis/LLM-PM state of the art (2026). Persisted Session #079.
type: project
---

# Process Intelligence Layer (Capability Layer L7)

**Terminology (confirmed):** the technique is **process mining** (discovery + conformance +
enhancement from event logs — van der Aalst). The **layer/product** is **Process Intelligence** =
process mining + AI reasoning + orchestration/action. "Process engineering" is the broader umbrella.

**Why this is now a LAYER:** the Session #008 research (pm4py, RWTH sap-extractor, OCEL) was a plan we
never operationalized. This makes it a first-class, productized capability layer. The objective is a
**commercial product** — so it must be solid, auditable, and differentiated.

## State of the art re-evaluated (2026) — what we take
| Source | What they do (2026) | What we take |
|--------|--------------------|--------------|
| **SAP Signavio** | Object-Centric Process Mining (OCPM); object-centric clustering ("spaghetti -> structure") | Go object-centric (OCEL 2.0), not case-centric |
| **Celonis** | Process Intelligence Graph = "dynamic, system-agnostic digital twin"; first **MCP server** to feed AI agents; **Orchestration Engine** (agents+people+systems); **LLM for PQL** (NL->query); Gartner PI Leader 2026 | The brain IS our PI Graph; expose it via MCP to agents; NL->query; orchestrate actions |
| **LLM+PM research** | LLMs for event-log extraction (ExOAR), object-centric analysis (GPT-4 strong), conversational PM, NL->DB-query; "Agentic AI Process Observability" | LLM extracts/labels activities + conversational layer — but NOT the mining itself |
| **Anthropic (Building Effective Agents)** | workflows (predefined paths) vs agents (dynamic); orchestrator-worker; evaluator-optimizer; start simple; **tracing/observability** | The agentic layer design + observability; deterministic core, agentic edges |

**Our differentiator (CP-001/002/003):** the mining engine is **deterministic and fully traceable**
(pm4py + networkx, evidence path:line) — NOT a black box. Competitors bolt AI on top of opaque
pipelines; we have an **auditable** process graph where every edge has provenance. That is the
trust moat for a commercial product (audit, compliance, public sector).

## The architecture — 5 components

### 1. Event Log Builder  (the hard, SAP-specific part)
Turns SAP data into an **object-centric event log (OCEL 2.0)**. Uses the 5 SAP table types
(Berti/van der Aalst 2022): Flow (VBFA), Transaction (BKPF/RBKP), Change (CDHDR/CDPOS),
Record (EKKO/EBAN), Detail (EKPO/BSEG). Columns: case/object, activity, timestamp, resource.
- **Standard processes:** case linkage = standard SAP flow — `bkpf.AWTYP+AWKEY`, `VBFA`,
  `EKBE.VGABE`, standard CDHDR object classes. Activity mapping from RWTH sap-extractor (100+ rules).
- **NON-standard / custom processes** (Z-flows, 7 .NET apps, custom BDC Allos/Y1, YWFI workflows):
  the standard rule does NOT apply — discover the case-key from custom artifacts first (Z tables+keys,
  CDHDR on custom classes, BDC logs APQI/APQD, job chains, RFC/IDoc), THEN mine. **Classify
  standard-vs-custom BEFORE choosing the linkage** (user rule, s079).
- Object-centric: one event touches multiple objects (Fund + PO + Invoice + Payment) — OCEL 2.0,
  the 2026 frontier, and natural for SAP via AWTYP+AWKEY.

### 2. Mining Engine — DETERMINISTIC (pm4py), auditable
- **Discovery**: DFG (directly-follows graph), object-centric DFG (OCDFG), Inductive/Heuristic miner.
- **Variants**: distinct end-to-end paths + frequency (the "spaghetti -> structure" view).
- **Conformance**: token replay / alignments — discovered vs reference (deviations, rework, SoD breaks).
- **Performance**: time-annotated DFG -> cycle time, bottlenecks, temporal profiles.
- Output is data, not opinion. Every finding carries its event evidence.

### 3. Process Intelligence Graph = the BRAIN  (we already have it)
Discovered artifacts become first-class graph nodes/edges: `PROCESS_PATTERN`, `VARIANT`,
`BOTTLENECK`, `ANOMALY`, `CONFORMANCE_GAP`. They connect to the existing spine:
STEP -USES_TCODE-> TRANSACTION -EXECUTES_PROGRAM-> PROGRAM -READS-> TABLE, and -OPERATES_TCODE- USER.
Celonis builds a separate "digital twin graph"; ours is the brain — discovered processes live next to
the code/config/data/users they touch. This is the unification competitors lack.

### 4. Agentic Reasoning & Action Layer = Claude  (how Anthropic works)
The DETERMINISTIC results go IN; reasoning/explanation/action come OUT. Claude:
- **Interprets** variants/bottlenecks ("why is this path slow / non-conformant?") with the graph context.
- **Conversational**: NL questions over the process ("show payment runs that skipped approval") ->
  generates the deterministic query (our equivalent of Celonis LLM-for-PQL).
- **Root-cause**: traverses the brain (process -> exit -> config -> incident) to explain deviations.
- **Acts/orchestrates** (workflow vs agent, per Anthropic): recommend, and where safe, trigger
  remediation — under the safety rules (no autonomous side-effects without confirmation).
- The LLM NEVER does the mining (that stays deterministic/auditable). It reasons over and acts on it.
- **Observability**: trace every agent decision (Anthropic guidance) — fits CP-001 traceability.

### 5. Product surface
- **Dashboards** — existing `companions/process-intelligence.html` + the mined DFG/variants/KPIs.
- **Conversational** — Claude over the PI Graph.
- **MCP server** — expose the PI Graph to external AI agents (Celonis shipped this in 2025; we have the brain + MCP already).

## Mapping to our existing assets (most of the layer already exists)
| Component | We have | Gap |
|-----------|---------|-----|
| Event data | bkpf 1.83M (AWKEY 100%), cdhdr 7.81M, tbtcp_history 85K, doc-flow tables | CDHDR/CDPOS activity mapping; OCEL builder |
| Mining engine | partial (counting/rule-based; P2P/Payment mined manually) | `pip install pm4py`; real DFG/conformance/OCDFG |
| PI Graph | the brain (55K nodes, the spine) | PROCESS_PATTERN/BOTTLENECK/ANOMALY node types + ingestion |
| Agentic layer | Claude + brain + MCP | NL->query, conformance reasoning, action orchestration |
| Product surface | process-intelligence.html, companions | productize: multi-tenant, conversational |

## Implementation phases (commercial-grade)
1. **pm4py engine** — `sap_process_discovery.py`: DFG / OCDFG / variants / conformance / performance.
2. **OCEL builder** — event log from bkpf AWTYP+AWKEY + cdhdr (standard) + custom case-keys; OCEL 2.0.
3. **Brain integration** — new node types; discovered processes feed the spine (process_ingestor becomes DISCOVERED, not hardcoded).
4. **Agentic layer** — NL->query, conformance/root-cause reasoning, observability/tracing.
5. **Productize** — MCP for agents, conversational UI, multi-tenant, audit trail.

## Why it wins commercially
Deterministic + auditable (trust/compliance, esp. public sector) · object-centric (2026 frontier) ·
the brain unifies process + code + config + data + people (competitors keep these separate) · Claude
as the reasoning/action layer with full traceability. The moat is **auditability**: every process
finding is provable to its events — not an opaque AI claim.
