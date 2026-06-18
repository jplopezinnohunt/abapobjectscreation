---
name: Process Engineering Model (UNESCO SAP — the main objective)
description: The formal model for HOW we discover processes from event data (logs, transactions, jobs) — Signavio/Celonis/van-der-Aalst process mining, applied to SAP ECC. The process map is the OUTPUT of mining, never an input. Validated from Session #008 tool research; persisted Session #079.
type: project
---

# Process Engineering Model

**Main objective of the project.** Process engineering = **discover** how the process actually runs
from event data (logs, transaction data, jobs, change docs). We READ the system and MINE the events;
we do NOT ask for process maps or hardcode them. The map is the OUTPUT.

This is the same science Signavio / Celonis use. We replicate their algorithms with **pm4py**
(open-source, van der Aalst's lineage) over event logs built from the Gold DB.

## 1. The engine (Signavio/Celonis-equivalent algorithms — via pm4py)
| Capability | pm4py | What it gives |
|-----------|-------|---------------|
| **Directly-Follows Graph (DFG)** | `discover_dfg` | the core: A->B transition counts; the process map |
| **Variants** | variant explorer | distinct end-to-end paths + frequency |
| **Process model** | `discover_petri_net_inductive` / heuristics miner | a sound process model (Inductive/Heuristic/Alpha) |
| **Conformance** | `fitness_token_based_replay` / alignments | discovered vs reference (deviations) |
| **Performance/bottlenecks** | `discover_performance_dfg` | time on edges -> cycle time, bottlenecks, rework |
| **Object-centric (OCEL 2.0)** | `discover_ocdfg` | multi-object events (Fund+PO+Invoice+Payment together) |
`pip install pm4py` (pulls networkx, scipy, lxml). Works directly on pandas DataFrames. HTML viz via
GraphvizJS (no system binary). Build `sap_process_discovery.py` with DFG/Inductive/Conformance commands.

## 2. SAP event-log construction (the four columns + the 5 table types)
Event log = {**case_id**, **activity**, **timestamp**, **resource**}.

Berti/van der Aalst (2022) "Event Data Extraction from SAP ERP" — SAP tables are 5 types:
1. **Flow** (VBFA, document flow) — the case chains.
2. **Transaction** (BKPF, RBKP) — financial/business records (events).
3. **Change** (CDHDR/CDPOS) — the audit trail (status/field-change events).
4. **Record** (EKKO, EBAN) — business document headers.
5. **Detail** (EKPO, BSEG) — line items.

Column sourcing on ECC (already in our Gold DB):
- **case_id**: the business object instance. STANDARD link = `bkpf.AWTYP+AWKEY` (FI doc -> originating
  object), `VBFA` (SD flow), `EKBE.VGABE` (MM flow: 1=GR, 2=IR). 1.83M bkpf rows, AWKEY 100% populated.
- **activity**: `bkpf.TCODE` (50), or a `CDHDR`+`CDPOS` change mapped to an activity (copy RWTH
  sap-extractor's 100+ field->activity rules, e.g. EINKBELEG+ME21N -> "Create PO", PROCSTAT='5' ->
  "Release completed"), or a job step.
- **timestamp**: `CPUDT+CPUTM` (entry), `BUDAT` (posting), `CDHDR.UDATE+UTIME`.
- **resource**: `USNAM`, `CDHDR.USERNAME`, job `AUTHCKNAM`.

Use **OCEL 2.0** for cross-process views (one event touches Fund + PO + Invoice + Payment).

## 3. ⭐ STANDARD vs NON-STANDARD processes (user rule, s079)
**The standard linkage rule applies ONLY to STANDARD SAP processes.**
- **Standard processes** (P2P, O2C, FI postings, bank statement, payment run): the case linkage IS
  the standard SAP flow — `AWTYP+AWKEY`, `VBFA`, `EKBE.VGABE`, the standard CDHDR object classes
  (EINKBELEG, VERKBELEG, ...). The 5-table-type model and the activity mappings apply directly.
- **NON-STANDARD / custom processes** (UNESCO Z-flows, the 7 .NET apps via RFC, custom BDC sessions
  like Allos/Y1 payroll, custom workflows YWFI): the standard rule **does NOT apply**. There is no
  AWTYP+AWKEY / VBFA chain to follow. Discover the case linkage from the CUSTOM artifacts: custom Z
  tables + their keys, CDHDR on custom object classes, BDC session logs (APQI/APQD), job chains
  (TBTCO/TBTCP), RFC/IDoc trails, .NET app call logs. Each custom process needs its own case-key
  discovered first, THEN the same pm4py mining applies.
Always classify the process as standard or custom BEFORE choosing the case linkage.

## 4. Proven discovery patterns (reuse before starting from scratch)
1. **Payment E2E**: T042Z -> T042I -> DMEE tree -> BAdI -> FPAYP -> BCM -> bank file (1.4M events).
2. **P2P**: EBAN -> EKKO/EKPO -> EKBE -> ESSR/ESLL -> RBKP/RSEG -> F110 (848K events).
3. **Integration**: RFCDES -> TFDIR -> TBTCO/TBTCP -> EDIDC -> file jobs (COUPA/SWIFT).
4. **Bank statement**: FEBKO -> FEBEP -> FEBRE -> T028A/E -> BKPF/BSIS (223K events).
5. **Code/BAdI trace**: TADIR -> READ REPORT -> regex SELECT/CALL -> DMEE BAdI mapping.
6. **Transport**: E070 -> E071 -> TADIR -> co-change coupling.
The methodology (HOW we discovered) is as valuable as the result. Document each as a reusable pattern.

## 5. Brain integration (the discovered process feeds the spine)
New node types: PROCESS_PATTERN, BOTTLENECK, ANOMALY, CONFORMANCE_GAP. The discovered process feeds
the brain PROCESS spine: STEP -USES_TCODE-> TRANSACTION -EXECUTES_PROGRAM-> PROGRAM -READS-> TABLE,
and -OPERATES_TCODE- USER. The hardcoded process_ingestor PROCESS_DEFINITIONS become DISCOVERED, not declared.

## 6. Status (s079)
- Validated tool research: Session #008 (pm4py, RWTH sap-extractor, Celonis checklist, OCEL 2.0) — STILL VALID.
- Already mined: P2P (848K events), Payment E2E (1.4M events, 550K cases), Bank statement (223K).
- Event data LOCAL in Gold DB (bkpf 1.83M, cdhdr 7.81M, tbtcp_history 85K) — discovery is UNBLOCKED, P01 not required.
- Next: `pip install pm4py`; build `sap_process_discovery.py` (DFG/variants/conformance); extend mining to
  un-mined domains; classify each process standard-vs-custom first; feed results to the brain spine.
