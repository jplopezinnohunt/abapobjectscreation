---
name: Process-Mining Analysis Maturity — measured score + roadmap to >90%
description: Measured maturity of our process-mining ANALYSIS layer (2026-06-21) = 12.5% (7.5/60 capabilities, HAVE=1/PARTIAL=0.5/NONE=0), scored from process_mining_capability_inventory.md. Plus the tiered roadmap (what we need) to reach >90% comprehension. Feeds capability_model H_IMPROVE for the process-mining capability.
type: project
---

# Process-Mining Analysis Maturity

## Measured score (2026-06-21): **12.5%** (7.5 / 60)
Scored deterministically from `process_mining_capability_inventory.md` (HAVE=1, PARTIAL=0.5, NONE=0).
6 of 12 sections are at **0%**: Conformance, Predictive/ML, Simulation, Decision/data-aware, Event-log-quality.
We do essentially only **DFG discovery** + basic variants. This is the "real product" gap — analysis, not extraction.

| Section | score | 0%? |
|---|---|---|
| A Discovery | 1.0/8 | |
| B Conformance | 0/5 | ⛔ |
| C Performance | 0.5/5 | |
| D Variant/case | 1.5/4 | |
| E Predictive/ML | 0/5 | ⛔ |
| F Simulation | 0/4 | ⛔ |
| G Organizational/SoD | 0.5/4 | |
| H Decision/data-aware | 0/4 | ⛔ |
| I Event-log quality | 0/5 | ⛔ |
| J Action/real-time | 1.0/5 | |
| K Self-service | 1.0/5 | |
| M Standards/tools | 2.0/6 | |

## What we need to reach >90% (close 46.5 / 60 points)
90% ≈ adopting most of the field. It is a multi-phase build, but sequenceable — a few foundations unlock
disproportionate downstream value. Tiers ordered by leverage:

### Tier 0 — FOUNDATION (cheap, unlocks the rest) → ~+12 pts
- **Event-log quality (§I, 0/5)**: incomplete-case filtering (stop reporting truncation artifacts), noise
  filtering, timestamp repair/ordering, OCEL sampling, log repair. **Prerequisite gate** — without it every
  downstream result is an artifact.
- **OCEL 2.0 + pm4py-full + ocpa (§M)**: adopt OCEL 2.0 as the log format (we use SQLite → trivial), upgrade
  pm4py PARTIAL→full, add ocpa (object-centric toolkit). Unlocks A, B, C at once.

### Tier 1 — DISCOVERY + CONFORMANCE (the "as-implemented vs standard" product) → ~+11 pts
- **Discovery (§A, 1/8)**: Inductive Miner, Heuristic Miner, **OCPN** (object-centric Petri net), process trees.
- **Conformance (§B, 0/5)**: token replay, alignments, **object-centric conformance**, Declare/rule conformance
  (SoD, "A before B"). **This IS the custom-over-standard overlay = the core product.**

### Tier 2 — ORGANIZATIONAL + DECISION + PERFORMANCE (data-ready NOW via RSAU) → ~+11 pts
- **Organizational/SoD (§G, 0.5/4)**: systematic SoD (BCM dual-control generalized), social-network/handover,
  resource behavior. **Data unlocked by `rsau_audit_history` (8.5M) — build the analysis.**
- **Decision/data-aware (§H, 0/4)**: decision mining (branch conditions), attribute root-cause, anomaly, drift.
- **Performance (§C, 0.5/5)**: performance spectrum, temporal profile, SLA/due-date.

### Tier 3 — ADVANCED → ~+12 pts
- **Predictive/ML (§E, 0/5)**: next-activity, remaining-time, outcome/risk, GNN over object-centric.
- **Simulation (§F, 0/4)**: discrete-event (SimPy) calibrated from the log, Monte-Carlo, auto-model-gen.
- **Action/real-time (§J)**: alerts/triggers, streaming/CDC, task mining.
- **Self-service (§K)**: NL→PQL (we have Claude — natural fit), PQL-equivalent, BPMN/reference models.

### Cross-cutting — DATA SOURCES (§L) underpins all tiers
Complete the missing event sources: **JCDS** (status history), **VBFA/VBAK** (O2C — biggest gap), **SWW*** 
(workflow/approval+agents), NAST, AFKO/RESB/QMEL. CDPOS (Change-detail) stays deferred by decision.

## Path math
12.5% → Tier0 (~+20%) → ~32% · +Tier1 (~+18%) → ~50% · +Tier2 (~+18%) → ~68% · +Tier3 (~+20%) → **~88-92%**.
So **>90% requires Tiers 0-3 essentially complete**. Highest-leverage first 3 moves: (1) event-log-quality
filtering, (2) OCEL 2.0 + pm4py-full, (3) conformance (as-implemented vs standard). These three alone lift the
two biggest-value 0% sections and stop artifact-reporting.

## Progress 2026-06-21 — first Tier 0/1/2 build (12.5% → ~20%)
Built and running (`process_mining/`): **Tier 0** semantic activity labeling (EKKO/EKBE VGABE→GR/IR) +
incomplete-case quality filter + OCEL 2.0/pm4py-full substrate; **Tier 1** inductive discovery + Declare-style
**conformance** on P2P (38% clean 3-way, 62% deviates; **70 IR-before-GR violations $713K**; GR→IR median 1d,
4% >30d); **Tier 2** behavioral **SoD** on rsau_audit_history (**32 invoice+payment conflicts**, incl. I_MARQUAND
corroborating BCM). Capabilities moved from NONE: Inductive (A) HAVE, Declare-conformance (B) PARTIAL, SoD (G)
PARTIAL, incomplete-case-filter (I) HAVE, pm4py (M) HAVE, OCEL2 (M) PARTIAL = **+4.5 pts → 12.0/60 = ~20%**.
Key learning: **semantic activity labeling is THE foundation** — same pipeline gave garbage on the coarse OCEL
(fitness 1.0 trivial) and real insight once activities were labeled. Next: formal alignments, LLM-semantic
labeling, permission-level SoD (AGR_*), roll the methodology to Payment/FI.

## Honest note
This is the project's stated North Star direction (the "real product is analysis, not more extraction"). It is a
program, not a task. Measure again after each Tier; register the delta in `capability_model` H_IMPROVE.
