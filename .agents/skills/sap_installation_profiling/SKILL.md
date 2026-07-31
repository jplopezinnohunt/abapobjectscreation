# SKILL — Profiling a SAP installation, end to end

**What this is:** the portable machine for understanding *any* SAP installation — what it
runs, how it is really operated, where the custom-over-standard delta lives, and how ready
it is to move. UNESCO is instance #1. **The product is the machine, not the insight.**

**Status:** v1.0 (s097). Derived from building instance #1 the hard way, including the
mistakes — which are recorded here as anti-methods because they cost real errors.

---

## The one distinction everything hangs on

| | travels to the next installation | stays with this one |
|---|---|---|
| **KIT** | the algorithms, the probes, the dimensions, the gates, the ladders | — |
| **INSTANCE** | — | the SIDs, the modules found, the domains discovered, the golden data |

A rule of thumb that survives contact: **code and definitions are KIT; JSON content is
INSTANCE.** Where a file mixes them, the mixing is a defect to split, not a style.

Domains and subdomains are **OUTPUT**, never input. The skill discovers them; it must not
arrive with a domain list and impose it. That is why phase 2 exists.

---

## Phase 0 — Landscape onboarding

**Answers:** what systems exist, what each is allowed for, and what the boundary refuses to
give us.

- Enumerate systems and roles (DEV / TEST / PROD). Record the role, not just the SID.
- **PROD is the analytical truth** — how the organisation actually runs. DEV and TEST are
  for code and for test data. Never mix their data into one conclusion.
- Run the negative-contract probe (`f0_probe.py`): what the RFC boundary blocks *here*.
  Three outcomes, never conflated: CONSTRAINT_CONFIRMED / NO_CONSTRAINT / COULD_NOT_PROBE.
  "I could not probe" is never reported as "the restriction exists".
- **One golden database per system.** `scripts/extraction/split_golden_by_system.py`.
  Provenance must be STRUCTURAL — the file *is* the environment. A `d01_` / `p01_` prefix
  convention is a promise, and instance #1 proves it gets broken: 24 dev tables ended up
  inside the production database, and a bare `SKB1` (one company code, 2,312 rows) sat
  beside `P01_SKB1` (nine company codes, 9,249 rows) with the bare name promising
  production. Anyone trusting the convention silently reads an eighth of the data.

**Output:** `installation.json` — the ROOT object: identity, systems, axes, firing order.

---

## Phase 1 — Footprint: what is installed vs implemented vs used

**Answers:** which modules exist, and which are actually alive.

Three tiers, never collapsed into "implemented":

| tier | source | worth |
|---|---|---|
| INSTALLED | `CVERS` | almost nothing — most components ship by default |
| CONFIGURED | org structure (company codes, sales orgs, plants, asset cocds) | real |
| PRODUCTIVE | business documents + execution in the audit log | the answer |

Plus four things that are systematically forgotten and each carried a finding in
instance #1:

1. **Activated business functions** (`SFW_SWITCH_STATE`, values are `T`/`F`) — an
   *independent* confirmation of the footprint that does not depend on counting documents.
   It is how `FMRE_RE_INT` revealed that Real Estate is wired into Funds Management.
2. **Third-party add-ons** — a licence, an upgrade dependency, and usually an independent
   DATA-EXIT channel. Instance #1 had three, all invisible until asked for by name.
3. **Digital front-end** (`/IWFND/I_MED_SRH`, `IS_ACTIVE = 'A'`) — the Fiori/OData surface
   that already exists. In instance #1 it was almost entirely HR, which said more about the
   organisation than any module list.
4. **Users and licences** (`USR02` type mix, `USR06` licence classes, last-logon spread).

**Tool:** `brain_v2/system_profile/probes/probe_footprint.py` — bounded, read-only, and a
hit cap is reported as `>=cap`, never as a count.

**Output:** `system_profile.json`, every module carrying a tier AND its evidence string.

---

## Phase 2 — Taxonomy: discover domains and subdomains

