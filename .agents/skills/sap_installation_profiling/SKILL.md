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
