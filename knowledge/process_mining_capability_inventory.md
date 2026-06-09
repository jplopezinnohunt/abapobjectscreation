---
name: Process Mining Capability Inventory — ALL solutions, what we DON'T use (adoption backlog)
description: PHASE 1. Exhaustive inventory of every process-mining capability/algorithm/tool/technique across ALL solutions (Celonis, SAP Signavio, UiPath, Apromore, LANA, mindzie, Software AG/ARIS, Fluxicon Disco, ProM, pm4py, ocpa, academic), mapped to our status (HAVE/PARTIAL/NONE) and adoption priority. The point is to bring in everything we are NOT using. Persisted s079.
type: project
---

# Process Mining Capability Inventory — what we DON'T use yet (adoption backlog)

PHASE 1 (per user): analyze ALL process-mining solutions, bring what we don't use. PHASE 2 (later):
build the Public Sector solution on our reality. This doc = the complete adoption backlog.
Status: HAVE / PARTIAL / NONE. (Running research w7owt1ec3 + prior research feed this; update on return.)

## A. DISCOVERY algorithms (mine a model from the log)
| Algorithm | What it adds | Tool | Status |
|-----------|-------------|------|--------|
| Directly-Follows Graph (DFG) | the basic process map | pm4py | **HAVE** |
| Inductive Miner | sound, block-structured model (Petri net/process tree) | pm4py | NONE |
| Heuristic Miner | frequency/threshold-robust model, handles noise | pm4py | NONE |
| Alpha / Alpha+ | classic baseline | pm4py | NONE |
| Split Miner / ILP / Genetic | precision/fitness-balanced models | pm4py/academic | NONE |
| Fuzzy Miner | simplify "spaghetti" (abstraction by significance) | Disco/ProM | NONE |
| **Object-Centric Petri Net (OCPN) discovery** | the real OCPM model (multi-object) | ocpa | NONE |
| Process trees / hierarchical | structured, repairable models | pm4py | NONE |

## B. CONFORMANCE (compare reality vs a model)
| Capability | Adds | Status |
|-----------|------|--------|
| Token-based replay | fitness, where the log violates the model | NONE |
| Alignments | optimal deviation diagnosis (insert/skip) | NONE |
| Footprint / behavioral comparison | matrix-level conformance | NONE |
| **Object-centric conformance** | conformance over OCEL | NONE |
| Rule/constraint conformance (Declare) | declarative rule violations (SoD, "A before B") | NONE |
→ This is the WHOLE "as-implemented vs as-delivered / custom-over-standard" overlay. Biggest analysis gap.

## C. PERFORMANCE & time
| Capability | Adds | Status |
|-----------|------|--------|
| Performance DFG (mean/median edge times) | bottlenecks | **PARTIAL** (built, but no incomplete-case filter -> reported artifacts) |
| Performance spectrum | flow/batching/overtaking patterns over time | NONE |
| Temporal profile | expected vs actual time per activity pair (anomalies) | NONE |
| Sojourn/waiting vs service time split | where time is lost (wait vs work) | NONE |
| SLA / due-date analysis | on-time, deadline breaches | NONE |

## D. VARIANT & CASE analysis
| Capability | Adds | Status |
|-----------|------|--------|
| Variant explorer + frequency | happy path vs long tail | **HAVE** (basic) |
| Trace clustering | group similar cases (behavioral segments) | NONE |
| Variant filtering / happy-path % | focus + the "rework" measure | PARTIAL |
| Case/variant deep-dive UI | drill to a single case's events | NONE |

## E. PREDICTIVE / ML
| Capability | Adds | Status |
|-----------|------|--------|
| Next-activity prediction | what happens next | NONE |
| Remaining-time / cycle-time prediction | when will it finish | NONE |
| Outcome/risk prediction (late, rejected, blocked) | early warning | NONE |
| **Graph Neural Nets over object-centric data** | prediction preserving the object graph | NONE |
| Recommendation / next-best-action | what to do | NONE |

## F. SIMULATION / what-if (our capability #3)
| Capability | Adds | Status |
|-----------|------|--------|
| Discrete-event simulation (SimPy) calibrated from the log | predict impact of a change | NONE (designed only) |
| Monte-Carlo play-out (pm4py) | KPI distribution under a model | NONE |
| System-dynamics / digital twin | scenario modeling | NONE |
| Automated simulation-model generation from the log | what-if without manual modeling | NONE |

## G. ORGANIZATIONAL / resource / control
| Capability | Adds | Status |
|-----------|------|--------|
| Social network / handover-of-work | who passes to whom | NONE |
| Resource/role profiling | workload, specialization | PARTIAL (USER OPERATES_TCODE edges) |
| **Segregation-of-Duties (SoD) violation** | same user create+approve (the BCM dual-control we found by hand) | NONE (systematic) |
| Resource behavior (batching, multitasking, fatigue) | performance drivers | NONE |