**Answers:** what does this object belong to? — and therefore, what domains exist here.

Use SAP's own taxonomy rather than guessing from names:

```
object → TADIR (package) → TDEVC (component id) → DF14L (APPLICATION COMPONENT)
```

The component string is already a **tree**: `FI-BL-PT-BS-EL` is Bank Accounting → Payment
Transactions → Bank Statement → Electronic. **Domains and subdomains fall out of that
hierarchy** — they do not have to be invented, and the depth you choose is the
domain/subdomain boundary.

This is the rung that makes the whole model verifiable, because it is deterministic. It is
also how instance #1 learnt that Position Budgeting is `PA-PM-PB` — filed under Personnel
Management, not under Funds Management, which is exactly why a budget-shaped search had
never found the largest staff-budget capability in the tenant.

**Cross-cutting is a KIND, not a gap.** Some domains span modules instead of owning one
(integration, period close, output management, security, transport, payroll-finance). When
a domain has no module behind it, ask whether it is a category the model lacks before
calling it a defect.

**Tools:** `probes/extract_component_hierarchy.py` (builds `df14l` + `tadir_obj`),
`process_mining/executed_objects_domain_map.py` (the classifier ladder),
`process_mining/adaptive_discovery.py` (learns the unresolved tail and converges).

**Output:** the domain/subdomain tree + the canonical vocabulary contract.

---

## Phase 3 — Extraction by domain

**Answers:** what data do we need, and how is each thing read *here*.

- **The method resolver comes first** (`method_registry.py`): given any object, return how
  to extract it and how to analyse it. Table class (`DD02L`) drives the default; overrides
  carry the hard-won exceptions (logs, clusters, pool tables, dump/syslog FMs).
- **Registry-driven refresh by domain × type** (`gold_refresh.py`): master → PK-delta,
  totals → value-compare, transactional → high-water-mark; every run audited.
- **Start the log accumulator on day one.** Audit, job, dump and syslog history is purged
  by the system in 7–120 days. The accumulator turns a rolling window into history, and
  that history is what makes the operating model measurable at all. It cannot be
  back-filled: a client onboarded without it loses that time permanently.

**Output:** one golden database per system, with a sync log that records the SYSTEM, not
only the table.

---

## Phase 4 — Operation: how the system is really run

**Answers:** who drives this system, through which channel, reading or writing.

The 2-axis engine over the audit log — **neither axis is sufficient alone**:

- **PROCESS** (from the function/report name → business process)
- **ORIGIN** (from host / destination / user → which system or satellite)

Without origin, a middleware call and an internal report look identical. Instance #1's
headline came from exactly this: 80.6% of business traffic is driven by external satellite
applications, stable month over month — the organisation does not operate SAP through SAP.
A process review scoped to SAP transactions would have described a system few people touch.

Combine channels: RFC/BAPI · IDoc · batch jobs · file interfaces · direct table access ·
dialog. Then split read vs write per satellite: what feeds *out* and what enters *in*, and
through which concentrated write path — that is where segregation-of-duties risk lives.

---

## Phase 5 — Boundary: interfaces and integration

**Answers:** how does data cross the edge, in both directions.

Sources: `RFCDES` (destinations), `EDIDC` (IDocs), `TBTCO`/`TBTCP` (jobs and their
variants), `ICFSERVICE` (HTTP), DB connections, plus the RFC stream from the audit log.

Record every flow as: source → target → channel → artifact → what it does → volume →
VERIFIED or INFERRED. Flag failing flows and insecure ones explicitly; instance #1 found two
database links failing 93% of runs and cloud destinations over plain HTTP.

**Do not stop at the module boundary.** The process does not live inside SAP.

---

## Phase 6 — Capability model: what WE know

**Answers:** how well do we understand each domain — as opposed to what the system does.

Domain × 11 dimensions: standard reference · process · code · config · data · authorisation ·
interface/file · conformance · improvement · S/4 readiness · usage.

