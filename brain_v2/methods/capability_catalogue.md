---
name: CAPABILITY CATALOGUE — every capability, what it does, how it helps the model, how it gets better
description: The evaluable inventory of the machine. A tool path in a table cannot be judged; an entry with a stated purpose, a stated contribution and a stated improvement path can be re-evaluated, prioritised and retired. Created s097.
type: project
---

# Capability catalogue

**Why this document exists.** The skill binds phases to tools. That tells you *what to run*.
It does not tell you whether a capability is strong, weak, redundant or worth investing in —
so nothing ever gets re-evaluated, and weak capabilities survive indefinitely because nobody
can see they are weak.

Every entry carries four things, and the fourth is the one that makes the document useful:

| | |
|---|---|
| **Does** | what it actually performs |
| **Helps** | what it contributes to the model — if this cannot be stated, the capability is decoration |
| **State** | where it is honestly: STRONG · WORKS · WEAK · FRAGILE |
| **Improve** | the specific next step. Not "make it better" — the actual lever |

**Re-evaluation cadence: per close.** Run `brain_v2/methods/audit_skill_coverage.py`, then
walk this catalogue and move at least one STATE upward. A capability whose *Improve* line has
not changed in five sessions is either finished or abandoned — decide which.

---

## Phase 0 — Landscape onboarding

### `f0_probe.py` — the negative contract
- **Does:** runs 8 read-only probes against a new system and records what the RFC boundary
  refuses, distinguishing CONSTRAINT_CONFIRMED / NO_CONSTRAINT / **COULD_NOT_PROBE**.
- **Helps:** it is the onboarding gate. Every extraction strategy downstream is chosen from
  this profile instead of discovered by failing repeatedly in production.
- **State:** STRONG. The three-outcome discipline is the valuable part — "I could not probe"
  is never reported as "the restriction exists", which is the failure that makes a system
  profile actively harmful.
- **Improve:** the suite is 8 probes derived from one landscape. Add probes for the
  constraints found since: ROWSKIPS rejection, OPTIONS length limits, per-table read
  restrictions (`TABLE_NOT_AVAILABLE` on tables that demonstrably hold data).

### `split_golden_by_system.py` — one golden DB per system
- **Does:** copies a SID's tables out of a shared golden database into its own file,
  verifying row counts, never dropping the source.
- **Helps:** makes provenance **structural**. The file is the environment, so no naming
  convention has to be trusted — and instance #1 proved the convention gets broken.
- **State:** WORKS. Split D01 out; V01 was already clean.
- **Improve:** it detects ambiguous provenance but cannot resolve it. Add a rule that a
  table whose column count differs from its prefixed twin is flagged as a *different
  extract*, not a subset — and teach `build_golden_manifest.py` to refuse to serve a table
  with ambiguous provenance rather than silently picking one.

### `build_golden_manifest.py` / `gold_ref.py` — the data interface
- **Does:** resolves a table → system → freshness → provenance without any consumer knowing
  a file path.
- **Helps:** the single seam that makes multi-system, multi-tenant possible. It is why
  adding a D01 database did not require editing every consumer.
- **State:** WORKS.
- **Improve:** the new D01 database is not yet declared in the manifest. And the manifest
  has no *freshness policy* — it reports mtime but nothing consumes it to warn "this table
  is 90 days stale for a weekly-cadence domain".

### `rfc_helpers.py` — the extraction floor
- **Does:** ConnectionGuard (auto-reconnect across VPN drops), pagination, automatic field
  splitting against the 512-byte line buffer.
- **Helps:** every extractor imports it. Reliability lives here once instead of in fifty
  scripts.
- **State:** STRONG, with one sharp edge.
- **Improve:** it swallows `TABLE_WITHOUT_DATA` as "empty is normal". That masked an
  invalid-FIELD error for three extraction runs in s097, each returning zero rows with no
  error. Distinguish *genuinely empty* from *the request was malformed* and surface the
  second.

---

## Phase 1 — Footprint

### `probe_footprint.py` — installed vs configured vs productive
- **Does:** bounded read-only probe of org structure and document volumes per module.
- **Helps:** answers the question the model exists to answer — what does this tenant
  actually run — with evidence rather than with a component list.
- **State:** WORKS. Found five productive modules that had been reported as absent.
- **Improve:** the probe list is hand-written. Derive it from the application-component
  hierarchy so a module that exists in DF14L but has no probe is *reported as unprobed*
  rather than silently missing. Also: nothing re-runs it, so footprint drift is invisible.

