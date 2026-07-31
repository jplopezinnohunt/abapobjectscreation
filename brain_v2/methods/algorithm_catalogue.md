---
name: ALGORITHM CATALOGUE — the techniques, by the data they operate on
description: What an algorithm is (as opposed to a tool or a method), which ones we actually have, what each operates on, its market equivalent, and where there is no algorithm at all. Created s097 after an audit found zero algorithms declared as assets.
type: project
---

# Algorithm catalogue

**Why this is separate from the tool list and the method list.** Three different things were
being collapsed into one:

| | what it is | example |
|---|---|---|
| **Tool** | a script — one binding of an algorithm to one problem | `p2p_conformance.py` |
| **Method** | an activity with a cadence and an owner | M1 footprint probe |
| **ALGORITHM** | the technique itself — portable across domains and problems | declarative conformance against a normative model |

**The audit that produced this document:** the asset registry declares `gold_table`, `store`,
`tool`, `doc`, `gold_database` — five kinds, all of them *artifacts*. **Zero assets declared an
algorithm.** The techniques existed only as implicit content inside scripts, which meant we could
not say which algorithm is used where, could not deliberately reuse one across domains, could not
compare ours against the market's, and could not improve one and know what it affected.

**The sharper reason they must be first-class:** an algorithm fails differently from a tool. A
broken tool fails loudly. A subtly wrong algorithm produces confident, plausible, wrong output —
and this session produced four of them: a greedy classifier rule that stole `FTBB` from bank
statements, a substring matcher that linked 337 claims to `CO`, a wrong denominator that made
ascent look like a 35% gap when half of it was a category error, and a swallowed generic error
that masked an invalid field for three runs. **You cannot review what you have not named.**

Organised by **what the algorithm operates on**, because that is how a gap becomes visible.

---

## A. LOGS — execution reality

*The execution log is the reality that validates. These make it readable.*

### A1 · Chunked temporal read
Read a purging log in bounded windows (≤6h for the audit log) because a wide call hangs and the
connection degrades roughly every 12 calls.
**Ours** — forced by the system, not chosen. **STRONG.** *Improve:* the chunk size is a constant;
derive it from observed response time.

### A2 · Rolling-window accumulation
Capture a window the source purges (7–120 days) into `*_history` tables, turning a window into a
history.
**No market equivalent** — commercial tools connect to a live system and inherit its retention.
**STRONG in function, FRAGILE in protection.** This is the moat: it cannot be back-filled at any
price. *Improve:* make "days of history captured" a first-class metric.

### A3 · Two-axis classification (process × origin)
Explain every call on two independent axes: PROCESS from the object name, ORIGIN from
host/destination/user. **Neither axis alone suffices** — without origin, a middleware call and an
internal report are indistinguishable.
**Our extension of the field.** Process mining assigns activities; it does not systematically
resolve *who called*. This produced the 80.6% finding.
**STRONG** — 91.1% of business calls explained. *Improve:* origin stops at the host name; a fleet
of 174 middleware endpoints collapses to one label.

### A4 · Ordered classifier ladder (first match wins)
An explicitly ordered rule chain — package → software component → overlay → name → text → substrate
— where specificity is expressed by ORDER.
**WORKS, with a known weakness.** Order-dependence is silent: a greedy early rule steals from a
later one, proven twice in s097. *Improve:* replace the package-regex rung with the DF14L component
lookup, which is authoritative. The regex should be the fallback, not the primary.

### A5 · Adaptive learning loop
Auto-resolve unknown calls by function group, naming and application domain; **learn the
resolution**; re-classify until convergence; expose the remainder as an explicit frontier.
**The closest thing we have to learning.** **STRONG in design, UNDER-EXERCISED** — not run since the
component chain existed. *Improve:* feed it the component as a signal and measure whether the
frontier shrinks. Directly measurable.

### A6 · Frontier measurement with a substrate tier
Coverage percentage plus an explicit worklist, with a third tier for technical substrate —
connectivity, session, monitoring: real execution, legitimately non-business.
**Ours. STRONG, new.** Declaring the tier moved "unexplained" from 40% of execution to 11.7%
without hiding anything. *Improve:* watch the TREND — a frontier that stops moving means the
discovery loop stopped running.

---

## B. PROCESS — from events to a process

*The market's core discipline, adopted rather than reinvented.*

### B1 · DFG discovery (directly-follows graph)
Activities as nodes, observed transitions as edges.
**Market standard — pm4py**, the reference implementation (van der Aalst lineage), the substrate
Celonis and Signavio productised. **WORKS.** *Improve:* two event sources are wired (transactions
and change documents); the change-document source is richer for lifecycle and under-used.

### B2 · Variant analysis
Group cases by exact path, rank by frequency and cost. The long tail is where exceptions live.
**Market standard. WORKS.**

### B3 · Performance / bottleneck
Cycle time per transition; waiting versus processing. **Market standard. WORKS.**

### B4 · Declarative conformance against a normative model
State the normative rules, classify every case, quantify deviation in money.
**Market standard, and where the product lives** — the delta between AS-DESIGNED and AS-RUN.
**STRONG and PROVEN** — 38% conformant, 70 violations, $713,341 exposure.
*Improve:* it exists for exactly one flow. The four public-sector flows have no normative model at
all. That is the real gap.

### B5 · OCEL 2.0 object-centric event log
One event references MULTIPLE object types, with no forced single-case notion.
**Ahead of most commercial tooling.** Flat single-case mining forces an artificial case ID and
distorts anything convergent or divergent — which public-sector finance is, constantly: one budget,
many commitments, many actuals.
**WORKS for P2P.** *Improve:* this is the correct substrate for the budget-to-actual flow, where
"the case" is genuinely ambiguous. Build it there next.