A domain is a **pair**: AS-DESIGNED (standard SAP) + AS-RUN (this organisation).
**The delta is the product.** Conformance has two preconditions — the standard baseline and
the discovered process — and the standard baseline is usually the binding constraint.

Keep cells honest: only what is earned by measurement. A row full of optimism is worse than
no row.

---

## Phase 7 — S/4HANA readiness

**Answers:** what would moving cost, and what blocks it.

Method: readiness ATC variant + the simplification database + custom-code analysis, scoped
by **actual usage** (dead custom code is not a migration cost). Structural blockers deserve
their own check — instance #1 found the Business Partner conversion undone, which is a hard
prerequisite, and it surfaced from the footprint phase, not from a migration study.

---

## Phase 8 — Change and transport intelligence

**Answers:** how does change reach production, and is that path disciplined.

Transport requests and their objects, release status, the presence or absence of a QA
system, ATC as a pre-release gate, four-eyes approval. In instance #1 the absence of a QA
system between DEV and PROD is recorded on the *installation* object itself, because it is a
structural property of the landscape rather than of any single change.

---

## Phase 9 — Bidirectional verification

**Answers:** does the macro survive contact with the detail?

- **ASCENT** — from every object, climb to the installation, recording *which rung* of the
  evidence ladder resolved it. Never present a curated assignment as an inference.
- **COHERENCE** — a module asserted PRODUCTIVE with nothing modelled underneath is an
  unsupported assertion, and the model must say so about itself.
- **SYSTEM-LEVEL BLIND SPOT** — a module the tenant runs in production with no capability
  row. Distinct from, and more expensive than, a name without a graph node.

**Tool:** `brain_v2/system_profile/build_model_graph.py`.

---

## Phase 10 — The maturity loop

**Answers:** is the machine getting better, and can we prove it?

Three things must land per discovery — **two out of three is a slow leak**:

| | lands in | enforced by |
|---|---|---|
| RESULT | a claim with evidence | claims health |
| METHOD | the method registry, at stage ≥3 (wired) | rebuild step |
| ASSET | the asset registry | `verify_assets.py`, rebuild step 0b |

Promotion lifecycle: *discovered → scripted → wired → gated → measured.* **Below stage 3 it
is not part of the product.** Stage 5 means it moves a number in the maturity score;
until then "maturity" is a claim, not a measurement.

---

## Tool binding — every phase to its runnable capability

Written after an audit, not from memory: the first draft of this skill named 9 of 80
portable capabilities (11%). A skill that describes phases without naming the tools that
execute them is a plan, not a machine. `brain_v2/methods/audit_skill_coverage.py` re-runs
this check and reports ORPHANED tools, PHANTOM references and missing cadences.