### `build_profile_links.py` — the crossing and its gate
- **Does:** crosses the profile against capability model, ontology, claims, docs and
  companions; enforces the profile invariants.
- **Helps:** produces SYSTEM-LEVEL BLIND SPOTS — modules the tenant runs that the model has
  never examined. It found six on its first run, reproducing errors made by hand.
- **State:** STRONG. Gated, so it cannot be skipped.
- **Improve:** the claim matcher still uses a text fallback for names of 4+ characters.
  Structured axes are authoritative; the text path should be reported separately as
  *weak linkage* rather than merged into the same list.

---

## Phase 2 — Taxonomy and discovery

### `extract_component_hierarchy.py` — SAP's own taxonomy
- **Does:** builds `df14l` (component id → application component) and `tadir_obj`
  (object → package, 10 object types), completing object → package → component.
- **Helps:** the deterministic bottom-up rung. It replaces guessing a module from a package
  name with SAP stating the answer, and it is what took the ascent to 92%.
- **State:** STRONG.
- **Improve:** TADIR is chunked by first character because P01 rejects ROWSKIPS; a type with
  more than 40,000 objects under one letter would still truncate silently. Add a per-chunk
  cap check that warns when a chunk returns exactly the cap. Function modules resolve only
  through their function group — resolve them directly via `TFDIR`.

### `executed_objects_domain_map.py` — the classifier ladder
- **Does:** classifies every executed object to a domain through DEVCLASS → DLVUNIT →
  overlay → name → text, first match wins.
- **Helps:** turns 11.4M executions into per-domain activity. It is the U_USAGE evidence for
  the whole capability model.
- **State:** WORKS, and it was actively misleading until s097. It had no bucket for RE-FX,
  PBC, FI-AA, PM, SD, TRM or any third-party namespace, so 40% of execution volume sat in
  `Uncatalogued` and was read as "these modules do not exist".
- **Improve:** it still resolves by package regex where the DF14L component is now
  available and authoritative. Replace the DEVCLASS rung with a component lookup and keep
  the regex only as the fallback for objects with no TADIR entry.

### `adaptive_discovery.py` — the self-improving classifier
- **Does:** auto-resolves unknown calls by function group, naming and app domain, **learns
  the resolution**, and re-classifies in a loop until it converges. What it cannot resolve it
  exposes as a frontier for human review.
- **Helps:** this is the closest thing the model has to learning. Each run explains more with
  zero hand-coding.
- **State:** STRONG in design; under-exercised in practice.
- **Improve:** it has not been run since the new component chain existed. Feed it the
  component as a signal and measure whether the frontier shrinks — that is a direct,
  measurable maturity gain.

### `canonical.py` — alias resolution
- **Does:** one lookup from any domain spelling to its canonical key.
- **Helps:** removes the single most repeated defect in the codebase — the same alias bug
  appeared three times in one session, in three files, and was fixed three times separately.
- **State:** WORKS, new.
- **Improve:** two consumers use it; others still compare names raw. Sweep the remaining
  call sites, then add a lint check so a raw comparison fails review.

### `validate_ontology.py` — the vocabulary gate
- **Does:** refuses any domain key that does not resolve against the canonical contract.
- **Helps:** the vocabulary stays canonical by construction rather than by discipline. It
  rejected six new domains until they were declared.
- **State:** STRONG. Gated at rebuild step 0.
- **Improve:** it validates keys but not *relationships* — a subdomain can declare a parent
  that does not exist. Extend it to validate the tree.

### `mine_domain.py` — per-domain footprint discovery
- **Does:** discovers the object footprint of a named domain from the data.
- **Helps:** the bottom-up complement to a curated domain registry.
- **State:** WEAK — it exists and is barely used; the registry is still largely hand-curated
  (128 objects curated vs 286 resolved automatically).
- **Improve:** run it per domain and *diff* its output against the curated registry. The
  disagreements are either discoveries or curation errors, and both are worth knowing.

---

## Phase 3 — Extraction

### `accumulate_logs.py` — **the time moat**
- **Does:** rolling-window capture of audit, job, dump and syslog data into `*_history`
  tables.
- **Helps:** the single most valuable capability in the inventory. The source system purges
  this data in 7–120 days; the accumulator builds the history that makes the operating model
  measurable at all. **Every conclusion about how the organisation runs depends on it.**
- **State:** STRONG in function, FRAGILE in status — it is gitignored and therefore not
  versioned, and its output lives only in a local, unbacked database.
