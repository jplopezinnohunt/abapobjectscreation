# Retrospective — How our model works, what to improve, and why each element needs its own method (2026-06-21)

Trigger: a session that went from "preserve the logs that purge" to "explain 92% of how UNESCO operates SAP."
The session exposed, in practice, how our intelligence model actually works and where it is weak.

## 1. How the model works (the discovery engine)
The working loop, every element:
**PROBE** (read-only; test the core tool first — BLOCKED gate) → **EXTRACT** (the right method *for this element*) →
**ANALYZE** (the right method *for this element*) → **CONSOLIDATE** (brain-steward → claims / capability_model /
domain docs / feedback_rules, with relationships) → **ESCALATE** (findings → PMO H-items + spawn_task chips) →
**BROADCAST** (ecosystem handoff). Backed by: the **brain** (persistent, queryable, self-describing) + the
**gates** (BLOCKED → conclude against constraints; CLOSE → commit source focused + flag local-only assets;
KNOWLEDGE-PROMOTION → steward). Strength: the brain + the self-adapting discovery. Weakness: see §4.

## 2. THE core insight — extraction method varies by ELEMENT TYPE (proven this session)
We hit, and solved, a *different* extraction path for almost every element. This is the central lesson:
| Element / type | Extraction method | Constraint we learned |
|---|---|---|
| Transparent table (EKKO, CDHDR…) | `RFC_READ_TABLE` | **P01-secured rejects ROWSKIPS** → read ROWSKIPS-free, date-chunked |
| Cluster table (CDPOS/CDCLS) | RFC_READ_TABLE FAILS → ABAP `FOR ALL ENTRIES` | declustered-sometimes; deferred (no value now) |
| Pool table (VARI/VARIS) | RFC reads KEY only → FM `RS_VARIANT_CONTENTS` | pool-table limitation |
| Workload (STAD/SWNCMONI) | not a table → FM `SAPWL_STATREC_READ_FILE` | kernel-verify; deferred |
| **Audit log (RSAU/SM20)** | FM `RSAU_API_GET_LOG_DATA` | **chunked ≤6h** (2-day call hangs); conn POISONS ~every 12 calls → reconnect; transient `partner not reached` → resilient reconnect |
| **Dumps (ST22) + syslog (SM21)** | FM `/USE/BL_GET_SHORTDUMPS` (one call, both) | SNAP `TABLE_NOT_AVAILABLE`; `RFC_ABAP_INSTALL_AND_RUN` **no auth on P01**; custom `Z_READ_SYSLOG` BROKEN; `SALC_MSC_READ_SYSLOG`→0 |
| Roles (AGR_*/USR*) | transparent → RFC_READ_TABLE | not yet extracted (H76) |
| RFC call stream | the audit `RFC Function Call` events | parse `host/dest/user` from PARAMX = the ORIGIN axis |
| SOAMANAGER GUIDs | **not resolvable** | they are external connection IDs, not SAP-named ports |
Key failure mode of OUR PROCESS: **we rediscovered each method by trial** (RFC_READ_TABLE → fails → hunt the FM
in TFDIR → probe its interface → build). That is the #1 inefficiency — it should be a lookup.

## 3. The ANALYSIS method also varies by element
| Element | Analysis method (this session) |
|---|---|
| Tables | SQL aggregation / joins (the golden query) |
| Document-flow (EKKO/EKBE) | process mining — OCEL, inductive miner, conformance (3-way-match) |
| Audit / RFC stream | **2-axis classification** (process × origin) + **self-adapting discovery** (auto-learn FM→process from TFDIR) |
| Change docs (CDHDR) | **blind-spot method**: an activity-stream value of ~0 means you are counting the wrong event → verify via change-docs (RESULT) × call-stream (METHOD) |
| Dumps / syslog | failure-pattern analysis (keyword/class) → the failure side mirrors the operating model |
| Master data | channel-attribution (CDHDR `TCODE` blank/named = BAPI vs dialog) |
| Roles | declared-vs-actual reconciliation (AGR_* × behavior) |

## 4. What to improve (prioritized)
1. **#1 — a per-ELEMENT METHOD REGISTRY (the biggest leverage).** For every SAP object/log: its TYPE
   (transparent/cluster/pool/FM-only/file/not-resolvable), the EXTRACTION method (+ exact FM + interface),
   the CONSTRAINTS (P01-ROWSKIPS, no-auth, retention), and the ANALYSIS method. Extend
   `gold_db_table_catalog.md` (capability **D_DATA**) with a `method` column. This turns the next session's
   "how do I read X?" from a probe-and-fail cycle into a lookup. Today that knowledge is scattered across
   memory notes + the catalog + rediscovered each time.
2. **Escalate findings as tasks** — ✅ DONE (feedback_rule `escalate_findings_as_tasks` + PMO H71–H81 + chips).
   Was the gap the user caught: find → document → move on lost the actionability.
3. **SSO/Kerberos fragility** — the interactive ticket died mid-run **twice**; needs a BASIS keytab (H66).
   Any unattended/overnight extraction is impossible until then. This blocks the whole "accumulator runs itself" goal.
4. **Tooling durability** — the accumulators (`accumulate_logs.py`, `accumulate_problems.py`) are GITIGNORED /
   local-only. The engine that builds the way-of-working isn't versioned. Move to tracked `scripts/` (H70/H78).
5. **Templatize the probe→find-FM→build→accumulate→analyze cycle.** Every new volatile log triggered the same
   sequence; make it a skill so the next log (e.g. table-change DBTABLOG) is faster.
6. **Extend self-adaptation to EXTRACTION-method selection.** The self-adapting discovery auto-learns the
   *analysis* classification; the registry (#1) lets it also auto-select the *extraction* method from the type.
7. **Promote continuously, not only at close.** The steward ran 3× this session — good — but a finding ideally
   becomes a claim the moment it's verified, so a long session never carries unpromoted knowledge.

## 5. Meta-conclusion
Our model is a strong **discovery + brain** engine (consolidation, queryable, self-adapting, ecosystem-aware)
sitting on a **weak METHOD layer** — each extraction and analysis is rediscovered. The fix mirrors the capability
model itself: as the capability model is `domain × capability`, the method registry is
**`object × (extraction-method, analysis-method, constraints, retention)`**. Build that, and the platform stops
re-learning how to read SAP every session — which is the difference between a tool and the SAP Agentic AGI north star.