| phase | tools |
|---|---|
| **0 · landscape** | `Zagentexecution/sap_data_extraction/scripts/f0_probe.py` (negative contract, 8 probes) · `scripts/extraction/split_golden_by_system.py` (one DB per system) · `scripts/extraction/build_golden_manifest.py` (the data interface: table → system → freshness → provenance) · `Zagentexecution/mcp-backend-server-python/rfc_helpers.py` (the floor: ConnectionGuard, pagination, field-splitting) · `probe_uba01_live.py` (a live single-object probe — the pattern for checking one thing without a full extraction) · `process_mining/gold_ref.py` (resolve the golden by manifest, never by path) |
| **1 · footprint** | `brain_v2/system_profile/probes/probe_footprint.py` · `brain_v2/system_profile/build_profile_links.py` (crossing + invariant gate) |
| **2 · taxonomy** | `brain_v2/system_profile/probes/extract_component_hierarchy.py` (TADIR→TDEVC→DF14L) · `process_mining/executed_objects_domain_map.py` (the classifier ladder) · `process_mining/adaptive_discovery.py` (learns the unresolved tail and re-classifies until it converges) · `process_mining/mine_domain.py` (per-domain footprint discovery) · `brain_v2/canonical.py` (alias resolution — one implementation, always) · `brain_v2/validate_ontology.py` (the vocabulary gate) |
| **3 · extraction** | `process_mining/method_registry.py` (object → how to extract/analyse) · `scripts/extraction/gold_refresh.py` (registry-driven, by domain × type) · `Zagentexecution/sap_data_extraction/scripts/delta_refresh_2026.py` (high-water-mark delta) · **`Zagentexecution/sap_data_extraction/scripts/accumulate_logs.py`** (the time moat — see the cycle below) · `run_overnight_extraction.py` (bounded parallel extraction) · `extract_ddic_model.py` (the real data model from DD03L/DD08L) · `brain_v2/build_gold_table_registry.py` |
| **4 · operation** | `process_mining/rfc_process_classifier.py` (the 2-axis engine) · `process_mining/parse_syslog.py` · `process_mining/fm_executed_census.py` · `process_mining/semantic_activity_map.py` |
| **5 · boundary** | the integration map is built from `RFCDES`/`EDIDC`/`TBTCO`/`TBTCP`/`ICFSERVICE` extracts · `.agents/skills/sap_interface_intelligence` · `.agents/skills/sap_job_intelligence` |
| **normative** | `brain_v2/normative_models/normative_models.json` — what CORRECT means per flow. The conformance algorithm is the market's; this content is ours, and it is the moat. |
| **6 · capability** | `scripts/extraction/psm_avc_refresh.py` (the recurring AVC/budget refresh — the differentiator domain's own pipeline) · `brain_v2/capability_model/maturity_score.py` · `brain_v2/capability_model/snapshot_model_state.py` (the time series IS the deliverable) · `brain_v2/gold_extractor_maturity.py` |
| **7 · S/4 readiness** | `brain_v2/capability_model/s4_readiness_model.json` (the verified factor method) · `.agents/skills/sap_change_audit` |
| **8 · transport** | `.agents/skills/sap_transport_intelligence` · CTS extracts (`cts_transports`, `cts_objects`) |
| **9 · verification** | `brain_v2/system_profile/build_model_graph.py` (ascent · coherence · cross-cutting) · `brain_v2/verify_claims.py` · `brain_v2/claims_health.py` · `brain_v2/curate.py` |
| **10 · maturity loop** | `brain_v2/rebuild_all.py` (the whole pipeline) · `brain_v2/meta_capability.py` (self-assessment) · `brain_v2/methods/verify_assets.py` (the asset gate) · `brain_v2/methods/audit_skill_coverage.py` (this audit) · **`brain_v2/methods/check_triggers.py`** (fires the loop on evidence) · **`brain_v2/methods/build_domain_capability_matrix.py`** (is capability where the work is?) · **`brain_v2/methods/build_domain_assets.py`** (the asset bundle PER DOMAIN — tables, extraction, algorithms, knowledge, flows, and what is missing) · `brain_v2/graph_queries.py` (profile · ascend · coherence · tree · methods) · `brain_v2/session_activate.py` + `brain_v2/migrate_memory.py` (session bootstrap and memory portability) |
| **algorithm engineering** | **`brain_v2/methods/algorithm_status.py`** (is an algorithm REAL or only declared? — derived from disk, never asserted) · **`brain_v2/methods/validate_paths.py`** (a path field must hold a path, never prose) · **`brain_v2/methods/validate_artifacts.py`** (SHAPE · FLOOR · INVARIANT cases over the artifacts themselves) · **`brain_v2/methods/improve_algorithms.py`** (which algorithm to strengthen next, and why) · **`brain_v2/methods/measure_portability.py`** (what survives on installation #2) · **`brain_v2/methods/run_analysis_cycle.py`** (runs the algorithms in dependency order — the answer to "who runs them, since nobody will", and THE ONLY PLACE the order lives) · **`brain_v2/methods/audit_agent_freshness.py`** (do the agents still know what the model knows?) |
| **the resolver** | **`brain_v2/component_map.py`** — SAP's own taxonomy `TADIR→TDEVC→DF14L` as the authoritative rung. Every object resolves to a domain with a CONFIDENCE and a RUNG, and each rung carries a `tenant_invariant` flag: the map of exactly what breaks on the next installation. **`brain_v2/parse_abap_edges.py`** derives the code edges the graph could not see |
| **operation, derived** | **`process_mining/interface_boundary.py`** (F1 — configured vs observed; DEAD and UNDECLARED are the findings) · **`process_mining/derive_satellites.py`** (F2 — group endpoints by call signature to recover a GUID fleet) · **`process_mining/detect_drift.py`** (A7 — concept drift over accumulated history; per-day RATES, never raw monthly volumes) · **`process_mining/derive_object_roles.py`** (C4 — what an object is FOR, not merely where it belongs) · **`process_mining/caller_parse.py`** (one parser for the audit caller string, plus the truncation reconciliation) · **`process_mining/attach_object_text.py`** (the human name of every object) · **`process_mining/attribute_changes_to_programs.py`** (A8 — what WRITES a thing and through which channel; see the section below) |
| **process mining** | `sap_process_discovery.py` · `ocel_build_p2p.py` (OCEL 2.0 event log) · `process_mining/p2p_conformance.py` (Tier-1: cases classified against the 3-way match) · **`p2p_stdref_xray.py`** (the custom-over-standard x-ray — AS-DESIGNED vs AS-RUN; a *different* capability that used to share the other one's filename) · `build_p2p_log.py` · `tier2_sod.py` (segregation of duties) |

---

## The cycle — why this is a model and not a report

**Maturity does not come from running these once.** It comes from the loop: logs
accumulate → the operating model sharpens → domains resolve → the profile updates →
coherence re-checks → the gaps move. Each layer feeds the one above it, at its own tempo.

| cadence | what runs | why that tempo | what it feeds |
|---|---|---|---|
| **DAILY — non-negotiable** | `accumulate_logs.py` | the system PURGES audit, job, dump and syslog history in 7–120 days. A day not captured is gone permanently; it cannot be back-filled at any price | the operating model, usage per domain, the time axis of everything |
| **WEEKLY** | `gold_refresh.py`, `delta_refresh_2026.py` | master and transactional data drift continuously | every downstream analysis |
| **EVERY REBUILD** | `rebuild_all.py` — ontology gate → **path gate** → asset gate → profile crossing → model graph → brain state → indexes | the gates only protect what they run against | the whole brain |
| **MONTHLY** | `executed_objects_domain_map.py`, `adaptive_discovery.py` | new objects appear; the unresolved tail is the frontier, and it shrinks only if re-run | domains, subdomains, usage |
| **QUARTERLY** | `probe_footprint.py`, `extract_component_hierarchy.py` | the FOOTPRINT DRIFTS — modules get activated, add-ons installed, org structure extended. Nothing currently detects that automatically | the profile, the ascent |
| **PER DOMAIN** | `attribute_changes_to_programs.py` (A8) | a domain with tables but no known write path is listed, not understood | the A_PROCESS and F_INTERFACE cells |
| **PER CLOSE** | `meta_capability.py`, `verify_assets.py`, `validate_paths.py`, `algorithm_status.py`, `audit_skill_coverage.py` | measure whether the machine improved, and catch knowledge that failed to land | the maturity score |

**The feedback that matters most:** the log accumulator is the only activity whose value
is *destroyed by delay*. Everything else can be caught up later; that one cannot. On a new
client it is the first thing to start, before any analysis is even scoped.

**The second feedback loop is the frontier.** `Uncatalogued` is not debt — it is what the
engine deliberately exposes as unresolved. It shrinks when the classifier learns, and it
grows when the system changes. Watching its *trend* is a better health signal than its
absolute size.

---

## Phase 11 — Delivery: how the analysis reaches a human

**Answers:** none of the above is worth anything if it stays queryable-only.

The audit that produced the tool binding above surfaced this phase by its absence: the
delivery machinery existed and the skill never mentioned it.

Three layers, in strict order, and the order is the point:

1. **Brain `.md`** — the source, and a node in the graph. Everything else derives from it.
2. **Companion `.html`** — the living visual (`brain_v2/companion_builder.py`,
   `scripts/build_companion_graph.py`, `scripts/build_landing_page.py`,
   `scripts/validate_companions.py`). Generated, never hand-edited: edit the builder.
3. **Document snapshot** — regenerated from the same source, never authored separately.

Lead with the improvement opportunity, not the inventory. A section that states what a
thing is without stating why it matters, who uses it and what breaks when it is wrong is
not documentation.

**Brain pipeline internals** — orchestrated by `rebuild_all.py`, not run by hand:
`build_brain_state.py` (materialises the layers), `build_active_db.py`,
`build_brain_index.py` (the lean bootstrap index), `add_knowledge_links.py`,
`generate_index.py`, `weave_connective.py`, `cli.py`.

**Operating gates** — `session_start_hook.py` (loads the index and the constraints at
session start), `stop_durability_hook.py` (refuses to let work end only on local disk),
`stop_steward_hook.py` (promotes conversational knowledge before close). These are what
make the cycle survive the humans running it.

**Process-mining leftovers worth naming:** `process_mining/tier0_1_pipeline.py`,
`process_mining/accumulate_problems.py` (the problem accumulator),
`Zagentexecution/sap_data_extraction/scripts/extraction_status.py` (what has been
extracted and what is stale).

---

## The principle that makes this portable: ALGORITHMS ARE THE ASSET

Everything in this skill is a binding of an algorithm to a problem. Strip the tenant away
and what remains — what actually travels to installation #2 — is the algorithms.

- **Data ages** from the moment it is extracted.
- **Findings age**: "80.6% external" is true for one four-month window.
- **Tools are bindings**: one algorithm, one flow, one schema, one tenant.
- **Algorithms compound.**

And the sharper reason they are first-class: **an algorithm fails differently from a tool.**
A broken tool fails loudly. A subtly wrong algorithm produces confident, plausible, WRONG
output. One classifier ran for months filing Project System cost reports under Controlling
— 19,524 executions — and never errored once. **You cannot review what you have not named.**

So every algorithm here declares four things, and the last two are the ones the market
does not publish:

| | |
|---|---|
| what it does | the technique |
| where it is bound | the tools that implement it — an algorithm with no binding is a paper |
| **its failure mode** | **how it produces a wrong answer without failing** |
| **its improvement lever** | **the specific next step, not "make it better"** |

**Registry:** `brain_v2/methods/algorithms.json` — 22 algorithms, organised by the data they
operate on: logs · process events · repository · data · model · interfaces.

### The continuous-improvement mechanism

Three tools, and they answer three different questions:

1. **`validate_algorithms.py`** — *did it regress?* 40 golden cases, every one a real defect
   found the hard way. Gated in the rebuild. **A fix without a case is not a fix.**
2. **`improve_algorithms.py`** — *which one next, and why that one?* Ranks from five measured
   signals: frontier trend · stale lever · unguarded · unexercised · failure-mode debt.
   A worklist, deliberately not a score — a score invites admiring the number.
3. **`check_triggers.py`** — *does anything need re-running now?* Accumulation, maturity and
   interpretation triggers.

**The signal that matters most is the frontier TREND.** An algorithm whose frontier stops
shrinking has stopped learning, and nothing else detects that. It is not the size of the
unexplained remainder that tells you the machine is healthy — it is whether that remainder
is still moving.

### How a new algorithm gets born

None of the twenty-two came from someone having an idea. Five real origins:

| origin | example |
|---|---|
| a **constraint** the system imposes | chunked reads, field-splitting — *the refusal IS the specification* |
| a **recurring defect** | alias canonicalisation, after the same bug appeared three times. **A defect that repeats is an algorithm waiting to be written.** |
| **adoption** from the field | DFG, variants, conformance, OCEL 2.0 — reinventing these would be vanity |
| a **question with no home** | the profile; the interface boundary |
| an observed **asymmetry** | the market assigns activities but not *who called* — in a system called from outside 80% of the time, the caller IS the process |

### How to improve one without breaking it

**Add a rung; do not rewrite.** The function-module fix did not touch the classifier — it
added one hop (module → function group → package). The frontier went from 40% of execution
to 7.7%.

**Correct the denominator before optimising the numerator.** Half of a measured "35% gap"
turned out to be a category error: synthesised concepts and user records counted as
unresolved repository objects, which they can never be.

**Prefer an authoritative source over a better heuristic.** Package-name regex was guessing;
`DF14L` states the answer. And note the trap — *a guess corrected by a guess is not a fix*:
one hand-correction here was itself wrong, and only the authoritative source settled it.

---

## The catalogue must not lie about itself

The registry says which algorithms exist. That claim has to be **derived from disk**, never
written by hand, and this is not a hypothetical:

> `C3_static_edge_extraction` was reported **PROPOSED** — an idea with no implementation —
> while `parse_abap_edges.py` sat in the repository, running. One entry in its list of
> tools was a sentence, `"brain_v2 graph build"`, instead of a path. The binding check
> requires every declared tool to exist on disk; a sentence exists nowhere, so the check
> went false and a BUILT algorithm was published as unbuilt.

Correcting that entry was not the fix. Searching for others found the **same prose copied
into the asset registry** — a second store, same defect, nobody checking. A defect that
appears twice is structural, so it became a gate: `validate_paths.py` now checks all 147
path-typed fields across five stores on every rebuild.

**The rule:** a field that is declared to hold a path holds a path. Prose belongs in a
field named for prose. A path field carrying a sentence does not fail loudly — it makes
every check over it *silently wrong*, which is worse than a gap, because a gap is visible.

---

## Write-path discovery — the generic enrichment (algorithm A8)

**Use it whenever a domain holds tables with no maintenance transaction.** Listing a
domain's tables is not understanding it; the WRITE PATH is the behaviour. And the field
that should answer — the transaction code on the change document — is frequently **empty**:
in this tenant, 93% of the largest object class's changes carry none.

**An empty transaction code is a POINTER, not a gap.** It usually means the write arrived
through a **BAPI or RFC whose interface design never set one**. Reading it as "batch" throws
away the interface; reading it correctly hands you straight to F1 and F2.

**The join** is two streams every SAP tenant already produces, on `(user, day, hour)`:

| | |
|---|---|
| change stream | who changed WHICH object, when |
| execution stream | who ran WHICH program, when |

Nothing about it is SAP-specific. The same shape answers *which program sends this IDoc
type*, *which job produces this file*, *which process touches this interface*.

### Three scorings, two of them wrong — do not repeat them

| attempt | what happened |
|---|---|
| raw coincidence | the RFC dispatcher runs constantly, so it coincides with everything. It named a **spool artifact** as the writer of the largest object class |
| **lift** `P(ran∣changed)/P(ran)` | fixes that and **inverts** the error. It rewards RARITY — so it ranked the real engine below noise and filtered it out. An engine runs on 91 of 108 days, giving a base rate of 0.84 and a lift that cannot exceed 1.19 *however perfect the coincidence*. **An engine is not rare; running whenever the thing changes is what makes it the engine** |
| **φ coefficient** over the slot contingency table | symmetric — how much of the change activity a program covers AND how specific it is — correcting for both base rates. A program present in every slot has `d=0`, its margin collapses, and it scores nothing |

Two further guards, both from defects that happened: **small denominators** (a program that
ran one day scored lift 27 on a single coincidence — the same defect as D6's z-score over a
two-month baseline), and **volume weighting** (a user with 4 changes and one with 5,640,493
are not equal witnesses).

### Exclusivity — the answer is an assignment, not N rankings

A program associated with forty classes has explained none of them. After scoring, each
program is counted across classes; one claimed broadly is reported **AMBIGUOUS**, and a
dispatcher is labelled as **evidence of an interface**, never as the writer. Attributing the
same writer to every table is the failure this constraint exists to prevent.

**Output is a ranked HYPOTHESIS with its evidence and a verdict, for a human to confirm.**
Co-occurrence is not causation, and two programs in the same chain cannot be separated below
the shared time granularity.

---

## Orchestration — a trigger reports evidence, the cycle holds the order

**A trigger must never name a script to run.** Naming one is a decision taken on demand, and
on-demand decisions are precisely the ones that stop being taken — which is the hole the
trigger mechanism exists to close, so committing it there defeats the mechanism. It also
scatters the ordering knowledge across every call site, where it rots quietly: nine of ten
triggers here named individual scripts, and not one of them knew that write-path attribution
must precede boundary discovery.

A trigger reports **evidence** and a **response class**:

| class | meaning |
|---|---|
| `CYCLE` | the analysis cycle runs it, in dependency order |
| `EXTRACTION` | needs a connection — deliberately outside the cycle, because it depends on a VPN and on someone deciding it is time |
| `AUTHORING` | a human writes it; no algorithm produces a domain doc or a capability row |

**Adding an algorithm means placing it in the chain**, with a stated reason for its level —
not remembering to call it. A8 sits at L2, ahead of boundary discovery, because classifying a
class as INTERFACE names the calling function modules, and those functions are what the
satellite derivation groups on.

**If the answer to a trigger is "run X", the real answer is "X belongs in the cycle".**

---

## Agents are frozen knowledge — audit them

An agent or skill was written on one day against one understanding, and nothing tells it when
that understanding moves. `brain_v2/methods/audit_agent_freshness.py` asks three questions of
every agent and skill, derived from disk: does it read something the registry marks
**SUPERSEDED**; does it name a table whose catalogue entry records a **trap** it omits; does
it name gold tables while citing no claim and no catalogue.

The cost is not hypothetical. The **change-audit skill was reading a scope-filtered copy of
the change log** — the one table its entire purpose depends on — and the FI domain agent still
said that table "needs extraction" with twelve million rows already on disk. An agent
answering confidently from a superseded fact is worse than one that says nothing, because it
is trusted.

---

## Anti-methods — each of these cost real errors in instance #1

| | why it looks like evidence, and is not |
|---|---|
| **Absence in a derived index** | Absence in an execution map or an extract is a FLOOR, never an inventory. It yields *not evidenced*, never *not used*. Cost: five productive modules reported as not implemented. |
| **Substring name matching** | Matching a module name inside free text. Two-letter modules are catastrophic — `CO` matched 337 claims. Noise presented as coverage reads as linkage. |
| **Suppressing a generic error** | `TABLE_WITHOUT_DATA` swallowed as "empty is normal" was masking an invalid FIELD. Three extraction runs returned zero rows with no error. |
| **Answering from memory** | Component codes, table and field names are resolved from the system, never recalled. |
| **Comparing domain names raw** | Aliases are declared; use the resolver. This single defect appeared three times in one session. |
| **Trusting a regenerated artifact** | Always diff it against its predecessor. An inline `#` comment silently swallowed two dictionary entries and moved 70,766 executions between domains with no error. |

---

## Order of work, and what actually blocks

Phases 0–2 are the foundation and are cheap. Phase 3 is the long pole and its log
accumulator is time-critical — **start it on day one or lose that history forever**.
Phases 4–5 produce the finding that reframes everything for the client. Phase 6 is where
the commercial product lives, and it is blocked on the AS-DESIGNED baseline more than on
any amount of extraction.

**References:** `brain_v2/installation/` · `brain_v2/system_profile/` ·
`brain_v2/capability_model/` · `brain_v2/methods/` · `process_mining/` ·
`scripts/extraction/`. Replicability analysis (reference, not authority):
`projects/sapilot/analysis/07-inventario-replicabilidad.md`.
