---
name: Product Architecture — SAP ECC Process Intelligence (commercial)
description: The product = a Process Intelligence tool that reads ALL of SAP ECC, helps UNDERSTAND specific processes, DESIGN new ones, and drive IMPROVEMENTS by domain — learning from real data. It sits ON TOP of the existing capability layers (L1-L10), which stay as the platform. Persisted Session #079.
type: project
---

# Product: SAP ECC Process Intelligence

**Product statement (user, s079):** a Process Intelligence product that **reads all of SAP ECC** and
helps you **(1) understand** specific processes, **(2) design** new ones — the way we work in this
project — **(3) SIMULATE the future solution in Python and validate feasibility BEFORE building it in
SAP**, and **(4) drive improvements by domain**. It **learns from the real data**, not documentation.

This does NOT replace the capability layers we already built ("estaban muy bien"). The layers are the
PLATFORM that reads SAP ECC; the product is the experience on top. The Process Intelligence Layer (L7)
is elevated into the product core.

## The stack — product on top of the existing platform

```
  ┌──────────────────────────────────────────────────────────────┐
  │  PRODUCT  ·  four capabilities, all data-driven               │
  │  1.UNDERSTAND  2.DESIGN  3.SIMULATE+VALIDATE  4.IMPROVE(domain)│
  └──────────────────────────────────────────────────────────────┘
                         ▲ powered by
  ┌──────────────────────────────────────────────────────────────┐
  │  L7  PROCESS INTELLIGENCE LAYER                               │
  │   Event-log builder (OCEL 2.0) · pm4py mining (deterministic) │
  │   · Brain = Process Intelligence Graph · Claude = agentic     │
  └──────────────────────────────────────────────────────────────┘
                         ▲ on top of the platform (unchanged, "muy bien")
  ┌──────────────────────────────────────────────────────────────┐
  │  L1 Connectivity · L2 Data Extraction (Gold DB) · L3 Brain    │
  │  (knowledge graph) · L4 Code Extraction · L5 Transport Intel  │
  │  · L6 Fiori · L8 Monitoring · L9 Deployment · L10 BDC Intel   │
  └──────────────────────────────────────────────────────────────┘
                         ▲ reads (real data, not docs)
  ┌──────────────────────────────────────────────────────────────┐
  │  SAP ECC  —  the live system + its event/transaction/log data │
  └──────────────────────────────────────────────────────────────┘
```

"Read all SAP ECC" = L1 (connect) + L2 (extract data) + L4 (extract code) + L3 (model it in the brain)
+ L5/L8/L10 (transport/monitoring/BDC). The product needs all of them; that is why the layers stay.

## The three product capabilities

### 1. UNDERSTAND a specific process  (= process mining DISCOVERY)
From real event data (L2: bkpf/cdhdr/jobs/doc-flow), the PI layer builds the OCEL and mines the
**as-is** process: the real variants, who does what, cycle times, bottlenecks, rework. Claude explains
it in business language with full traceability to the events. Answers: *"how does this process actually
run today?"* — from data, not from a person's memory or an outdated SOP.

### 2. DESIGN a new process  (= the to-be model — our differentiator)
This is what we do in this project: read reality → understand it → design the improvement. The product
embodies that methodology. Using the discovered as-is + the brain (code, config, exits, the data model,
the LDB hierarchy, the incidents) + the domain knowledge, Claude helps DESIGN the **to-be**: a new or
re-engineered process (the target flow, the config/code changes, the controls). Pure mining tools mostly
show as-is; designing the to-be (BPMN-style, with the SAP objects it touches) is where the brain + Claude
add value competitors lack.

### 3. SIMULATE the future solution in Python + validate feasibility  (de-risk BEFORE building)
Before touching SAP, test the to-be in Python — fast and cheap. Two validations:
- **Process simulation (impact):** build a digital twin of the process as a **discrete-event simulation**
  (SimPy) or **pm4py play-out/Monte-Carlo** on the discovered model, **calibrated from the REAL event
  log** (arrival rates, activity durations, branching probabilities from the mined performance DFG). Run
  what-ifs ("automate F.05", "fix OB09 repoint", "add an approval step", "merge two steps") and predict
  the KPIs: cycle time, throughput, bottleneck shift, error/rework rate, cost. Compare options quickly,
  pick the best — all in Python, zero SAP risk.
- **Technical feasibility:** can the change actually be built on THIS kernel? Reuse our capability-probe
  methodology (verify_capabilities_before_recommending): empirical ADT/RFC/DDIF probe on D01, the
  standard-object rule (never modify SAP-delivered objects), D01-only for new objects, transport
  implications. Output: feasible / not-feasible / feasible-with-constraints, BEFORE committing build effort.
Only a change that passes BOTH (good simulated impact + technically buildable) proceeds to IMPROVE.
This is the enterprise de-risking step pure mining tools lack — simulate the future, validate fast, then build.

### 4. IMPROVE by domain  (= conformance + enhancement + action)
Per domain (FI, Treasury, Payment, PSM, HCM, ...): **conformance** (where execution deviates from the
intended process — SoD breaks, skipped approvals, the FX-revaluation OB09 gap, the BCM same-user batches),
**bottlenecks/cost** (where time/money is lost), and **recommendations** Claude can turn into action
(remediation, config fix, automation) under the safety rules. Each incident is resolved WITH process
context — not in isolation.

## The data-driven learning loop ("aprende de los datos reales")
```
real SAP data ──extract(L2)──▶ brain model(L3) ──mine(L7)──▶ understand ──▶ design
      ▲                                                                        │
      │                                          simulate+validate in Python ◀─┘
   new data ◀── system changes ◀── deploy(L9) ◀── act(Claude) ◀── (only if it passes)
```
The Python simulation step means we never build in SAP what we have not first proven works AND is
feasible — the loop is **propose → simulate on real data → validate feasibility → then build**.
The product learns continuously from real execution: more event data → better mined processes → better
understanding → better design/improvement → deployed changes → new data. Process maps are OUTPUTS that
keep updating from reality, never static documents.

## Per-domain operating model
The product works domain by domain (the brain is already domain-indexed: Layer 14 domains registry).
For each domain: read its real data → mine its processes → understand → design improvements → resolve its
incidents with context. The discovery patterns (project_discovery_patterns.md) are the reusable
methodology; the process mining + brain make it repeatable and data-grounded.

## Commercial differentiators (the moat)
1. **Reads ALL of ECC** — code + config + data + transport + jobs + users, unified in one brain (the
   platform layers). Competitors connect to data; we connect to the whole system.
2. **Deterministic + auditable** (CP-001/002/003) — every finding provable to its events (path:line).
   Trust moat for compliance / public sector.
3. **Understand AND design AND improve** — not just as-is monitoring. The to-be design + agentic action.
4. **Object-centric** (OCEL 2.0) — the 2026 frontier, natural for SAP via AWTYP+AWKEY.
5. **Claude as the reasoning/action layer** over a deterministic core — explain, design, act, with tracing.
6. **Simulate-before-build** — Python digital-twin simulation calibrated on real data + technical
   feasibility probe, so changes are de-risked BEFORE any SAP build. Pure mining tools show as-is; we
   prove the to-be works AND is buildable first.

## Where we are / next
Platform layers L1-L6, L8-L10 exist. L7 spec: process_intelligence_layer.md. Event data LOCAL
(bkpf 1.83M, cdhdr 7.81M, jobs). Next: build the L7 mining engine (pm4py) so capability #1 (UNDERSTAND)
runs on real data; then #2 (DESIGN) and #3 (IMPROVE) build on it. Phases 1-3 unblocked without P01.