- **Improve:** version the script itself. Then treat "days of history captured" as a
  first-class metric, because it is the one asset that **cannot be recovered by working
  harder later**. On a new client this starts on day one, before analysis is even scoped.

### `method_registry.py` — object → how to extract it
- **Does:** resolves any object to its extraction method and analysis method, by table class
  with overrides for the hard cases (logs, clusters, pool tables, dump FMs).
- **Helps:** stops the model rediscovering "how do I read X" every session.
- **State:** STRONG. The resolver design is right: rules plus overrides, not an enumeration.
- **Improve:** its constraints hard-code a SID (`"P01-secured: NO ROWSKIPS"`). The *concept*
  — production is restricted — is portable; the *name* is not. Parameterise by system role.

### `gold_refresh.py` — registry-driven refresh
- **Does:** refreshes by domain × table type using the right strategy per type
  (master → PK-delta, totals → value-compare, transactional → high-water-mark), auditing
  each run.
- **Helps:** the only capability that keeps the golden data *current* rather than a snapshot.
- **State:** STRONG.
- **Improve:** `_gold_sync_log` records domain, table and strategy but **never the system**.
  With a golden database per system now, that column is required or the audit trail is
  ambiguous by construction.

### `delta_refresh_2026.py` — high-water-mark delta
- **Does:** incremental transactional refresh.
- **Helps:** makes re-extraction affordable; without it every refresh is a full pull.
- **State:** WORKS. Large (52 KB) and instance-shaped.
- **Improve:** split the engine from the table list. The engine is KIT; the list is INSTANCE.

---

## Phase 4 — Operation

### `rfc_process_classifier.py` — the 2-axis engine
- **Does:** explains every call on two axes — PROCESS (from the name) and ORIGIN (from
  host/destination/user).
- **Helps:** produced the finding that reframes the entire engagement: 80.6% of business
  traffic is driven by external satellites. Neither axis alone can produce it — without
  origin, a middleware call and an internal report look identical.
- **State:** STRONG. 91.1% of business calls explained.
- **Improve:** origin resolution stops at the host name. Middleware endpoint GUIDs remain
  unresolvable, so a fleet of 174 endpoints collapses to one label. Worth attacking from the
  middleware side rather than from SAP.

### `semantic_activity_map.py` · `fm_executed_census.py` · `parse_syslog.py`
- **Does:** map executed objects to business activities; census function-module execution;
  parse system log.
- **Helps:** turn raw execution into process language.
- **State:** WORKS, thinly exercised.
- **Improve:** the activity map is the bridge to process mining. Connect it to the OCEL
  builder so activities are named consistently in both places.

---

## Phase 5 — Boundary

### Interface intelligence (skills + extracts)
- **Does:** builds the integration map from destinations, IDocs, jobs, HTTP services and DB
  links; every flow with channel, artifact, volume, direction and a VERIFIED/INFERRED tag.
- **Helps:** the process does not live inside the module boundary. 37 flows, 18+ external
  systems — a review scoped to SAP would miss where the work happens.
- **State:** WORKS. Documented, with 10 open questions honestly recorded.
- **Improve:** it is a hand-maintained document, not a generated artifact. Generate the flow
  table from the sources so it cannot go stale silently, and keep the prose for the reasoning.

---

## Phase 6 — Capability model

### `maturity_score.py` · `snapshot_model_state.py` · `gold_extractor_maturity.py`
- **Does:** score the domain × capability matrix; append each measurement to a history file;
  score extraction maturity per domain × table.
- **Helps:** the time series *is* the deliverable — it shows the understanding improving,
  which a snapshot cannot.
- **State:** WORKS.
- **Improve:** the matrix is hand-maintained. Several cells are now derivable from evidence
  the model already holds (U_USAGE from the execution map, D_DATA from the golden registry).
  Derive what can be derived and reserve hand-curation for judgement.

---

## Phase 7-8 — S/4 readiness · Transport intelligence

### S/4 readiness model
- **Does:** a verified factor scorecard (readiness ATC, simplification database, custom-code
  analysis, usage scoping).
- **Helps:** the migration x-ray, and the commercial hook.
- **State:** WEAK — the *method* is verified, the *application* is empty for every domain.
- **Improve:** it is largely runnable against DEV. The blocker is that nobody has run it,
  not that it is hard. Also: instance #1's real blocker (the Business Partner conversion)
  surfaced from the footprint phase, not from here — feed footprint findings into the
  readiness factors.

