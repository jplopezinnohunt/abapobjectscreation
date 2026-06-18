---
name: Gap Analysis — What the BEST SAP Process Mining does that we DON'T
description: Honest gap analysis of our L7 engine vs best-in-class SAP process mining (Celonis EMS / Process Intelligence Graph, SAP Signavio Process Intelligence, SAP's own). What they do that we are NOT doing, table-level and capability-level. Born s079 — "decir qué NO estamos haciendo que los mejores están haciendo." Confidence noted per item.
type: project
---

# What the best SAP process mining does that we DON'T (gap analysis)

Honest contrast: today we are a THIN SLICE — FI-document discovery (bkpf clearing), change-header
discovery (cdhdr), jobs — with pm4py DFG/variants. Best-in-class do far more. Below: what they do,
we don't. [V]=verified by s079 deep research / knowledge; [E]=expert-inferred.

## 1. DATA BREADTH — they map hundreds of tables per process; we tap a handful
We have: bkpf, bseg_union, cdhdr (headers only), jest, edidc, tbtco/tbtcp. They extract the FULL
process table set per module: [V/E]
- **P2P / MM**: EBAN, EKKO, EKPO, EKET, EKBE, EKPA, ESSR/ESLL, RBKP/RSEG, MKPF/MSEG, MARA, LFA1/LFB1.
- **O2C / SD**: VBAK, VBAP, VBEP, VBFA (flow), VBUK/VBUP (status), LIKP/LIPS, VBRK/VBRP, KNA1/KNB1.
- **AP/AR**: BSIK/BSAK/BSID/BSAD (open/cleared items — the payment & collection lifecycle).
- **Change ITEMS**: CDPOS (we have only headers) — the field-level activities.
- **Status**: JEST + **JCDS** (history) + TJ02T — status lifecycle.
- **Workflow**: SWWWIHEAD + SWWLOGHIST — approvals.
- **Output/inventory/etc.**: NAST, and inventory/movement tables.
→ We mine ~5% of the event surface. The "muchas tablas" gap is real and large.

## 2. CONNECTIVITY — they do real-time delta; we do one-off snapshots [V/E]
- **Pre-built SAP connectors + standard CONTENT/templates** per process (table→event mappings shipped).
- **Delta / CDC real-time** extraction (continuous), not a manual RFC snapshot.
- **Multi-system harmonization** (ECC + S/4 + non-SAP into one model).
We do: manual RFC_READ_TABLE snapshots, hand-built mappings, no delta, single system.

## 3. ANALYSIS — they conform, benchmark, predict; we only discover [V/E]
- **Conformance checking** vs a reference/normative model (deviations, not just the as-is graph). WE DON'T.
- **Process-specific KPI library**: DSO/DPO, payment-terms compliance, **duplicate payments**, **maverick
  buying**, cash-discount loss, on-time delivery/payment, touchless/automation rate, rework rate,
  segregation-of-duties violations. WE HAVE NONE.
- **Root-cause analysis** (why a case is late/non-conformant — attribute correlation/ML). WE DON'T.
- **Predictive / ML** (predict late/at-risk cases, next activity). WE DON'T.
- **Benchmarking** (vs industry, vs plant/entity). WE DON'T.

## 4. ACTION / EXECUTION — they close the loop; we only describe [V]
- Celonis is an **Execution Management System**: alerts, automated actions, an **Orchestration Engine**
  coordinating people + systems + AI agents, plus an **MCP server** to feed AI agents operational context.
- Signavio links discovered process to **BPMN models** + improvement workflows.
We: produce a JSON/graph. No action, no alerting, no orchestration, no closed loop.

## 5. TASK MINING — they capture desktop clicks; we only have system events [E]
Best tools combine PROCESS mining (system events) with **TASK mining** (user desktop clicks/keystrokes)
to see the MANUAL work between system steps (copy-paste, swivel-chair, spreadsheets). We have zero
desktop-level visibility — only what SAP records.

## 6. SELF-SERVICE / NL — business users, not scripts [V]
- No-code modeling for business users; **NL → query** (Celonis LLM-for-PQL). We have a Python script.

## 7. GOVERNANCE — PII & data model [V/E]
- **Anonymization / pseudonymization** of users (works-council / GDPR compliance) — shipped. WE IGNORE IT.
- Governed semantic data model / catalog. We have the brain (an asset) but no PII layer.

## Where WE differ / could LEAD (honest, not all gap)
- **Unified brain**: process + code + config + exits + transports + users in ONE graph. Competitors keep
  process-data separate from the code/config. This is our genuine edge.
- **Deterministic + auditable** (path:line evidence) — a trust/compliance moat.
- **Simulate-before-build** + Claude as agentic reasoning/design layer.
But these are POTENTIAL; today they are not productized, while the gaps above are table-stakes the
leaders already ship.

## The honest takeaway
We have built a correct but THIN discovery engine. Table-stakes we lack: (1) data breadth (full module
tables), (2) conformance + KPI library, (3) action/execution loop, (4) PII/real-time. Our differentiation
(unified brain, auditable, simulate, agentic) only matters once the table-stakes exist. Priority: close
the analysis gap (conformance + KPIs) and data-breadth gap, with PII before any external use.