---

## C. REPOSITORY — code, config, objects

### C1 · Component resolution chain
`object → TADIR → TDEVC → DF14L (application component)`.
**Ours, and the strongest in the inventory** because it is deterministic: SAP states the answer
instead of us pattern-matching a name. **STRONG** — 1.61M objects resolvable.
*Improve:* function modules resolve only via their function group; resolve them directly via `TFDIR`.

### C2 · Ascent with a provenance rung
Climb from any object to the installation, **always recording which rung resolved it**.
**Ours.** The rung is the point: a curated assignment must never be presentable as an inference.
**STRONG** — 92.2%. *Improve:* add recency — an object with no execution in the window is a
different verdict from one with none at all.

### C3 · Static edge extraction
Parse source for `reads_tables` / `calls_fms` / `writes_tables`.
**WEAK.** Only **98 of 1,212** objects carry code edges. Most of the graph is connected by
crossings, not by parsed structure. *Improve:* the thinnest layer in the model, and the one that
would most improve impact analysis. Requires source at scale.

---

## D. DATA — master and transactional

### D1 · PK-delta (master) · D2 · Value-compare (totals) · D3 · High-water-mark (transactional)
**Standard data engineering, correctly routed per table type** — the intelligence is the ROUTING
(table class → strategy), not the strategies. **STRONG**, registry-driven.
*Improve:* `_gold_sync_log` records domain, table and strategy but **never the system**. With one
golden database per system, that column is now required.

### D4 · Field-splitting against the 512-byte buffer
Split a wide read into column groups, re-join locally. **Forced by the boundary. STRONG.**

### D5 · Bounded probe with cap reporting
Read with an explicit cap and date filter; report a hit cap as `>=cap`, **never as a count**.
**STRONG.** The discipline *is* the algorithm: a truncated read reported as a total is how a model
starts lying.

---

## E. THE MODEL ANALYSING ITSELF

### E1 · Crossing
Join profile × capability × claims × documents × companions through an explicit canonical key.
**STRONG, gated.** Produces system-level blind spots.

### E2 · Coherence
Compare what the macro asserts against what the detail evidences.
**Ours.** The only mechanism that detects the model drifting from the system it describes. **STRONG.**

### E3 · Trigger evaluation
Compare state against thresholds across accumulation, maturity and interpretation; return what to
re-run and why. **WORKS, new.** *Improve:* thresholds are constants chosen by judgement; derive
them from observed variance.

### E4 · Canonicalisation
Resolve any spelling to a canonical key through a declared alias contract, in exactly one place.
**WORKS.** The defect it removes appeared three times in one session.

---

## F. INTERFACES — **there is no algorithm**

The audit found this directly: `RFCDES` appears in the codebase only inside a comment. There is
**no programmatic analysis of the integration boundary at all.**

The 37-flow integration map is **prose, written by hand**. Good prose — every flow carries channel,
artifact, volume, direction and a VERIFIED/INFERRED tag — but:

- it cannot detect a new destination, IDoc type or job appearing;
- it cannot go stale *visibly*, so it goes stale silently;
- it cannot be reproduced on a second installation, which makes it INSTANCE, not KIT.

**What the algorithm should be:**

1. Enumerate the boundary from its sources — `RFCDES`, `EDIDC`, `TBTCO`/`TBTCP`, `ICFSERVICE`,
   database connections, and the RFC call stream in the audit log.
2. Correlate each destination against **observed traffic**: a configured destination with no
   traffic is dead; traffic with no configured destination is a finding.
3. Classify direction and volume per flow, and bind each flow to the process flows it serves.
4. **Diff against the previous run** — a new interface can change the meaning of a domain, which is
   exactly the interpretation trigger already declared.

Well-defined, buildable, on data already extracted. Its absence is the largest single gap here.

---

## Honest summary

| operates on | algorithms | state |
|---|---:|---|
| logs | 6 | strong; A2 fragile, A4 needs the component lookup |
| process | 5 | market-standard, adopted; normative models exist for ONE flow |
| repository | 3 | C1 strongest in the inventory; **C3 weak — 98 of 1,212 objects** |
| data | 5 | strong; sync log missing the system column |
| model self-analysis | 4 | strong and gated |
| **interfaces** | **0** | **no algorithm exists** |

**Three fixes, in order:**

1. **Build the interface algorithm.** Zero algorithms for a boundary carrying 1.33M executions and
   37 flows, on data we already hold.
2. **Give A4 the component lookup.** The authoritative signal exists and the classifier still
   guesses by package regex.
3. **Write normative models for the public-sector flows.** B4 is proven, and the product lives in
   the delta it measures — but it measures one flow today.

---

## Where each algorithm is bound

| algorithm | implemented in |
|---|---|
| A1, A2 | `accumulate_logs.py` |
| A3 | `process_mining/rfc_process_classifier.py` |
| A4, A6 | `process_mining/executed_objects_domain_map.py` |
| A5 | `process_mining/adaptive_discovery.py` |
| B1–B3 | `sap_process_discovery.py` (pm4py) |
| B4 | `process_mining/p2p_conformance.py`, `p2p_stdref_xray.py` |
| B5 | `ocel_build_p2p.py` (pm4py OCEL) |
| C1 | `probes/extract_component_hierarchy.py` |
| C2 | `system_profile/build_model_graph.py` |
| C3 | `brain_v2` graph build |
| D1–D5 | `gold_refresh.py`, `delta_refresh_2026.py`, `rfc_helpers.py`, `probe_footprint.py` |
| E1 | `system_profile/build_profile_links.py` |
| E2 | `system_profile/build_model_graph.py` |
| E3 | `methods/check_triggers.py` |
| E4 | `brain_v2/canonical.py` |
| **F** | **nothing** |