### Transport intelligence
- **Does:** transports, their objects, release status and the change path to production.
- **Helps:** answers whether change reaches production with discipline.
- **State:** WORKS as extraction; WEAK as analysis.
- **Improve:** connect it to the S/4 readiness custom-code scoping — a transport history is
  a usage signal for custom code, and dead code is not a migration cost.

---

## Phase 9 — Verification

### `build_model_graph.py` — ascent, coherence, cross-cutting
- **Does:** climbs from every object to the installation recording the rung that resolved it;
  compares macro assertions against detail evidence; classifies domains that span modules.
- **Helps:** the only mechanism that can detect the model drifting from the system it
  describes. Its coherence check found a defect *in itself* on first run, which is the
  point.
- **State:** STRONG. 92.2% ascent.
- **Improve:** coherence currently only counts objects. Add *recency* — a module with
  objects but no execution in the audit window is a different verdict from one with neither.

### `verify_claims.py` · `claims_health.py` · `curate.py`
- **Does:** verify claims against the golden data; report claims lacking independent
  sources; curate structural drift.
- **Helps:** stops the brain accumulating unverified assertions.
- **State:** WORKS. Verification rate ~24.5% — most claims have a single source.
- **Improve:** that 24.5% is the most under-invested number in the model. Raising it is
  cheaper than most new extraction, and it directly protects against confidently repeating
  something wrong.

---

## Phase 10 — The maturity loop

### `rebuild_all.py` — the pipeline
- **Does:** ontology gate → asset gate → crossings → model graph → brain state → indexes →
  companions → landing.
- **Helps:** the gates only protect what runs. This is what makes them run.
- **State:** STRONG.
- **Improve:** nothing schedules it. It runs when a human remembers.

### `meta_capability.py` — self-assessment
- **Does:** scores 8 capabilities of *our way of working* from artifacts, marking each
  sub-lever measured [M] or estimated [E].
- **Helps:** the model can see itself improving. An [E] is itself a backlog item.
- **State:** STRONG.
- **Improve:** DURABILITY sits at 0.10 and has for sessions. Two of its three sub-levers
  cannot be fixed by code — they need an offsite backup of the golden database and the
  memory directory. Naming that repeatedly has not moved it; it needs an owner.

### `verify_assets.py` — the asset gate
- **Does:** fails the rebuild when a declared asset is missing or a method points at a
  non-existent tool; warns on undeclared golden tables.
- **Helps:** the guarantee that exploration lands in the model. It found two load-bearing
  tables undeclared since session 92 on its first run.
- **State:** STRONG, new.
- **Improve:** it warns rather than fails on undeclared tables. Once the backlog of legacy
  tables is declared, promote that check to a failure.

### `audit_skill_coverage.py` — is the skill complete?
- **Does:** walks the real tool surface and reports orphaned tools, phantom references and
  missing cadences.
- **Helps:** the skill was written from memory and covered 11% of capability. This is what
  made that visible; it is now 92.7%.
- **State:** WORKS, new.
- **Improve:** it matches tools by filename mentioned anywhere in the skill, so a tool named
  in passing counts as covered. Require the mention to sit inside a phase section.

---

## Phase 11 — Delivery

### `companion_builder.py` · companion graph · landing page
- **Does:** generates the living visual layer and the graph that links companions.
- **Helps:** none of the analysis matters if it stays queryable-only. This is where it
  reaches a human.
- **State:** WORKS.
- **Improve:** companion drift is bidirectional and currently reconciled by hand. And the
  delivery layer has no notion of *audience* — the same content serves an engineer and an
  executive, which means it serves neither well.

---

## Honest summary of the portfolio

| state | count | what it means |
|---|---|---|
| STRONG | 11 | works, is gated or measured, and its failure modes are known |
| WORKS | 12 | functions, but under-exercised or hand-maintained |
| WEAK | 4 | exists and is barely used — `mine_domain`, S/4 application, transport analysis, claim verification rate |
| FRAGILE | 1 | `accumulate_logs` — the most valuable capability, and the least protected |

**The three levers that would move the model most, in order:**

1. **Back up the golden database and the memory directory.** The most valuable capability in
   the inventory writes to an unbacked local file. Everything else is reproducible; that is not.
2. **Replace the classifier's DEVCLASS regex with the DF14L component lookup.** The
   authoritative signal now exists and the classifier still guesses.
3. **Raise the claim verification rate from 24.5%.** Cheaper than new extraction, and it is
   what stops the model repeating something wrong with confidence.