## H. DECISION / data-aware
| Capability | Adds | Status |
|-----------|------|--------|
| Decision mining (branch conditions) | WHY a case took a path (data rules at gateways) | NONE |
| Attribute/feature correlation root-cause | what attributes drive delay/deviation | NONE |
| Anomaly / outlier detection | abnormal cases | NONE |
| Concept-drift detection | how the process CHANGED over time | NONE |

## I. EVENT-LOG QUALITY (the gap that made us report artifacts)
| Capability | Adds | Status |
|-----------|------|--------|
| Incomplete-case filtering (within window) | stop reporting truncation artifacts | NONE |
| Noise / infrequent-behavior filtering | clean discovery | NONE |
| **Object-centric filtering/sampling** (arXiv:2205.01428) | OCEL quality | NONE |
| Timestamp repair / ordering (same-day) | fix arbitrary intra-day edges | NONE |
| Log repair / missing-event inference | completeness | NONE |

## J. ACTION / EXECUTION / real-time (Celonis EMS)
| Capability | Adds | Status |
|-----------|------|--------|
| Alerts / triggers on deviations | operational use | NONE |
| Automated actions / orchestration (people+systems+AI agents) | close the loop | NONE |
| **MCP server feeding AI agents** the process graph | agentic | PARTIAL (we have brain+MCP) |
| Real-time / streaming / delta (CDC) | continuous, not snapshot | NONE (snapshot) |
| Task mining (desktop clicks) | the manual work between system steps | NONE |

## K. SELF-SERVICE / interface
| Capability | Status |
|-----------|--------|
| No-code modeling for business users | NONE |
| **NL → query (Celonis LLM-for-PQL)** | NONE (we have Claude — natural fit) |
| Process query language (PQL-equivalent) | NONE |
| BPMN modeling + reference models (Signavio) | NONE |
| Benchmarking (vs peers/industry) | NONE |

## L. DATA SOURCES (see sap_event_sources_catalog.md)
Have: bkpf/bseg, cdhdr-headers, jest, edidc, jobs. Missing (priority): CDPOS, JCDS, VBFA, SWW*, NAST,
BAL*, APQ*, STAD/SWNC, SNAP, AFKO/RESB/QMEL. Plus: TASK MINING data (desktop) — a whole source we lack.
**ADDED s079 (user):** (a) **JOB INTENT via VARIANT** — TBTCP.VARIANT + VARI/VARIS contents (skill
`sap_variant_analysis`) turns a job step from "program ran" into "parameterized business action" (what
CC/accounts/dates/test-update it targets). (b) **FILE SYSTEM** — AL11 dirs, logical file paths
(PATH/FILENAMECI/FILENAME, tcode FILE), `OPEN DATASET` code I/O, IDoc file ports, file-based interfaces
(COUPA/MT940/DMEE) — File as an OCEL object; the JOIN between external systems and the SAP process.
**UNMODELED — real gap, no tool evaluated it.** See catalog §"FILE SYSTEM as an event/object source".

## M. STANDARD & FORMATS / tools to adopt
| Item | Status |
|------|--------|
| **OCEL 2.0 standard** (SQLite/XML/JSON) as our log format | NONE (we use SQLite -> trivial to adopt) |
| **pm4py** (full: inductive/heuristic/conformance/OCDFG) | PARTIAL (only DFG) |
| **ocpa** (object-centric toolkit: OCPN, OCEL conformance/perf) | NONE |
| **OCPM² methodology** (structured OCED extraction) | NONE |
| GoR (Graph of Relations) generation | PARTIAL (the brain IS a GoR engine — not wired) |
| ST01 SQL-trace for field->activity discovery | PARTIAL (we have the ST01 skill — not used for this) |

## Honest summary — what we're NOT using (the adoption backlog, ranked)
1. **Conformance** (B) — the entire as-implemented-vs-standard / custom-overlay analysis. NONE.
2. **Object-centric done right** (A-OCPN, M-ocpa, OCEL 2.0) — we flatten; the field is object-centric. NONE.
3. **Event-log quality** (I) — we report artifacts. NONE.
4. **Real discovery algorithms** (A) — only DFG; no inductive/heuristic/OCPN. NONE.
5. **Predictive/ML + GNN** (E). NONE.
6. **Simulation** (F) — designed, not built.
7. **Decision/root-cause/drift/anomaly** (H). NONE.
8. **Organizational/SoD** (G). NONE (systematic).
9. **Action/real-time/task-mining** (J). NONE.
10. **NL self-service** (K) — we have Claude; not wired as PQL-equivalent.
11. **Data sources** (L) — ~80% of event tables.
12. **Standard/format/tools** (M) — OCEL 2.0, pm4py-full, ocpa, GoR, ST01.

We use ~5–10% of what the field offers. This is the backlog to bring in (Phase 1) before the
Public-Sector solution (Phase 2). Each row = a concrete adoption task.
